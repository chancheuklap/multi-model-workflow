#!/usr/bin/env python3
"""The board: one view of every ticket under a spec and every session on one.

    board.py --once [<spec>]        print one table and exit
    board.py [<spec>]               stay up, append one line per event
    board.py --watch <spec>         the same, and act on what it sees
    board.py --advance-plan <spec>  what `dispatch.sh advance` has to do, in order
    board.py --worker-grades <spec> the worker-grade labels of every ticket in the queue

One program, several forms, reading the same two sources, so there is never a second
truth to reconcile. `--once` is what an agent runs when it wants the whole picture in
one screen. The argument-less form is what a person leaves open in a tab: it appends,
never redraws, and never enters the alternate screen, so its lines stay in the host's
scrollback where `herdr pane read` can still reach them. `--watch` is the one form that
does anything, and it does three things: a worker whose turn failed on the network is
sent `continue`; a worker that ended a turn on its own short of `closed` or `handoff`
is reported to `mmw-main`, which reads its screen and decides; a worker at `closed` or
`handoff` has its pane closed. Nothing it does needs a model.

What it does not do is dispatch. `advance` is the main agent's: when the frontier
grows, `--watch` tells `mmw-main` to run `dispatch.sh advance`, which merges the
branches of the tickets that closed and then starts the ones that can start. The board
never takes a ticket out of the agent queue either: a ticket leaves the night by the
closing comment its worker writes, or by staying behind an open blocker all night — the
`NIGHT SUMMARY` lists it, and it keeps its label.

One board covers one Herdr workspace. Sessions in another workspace belong to another
board and are not read, not counted and not touched.

The two sources are the tracker and Herdr, and nothing else. There is no state file:
each of the board's rounds is a full re-read, so a dropped connection or a restart
loses nothing.

How a session is doing comes from the session itself: `turn.py`, next to this file,
runs on the host's own lifecycle hooks and writes the `turn` pane token — `ready`,
`working`, `ended`, `failed:<error>`, `cancelled:<reason>` — beside the
`agent_status` it reports to Herdr. The board reads the token and never the screen.
A session with no token, because its hooks are not installed or Herdr restarted, is
left alone until it has been `idle` for `FALLBACK_SECONDS` with nothing new on the
ticket, and then reported to `mmw-main` the same way as one that stopped on purpose.
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
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------- constants

MAX_HOURS = 4                   # hours one ticket may hold a session before mmw-main is told
SNAPSHOT_INTERVAL = 60          # seconds between full re-reads when no event arrives
FAILED_LIMIT = 3                # `continue`s per phase before mmw-main is told instead
FALLBACK_SECONDS = 600          # idle with no `turn` token and nothing new on the ticket

# --------------------------------------------------------------------- vocabulary

# The two `phase` values `verify-ticket.py --closeout` writes. Every other value means
# the ticket has not been through it.
CLOSED_OR_HANDOFF = ("closed", "handoff")

# `done` is the same underlying idle state, after unseen background work finished.
IDLE_STATUSES = ("idle", "done")

TOKEN_TTL_MS = 86400000         # a day, so a night's run never outlives its metadata

SOCKET_PATH = os.path.expanduser("~/.config/herdr/herdr.sock")
LOG_DIR = Path(os.path.expanduser("~/.mmw/logs"))

# `dispatch.sh` is this script's neighbour, so the pair moves as one skill.
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


def own_login() -> str:
    """The account `gh` is signed in as, or empty when it cannot be read.

    Empty is the safe answer. The one judgement that turns on it — whether a claim on
    a ticket was made by this pipeline rather than by a person — then decides that it
    was not, and no claim is given back.
    """
    return gh(["api", "user", "-q", ".login"]).strip()


def herdr(args: list[str]) -> dict:
    try:
        return herdr_strict(args)
    except Exception:
        return {}


def herdr_strict(args: list[str]) -> dict:
    """A Herdr call whose failure the caller has to face.

    `herdr` answers `{}` for a refusal, a timeout and a broken pipe alike, which is
    the right shape for a call whose answer only decorates a line of output. It is
    the wrong shape for the question this board acts on — which sessions exist —
    because an unanswered call and an empty answer would then be the same thing, and
    the board would read a Herdr that is restarting as a workspace with no sessions
    left in it.
    """
    run = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=20)
    if run.returncode != 0:
        raise RuntimeError(f"herdr {' '.join(args)}: exit {run.returncode}")
    return json.loads(run.stdout)


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


def unwrap(payload: dict) -> dict:
    """Herdr answers `{"id":…, "result":{…}}`; some calls are read for their result."""
    return payload.get("result", payload) if isinstance(payload, dict) else {}


def snapshot() -> dict:
    """Everything Herdr can see right now.

    Raises when Herdr could not be asked. A round that cannot see the workspace must
    not act on it. `Watch.run` catches it and skips the round.
    """
    payload = unwrap(herdr_strict(["api", "snapshot"])).get("snapshot")
    if not isinstance(payload, dict):
        raise RuntimeError("herdr api snapshot: no snapshot in the answer")
    return payload


def live_agents() -> list[dict]:
    """Every agent Herdr can see, with its name, status and pane tokens."""
    return snapshot().get("agents") or []


def live_panes() -> list[dict]:
    """Every terminal Herdr can see, whether or not an agent has been detected in it.

    A pane is there as soon as its terminal is, while an agent appears only once Herdr
    has worked out that a session is running in it. The two are read apart for that
    reason: `terminals_holding` needs the half that does not wait on detection.
    """
    return snapshot().get("panes") or []


def sub_issues(spec: int) -> list[int]:
    """The spec's own children, followed through the tracker's native relation.

    A sub-issue a worker opened during the night is in here too, told apart by its
    labels rather than by when it appeared.
    """
    rows = gh_json(["api", "--paginate", "--slurp",
                    f"repos/{{owner}}/{{repo}}/issues/{spec}/sub_issues?per_page=100"], [])
    # `--slurp` answers with one array per page; a single page answered flat is read too.
    flat = [r for page in rows for r in (page if isinstance(page, list) else [page])]
    return [int(r["number"]) for r in flat if isinstance(r, dict) and r.get("number")]


def read_ticket(number: int) -> dict:
    """One ticket, in the shape the rest of this file expects."""
    fields = ("state,labels,assignees,blockedBy,comments,title,"
              "createdAt,closedAt")
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
        "created": raw.get("createdAt") or "",
        "closed_at": raw.get("closedAt") or "",
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
    """The first line of the ticket's newest comment: the pipeline's protocol slot."""
    comments = ticket.get("comments") or []
    return first_line(comments[-1]) if comments else ""


def newest_with_first_line(ticket: dict, *prefixes: str) -> str:
    """The newest comment whose first line starts with one of `prefixes`."""
    for body in reversed(ticket.get("comments") or []):
        head = first_line(body)
        if any(head.startswith(p) for p in prefixes):
            return body
    return ""


# The three summary lines gate-check prints, one of which is the second line of every
# `self-run` and `reverify` comment. Each stops at its own numbers rather than at the
# closing bracket, because the bracket may also hold the reverify counts or a scope.
ALL_MET_RE = re.compile(r"^ALL MET\s*\((\d+)\s+met\b")
UNMET_RE = re.compile(r"^UNMET:\s*(\d+)\s*\(met:\s*(\d+)\b")
HANDOFF_RE = re.compile(
    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(met:\s*(\d+)"
    r"(?:,\s*unmet:\s*(\d+))?")


def counted_ac(ticket: dict) -> str:
    """`<met>/<total>` off the newest self-run or reverify comment, or `-`.

    The total is every criterion the summary line accounts for: met, unmet, and, on a
    `HANDOFF REQUIRED:` line, abandoned as well. `ALL MET` accounts for none but the
    met ones, which is what makes it `ALL MET`.
    """
    body = newest_with_first_line(ticket, "self-run", "reverify")
    for raw in body.splitlines():
        line = raw.strip()
        found = ALL_MET_RE.match(line)
        if found:
            met = int(found.group(1))
            return f"{met}/{met}"
        found = HANDOFF_RE.match(line)
        if found:
            abandoned, met = int(found.group(1)), int(found.group(2))
            unmet = int(found.group(3) or 0)
            return f"{met}/{met + unmet + abandoned}"
        found = UNMET_RE.match(line)
        if found:
            unmet, met = int(found.group(1)), int(found.group(2))
            return f"{met}/{met + unmet}"
    return "-"


# --------------------------------------------------------------------- the sessions

def name_prefix() -> str:
    """What every Herdr name this pipeline hands out starts with, in this workspace.

    Herdr's agent names are unique among live agents across the whole server, not per
    workspace, so two repositories each holding a ticket #100 would collide on
    `issue-100` and the second `herdr agent start` would simply fail. The workspace id
    is short, stable, and already the prefix of every pane id in it. Outside Herdr, or
    on a server that reports no workspace, the names are the bare ones.
    """
    ws = (os.environ.get("HERDR_WORKSPACE_ID") or "").strip().lower()
    return f"{ws}-" if ws else ""


def worker_name(number: int) -> str:
    """The Herdr name `dispatch.sh` gives this ticket's worker session."""
    return f"{name_prefix()}issue-{number}"


