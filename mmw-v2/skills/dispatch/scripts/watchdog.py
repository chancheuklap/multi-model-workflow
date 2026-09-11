#!/usr/bin/env python3
"""The watchdog: the second and third layers of liveness for one repository's open watches.

    watchdog.py run --repo O/R [--poll S] [--silence S] [--idle S] [--once]
    watchdog.py arm --repo O/R [--wait S]
    watchdog.py status --repo O/R

The board only ever brings good news. A worker that finishes writes on its ticket and the
relay wakes whoever waits on it; a worker that dies writes nothing, and on the board its
silence looks exactly like work in progress (docs/adr/0008-silence-is-never-a-pass.md).
This process is what notices. It costs no tokens and holds no session: it reads files,
`gh` and the runner adapters, and it is not an agent.

**Three layers, and which one this is.** The first layer is `turn-guard.py`, beside this
file: a hook on each main agent's own turn end that re-arms this process and will not let
that turn end while tickets are held and this process is not healthy. This file is the
second layer (it beats, it watches the relay) and the third (it asks a silent ticket's
runner whether its worker is still there). When this process dies, the first layer finds
out at a main agent's next turn end; there is no fourth layer, so a crash of the host a
main agent runs in is found by a person.

**What it watches.** Every watch the relay has open for the repository (`watches.json` in
the state directory, relay.py): a night — a spec, whose sub-issues are listed again every
round — or tickets outside a night. Each watch has its own main agent. A closed sub-issue
of a spec is not read: a closed ticket's worker has handed in its work. A ticket a tickets
watch names is always read. A night is open while `watches.json` names a watch: `relay.py
stop`, which `summary`, `suspend` and `land` run, closes one, and the relay closes the
watch of a main agent that has been gone for an hour. A relay that died leaves its
watches open, so a dead relay is an open night with no relay, never a closed one. When no
watch is open this process writes a last heartbeat saying so and exits.

**Each round**, every `--poll` seconds (default 60):

1. The relay. Its lock record (`relay.lock`: pid and process identity, statedir.py) must
   name a live process, and its last good poll must be within its grace, less the time it
   spent delivering. A relay that has not polled yet is given its grace from the moment it
   started. Otherwise that is a finding: `relay down`.
2. Every watched ticket is read in full and folded (`events.py` of the verify-ticket
   skill). A ticket not held is skipped. A held ticket in the waiting step — the fold's
   `waiting`: a `worker.queued` its run still waits under, because no product slot was
   free — is quiet by design, so its silence proves nothing, and it is asked about every
   round however long it has been quiet: queueing is not dying, and it is not exempt
   either, since a worker that dies in the queue would otherwise hold its ticket for good.
   Any other held ticket whose newest event is less than `--silence` seconds old (default
   600) is skipped.
3. Every other held ticket is silent. For each session that still holds a silent or a
   waiting ticket — the (runner, session) pair of every `worker.started`,
   `reviewer.started` or `verifier.started` no later event has ended, less a reviewer or
   verifier whose result is already on the ticket after its start — this asks that
   session's own runner, and no other runner, `runners/<runner>.sh liveness <session>`:

       alive     nothing
       stopped   `<kind>.lost` is posted on the ticket, naming that pair: `worker.lost`,
                 `reviewer.lost` or `verifier.lost`. They are the only events not written
                 by the agent they are about, and this process is their one writer. Each
                 ends that session's hold; the relay wakes the main agent on
                 `worker.lost`, and the ticket's worker on the other two, so a worker
                 asleep on a reviewer or verifier that died is woken to start another.
       unknown   recorded as unknown in the heartbeat, and a finding. Never rendered as
                 alive, never a `*.lost`: an answer the adapter could not give — or a
                 missing adapter, a non-zero exit, a timeout — is not a death.

   A silent ticket held by no session to ask (a claim no start names, or only sessions
   whose results are in) is a finding too. So is a ticket whose events cannot be read.
4. A silent ticket whose newest event is at least `--idle` seconds old (default 3600),
   whose worker's runner answered `alive`, and whose fold shows it waiting for nothing —
   no live reviewer or verifier session, no `waiting`, not `passed` — is a finding: its
   worker is there and nothing will ever wake it (a worker that ended its turn with no
   result, say). Once per ticket and newest event.

**Findings wake the main agent directly**, through the `send` of the runner that main
agent runs in, one message on one line, each finding in it beginning `watchdog:`. Not
through the relay's queue: the relay may be the thing that is down. A finding about a
ticket goes to the main agent of the watch the ticket belongs to; `relay down` and
`cannot read the board` go to every watch's main agent. Each finding is sent to each of
its main agents once — keyed by that main agent, what the finding is about, and the
ticket's newest event or the relay's last good poll — and never again for the same
stretch, across restarts of this process. What `send` answered decides what happens next:

    0      delivered and a turn started. This process exits once the round's sends are
           done: that main agent is now in a turn, and that turn's end re-arms it
           (one-shot, re-armed by the hook)
    4      handed over, not confirmed: not sent again, and this process keeps running
    3, 5+  nothing was sent: kept, and sent again next round
    2      that main agent's session is gone: recorded, kept, nobody to tell

The findings exactly:

    watchdog: relay down (<what is wrong>); details: python3 <this file> status --repo <repo>
    watchdog: #<n> events unreadable
    watchdog: #<n> is held with no session to ask, silent since <time>
    watchdog: #<n> liveness unknown: <runner> could not say whether the <kind> session
              <session> is alive; silent since <time>
    watchdog: #<n> liveness unknown: the <kind> session <session> was started on
              <machine>, not on <this machine>, and only that machine can ask <runner>;
              silent since <time>
    watchdog: #<n> silent since <time> with nothing to wait on: its worker <session> on
              <runner> is alive, and no reviewer, verifier or product slot is pending
    watchdog: cannot read the board since <time>: <what failed>

**The heartbeat and the lock.** `run` holds `watchdog.lock` for as long as it runs, so a
repository has one watchdog, serving every watch; the lock's record names its pid and
process identity, the same convention as the relay's. It writes `watchdog.json`, the
heartbeat, at start, after every ticket and at the end of every round, with that same pid
and identity. A heartbeat is fresh when its age is within the tolerance
`max(300, poll + MARGIN)` seconds, MARGIN being one adapter call plus one gh read
(60 + 120 s), the longest it waits between two beats: a fixed number would read a healthy
watchdog as dead as soon as its poll grew past it. The watchdog is healthy when the lock
names a live process, the heartbeat was written by that process, it is fresh, and its last
whole read of the board (`read_at`, carried across restarts) is within the tolerance too:
a watchdog that cannot read the board watches nothing, and after the tolerance it says so
once (`cannot read the board`). A pid alone is never enough: a dead watchdog's pid can be
handed to another process, and that process is not a watchdog.

**Only this machine's sessions are asked.** Every `*.started` records the machine it was
started on (`machine`, the hostname). A runner answers for its own machine, and asked about
a session started on another it would say `stopped` of a worker that is alive; so a session
from another machine is recorded as unknown and reported, never asked and never lost.

**Arming.** `arm` does nothing when the watchdog is healthy, and ends nothing that still
beats: one that cannot read the board is left running to report it. Otherwise it ends a hung
one (a live holder whose heartbeat is past its tolerance, identity checked, SIGTERM), starts
`run` as a process of its own session with its output appended to `watchdog.log`, and waits
up to `--wait` seconds (default 5) for it to be healthy. `MMW_WATCHDOG_PY` names the script
that is started, for tests and for trying the hook against a watchdog that will not start.

Files in the state directory, beside the relay's:

    watchdog.lock   held for as long as a `run` runs: one watchdog per repository
    watchdog.json   the heartbeat: pid, identity, machine, at, poll, tolerance, silence,
                    idle, watches (the open watches as last read, with their main agents),
                    held, waiting, unknown, lost, relay, read_at, read_failure, pending
                    (findings not yet sent, each with the runner and session it is for),
                    reported ([runner, session, key] of each finding sent), main (per main
                    agent, why its findings could not be sent), closed, reads (billed and
                    not-modified comment-list reads since this process started; null for a
                    board that does not count them)
    watchdog.log    what every started watchdog printed, appended

Exit codes:

    run      0 ran until no watch was open, until it woke a main agent, or one round with
             --once; 1 refused (the repository name, a state file that is not JSON).
             Another watchdog already running is 0: arming twice is not an error
    arm      0 the watchdog is healthy (now, or already); 1 it could not be made healthy,
             and stderr says why with the last lines of watchdog.log
    status   0 healthy; 3 not healthy, or no open night; the heartbeat is printed either way
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import socket
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import statedir  # noqa: E402
from statedir import LockHeld  # noqa: E402
import relay as relay_mod  # noqa: E402  (loads events.py beside it)

events = relay_mod.events

DEFAULT_POLL = 60
DEFAULT_SILENCE = 600
DEFAULT_IDLE = 3600
BASE_TOLERANCE = 300
ARM_WAIT = 5.0
ADAPTER_TIMEOUT = 60
# The longest a healthy watchdog goes between two heartbeats beyond its sleep: it beats
# after every ticket read and every runner asked, so one gh read and one adapter call.
MARGIN = ADAPTER_TIMEOUT + relay_mod.GH_TIMEOUT
POST_TIMEOUT = 60
REPORTED_KEEP = 200

ANSWERS = ("alive", "stopped", "unknown")


# ----------------------------------------------------------------- time

def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text) -> datetime | None:
    if not isinstance(text, str) or not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


# ----------------------------------------------------------------- judgements (pure)

def tolerance(poll) -> int:
    """How old a heartbeat may be and still be fresh: `max(300, poll + MARGIN)` seconds,
    MARGIN being one adapter call plus one gh read (60 + 120).

    A watchdog sleeps `poll` seconds between rounds and beats after every ticket read and
    every runner asked, so a healthy one's heartbeat is up to `poll` old plus the slowest
    single call it waits on. A fixed tolerance stops bounding that the moment the poll
    grows past it, and a smaller margin would have `arm` end a watchdog that is only slow.
    """
    try:
        poll = int(poll)
    except (TypeError, ValueError):
        poll = DEFAULT_POLL
    return max(BASE_TOLERANCE, poll + MARGIN)


def health(holder: dict | None, beat: dict | None, now: datetime) -> tuple[bool, str]:
    """Whether a watchdog is healthy, from its lock's live holder and its heartbeat.

    `holder` is `statedir.holder(watchdog.lock)`: the lock's record when its pid runs now
    with the recorded identity, else None. Healthy is four things together: a live holder,
    a heartbeat that holder wrote (same pid and identity: a heartbeat left by an earlier
    watchdog proves nothing about this one), that heartbeat within `tolerance`, and a
    whole read of the board within `tolerance` too (`read_at`, carried across restarts): a
    watchdog that cannot read the board watches nothing, however regularly it beats.
    """
    if holder is None:
        last = f", last heartbeat {beat.get('at')}" if beat and beat.get("at") else ""
        return False, f"no watchdog is running: its lock names no live process{last}"
    pid = holder.get("pid")
    if not beat or not beat.get("at"):
        return False, f"the watchdog (pid {pid}) has written no heartbeat"
    if (beat.get("pid"), beat.get("identity")) != (pid, holder.get("identity")):
        return False, (f"the heartbeat was written by pid {beat.get('pid')}, not by the watchdog "
                       f"holding the lock (pid {pid})")
    at = parse_iso(beat.get("at"))
    if at is None:
        return False, f"the watchdog's heartbeat time {beat.get('at')!r} cannot be read"
    age = int((now - at).total_seconds())
    limit = tolerance(beat.get("poll"))
    if age > limit:
        return False, (f"the watchdog (pid {pid}) last beat {age}s ago, past its tolerance of "
                       f"{limit}s")
    read = parse_iso(beat.get("read_at") or beat.get("started"))
    if read is not None and (now - read).total_seconds() > limit:
        return False, (f"the watchdog (pid {pid}) has not read the whole board since "
                       f"{iso(read)}, past its tolerance of {limit}s: "
                       f"{beat.get('read_failure') or 'no read has succeeded'}")
    return True, f"the watchdog (pid {pid}) beat {max(age, 0)}s ago"


def stale(beat: dict | None, now: datetime) -> bool:
    """A heartbeat older than its tolerance: the watchdog writing it is hung, not slow."""
    at = parse_iso((beat or {}).get("at"))
    return at is None or (now - at).total_seconds() > tolerance((beat or {}).get("poll"))


def judge(fold: dict, now: datetime, silence: int, idle: int = DEFAULT_IDLE) -> dict:
    """What one ticket's fold says the third layer should do with it.

        {"state": "unreadable"}                        a comment's event cannot be read
        {"state": "free"}                              no hold on it
        {"state": "waiting", "since": T, "sessions": [...], "comment": C}
                                                       in the waiting step: the fold's
                                                       `waiting`, the `worker.queued` its
                                                       run still waits under; asked about
                                                       whatever its silence
        {"state": "recent", "since": T}                newest event younger than `silence`
        {"state": "silent", "since": T, "sessions": [...], "comment": C, "idle": B}
                                                       held and silent; `sessions` is every
                                                       (kind, runner, session) to ask;
                                                       `idle` when its newest event is at
                                                       least `idle` old and it waits for
                                                       nothing: no live reviewer or
                                                       verifier, and no pass
    """
    if fold.get("unreadable"):
        return {"state": "unreadable",
                "comments": [item.get("comment") for item in fold["unreadable"]]}
    if not fold.get("held"):
        return {"state": "free"}
    last = fold.get("last") or {}
    since = last.get("at")
    waiting = fold.get("waiting")
    if waiting:
        return {"state": "waiting",
                "since": waiting.get("at") if isinstance(waiting, dict) else since,
                "sessions": to_ask(fold), "comment": last.get("comment")}
    at = parse_iso(since)
    if at is not None and (now - at).total_seconds() < silence:
        return {"state": "recent", "since": since}
    helpers = [r for r in fold.get("holders") or [] if r.get("kind") in ("reviewer", "verifier")]
    quiet = at is not None and (now - at).total_seconds() >= idle
    return {"state": "silent", "since": since, "sessions": to_ask(fold),
            "comment": last.get("comment"),
            "idle": quiet and not helpers and not fold.get("passed")}


def to_ask(fold: dict) -> list[tuple[str, str, str, str]]:
    """(kind, runner, session, machine) of every session still holding the ticket. A
    reviewer's or verifier's result ends its own hold in the fold, so one whose result is
    in is not among them: its process ending is not a loss."""
    out = []
    for record in fold.get("holders") or []:
        kind, runner, session = record.get("kind"), record.get("runner"), record.get("session")
        if kind and runner and session:
            out.append((kind, runner, session, record.get("machine") or ""))
    return out


def night_open(state: Path) -> bool:
    """Whether a night — any watch — is open on this state directory: the relay's
    `watches.json` names one. `relay.py stop` closes a watch, and the relay closes the
    watch of a main agent gone for an hour; a relay that died leaves its watches open. A
    `watches.json` that cannot be read is not a closed night."""
    try:
        return bool(relay_mod.read_watches(state))
    except ValueError:
        return True


def relay_problem(state: Path, now: datetime) -> str | None:
    """What is wrong with the relay of an open night, or None when it polls.

    Its lock must name a live process (pid and identity), and its last good poll must be
    within its grace less the time it spent delivering. A relay that has not polled yet is
    given its grace from the moment it started.
    """
    holder = statedir.holder(state / "relay.lock")
    try:
        beat = statedir.read_json(state / "beat.json", {})
        record = statedir.read_json(state / "relay.json", {})
    except ValueError as exc:
        return f"the relay's state cannot be read ({exc})"
    beat = beat if isinstance(beat, dict) else {}
    record = record if isinstance(record, dict) else {}
    last = beat.get("at")
    grace = beat.get("grace") if isinstance(beat.get("grace"), (int, float)) else record.get("grace")
    if not isinstance(grace, (int, float)):
        grace = 3 * relay_mod.DEFAULT_INTERVAL
    failure = f"; its last failed poll: {beat.get('failure')}" if beat.get("failure") else ""
    if holder is None:
        return f"no relay is running (last good poll: {last or 'never'}){failure}"
    if not last:
        began = parse_iso(record.get("started"))
        if began is not None and (now - began).total_seconds() <= grace:
            return None
        return f"the relay (pid {holder.get('pid')}) has made no good poll since it started{failure}"
    unattended = relay_mod.Relay._unattended(beat, now)
    if unattended > grace:
        return (f"the relay (pid {holder.get('pid')}) last polled at {last}, {int(unattended)}s "
                f"ago, past its grace of {int(grace)}s{failure}")
    return None


# ----------------------------------------------------------------- the outside

def runners_dir() -> Path:
    """Where the runner adapters are: `MMW_RUNNERS_DIR`, else `runners/` beside this file."""
    return Path(os.environ.get("MMW_RUNNERS_DIR") or (HERE / "runners"))


def ask_liveness(runner: str, session: str) -> str:
    """`runners/<runner>.sh liveness <session>`: alive, stopped or unknown. Anything the
    adapter did not answer in so many words — no adapter, a non-zero exit, a timeout, other
    output — is unknown, never alive and never stopped."""
    adapter = runners_dir() / f"{runner}.sh"
    if not runner or not adapter.is_file():
        return "unknown"
    try:
        run = subprocess.run(["bash", str(adapter), "liveness", session], capture_output=True,
                             text=True, env=relay_mod.quiet_env(), timeout=ADAPTER_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    answer = (run.stdout or "").strip()
    return answer if run.returncode == 0 and answer in ANSWERS else "unknown"


def send_to(runner: str, session: str, text: str) -> int:
    """`runners/<runner>.sh send <session> <text>`; its exit code, or 5 when the adapter
    gave none (missing, could not be run, did not answer)."""
    adapter = runners_dir() / f"{runner}.sh"
    if not adapter.is_file():
        sys.stderr.write(f"watchdog: no runner adapter at {adapter}; nothing was sent\n")
        return 5
    try:
        run = subprocess.run(["bash", str(adapter), "send", session, text], capture_output=True,
                             text=True, env=relay_mod.quiet_env(), timeout=relay_mod.SEND_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        sys.stderr.write(f"watchdog: {runner}.sh send could not be run: {exc}\n")
        return 5
    for line in (run.stderr or "").splitlines():
        if line.strip():
            sys.stderr.write(f"watchdog: {runner}.sh: {line}\n")
    return run.returncode


def lost_body(kind: str, ticket: int, spec: int | None, runner: str, session: str,
              since: str | None) -> str:
    """The comment body of `<kind>.lost` for (runner, session) on `ticket`."""
    return events.build(
        f"{kind}.lost", ticket=ticket, spec=spec, runner=runner, session=session,
        line=(f"The {kind}, {runner} session {session}, is gone: {runner} says it has "
              f"stopped, and the ticket has had no event since {since or 'its start'}."),
    )


def post_lost(repo: str, kind: str, ticket: int, spec: int | None, runner: str, session: str,
              since: str | None) -> tuple[bool, str]:
    """Post `<kind>.lost` for (runner, session) on `ticket`. (posted, what went wrong)."""
    body = lost_body(kind, ticket, spec, runner, session, since)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        path = fh.name
    try:
        run = subprocess.run(["gh", "issue", "comment", str(ticket), "--repo", repo,
                              "--body-file", path], capture_output=True, text=True,
                             env=relay_mod.quiet_env(), timeout=POST_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"gh could not be run: {exc}"
    finally:
        os.unlink(path)
    if run.returncode != 0:
        said = " ".join((run.stderr or run.stdout or "").split())[:300]
        return False, f"gh exited {run.returncode}: {said or 'nothing on stderr'}"
    return True, ""


def repo_of(state: Path) -> str:
    """The repository a state directory is for: `owner__name` read back as `owner/name`."""
    owner, _, name = state.name.partition("__")
    return f"{owner}/{name}"


# ----------------------------------------------------------------- the watchdog

class Watchdog:
    """One repository's watchdog: its rounds, its heartbeat, its findings."""

    def __init__(self, state: Path, repo: str, board=None,
                 ask: Callable[[str, str], str] = ask_liveness,
                 send: Callable[[str, str, str], int] = send_to,
                 post: Callable[..., tuple[bool, str]] = post_lost,
                 clock: Callable[[], datetime] = now_utc,
                 poll: int = DEFAULT_POLL, silence: int = DEFAULT_SILENCE,
                 idle: int = DEFAULT_IDLE,
                 pid: int | None = None, identity: str | None = None,
                 machine: str | None = None, err=None):
        self.state = Path(state)
        self.repo = repo
        self.board = board if board is not None else relay_mod.Board(repo)
        self.ask = ask
        self.send = send
        self.post = post
        self.clock = clock
        self.poll = poll
        self.silence = silence
        self.idle = idle
        self.pid = pid if pid is not None else os.getpid()
        self.identity = identity if identity is not None else statedir.own_identity()
        self.machine = machine if machine is not None else socket.gethostname()
        self.err = err or sys.stderr
        previous = self._read("watchdog.json", {})
        previous = previous if isinstance(previous, dict) else {}
        self.beat = {
            "pid": self.pid, "identity": self.identity, "started": iso(self.clock()),
            "poll": poll, "tolerance": tolerance(poll), "silence": silence, "idle": idle,
            "round": 0,
            "watches": previous.get("watches") if isinstance(previous.get("watches"), dict) else {},
            "held": None, "waiting": [], "unknown": {}, "lost": {}, "relay": None,
            "pending": [p for p in previous.get("pending") or []
                        if isinstance(p, dict) and p.get("runner") and p.get("session")],
            "reported": [r for r in previous.get("reported") or []
                         if isinstance(r, list) and len(r) == 3],
            "main": None, "closed": None, "machine": self.machine,
            # The last round that read every ticket. While reads are failing it is carried
            # across restarts, so a restart does not wipe out how long the board has gone
            # unread; a watchdog that was reading, or a night that closed, starts afresh.
            "read_at": (previous.get("read_at") if previous.get("read_failure")
                        and not previous.get("closed") else None) or iso(self.clock()),
            "read_failure": (previous.get("read_failure")
                             if not previous.get("closed") else None),
        }

    # ------------------------------------------------------------- files

    def _read(self, name: str, default):
        return statedir.read_json(self.state / name, default)

    def write_beat(self) -> None:
        """The heartbeat, stamped now, written in one step. Only the lock holder writes it."""
        self.beat["at"] = iso(self.clock())
        reads = getattr(self.board, "reads", None)
        self.beat["reads"] = dict(reads) if isinstance(reads, dict) else None
        statedir.write_atomic(self.state / "watchdog.json",
                              json.dumps(self.beat, sort_keys=True, indent=1) + "\n")

    # ------------------------------------------------------------- one round

    def watches(self, failures: list[str]) -> dict[str, dict]:
        """The open watches, by key; the last ones read when `watches.json` cannot be."""
        try:
            self.beat["watches"] = relay_mod.read_watches(self.state)
        except ValueError as exc:
            failures.append(f"the watches ({self.state / 'watches.json'} is not JSON: {exc})")
        return self.beat.get("watches") or {}

    def watched(self, watches: dict[str, dict], failures: list[str]) -> dict[int, dict]:
        """Every ticket to read this round, each with its watch: `spec` (None for a
        tickets watch) and `main`, the (runner, session) its findings go to. Tickets
        watches are taken first, as the relay takes them. A closed sub-issue of a spec is
        left out; a spec whose sub-issues cannot be listed is a failure."""
        tickets: dict[int, dict] = {}
        ordered = sorted(watches.items(), key=lambda kv: (0 if kv[1].get("tickets") else 1, kv[0]))
        for key, entry in ordered:
            home = {"key": key, "spec": None, "main": relay_mod.main_of(entry)}
            if entry.get("tickets"):
                for number in entry["tickets"]:
                    tickets.setdefault(int(number), home)
                continue
            spec = int(entry["spec"])
            try:
                children = self.board.children(spec)
            except relay_mod.PollError as exc:
                self.err.write(f"watchdog: could not read the tickets of spec #{spec}: {exc}\n")
                failures.append(f"the tickets of spec #{spec}: {exc}")
                continue
            for number, state in children:
                if state != "closed":
                    tickets.setdefault(int(number), {**home, "spec": spec})
        return tickets

    def round(self) -> str:
        """One round. Returns `closed` (no watch is open), `woke` (a main agent was woken
        and is in a turn) or `watching`."""
        now = self.clock()
        self.beat["round"] += 1
        if not night_open(self.state):
            self.beat["closed"] = iso(now)
            self.write_beat()
            return "closed"

        findings: list[dict] = []
        failures: list[str] = []
        watches = self.watches(failures)
        everyone = sorted({relay_mod.main_of(entry) for entry in watches.values()})
        problem = relay_problem(self.state, now)
        self.beat["relay"] = problem
        if problem:
            beat = self._read_quiet("beat.json")
            record = self._read_quiet("relay.json")
            findings.append({
                "key": f"relay:{beat.get('at') or 'never'}:{record.get('started') or ''}",
                "text": f"watchdog: relay down ({problem}); details: python3 {Path(__file__).resolve()} "
                        f"status --repo {self.repo}",
                "to": everyone,
            })

        tickets = self.watched(watches, failures)
        read_all = not failures
        held: list[int] = []
        waiting: list[int] = []
        unknown: dict = {}
        for number, home in tickets.items():
            to = [home["main"]]
            try:
                comments = self.board.comments(number, None)
            except relay_mod.PollError as exc:
                self.err.write(f"watchdog: could not read #{number}: {exc}\n")
                failures.append(f"#{number}: {exc}")
                read_all = False
                continue
            fold = events.fold(comments, issue=number)
            verdict = judge(fold, now, self.silence, self.idle)
            state = verdict["state"]
            if state == "unreadable":
                held.append(number)
                unknown[str(number)] = {"why": "events unreadable"}
                findings.append({"key": f"unreadable:{number}:{verdict['comments']}",
                                 "text": f"watchdog: #{number} events unreadable", "to": to})
            elif state == "free":
                pass
            elif state == "waiting":
                held.append(number)
                waiting.append(number)
                self._silent(number, home["spec"], verdict, unknown, findings, to)
            elif state == "recent":
                held.append(number)
            else:
                held.append(number)
                self._silent(number, home["spec"], verdict, unknown, findings, to)
            self.beat["unknown"] = unknown
            self.write_beat()

        # A round that could not read every ticket does not know that nothing is held.
        self.beat.update(held=held if read_all else (held or None), waiting=waiting,
                         unknown=unknown)
        if read_all:
            self.beat.update(read_at=iso(now), read_failure=None)
        else:
            self.beat["read_failure"] = "; ".join(failures)
            since = parse_iso(self.beat.get("read_at"))
            if since is not None and (now - since).total_seconds() > tolerance(self.poll):
                findings.append({
                    "key": f"read:{self.beat.get('read_at')}",
                    "text": f"watchdog: cannot read the board since {self.beat.get('read_at')}: "
                            f"{self.beat['read_failure']}",
                    "to": everyone,
                })
        woke = self._report(findings, everyone)
        self.write_beat()
        return "woke" if woke else "watching"

    def _read_quiet(self, name: str) -> dict:
        try:
            value = self._read(name, {})
        except ValueError:
            return {}
        return value if isinstance(value, dict) else {}

    def _silent(self, number: int, spec: int | None, verdict: dict, unknown: dict,
                findings: list[dict], to: list[tuple[str, str]]) -> None:
        """The third layer, for one held and silent ticket."""
        since = verdict.get("since")
        if not verdict["sessions"]:
            unknown[str(number)] = {"why": "held by no session to ask", "since": since}
            findings.append({
                "key": f"unheld:{number}:{verdict.get('comment')}",
                "text": f"watchdog: #{number} is held with no session to ask, silent "
                        f"since {since or 'an unknown time'}",
                "to": to,
            })
            return
        for kind, runner, session, machine in verdict["sessions"]:
            if machine != self.machine:
                # A runner answers for its own machine: asked here about a session started
                # elsewhere it would say `stopped` of a worker that is alive.
                entry = unknown.setdefault(str(number), {"sessions": [], "since": since,
                                                         "why": "the runner could not say"})
                entry["sessions"].append({"kind": kind, "runner": runner, "session": session,
                                          "machine": machine})
                findings.append({
                    "key": f"elsewhere:{number}:{kind}:{runner}:{session}:{verdict.get('comment')}",
                    "text": f"watchdog: #{number} liveness unknown: the {kind} session "
                            f"{session} was started on {machine or 'an unrecorded machine'}, "
                            f"not on {self.machine}, and only that machine can ask {runner}; "
                            f"silent since {since or 'an unknown time'}",
                    "to": to,
                })
                continue
            answer = self.ask(runner, session)
            self.write_beat()
            if answer == "alive":
                if kind == "worker" and verdict.get("idle"):
                    # Alive, and nothing it waits on will ever land: nobody is coming to wake it.
                    findings.append({
                        "key": f"idle:{number}:{verdict.get('comment')}",
                        "text": f"watchdog: #{number} silent since {since} with nothing to wait "
                                f"on: its worker {session} on {runner} is alive, and no "
                                f"reviewer, verifier or product slot is pending",
                        "to": to,
                    })
                continue
            if answer == "stopped":
                posted, why = self.post(self.repo, kind, number, spec, runner, session, since)
                if posted:
                    self.beat["lost"].setdefault(str(number), []).append(
                        {"kind": kind, "runner": runner, "session": session,
                         "at": iso(self.clock())})
                    self.err.write(f"watchdog: posted {kind}.lost on #{number} for {runner} "
                                   f"session {session}\n")
                else:
                    self.err.write(f"watchdog: {runner} says {kind} session {session} of "
                                   f"#{number} stopped, and {kind}.lost could not be posted: "
                                   f"{why}; it is tried again next round\n")
                continue
            entry = unknown.setdefault(str(number), {"sessions": [], "since": since,
                                                     "why": "the runner could not say"})
            entry["sessions"].append({"kind": kind, "runner": runner, "session": session})
            findings.append({
                "key": f"unknown:{number}:{kind}:{runner}:{session}:{verdict.get('comment')}",
                "text": f"watchdog: #{number} liveness unknown: {runner} could not say whether "
                        f"the {kind} session {session} is alive; silent since "
                        f"{since or 'an unknown time'}",
                "to": to,
            })

    def _report(self, findings: list[dict], everyone: list[tuple[str, str]]) -> bool:
        """Send each main agent what has not been sent to it. True when a turn started on
        one of them. A finding kept for a session that is the main agent of no open watch
        any more is let go: there is nobody left to tell."""
        reported = [r for r in self.beat.get("reported") or [] if isinstance(r, list) and len(r) == 3]
        done = {tuple(r) for r in reported}
        mains = set(everyone)
        pending = [p for p in self.beat.get("pending") or []
                   if (p.get("runner"), p.get("session"), p.get("key")) not in done
                   and (p.get("runner"), p.get("session")) in mains]
        keys = {(p["runner"], p["session"], p["key"]) for p in pending}
        for finding in findings:
            for runner, session in finding["to"]:
                mark = (runner, session, finding["key"])
                if mark not in done and mark not in keys:
                    pending.append({"key": finding["key"], "text": finding["text"],
                                    "runner": runner, "session": session})
                    keys.add(mark)
        self.beat["pending"] = pending
        if not pending:
            self.beat["main"] = None
            return False
        by_main: dict[tuple[str, str], list[dict]] = {}
        for item in pending:
            by_main.setdefault((item["runner"], item["session"]), []).append(item)
        woke = False
        kept: list[dict] = []
        problems: dict[str, str] = {}
        for (runner, session), items in by_main.items():
            # One line: a runner types what it is handed into a terminal, where a newline submits.
            text = " | ".join(p["text"] for p in items)
            code = self.send(runner, session, text)
            if code in (0, 4):
                reported.extend([runner, session, p["key"]] for p in items)
                woke = woke or code == 0
                continue
            kept.extend(items)
            if code == 2:
                problems[f"{runner} {session}"] = f"{runner} has no session {session}"
                self.err.write(f"watchdog: the main agent's session ({runner} {session}) is "
                               f"gone, so nobody can be told: {text}\n")
            else:
                self.err.write(f"watchdog: {runner}.sh send answered {code}; the findings for "
                               f"{session} are sent again next round\n")
        self.beat["reported"] = reported[-REPORTED_KEEP:]
        self.beat["pending"] = kept
        self.beat["main"] = problems or None
        return woke


