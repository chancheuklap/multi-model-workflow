#!/usr/bin/env python3
"""The night board: one view of every ticket under a spec and every session on one.

    board.py --once [<spec>]   print one table and exit
    board.py [<spec>]          stay up, append one line per event

One program, several forms, reading the same two sources, so there is never a second
truth to reconcile. `--once` is what an agent runs when it wants the whole picture in
one screen. The argument-less form is what a person leaves open in a tab: it appends,
never redraws, and never enters the alternate screen, so its lines stay in the host's
scrollback where `herdr pane read` can still reach them.

The two sources are the tracker and Herdr, and nothing else. There is no state file:
every round is a full re-read, so a dropped connection or a restart loses nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import threading
from datetime import datetime

# --------------------------------------------------------------------- constants

PARALLEL = 2                    # workers alive at once
COOLDOWN_SECONDS = 120          # a first idle may be nothing but a gap between turns
WAKE_BACKOFF = (120, 240, 480)  # seconds to wait before the 1st, 2nd, 3rd prompt
WAKE_LIMIT = 3                  # prompts per session before the ticket goes back
REDISPATCH_LIMIT = 1            # times one ticket is started again after a session dies
MAX_HOURS = 4                   # hours one ticket may hold a session
SNAPSHOT_INTERVAL = 60          # seconds between full re-reads when no event arrives

# --------------------------------------------------------------------- vocabulary

# The phases at which a worker has finished with its ticket, one way or the other.
TERMINAL_PHASES = ("closed", "handoff")

# Herdr's five lifecycle words. `idle` and `done` are the same underlying state.
SETTLED_STATUSES = ("idle", "done")

SOCKET_PATH = os.path.expanduser("~/.config/herdr/herdr.sock")

# --------------------------------------------------------------------- reading

def gh(args: list[str]) -> str:
    """`gh` with the colour forcing some hosts inject stripped off its output.

    Grok Build hands its agents CLICOLOR_FORCE=1, under which `gh` writes ANSI escapes
    into --json output that no JSON reader can parse.
    """
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    run = subprocess.run(["gh", *args], capture_output=True, text=True, env=env)
    return run.stdout if run.returncode == 0 else ""


def gh_json(args: list[str], fallback):
    try:
        return json.loads(gh(args))
    except Exception:
        return fallback


def herdr(args: list[str]) -> dict:
    try:
        run = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=20)
        return json.loads(run.stdout)
    except Exception:
        return {}


def unwrap(payload: dict) -> dict:
    """Herdr answers `{"id":…, "result":{…}}`; some calls are read for their result."""
    return payload.get("result", payload) if isinstance(payload, dict) else {}


def live_agents() -> list[dict]:
    """Every agent Herdr can see, with its name, status and pane tokens."""
    snapshot = unwrap(herdr(["api", "snapshot"])).get("snapshot") or {}
    return snapshot.get("agents") or []


def sub_issues(spec: int) -> list[int]:
    """The spec's own children, followed through the tracker's native relation.

    A sub-issue a worker opened during the night is in here too, told apart by its
    labels rather than by when it appeared.
    """
    rows = gh_json(["api", f"repos/:owner/:repo/issues/{spec}/sub_issues"], [])
    return [int(r["number"]) for r in rows if isinstance(r, dict) and r.get("number")]


def read_ticket(number: int) -> dict:
    """One ticket, in the shape the rest of this file expects."""
    fields = "state,labels,assignees,blockedBy,comments,title"
    raw = gh_json(["issue", "view", str(number), "--json", fields], {})
    return normalise_ticket(number, raw)


def normalise_ticket(number: int, raw: dict) -> dict:
    labels = [l.get("name") for l in raw.get("labels") or [] if isinstance(l, dict)]
    nodes = (raw.get("blockedBy") or {}).get("nodes") or []
    bodies = [c.get("body") or "" for c in raw.get("comments") or [] if isinstance(c, dict)]
    return {
        "number": number,
        "state": (raw.get("state") or "").upper(),
        "title": raw.get("title") or "",
        "labels": labels,
        "assignees": [a.get("login") for a in raw.get("assignees") or [] if isinstance(a, dict)],
        "blockers": [int(n["number"]) for n in nodes
                     if isinstance(n, dict) and n.get("state") != "CLOSED" and n.get("number")],
        "comments": bodies,
    }

# --------------------------------------------------------------------- the tickets

def first_line(text: str) -> str:
    stripped = (text or "").strip()
    return stripped.splitlines()[0].strip() if stripped else ""


def last_first_line(ticket: dict) -> str:
    """The first line of the ticket's newest comment: the pipeline's own status word."""
    comments = ticket.get("comments") or []
    return first_line(comments[-1]) if comments else ""


def newest_with_first_line(ticket: dict, *prefixes: str) -> str:
    """The newest comment whose first line starts with one of `prefixes`."""
    for body in reversed(ticket.get("comments") or []):
        head = first_line(body)
        if any(head.startswith(p) for p in prefixes):
            return body
    return ""


UNMET_RE = re.compile(r"^UNMET:\s*(\d+)\s*\(met:\s*(\d+)\)")
UNTICKED_RE = re.compile(r"^-\s\[\s\]\s+(AC\d+):")


def counted_ac(ticket: dict) -> str:
    """`<met>/<total>` off the newest self-run or reverify comment, or `-`."""
    body = newest_with_first_line(ticket, "self-run", "reverify")
    for line in body.splitlines():
        found = UNMET_RE.match(line.strip())
        if found:
            unmet, met = int(found.group(1)), int(found.group(2))
            return f"{met}/{met + unmet}"
    return "-"


def unmet_criteria(body: str) -> list[str]:
    """The criteria a self-run left unticked, in ticket order."""
    return [m.group(1) for m in
            (UNTICKED_RE.match(line.strip()) for line in body.splitlines()) if m]

# --------------------------------------------------------------------- the sessions

NAME_RE = re.compile(r"^issue-(\d+)(-review)?$")


def session_of(agent: dict) -> dict | None:
    """The ticket and role this live agent belongs to, or None if it is not ours.

    The tokens are written at dispatch, so they are there from the first moment. The
    name is the fallback for a session that came up but was never told anything: the
    dispatcher gives it `issue-<n>` before it prompts, and only the dispatcher uses
    that name, so it is as good an identity as the token.

    `dispatched` is the narrower question of whether this is a session the dispatcher
    started and still holds — the name is what answers it, because nothing else hands
    out `issue-<n>`. A pane carrying a token from a ticket it finished long ago is
    somebody's own session now, and only the dispatched ones are ever acted on.
    """
    tokens = agent.get("tokens") or {}
    named = NAME_RE.match(agent.get("name") or "")
    number, role = tokens.get("ticket"), tokens.get("role")
    if not (number and str(number).isdigit()):
        if not named:
            return None
        number = named.group(1)
        role = "reviewer" if named.group(2) else "worker"
    return {
        "ticket": int(number),
        "role": role or "worker",
        "name": agent.get("name") or "",
        "dispatched": bool(named and int(named.group(1)) == int(number)),
        "pane_id": agent.get("pane_id") or "",
        "session": ((agent.get("agent_session") or {}).get("value") or ""),
        "status": agent.get("agent_status") or "unknown",
        "focused": bool(agent.get("focused")),
        "cwd": agent.get("cwd") or "",
        "phase": tokens.get("phase") or "",
        "ac": tokens.get("ac") or "",
        "wake": int(tokens["wake"]) if str(tokens.get("wake", "")).isdigit() else 0,
        "model": tokens.get("model") or "",
    }


def sessions(agents: list[dict]) -> list[dict]:
    return [s for s in (session_of(a) for a in agents) if s]


def worker_on(sessions_: list[dict], number: int) -> dict | None:
    for s in sessions_:
        if s["ticket"] == number and s["role"] == "worker":
            return s
    return None


def held(rows: list[dict]) -> list[dict]:
    """The rows whose worker is a session the dispatcher started and still holds."""
    return [r for r in rows if r["worker"] and r["worker"]["dispatched"]]

# --------------------------------------------------------------------- the rows

def build_rows(numbers: list[int], tickets: dict[int, dict],
               sessions_: list[dict]) -> list[dict]:
    """One row per ticket, joining what the tracker says to what Herdr sees."""
    rows = []
    for number in sorted(set(numbers)):
        ticket = tickets.get(number) or {"number": number, "state": "", "labels": [],
                                         "assignees": [], "blockers": [], "comments": []}
        worker = worker_on(sessions_, number)
        rows.append({
            "ticket": number,
            "worker": worker,
            "state": ticket["state"],
            "labels": ticket["labels"],
            "blockers": ticket["blockers"],
            "assignees": ticket["assignees"],
            "agent": worker["name"] if worker else "-",
            "status": worker["status"] if worker else "-",
            "phase": phase_of(ticket, worker),
            "ac": (worker["ac"] if worker and worker["ac"] else counted_ac(ticket)) or "-",
            "wake": str(worker["wake"]) if worker else "-",
            "note": note_of(ticket, worker),
        })
    return rows


def phase_of(ticket: dict, worker: dict | None) -> str:
    if worker and worker["phase"]:
        return worker["phase"]
    if ticket.get("state") == "CLOSED":
        return "closed"
    return "-"


def stalled(worker: dict | None) -> bool:
    """A settled session that has not reached either exit is a session that stopped."""
    return bool(worker
                and worker["status"] in SETTLED_STATUSES
                and worker["phase"] not in TERMINAL_PHASES)


def note_of(ticket: dict, worker: dict | None) -> str:
    """One short phrase saying where this ticket stands, in the pipeline's own words."""
    head = last_first_line(ticket)
    if worker:
        if worker["status"] == "blocked":
            return "QUESTION commented"
        if worker["status"] == "unknown":
            return "session gone"
        if worker["status"] in SETTLED_STATUSES:
            if worker["phase"] in TERMINAL_PHASES:
                return head[:60]
            if worker["wake"]:
                return f"stalled, prompted {worker['wake']} of {WAKE_LIMIT}"
            return "stalled"
        return ""
    if ticket.get("state") == "CLOSED":
        return (head[:60] + ", pane closed").strip(", ")
    if ticket.get("blockers"):
        return "waiting on " + ", ".join(f"#{b}" for b in ticket["blockers"])
    if "needs-triage" in (ticket.get("labels") or []):
        return head[:60] or "needs-triage"
    if "ready-for-agent" in (ticket.get("labels") or []):
        return "ready"
    return head[:60]