def name_re() -> re.Pattern:
    """The shape of a name this pipeline hands out, in this workspace.

    Read at the moment it is used rather than frozen at import, so that whichever
    workspace this process was started in is the one it answers for.
    """
    return re.compile(rf"^{re.escape(name_prefix())}issue-(\d+)(-review)?$")


def session_of(agent: dict) -> dict | None:
    """The ticket and kind this live agent belongs to, or None if it is not ours.

    The `kind` token is `worker` or `reviewer`, the same two words a dispatch takes.
    Which `models.md` row a worker started from is the `model` token beside it.

    The tokens are written at dispatch, so they are there from the first moment. The
    name is the fallback for a session that came up but was never told anything:
    `dispatch.sh` gives it `issue-<n>` before it prompts, and only `dispatch.sh` uses
    that name, so it is as good an identity as the token.

    `dispatched` is the narrower question of whether this is a session `dispatch.sh`
    started and still holds — the name is what answers it, because nothing else hands
    out `issue-<n>`. A pane carrying a token from a ticket it finished long ago is
    somebody's own session now, and only the dispatched ones are ever acted on.
    """
    tokens = agent.get("tokens") or {}
    named = name_re().match(agent.get("name") or "")
    number, kind = tokens.get("ticket"), tokens.get("kind")
    if not (number and str(number).isdigit()):
        if not named:
            return None
        number = named.group(1)
        kind = "reviewer" if named.group(2) else "worker"
    return {
        "ticket": int(number),
        "kind": kind or "worker",
        "name": agent.get("name") or "",
        "dispatched": bool(named and int(named.group(1)) == int(number)),
        "pane_id": agent.get("pane_id") or "",
        "session": ((agent.get("agent_session") or {}).get("value") or ""),
        "status": agent.get("agent_status") or "unknown",
        "focused": bool(agent.get("focused")),
        "cwd": agent.get("cwd") or "",
        "phase": tokens.get("phase") or "",
        "ac": tokens.get("ac") or "",
        "turn": tokens.get("turn") or "",
        "turn_id": tokens.get("turn_id") or "",
        "model": tokens.get("model") or "",
        "host": agent.get("agent") or "",
        "workspace": agent.get("workspace_id") or "",
    }


