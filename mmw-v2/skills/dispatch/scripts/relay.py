#!/usr/bin/env python3
"""The relay: events on the board in, wake-ups for the session waiting on them out.

    relay.py start --repo O/R (--spec N | --tickets N[,N...]) --runner R --session S [--interval S] [--grace S]
    relay.py add --repo O/R (--spec N | --tickets N[,N...]) --runner R --session S
    relay.py stop --repo O/R [--spec N | --tickets N[,N...]]
    relay.py watching --repo O/R [--ticket N] [--spec S]
    relay.py run --repo O/R [--once] [--interval S] [--grace S]
    relay.py ack --repo O/R --runner R --session S (--through SEQ | --ticket N --event E | --event relay.recovered)
    relay.py queue --repo O/R [--runner R --session S]

**A translator, not a board.** The relay does one thing: when a comment carrying one of
the events in `WAKES` lands on a ticket it watches, it writes one row into the wake queue
("wake session S about ticket N, event E") and hands that row to the runner that runs
session S. It does not know what a spec, a frontier, a phase or a blocker is, and it
decides nothing: whether to advance, resume, retract or stop belongs to the main agent,
which reads the board to decide it (docs/adr/0009-night-orchestration-on-paseo.md). It is
not `board.py`, the modelless night watcher that ADR removed because it decided on the
main agent's behalf. That one judged; this one translates.

**It never writes to GitHub.** Its only calls to the tracker are `gh api` reads of issue
comments and sub-issues; its only writes are files in this repository's state directory
on this machine (statedir.py). Tickets are written by the scripts that write them and by
nothing else (docs/adr/0001-tracker-repo-authority.md).

**Watches.** What the relay reads is the union of its watches. A watch is what one
`dispatch.sh open`, `open-ticket` or `adopt` opens: `{"spec": N}`, a night — N's
sub-issues, listed again every cycle — or `{"tickets": [n, ...]}`, tickets outside a
night. Each watch has its own main agent, a (runner, session) pair: the session that
opened it. Nothing names a main agent but the watch it opened; there is no registration
apart from a watch. A repository has one relay process and one state directory however many
watches are open, so nights run from several branches or worktrees, one-ticket runs and
adopted tickets all go through the same process. Two watches never share a ticket: a
tickets watch naming a sub-issue of a watched spec, or a spec one of whose sub-issues a
tickets watch names, is refused, since that ticket's wakes would have two main agents. A
ticket that comes to sit under a watched spec after both were opened stays with its
tickets watch.

**Who is woken.** The session waiting on the event, which `WAKES` names by role:

    worker   reviewer.reported, verifier.passed, verifier.failed, and reviewer.lost or
             verifier.lost (that reviewer or verifier died with no result): the session
             that started that reviewer or verifier. Its runner and session are the
             `runner` and `session` fields of the ticket's latest `worker.started` before
             the event. And worker.queued, when a product slot is given back (below)
    main     ticket.passed, ticket.returned, ticket.refused, child.opened of kind fault
             (the pipeline itself broken) or decision, worker.lost: the main agent of the
             ticket's watch. The relay's own relay.recovered: every watch's main agent

A worker needs no registration: the ticket says who it is. Each row is written with its
recipient's runner and session, and only that recipient — the pair, never the session
id alone — consumes it.

**A slot given back.** A run of the criteria that finds no free product slot posts
`worker.queued` and exits, and nothing on its own ticket will ever wake it. So the relay
keeps, per watched ticket, whether a `worker.queued` is pending: set by one, cleared by
exactly the events that clear the fold's `waiting` in events.py — a `ticket.checked`, any
event of `ENDS_EVERY_HOLD`, the worker's result (`RESULTS["worker"]`), and an event of
`ENDS_ONE_HOLD` other than `reviewer.lost` and `verifier.lost`. When an event of
`SLOT_ENDS` that gives a slot back lands on any watched ticket (all of them but
`spec.suspended`, which stops the night), every watched ticket whose pending
`worker.queued` is older — a lower comment id — gets one row `#<m> worker.queued` for its
worker: the latest `worker.started` of that ticket before the releasing comment. The row
is keyed by the releasing comment and the woken ticket, so a re-read never queues it
twice. Slots are counted per machine, not per watch, so a waiting ticket of any watch is
woken. A poll's events are taken in comment-id order across all its tickets, so an older
wait and a newer release meet in the order they happened. The flag is kept in `seen.json`
and recomputed by the full read on start. The woken worker runs its criteria again and
acks the wake like any other.

**Reading the board.** Every `--interval` seconds (default 30) the relay reads the
comments of each watched ticket updated since the newest one it saw there, less two
minutes of overlap, and records every (comment, event) pair it has translated, so the
overlap never queues one twice. On start it reads every watched ticket in full, not since
anything: a relay that was down does not get to assume it missed nothing. So is a ticket
the first time a watch brings it in. A ticket whose read fails is reported on stderr,
keeps its old mark and is read again next cycle, and a cycle with a failed read is never
recorded as a good poll (docs/adr/0008-silence-is-never-a-pass.md).

**A row's life.** Queued: `seq` (monotonic across all recipients, never reused, even after
the queue empties), `ticket`, `event`, `to` (worker or main), `watch` (the key of the
watch its ticket belongs to; none on relay.recovered), the recipient's `runner` and
`session`, `at`. Delivered: the relay ran `runners/<runner>.sh send <session> "#<ticket>
<event>"` — the text carries the ticket number and the event name and nothing else; what
happened is read on the board. What `send` answered decides what happens to the row:

    0                 delivered; the row stays until it is acked
    4                 handed over and not confirmed: the text reached the session and
                      no turn start was seen. Delivered all the same (`unconfirmed` on
                      the row): typing it again every cycle would bury the session in
                      copies. Like any delivered row it stays until acked, and is sent
                      once more only when the relay restarts
    3                 nothing was sent: the recipient is in a turn, or its runner could
                      not be asked; the row stays and is sent again next cycle
    2                 the runner has no such session: a late delivery to a retired
                      session; the row is dropped
    anything else     the send could not be run or did not answer; the row stays

A row that is no longer its recipient's is dropped without a send, for the same reason
as a 2: its watch was closed; its watch's main agent is now another session (the watch
was opened again from a new session); a later `worker.started` put another worker on the
ticket; or, for relay.recovered, its recipient is the main agent of no watch any more.
Every drop is reported on stderr. A recipient's rows reach it in sequence order: after
one of them stays, that recipient gets nothing more this pass, and the other recipients
are not held up by it. Delivery never removes a row: only `ack --runner R --session S
--through <seq>` does, and it removes that recipient's rows up to that sequence number
whatever their content, and nobody else's. So a row sent twice — every unacked row is
sent once more each time the relay starts — is still handled once. A woken session knows
the wake it read, not its sequence number, so `ack --ticket N --event E` names the wake
instead: it acks through the recipient's oldest delivered row naming that ticket and event
(the oldest queued one when none is marked delivered), and `--event relay.recovered` does
the same for the announcement. Only that recipient's rows are looked at: an ack that
matches none of them — acked already, sent to another session, or never queued — is
refused, naming what it looked for and what is queued for that recipient, and removes
nothing.

**Opening a watch.** `start` checks first and writes after. It refuses when there is no
adapter for the runner, when that runner's `liveness` says the session is `stopped`
(every wake-up sent to it would be dropped), or when the watch overlaps another (the
sub-issues of the specs involved are read from the board for that; a read that fails is
a refusal too). Only when every check passes is the watch written with its main agent,
under the queue lock. Opening a watch that is open already replaces that watch's main
agent — a main agent replaced by a new session — and never touches another watch's.
Then, when no relay runs for the repository, it starts `run` as a process of its own
session, detached from the caller, with its output appended to `relay.log`, and returns
once that process holds `relay.lock`: a caller's turn ending does not end the relay. A
relay that does not come up has the watch this call opened closed again. When a relay
runs, `start` only records the watch, and that process reads it on its next cycle. `add`
is `start` without the process: the checks and the write.

**Closing a watch.** `stop --spec N` or `--tickets N` closes that watch and its main
agent; with none named it closes every watch. When no watch is left it ends the process
with SIGTERM and forgets the last good poll: the night was closed on purpose, and the time
until the next start is nobody's unattended stretch. Closing a watch that is not open
changes nothing. `watching` says whether a running relay would see a ticket's events: a
tickets watch names the ticket, or a spec watch is the ticket's spec; with `--spec`
alone, whether that spec is watched.

**A main agent that is gone.** A night whose main agent's session was closed without
`summary` or `suspend` would otherwise be polled for ever, a few thousand REST requests an
hour. Every 10 cycles the relay asks each watch's main agent's runner `liveness`. A main
agent answered `stopped` at every ask for 3600 seconds or more has its watch closed as
`stop` would close it, with a line in `relay.log`; `alive` or `unknown` starts the count
again. The hour lets the reviewers and verifiers still at work bring their results back
to their workers first, and the next `open` reads everything in full. The relay exits
when no watch is left.

**An unattended stretch** is time with no good poll: the relay was down, or its reads kept
failing. Time spent in delivery passes is not part of it: a slow send delays the next poll,
and the relay was attending all the while. When the time since the last good poll, less
the time spent delivering, exceeds `--grace` seconds (default three intervals), the next
good poll queues one `relay.recovered` row to each watch's main agent (one per session,
however many watches it opened) for the whole stretch, ahead of the events it recovered:
one announcement per stretch, never one per missed event. A stretch is named by the time
of the last good poll before it — its generation — and `gap.json` records the latest one
announced; a stretch already announced is never announced again, whatever became of its
rows. Consuming rows goes by sequence number and announcing a stretch goes by generation;
neither touches the other.

Files in the state directory:

    queue.jsonl     the rows, one JSON object per line, in sequence order
    queue.seq       the last sequence number issued
    queue.lock      taken for every read-and-write of the files below it
    seen.json       per ticket: (comment, event) pairs translated, newest updated_at,
                    every worker.started as [comment id, runner, session], the pending
                    worker.queued (`waiting`: its comment id, or null) and the newest
                    comment id applied to that flag (`waiting_read`)
    watches.json    every open watch, keyed `spec:<n>` or `tickets:<n>[,<n>...]`: the
                    watch (`spec` or `tickets`), its main agent's `runner` and `session`,
                    when it was opened (`at`), and since when that runner has answered
                    `stopped` (`stopped_since`, null while it has not). It outlives the
                    process: a relay that died leaves its watches open
    relay.json      the running relay's pid, process identity, interval, grace, start
                    time, and `ending` once it has no watch left and is on its way out
    relay.log       what every started relay printed, appended
    beat.json       the last good poll, seconds spent delivering since it, the pass under way,
                    the last failed poll and why, the run's interval and grace
    gap.json        the latest unattended stretch announced
    relay.lock      held for as long as a `run` runs: one relay per repository

Exit codes:

    start     0 the watch is recorded and a relay runs (started now, or already); 1
              refused (no adapter, the runner says the session is stopped, the watch
              overlaps another, the board could not be read to check that, the relay
              running is one whose `relay.json` names a single `watch` and reads no
              watches.json, a state file unreadable, the relay exited or did not take its
              lock: its log's last lines are on stderr, and a watch this call opened was
              closed again)
    add       0 recorded; 1 refused, as for start
    stop      0 done: that watch is closed, and the process ended with the last watch (or
              nothing was watched); 1 the process did not end; 3 that watch is not open,
              and nothing was changed
    watching  0 a running relay watches that ticket, or that spec; 1 none does (stderr
              says why)
    run       0 --once read every watched ticket, or the last watch was closed; 3 --once
              could not read at least one; 1 refused (nothing is watched, another relay is
              running, a state file unreadable)
    ack       0 acked; 1 refused (a sequence number that was never issued, a wake with no
              row queued for that runner and session)
    queue     0 rows printed and a relay polled within its grace; 3 rows printed, but no
              relay is running or its last good poll is older than its grace

`start` and `add` print `opened the watch on <watch> for <repo>: wake-ups go to <runner>
session <session>` for a watch that was not open, or `reopened ...` for one that was
(`, was <runner> session <session>` when its main agent changed); `start` then prints
`relay started for <repo>: pid <pid>, watching <watches>, log <path>` or `relay already
running for <repo>: pid <pid>, watching <watches>`. `stop` prints `stopped the relay for
<repo>: pid <pid>, watching <watches closed>` when the process ended, `stopped watching
<watch> for <repo>: ...` when other watches remain or no process ran, and `no relay is
running for <repo>` when nothing was watched.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import statedir  # noqa: E402
from statedir import LockHeld  # noqa: E402


def _load_events():
    """`events.py` of the verify-ticket skill, beside this one: the one reader of the
    comment format. `MMW_EVENTS_PY` names it when `dispatch.sh` resolved it elsewhere."""
    default = HERE.parents[1] / "verify-ticket" / "scripts" / "events.py"
    path = Path(os.environ.get("MMW_EVENTS_PY") or default)
    if not path.is_file():
        sys.stderr.write(f"relay: no events.py at {path}; the verify-ticket skill has to sit "
                         f"beside this one, or MMW_EVENTS_PY has to name its events.py\n")
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location("mmw_events", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = _load_events()

RUNNERS = HERE / "runners"
DEFAULT_INTERVAL = 30
OVERLAP = timedelta(seconds=120)
QUEUE_WAIT = 10.0
SEND_TIMEOUT = 180
# How long one `gh` read of the board may take before it counts as failed.
GH_TIMEOUT = 120
# How long one adapter's `liveness` may take before its answer counts as unknown.
LIVENESS_TIMEOUT = 60
START_WAIT = 15.0
STOP_WAIT = 15.0
# Every this many cycles the relay asks each watch's main agent's runner whether it lives,
MAIN_CHECK_EVERY = 10
# and closes the watch of one answered `stopped` at every ask for this many seconds.
MAIN_GONE_AFTER = 3600

MAIN = "main"
WORKER = "worker"

# Which events wake whom. `to` is the role of the session woken; `when`, where present,
# lists the payload values the event must carry for it to wake anyone.
WAKES: dict[str, dict] = {
    "reviewer.reported": {"to": WORKER},
    "verifier.passed": {"to": WORKER},
    "verifier.failed": {"to": WORKER},
    "reviewer.lost": {"to": WORKER},
    "verifier.lost": {"to": WORKER},
    "ticket.passed": {"to": MAIN},
    "ticket.returned": {"to": MAIN},
    "ticket.refused": {"to": MAIN},
    "child.opened": {"to": MAIN, "when": {"kind": ("fault", "decision")}},
    "worker.lost": {"to": MAIN},
}

# The event that says which session is a ticket's worker.
WORKER_STARTED = "worker.started"

# The event a run posts when it waits for a product slot, and the wake its worker gets
# when one is given back.
QUEUED = "worker.queued"

# The one row the relay writes about itself rather than about a ticket.
RECOVERED = "relay.recovered"

LIVENESS_ANSWERS = ("alive", "stopped", "unknown")


class Refusal(RuntimeError):
    """A command that will not do what it was asked; the message names the fact and the way out."""


class PollError(RuntimeError):
    """A read of the board that could not be made."""


class UnreadableEvent(ValueError):
    """A comment with an mmw block that is not a usable version-1 event."""


# ----------------------------------------------------------------- time

def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


# ----------------------------------------------------------------- the comment format

def read_event(body: str) -> dict | None:
    """The event one comment carries, as its payload, or None when it carries none.

    The comment format is read by `events.parse` and nowhere else in the pipeline: the
    hidden `<!-- mmw {...} -->` block that ends an event comment, checked against the
    event table. The comment's first line is prose for people and is never read. A block
    that is there but cannot be read raises UnreadableEvent: a comment that looks like an
    event and cannot be read is a different answer from a comment with no event.
    """
    what, value = events.parse(body or "")
    if what == "none":
        return None
    if what == "unreadable":
        raise UnreadableEvent(value)
    return value


def woken_by(event: dict) -> str | None:
    """The role this event wakes (`WAKES`), or None when it wakes nobody."""
    rule = WAKES.get(event.get("event"))
    if rule is None:
        return None
    for field, allowed in (rule.get("when") or {}).items():
        if event.get(field) not in allowed:
            return None
    return rule["to"]


def ends_waiting(name: str) -> bool:
    """Whether this event ends a run's wait for a product slot: the events that clear the
    fold's `waiting` in events.py. A lost reviewer or verifier ends only its own hold, and
    the worker's run is still waiting."""
    return (name == "ticket.checked" or name in events.ENDS_EVERY_HOLD
            or name in events.RESULTS["worker"]
            or (name in events.ENDS_ONE_HOLD and name not in ("reviewer.lost", "verifier.lost")))