# --------------------------------------------------------------------- the frontier

def frontier(rows: list[dict]) -> list[dict]:
    """The tickets that may be started right now, in ticket order.

    Open, in the agent lane, every blocker closed, nobody has claimed it, and no live
    session already holds it. The last of those is what keeps a second round from
    starting a second worker on a ticket the first one is still doing.
    """
    return [r for r in rows
            if r["state"] == "OPEN"
            and "ready-for-agent" in r["labels"]
            and not r["blockers"]
            and not r["assignees"]
            and r["worker"] is None]

# --------------------------------------------------------------------- output

COLUMNS = (("ticket", 8), ("agent", 18), ("status", 9),
           ("phase", 19), ("ac", 7), ("wake", 6), ("note", 0))


def render_row(cells: dict) -> str:
    out = []
    for name, width in COLUMNS:
        value = str(cells.get(name, ""))
        out.append(value.ljust(width) if width else value)
    return (" " + "".join(out)).rstrip()


def render_table(rows: list[dict], spec: int | None, now: datetime,
                 parallel: int = PARALLEL) -> str:
    live = len(held(rows))
    head = ["mmw board", now.strftime("%H:%M")]
    if spec:
        head.append(f"spec #{spec}")
    head.append(f"{len(rows)} tickets")
    head.append(f"parallel {live}/{parallel}")
    lines = [" · ".join(head), ""]
    lines.append(render_row({name: name for name, _ in COLUMNS}))
    for row in rows:
        lines.append(render_row({
            "ticket": f"#{row['ticket']}",
            "agent": row["agent"],
            "status": row["status"],
            "phase": row["phase"],
            "ac": row["ac"],
            "wake": row["wake"],
            "note": row["note"],
        }))
    return "\n".join(lines)


