#!/usr/bin/env python3
"""The night board: one view of every ticket under a spec and every session on one.

    board.py --once [<spec>]        print one table and exit
    board.py [<spec>]               stay up, append one line per event
    board.py --watch <spec>         the same, and act on what it sees
    board.py --advance-plan <spec>  what `dispatch.sh advance` has to do, in order

One program, several forms, reading the same two sources, so there is never a second
truth to reconcile. `--once` is what an agent runs when it wants the whole picture in
one screen. The argument-less form is what a person leaves open in a tab: it appends,
never redraws, and never enters the alternate screen, so its lines stay in the host's
scrollback where `herdr pane read` can still reach them. `--watch` is the one form that
does anything: it re-prompts a session that is `idle` with a `phase` other than `closed`
or `handoff`, redispatches one whose session is gone, and hands back the tickets that
reached a limit. Nothing it does needs a model, because the only thing it ever says to a
worker is that worker's own dispatch line.

What it does not do is dispatch. Moving the batch on is the main agent's: when the
frontier grows, `--watch` tells `mmw-main` to run `dispatch.sh advance`, which merges
the branches of the tickets that closed and then starts the ones that can start. Repair
is the board's, the next step is the main agent's, and the line between them is that a
repair puts a session that was already dispatched back on its feet.

One board covers one Herdr workspace. Sessions in another workspace belong to another
board and are not read, not counted and not touched.

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
from datetime import datetime, timezone

# --------------------------------------------------------------------- constants

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


def form_text(screen: str) -> str:
    """The form out of a screen that also holds whatever scrolled above it.

    A question or approval form is drawn at the foot of the viewport, so the last few
    non-empty lines are the form and everything before them is the turn that led to it.
    """
    lines = [l.strip() for l in (screen or "").splitlines() if l.strip()]
    return " ".join(lines[-FORM_LINES:])


def herdr_text(args: list[str]) -> str:
    """A Herdr call whose answer is a pane's own text rather than JSON."""
    try:
        run = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=30)
        return run.stdout if run.returncode == 0 else ""
    except Exception:
        return ""


