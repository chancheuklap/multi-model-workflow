#!/usr/bin/env python3
"""The watchdog: the second and third layers of liveness for one repository's open night.

    watchdog.py run --repo O/R [--poll S] [--silence S] [--once]
    watchdog.py arm --repo O/R [--wait S]
    watchdog.py status --repo O/R

The board only ever brings good news. A worker that finishes writes on its ticket and the
relay wakes whoever waits on it; a worker that dies writes nothing, and on the board its
silence looks exactly like work in progress (docs/adr/0008-silence-is-never-a-pass.md).
This process is what notices. It costs no tokens and holds no session: it reads files,
`gh` and the runner adapters, and it is not an agent.

**Three layers, and which one this is.** The first layer is `turn-guard.py`, beside this
file: a hook on the main agent's own turn end that re-arms this process and will not let
that turn end while tickets are held and this process is not healthy. This file is the
second layer (it beats, it watches the relay) and the third (it asks a silent ticket's
runner whether its worker is still there). When this process dies, the first layer finds
out at the main agent's next turn end; there is no fourth layer, so a crash of the host
the main agent runs in is found by a person.

**What it watches.** The tickets of the night the relay was started for: `relay.json` in
the state directory names the spec (whose sub-issues are read again every round) or the
tickets. A night is open while `relay.json` is there or the relay's `beat.json` still holds
a last good poll: `relay.py stop`, which `summary`, `suspend` and `land` run, clears the
latter and the relay removes the former on its way out. A relay that died leaves one of the
two behind, so a dead relay is an open night with no relay, never a closed one. When the
night is closed this process writes a last heartbeat saying so and exits.

**Each round**, every `--poll` seconds (default 60):

1. The relay. Its lock record (`relay.lock`: pid and process identity, statedir.py) must
   name a live process, and its last good poll must be within its grace, less the time it
   spent delivering. A relay that has not polled yet is given its grace from the moment it
   started. Otherwise that is a finding: `relay down`.
2. Every watched ticket is read in full and folded (`events.py` of the verify-ticket
   skill). A ticket not held is skipped. A held ticket in the waiting step — the fold's
   `waiting`: a `worker.queued` its run still waits under, because no product slot was
   free — is skipped: queueing is not dying. A held ticket whose newest event is less than
   `--silence` seconds old (default 600) is skipped.
3. Every other held ticket is silent. For each live worker session its fold names — the
   (runner, session) pair of its `worker.started` — this asks that runner's adapter, and no
   other runner, `runners/<runner>.sh liveness <session>`:

       alive     nothing
       stopped   `worker.lost` is posted on the ticket, naming that pair. It is the one
                 event not written by the agent it is about, and this process is its one
                 writer. It ends that session's hold, and the relay wakes the main agent
                 with `#<n> worker.lost`.
       unknown   recorded as unknown in the heartbeat, and a finding. Never rendered as
                 alive, never a `worker.lost`: an answer the adapter could not give — or a
                 missing adapter, a non-zero exit, a timeout — is not a death.

   A silent ticket held by no live worker session (a claim no start names, or a reviewer
   or verifier left holding it) has nobody to ask, and is a finding too. So is a ticket
   whose events cannot be read.

**Findings wake the main agent directly**, through the `send` of the runner the relay has
it registered under (`recipient.json`), one message on one line, each finding in it beginning `watchdog:`. Not
through the relay's queue: the relay may be the thing that is down. Each finding is sent
once — keyed by what it is about and the ticket's newest event, or the relay's last good
poll — and never again for the same stretch, across restarts of this process. What `send`
answered decides what happens next:

    0      delivered and a turn started. This process exits: the main agent is now in a
           turn, and that turn's end re-arms it (one-shot, re-armed by the hook)
    4      handed over, not confirmed: not sent again, and this process keeps running
    3, 5+  nothing was sent: kept, and sent again next round
    2      the main agent's session is gone: recorded, kept, nobody to tell

**The heartbeat and the lock.** `run` holds `watchdog.lock` for as long as it runs, so a
repository has one watchdog; the lock's record names its pid and process identity, the
same convention as the relay's. It writes `watchdog.json`, the heartbeat, at start, after
every ticket and at the end of every round, with that same pid and identity. A heartbeat
is fresh when its age is within the tolerance `max(300, poll + 60)` seconds: a fixed number
would read a healthy watchdog as dead as soon as its poll grew past it. The watchdog is
healthy when the lock names a live process, the heartbeat was written by that process, and
it is fresh. A pid alone is never enough: a dead watchdog's pid can be handed to another
process, and that process is not a watchdog.

**Arming.** `arm` does nothing when the watchdog is healthy. Otherwise it ends a hung one
(a live holder whose heartbeat is past its tolerance, identity checked, SIGTERM), starts
`run` as a process of its own session with its output appended to `watchdog.log`, and waits
up to `--wait` seconds (default 5) for it to be healthy. `MMW_WATCHDOG_PY` names the script
that is started, for tests and for trying the hook against a watchdog that will not start.

Files in the state directory, beside the relay's:

    watchdog.lock   held for as long as a `run` runs: one watchdog per repository
    watchdog.json   the heartbeat: pid, identity, at, poll, tolerance, silence, watch, held,
                    waiting, unknown, lost, relay, pending, reported, main, closed
    watchdog.log    what every started watchdog printed, appended

Exit codes:

    run      0 ran until the night closed, until it woke the main agent, or one round with
             --once; 1 refused (the repository name, a state file that is not JSON). Another
             watchdog already running is 0: arming twice is not an error
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
BASE_TOLERANCE = 300
MARGIN = 60
ARM_WAIT = 5.0
ADAPTER_TIMEOUT = 60
POST_TIMEOUT = 60
REPORTED_KEEP = 200

LOST = "worker.lost"
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
    """How old a heartbeat may be and still be fresh: `max(300, poll + 60)` seconds.

    A watchdog beats once a round and sleeps `poll` seconds between rounds, so a healthy
    one's heartbeat is up to `poll` old plus the round's own work. A fixed tolerance stops
    bounding that the moment the poll grows past it.
    """
    try:
        poll = int(poll)
    except (TypeError, ValueError):
        poll = DEFAULT_POLL
    return max(BASE_TOLERANCE, poll + MARGIN)


def health(holder: dict | None, beat: dict | None, now: datetime) -> tuple[bool, str]:
    """Whether a watchdog is healthy, from its lock's live holder and its heartbeat.

    `holder` is `statedir.holder(watchdog.lock)`: the lock's record when its pid runs now
    with the recorded identity, else None. Healthy is three things together: a live holder,
    a heartbeat that holder wrote (same pid and identity: a heartbeat left by an earlier
    watchdog proves nothing about this one), and that heartbeat within `tolerance`.
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