def gives_slot_back(name: str) -> bool:
    """Whether this event gives a product slot back to the machine. `spec.suspended` gives
    its slots back too, and stops the night with them: nobody waits on it."""
    return name in events.SLOT_ENDS and name != "spec.suspended"


def wake_text(row: dict) -> str:
    """What is sent: the ticket number and the event name, nothing the board already says."""
    if row.get("event") == RECOVERED:
        return f"{RECOVERED} since {row.get('since')}"
    return f"#{row.get('ticket')} {row.get('event')}"


# ----------------------------------------------------------------- watches

def watch_key(watch: dict) -> str:
    """The name a watch is kept under: `spec:<n>`, or `tickets:<n>[,<n>...]` in order."""
    if watch.get("spec"):
        return f"spec:{int(watch['spec'])}"
    return "tickets:" + ",".join(str(n) for n in sorted({int(n) for n in watch.get("tickets") or []}))


def watch_from_key(key: str) -> dict:
    kind, _, numbers = (key or "").partition(":")
    if kind == "spec":
        return {"spec": int(numbers)}
    return {"tickets": [int(n) for n in numbers.split(",") if n]}


def describe_watch(watch: dict | None) -> str:
    if not watch:
        return "nothing"
    if watch.get("spec"):
        return f"spec #{watch['spec']}"
    tickets = watch.get("tickets") or []
    return ("tickets " if len(tickets) > 1 else "ticket ") + ", ".join(f"#{n}" for n in tickets)