# ----------------------------------------------------------------- reading and arming

def read_health(state: Path, now: datetime | None = None) -> tuple[bool, str, dict]:
    """(healthy, why, heartbeat) for the watchdog of this state directory."""
    try:
        beat = statedir.read_json(state / "watchdog.json", {})
    except ValueError as exc:
        return False, f"the heartbeat {state / 'watchdog.json'} is not JSON ({exc})", {}
    beat = beat if isinstance(beat, dict) else {}
    ok, why = health(statedir.holder(state / "watchdog.lock"), beat, now or now_utc())
    return ok, why, beat


def watchdog_py() -> Path:
    return Path(os.environ.get("MMW_WATCHDOG_PY") or Path(__file__).resolve())


def log_tail(path: Path, lines: int = 5) -> str:
    return relay_mod.log_tail(path, lines)


def arm(state: Path, repo: str, wait: float = ARM_WAIT) -> tuple[bool, str]:
    """Make this repository's watchdog healthy. (healthy, what was done or what is wrong)."""
    ok, why, beat = read_health(state)
    if ok:
        return True, why
    holder = statedir.holder(state / "watchdog.lock")
    if holder is not None and not stale(beat, now_utc()):
        # Beating, and unhealthy for another reason (it cannot read the board): starting
        # another would change nothing, and this one reports what fails.
        return False, why
    if holder is not None:
        # A live holder with a stale heartbeat is hung. Its identity was just checked by
        # `holder`, so this pid is that watchdog and nobody else.
        try:
            os.kill(int(holder["pid"]), signal.SIGTERM)
        except (OSError, ValueError, TypeError):
            pass
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline and statedir.holder(state / "watchdog.lock") is not None:
            time.sleep(0.1)
        if statedir.holder(state / "watchdog.lock") is not None:
            return False, f"{why}, and it did not end on SIGTERM"
    log = state / "watchdog.log"
    argv = [sys.executable, str(watchdog_py()), "run", "--repo", repo]
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"--- {iso(now_utc())} arming the watchdog for {repo} ({why})\n")
        fh.flush()
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                                 env=relay_mod.quiet_env(), start_new_session=True, close_fds=True)
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        ok, why, _ = read_health(state)
        if ok:
            return True, f"started it: {why}"
        code = child.poll()
        if code is not None:
            return False, f"it exited {code} as it started; the last lines of {log}: {log_tail(log)}"
        time.sleep(0.1)
    return False, f"it was started and is not healthy after {wait:.0f}s: {why}; the last lines of {log}: {log_tail(log)}"