def say(who: str, action: str, detail: str = "", when: datetime | None = None) -> None:
    """Append one line about one thing that happened. Never redraw, never clear."""
    when = when or datetime.now()
    line = f"{when.strftime('%H:%M:%S')}  {who.ljust(10)}{action.ljust(11)}{detail}".rstrip()
    print(line, flush=True)

# --------------------------------------------------------------------- events

class Events:
    """A live feed of pane changes, with a full re-read as the thing that never fails.

    Herdr pushes a whole `PaneInfo` on `pane.updated`, and neither that subscription
    nor `pane.closed` takes a pane id, so one connection sees every pane. When the
    connection drops, the caller keeps working off its own timer: nothing is stored
    between rounds, so a missed event costs at most one interval.
    """

    def __init__(self) -> None:
        self.woke = threading.Event()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def wait(self, seconds: float) -> bool:
        """Block until something happened or `seconds` passed. True if something did."""
        woken = self.woke.wait(seconds)
        self.woke.clear()
        return woken

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                self._listen()
            except Exception:
                pass
            self.stop.wait(2)

    def _listen(self) -> None:
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.settimeout(SNAPSHOT_INTERVAL)
        conn.connect(SOCKET_PATH)
        request = {"id": "mmw-board", "method": "events.subscribe",
                   "params": {"subscriptions": [{"type": "pane.updated"},
                                                {"type": "pane.closed"}]}}
        conn.sendall((json.dumps(request) + "\n").encode())
        buffer = b""
        while not self.stop.is_set():
            try:
                chunk = conn.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                break
            buffer += chunk
            if b"\n" in buffer:
                buffer = buffer.rsplit(b"\n", 1)[1]
                self.woke.set()
        conn.close()