def describe_watches(watches: dict) -> str:
    return " and ".join(describe_watch(w) for _, w in sorted(watches.items())) or "nothing"


def watch_of(args) -> dict | None:
    if getattr(args, "spec", None):
        return {"spec": args.spec}
    if getattr(args, "tickets", None):
        return {"tickets": sorted(set(args.tickets))}
    return None


def read_watches(state: Path) -> dict[str, dict]:
    """The open watches of a state directory, by key: each a watch (`spec` or `tickets`)
    with its main agent's `runner` and `session`. An entry without a main agent is no
    watch. Raises ValueError when `watches.json` is there and is not JSON."""
    data = statedir.read_json(Path(state) / "watches.json", {})
    out: dict[str, dict] = {}
    for key, entry in (data.items() if isinstance(data, dict) else []):
        if not isinstance(entry, dict) or not entry.get("runner") or not entry.get("session"):
            continue
        if not entry.get("spec") and not entry.get("tickets"):
            continue
        out[key] = entry
    return out


def main_of(entry: dict) -> tuple[str, str]:
    return entry["runner"], entry["session"]


def overlap(want: dict, watches: dict[str, dict], children: dict[int, list[int]]) -> str | None:
    """Why `want` shares a ticket with another open watch, or None. `children` holds the
    sub-issues of every spec the comparison needs."""
    key = watch_key(want)
    for other_key, other in sorted(watches.items()):
        if other_key == key:
            continue
        whose = f"{other['runner']} session {other['session']}"
        if want.get("tickets"):
            mine = set(want["tickets"])
            if other.get("tickets"):
                shared = sorted(mine & set(other["tickets"]))
                if shared:
                    return (f"#{shared[0]} is already watched as {describe_watch(other)}, whose "
                            f"main agent is {whose}")
            else:
                shared = sorted(mine & set(children.get(int(other["spec"]), [])))
                if shared:
                    return (f"#{shared[0]} is a sub-issue of spec #{other['spec']}, which is "
                            f"watched with {whose} as its main agent")
        elif other.get("tickets"):
            shared = sorted(set(children.get(int(want["spec"]), [])) & set(other["tickets"]))
            if shared:
                return (f"its sub-issue #{shared[0]} is already watched as "
                        f"{describe_watch(other)}, whose main agent is {whose}")
    return None


# ----------------------------------------------------------------- reading the board

def quiet_env() -> dict:
    """The environment without the colour forcing some hosts inject: `gh` writes ANSI
    escapes into its JSON under CLICOLOR_FORCE, and no JSON reader can parse them."""
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    return env