# ----------------------------------------------------------------- commands

def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"{value} is not a positive number")
    return value


def state_for(repo: str) -> Path:
    try:
        return statedir.state_dir(repo)
    except ValueError as exc:
        raise SystemExit(f"watchdog: {exc}. Pass --repo as owner/name, the way `gh` names it.")


def cmd_run(args) -> int:
    state = state_for(args.repo)

    def stop(signum, frame):
        raise SystemExit(0)

    try:
        with statedir.locked(state / "watchdog.lock", wait=0, purpose=f"watchdog for {args.repo}"):
            signal.signal(signal.SIGTERM, stop)
            signal.signal(signal.SIGINT, stop)
            dog = Watchdog(state, args.repo, poll=args.poll, silence=args.silence, idle=args.idle)
            dog.write_beat()
            while True:
                outcome = dog.round()
                if outcome != "watching":
                    print(f"watchdog for {args.repo}: {outcome} at {dog.beat.get('at')}", flush=True)
                    return 0
                if args.once:
                    return 0
                time.sleep(args.poll)
    except LockHeld as exc:
        print(f"watchdog for {args.repo} already running: {exc}")
        return 0
    except ValueError as exc:
        sys.stderr.write(f"watchdog: a state file is not JSON ({exc}); move it aside and arm again\n")
        return 1