# --------------------------------------------------------------------- the forms

def collect(spec: int | None) -> tuple[list[dict], list[dict]]:
    """Everything one round needs: the rows, and the live sessions behind them."""
    agents = live_agents()
    sessions_ = sessions(agents)
    numbers = list(sub_issues(spec)) if spec else []
    numbers += [s["ticket"] for s in sessions_]
    tickets = {n: read_ticket(n) for n in sorted(set(numbers))}
    return build_rows(numbers, tickets, sessions_), sessions_


def once(spec: int | None) -> int:
    rows, _ = collect(spec)
    print(render_table(rows, spec, datetime.now()))
    return 0


def watched_fields(row: dict) -> tuple:
    return (row["status"], row["phase"], row["ac"], row["wake"])


def report_changes(rows: list[dict], seen: dict[int, tuple]) -> None:
    """Append a line for every row whose visible state moved since the last round."""
    for row in rows:
        now = watched_fields(row)
        was = seen.get(row["ticket"])
        if was == now:
            continue
        seen[row["ticket"]] = now
        if was is None:
            continue
        detail = f"phase={row['phase']} ac={row['ac']}"
        if row["note"]:
            detail += f"  {row['note']}"
        say(f"#{row['ticket']}", row["status"], detail)
    for number in [n for n in seen if n not in {r["ticket"] for r in rows}]:
        seen.pop(number, None)
        say(f"#{number}", "gone", "no ticket and no session")


def resident(spec: int | None) -> int:
    """Stay up and append. Reports; changes nothing."""
    events = Events()
    events.start()
    seen: dict[int, tuple] = {}
    rows, _ = collect(spec)
    print(render_table(rows, spec, datetime.now()), flush=True)
    print(flush=True)
    for row in rows:
        seen[row["ticket"]] = watched_fields(row)
    while True:
        events.wait(SNAPSHOT_INTERVAL)
        try:
            rows, _ = collect(spec)
        except Exception as problem:
            say("board", "error", str(problem)[:120])
            continue
        report_changes(rows, seen)

# --------------------------------------------------------------------- entry

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="board.py",
        description="The night board over one spec's tickets and their sessions.")
    parser.add_argument("--once", action="store_true",
                        help="print one table and exit")
    parser.add_argument("spec", nargs="?", type=int,
                        help="the spec issue whose sub-issues are tonight's tickets")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.once:
        return once(args.spec)
    return resident(args.spec)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