def gh_list(args: list[str]) -> list:
    """Run `gh` and read its answer as a list, pages flattened. Raises PollError otherwise."""
    try:
        run = subprocess.run(["gh", *args], capture_output=True, text=True,
                             env=quiet_env(), timeout=GH_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PollError(f"gh could not be run: {exc}") from None
    if run.returncode != 0:
        said = " ".join((run.stderr or run.stdout or "").split())[:300]
        raise PollError(f"gh exited {run.returncode}: {said or 'nothing on stderr'}")
    try:
        data = json.loads(run.stdout)
    except ValueError:
        raise PollError("gh answered with something that is not JSON") from None
    if not isinstance(data, list):
        raise PollError("gh answered with JSON that is not a list")
    # `--slurp` answers with one list per page; a single page answered flat is read too.
    flat: list = []
    for page in data:
        flat.extend(page if isinstance(page, list) else [page])
    return flat


class Board:
    """The tracker, read-only: comments of one issue, and the sub-issues of one issue."""

    def __init__(self, repo: str, gh: Callable[[list[str]], list] = gh_list):
        self.repo = repo
        self.gh = gh

    def comments(self, ticket: int, since: str | None) -> list[dict]:
        url = f"repos/{self.repo}/issues/{ticket}/comments?per_page=100"
        if since:
            url += f"&since={since}"
        return [c for c in self.gh(["api", "--paginate", "--slurp", url]) if isinstance(c, dict)]

    def children(self, number: int) -> list[tuple[int, str]]:
        """Each sub-issue of `number` as (number, state): the state lower case, `open` or
        `closed` as the REST answer gives it, empty when the answer carries none."""
        rows = self.gh(["api", "--paginate", "--slurp",
                        f"repos/{self.repo}/issues/{number}/sub_issues?per_page=100"])
        return [(int(r["number"]), str(r.get("state") or "").lower())
                for r in rows if isinstance(r, dict) and r.get("number")]

    def sub_issues(self, number: int) -> list[int]:
        return [n for n, _ in self.children(number)]


# ----------------------------------------------------------------- the runner

def adapter_path(runner: str) -> Path:
    return RUNNERS / f"{runner}.sh"


# What `send_via_adapter` answers when the adapter itself gave no answer: it is not an
# adapter's exit code, so the row is kept and sent again.
NOT_SENT = 5


def send_via_adapter(runner: str, session: str, text: str) -> int:
    """`runners/<runner>.sh send <session> <text>`; its exit code. A send that could not be
    run, or did not answer in time, is NOT_SENT: the adapter said nothing, not 4."""
    adapter = adapter_path(runner)
    if not adapter.is_file():
        sys.stderr.write(f"relay: no runner adapter at {adapter}; nothing was sent\n")
        return NOT_SENT
    try:
        run = subprocess.run(["bash", str(adapter), "send", session, text],
                             capture_output=True, text=True, env=quiet_env(),
                             timeout=SEND_TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"relay: {runner}.sh send did not answer within {SEND_TIMEOUT}s\n")
        return NOT_SENT
    except OSError as exc:
        sys.stderr.write(f"relay: {runner}.sh send could not be run: {exc}\n")
        return NOT_SENT
    for line in (run.stderr or "").splitlines():
        if line.strip():
            sys.stderr.write(f"relay: {runner}.sh: {line}\n")
    return run.returncode


def ask_liveness(runner: str, session: str) -> str:
    """`runners/<runner>.sh liveness <session>`: alive, stopped or unknown. Anything the
    adapter did not answer in so many words — no adapter, a non-zero exit, a timeout,
    other output — is unknown, never alive and never stopped."""
    adapter = adapter_path(runner)
    if not runner or not adapter.is_file():
        return "unknown"
    try:
        run = subprocess.run(["bash", str(adapter), "liveness", session], capture_output=True,
                             text=True, env=quiet_env(), timeout=LIVENESS_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    answer = (run.stdout or "").strip()
    return answer if run.returncode == 0 and answer in LIVENESS_ANSWERS else "unknown"


# ----------------------------------------------------------------- the relay

def _slot(per_ticket: dict, ticket: int) -> dict:
    slot = per_ticket.setdefault(str(ticket), {})
    slot.setdefault("keys", [])
    slot.setdefault("mark", None)
    slot.setdefault("workers", [])
    slot.setdefault("waiting", None)
    slot.setdefault("waiting_read", 0)
    return slot


class Relay:
    """The queue, the watches, the recipients and the marks for one repository's state
    directory."""

    def __init__(self, state: Path, board: Board | None = None,
                 send: Callable[[str, str, str], int] = send_via_adapter,
                 clock: Callable[[], datetime] = now_utc,
                 ask: Callable[[str, str], str] = ask_liveness,
                 out=None, err=None):
        self.state = Path(state)
        self.board = board
        self.send = send
        self.clock = clock
        self.ask = ask
        self.out = out or sys.stdout
        self.err = err or sys.stderr
        # Tickets read in full since this process started: the rest are read since their mark.
        self.reconciled: set[int] = set()
        self.cycles = 0

    # ------------------------------------------------------------- files

    def path(self, name: str) -> Path:
        return self.state / name

    def queue_lock(self):
        return statedir.locked(self.path("queue.lock"), wait=QUEUE_WAIT, purpose="wake queue")

    def _read_state(self, name: str, default):
        try:
            return statedir.read_json(self.path(name), default)
        except ValueError as exc:
            raise Refusal(f"{self.path(name)} is not JSON ({exc}); the relay cannot tell what it "
                          f"holds. Move that file aside and start the relay again: it reads "
                          f"every watched ticket in full on start.") from None

    def _rows(self) -> list[dict]:
        try:
            text = self.path("queue.jsonl").read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        rows = []
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                raise Refusal(f"line {number} of {self.path('queue.jsonl')} is not JSON; the "
                              f"queue cannot be read past it. Remove that line and run the "
                              f"command again.") from None
            if not isinstance(row, dict) or not isinstance(row.get("seq"), int):
                raise Refusal(f"line {number} of {self.path('queue.jsonl')} is not a row with a "
                              f"sequence number. Remove that line and run the command again.")
            rows.append(row)
        return rows

    def _write_rows(self, rows: list[dict]) -> None:
        text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in sorted(rows, key=lambda r: r["seq"]))
        statedir.write_atomic(self.path("queue.jsonl"), text)

    def _last_seq(self, rows: list[dict]) -> int:
        try:
            recorded = int(self.path("queue.seq").read_text(encoding="utf-8").strip() or 0)
        except FileNotFoundError:
            recorded = 0
        except ValueError:
            raise Refusal(f"{self.path('queue.seq')} does not hold a number. Write into it the "
                          f"highest seq in {self.path('queue.jsonl')}, or 0 when that is empty, "
                          f"and run the command again.") from None
        return max([recorded] + [r["seq"] for r in rows])

    # ------------------------------------------------------------- watches

    def watches(self) -> dict[str, dict]:
        """Every open watch, by key. `watches.json` is replaced in one step, so it is read
        without the lock; every change to it is made under the lock."""
        try:
            return read_watches(self.state)
        except ValueError as exc:
            raise Refusal(f"{self.path('watches.json')} is not JSON ({exc}); which watches are "
                          f"open, and whose wake-ups go where, cannot be told. Move that file "
                          f"aside and open each watch again (dispatch.sh open, open-ticket or "
                          f"adopt).") from None

    def _write_watches(self, watches: dict[str, dict]) -> None:
        statedir.write_atomic(self.path("watches.json"),
                              json.dumps(watches, sort_keys=True, indent=1) + "\n")

    def _relay_record(self) -> dict:
        try:
            record = statedir.read_json(self.path("relay.json"), {})
        except ValueError:
            return {}
        return record if isinstance(record, dict) else {}

    def _mark_ending(self) -> None:
        """Say in the running relay's record that it has no watch left and is leaving, so a
        `start` that comes now starts another instead of counting on this one."""
        record = self._relay_record()
        if record:
            record["ending"] = True
            statedir.write_atomic(self.path("relay.json"), json.dumps(record, sort_keys=True) + "\n")

    def _forget_last_poll(self) -> None:
        """No watch is left: the time until the next start is nobody's unattended stretch,
        and no `relay.recovered` is announced for a closed night. The next relay reads
        every ticket in full on start all the same."""
        beat = self._read_state("beat.json", {})
        if beat:
            beat.update(at=None, delivering=0, delivery_started=None, stopped=iso(self.clock()))
            statedir.write_atomic(self.path("beat.json"), json.dumps(beat, sort_keys=True) + "\n")

    def _children_for(self, want: dict, watches: dict[str, dict]) -> dict[int, list[int]]:
        """The sub-issues of every spec the overlap check of `want` needs, from the board."""
        key = watch_key(want)
        if want.get("tickets"):
            specs = [int(w["spec"]) for k, w in watches.items() if k != key and w.get("spec")]
        elif any(w.get("tickets") for k, w in watches.items() if k != key):
            specs = [int(want["spec"])]
        else:
            specs = []
        children: dict[int, list[int]] = {}
        for spec in specs:
            try:
                children[spec] = self.board.sub_issues(spec)
            except PollError as exc:
                raise Refusal(f"could not read the sub-issues of spec #{spec}, so whether "
                              f"{describe_watch(want)} shares a ticket with another watch is "
                              f"not known: {exc}. Nothing was recorded; run it again once the "
                              f"tracker answers.") from None
        return children

    def open_watch(self, want: dict, runner: str, session: str) -> tuple[dict | None, dict]:
        """Record `want` with (runner, session) as its main agent, unless it shares a ticket
        with another open watch. Opening a watch that is open replaces its main agent and
        nothing else. Returns (the entry replaced, or None for a new watch; the running
        relay's record as it stood when the watch was written)."""
        key = watch_key(want)
        for _ in range(3):
            before = self.watches()
            children = self._children_for(want, before)
            with self.queue_lock():
                watches = self.watches()
                # A watch opened or closed while the board was read: check against that.
                if set(watches) != set(before):
                    continue
                problem = overlap(want, watches, children)
                if problem:
                    raise Refusal(f"{describe_watch(want)} was not opened: {problem}. A ticket "
                                  f"is watched once, so that its wake-ups have one main agent. "
                                  f"Close that watch first (land for one ticket, summary or "
                                  f"suspend for a night), or work the ticket in the watch that "
                                  f"has it. Nothing was recorded.")
                previous = watches.get(key)
                watches[key] = {**want, "runner": runner, "session": session,
                                "at": iso(self.clock()), "stopped_since": None}
                self._write_watches(watches)
                return previous, self._relay_record()
        raise Refusal("the open watches kept changing while this one was checked against them; "
                      "run it again.")

    def restore_watch(self, key: str, previous: dict | None) -> None:
        """Put watch `key` back as it was before `open_watch`: gone when it was new."""
        with self.queue_lock():
            watches = self.watches()
            if previous is None:
                watches.pop(key, None)
            else:
                watches[key] = previous
            self._write_watches(watches)

    def close_watch(self, key: str | None) -> tuple[dict[str, dict], dict[str, dict]]:
        """Close the watch `key`, or every watch when it is None. Returns (the watches
        closed, the watches left). When none is left, the running relay's record says it is
        ending and the last good poll is forgotten."""
        with self.queue_lock():
            watches = self.watches()
            closed = {k: v for k, v in watches.items() if key is None or k == key}
            left = {k: v for k, v in watches.items() if k not in closed}
            if closed:
                self._write_watches(left)
            if not left:
                self._mark_ending()
                self._forget_last_poll()
        return closed, left

    def leave_if_unwatched(self) -> bool:
        """True, with the record marked ending, when no watch is left for this relay."""
        with self.queue_lock():
            if self.watches():
                return False
            self._mark_ending()
            return True

    def check_mains(self) -> None:
        """Ask each watch's main agent's runner whether it lives, and close the watch of one
        answered `stopped` at every ask for MAIN_GONE_AFTER seconds or more."""
        answers: dict[tuple[str, str], str] = {}
        for entry in self.watches().values():
            address = main_of(entry)
            if address not in answers:
                answers[address] = self.ask(*address)
        now = self.clock()
        gone: list[tuple[str, dict]] = []
        with self.queue_lock():
            watches = self.watches()
            changed = False
            for key, entry in sorted(watches.items()):
                answer = answers.get(main_of(entry))
                if answer is None:
                    continue  # opened, or given another main agent, while the runners were asked
                if answer != "stopped":
                    if entry.get("stopped_since"):
                        entry["stopped_since"] = None
                        changed = True
                    continue
                try:
                    since = parse_iso(entry["stopped_since"]) if entry.get("stopped_since") else None
                except ValueError:
                    since = None
                if since is None:
                    entry["stopped_since"] = iso(now)
                    changed = True
                elif (now - since).total_seconds() >= MAIN_GONE_AFTER:
                    gone.append((key, entry))
            for key, _ in gone:
                del watches[key]
                changed = True
            if changed:
                self._write_watches(watches)
            if gone and not watches:
                self._mark_ending()
                self._forget_last_poll()
        for _, entry in gone:
            self.out.write(f"closed the watch on {describe_watch(entry)}: {entry['runner']} has "
                           f"answered that its main agent, session {entry['session']}, is "
                           f"stopped at every ask since {entry['stopped_since']}, "
                           f"{MAIN_GONE_AFTER}s or more, so its wake-ups have nobody to go to\n")
        if gone and not watches:
            self.out.write("no watch is left, and the relay ends\n")
        self.out.flush()

    @staticmethod
    def _worker_before(per_ticket: dict, ticket, cid: int | None) -> tuple[str, str] | None:
        """The (runner, session) of the ticket's latest worker.started before comment `cid`;
        with `cid` None, its latest worker.started of all."""
        entries = (per_ticket.get(str(ticket)) or {}).get("workers") or []
        earlier = [e for e in entries if cid is None or e[0] < cid]
        if not earlier:
            return None
        _, runner, session = max(earlier, key=lambda e: e[0])
        return runner, session

    # ------------------------------------------------------------- reading the queue

    def rows(self, address: tuple[str, str] | None = None) -> list[dict]:
        """Every row, or the rows of one recipient, named by its (runner, session)."""
        with self.queue_lock():
            rows = self._rows()
        return [r for r in rows if address is None or (r.get("runner"), r.get("session")) == address]

    def ack(self, address: tuple[str, str], through: int) -> tuple[int, int]:
        """Remove the rows of recipient `address` (runner, session) with seq <= through.
        Returns (removed, left for that recipient)."""
        runner, session = address
        with self.queue_lock():
            rows = self._rows()
            last = self._last_seq(rows)
            if through > last:
                raise Refusal(f"no row with sequence {through} was ever issued; the last one is "
                              f"{last}. Acking past it would remove rows nobody has read. Run "
                              f"`relay.py queue --runner {runner} --session {session}` and ack "
                              f"through the highest seq it printed.")

            def mine(row: dict) -> bool:
                return (row.get("runner"), row.get("session")) == address

            keep = [r for r in rows if not (mine(r) and r["seq"] <= through)]
            if len(keep) != len(rows):
                self._write_rows(keep)
            return len(rows) - len(keep), sum(1 for r in keep if mine(r))

    def ack_wake(self, address: tuple[str, str], ticket: int | None, event: str) -> tuple[int, int, int] | None:
        """Ack the wake `address` read, named as it was sent: ticket and event, or the
        announcement `relay.recovered`. Acks through that recipient's oldest delivered row
        naming it, or its oldest queued one when none is marked delivered. Returns
        (through, removed, left for that recipient), or None when no such row is queued
        for it."""
        def names_it(row: dict) -> bool:
            if (row.get("runner"), row.get("session")) != address or row.get("event") != event:
                return False
            return event == RECOVERED or row.get("ticket") == ticket

        with self.queue_lock():
            hits = [r for r in self._rows() if names_it(r)]
        if not hits:
            return None
        delivered = [r for r in hits if r.get("delivered")]
        through = min(r["seq"] for r in (delivered or hits))
        removed, left = self.ack(address, through)
        return through, removed, left

    # ------------------------------------------------------------- polling

    def cycle(self, interval: int, grace: int) -> bool:
        """One cycle of `run`: poll, deliver, and every MAIN_CHECK_EVERY cycles ask after
        the main agents. True when every read was made."""
        self.cycles += 1
        good = self.poll(interval, grace)
        self.deliver()
        if self.cycles % MAIN_CHECK_EVERY == 0:
            self.check_mains()
        return good

    def _watched_tickets(self, watches: dict[str, dict], failures: list[str]) -> dict[int, str]:
        """Every watched ticket and the key of the watch it belongs to. Tickets watches are
        taken first: a ticket one names stays its, whatever spec it later sits under."""
        tickets: dict[int, str] = {}
        ordered = sorted(watches.items(), key=lambda kv: (0 if kv[1].get("tickets") else 1, kv[0]))
        for key, entry in ordered:
            if entry.get("tickets"):
                numbers = entry["tickets"]
            else:
                try:
                    numbers = self.board.sub_issues(int(entry["spec"]))
                except PollError as exc:
                    failures.append(f"the tickets of spec #{entry['spec']}: {exc}")
                    continue
            for number in numbers:
                tickets.setdefault(int(number), key)
        return tickets

    def poll(self, interval: int, grace: int) -> bool:
        """Read the watched tickets and queue what they carry. True when every read was made."""
        watches = self.watches()
        if not watches:
            return True
        started = self.clock()
        failures: list[str] = []
        tickets = self._watched_tickets(watches, failures)
        with self.queue_lock():
            marks = {k: v.get("mark") for k, v in self._read_state("seen.json", {}).get("tickets", {}).items()}

        # Everything that happened, to be taken in the order it landed: the wakes, and what
        # makes a ticket wait for a product slot, stop waiting, or give a slot back.
        timeline: list[dict] = []
        workers: list[tuple[int, int, str, str]] = []
        unreadable: list[tuple[int, object, str]] = []
        read: dict[int, str | None] = {}
        for number, key in tickets.items():
            mark = marks.get(str(number))
            since = None
            if number in self.reconciled and mark:
                since = iso(parse_iso(mark) - OVERLAP)
            try:
                comments = self.board.comments(number, since)
            except PollError as exc:
                failures.append(f"#{number}: {exc}")
                continue
            newest = mark or ""
            for comment in sorted(comments, key=lambda c: c.get("id") or 0):
                newest = max(newest, comment.get("updated_at") or "")
                cid = comment.get("id") or 0
                try:
                    event = read_event(comment.get("body") or "")
                except UnreadableEvent as exc:
                    unreadable.append((number, cid, str(exc)))
                    continue
                if event is None:
                    continue
                name = event["event"]
                ticket = event.get("ticket") if isinstance(event.get("ticket"), int) else number
                if name == WORKER_STARTED:
                    runner, session = event.get("runner"), event.get("session")
                    if isinstance(runner, str) and runner and isinstance(session, str) and session:
                        workers.append((ticket, cid, runner, session))
                    else:
                        unreadable.append((number, cid, "its worker.started names no runner and session"))
                    continue
                if name == QUEUED or ends_waiting(name) or gives_slot_back(name):
                    timeline.append({"slot": True, "cid": cid, "home": number, "event": name})
                role = woken_by(event)
                if role is None:
                    continue
                timeline.append({"key": f"{cid}:{name}", "cid": cid, "home": number,
                                 "ticket": ticket, "event": name, "to": role, "watch": key})
            read[number] = newest or None

        now = self.clock()
        added: list[dict] = []
        unaddressed: list[dict] = []
        reported: list[tuple[int, object, str]] = []
        with self.queue_lock():
            # Read here, under the lock every change to them is made under: a main agent
            # replaced while the board was read addresses these rows, not the one before it.
            watches = self.watches()
            seen = self._read_state("seen.json", {})
            per_ticket = seen.setdefault("tickets", {})
            for ticket, cid, runner, session in workers:
                slot = _slot(per_ticket, ticket)
                if all(entry[0] != cid for entry in slot["workers"]):
                    slot["workers"].append([cid, runner, session])
                    slot["workers"].sort()
            # A ticket read in full has its wait for a slot recomputed from its whole history.
            for number in read:
                if number not in self.reconciled:
                    _slot(per_ticket, number).update(waiting=None, waiting_read=0)
            rows = self._rows()
            queued = {r.get("key") for r in rows}
            already = {k for entry in per_ticket.values() for k in entry.get("keys", [])}

            beat = self._read_state("beat.json", {})
            gap = self._read_state("gap.json", {})
            last_good = beat.get("at")
            new_gap = None
            if not failures and last_good and self._unattended(beat, now) > grace \
                    and gap.get("since") != last_good:
                for address in sorted({main_of(e) for e in watches.values()}):
                    key = f"gap:{last_good}:{address[0]}:{address[1]}"
                    if key in queued:
                        continue
                    added.append({"key": key, "home": None, "ticket": None, "event": RECOVERED,
                                  "to": MAIN, "watch": None, "runner": address[0],
                                  "session": address[1], "since": last_good})
                if added:
                    new_gap = {"generation": int(gap.get("generation") or 0) + 1,
                               "since": last_good, "until": iso(now)}
            # Comment ids rise across the whole repository, so this is the order the events landed in.
            for item in sorted(timeline, key=lambda f: (f["cid"], 0 if f.get("slot") else 1)):
                if item.get("slot"):
                    self._slot_event(item, per_ticket, tickets, queued, already, added, unaddressed)
                    continue
                if item["key"] in already or item["key"] in queued:
                    continue
                if item["to"] == MAIN:
                    entry = watches.get(item["watch"])
                    address = main_of(entry) if entry else None
                else:
                    address = self._worker_before(per_ticket, item["ticket"], item["cid"])
                if address is None:
                    unaddressed.append(item)
                    continue
                item["runner"], item["session"] = address
                queued.add(item["key"])
                added.append(item)

            seq = self._last_seq(rows)
            for row in added:
                seq += 1
                row.update(seq=seq, at=iso(now), delivered=None)
            if added:
                statedir.write_atomic(self.path("queue.seq"), f"{seq}\n")
                self._write_rows(rows + [{k: v for k, v in r.items() if k not in ("home", "cid")}
                                         for r in added])
            if new_gap:
                new_gap["seq"] = added[0]["seq"]
                statedir.write_atomic(self.path("gap.json"), json.dumps(new_gap, sort_keys=True) + "\n")

            for number, newest in read.items():
                slot = _slot(per_ticket, number)
                if newest:
                    slot["mark"] = newest
            for row in added:
                if row.get("home") is not None:
                    _slot(per_ticket, row["home"])["keys"].append(row["key"])
            # A comment the relay could not translate, or a wake-up with nobody to go to, is
            # reported the first time it is seen and not again.
            problems = [(n, cid, f"{cid}:reported", why) for n, cid, why in unreadable]
            for item in unaddressed:
                if item.get("slot"):
                    woken = item["woken"]
                    problems.append((woken, item["cid"], f"{item['cid']}:reported",
                                     f"it gives a product slot back and #{woken} waits for one, "
                                     f"and no worker.started on #{woken} comes before it, so "
                                     f"there is no session to wake"))
                elif item["to"] == MAIN:
                    problems.append((item["home"], item["cid"], f"{item['cid']}:reported",
                                     f"it wakes the main agent of "
                                     f"{describe_watch(watch_from_key(item['watch']))}, and that "
                                     f"watch was closed"))
                else:
                    problems.append((item["home"], item["cid"], f"{item['cid']}:reported",
                                     f"it wakes #{item['ticket']}'s worker, and no "
                                     f"worker.started on #{item['ticket']} comes before it, so "
                                     f"there is no session to wake"))
            for number, cid, key, why in problems:
                slot = _slot(per_ticket, number)
                if key not in slot["keys"]:
                    slot["keys"].append(key)
                    reported.append((number, cid, why))
            statedir.write_atomic(self.path("seen.json"), json.dumps(seen, sort_keys=True, indent=1) + "\n")

            if failures:
                beat.update(failed_at=iso(now), failure="; ".join(failures))
            else:
                beat.update(at=iso(now), delivering=0, failed_at=None, failure=None)
            beat.update(interval=interval, grace=grace)
            statedir.write_atomic(self.path("beat.json"), json.dumps(beat, sort_keys=True) + "\n")

        self.reconciled.update(read)
        for row in added:
            self.out.write(f"queued {row['seq']} {wake_text(row)} for {row['to']} {row['session']}\n")
        for number, cid, why in reported:
            self.err.write(f"relay: comment {cid} on #{number} was not translated: {why}. "
                           f"Read it on the ticket; the relay will not report it again.\n")
        for failure in failures:
            self.err.write(f"relay: could not read {failure}. That is not the same as no new "
                           f"events: the ticket keeps its mark and is read again next cycle, and "
                           f"this cycle is not recorded as a good poll (started {iso(started)}).\n")
        self.out.flush()
        return not failures

    def _slot_event(self, item: dict, per_ticket: dict, tickets: dict[int, str],
                    queued: set, already: set, added: list[dict], unaddressed: list[dict]) -> None:
        """One event that starts or ends its ticket's wait for a product slot, or gives a
        slot back. A ticket's wait moves only on events newer than the last one applied to
        it, so the overlap of an incremental read never brings back a wait that ended."""
        cid, name = item["cid"], item["event"]
        slot = _slot(per_ticket, item["home"])
        if cid > (slot.get("waiting_read") or 0):
            if name == QUEUED:
                slot["waiting"] = cid
            elif ends_waiting(name):
                slot["waiting"] = None
            slot["waiting_read"] = cid
        if not gives_slot_back(name):
            return
        for number in sorted(tickets):
            waiting = (per_ticket.get(str(number)) or {}).get("waiting")
            if not waiting or waiting >= cid:
                continue
            key = f"slot:{cid}:{number}"
            if key in already or key in queued:
                continue
            address = self._worker_before(per_ticket, number, cid)
            if address is None:
                unaddressed.append({"slot": True, "cid": cid, "woken": number})
                continue
            queued.add(key)
            added.append({"key": key, "cid": cid, "home": number, "ticket": number,
                          "event": QUEUED, "to": WORKER, "watch": tickets[number],
                          "runner": address[0], "session": address[1]})

    # ------------------------------------------------------------- delivering

    def forget_deliveries(self) -> None:
        """Mark every row undelivered, so each unacked row is sent once more."""
        with self.queue_lock():
            rows = self._rows()
            if any(r.get("delivered") for r in rows):
                for row in rows:
                    row["delivered"] = None
                self._write_rows(rows)

    def _settle(self, seq: int, delivered: str | None = None, drop: bool = False,
                unconfirmed: bool = False) -> bool:
        """Mark row `seq` delivered, or drop it. False when it is no longer queued (acked)."""
        with self.queue_lock():
            rows = self._rows()
            hit = [r for r in rows if r["seq"] == seq]
            if not hit:
                return False
            if drop:
                rows = [r for r in rows if r["seq"] != seq]
            else:
                hit[0]["delivered"] = delivered
                if unconfirmed:
                    hit[0]["unconfirmed"] = True
            self._write_rows(rows)
            return True

    def _drop(self, row: dict, why: str) -> None:
        if self._settle(row["seq"], drop=True):
            self.err.write(f"relay: dropped row {row['seq']} ({wake_text(row)} for {row.get('to')} "
                           f"{row.get('session')}): {why}\n")
            self.out.write(f"dropped {row['seq']} {wake_text(row)}\n")

    @staticmethod
    def _unattended(beat: dict, now: datetime) -> float:
        """Seconds since the last good poll that the relay spent neither delivering nor able
        to poll: down, or its reads failing. Time in delivery passes does not count — a slow
        send delays the next poll, and nobody was unattended while it ran."""
        last = beat.get("at")
        if not last:
            return 0.0
        spent = float(beat.get("delivering") or 0)
        if beat.get("delivery_started"):
            spent += max(0.0, (now - parse_iso(beat["delivery_started"])).total_seconds())
        return (now - parse_iso(last)).total_seconds() - spent

    def _note_delivery(self, begun: datetime, ended: datetime | None) -> None:
        """Record a delivery pass in beat.json: its start while it runs, its length after."""
        with self.queue_lock():
            beat = self._read_state("beat.json", {})
            if ended is None:
                beat["delivery_started"] = iso(begun)
            else:
                beat["delivery_started"] = None
                beat["delivering"] = float(beat.get("delivering") or 0) + (ended - begun).total_seconds()
            statedir.write_atomic(self.path("beat.json"), json.dumps(beat, sort_keys=True) + "\n")

    def deliver(self) -> None:
        """One pass over the undelivered rows, in sequence order, each to its own recipient."""
        with self.queue_lock():
            pending = [r for r in self._rows() if not r.get("delivered")]
        if not pending:
            return
        begun = self.clock()
        self._note_delivery(begun, None)
        try:
            self._deliver(pending)
        finally:
            self._note_delivery(begun, self.clock())

    def _recipient_now(self, row: dict, watches: dict[str, dict], per_ticket: dict) -> tuple[str, str | None]:
        """Whether `row` is still its recipient's: ("send", None); ("drop", why); or
        ("keep", why) when there is nobody to compare it with."""
        address = (row.get("runner"), row.get("session"))
        watch = row.get("watch")
        if watch is not None and watch not in watches:
            return "drop", (f"it belongs to the watch on {describe_watch(watch_from_key(watch))}, "
                            f"which was closed")
        if row.get("to") == WORKER:
            current = self._worker_before(per_ticket, row.get("ticket"), None)
            if current is None:
                return "keep", f"there is no #{row.get('ticket')}'s worker to compare it with"
            whose = f"#{row.get('ticket')}'s worker"
        elif watch is not None:
            current = main_of(watches[watch])
            whose = f"the main agent of {describe_watch(watches[watch])}"
        elif address in {main_of(e) for e in watches.values()}:
            return "send", None
        else:
            return "drop", (f"it is addressed to {address[0]} session {address[1]}, the main "
                            f"agent of no open watch: a late message for a retired session")
        if address != current:
            return "drop", (f"it is addressed to {address[0]} session {address[1]}, and {whose} "
                            f"is now {current[0]} session {current[1]}: a late message for a "
                            f"retired session")
        return "send", None

    def _deliver(self, pending: list[dict]) -> None:
        watches = self.watches()
        with self.queue_lock():
            per_ticket = self._read_state("seen.json", {}).get("tickets", {})
        held: set[tuple[str, str]] = set()
        for row in pending:
            address = (row.get("runner"), row.get("session"))
            verdict, why = self._recipient_now(row, watches, per_ticket)
            if verdict == "keep":
                self.err.write(f"relay: kept row {row['seq']} ({wake_text(row)}): {why}\n")
                continue
            if verdict == "drop":
                self._drop(row, why)
                continue
            if address in held:
                continue
            code = self.send(address[0], address[1], wake_text(row))
            if code == 0:
                if self._settle(row["seq"], delivered=iso(self.clock())):
                    self.out.write(f"delivered {row['seq']} {wake_text(row)} to {address[1]}\n")
            elif code == 4:
                # Handed over and not confirmed. Marked delivered, so it is not typed into
                # the session again every cycle; it is sent once more on a restart, like
                # every unacked row.
                held.add(address)
                if self._settle(row["seq"], delivered=iso(self.clock()), unconfirmed=True):
                    self.out.write(f"delivered {row['seq']} {wake_text(row)} to {address[1]}, "
                                   f"unconfirmed: {address[0]} took it and saw no turn start\n")
            elif code == 2:
                self._drop(row, f"{address[0]} has no session {address[1]}: a late message for a "
                                f"retired session")
            elif code == 3:
                held.add(address)
                self.out.write(f"kept {row['seq']} {wake_text(row)}: {address[1]} is in a turn\n")
            else:
                held.add(address)
                self.err.write(f"relay: kept row {row['seq']} ({wake_text(row)}): {address[0]}.sh "
                               f"send answered {code}, which says it was not sent; it is sent "
                               f"again next cycle\n")
        self.out.flush()

    # ------------------------------------------------------------- health

    def health(self) -> str | None:
        """What is wrong with the relay feeding this queue, or None when it is polling."""
        holder = statedir.holder(self.path("relay.lock"))
        beat = self._read_state("beat.json", {})
        last = beat.get("at")
        failure = f"; its last failed poll, at {beat.get('failed_at')}: {beat.get('failure')}" \
            if beat.get("failure") else ""
        if holder is None:
            return (f"no relay is running for this repository (last good poll: {last or 'never'}), "
                    f"so an empty queue does not mean nothing happened{failure}")
        if not last:
            return f"the relay (pid {holder.get('pid')}) has not completed a good poll yet{failure}"
        unattended = self._unattended(beat, self.clock())
        grace = beat.get("grace")
        if isinstance(grace, (int, float)) and unattended > grace:
            return (f"the relay (pid {holder.get('pid')}) last completed a good poll at {last}, and "
                    f"{int(unattended)}s since then went on no poll and no delivery, past its "
                    f"grace of {int(grace)}s{failure}")
        return None


# ----------------------------------------------------------------- the running relay

def running(state: Path) -> tuple[dict, dict] | None:
    """The live holder of this state directory's `relay.lock` and its `relay.json` record,
    or None when no relay runs. The record is empty while the relay has not written it yet
    (the moment between taking the lock and writing `relay.json`)."""
    holder = statedir.holder(state / "relay.lock")
    if holder is None:
        return None
    try:
        record = statedir.read_json(state / "relay.json", {})
    except ValueError:
        record = {}
    if isinstance(record, dict) and record.get("pid") == holder.get("pid") \
            and record.get("identity") == holder.get("identity"):
        return holder, record
    return holder, {}


def log_tail(path: Path, lines: int = 5) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "nothing"
    kept = [line for line in text.splitlines() if line.strip()][-lines:]
    return " | ".join(kept) or "nothing"


# ----------------------------------------------------------------- commands

def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a whole number") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"{value} is not a positive number")
    return value


def non_negative_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a whole number") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"{value} is negative")
    return value


def ticket_list(text: str) -> list[int]:
    try:
        numbers = [int(part) for part in text.split(",") if part.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a comma-separated list of ticket numbers") from None
    if not numbers or any(n < 1 for n in numbers):
        raise argparse.ArgumentTypeError(f"{text!r} names no ticket")
    return numbers


def state_for(repo: str) -> Path:
    try:
        return statedir.state_dir(repo)
    except ValueError as exc:
        raise Refusal(f"{exc}. Pass --repo as owner/name, the way `gh` names it.") from None


def cmd_run(args) -> int:
    state = state_for(args.repo)
    relay = Relay(state, Board(args.repo))
    interval = args.interval
    grace = args.grace if args.grace is not None else 3 * interval
    if not relay.watches():
        raise Refusal(f"nothing is watched for {args.repo}: {state / 'watches.json'} names no "
                      f"watch, so no event would wake anyone. `relay.py start --repo {args.repo} "
                      f"--spec <n> | --tickets <n> --runner <runner> --session <session>` opens "
                      f"one and starts the relay.")

    def stop(signum, frame):
        raise SystemExit(0)

    try:
        with statedir.locked(state / "relay.lock", wait=0, purpose=f"relay for {args.repo}"):
            signal.signal(signal.SIGTERM, stop)
            signal.signal(signal.SIGINT, stop)
            record = {"pid": os.getpid(), "identity": statedir.own_identity(),
                      "interval": interval, "grace": grace, "started": iso(now_utc())}
            statedir.write_atomic(state / "relay.json", json.dumps(record, sort_keys=True) + "\n")
            try:
                relay.forget_deliveries()
                while True:
                    if relay.leave_if_unwatched():
                        print(f"no watch is open for {args.repo} any more; the relay ends", flush=True)
                        return 0
                    good = relay.cycle(interval, grace)
                    if args.once:
                        return 0 if good else 3
                    time.sleep(interval)
            finally:
                try:
                    (state / "relay.json").unlink()
                except OSError:
                    pass
    except LockHeld as exc:
        if exc.path != state / "relay.lock":
            raise
        raise Refusal(f"another relay is running for {args.repo}: {exc}. One repository has one "
                      f"relay process, and it serves every watch. Leave that one running, or end "
                      f"that pid and start this again.") from None


def open_checked(args) -> tuple[Relay, dict, dict | None, dict]:
    """The checks `start` and `add` make, then the watch written: (the relay, the watch,
    the entry it replaced or None, the running relay's record when it was written)."""
    state = state_for(args.repo)
    adapter = adapter_path(args.runner)
    if not adapter.is_file():
        known = ", ".join(sorted(p.stem for p in RUNNERS.glob("*.sh"))) or "none"
        raise Refusal(f"there is no runner adapter {adapter}; the adapters here are: {known}. "
                      f"Open the watch from a session of one of those runners.")
    answer = ask_liveness(args.runner, args.session)
    if answer == "stopped":
        raise Refusal(f"{args.runner} says session {args.session} is stopped, so every wake-up sent "
                      f"to it would be dropped. Open the watch from the main agent's live session.")
    if answer != "alive":
        sys.stderr.write(f"relay: {args.runner} could not say whether session {args.session} is "
                         f"alive; the watch is opened all the same, and the first delivery will tell\n")
    found = running(state)
    if found is not None and "watch" in found[1]:
        # A record that names a `watch` was written by a relay that serves that one watch,
        # takes its main agent from recipient.json and never reads watches.json.
        raise Refusal(f"the relay running for {args.repo} (pid {found[0].get('pid')}) serves one "
                      f"watch, {describe_watch(found[1]['watch'])}, and would never read this one. "
                      f"End it with `relay.py stop --repo {args.repo}`, open its night again "
                      f"(dispatch.sh open or open-ticket), then open this watch. Nothing was "
                      f"recorded.")
    relay = Relay(state, Board(args.repo))
    want = watch_of(args)
    previous, record = relay.open_watch(want, args.runner, args.session)
    return relay, want, previous, record


def opened_line(repo: str, want: dict, previous: dict | None, runner: str, session: str) -> str:
    if previous is None:
        return (f"opened the watch on {describe_watch(want)} for {repo}: wake-ups go to {runner} "
                f"session {session}")
    was = "" if main_of(previous) == (runner, session) else \
        f", was {previous['runner']} session {previous['session']}"
    return (f"reopened the watch on {describe_watch(want)} for {repo}: wake-ups go to {runner} "
            f"session {session}{was}")


def cmd_add(args) -> int:
    _, want, previous, _ = open_checked(args)
    print(opened_line(args.repo, want, previous, args.runner, args.session))
    return 0


def cmd_start(args) -> int:
    relay, want, previous, record = open_checked(args)
    state = relay.state
    opened = opened_line(args.repo, want, previous, args.runner, args.session)
    holder = statedir.holder(state / "relay.lock")
    ending = holder is not None and record.get("pid") == holder.get("pid") and record.get("ending")
    if holder is not None and not ending:
        print(opened)
        print(f"relay already running for {args.repo}: pid {holder.get('pid')}, watching "
              f"{describe_watches(relay.watches())}")
        return 0
    try:
        if ending:
            # It had no watch left and is on its way out: let it go, then start another.
            deadline = time.monotonic() + STOP_WAIT
            while time.monotonic() < deadline and statedir.holder(state / "relay.lock") is not None:
                time.sleep(0.1)
            if statedir.holder(state / "relay.lock") is not None:
                raise Refusal(f"the relay (pid {holder.get('pid')}) had no watch left and was "
                              f"ending, and it still holds {state / 'relay.lock'} after "
                              f"{STOP_WAIT:.0f}s. End that pid by hand, then start again.")
        pid = spawn(args, state)
    except Refusal:
        relay.restore_watch(watch_key(want), previous)
        raise
    print(opened)
    print(f"relay started for {args.repo}: pid {pid}, watching {describe_watches(relay.watches())}, "
          f"log {state / 'relay.log'}")
    return 0


def spawn(args, state: Path) -> int:
    """Start `run` as a process of its own session; its pid once it holds the lock."""
    log = state / "relay.log"
    argv = [sys.executable, str(Path(__file__).resolve()), "run", "--repo", args.repo,
            "--interval", str(args.interval)]
    if args.grace is not None:
        argv += ["--grace", str(args.grace)]
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"--- {iso(now_utc())} starting a relay for {args.repo}\n")
        fh.flush()
        # A session of its own: the caller's turn, shell or terminal ending does not end it.
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=fh,
                                 stderr=subprocess.STDOUT, env=quiet_env(),
                                 start_new_session=True, close_fds=True)
    deadline = time.monotonic() + START_WAIT
    while time.monotonic() < deadline:
        code = child.poll()
        if code is not None:
            raise Refusal(f"the relay exited {code} as it started, so nothing watches the "
                          f"board. The last lines of {log}: {log_tail(log)}")
        found = running(state)
        if found is not None and found[0].get("pid") == child.pid and found[1]:
            return child.pid
        time.sleep(0.1)
    child.terminate()
    raise Refusal(f"the relay (pid {child.pid}) did not take {state / 'relay.lock'} within "
                  f"{START_WAIT:.0f}s and was ended. The last lines of {log}: {log_tail(log)}")


