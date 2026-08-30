#!/usr/bin/env python3
"""The night board: one view of every ticket under a spec and every session on one.

    board.py --once [<spec>]   print one table and exit
    board.py [<spec>]          stay up, append one line per event
    board.py --watch <spec>    the same, and act on what it sees

One program, several forms, reading the same two sources, so there is never a second
truth to reconcile. `--once` is what an agent runs when it wants the whole picture in
one screen. The argument-less form is what a person leaves open in a tab: it appends,
never redraws, and never enters the alternate screen, so its lines stay in the host's
scrollback where `herdr pane read` can still reach them. `--watch` is the one form that
does anything: it dispatches the frontier, re-prompts a session that is `idle` with a
`phase` other than `closed` or `handoff`, and hands back the tickets that reached a
limit. Nothing it does needs a model, because the only thing it ever says to a worker
is that worker's own dispatch line.

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
import time
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

# The two `phase` values the closing gate writes. Every other value means the ticket
# has not been through it.
CLOSED_OR_HANDOFF = ("closed", "handoff")

# `done` is the same underlying idle state, after unseen background work finished.
IDLE_STATUSES = ("idle", "done")

TOKEN_TTL_MS = 86400000         # a day, so a night's run never outlives its metadata

SOCKET_PATH = os.path.expanduser("~/.config/herdr/herdr.sock")

# The dispatcher is this script's neighbour, so the pair moves as one skill.
DISPATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dispatch.sh")

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


def herdr_run(args: list[str]) -> tuple[int, str]:
    """A Herdr call read for whether it worked, and for what it said when it did not.

    `agent prompt` is the one call whose refusals matter: `agent_blocked` when the
    session is at a question or an approval, `agent_prompt_stalled` when the pane no
    longer takes input at all.
    """
    try:
        run = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=60)
        return run.returncode, (run.stderr or run.stdout or "").strip()
    except Exception as problem:
        return 1, str(problem)


def run_dispatch(number: int, role: str) -> tuple[int, str, str]:
    """`dispatch.sh <n> <role>`: its exit code is a row of the table all by itself."""
    run = subprocess.run(["bash", DISPATCH, str(number), role],
                         capture_output=True, text=True)
    return run.returncode, (run.stdout or "").strip(), (run.stderr or "").strip()


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


def counted_ac(ticket: dict) -> str:
    """`<met>/<total>` off the newest self-run or reverify comment, or `-`."""
    body = newest_with_first_line(ticket, "self-run", "reverify")
    for line in body.splitlines():
        found = UNMET_RE.match(line.strip())
        if found:
            unmet, met = int(found.group(1)), int(found.group(2))
            return f"{met}/{met + unmet}"
    return "-"


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


def idle_and_not_closed_or_handoff(worker: dict | None) -> bool:
    """`idle` or `done`, with a `phase` that is neither `closed` nor `handoff`.

    Both halves are machine-read: the lifecycle state comes from Herdr, the phase from
    the token the ticket script writes. Nothing on screen is consulted.
    """
    return bool(worker
                and worker["status"] in IDLE_STATUSES
                and worker["phase"] not in CLOSED_OR_HANDOFF)


def note_of(ticket: dict, worker: dict | None) -> str:
    """One short phrase saying where this ticket stands, in the pipeline's own words."""
    head = last_first_line(ticket)
    if worker:
        if worker["status"] == "blocked":
            return "BLOCKED: commented, form dismissed"
        if worker["status"] == "unknown":
            return "unknown"
        if worker["status"] in IDLE_STATUSES:
            if worker["phase"] in CLOSED_OR_HANDOFF:
                return head[:60]
            if worker["wake"]:
                return f"re-prompted {worker['wake']} of {WAKE_LIMIT}"
            return ""
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