def run_dispatch(number: int, kind: str) -> tuple[int, str, str]:
    """`dispatch.sh <n> <kind>`: its exit code is a row of the table all by itself."""
    run = subprocess.run(["bash", DISPATCH, str(number), kind],
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
    rows = gh_json(["api", f"repos/{{owner}}/{{repo}}/issues/{spec}/sub_issues"], [])
    return [int(r["number"]) for r in rows if isinstance(r, dict) and r.get("number")]


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


# The three summary lines gate-check prints, one of which is the second line of every
# `self-run` and `reverify` comment. Each stops at its own numbers rather than at the
# closing bracket, because the bracket may also hold the reverify counts or a scope.
ALL_MET_RE = re.compile(r"^ALL MET\s*\((\d+)\s+met\b")
UNMET_RE = re.compile(r"^UNMET:\s*(\d+)\s*\(met:\s*(\d+)\b")
HANDOFF_RE = re.compile(
    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(met:\s*(\d+)"
    r"(?:,\s*unmet:\s*(\d+))?")

# The two first lines a worker's closing comment can carry.
CLOSING_LINES = ("ALL MET", "HANDOFF REQUIRED")


def has_closing_comment(ticket: dict) -> bool:
    """Whether a worker ever left a closing comment on this ticket, of either kind."""
    return any(first_line(c).startswith(CLOSING_LINES) for c in ticket.get("comments") or [])


def redispatch_count(ticket: dict) -> int:
    """How many times a session on this ticket has already been redispatched.

    Counted off the ticket's own `REDISPATCHED:` comments, the way the three self-run
    rounds are counted off its `self-run` comments, so nothing is stored between rounds.
    """
    return sum(1 for c in ticket.get("comments") or []
               if first_line(c).startswith("REDISPATCHED:"))


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
        "wake": int(tokens["wake"]) if str(tokens.get("wake", "")).isdigit() else 0,
        "model": tokens.get("model") or "",
        "host": agent.get("agent") or "",
        "workspace": agent.get("workspace_id") or "",
    }


def sessions(agents: list[dict]) -> list[dict]:
    """The sessions of this workspace, and no others.

    Several boards run at once, one per workspace, and every one of them sees every
    pane on the server. Without this a board would re-prompt, close and hand back the
    sessions of a batch it knows nothing about. A server that reports no workspace for
    this process leaves every session in, which is the one-board case.
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

    Almost nothing the board does reaches it: a reviewer that dies or runs long is the
    worker's own `dispatch.sh wait` to time out, and the ticket is never handed back
    over one. A form on its screen is the exception, because the worker waiting on it
    only reads the ticket — it presses no key — so the round is lost to a timeout that
    one keystroke would have prevented.
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
            "wake": str(worker["wake"]) if worker else "-",
            "note": note_of(ticket, worker),
            "head": last_first_line(ticket),
            "closing_comment": has_closing_comment(ticket),
            "redispatches": redispatch_count(ticket),
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

# What a session that is `idle` with a `phase` other than `closed` or `handoff` is sent,
# and what a session gets after its question form is dismissed. One word, because the
# session is alive and still holds everything it has read and written this run: it
# carries on from where it stopped. Naming the skill and the ticket again would send it
# back in at the skill's first step, and that step is a gate written for a worker that
# has not started — a tree with this run's own uncommitted work in it is refused there.
CONTINUE_LINE = "continue"

# --------------------------------------------------------------------- acting

# Herdr is what recognises a question or approval form. This is only which key puts it
# away, which every host spells its own way; anything else is sent `esc`.
CLOSE_KEYS = {"grok": "shift+x", "cursor": "esc"}
CLOSE_KEY_OTHERWISE = "esc"
FORM_CHARS = 500                # enough of the form to read it in the morning
FORM_LINES = 20                 # a form sits at the foot of the screen, above nothing

def main_name() -> str:
    """The Herdr name `dispatch.sh run` gives the main agent's own pane."""
    return name_prefix() + "mmw-main"


# Two lines, because the two say different things. A limit was reached and the board has
# already commented and relabelled, so there is nothing to do but read. The frontier
# grew, or the night is over with branches still unmerged, so there is a step to take.
#
# Both name the skill rather than a script path. The main agent's host found that skill
# wherever it installs skills, and the row it lands on carries the command, its exit
# codes and what to do with each — none of which fits on a line sent to a pane.
MAIN_LINE = ("mmw board: {case} #{n} — read spec #{spec} with the dispatch skill")
ADVANCE_LINE = ("mmw board: {case} #{spec} — advance spec #{spec} with the "
                "dispatch skill")

BLOCKED = "BLOCKED: {form}"
# Same first line, because everything that reads these comments keys on it, and a second
# line naming who asked, because the morning reader is looking at one ticket and the two
# sessions on it want different things.
BLOCKED_REVIEWER = "BLOCKED: the reviewer on this ticket asked:\n\n{form}"
REDISPATCHED = "REDISPATCHED: session {name} ended at phase={phase}; started again"
REDISPATCH_SPENT = ("REDISPATCHED: session {name} ended at phase={phase} and it had "
                    "already been redispatched {k} time(s). Handed back to "
                    "needs-triage; the ticket stays open.")
WAKEUP_LIMIT = ("WAKEUP LIMIT: re-prompted {k} times and it went idle again at "
                "phase={phase}. Handed back to needs-triage; the ticket stays open.")
WAKEUP_LIMIT_FORM = ("WAKEUP LIMIT: dismissed {k} forms and it asked again at "
                     "phase={phase}. Handed back to needs-triage; the ticket stays "
                     "open.")
TIME_LIMIT = ("TIME LIMIT: {hours} h under this board, still at phase={phase}. Handed "
              "back to needs-triage; the session was left alone.")
NIGHT_SUMMARY = "NIGHT SUMMARY {date}"


class Watch:
    """The night's one moving part: a full re-read, then the table of §4, then dispatch.

    It holds no file. What it does keep between rounds is what only it can know — when
    a session was first seen settled, and when it may next be prompted — and losing
    that on a restart costs one cooldown, nothing more. Everything else it can be told
    again by the tracker and by Herdr.
    """

    def __init__(self, spec: int, max_hours: int) -> None:
        self.spec = spec
        self.max_hours = max_hours
        self.settled_since: dict[str, float] = {}
        self.held_since: dict[int, float] = {}
        self.wakes: dict[str, int] = {}
        self.handed_back: set[int] = set()
        # Panes of reviewers that used up their dismissals, so the line saying so is
        # written once instead of every time the backoff elapses.
        self.reviewers_spent: set[str] = set()
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

    # ------------------------------------------------------------- the round

    def run(self) -> int:
        events = Events()
        events.start()
        say("board", "watch", f"spec #{self.spec} max-hours={self.max_hours}")
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
            if self.gone(row):
                self.redispatch(row)
            elif row["worker"] and row["worker"]["dispatched"]:
                self.pick_up(row)
            # Independent of the worker's own row: the two sessions on a ticket can be
            # at a form at the same time, and a reviewer at one has no other rescuer.
            if row["reviewer"] and row["reviewer"]["status"] == "blocked":
                self.at_a_form(row, row["reviewer"])
        self.tell_main_to_advance(rows)
        if self.nothing_left(rows):
            self.write_summary(rows)
        self.tell_main()

    def pick_up(self, row: dict) -> None:
        worker = row["worker"]
        if self.over_time(row):
            return
        if worker["status"] == "blocked":
            self.at_a_form(row, worker)
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

        The row loses its worker at the same moment, so the place this session held is
        free to the rest of this round rather than to the next one.
        """
        worker = row["worker"]
        say(f"#{row['ticket']}", worker["status"],
            f"phase={worker['phase']}  {row['note']}")
        herdr(["pane", "close", worker["pane_id"]])
        self.settled_since.pop(worker["pane_id"], None)
        self.held_since.pop(row["ticket"], None)
        row["worker"] = None

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
            self.hand_back(row, WAKEUP_LIMIT.format(k=WAKE_LIMIT, phase=worker["phase"]),
                           case="WAKEUP LIMIT")
            return
        self.send(row, row["worker"], CONTINUE_LINE)

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
                       case="TIME LIMIT", close_pane=False)
        return True

    def at_a_form(self, row: dict, session: dict) -> None:
        """`blocked`: a question or approval form is on screen and the discipline is
        not to ask.

        The form goes on the ticket so a person can read in the morning what was wanted,
        then it is dismissed with the host's own key and the session is told to continue.
        Board never answers a form: sending text into one selects an option rather than
        typing an answer.

        A worker and a reviewer are repaired the same way and part company only at the
        limit. A worker out of dismissals takes its ticket back to `needs-triage`,
        because without a worker the ticket does not move. A reviewer out of dismissals
        is left where it stands: `dispatch.sh wait` times out, `implement` skips that
        round, and a dead reviewer is no reason to hand the ticket to a person.
        """
        pane = session["pane_id"]
        wake = self.prompts_so_far(session)
        last = self.settled_since.get(pane)
        if last is not None and time.monotonic() - last < WAKE_BACKOFF[
                min(wake, len(WAKE_BACKOFF) - 1)]:
            return
        if wake >= WAKE_LIMIT:
            if session["kind"] != "worker":
                if pane not in self.reviewers_spent:
                    self.reviewers_spent.add(pane)
                    say(f"#{row['ticket']}", "reviewer",
                        f"asked again after {WAKE_LIMIT} forms; left for the worker's "
                        f"wait to time out")
                return
            self.hand_back(row, WAKEUP_LIMIT_FORM.format(k=WAKE_LIMIT,
                                                         phase=session["phase"]),
                           case="WAKEUP LIMIT")
            return
        form = form_text(herdr_text(
            ["agent", "read", pane, "--source", "visible", "--lines", "60"]))
        shape = BLOCKED if session["kind"] == "worker" else BLOCKED_REVIEWER
        gh(["issue", "comment", str(row["ticket"]),
            "--body", shape.format(form=form[:FORM_CHARS] or "(nothing on screen)")])
        say(f"#{row['ticket']}", "comment", f"BLOCKED: {form[:80]}")
        # grok answers to its own key; every other host takes the fallback, claude
        # included — its question form reports `blocked` with no detection rule of its
        # own, and `esc` puts it away, both driven on a real machine.
        key = CLOSE_KEYS.get(session["host"], CLOSE_KEY_OTHERWISE)
        herdr(["agent", "send-keys", pane, key])
        herdr(["agent", "wait", pane, "--until", "idle", "--until", "done",
               "--timeout", "15000"])
        say(f"#{row['ticket']}", key, "form dismissed")
        self.settled_since[pane] = time.monotonic()
        self.send(row, session, CONTINUE_LINE)

    # ------------------------------------------------------------- the session is gone

    def gone(self, row: dict) -> bool:
        """`unknown`, or the pane is gone, while the ticket is still open and unclosed.

        A ticket nobody ever claimed was never dispatched, so its missing pane is not a
        session that died; the assignee the start-of-work guard sets is what tells the
        two apart.
        """
        if row["state"] != "OPEN" or "ready-for-agent" not in row["labels"]:
            return False
        if row["closing_comment"] or row["ticket"] in self.handed_back:
            return False
        worker = row["worker"]
        if worker and worker["dispatched"]:
            return worker["status"] == "unknown"
        return bool(row["assignees"])

    def redispatch(self, row: dict) -> None:
        number, worker = row["ticket"], row["worker"]
        phase = (worker or {}).get("phase") or "unknown"
        if row["redispatches"] >= REDISPATCH_LIMIT:
            self.hand_back(row, REDISPATCH_SPENT.format(name=worker_name(number),
                                                        phase=phase,
                                                        k=row["redispatches"]),
                           case="REDISPATCHED")
            return
        gh(["issue", "comment", str(number),
            "--body", REDISPATCHED.format(name=worker_name(number), phase=phase)])
        say(f"#{number}", "comment", f"REDISPATCHED: ended at phase={phase}")
        if worker:
            herdr(["pane", "close", worker["pane_id"]])
            self.settled_since.pop(worker["pane_id"], None)
            self.wakes.pop(worker["pane_id"], None)
        self.held_since.pop(number, None)
        self.start(number)

    # ------------------------------------------------------------- prompting

    def send(self, row: dict, session: dict, text: str) -> None:
        """Prompt one session, under the seven conditions such a prompt has to meet."""
        worker = session
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

    def hand_back(self, row: dict, body: str, case: str,
                  close_pane: bool = True) -> None:
        number = row["ticket"]
        if number in self.handed_back:
            return
        self.handed_back.add(number)
        self.for_main.append(MAIN_LINE.format(case=case, n=number, spec=self.spec))
        say(f"#{number}", "comment", first_line(body))
        gh(["issue", "comment", str(number), "--body", body])
        gh(["issue", "edit", str(number),
            "--remove-label", "ready-for-agent", "--add-label", "needs-triage"])
        say(f"#{number}", "label", "needs-triage")
        if close_pane and row["worker"]:
            herdr(["pane", "close", row["worker"]["pane_id"]])
            self.settled_since.pop(row["worker"]["pane_id"], None)
            self.held_since.pop(number, None)
            # Same as at either exit: the place is free from here on, not next round.
            row["worker"] = None

    # ------------------------------------------------------------- moving on

    def tell_main_to_advance(self, rows: list[dict]) -> None:
        """Say that the frontier has tickets on it. The main agent is the one who acts.

        Sent once per frontier rather than once per round, and again whenever the set
        changes. A ticket that stays on the frontier after the main agent has been told
        is one whose dispatch it already tried and reported on, so saying it again would
        add nothing.

        The line waits in the queue until the main agent is idle enough to take it, and
        what it says is true of the frontier at the moment it was read. A frontier this
        board empties in the meantime — by repairing a session and starting that ticket
        itself — withdraws the line it queued, together with `announced`, so the next
        non-empty frontier queues one again. Only ever one line: `advance` starts every
        ticket on the frontier, so a second copy behind the first runs the same command
        against what the first one already took.
        """
        line = ADVANCE_LINE.format(case="ADVANCE", spec=self.spec)
        ready = {row["ticket"] for row in frontier(rows)
                 if row["ticket"] not in self.handed_back}
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

    def start(self, number: int) -> bool:
        """Start one worker. Returns whether a session now occupies one of the places.

        Exit 1 means a session is up in that pane but was never told anything: it
        occupies a place, and the next round finds it `idle` with no `phase` and sends
        it its dispatch line. Exit 2 means the ticket did not qualify, so it simply is
        not on this round's frontier and the next round asks the tracker again.
        """
        code, told, refused = run_dispatch(number, "worker")
        if code == 0:
            say(f"#{number}", "dispatch", told[:120])
            self.held_since[number] = time.monotonic()
            return True
        if code == 1:
            say(f"#{number}", "dispatch", f"up but not told: {refused[:100]}")
            self.held_since[number] = time.monotonic()
            return True
        say(f"#{number}", "not dispatched", refused[:120])
        return False

    # ------------------------------------------------------------- the night's end

    def nothing_left(self, rows: list[dict]) -> bool:
        """No open ticket in the agent lane, and no session of ours still alive."""
        lane = [r for r in rows
                if r["state"] == "OPEN" and "ready-for-agent" in r["labels"]]
        return not lane and not held(rows)

    def write_summary(self, rows: list[dict]) -> None:
        body = self.summary(rows)
        gh(["issue", "comment", str(self.spec), "--body", body])
        say(f"#{self.spec}", "comment", first_line(body))
        self.summary_written = True
        # `advance` and not just a read: the tickets that closed last still have their
        # branches sitting outside the main branch, and this is the last chance to merge
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

        Only two cases ever reach it: a limit was reached, or the night ended. It is
        told, never asked; it answers by running `board.py --once` and reading.

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


# --------------------------------------------------------------------- the forms

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

    Two kinds of line and nothing else on stdout, because a script reads this:

        MERGE <ticket>      closed with `ALL MET`, the one that closed first at the top
        DISPATCH <ticket>   on the frontier, in ticket order

    The merge order is the order the tickets closed, which is already the order their
    blockers imposed: the start-of-work guard refuses a ticket whose blocker is open, so
    none of them can have closed before the ones it waited on.

    Whether a branch exists and whether it is already in the main branch are git's
    questions, and git is not one of this program's two sources. `dispatch.sh` asks
    them, and skips what it finds already merged.
    """
    numbers = sub_issues(spec)
    tickets = {n: read_ticket(n) for n in numbers}
    done = [t for t in tickets.values()
            if t["state"] == "CLOSED"
            and first_line(newest_with_first_line(t, "ALL MET")).startswith("ALL MET")]
    for ticket in sorted(done, key=lambda t: t["closed_at"]):
        print(f"MERGE {ticket['number']}")
    rows = build_rows(numbers, tickets, sessions(live_agents()))
    for row in frontier(rows):
        print(f"DISPATCH {row['ticket']}")
    return 0


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
    parser.add_argument("--advance-plan", action="store_true",
                        help="print what `dispatch.sh advance` has to do, in order")
    parser.add_argument("--max-hours", type=int, default=MAX_HOURS,
                        help="how long one ticket may hold a session")
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