def cmd_stop(args) -> int:
    state = state_for(args.repo)
    want = watch_of(args)
    relay = Relay(state)
    key = watch_key(want) if want else None
    watches = relay.watches()
    if key is not None and watches and key not in watches:
        sys.stderr.write(f"relay: {describe_watch(want)} is not watched for {args.repo}; the relay "
                         f"watches {describe_watches(watches)}, and nothing was changed\n")
        return 3
    closed, left = relay.close_watch(key)
    found = running(state)
    if left:
        if not closed:
            sys.stderr.write(f"relay: {describe_watch(want)} is not watched for {args.repo}; the "
                             f"relay watches {describe_watches(left)}, and nothing was changed\n")
            return 3
        if found is not None:
            print(f"stopped watching {describe_watches(closed)} for {args.repo}: the relay "
                  f"(pid {found[0].get('pid')}) goes on watching {describe_watches(left)}")
        else:
            print(f"stopped watching {describe_watches(closed)} for {args.repo}: no relay is "
                  f"running, and {describe_watches(left)} is still watched")
        return 0
    if found is None:
        if closed:
            print(f"stopped watching {describe_watches(closed)} for {args.repo}; no relay was running")
        else:
            print(f"no relay is running for {args.repo}")
        return 0
    pid = found[0].get("pid")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError as exc:
        raise Refusal(f"could not signal the relay (pid {pid}): {exc}. It is still running with "
                      f"no watch left; end that pid by hand.") from None
    deadline = time.monotonic() + STOP_WAIT
    while time.monotonic() < deadline:
        if statedir.holder(state / "relay.lock") is None:
            print(f"stopped the relay for {args.repo}: pid {pid}, watching {describe_watches(closed)}")
            return 0
        time.sleep(0.1)
    raise Refusal(f"the relay (pid {pid}) was sent SIGTERM and still holds "
                  f"{state / 'relay.lock'} after {STOP_WAIT:.0f}s. It is still running with no "
                  f"watch left; end that pid by hand.")