def sessions(agents: list[dict]) -> list[dict]:
    """The sessions of this workspace, and no others.

    Several boards run at once, one per workspace, and every one of them sees every
    pane on the server. Without this a board would re-prompt and close the sessions
    of a batch it knows nothing about. A server that reports no workspace for this
    process leaves every session in, which is the one-board case.
    """
    own = (os.environ.get("HERDR_WORKSPACE_ID") or "").strip()
    found = [s for s in (session_of(a) for a in agents) if s]
    return [s for s in found if not own or s["workspace"] == own]


def worker_on(sessions_: list[dict], number: int) -> dict | None:
    for s in sessions_:
        if s["ticket"] == number and s["kind"] == "worker":
            return s
    return None


def reviewer_on(sessions_: list[dict], number: int) -> dict | None:
    """The reviewer session on this ticket, held apart from its worker.

    Nothing the board does reaches it: a reviewer that stops or runs long is the
    worker's own `dispatch.sh wait` to time out, and the ticket is never handed back
    over one.
    """
    for s in sessions_:
        if s["ticket"] == number and s["kind"] == "reviewer":
            return s
    return None


def held(rows: list[dict]) -> list[dict]:
    """The rows whose worker is a session `dispatch.sh` started and still holds."""
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
            "reviewer": reviewer_on(sessions_, number),
            "state": ticket["state"],
            "labels": ticket["labels"],
            "blockers": ticket["blockers"],
            "assignees": ticket["assignees"],
            "agent": worker["name"] if worker else "-",
            "status": worker["status"] if worker else "-",
            "phase": phase_of(ticket, worker),
            "ac": (worker["ac"] if worker and worker["ac"] else counted_ac(ticket)) or "-",
            "turn": worker["turn"] if worker and worker["turn"] else "-",
            "note": note_of(ticket, worker),
            "head": last_first_line(ticket),
            "comment_count": len(ticket.get("comments") or []),
            "created": ticket.get("created") or "",
            "closed_at": ticket.get("closed_at") or "",
        })
    return rows


def phase_of(ticket: dict, worker: dict | None) -> str:
    if worker and worker["phase"]:
        return worker["phase"]
    if ticket.get("state") == "CLOSED":
        return "closed"
    return "-"


def turn_kind(turn: str) -> str:
    """`failed`, `stopped`, `running`, or `` for a session with no `turn` token.

    `stopped` is a turn the session ended itself, whether it completed or was cut
    short: neither is a network error, and what both need is somebody to look.
    """
    if turn.startswith("failed:"):
        return "failed"
    if turn == "ended" or turn.startswith("cancelled:"):
        return "stopped"
    if turn in ("working", "ready"):
        return "running"
    return ""