COLUMNS = (("ticket", 8), ("agent", 18), ("agent_status", 14),
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
    head.append(f"PARALLEL {live}/{parallel}")
    lines = [" · ".join(head), ""]
    lines.append(render_row({name: name for name, _ in COLUMNS}))
    for row in rows:
        lines.append(render_row({
            "ticket": f"#{row['ticket']}",
            "agent": row["agent"],
            "agent_status": row["status"],
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

# --------------------------------------------------------------------- the prompt

# What a session that is `idle` with a `phase` other than `closed` or `handoff` is sent:
# its own dispatch line, and not one word more. Where it got to is on the ticket — the
# `self-run`, `VERDICT` and `REVIEW` comments and the `phase` token say it — and the
# ticket is the only place that is kept. The skill it is already running is what tells
# it to carry on from the newest of those rather than start the closing steps again.
DISPATCH_LINE = "implement #{n}"

# --------------------------------------------------------------------- acting

WAKEUP_LIMIT = ("WAKEUP LIMIT: prompted {k} times and it stopped again at phase={phase}. "
                "Handed back to needs-triage; the ticket stays open.")
TIME_LIMIT = ("TIME LIMIT: {hours} h at phase={phase}. Handed back to needs-triage; the "
              "session was left alone.")


class Watch:
    """The night's one moving part: a full re-read, then the table of §4, then dispatch.

    It holds no file. What it does keep between rounds is what only it can know — when
    a session was first seen settled, and when it may next be prompted — and losing
    that on a restart costs one cooldown, nothing more. Everything else it can be told
    again by the tracker and by Herdr.
    """

    def __init__(self, spec: int, role: str, parallel: int, max_hours: int) -> None:
        self.spec = spec
        self.role = role
        self.parallel = parallel
        self.max_hours = max_hours
        self.settled_since: dict[str, float] = {}
        self.held_since: dict[int, float] = {}
        self.wakes: dict[str, int] = {}
        self.handed_back: set[int] = set()

    # ------------------------------------------------------------- the round

    def run(self) -> int:
        events = Events()
        events.start()
        say("board", "watch", f"spec #{self.spec} role={self.role} "
                              f"parallel={self.parallel} max-hours={self.max_hours}")
        while True:
            try:
                self.round()
            except Exception as problem:
                say("board", "error", str(problem)[:160])
            events.wait(SNAPSHOT_INTERVAL)

    def round(self) -> None:
        rows, _ = collect(self.spec)
        mine = [r for r in rows if r["worker"] and r["worker"]["dispatched"]]
        for row in mine:
            self.pick_up(row)
        self.dispatch_frontier(rows)

    def pick_up(self, row: dict) -> None:
        worker = row["worker"]
        if worker["role"] != "worker":
            # A reviewer that stops is the worker's own `dispatch.sh wait` to time out.
            return
        if self.over_time(row):
            return
        if worker["status"] in IDLE_STATUSES:
            if worker["phase"] in CLOSED_OR_HANDOFF:
                self.close_its_pane(row)
            else:
                self.re_prompt(row)
            return
        if worker["status"] == "working":
            self.settled_since.pop(worker["pane_id"], None)

    # ------------------------------------------------------------- the rows of §4

    def close_its_pane(self, row: dict) -> None:
        """`phase` is `closed` or `handoff`: the closing comment is already on the ticket.

        The pane goes, and with it the tab and the `issue-<n>` name. The reader is on
        GitHub, not in Herdr.
        """
        worker = row["worker"]
        say(f"#{row['ticket']}", worker["status"],
            f"phase={worker['phase']}  {row['note']}")
        herdr(["pane", "close", worker["pane_id"]])
        self.settled_since.pop(worker["pane_id"], None)
        self.held_since.pop(row["ticket"], None)

    def prompts_so_far(self, worker: dict) -> int:
        """How many times this session has been prompted.

        The count lives on the pane, which is where the session it counts lives. A
        token takes a moment to come back round through the snapshot, so this round's
        own prompt is remembered as well; without that a fast round would read a stale
        zero and prompt again immediately.
        """
        return max(worker["wake"], self.wakes.get(worker["pane_id"], 0))

    def re_prompt(self, row: dict) -> None:
        """`idle` with a `phase` other than `closed` or `handoff`.

        A host's idle can be nothing but a gap between turns, so wait
        `COOLDOWN_SECONDS`, confirm it is still idle, and then send the dispatch line.
        """
        worker = row["worker"]
        pane = worker["pane_id"]
        wake = self.prompts_so_far(worker)
        wait = WAKE_BACKOFF[min(wake, len(WAKE_BACKOFF) - 1)]
        first_seen = self.settled_since.get(pane)
        if first_seen is None:
            self.settled_since[pane] = time.monotonic()
            say(f"#{row['ticket']}", worker["status"],
                f"phase={worker['phase']} ac={row['ac']}  COOLDOWN {wait}s")
            return
        if time.monotonic() - first_seen < wait:
            return
        if wake >= WAKE_LIMIT:
            self.hand_back(row, WAKEUP_LIMIT.format(k=WAKE_LIMIT, phase=worker["phase"]))
            return
        self.send(row, DISPATCH_LINE.format(n=row["ticket"]))

    def over_time(self, row: dict) -> bool:
        """Held longer than a ticket may hold a session. Hand it back; leave it running."""
        number = row["ticket"]
        started = self.held_since.setdefault(number, time.monotonic())
        if row["worker"]["phase"] in CLOSED_OR_HANDOFF:
            return False
        if time.monotonic() - started < self.max_hours * 3600:
            return False
        self.hand_back(row, TIME_LIMIT.format(hours=self.max_hours,
                                              phase=row["worker"]["phase"] or "unknown"),
                       close_pane=False)
        return True

    # ------------------------------------------------------------- prompting

    def send(self, row: dict, text: str) -> None:
        """Prompt one session, under the seven conditions such a prompt has to meet."""
        worker = row["worker"]
        if not os.environ.get("HERDR_PANE_ID"):
            say("board", "refuse", "no pane of my own, so I may not prompt anyone")
            return
        fresh = unwrap(herdr(["agent", "get", worker["pane_id"]])).get("agent") or {}
        status = fresh.get("agent_status") or "unknown"
        session = (fresh.get("agent_session") or {}).get("value") or ""
        if session and worker["session"] and session != worker["session"]:
            say(f"#{row['ticket']}", "skip", "the pane holds a different session now")
            self.settled_since.pop(worker["pane_id"], None)
            return
        if fresh.get("focused"):
            say(f"#{row['ticket']}", "hold", "its pane is focused")
            return
        if status not in IDLE_STATUSES:
            say(f"#{row['ticket']}", "hold", f"it is {status} again")
            self.settled_since.pop(worker["pane_id"], None)
            return
        wake = self.prompts_so_far(worker) + 1
        say(f"#{row['ticket']}", "prompt", f"{text} (wake={wake})")
        code, reason = herdr_run(["agent", "prompt", worker["pane_id"], text])
        if code != 0:
            say(f"#{row['ticket']}", "refused", reason[:120] or "the prompt was refused")
        self.bump(worker, wake)

    def bump(self, worker: dict, wake: int) -> None:
        """The count of prompts lives on the pane, where the session it counts lives."""
        herdr(["pane", "report-metadata", worker["pane_id"], "--source", "mmw",
               "--token", f"wake={wake}", "--ttl-ms", str(TOKEN_TTL_MS)])
        self.wakes[worker["pane_id"]] = wake
        self.settled_since[worker["pane_id"]] = time.monotonic()

    # ------------------------------------------------------------- handing back

    def hand_back(self, row: dict, body: str, close_pane: bool = True) -> None:
        number = row["ticket"]
        if number in self.handed_back:
            return
        self.handed_back.add(number)
        say(f"#{number}", "comment", first_line(body))
        gh(["issue", "comment", str(number), "--body", body])
        gh(["issue", "edit", str(number),
            "--remove-label", "ready-for-agent", "--add-label", "needs-triage"])
        say(f"#{number}", "label", "needs-triage")
        if close_pane and row["worker"]:
            herdr(["pane", "close", row["worker"]["pane_id"]])
            self.settled_since.pop(row["worker"]["pane_id"], None)

    # ------------------------------------------------------------- dispatching

    def dispatch_frontier(self, rows: list[dict]) -> None:
        room = self.parallel - len(held(rows))
        for row in frontier(rows):
            if room <= 0:
                return
            if row["ticket"] in self.handed_back:
                continue
            if self.start(row["ticket"]):
                room -= 1

    def start(self, number: int) -> bool:
        code, told, refused = run_dispatch(number, self.role)
        if code == 0:
            say(f"#{number}", "dispatch", told[:120])
            self.held_since[number] = time.monotonic()
            return True
        say(f"#{number}", "not started", refused[:120])
        return False

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
    parser.add_argument("--watch", action="store_true",
                        help="stay up and act on what the table says")
    parser.add_argument("--role", default="junior-worker",
                        help="which row of models.md tonight's workers are started from")
    parser.add_argument("--parallel", type=int, default=PARALLEL,
                        help="how many workers may be alive at once")
    parser.add_argument("--max-hours", type=int, default=MAX_HOURS,
                        help="how long one ticket may hold a session")
    parser.add_argument("spec", nargs="?", type=int,
                        help="the spec issue whose sub-issues are tonight's tickets")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.once:
        return once(args.spec)
    if args.watch:
        if not args.spec:
            sys.stderr.write("board: --watch needs the spec whose tickets to work\n")
            return 2
        return Watch(args.spec, args.role, args.parallel, args.max_hours).run()
    return resident(args.spec)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