def cmd_watching(args) -> int:
    if args.ticket is None and args.spec is None:
        raise Refusal("name the ticket (--ticket), its spec (--spec), or both.")
    state = state_for(args.repo)
    found = running(state)
    if found is None:
        sys.stderr.write(f"relay: no relay is running for {args.repo}\n")
        return 1
    pid = found[0].get("pid")
    watches = Relay(state).watches()
    asked = f"#{args.ticket}" if args.ticket is not None else f"spec #{args.spec}"
    for entry in watches.values():
        if (args.spec and entry.get("spec") == args.spec) \
                or (args.ticket is not None and args.ticket in (entry.get("tickets") or [])):
            print(f"{asked} is watched by the relay for {args.repo}: pid {pid}, as "
                  f"{describe_watch(entry)}, whose main agent is {entry['runner']} session "
                  f"{entry['session']}")
            return 0
    if args.ticket is not None:
        asked += f", a ticket of spec #{args.spec}," if args.spec else ", a ticket of no spec,"
    sys.stderr.write(f"relay: the relay running for {args.repo} (pid {pid}) watches "
                     f"{describe_watches(watches)}, and {asked} is not among them\n")
    return 1


def cmd_ack(args) -> int:
    relay = Relay(state_for(args.repo))
    address = (args.runner, args.session)
    if args.through is not None:
        if args.event or args.ticket is not None:
            raise Refusal("an ack names a sequence number (--through) or a wake (--ticket and "
                          "--event), not both.")
        removed, left = relay.ack(address, args.through)
        print(f"acked {args.runner} {args.session} through {args.through}: removed {removed}, "
              f"{left} left for it")
        return 0
    if not args.event:
        raise Refusal("an ack names a sequence number (--through) or the wake it read "
                      "(--ticket N --event E, or --event relay.recovered).")
    if args.event != RECOVERED and args.ticket is None:
        raise Refusal(f"the wake `{args.event}` is about a ticket; pass --ticket with its number.")
    ticket = None if args.event == RECOVERED else args.ticket
    wake = RECOVERED if ticket is None else f"#{ticket} {args.event}"
    done = relay.ack_wake(address, ticket, args.event)
    if done is None:
        mine = [wake_text(r).split(" since ")[0] for r in relay.rows(address)]
        held = ", ".join(f"`{w}`" for w in mine) if mine else "nothing"
        raise Refusal(f"no wake `{wake}` is queued for {args.runner} session {args.session}, "
                      f"so nothing was acked: it was acked already, it went to another "
                      f"session, or it was never queued. Queued for this session: {held}. "
                      f"Ack a wake from this session, as it reached it: the ticket number and "
                      f"the event name it carried.")
    through, removed, left = done
    print(f"acked {args.runner} {args.session} `{wake}` through {through}: removed {removed}, "
          f"{left} left for it")
    return 0