def judge(fold: dict, now: datetime, silence: int) -> dict:
    """What one ticket's fold says the third layer should do with it.

        {"state": "unreadable"}                        a comment's event cannot be read
        {"state": "free"}                              no hold on it
        {"state": "waiting", "since": T}               in the waiting step: the fold's
                                                       `waiting`, the `worker.queued` its
                                                       run still waits under
        {"state": "recent", "since": T}                newest event younger than `silence`
        {"state": "silent", "since": T, "pairs": [...], "comment": C}
                                                       held and silent; `pairs` is every
                                                       live worker's (runner, session)
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
                "since": waiting.get("at") if isinstance(waiting, dict) else since}
    at = parse_iso(since)
    if at is not None and (now - at).total_seconds() < silence:
        return {"state": "recent", "since": since}
    pairs = [(r.get("runner"), r.get("session")) for r in fold.get("live_workers") or []
             if r.get("runner") and r.get("session")]
    return {"state": "silent", "since": since, "pairs": pairs, "comment": last.get("comment")}


def night_open(state: Path) -> bool:
    """Whether a night is open on this state directory: the relay's `relay.json` is there,
    or its `beat.json` still holds a last good poll. `relay.py stop` clears the one and the
    relay removes the other on its way out; a relay that died leaves one behind. A
    `beat.json` that cannot be read is not a closed night."""
    if (state / "relay.json").exists():
        return True
    try:
        beat = statedir.read_json(state / "beat.json", {})
    except ValueError:
        return True
    return bool(isinstance(beat, dict) and beat.get("at"))


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


def lost_body(ticket: int, spec: int | None, runner: str, session: str,
              since: str | None) -> str:
    """The comment body of `worker.lost` for (runner, session) on `ticket`."""
    return events.build(
        LOST, ticket=ticket, spec=spec, runner=runner, session=session,
        line=(f"Worker {runner} session {session} is gone: {runner} says it has stopped, and "
              f"the ticket has had no event since {since or 'its start'}."),
    )


def post_lost(repo: str, ticket: int, spec: int | None, runner: str, session: str,
              since: str | None) -> tuple[bool, str]:
    """Post `worker.lost` for (runner, session) on `ticket`. (posted, what went wrong)."""
    body = lost_body(ticket, spec, runner, session, since)
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
                 pid: int | None = None, identity: str | None = None, err=None):
        self.state = Path(state)
        self.repo = repo
        self.board = board if board is not None else relay_mod.Board(repo)
        self.ask = ask
        self.send = send
        self.post = post
        self.clock = clock
        self.poll = poll
        self.silence = silence
        self.pid = pid if pid is not None else os.getpid()
        self.identity = identity if identity is not None else statedir.own_identity()
        self.err = err or sys.stderr
        previous = self._read("watchdog.json", {})
        previous = previous if isinstance(previous, dict) else {}
        self.beat = {
            "pid": self.pid, "identity": self.identity, "started": iso(self.clock()),
            "poll": poll, "tolerance": tolerance(poll), "silence": silence, "round": 0,
            "watch": previous.get("watch"),
            "held": None, "waiting": [], "unknown": {}, "lost": {}, "relay": None,
            "pending": previous.get("pending") or [],
            "reported": previous.get("reported") or [],
            "main": None, "closed": None,
        }

    # ------------------------------------------------------------- files

    def _read(self, name: str, default):
        return statedir.read_json(self.state / name, default)

    def write_beat(self) -> None:
        """The heartbeat, stamped now, written in one step. Only the lock holder writes it."""
        self.beat["at"] = iso(self.clock())
        statedir.write_atomic(self.state / "watchdog.json",
                              json.dumps(self.beat, sort_keys=True, indent=1) + "\n")

    # ------------------------------------------------------------- one round

    def watched(self) -> tuple[list[int], int | None]:
        """The tickets of the open night and its spec (None for a night of tickets)."""
        try:
            record = self._read("relay.json", {})
        except ValueError:
            record = {}
        watch = (record or {}).get("watch") if isinstance(record, dict) else None
        if watch:
            self.beat["watch"] = watch
        watch = self.beat.get("watch") or {}
        if watch.get("spec"):
            return self.board.sub_issues(int(watch["spec"])), int(watch["spec"])
        return [int(n) for n in watch.get("tickets") or []], None

    def round(self) -> str:
        """One round. Returns `closed` (the night is over), `woke` (the main agent was woken
        and is in a turn) or `watching`."""
        now = self.clock()
        self.beat["round"] += 1
        if not night_open(self.state):
            self.beat["closed"] = iso(now)
            self.write_beat()
            return "closed"

        findings: list[dict] = []
        problem = relay_problem(self.state, now)
        self.beat["relay"] = problem
        if problem:
            beat = self._read_quiet("beat.json")
            record = self._read_quiet("relay.json")
            findings.append({
                "key": f"relay:{beat.get('at') or 'never'}:{record.get('started') or ''}",
                "text": f"watchdog: relay down ({problem}); details: python3 {Path(__file__).resolve()} "
                        f"status --repo {self.repo}",
            })

        read_all = True
        try:
            tickets, spec = self.watched()
        except relay_mod.PollError as exc:
            self.err.write(f"watchdog: could not read the night's tickets: {exc}\n")
            tickets, spec = [], None
            read_all = False
        held: list[int] = []
        waiting: list[int] = []
        unknown: dict = {}
        for number in dict.fromkeys(tickets):
            try:
                comments = self.board.comments(number, None)
            except relay_mod.PollError as exc:
                self.err.write(f"watchdog: could not read #{number}: {exc}\n")
                self.beat["failure"] = f"#{number}: {exc}"
                read_all = False
                continue
            fold = events.fold(comments, issue=number)
            verdict = judge(fold, now, self.silence)
            state = verdict["state"]
            if state == "unreadable":
                held.append(number)
                unknown[str(number)] = {"why": "events unreadable"}
                findings.append({"key": f"unreadable:{number}:{verdict['comments']}",
                                 "text": f"watchdog: #{number} events unreadable"})
            elif state == "free":
                pass
            elif state == "waiting":
                held.append(number)
                waiting.append(number)
            elif state == "recent":
                held.append(number)
            else:
                held.append(number)
                self._silent(number, spec, verdict, unknown, findings)
            self.beat["unknown"] = unknown
            self.write_beat()

        # A round that could not read every ticket does not know that nothing is held.
        self.beat.update(held=held if read_all else (held or None), waiting=waiting,
                         unknown=unknown)
        if read_all:
            self.beat.pop("failure", None)
        woke = self._report(findings)
        self.write_beat()
        return "woke" if woke else "watching"

    def _read_quiet(self, name: str) -> dict:
        try:
            value = self._read(name, {})
        except ValueError:
            return {}
        return value if isinstance(value, dict) else {}

    def _silent(self, number: int, spec: int | None, verdict: dict, unknown: dict,
                findings: list[dict]) -> None:
        """The third layer, for one held and silent ticket."""
        since = verdict.get("since")
        if not verdict["pairs"]:
            unknown[str(number)] = {"why": "held by no live worker session", "since": since}
            findings.append({
                "key": f"unheld:{number}:{verdict.get('comment')}",
                "text": f"watchdog: #{number} is held with no worker session to ask, silent "
                        f"since {since or 'an unknown time'}",
            })
            return
        for runner, session in verdict["pairs"]:
            answer = self.ask(runner, session)
            if answer == "alive":
                continue
            if answer == "stopped":
                posted, why = self.post(self.repo, number, spec, runner, session, since)
                if posted:
                    self.beat["lost"][str(number)] = {"runner": runner, "session": session,
                                                      "at": iso(self.clock())}
                    self.err.write(f"watchdog: posted worker.lost on #{number} for {runner} "
                                   f"session {session}\n")
                else:
                    self.err.write(f"watchdog: {runner} says session {session} of #{number} "
                                   f"stopped, and worker.lost could not be posted: {why}; "
                                   f"it is tried again next round\n")
                continue
            unknown[str(number)] = {"runner": runner, "session": session, "since": since,
                                    "why": "the runner could not say"}
            findings.append({
                "key": f"unknown:{number}:{runner}:{session}:{verdict.get('comment')}",
                "text": f"watchdog: #{number} liveness unknown: {runner} could not say whether "
                        f"session {session} is alive; silent since {since or 'an unknown time'}",
            })

    def _report(self, findings: list[dict]) -> bool:
        """Send what has not been sent to the main agent. True when a turn started on it."""
        reported = list(self.beat.get("reported") or [])
        pending = [p for p in self.beat.get("pending") or [] if p.get("key") not in reported]
        keys = {p["key"] for p in pending}
        for finding in findings:
            if finding["key"] not in reported and finding["key"] not in keys:
                pending.append(finding)
                keys.add(finding["key"])
        self.beat["pending"] = pending
        if not pending:
            return False
        main = self._read_quiet("recipient.json")
        if not main.get("runner") or not main.get("session"):
            self.beat["main"] = "no main agent is registered with the relay"
            self.err.write("watchdog: no main agent is registered (recipient.json), so these "
                           "findings are kept: " + "; ".join(p["text"] for p in pending) + "\n")
            return False
        # One line: a runner types what it is handed into a terminal, where a newline submits.
        text = " | ".join(p["text"] for p in pending)
        code = self.send(main["runner"], main["session"], text)
        if code in (0, 4):
            self.beat["reported"] = (reported + [p["key"] for p in pending])[-REPORTED_KEEP:]
            self.beat["pending"] = []
            self.beat["main"] = None
            return code == 0
        if code == 2:
            self.beat["main"] = f"{main['runner']} has no session {main['session']}"
            self.err.write(f"watchdog: the main agent's session ({main['runner']} "
                           f"{main['session']}) is gone, so nobody can be told: {text}\n")
        else:
            self.err.write(f"watchdog: {main['runner']}.sh send answered {code}; the findings "
                           f"are sent again next round\n")
        return False


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
            dog = Watchdog(state, args.repo, poll=args.poll, silence=args.silence)
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

    run = sub.add_parser("run", help="watch the open night until it closes or a wake lands")
    run.add_argument("--repo", required=True)
    run.add_argument("--poll", type=positive_int, default=DEFAULT_POLL)
    run.add_argument("--silence", type=positive_int, default=DEFAULT_SILENCE)
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