def note_of(ticket: dict, worker: dict | None) -> str:
    """One short phrase saying where this ticket stands, in the pipeline's own words."""
    head = last_first_line(ticket)
    if worker:
        if worker["phase"] in CLOSED_OR_HANDOFF:
            return head[:60]
        kind = turn_kind(worker["turn"])
        if kind == "failed":
            return "turn failed; continue"
        if kind == "stopped":
            return "stopped; mmw-main told"
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

    Open, in the agent queue, every blocker closed, nobody has claimed it, and no live
    session already holds it. The last of those is what keeps a second round from
    starting a second worker on a ticket the first one is still doing.
    """
    return [r for r in rows
            if r["state"] == "OPEN"
            and "ready-for-agent" in r["labels"]
            and not r["blockers"]
            and not r["assignees"]
            and r["worker"] is None]


# The worktree `dispatch.sh` opens for a ticket, by its directory name.
WORKTREE_RE = re.compile(r"^issue-(\d+)$")


def terminals_holding(panes: list[dict]) -> set[int]:
    """The tickets of this workspace that still have a terminal standing in them.

    Two readings, either of which counts. The `ticket` token is what `dispatch.sh`
    wrote on the pane; the pane's working directory is the `issue-<n>` worktree the
    tab was opened in, which is the shell's own state and survives anything Herdr
    forgets about the session inside it.
    """
    own = (os.environ.get("HERDR_WORKSPACE_ID") or "").strip()
    held: set[int] = set()
    for pane in panes:
        if own and (pane.get("workspace_id") or "") != own:
            continue
        number = ((pane.get("tokens") or {}).get("ticket") or "")
        if not str(number).isdigit():
            named = WORKTREE_RE.match(os.path.basename((pane.get("cwd") or "").rstrip("/")))
            number = named.group(1) if named else ""
        if str(number).isdigit():
            held.add(int(number))
    return held


def orphan_claims(rows: list[dict], login: str, held: set[int] | None = None) -> list[dict]:
    """The rows whose claim outlived the session that made it, in ticket order.

    `verify-ticket.py --preflight` claims a ticket by assigning it to the account it
    runs as, and exactly two paths give that claim back: the closeout, and the hand
    back to triage. A session that ends any other way — a crash, a machine restart, a
    tab somebody closed — leaves the claim standing, and since `frontier` takes only
    unassigned tickets, that ticket is never dispatched again.

    Four things together say the owner of the claim is gone: the ticket is open, it is
    in the agent queue rather than taken out of it by a person, this pipeline's own
    account is on it, and no live session of ours holds it. A claim by anyone else is
    not this pipeline's to give back, and a ticket carrying one stays off the frontier,
    which is the right answer: somebody took it.

    `held` is the fourth condition read a second way, and it is what keeps a Herdr
    that has not finished coming up from emptying a whole night's claims. An answered
    snapshot listing no agents is not proof that no worker is running: agent detection
    lags the terminals it runs in, so a restarted Herdr reports panes before it reports
    the sessions inside them, and without this every claim of the batch would be given
    back and every ticket dispatched a second time over the workers still holding them.
    A ticket whose terminal is still standing keeps its claim; when the machine really
    did lose the run, its panes are gone with it and the release goes ahead. Passing no
    `held` at all reads every claim on its session alone.

    One risk stays here, unsolved on purpose: Herdr answers for this machine and no
    other. A worker of the same account running on a second machine reads from here as
    a claim whose owner is gone. `dispatch.sh` printing a line for every release is
    what makes that case visible instead of silent.
    """
    if not login:
        return []
    held = held or set()
    return [r for r in rows
            if r["state"] == "OPEN"
            and "ready-for-agent" in r["labels"]
            and login in r["assignees"]
            and r["worker"] is None
            and r["ticket"] not in held]


def why_not_on_frontier(row: dict) -> str:
    """Which of `frontier`'s conditions this ticket fails, in that function's order.

    Read only for a ticket already known to be open and in the agent queue, so the
    first two conditions are behind it and the three left are the ones a person cannot
    see from outside this program.
    """
    reasons = []
    if row["blockers"]:
        reasons.append("blocked by " + ", ".join(f"#{b}" for b in row["blockers"]))
    if row["assignees"]:
        reasons.append("claimed by " + ", ".join(row["assignees"]))
    if row["worker"] is not None:
        reasons.append(f"held by the live session {row['worker']['name']}")
    return "; ".join(reasons) or "open, unclaimed, unblocked and unheld: it should have started"


def explain_empty_frontier(rows: list[dict], spec: int) -> None:
    """Say on stderr why nothing can start, one line per ticket still in the queue.

    A frontier that is empty because the batch is finished and a frontier that is empty
    because every ticket is stuck print the same thing — nothing — and what separates
    them is five conditions no reader can see from outside `frontier`. So whenever the
    batch still holds open tickets in the agent queue and none of them can start, each
    of those tickets names the condition holding it.
    """
    queued = [r for r in rows
              if r["state"] == "OPEN" and "ready-for-agent" in r["labels"]]
    if not queued:
        return
    sys.stderr.write(f"board: nothing on #{spec}'s frontier, and {len(queued)} open "
                     "ticket(s) are still in the agent queue:\n")
    for row in queued:
        sys.stderr.write(f"  #{row['ticket']} {why_not_on_frontier(row)}\n")

# --------------------------------------------------------------------- output

COLUMNS = (("ticket", 8), ("agent", 18), ("agent_status", 14),
           ("phase", 19), ("ac", 7), ("turn", 22), ("note", 0))


def render_row(cells: dict) -> str:
    out = []
    for name, width in COLUMNS:
        value = str(cells.get(name, ""))
        out.append(value.ljust(width) if width else value)
    return (" " + "".join(out)).rstrip()


def render_table(rows: list[dict], spec: int | None, now: datetime) -> str:
    head = ["mmw board", now.strftime("%H:%M")]
    if spec:
        head.append(f"spec #{spec}")
    head.append(f"{len(rows)} tickets")
    head.append(f"{len(held(rows))} live")
    lines = [" · ".join(head), ""]
    lines.append(render_row({name: name for name, _ in COLUMNS}))
    for row in rows:
        lines.append(render_row({
            "ticket": f"#{row['ticket']}",
            "agent": row["agent"],
            "agent_status": row["status"],
            "phase": row["phase"],
            "ac": row["ac"],
            "turn": row["turn"],
            "note": row["note"],
        }))
    return "\n".join(lines)


# The file every `say()` line is also appended to, once `--watch` names it. The pane
# the board runs in is closed in the morning, and with it the only other record of
# what the board did.
LOG_FILE: Path | None = None


def say(who: str, action: str, detail: str = "", when: datetime | None = None) -> None:
    """Append one line about one thing that happened. Never redraw, never clear."""
    when = when or datetime.now()
    line = f"{when.strftime('%H:%M:%S')}  {who.ljust(10)}{action.ljust(11)}{detail}".rstrip()
    print(line, flush=True)
    if LOG_FILE is not None:
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with LOG_FILE.open("a", encoding="utf-8") as out:
                out.write(when.strftime("%Y-%m-%d ") + line + "\n")
        except Exception:
            pass

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

# What a worker whose turn failed is sent. One word, because the session is alive and
# still holds everything it has read and written this run: it carries on from where
# it stopped. Naming the skill and the ticket again would send it back in at the
# skill's first step, and that step is `--preflight`, written for a worker that has
# not started — a tree with this run's own uncommitted work in it is refused there.
CONTINUE_LINE = "continue"

# --------------------------------------------------------------------- acting

def main_name() -> str:
    """The Herdr name `dispatch.sh run` gives the main agent's own pane."""
    return name_prefix() + "mmw-main"