def cmd_queue(args) -> int:
    if (args.runner is None) != (args.session is None):
        raise Refusal("a recipient is a runner and a session together; pass both --runner and "
                      "--session, or neither for every row.")
    relay = Relay(state_for(args.repo))
    address = (args.runner, args.session) if args.session else None
    for row in relay.rows(address):
        print(json.dumps({k: v for k, v in row.items() if k != "key"}, sort_keys=True))
    sys.stdout.flush()
    problem = relay.health()
    if problem:
        sys.stderr.write(f"relay: {problem}\n")
        return 3
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="relay.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def watch_args(command, required: bool) -> None:
        which = command.add_mutually_exclusive_group(required=required)
        which.add_argument("--tickets", type=ticket_list)
        which.add_argument("--spec", type=positive_int)

    start = sub.add_parser("start", help="open a watch with its main agent, and run the relay unless it runs")
    start.add_argument("--repo", required=True)
    watch_args(start, True)
    start.add_argument("--runner", required=True)
    start.add_argument("--session", required=True)
    start.add_argument("--interval", type=positive_int, default=DEFAULT_INTERVAL)
    start.add_argument("--grace", type=non_negative_int)
    start.set_defaults(fn=cmd_start)

    add = sub.add_parser("add", help="open a watch with its main agent, starting nothing")
    add.add_argument("--repo", required=True)
    watch_args(add, True)
    add.add_argument("--runner", required=True)
    add.add_argument("--session", required=True)
    add.set_defaults(fn=cmd_add)

    stop = sub.add_parser("stop", help="close a watch, or every watch; the relay ends with the last")
    stop.add_argument("--repo", required=True)
    watch_args(stop, False)
    stop.set_defaults(fn=cmd_stop)

    watching = sub.add_parser("watching", help="whether a running relay sees a ticket's events")
    watching.add_argument("--repo", required=True)
    watching.add_argument("--ticket", type=positive_int)
    watching.add_argument("--spec", type=positive_int)
    watching.set_defaults(fn=cmd_watching)

    run = sub.add_parser("run", help="poll the board for every open watch and deliver wake-ups")
    run.add_argument("--repo", required=True)
    run.add_argument("--once", action="store_true")
    run.add_argument("--interval", type=positive_int, default=DEFAULT_INTERVAL)
    run.add_argument("--grace", type=non_negative_int)
    run.set_defaults(fn=cmd_run)

    ack = sub.add_parser("ack", help="remove one recipient's rows through a sequence number or a wake")
    ack.add_argument("--repo", required=True)
    ack.add_argument("--runner", required=True)
    ack.add_argument("--session", required=True)
    ack.add_argument("--through", type=positive_int)
    ack.add_argument("--ticket", type=positive_int)
    ack.add_argument("--event")
    ack.set_defaults(fn=cmd_ack)

    queue = sub.add_parser("queue", help="print the rows, or one recipient's rows")
    queue.add_argument("--repo", required=True)
    queue.add_argument("--runner")
    queue.add_argument("--session")
    queue.set_defaults(fn=cmd_queue)

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except Refusal as exc:
        sys.stderr.write(f"relay: {exc}\n")
        return 1
    except LockHeld as exc:
        sys.stderr.write(f"relay: the wake queue stayed locked for {QUEUE_WAIT:.0f}s: {exc}. Run the "
                         f"command again; if it stays locked, that pid is stuck.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
