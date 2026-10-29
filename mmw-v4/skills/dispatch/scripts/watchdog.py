#!/usr/bin/env python3
"""The watchdog: the second and third layers of liveness for one repository's open watches.

    watchdog.py run --repo O/R [--poll S] [--idle S] [--stuck S] [--nudge S] [--once]
    watchdog.py arm --repo O/R [--wait S]
    watchdog.py status --repo O/R

The tracker only ever brings good news. A worker that finishes writes on its ticket and the
relay wakes whoever waits on it; a worker that dies writes nothing, and on the tracker its
silence looks exactly like work in progress (docs/adr/0008-silence-is-never-a-pass.md).
This process is what notices. It costs no tokens and holds no session: it reads files,
`gh` and the runner adapters, and it is not an agent.

**Three layers, and which one this is.** The first layer is `turn-guard.py`, beside this
file: a hook on every host turn end that re-arms this process and lets the turn end. This file is the
second layer (it beats, it watches the relay) and the third (it asks each held session's
runner what that session is doing). When this process dies, the first layer finds
out at the next turn end; there is no fourth layer, so a crash of the host a
orchestrator runs in is found by a person.

**What it watches.** Every watch the relay has open for the repository (`watches.json` in
the state directory, relay.py): a night — a spec, whose sub-issues are listed again every
round — or tickets outside a night, or a batch of briefs (briefs.py). Each watch has its own orchestrator. A closed sub-issue
of a spec is not read: a closed ticket's worker has handed in its work. A ticket a tickets
watch names is always read. A night is open while `watches.json` names a watch: `relay.py
stop`, which `summary`, `suspend` and `land` run, closes one, and the relay closes the
watch of an orchestrator that has been gone for an hour. A relay that died leaves its
watches open, so a dead relay is an open night with no relay, never a closed one. When no
watch is open this process writes a last heartbeat saying so and exits.

**Each round**, every `--poll` seconds (default 60):

1. The relay's lock record (`relay.lock`: pid and process identity, statedir.py) must
   name a live process that finished a cycle (`cycle_at` in `beat.json`) within its grace.
   Otherwise the alert is `relay down`. Time spent delivering does not count against
   the grace. A relay that has not cycled yet gets its grace from its start time.
   A beat with no cycle stamp uses its last good poll. Tracker-read outages raise no
   alert because the relay reads the missed events when the tracker recovers.
2. Every watched ticket is read in full and folded. The session table covers every
   worker or reviewer still holding a ticket, plus every unreported brief of a watched
   batch. Each session's own runner is asked `liveness <session>` first:

       stopped   post `<kind>.lost` on the ticket, or mark a brief lost
       unknown   record unknown and alert, never post a lost event
       alive     ask the same runner `state <session>`

   A session started on another machine is unknown and is never asked here. A runner
   that cannot be called, times out, exits nonzero or returns an invalid answer is unknown.
   The turn state determines the session table's result:

       dialog<TAB>line   alert with that screen line in this round
       unknown          record unknown and alert, never post a lost event
       stopped          post `<kind>.lost`, or mark a brief lost
       working          alert once if no progress for `--stuck` seconds (7200)
       idle             alert once after `--idle` seconds (3600) without worktree activity,
                        unless another session's result or landing is pending

   Worktree activity is the latest commit time or file modification time in the worktree
   named by the session's start event or brief batch record, bounded below by its start
   time. An idle host with worktree activity within `--idle` is working. Idle alerts use
   only that activity. Stuck alerts use the later of worktree activity and the ticket's
   newest event, or the brief's send time. Each alert's key includes its session and its
   activity reference time, so a new event can start a new stuck interval across restarts.
   A hold with no session to ask is unknown, and unreadable events are an alert.
3. A delivered row in `queue.jsonl` that has not been acked for `--nudge` seconds
   (default 1800) brings one reminder to its watch's orchestrator. Its sequence number
   identifies the reminder in `reported`, so another round or restart does not repeat it.

**Alerts wake the orchestrator directly**, through its runner's `send`, in one message
on one line, each alert beginning `watchdog:`. They do not use the relay queue because
that relay may be down. Ticket alerts go only to their watch's orchestrator. Relay and
wake-queue alerts go to every watch's orchestrator. Unsent alerts are rechecked each
round, so a resolved condition is not delivered later.

    0      delivered and a turn started. This process exits after the round's sends.
           That turn's end re-arms it.
    4      handed over, not confirmed. Recorded as reported and never sent again.
           This process keeps running.
    3, 5+  nothing was sent. Rechecked and tried again next round.
    2      the orchestrator's session is gone. Recorded, kept, nobody to tell.

The alerts exactly:

    watchdog: relay down (<what is wrong>); details: python3 <this file> status --repo <repo>
    watchdog: #<n> events unreadable
    watchdog: #<n> is held with no session to ask
    watchdog: <ticket or brief> liveness unknown: the <kind> session <session> on <runner> <why>
    watchdog: <ticket or brief> <kind> session <session> on <runner> is on a dialog: <line>
    watchdog: <ticket or brief> silent since <time> with nothing to wait on
    watchdog: <ticket or brief> <kind> session <session> on <runner> has a stuck turn
    watchdog: #<n> is waiting on the orchestrator: <unacked delivered wake>
    watchdog: wake queue unreadable: <what failed>

**The heartbeat and the lock.** `run` holds `watchdog.lock` for as long as it runs, so a
repository has one watchdog, serving every watch; the lock's record names its pid and
process identity, the same convention as the relay's. It writes `watchdog.json`, the
heartbeat, at start, after every ticket and at the end of every round, with that same pid
and identity. A heartbeat is fresh when its age is within the tolerance
`max(300, poll + MARGIN)` seconds. MARGIN is one adapter call plus one gh read
(60 + 120 seconds), the longest wait between two beats. The watchdog is healthy when
its lock names a live process, that process wrote its heartbeat, and the heartbeat is
fresh. A pid alone is not enough because another process can receive a dead watchdog's pid.

**Only this machine's sessions are asked.** Every `*.started` records the machine it was
started on (`machine`, the hostname). A runner answers for its own machine, and asked about
a session started on another it would say `stopped` of a worker that is alive; so a session
from another machine is recorded as unknown and reported, never asked and never lost.

**Arming.** `arm` does nothing when the watchdog is healthy, and ends nothing that still
beats. Otherwise it ends a hung
one (a live holder whose heartbeat is past its tolerance, identity checked, SIGTERM), starts
`run` as a process of its own session with its output appended to `watchdog.log`, and waits
up to `--wait` seconds (default 5) for it to be healthy. `MMW_WATCHDOG_PY` names the script
that is started, for tests and for trying the hook against a watchdog that will not start.

Files in the state directory, beside the relay's:

    watchdog.lock   held for as long as a `run` runs: one watchdog per repository
    watchdog.json   the heartbeat: pid, identity, machine, at, poll, tolerance,
                    idle, stuck, nudge, watches (the open watches as last read, with their orchestrators),
                    held, briefs (each open brief, `<batch>/<n>`), unknown,
                    lost, relay, pending
                    (alerts not yet sent, each with the runner and session it is for),
                    reported ([runner, session, key] of each once-only alert sent),
                    main (per orchestrator, why its alerts could not be sent), closed, reads (billed and
                    not-modified comment-list reads since this process started; null for a
                    `Board` that does not count them)
    watchdog.log    what every started watchdog printed, appended

Exit codes:

    run      0 ran until no watch was open, until it woke an orchestrator, or one round with
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
import briefs  # noqa: E402

events = relay_mod.events

DEFAULT_POLL = 60
DEFAULT_IDLE = 3600
DEFAULT_STUCK = 7200
DEFAULT_NUDGE = 1800
BASE_TOLERANCE = 300
ARM_WAIT = 5.0
ADAPTER_TIMEOUT = 60
# The longest a healthy watchdog goes between two heartbeats beyond its sleep: it beats
# after every ticket read and every runner asked, so one gh read and one adapter call.
MARGIN = ADAPTER_TIMEOUT + relay_mod.GH_TIMEOUT
POST_TIMEOUT = 60

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

    `holder` is statedir.holder(watchdog.lock). Its live process must have written the
    heartbeat, identified by both pid and process identity, within the tolerance.
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
    return True, f"the watchdog (pid {pid}) beat {max(age, 0)}s ago"


def stale(beat: dict | None, now: datetime) -> bool:
    """A heartbeat older than its tolerance: the watchdog writing it is hung, not slow."""
    at = parse_iso((beat or {}).get("at"))
    return at is None or (now - at).total_seconds() > tolerance((beat or {}).get("poll"))


def judge(fold: dict) -> dict:
    if fold.get("unreadable"):
        return {"state": "unreadable",
                "comments": [item.get("comment") for item in fold["unreadable"]]}
    if not fold.get("held"):
        return {"state": "free"}
    last = fold.get("last") or {}
    return {"state": "held", "since": last.get("at"), "comment": last.get("comment"),
            "sessions": fold.get("holders") or [], "passed": bool(fold.get("passed"))}


def night_open(state: Path) -> bool:
    """Whether a night — any watch — is open on this state directory: the relay's
    `watches.json` names one. `relay.py stop` closes a watch, and the relay closes the
    watch of an orchestrator gone for an hour; a relay that died leaves its watches open. A
    `watches.json` that cannot be read is not a closed night."""
    try:
        return bool(relay_mod.read_watches(state))
    except ValueError:
        return True


DOWN = "down"
NEXT = "nothing is relaying: `dispatch.sh advance <spec>` starts it again for the " \
       "recorded orchestrator, or `dispatch.sh open-ticket <n>` for a ticket outside " \
       "a night; "


def relay_problem(state: Path, now: datetime) -> dict | None:
    """A relay-down alert, or None when the relay is running within its grace.

    cycle_at records every cycle, including a failed tracker read. Delivery time does
    not count against the grace. A beat without cycle_at uses the last good poll.
    """
    holder = statedir.holder(state / "relay.lock")
    try:
        beat = statedir.read_json(state / "beat.json", {})
        record = statedir.read_json(state / "relay.json", {})
    except ValueError as exc:
        return {"kind": DOWN, "why": f"the relay's state cannot be read ({exc})",
                "key": f"relay:{DOWN}:unreadable"}
    beat = beat if isinstance(beat, dict) else {}
    record = record if isinstance(record, dict) else {}
    last = beat.get("at")
    cycled = beat.get("cycle_at")
    grace = beat.get("grace") if isinstance(beat.get("grace"), (int, float)) else record.get("grace")
    if not isinstance(grace, (int, float)):
        grace = 3 * relay_mod.DEFAULT_INTERVAL
    failure = f"; its last failed poll: {beat.get('failure')}" if beat.get("failure") else ""
    started = record.get("started") or ""

    def finding(kind: str, why: str) -> dict:
        return {"kind": kind, "why": why, "key": f"relay:{kind}:{last or 'never'}:{started}"}

    if holder is None:
        return finding(DOWN, f"no relay is running (last good poll: {last or 'never'}){failure}")
    pid = holder.get("pid")
    began = parse_iso(record.get("started"))
    within_start_grace = began is not None and (now - began).total_seconds() <= grace
    unattended = relay_mod.Relay._unattended(beat, now)
    since_cycle = relay_mod.Relay._since_cycle(beat, now)

    if since_cycle is None:
        if not last:
            if within_start_grace:
                return None
            return finding(DOWN, f"the relay (pid {pid}) has made no good poll since it "
                                 f"started{failure}")
        if unattended > grace:
            return finding(DOWN, f"the relay (pid {pid}) last polled at {last}, "
                                 f"{int(unattended)}s ago, past its grace of "
                                 f"{int(grace)}s{failure}")
        return None

    if since_cycle > grace:
        return finding(DOWN, f"the relay (pid {pid}) last finished a cycle at {cycled}, "
                             f"{int(since_cycle)}s ago, past its grace of {int(grace)}s "
                             f"(last good poll: {last or 'never'}){failure}")
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


def ask_state(runner: str, session: str) -> str:
    adapter = runners_dir() / f"{runner}.sh"
    if not runner or not adapter.is_file():
        return "unknown"
    try:
        run = subprocess.run(["bash", str(adapter), "state", session], capture_output=True,
                             text=True, env=relay_mod.quiet_env(), timeout=ADAPTER_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    answer = (run.stdout or "").strip()
    if run.returncode == 0 and "\n" not in answer:
        if answer in ("working", "idle", "stopped", "unknown"):
            return answer
        if answer.startswith("dialog\t") and answer.partition("\t")[2].strip():
            return answer
    return "unknown"


def worktree_activity(worktree: str | None, started: str | None, now: datetime) -> datetime:
    latest = parse_iso(started) or datetime.min.replace(tzinfo=timezone.utc)
    if not worktree:
        return latest
    try:
        commit = subprocess.run(["git", "-C", worktree, "log", "-1", "--format=%ct"],
                                capture_output=True, text=True, timeout=ADAPTER_TIMEOUT)
        if commit.returncode == 0 and commit.stdout.strip():
            at = datetime.fromtimestamp(int(commit.stdout.strip()), timezone.utc)
            if at <= now:
                latest = max(latest, at)
        files = subprocess.run(["git", "-C", worktree, "ls-files", "-z", "--cached",
                                "--others"], capture_output=True,
                               text=True, timeout=ADAPTER_TIMEOUT)
        if files.returncode == 0:
            for name in files.stdout.split("\0"):
                if name:
                    try:
                        at = datetime.fromtimestamp((Path(worktree) / name).lstat().st_mtime,
                                                    timezone.utc)
                        if at <= now:
                            latest = max(latest, at)
                    except OSError:
                        pass
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return latest


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
    """One repository's watchdog: its rounds, its heartbeat, its alerts."""

    def __init__(self, state: Path, repo: str, board=None,
                 ask: Callable[[str, str], str] = ask_liveness,
                 send: Callable[[str, str, str], int] = send_to,
                 post: Callable[..., tuple[bool, str]] = post_lost,
                 clock: Callable[[], datetime] = now_utc,
                 poll: int = DEFAULT_POLL,
                 idle: int = DEFAULT_IDLE, stuck: int = DEFAULT_STUCK, nudge: int = DEFAULT_NUDGE,
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
        self.idle = idle
        self.stuck = stuck
        self.nudge = nudge
        self.pid = pid if pid is not None else os.getpid()
        self.identity = identity if identity is not None else statedir.own_identity()
        self.machine = machine if machine is not None else socket.gethostname()
        self.err = err or sys.stderr
        previous = self._read("watchdog.json", {})
        previous = previous if isinstance(previous, dict) else {}
        self.beat = {
            "pid": self.pid, "identity": self.identity, "started": iso(self.clock()),
            "poll": poll, "tolerance": tolerance(poll), "idle": idle,
            "stuck": stuck, "nudge": nudge,
            "round": 0,
            "watches": previous.get("watches") if isinstance(previous.get("watches"), dict) else {},
            "held": None, "briefs": [], "unknown": {}, "lost": {}, "relay": None,
            "pending": [p for p in previous.get("pending") or []
                        if isinstance(p, dict) and p.get("runner") and p.get("session")],
            "reported": [r for r in previous.get("reported") or []
                         if isinstance(r, list) and len(r) == 3],
            "main": None, "closed": None, "machine": self.machine,
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
        tickets watch) and `main`, the (runner, session) its alerts go to. Tickets
        watches are taken first, as the relay takes them. A closed sub-issue of a spec is
        left out; a spec whose sub-issues cannot be listed is a failure."""
        tickets: dict[int, dict] = {}
        ordered = sorted(watches.items(), key=lambda kv: (0 if kv[1].get("tickets") else 1, kv[0]))
        for key, entry in ordered:
            if entry.get("briefs"):
                continue
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
        """One round. Returns `closed` (no watch is open), `woke` (an orchestrator was woken
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
        self.beat["relay"] = f"relay {problem['kind']}: {problem['why']}" if problem else None
        if problem:
            findings.append({
                "key": problem["key"],
                "text": f"watchdog: relay {problem['kind']} ({problem['why']}); "
                        f"{NEXT}"
                        f"details: python3 {Path(__file__).resolve()} "
                        f"status --repo {self.repo}",
                "to": everyone,
            })

        try:
            wakes = relay_mod.Relay(self.state).rows()
        except (relay_mod.Refusal, LockHeld) as exc:
            wakes = []
            failures.append(f"the wake queue: {exc}")
            findings.append({"key": f"queue:{exc}",
                             "text": f"watchdog: wake queue unreadable: {' '.join(str(exc).split())}",
                             "to": everyone})
        tickets = self.watched(watches, failures)
        read_all = not failures
        held: list[int] = []
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
            verdict = judge(fold)
            self._waiting(number, home, wakes, findings)
            state = verdict["state"]
            if state == "unreadable":
                held.append(number)
                unknown[str(number)] = {"why": "events unreadable"}
                findings.append({"key": f"unreadable:{number}:{verdict['comments']}",
                                 "text": f"watchdog: #{number} events unreadable; leave "
                                         f"this alert as a comment for the user",
                                 "to": to})
            elif state == "free":
                pass
            else:
                held.append(number)
                self._sessions(number, home["spec"], verdict, unknown, findings, to)
            self.beat["unknown"] = unknown
            self.write_beat()

        self.beat["briefs"] = self._briefs(watches, unknown, findings)
        # A round that could not read every ticket does not know that nothing is held.
        self.beat.update(held=held if read_all else (held or None), unknown=unknown)
        woke = self._report(findings)
        self.write_beat()
        return "woke" if woke else "watching"

    def _waiting(self, number: int, home: dict, wakes: list[dict],
                 findings: list[dict]) -> None:
        for wake in wakes:
            if wake.get("ticket") != number or wake.get("watch") != home["key"]:
                continue
            delivered = parse_iso(wake.get("delivered"))
            if delivered is None or (self.clock() - delivered).total_seconds() < self.nudge:
                continue
            findings.append({"key": f"wait:{wake['seq']}",
                             "text": f"watchdog: #{number} is waiting on the orchestrator: "
                                     f"unacked delivered wake {wake['seq']}; read the ticket "
                                     f"and have its recipient ack the wake through dispatch.sh",
                             "to": [home["main"]]})

    def _observe(self, record: dict) -> str:
        if record.get("machine", self.machine) != self.machine:
            return "unknown"
        answer = self.ask(record.get("runner") or "", record.get("session") or "")
        self.write_beat()
        if answer != "alive":
            return answer if answer == "stopped" else "unknown"
        answer = ask_state(record.get("runner") or "", record.get("session") or "")
        self.write_beat()
        return answer

    def _session_alert(self, record: dict, answer: str, label: str, unknown: dict,
                       findings: list[dict], to: list[tuple[str, str]], waiting: bool,
                       progress: dict) -> None:
        kind, runner, session = record["kind"], record.get("runner"), record.get("session")
        machine = record.get("machine", self.machine)
        if answer == "idle" and not waiting:
            waiting = any(not briefs.complete(self.state, b["batch"])
                          for b in briefs.open_batches(self.state, (runner, session)))
        activity = worktree_activity(record.get("worktree"),
                                     record.get("started_at") or record.get("at"), self.clock())
        since = iso(activity)
        key = f"{label}:{kind}:{runner}:{session}"
        if answer == "unknown":
            entry = unknown.setdefault(label.lstrip("#"), {"sessions": [], "since": since,
                                                          "why": "the runner could not say"})
            details = {"kind": kind, "runner": runner, "session": session}
            if machine != self.machine:
                details["machine"] = machine
                why = (f"was started on {machine or 'an unrecorded machine'}, not on "
                       f"{self.machine}, and only that machine can ask {runner}")
            else:
                why = "has unknown liveness or turn state"
            entry["sessions"].append(details)
            findings.append({"key": f"unknown:{key}:{progress.get('comment')}",
                             "text": f"watchdog: {label} liveness unknown: the {kind} session "
                                     f"{session} on {runner} {why}; inspect that session "
                                     f"through its runner before resuming it",
                             "to": to})
        elif answer.startswith("dialog\t"):
            line = " ".join(answer.partition("\t")[2].split())
            findings.append({"key": f"dialog:{key}:{line}",
                             "text": f"watchdog: {label} {kind} session {session} on {runner} "
                                     f"is on a dialog: {line}; resolve that dialog on its runner",
                             "to": to})
        elif answer == "idle" and not waiting and (self.clock() - activity).total_seconds() >= self.idle:
            findings.append({"key": f"idle:{key}:{since}",
                             "text": f"watchdog: {label} silent since {since} with nothing to "
                                     f"wait on: its {kind} {session} on {runner} is idle; "
                                     f"resume that session through dispatch.sh",
                             "to": to})
        elif answer == "working":
            activity = max(activity, parse_iso(progress.get("since")) or activity)
            if (self.clock() - activity).total_seconds() < self.stuck:
                return
            since = iso(activity)
            findings.append({"key": f"stuck:{key}:{since}",
                             "text": f"watchdog: {label} {kind} session {session} on {runner} "
                                     f"has a stuck turn with no progress since {since}; "
                                     f"inspect its running tool through the runner",
                             "to": to})

    def _sessions(self, number: int, spec: int | None, verdict: dict, unknown: dict,
                  findings: list[dict], to: list[tuple[str, str]]) -> None:
        records = verdict["sessions"]
        since = verdict.get("since")
        if not records:
            unknown[str(number)] = {"why": "held by no session to ask", "since": since}
            findings.append({"key": f"unheld:{number}:{verdict.get('comment')}",
                             "text": f"watchdog: #{number} is held with no session to ask; "
                                     f"read its events before dispatch.sh retract {number}",
                             "to": to})
            return
        observed = [(r, self._observe(r)) for r in records]
        reviewer_pending = any(r["kind"] == "reviewer" for r in records)
        for record, answer in observed:
            kind, runner, session = record["kind"], record.get("runner"), record.get("session")
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
            waiting = verdict["passed"] or (kind == "worker" and reviewer_pending)
            self._session_alert(record, answer, f"#{number}", unknown, findings, to, waiting, verdict)

    def _briefs(self, watches: dict[str, dict], unknown: dict, findings: list[dict]) -> list[str]:
        batches = {entry["briefs"]: entry for entry in watches.values() if entry.get("briefs")}
        still: list[str] = []
        for child in briefs.open_children(self.state):
            if child["batch"] not in batches:
                continue
            name = f"{child['batch']}/{child['n']}"
            batch = briefs.batch_record(self.state, child["batch"]) or {}
            record = {**child, "kind": batch.get("role") or "researcher",
                      "worktree": child.get("worktree") or batch.get("worktree")}
            runner, session = child.get("runner") or "", child.get("session") or ""
            answer = self._observe(record)
            if answer == "stopped":
                why = (f"{runner} answered that its session {session} is stopped, and it had "
                       f"not reported")
                if briefs.mark_lost(self.state, child["batch"], child["n"], why):
                    self.err.write(f"watchdog: brief {name} marked lost: {why}\n")
                continue
            self._session_alert(record, answer, f"brief {name}", unknown, findings,
                                [relay_mod.main_of(batches[child["batch"]])], False,
                                {"since": child.get("at"), "comment": child.get("at")})
            still.append(name)
        return still

    def _report(self, findings: list[dict]) -> bool:
        """Send each orchestrator what has not been sent to it. True when a turn started on
        one of them. An alert kept for a session that is the orchestrator of no open watch
        any more is let go: there is nobody left to tell."""
        reported = [r for r in self.beat.get("reported") or [] if isinstance(r, list) and len(r) == 3]
        done = {tuple(r) for r in reported}
        pending = []
        keys = set()
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
                for p in items:
                    mark = [runner, session, p["key"]]
                    reported.append(mark)
                woke = woke or code == 0
                continue
            kept.extend(items)
            if code == 2:
                problems[f"{runner} {session}"] = f"{runner} has no session {session}"
                self.err.write(f"watchdog: the orchestrator's session ({runner} {session}) is "
                               f"gone, so nobody can be told: {text}\n")
            else:
                self.err.write(f"watchdog: {runner}.sh send answered {code}; the alerts for "
                               f"{session} are sent again next round\n")
        self.beat["reported"] = reported
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
    if holder is not None and (
            (beat.get("pid"), beat.get("identity")) != (holder["pid"], holder["identity"])
            or not stale(beat, now_utc())):
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
        # The state directory as working directory, as relay.py's `spawn` says why.
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                                 env=relay_mod.quiet_env(), cwd=state, start_new_session=True,
                                 close_fds=True)
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
            dog = Watchdog(state, args.repo, poll=args.poll, idle=args.idle,
                           stuck=args.stuck, nudge=args.nudge)
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
    run.add_argument("--idle", type=positive_int, default=DEFAULT_IDLE)
    run.add_argument("--stuck", type=positive_int, default=DEFAULT_STUCK)
    run.add_argument("--nudge", type=positive_int, default=DEFAULT_NUDGE)
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
