#!/usr/bin/env python3
"""The relay: events on the board in, wake-ups for the session waiting on them out.

    relay.py run --repo O/R (--tickets N[,N...] | --spec N) [--once] [--interval S] [--grace S]
    relay.py register --repo O/R --runner R --session S
    relay.py ack --repo O/R --runner R --session S --through SEQ
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

**Who is woken.** The session waiting on the event, which `WAKES` names by role:

    worker   reviewer.reported, verifier.passed, verifier.failed: the session that started
             that reviewer or verifier. Its runner and session are the `runner` and
             `session` fields of the ticket's latest `worker.started` before the event.
    main     ticket.passed, ticket.returned, ticket.refused, child.opened of kind fault
             (the pipeline itself broken) or decision, worker.lost, and the relay's own
             relay.recovered: the main agent, as `register` names it.

A worker needs no registration: the ticket says who it is. Each row is written with its
recipient's runner and session, and only that recipient — the pair, never the session
id alone — consumes it.

**Reading the board.** Every `--interval` seconds (default 30) the relay reads the
comments of each watched ticket updated since the newest one it saw there, less two
minutes of overlap, and records every (comment, event) pair it has translated, so the
overlap never queues one twice. With `--spec N` the watched tickets are N's sub-issues,
read again every cycle. On start it reads every watched ticket in full, not since
anything: a relay that was down does not get to assume it missed nothing. A ticket whose
read fails is reported on stderr, keeps its old mark and is read again next cycle, and a
cycle with a failed read is never recorded as a good poll
(docs/adr/0008-silence-is-never-a-pass.md).

**A row's life.** Queued: `seq` (monotonic across all recipients, never reused, even after
the queue empties), `ticket`, `event`, `to` (worker or main), the recipient's `runner` and
`session`, `at`. Delivered: the relay ran `runners/<runner>.sh send <session> "#<ticket>
<event>"` — the text carries the ticket number and the event name and nothing else; what
happened is read on the board. What `send` answered decides what happens to the row:

    0                 delivered; the row stays until it is acked
    3                 the recipient is in a turn and did not take it; the row stays
    2                 the runner has no such session: a late delivery to a retired
                      session; the row is dropped
    4, anything else  unknown; the row stays

A row whose runner and session are no longer the current ones for its role — the main
agent registered another session, or a later `worker.started` put another worker on the
ticket — is dropped without a send, for the same reason as a 2. Every drop is reported on
stderr. A recipient's rows reach it in sequence order: after one of them stays, that
recipient gets nothing more this pass, and the other recipients are not held up by it.
Delivery never removes a row: only `ack --runner R --session S --through <seq>` does, and it
removes that recipient's rows up to that sequence number whatever their content, and nobody
else's. So a row
sent twice — every unacked row is sent once more each time the relay starts — is still
handled once.

**An unattended stretch** is time with no good poll: the relay was down, or its reads kept
failing. Time spent in delivery passes is not part of it: a slow send delays the next poll,
and the relay was attending all the while. When the time since the last good poll, less
the time spent delivering, exceeds `--grace` seconds (default three intervals), the next
good poll queues one `relay.recovered` row to the main agent for the whole stretch, ahead of the events it recovered: one announcement per stretch, never one
per missed event. A stretch is named by the time of the last good poll before it — its
generation — and `gap.json` records the latest one announced; a stretch already announced
is never announced again, whatever became of its row. Consuming rows goes by sequence
number and announcing a stretch goes by generation; neither touches the other.

Files in the state directory:

    queue.jsonl     the rows, one JSON object per line, in sequence order
    queue.seq       the last sequence number issued
    queue.lock      taken for every read and write of the files below it
    seen.json       per ticket: (comment, event) pairs translated, newest updated_at, and
                    every worker.started as [comment id, runner, session]
    recipient.json  the main agent's registered runner and session
    beat.json       the last good poll, seconds spent delivering since it, the pass under way,
                    the last failed poll and why, the run's interval and grace
    gap.json        the latest unattended stretch announced
    relay.lock      held for as long as a `run` runs: one relay per repository

Exit codes:

    run       0 --once read every watched ticket; 3 --once could not read at least one;
              1 refused (no main agent registered, another relay running, a state file
              unreadable)
    register  0 registered; 1 refused (no such adapter, the runner says the session stopped)
    ack       0 acked; 1 refused (a sequence number that was never issued)
    queue     0 rows printed and a relay polled within its grace; 3 rows printed, but no
              relay is running or its last good poll is older than its grace
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

MAIN = "main"
WORKER = "worker"

# Which events wake whom. `to` is the role of the session woken; `when`, where present,
# lists the payload values the event must carry for it to wake anyone.
WAKES: dict[str, dict] = {
    "reviewer.reported": {"to": WORKER},
    "verifier.passed": {"to": WORKER},
    "verifier.failed": {"to": WORKER},
    "ticket.passed": {"to": MAIN},
    "ticket.returned": {"to": MAIN},
    "ticket.refused": {"to": MAIN},
    "child.opened": {"to": MAIN, "when": {"kind": ("fault", "decision")}},
    "worker.lost": {"to": MAIN},
}

# The event that says which session is a ticket's worker.
WORKER_STARTED = "worker.started"

# The one row the relay writes about itself rather than about a ticket.
RECOVERED = "relay.recovered"


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


def wake_text(row: dict) -> str:
    """What is sent: the ticket number and the event name, nothing the board already says."""
    if row.get("event") == RECOVERED:
        return f"{RECOVERED} since {row.get('since')}"
    return f"#{row.get('ticket')} {row.get('event')}"


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
                             env=quiet_env(), timeout=120)
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

    def sub_issues(self, number: int) -> list[int]:
        rows = self.gh(["api", "--paginate", "--slurp",
                        f"repos/{self.repo}/issues/{number}/sub_issues?per_page=100"])
        return [int(r["number"]) for r in rows if isinstance(r, dict) and r.get("number")]


# ----------------------------------------------------------------- delivering

def adapter_path(runner: str) -> Path:
    return RUNNERS / f"{runner}.sh"


def send_via_adapter(runner: str, session: str, text: str) -> int:
    """`runners/<runner>.sh send <session> <text>`; its exit code. A send that could not be
    run, or did not answer in time, is 4: nobody knows whether it arrived."""
    adapter = adapter_path(runner)
    if not adapter.is_file():
        sys.stderr.write(f"relay: no runner adapter at {adapter}; nothing was sent\n")
        return 4
    try:
        run = subprocess.run(["bash", str(adapter), "send", session, text],
                             capture_output=True, text=True, env=quiet_env(),
                             timeout=SEND_TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"relay: {runner}.sh send did not answer within {SEND_TIMEOUT}s\n")
        return 4
    except OSError as exc:
        sys.stderr.write(f"relay: {runner}.sh send could not be run: {exc}\n")
        return 4
    for line in (run.stderr or "").splitlines():
        if line.strip():
            sys.stderr.write(f"relay: {runner}.sh: {line}\n")
    return run.returncode


# ----------------------------------------------------------------- the relay

def _slot(per_ticket: dict, ticket: int) -> dict:
    slot = per_ticket.setdefault(str(ticket), {})
    slot.setdefault("keys", [])
    slot.setdefault("mark", None)
    slot.setdefault("workers", [])
    return slot


class Relay:
    """The queue, the recipients and the marks for one repository's state directory."""

    def __init__(self, state: Path, board: Board | None = None,
                 send: Callable[[str, str, str], int] = send_via_adapter,
                 clock: Callable[[], datetime] = now_utc,
                 out=None, err=None):
        self.state = Path(state)
        self.board = board
        self.send = send
        self.clock = clock
        self.out = out or sys.stdout
        self.err = err or sys.stderr
        # Tickets read in full since this process started: the rest are read since their mark.
        self.reconciled: set[int] = set()

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

    # ------------------------------------------------------------- recipients

    def recipient(self) -> dict | None:
        """The main agent's registration, or None."""
        data = self._read_state("recipient.json", None)
        if isinstance(data, dict) and data.get("runner") and data.get("session"):
            return data
        return None

    def _no_main(self) -> Refusal:
        return Refusal(f"no main agent is registered in {self.path('recipient.json')}, so its "
                       f"wake-ups have nobody to go to. Run `relay.py register --repo "
                       f"<owner/name> --runner <runner> --session <session>` for the main "
                       f"agent's session.")

    def register(self, runner: str, session: str) -> dict:
        record = {"runner": runner, "session": session, "at": iso(self.clock())}
        with self.queue_lock():
            statedir.write_atomic(self.path("recipient.json"), json.dumps(record, sort_keys=True) + "\n")
        return record

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

    # ------------------------------------------------------------- polling

    def poll(self, watched: Callable[[], list[int]], interval: int, grace: int) -> bool:
        """Read the watched tickets and queue what they carry. True when every read was made."""
        if self.recipient() is None:
            raise self._no_main()
        started = self.clock()
        failures: list[str] = []
        try:
            tickets = list(dict.fromkeys(watched()))
        except PollError as exc:
            failures.append(f"the watched tickets: {exc}")
            tickets = []
        with self.queue_lock():
            marks = {k: v.get("mark") for k, v in self._read_state("seen.json", {}).get("tickets", {}).items()}

        found: list[dict] = []
        workers: list[tuple[int, int, str, str]] = []
        unreadable: list[tuple[int, object, str]] = []
        read: dict[int, str | None] = {}
        for number in tickets:
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
                ticket = event.get("ticket") if isinstance(event.get("ticket"), int) else number
                if event["event"] == WORKER_STARTED:
                    runner, session = event.get("runner"), event.get("session")
                    if isinstance(runner, str) and runner and isinstance(session, str) and session:
                        workers.append((ticket, cid, runner, session))
                    else:
                        unreadable.append((number, cid, "its worker.started names no runner and session"))
                    continue
                role = woken_by(event)
                if role is None:
                    continue
                found.append({"key": f"{cid}:{event['event']}", "cid": cid, "home": number,
                              "ticket": ticket, "event": event["event"], "to": role})
            read[number] = newest or None

        now = self.clock()
        added: list[dict] = []
        unaddressed: list[dict] = []
        reported: list[tuple[int, object, str]] = []
        with self.queue_lock():
            # Read here, under the lock `register` writes under: a registration that changed
            # while the board was being read addresses these rows, not the one before it.
            main = self.recipient()
            if main is None:
                raise self._no_main()
            seen = self._read_state("seen.json", {})
            per_ticket = seen.setdefault("tickets", {})
            for ticket, cid, runner, session in workers:
                slot = _slot(per_ticket, ticket)
                if all(entry[0] != cid for entry in slot["workers"]):
                    slot["workers"].append([cid, runner, session])
                    slot["workers"].sort()
            rows = self._rows()
            queued = {r.get("key") for r in rows}
            already = {k for entry in per_ticket.values() for k in entry.get("keys", [])}

            beat = self._read_state("beat.json", {})
            gap = self._read_state("gap.json", {})
            last_good = beat.get("at")
            new_gap = None
            if not failures and last_good and self._unattended(beat, now) > grace:
                key = f"gap:{last_good}"
                if gap.get("since") != last_good and key not in queued:
                    added.append({"key": key, "home": None, "ticket": None, "event": RECOVERED,
                                  "to": MAIN, "runner": main["runner"], "session": main["session"],
                                  "since": last_good})
                    new_gap = {"generation": int(gap.get("generation") or 0) + 1,
                               "since": last_good, "until": iso(now)}
            # Comment ids rise across the whole repository, so this is the order the events landed in.
            for item in sorted(found, key=lambda f: f["cid"]):
                if item["key"] in already or item["key"] in queued:
                    continue
                if item["to"] == MAIN:
                    address = (main["runner"], main["session"])
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
            # A comment the relay could not translate, or a worker wake-up with no worker on
            # its ticket, is reported the first time it is seen and not again.
            problems = [(n, cid, why) for n, cid, why in unreadable] + [
                (item["home"], item["cid"], f"it wakes #{item['ticket']}'s worker, and no "
                 f"worker.started on #{item['ticket']} comes before it, so there is no session "
                 f"to wake") for item in unaddressed]
            for number, cid, why in problems:
                slot = _slot(per_ticket, number)
                key = f"{cid}:reported"
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

    # ------------------------------------------------------------- delivering

    def forget_deliveries(self) -> None:
        """Mark every row undelivered, so each unacked row is sent once more."""
        with self.queue_lock():
            rows = self._rows()
            if any(r.get("delivered") for r in rows):
                for row in rows:
                    row["delivered"] = None
                self._write_rows(rows)

    def _settle(self, seq: int, delivered: str | None = None, drop: bool = False) -> bool:
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

    def _deliver(self, pending: list[dict]) -> None:
        main = self.recipient()
        with self.queue_lock():
            per_ticket = self._read_state("seen.json", {}).get("tickets", {})
        held: set[tuple[str, str]] = set()
        for row in pending:
            address = (row.get("runner"), row.get("session"))
            if row.get("to") == WORKER:
                current = self._worker_before(per_ticket, row.get("ticket"), None)
                whose = f"#{row.get('ticket')}'s worker"
            else:
                current = (main["runner"], main["session"]) if main else None
                whose = "the registered main agent"
            if current is None:
                self.err.write(f"relay: kept row {row['seq']} ({wake_text(row)}): there is no "
                               f"{whose} to compare it with; run `relay.py register`\n")
                continue
            if address != current:
                self._drop(row, f"it is addressed to {address[0]} session {address[1]}, and "
                                f"{whose} is now {current[0]} session {current[1]}: a late message "
                                f"for a retired session")
                continue
            if address in held:
                continue
            code = self.send(address[0], address[1], wake_text(row))
            if code == 0:
                if self._settle(row["seq"], delivered=iso(self.clock())):
                    self.out.write(f"delivered {row['seq']} {wake_text(row)} to {address[1]}\n")
            elif code == 2:
                self._drop(row, f"{address[0]} has no session {address[1]}: a late message for a "
                                f"retired session")
            elif code == 3:
                held.add(address)
                self.out.write(f"kept {row['seq']} {wake_text(row)}: {address[1]} is in a turn\n")
            else:
                held.add(address)
                self.err.write(f"relay: kept row {row['seq']} ({wake_text(row)}): {address[0]}.sh "
                               f"send answered {code}, which says neither delivered nor refused; it "
                               f"is sent again next cycle\n")
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
    board = Board(args.repo)
    relay = Relay(state, board)
    interval = args.interval
    grace = args.grace if args.grace is not None else 3 * interval
    if relay.recipient() is None:
        raise Refusal(f"no main agent is registered in {state / 'recipient.json'}, so its "
                      f"wake-ups have nobody to go to. Run `relay.py register --repo {args.repo} "
                      f"--runner <runner> --session <session>` for the main agent's session, then "
                      f"start the relay again.")
    if args.spec:
        def watched() -> list[int]:
            return board.sub_issues(args.spec)
    else:
        tickets = args.tickets

        def watched() -> list[int]:
            return tickets

    def stop(signum, frame):
        raise SystemExit(0)

    try:
        with statedir.locked(state / "relay.lock", wait=0, purpose=f"relay for {args.repo}"):
            signal.signal(signal.SIGTERM, stop)
            signal.signal(signal.SIGINT, stop)
            relay.forget_deliveries()
            while True:
                good = relay.poll(watched, interval, grace)
                relay.deliver()
                if args.once:
                    return 0 if good else 3
                time.sleep(interval)
    except LockHeld as exc:
        if exc.path != state / "relay.lock":
            raise
        raise Refusal(f"another relay is running for {args.repo}: {exc}. One repository has one "
                      f"relay. Leave that one running, or end that pid and start this again.") from None