# The lines `mmw-main` is sent. Each names the case and the ticket, and what the case
# asks for is the `Find your command` table of this skill's `SKILL.md`. `STOPPED` and
# `TIME LIMIT` name the session too, because the first thing to do with either is to
# read that session's screen. None of them names a script path: the main agent's host
# found the skill wherever it installs skills.
ADVANCE_LINE = ("mmw board: {case} #{spec} — advance spec #{spec} with the "
                "dispatch skill")
STOPPED_LINE = ("mmw board: STOPPED #{n} at phase={phase} — read {name} with herdr, "
                "then move it on with the dispatch skill")
TIME_LIMIT_LINE = ("mmw board: TIME LIMIT #{n} — {hours} h at phase={phase}; read "
                   "{name} with herdr and decide with the dispatch skill")
NIGHT_SUMMARY = "NIGHT SUMMARY {date}"


class Watch:
    """The night's one moving part: a full re-read, then one decision per session.

    It holds no file. What it does keep between rounds is what only it can know — which
    turns it already acted on, when a ticket was first seen held, when a session was
    first seen idle without a `turn` token — and losing that on a restart costs at most
    one repeated line to `mmw-main`. Everything else it can be told again by the
    tracker and by Herdr.
    """

    def __init__(self, spec: int, max_hours: int) -> None:
        self.spec = spec
        self.max_hours = max_hours
        self.held_since: dict[int, float] = {}
        # (pane, turn) pairs already answered with a `continue`, so a token that has not
        # come back round through the snapshot does not earn a second one.
        self.continued: set[tuple[str, str]] = set()
        # `continue`s sent per pane at its current phase: (phase, count).
        self.failures: dict[str, tuple[str, int]] = {}
        # (ticket, turn) pairs already reported to mmw-main as STOPPED.
        self.told: set[tuple[int, str]] = set()
        self.timed_out: set[int] = set()
        # Sessions seen idle with no `turn` token: pane -> (since, comment count, phase).
        self.idle_since: dict[str, tuple[float, int, str]] = {}
        # The frontier the main agent was last told about. It takes it tens of seconds
        # to read the board and run `advance`, and a round goes by faster than that, so
        # without this the same frontier would queue the same line several times over.
        self.announced: set[int] = set()
        self.for_main: list[str] = []
        # Whether the last look for `mmw-main` found nobody. Only so the line saying so
        # is written once rather than every round for as long as it is gone.
        self.main_absent = False
        # The same shape GitHub writes into createdAt and closedAt — UTC, `Z` suffix —
        # so the summary can compare the two as strings.
        self.opened = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.summary_written = False

    # ------------------------------------------------------------- the board's round

    def run(self) -> int:
        global LOG_FILE
        ws = (os.environ.get("HERDR_WORKSPACE_ID") or "").strip().lower() or "none"
        LOG_FILE = LOG_DIR / f"board-{ws}-{self.spec}.log"
        events = Events()
        events.start()
        say("board", "watch", f"spec #{self.spec} max-hours={self.max_hours} log={LOG_FILE}")
        while True:
            try:
                self.round()
            except Exception as problem:
                say("board", "error", str(problem)[:160])
            # Nobody named `mmw-main` at the night's end is the one other way to be
            # finished: the summary is on the spec, and a line nobody can take would
            # otherwise keep this process alive all day.
            if self.summary_written and (not self.for_main or self.main_absent):
                return 0
            events.wait(SNAPSHOT_INTERVAL)

    def round(self) -> None:
        if self.summary_written:
            self.tell_main()
            return
        rows, _ = collect(self.spec)
        for row in rows:
            if row["worker"] and row["worker"]["dispatched"]:
                self.pick_up(row)
        self.tell_main_to_advance(rows)
        if self.nothing_left(rows):
            self.write_summary(rows)
        self.tell_main()

    def pick_up(self, row: dict) -> None:
        worker = row["worker"]
        if worker["phase"] in CLOSED_OR_HANDOFF:
            self.close_its_pane(row)
            return
        self.over_time(row)
        kind = turn_kind(worker["turn"])
        if kind == "failed":
            self.idle_since.pop(worker["pane_id"], None)
            self.turn_failed(row)
        elif kind == "stopped":
            self.idle_since.pop(worker["pane_id"], None)
            self.stopped(row, worker["turn"])
        elif kind == "running":
            self.idle_since.pop(worker["pane_id"], None)
        else:
            self.no_report(row)

    # ------------------------------------------------------------- the three actions

    def close_its_pane(self, row: dict) -> None:
        """`phase` is `closed` or `handoff`: the closing comment is already on the ticket.

        The pane goes, and with it the tab and the `issue-<n>` name. The reader is on
        GitHub, not in Herdr.

        The row loses its worker at the same moment, so the rest of this round already
        reads the ticket as having none, rather than the next round.
        """
        worker = row["worker"]
        say(f"#{row['ticket']}", worker["status"],
            f"phase={worker['phase']}  {row['note']}")
        herdr(["pane", "close", worker["pane_id"]])
        self.held_since.pop(row["ticket"], None)
        self.idle_since.pop(worker["pane_id"], None)
        self.failures.pop(worker["pane_id"], None)
        row["worker"] = None

    def turn_failed(self, row: dict) -> None:
        """`turn=failed:<error>`: the host gave up on the turn after its own retries.

        The session is alive and holds everything it read and wrote, so `continue` is
        the whole repair. Once per turn, and `FAILED_LIMIT` times per phase: a fourth
        failure at the same phase is something to look at, not to retry.
        """
        worker = row["worker"]
        pane = worker["pane_id"]
        key = (pane, worker["turn_id"] or worker["turn"])
        if key in self.continued:
            return
        self.continued.add(key)
        phase, count = self.failures.get(pane, ("", 0))
        if phase != worker["phase"]:
            count = 0
        count += 1
        self.failures[pane] = (worker["phase"], count)
        say(f"#{row['ticket']}", worker["status"],
            f"phase={worker['phase']} {worker['turn']} ({count} of {FAILED_LIMIT})")
        if count > FAILED_LIMIT:
            self.stopped(row, worker["turn"])
            return
        self.send(row, worker, CONTINUE_LINE)

    def stopped(self, row: dict, turn: str) -> None:
        """A turn the session ended itself, short of `closed` or `handoff`.

        Not the board's to answer: it queues one line for `mmw-main`, which reads the
        session's screen and decides. Once per turn.
        """
        worker = row["worker"]
        key = (row["ticket"], worker["turn_id"] or turn)
        if key in self.told:
            return
        self.told.add(key)
        line = STOPPED_LINE.format(n=row["ticket"], phase=worker["phase"] or "-",
                                   name=worker["name"])
        say(f"#{row['ticket']}", worker["status"],
            f"phase={worker['phase']} {turn}; telling mmw-main")
        if line not in self.for_main:
            self.for_main.append(line)

    def no_report(self, row: dict) -> None:
        """No `turn` token: the hooks are not installed, or Herdr restarted and lost it.

        The only reading left is Herdr's own `agent_status`, which is a guess, so it is
        held to `FALLBACK_SECONDS` of idle with nothing new on the ticket before it
        counts — and then it is reported, never answered with `continue`, because a
        session that stopped on purpose would have its reason written over.
        """
        worker = row["worker"]
        pane = worker["pane_id"]
        if worker["status"] not in IDLE_STATUSES:
            self.idle_since.pop(pane, None)
            return
        seen = self.idle_since.get(pane)
        now = time.monotonic()
        if seen is None or seen[1] != row["comment_count"] or seen[2] != worker["phase"]:
            self.idle_since[pane] = (now, row["comment_count"], worker["phase"])
            return
        if now - seen[0] < FALLBACK_SECONDS:
            return
        self.stopped(row, f"idle {FALLBACK_SECONDS}s with no turn report")
        self.idle_since[pane] = (now, row["comment_count"], worker["phase"])

    def over_time(self, row: dict) -> None:
        """Held longer than a ticket may hold a session: tell mmw-main, once.

        The ticket keeps its label, the pane stays open, the session is not touched.
        """
        number = row["ticket"]
        started = self.held_since.setdefault(number, time.monotonic())
        if number in self.timed_out:
            return
        if time.monotonic() - started < self.max_hours * 3600:
            return
        self.timed_out.add(number)
        worker = row["worker"]
        line = TIME_LIMIT_LINE.format(n=number, hours=self.max_hours,
                                      phase=worker["phase"] or "-", name=worker["name"])
        say(f"#{number}", "time limit", f"{self.max_hours} h at phase={worker['phase']}")
        if line not in self.for_main:
            self.for_main.append(line)

    # ------------------------------------------------------------- prompting

    def send(self, row: dict, worker: dict, text: str) -> None:
        """Prompt one session, under the conditions such a prompt has to meet."""
        if not os.environ.get("HERDR_PANE_ID"):
            say("board", "refuse", "no pane of my own, so I may not prompt anyone")
            return
        fresh = unwrap(herdr(["agent", "get", worker["pane_id"]])).get("agent") or {}
        status = fresh.get("agent_status") or "unknown"
        session = (fresh.get("agent_session") or {}).get("value") or ""
        if session and worker["session"] and session != worker["session"]:
            say(f"#{row['ticket']}", "skip", "the pane holds a different session now")
            return
        if fresh.get("focused"):
            say(f"#{row['ticket']}", "hold", "its pane is focused")
            return
        if status == "working":
            say(f"#{row['ticket']}", "hold", "it is working again")
            return
        say(f"#{row['ticket']}", "prompt", text)
        code, reason = herdr_run(["agent", "prompt", worker["pane_id"], text])
        if code != 0:
            say(f"#{row['ticket']}", "refused", reason[:120] or "the prompt was refused")

    # ------------------------------------------------------------- moving on

    def tell_main_to_advance(self, rows: list[dict]) -> None:
        """Say that the frontier has tickets on it. The main agent is the one who acts.

        Sent once per frontier rather than once per round, and again whenever the set
        changes. A ticket that stays on the frontier after the main agent has been told
        is one whose dispatch it already tried and reported on, so saying it again would
        add nothing.

        The line waits in the queue until the main agent is idle enough to take it, and
        what it says is true of the frontier at the moment it was read. A frontier that
        empties in the meantime withdraws the line it queued, together with
        `announced`, so the next non-empty frontier queues one again. Only ever one
        line: `advance` starts every ticket on the frontier, so a second copy behind the
        first runs the same command against what the first one already took.
        """
        line = ADVANCE_LINE.format(case="ADVANCE", spec=self.spec)
        ready = {row["ticket"] for row in frontier(rows)}
        if ready == self.announced:
            return
        self.announced = ready
        if not ready:
            self.for_main = [queued for queued in self.for_main if queued != line]
            return
        say(f"#{self.spec}", "frontier",
            ", ".join(f"#{t}" for t in sorted(ready)))
        if line not in self.for_main:
            self.for_main.append(line)

    # ------------------------------------------------------------- the night's end

    def nothing_left(self, rows: list[dict]) -> bool:
        """Nothing to start and nothing running: an empty frontier, no session of ours.

        A ticket still in the agent queue behind a blocker that was handed back does
        not keep the night open — nothing will start it before the morning. It keeps
        its label, and the summary's `Not dispatched` line names it.
        """
        return not frontier(rows) and not held(rows)

    def write_summary(self, rows: list[dict]) -> None:
        body = self.summary(rows)
        gh(["issue", "comment", str(self.spec), "--body", body])
        say(f"#{self.spec}", "comment", first_line(body))
        self.summary_written = True
        # `advance` and not just a read: the tickets that closed last still have their
        # branches sitting outside the base branch, and this is the last chance to merge
        # them. With nothing left on the frontier it dispatches nothing.
        self.for_main.append(ADVANCE_LINE.format(case="night over", spec=self.spec))

    def summary(self, rows: list[dict]) -> str:
        """Ticket numbers and first lines. What each says is on the ticket itself."""
        closed = [f"#{r['ticket']} {r['head'][:80]}".strip()
                  for r in rows if r["state"] == "CLOSED" and r["closed_at"] > self.opened]
        back = [f"#{r['ticket']} {r['head'][:80]}".strip()
                for r in rows if r["state"] == "OPEN" and "needs-triage" in r["labels"]]
        waiting = [f"#{r['ticket']} blocked by "
                   + ", ".join(f"#{b}" for b in r["blockers"])
                   for r in rows if r["state"] == "OPEN" and r["blockers"]]
        fresh = [f"#{r['ticket']} {r['head'][:80]}".strip()
                 for r in rows if r["created"] > self.opened]
        return "\n".join([
            NIGHT_SUMMARY.format(date=datetime.now().strftime("%Y-%m-%d")),
            "",
            "Closed: " + (", ".join(closed) or "None"),
            "Handed back to needs-triage: " + (", ".join(back) or "None"),
            "Not dispatched, a blocker stayed open: " + (", ".join(waiting) or "None"),
            "Sub-issues opened tonight: " + (", ".join(fresh) or "None"),
        ])

    def tell_main(self) -> None:
        """Re-prompt `mmw-main`, under the same conditions as any other re-prompt.

        It is told, never asked; what each line asks of it is the `Find your command`
        table of `SKILL.md`.

        A line nobody takes waits in the queue, and there being nobody named `mmw-main`
        is that same case: the pane may be back next round. Losing the line would stop
        the night for good, because `tell_main_to_advance` records a frontier before
        queueing the line for it and so never announces that frontier a second time.
        """
        while self.for_main:
            main = self.find_main()
            if main is None:
                if not self.main_absent:
                    self.main_absent = True
                    say(main_name(), "absent",
                        f"nobody is named mmw-main; {len(self.for_main)} line(s) wait")
                return
            if self.main_absent:
                self.main_absent = False
                say(main_name(), "back", f"{len(self.for_main)} line(s) waiting")
            if main["focused"] or main["agent_status"] not in IDLE_STATUSES:
                return
            line = self.for_main[0]
            code, reason = herdr_run(["agent", "prompt", main_name(), line])
            if code != 0:
                say(main_name(), "refused", reason[:120])
                return
            say(main_name(), "prompt", line)
            self.for_main.pop(0)

    def find_main(self) -> dict | None:
        return next((a for a in live_agents() if a.get("name") == main_name()), None)