def cmd_arm(args) -> int:
    state = state_for(args.repo)
    ok, why = arm(state, args.repo, args.wait)
    if ok:
        print(f"watchdog for {args.repo}: {why}")
        return 0
    sys.stderr.write(f"watchdog: {why}\n")
    return 1


def cmd_status(args) -> int:
    state = state_for(args.repo)
    ok, why, beat = read_health(state)
    print(json.dumps({"healthy": ok, "why": why, "night_open": night_open(state),
                      "heartbeat": beat}, sort_keys=True, indent=1))
    return 0 if ok and night_open(state) else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="watchdog.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="watch the open watches until none is left or a wake lands")
    run.add_argument("--repo", required=True)
    run.add_argument("--poll", type=positive_int, default=DEFAULT_POLL)
    run.add_argument("--silence", type=positive_int, default=DEFAULT_SILENCE)
    run.add_argument("--idle", type=positive_int, default=DEFAULT_IDLE)
    run.add_argument("--once", action="store_true")
    run.set_defaults(fn=cmd_run)

    arm_ = sub.add_parser("arm", help="start the watchdog unless it is healthy")
    arm_.add_argument("--repo", required=True)
    arm_.add_argument("--wait", type=float, default=ARM_WAIT)
    arm_.set_defaults(fn=cmd_arm)

    status = sub.add_parser("status", help="print the heartbeat and whether it is healthy")
    status.add_argument("--repo", required=True)
    status.set_defaults(fn=cmd_status)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