def cmd_register(args) -> int:
    state = state_for(args.repo)
    adapter = adapter_path(args.runner)
    if not adapter.is_file():
        known = ", ".join(sorted(p.stem for p in RUNNERS.glob("*.sh"))) or "none"
        raise Refusal(f"there is no runner adapter {adapter}; the adapters here are: {known}. "
                      f"Register with one of those runners.")
    try:
        run = subprocess.run(["bash", str(adapter), "liveness", args.session], capture_output=True,
                             text=True, env=quiet_env(), timeout=60)
        answer = (run.stdout or "").strip() if run.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        answer = "unknown"
    if answer == "stopped":
        raise Refusal(f"{args.runner} says session {args.session} is stopped, so every wake-up sent "
                      f"to it would be dropped. Register the main agent's live session id.")
    record = Relay(state).register(args.runner, args.session)
    if answer != "alive":
        sys.stderr.write(f"relay: registered, but {args.runner} could not say whether session "
                         f"{args.session} is alive (it answered {answer!r}); the first delivery will tell\n")
    print(json.dumps(record, sort_keys=True))
    return 0


def cmd_ack(args) -> int:
    removed, left = Relay(state_for(args.repo)).ack((args.runner, args.session), args.through)
    print(f"acked {args.runner} {args.session} through {args.through}: removed {removed}, "
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

    run = sub.add_parser("run", help="poll the board and deliver wake-ups")
    run.add_argument("--repo", required=True)
    which = run.add_mutually_exclusive_group(required=True)
    which.add_argument("--tickets", type=ticket_list)
    which.add_argument("--spec", type=positive_int)
    run.add_argument("--once", action="store_true")
    run.add_argument("--interval", type=positive_int, default=DEFAULT_INTERVAL)
    run.add_argument("--grace", type=non_negative_int)
    run.set_defaults(fn=cmd_run)

    reg = sub.add_parser("register", help="name the main agent's runner and session")
    reg.add_argument("--repo", required=True)
    reg.add_argument("--runner", required=True)
    reg.add_argument("--session", required=True)
    reg.set_defaults(fn=cmd_register)

    ack = sub.add_parser("ack", help="remove one recipient's rows up to a sequence number")
    ack.add_argument("--repo", required=True)
    ack.add_argument("--runner", required=True)
    ack.add_argument("--session", required=True)
    ack.add_argument("--through", required=True, type=positive_int)
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