# --------------------------------------------------------------- the command forms

def collect(spec: int | None) -> tuple[list[dict], list[dict]]:
    """Everything one round needs: the rows, and the live sessions behind them."""
    agents = live_agents()
    sessions_ = sessions(agents)
    numbers = list(sub_issues(spec)) if spec else []
    numbers += [s["ticket"] for s in sessions_]
    tickets = {n: read_ticket(n) for n in sorted(set(numbers))}
    return build_rows(numbers, tickets, sessions_), sessions_


def advance_plan(spec: int) -> int:
    """What the main agent's next `dispatch.sh advance` has to do, in order.

    Three kinds of line and nothing else on stdout, because a script reads this, in the
    order `dispatch.sh` acts on them:

        MERGE <ticket>      closed with `ALL MET`, the one that closed first at the top
        RELEASE <ticket>    in the agent queue and claimed, with neither a live session
                            nor a standing terminal behind the claim: its worker is gone
        DISPATCH <ticket>   on the frontier, in ticket order

    A ticket usually carries a `RELEASE` line and a `DISPATCH` line of the same plan:
    the claim is what kept it off the frontier, and the frontier is read here as it
    stands once `dispatch.sh` has done the releases printed above it, so a ticket freed
    by this plan starts in the same advance rather than the next one.

    The merge order is the order the tickets closed, which is already the order their
    blockers imposed: `--preflight` refuses a ticket whose blocker is open, so none of
    them can have closed before the ones it waited on.

    Whether a branch exists and whether it is already in the base branch are git's
    questions, and git is not one of this program's two sources. `dispatch.sh` asks
    them, and skips what it finds already merged.

    What no line accounts for goes to stderr: an empty frontier with tickets still in
    the agent queue names every one of them and the condition holding it, because
    otherwise it reads exactly like a batch with nothing left to do.
    """
    numbers = sub_issues(spec)
    tickets = {n: read_ticket(n) for n in numbers}
    done = [t for t in tickets.values()
            if t["state"] == "CLOSED"
            and first_line(newest_with_first_line(t, "ALL MET")).startswith("ALL MET")]
    for ticket in sorted(done, key=lambda t: t["closed_at"]):
        print(f"MERGE {ticket['number']}")
    rows = build_rows(numbers, tickets, sessions(live_agents()))
    login = own_login()
    held = terminals_holding(live_panes())
    for row in orphan_claims(rows, login):
        if row["ticket"] in held:
            print(f"#{row['ticket']} keeps its claim: Herdr lists no session on it, but a "
                  f"terminal of this workspace is still standing in issue-{row['ticket']}",
                  file=sys.stderr)
            continue
        print(f"RELEASE {row['ticket']}")
        row["assignees"] = [a for a in row["assignees"] if a != login]
    ready = frontier(rows)
    for row in ready:
        print(f"DISPATCH {row['ticket']}")
    if not ready:
        explain_empty_frontier(rows, spec)
    return 0


def worker_grades(spec: int) -> int:
    """The worker-grade labels of every ticket the night could dispatch.

    One line per ticket that is `OPEN` and labelled `ready-for-agent`, blocked or not:

        GRADE <ticket> [<label> ...]

    The labels are the ticket's own ending in `-worker`, in name order, and a ticket
    carrying none prints the number alone. `dispatch.sh run` reads this before the
    night opens, and refuses the night when a label names a row `models.md` lacks or a
    ticket carries two — the same refusals a dispatch would make, brought to the one
    moment somebody is here to fix them.
    """
    for number in sub_issues(spec):
        ticket = read_ticket(number)
        if ticket["state"] != "OPEN" or "ready-for-agent" not in ticket["labels"]:
            continue
        grades = sorted(l for l in ticket["labels"] if l and l.endswith("-worker"))
        print(" ".join(["GRADE", str(number), *grades]))
    return 0


def once(spec: int | None) -> int:
    rows, _ = collect(spec)
    print(render_table(rows, spec, datetime.now()))
    return 0


def watched_fields(row: dict) -> tuple:
    return (row["status"], row["phase"], row["ac"], row["turn"])


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
        detail = f"phase={row['phase']} ac={row['ac']} turn={row['turn']}"
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
        description="The board over one spec's tickets and their sessions.")
    parser.add_argument("--once", action="store_true",
                        help="print one table and exit")
    parser.add_argument("--watch", action="store_true",
                        help="stay up and act on what it sees")
    parser.add_argument("--advance-plan", action="store_true",
                        help="print what `dispatch.sh advance` has to do, in order")
    parser.add_argument("--worker-grades", action="store_true",
                        help="print the worker-grade labels of every ticket in the agent queue")
    parser.add_argument("--max-hours", type=int, default=MAX_HOURS,
                        help="how long one ticket may hold a session before mmw-main is told")
    parser.add_argument("spec", nargs="?", type=int,
                        help="the spec issue whose sub-issues are tonight's tickets")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.advance_plan:
        if not args.spec:
            sys.stderr.write("board: --advance-plan needs the spec whose batch to read\n")
            return 2
        return advance_plan(args.spec)
    if args.worker_grades:
        if not args.spec:
            sys.stderr.write("board: --worker-grades needs the spec whose batch to read\n")
            return 2
        return worker_grades(args.spec)
    if args.once:
        return once(args.spec)
    if args.watch:
        if not args.spec:
            sys.stderr.write("board: --watch needs the spec whose tickets to work\n")
            return 2
        return Watch(args.spec, args.max_hours).run()
    return resident(args.spec)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
