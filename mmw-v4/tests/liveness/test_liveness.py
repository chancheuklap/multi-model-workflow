from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "dispatch" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dog = load("mmw_watchdog_under_test", "watchdog.py")
guard = load("mmw_turn_guard_under_test", "turn-guard.py")
import statedir  # noqa: E402

events = dog.events
T0 = datetime(2026, 9, 10, 1, 0, 0, tzinfo=timezone.utc)
MAIN = {"runner": "orca", "session": "term_main"}


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


# The machine every fixture session was started on, and the one the watchdog under test
# says it runs on.
HERE_MACHINE = "mac-1"

REQUIRED = {
    "worker.started": {"machine": HERE_MACHINE, "host": "claude", "model": "m", "effort": "high",
                       "grade": "junior-worker", "worktree": "/repo/.worktrees/issue-61",
                       "branch": "issue-61", "base": "0" * 40},
    "reviewer.started": {"machine": HERE_MACHINE},
    "worker.lost": {},
    "worker.replaced": {},
    "ticket.released": {"reason": "landed"},
}


def comment(cid: int, event: str, ticket: int, at: datetime, **payload) -> dict:
    body = events.build(event, ticket=ticket, line="a line for people", at=stamp(at),
                        **{**REQUIRED.get(event, {}), **payload})
    return {"id": cid, "body": body, "created_at": stamp(at), "updated_at": stamp(at)}


class Clock:
    def __init__(self, moment: datetime = T0):
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


class FakeBoard:
    """Comments by ticket, and each spec's sub-issues as numbers (open) or (number, state)."""

    def __init__(self, tickets: dict[int, list[dict]], spec_children=None):
        self.tickets = tickets
        self.spec_children = spec_children or {}
        self.read: list[int] = []

    def comments(self, ticket, since):
        self.read.append(ticket)
        return list(self.tickets.get(ticket, []))

    def children(self, number):
        return [c if isinstance(c, tuple) else (c, "open") for c in self.spec_children.get(number, [])]


class Recorder:
    """A runner verb or a post: records its calls and answers from `answers` (or `default`)."""

    def __init__(self, answers=None, default=None):
        self.answers = answers or {}
        self.default = default
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        key = args[:2] if len(args) >= 2 else args
        return self.answers.get(key, self.default)


class StateCase(unittest.TestCase):
    """A temporary MMW_HOME with one repository's state directory."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        old = os.environ.get("MMW_HOME")
        os.environ["MMW_HOME"] = self.tmp.name
        self.addCleanup(lambda: os.environ.pop("MMW_HOME") if old is None
                        else os.environ.__setitem__("MMW_HOME", old))
        self.state = statedir.state_dir("o/r")

    def write(self, name: str, value) -> None:
        (self.state / name).write_text(json.dumps(value) + "\n", encoding="utf-8")

    def open_watches(self, *entries: dict) -> None:
        """watches.json holding each entry: a watch (`spec` or `tickets`) with its orchestrator."""
        self.write("watches.json", {
            (f"spec:{e['spec']}" if e.get("spec") else
             "tickets:" + ",".join(str(n) for n in e["tickets"])): e for e in entries})


# ----------------------------------------------------------------- tolerance and health

class Tolerance(unittest.TestCase):
    def test_short_polls_keep_the_floor(self):
        self.assertEqual(dog.tolerance(60), 300)
        self.assertEqual(dog.tolerance(120), 300)

    def test_it_grows_with_the_poll_once_the_poll_passes_the_floor(self):
        # A fixed 300 would read a healthy watchdog polling every 300s as dead mid-wait.
        self.assertEqual(dog.tolerance(300), 480)
        self.assertEqual(dog.tolerance(1000), 1180)

    def test_the_margin_outlasts_one_adapter_call_plus_one_gh_read(self):
        # A slow but alive watchdog, waiting on one of each, is never read as hung.
        self.assertGreaterEqual(dog.MARGIN, dog.ADAPTER_TIMEOUT + dog.relay_mod.GH_TIMEOUT)

    def test_an_unreadable_poll_takes_the_default(self):
        self.assertEqual(dog.tolerance(None), 300)
        self.assertEqual(dog.tolerance("x"), 300)


class Health(unittest.TestCase):
    HOLDER = {"pid": 4242, "identity": "Thu Sep 10 01:00:00 2026"}

    def beat(self, age: int, poll: int = 60, **over) -> dict:
        return {"pid": 4242, "identity": "Thu Sep 10 01:00:00 2026",
                "at": stamp(T0 - timedelta(seconds=age)),
                "poll": poll, **over}

    def test_no_live_holder_is_not_healthy_whatever_the_heartbeat_says(self):
        self.assertFalse(dog.health(None, self.beat(1), T0)[0])

    def test_a_live_holder_with_no_heartbeat_is_not_healthy(self):
        self.assertFalse(dog.health(self.HOLDER, None, T0)[0])
        self.assertFalse(dog.health(self.HOLDER, {}, T0)[0])

    def test_a_heartbeat_another_process_wrote_proves_nothing(self):
        ok, why = dog.health(self.HOLDER, self.beat(1, pid=999), T0)
        self.assertFalse(ok)
        self.assertIn("999", why)
        ok, _ = dog.health(self.HOLDER, self.beat(1, identity="another start"), T0)
        self.assertFalse(ok)

    def test_fresh_within_the_tolerance_and_stale_past_it(self):
        self.assertTrue(dog.health(self.HOLDER, self.beat(300), T0)[0])
        ok, why = dog.health(self.HOLDER, self.beat(301), T0)
        self.assertFalse(ok)
        self.assertIn("301s", why)
        self.assertIn("300s", why)

    def test_a_long_poll_is_not_read_as_stale_mid_wait(self):
        # poll 400: the tolerance is 580, so a heartbeat 400s old is a watchdog asleep.
        self.assertTrue(dog.health(self.HOLDER, self.beat(400, poll=400), T0)[0])
        self.assertFalse(dog.health(self.HOLDER, self.beat(581, poll=400), T0)[0])



class ArmDirectory(StateCase):
    """The watchdog runs in the state directory, as the relay does (2026-10-08)."""

    def test_the_watchdog_runs_in_the_state_directory(self):
        seen = {}

        def popen(argv, **kwargs):
            seen.update(kwargs)
            return mock.Mock(pid=1)

        with mock.patch.object(dog.subprocess, "Popen", popen):
            dog.arm(self.state, "o/r", wait=0.01)
        self.assertEqual(Path(seen["cwd"]), self.state)


class LockIdentity(StateCase):
    """The watchdog's lock read through statedir.holder, against real processes."""

    def heartbeat_by(self, pid: int, identity: str | None) -> None:
        self.write("watchdog.json", {"pid": pid, "identity": identity, "at": stamp(dog.now_utc()),
                                     "poll": 60})

    def test_own_pid_and_identity_with_its_own_heartbeat_is_healthy(self):
        me = statedir.process_identity(os.getpid())
        self.write("watchdog.lock", {"pid": os.getpid(), "identity": me})
        self.heartbeat_by(os.getpid(), me)
        ok, why, _ = dog.read_health(self.state)
        self.assertTrue(ok, why)

    def test_a_dead_pid_names_nobody(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        identity = statedir.process_identity(child.pid)
        child.wait()
        self.write("watchdog.lock", {"pid": child.pid, "identity": identity or "x"})
        self.heartbeat_by(child.pid, identity or "x")
        self.assertIsNone(statedir.holder(self.state / "watchdog.lock"))
        self.assertFalse(dog.read_health(self.state)[0])

    def test_a_recycled_pid_is_not_the_watchdog(self):
        # A live pid whose process started at another time than the one recorded: the pid
        # was handed to another process, and a pid-only check would call it the watchdog.
        self.write("watchdog.lock", {"pid": os.getpid(), "identity": "Mon Jan  1 00:00:00 2001"})
        self.heartbeat_by(os.getpid(), "Mon Jan  1 00:00:00 2001")
        self.assertIsNone(statedir.holder(self.state / "watchdog.lock"))
        self.assertFalse(dog.read_health(self.state)[0])


class TurnGuardOnlyArms(StateCase):
    def test_an_arm_error_in_one_repository_does_not_skip_the_next(self):
        broken = statedir.state_dir("a/broken")
        (broken / "watches.json").write_text(json.dumps({"spec:7": {"spec": 7, **MAIN}}))
        (broken / "watchdog.log").mkdir()
        self.open_watches({"tickets": [61], **MAIN})
        starter = Path(self.tmp.name) / "nodog.py"
        starter.write_text("from pathlib import Path\nPath('armed').touch()\nraise SystemExit(1)\n")
        run = subprocess.run([sys.executable, guard.__file__, "stop", "codex"],
                             input="{}", capture_output=True, text=True,
                             env={**os.environ, "MMW_WATCHDOG_PY": str(starter)})
        self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertIn("IsADirectoryError", (broken / "guard.log").read_text())
        self.assertTrue((self.state / "armed").exists())
        self.assertIn("unhealthy", (self.state / "guard.log").read_text())

    def test_held_tickets_and_an_unhealthy_watchdog_never_hold_a_turn(self):
        self.open_watches({"tickets": [61], **MAIN})
        other = statedir.state_dir("o/other")
        (other / "watches.json").write_text(json.dumps({"spec:7": {"spec": 7, **MAIN}}))
        self.write("watchdog.json", {"held": [61]})
        starter = Path(self.tmp.name) / "nodog.py"
        starter.write_text("from pathlib import Path\nPath('armed').touch()\nraise SystemExit(1)\n")
        runners = Path(self.tmp.name) / "runners"
        runners.mkdir()
        (runners / "orca.sh").write_text('echo term_main\n')
        env = {**os.environ, "MMW_WATCHDOG_PY": str(starter), "MMW_RUNNERS_DIR": str(runners)}
        for host in guard.HOSTS:
            for who in ("term_main", "worker"):
                (runners / "orca.sh").write_text(f'echo {who}\n')
                with self.subTest(host=host, who=who):
                    for state in (self.state, other):
                        (state / "armed").unlink(missing_ok=True)
                    run = subprocess.run([sys.executable, guard.__file__, "stop", host],
                                         input="{}", capture_output=True, text=True, env=env)
                    self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
                    for state in (self.state, other):
                        self.assertTrue((state / "armed").exists(), state)
                        self.assertIn(f"{host} allow", (state / "guard.log").read_text())


class TurnGuardLetsBriefsStop(StateCase):
    def test_an_unreported_brief_can_end_its_turn(self):
        batch = dog.briefs.create(self.state, "researcher", 1, "fake", "parent")
        dog.briefs.mark_started(self.state, batch, 1, {"runner": "fake", "session": "child"})
        self.write("watches.json", {f"briefs:{batch}": {"briefs": batch, "runner": "fake",
                                                     "session": "parent"}})
        runners = Path(self.tmp.name) / "runners"
        runners.mkdir()
        (runners / "fake.sh").write_text('echo child\n')
        starter = Path(self.tmp.name) / "nodog.py"
        starter.write_text("raise SystemExit(1)\n")
        env = {**os.environ, "MMW_WATCHDOG_PY": str(starter), "MMW_RUNNERS_DIR": str(runners)}
        for host in guard.HOSTS:
            run = subprocess.run([sys.executable, guard.__file__, "stop", host],
                                 input="{}", capture_output=True, text=True, env=env)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))
        self.assertEqual(dog.briefs.briefs_of(self.state, batch)[0]["state"], "open")


# ----------------------------------------------------------------- the night

class NightOpen(StateCase):
    def test_an_open_watch_is_an_open_night_whether_or_not_a_relay_runs(self):
        # A relay that died leaves its watches: an open night with no relay.
        self.open_watches({"spec": 7, **MAIN})
        self.assertTrue(dog.night_open(self.state))

    def test_no_watch_open_is_no_night(self):
        self.write("beat.json", {"at": stamp(T0)})
        self.assertFalse(dog.night_open(self.state))
        self.write("watches.json", {})
        self.assertFalse(dog.night_open(self.state))
        self.assertFalse(dog.night_open(statedir.state_dir("o/never")))

    def test_unreadable_watches_are_not_a_closed_night(self):
        (self.state / "watches.json").write_text("{not json", encoding="utf-8")
        self.assertTrue(dog.night_open(self.state))


# ----------------------------------------------------------------- the third layer

class Judge(unittest.TestCase):
    def fold(self, *comments):
        return events.fold(list(comments), issue=61)

    def test_a_ticket_nobody_holds_is_free(self):
        f = self.fold(comment(1, "worker.started", 61, T0, runner="orca", session="t1"),
                      comment(2, "ticket.landed", 61, T0))
        self.assertEqual(dog.judge(f)["state"], "free")

    def test_a_recent_event_still_needs_the_session_table(self):
        f = self.fold(comment(1, "worker.started", 61, T0, runner="orca", session="t1"))
        self.assertEqual(dog.judge(f)["state"], "held")

    def test_only_the_live_workers_pair_is_named(self):
        f = self.fold(comment(1, "worker.started", 61, T0, runner="herdr", session="h1"),
                      comment(2, "worker.replaced", 61, T0, runner="herdr", session="h1"),
                      comment(3, "worker.started", 61, T0, runner="orca", session="t2"))
        self.assertEqual([(r["kind"], r["runner"], r["session"], r["machine"])
                          for r in dog.judge(f)["sessions"]],
                         [("worker", "orca", "t2", HERE_MACHINE)])

    def test_an_unreadable_event_is_its_own_answer(self):
        f = events.fold(["prose", "x\n\n<!-- mmw {not json} -->"], issue=61)
        self.assertEqual(dog.judge(f)["state"], "unreadable")


class Rounds(StateCase):
    """Watchdog.round over a fake board, fake runner verbs and a fake post."""

    SILENT = T0 - timedelta(minutes=30)

    def setUp(self):
        super().setUp()
        self.open_watches({"spec": 7, **MAIN})
        # An open night whose relay is healthy: this process holds the relay's lock with its
        # own identity, and the relay polled a moment ago.
        self.relay_lock = statedir.locked(self.state / "relay.lock", wait=0, purpose="test relay")
        self.relay_lock.__enter__()
        self.addCleanup(self.relay_lock.__exit__, None, None, None)
        self.write("relay.json", {"pid": os.getpid(), "identity": statedir.own_identity(),
                                  "started": stamp(T0 - timedelta(hours=1))})
        self.write("beat.json", {"at": stamp(T0), "delivering": 0, "grace": 90, "interval": 30})
        self.board = FakeBoard({}, {7: [61]})
        self.ask = Recorder(default="alive")
        self.send = Recorder(default=0)
        self.post = Recorder(default=(True, ""))
        self.clock = Clock()
        self.runners = Path(self.tmp.name) / "runners"
        self.runners.mkdir()
        for runner in ("orca", "herdr"):
            (self.runners / f"{runner}.sh").write_text(
                'if [ "$1" = state ]; then cat "$(dirname "$0")/$2.state"; else exit 3; fi\n')
        for session in ("h1", "rv", "rv2", "h70"):
            (self.runners / f"{session}.state").write_text("idle\n")
        runner_env = mock.patch.dict(os.environ, {"MMW_RUNNERS_DIR": str(self.runners)})
        runner_env.start()
        self.addCleanup(runner_env.stop)

    def watchdog(self) -> "dog.Watchdog":
        return dog.Watchdog(self.state, "o/r", board=self.board, ask=self.ask, send=self.send,
                            post=self.post, clock=self.clock, pid=os.getpid(),
                            identity=statedir.own_identity(), machine=HERE_MACHINE,
                            err=io.StringIO())

    def silent_worker(self, runner="herdr", session="h1"):
        self.board.tickets[61] = [comment(1, "worker.started", 61, self.SILENT, runner=runner,
                                          session=session)]

    def repository(self, commit_at):
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        (repo / "work.txt").write_text("work\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "work"], check=True,
                       env={**os.environ, "GIT_AUTHOR_DATE": stamp(commit_at),
                            "GIT_COMMITTER_DATE": stamp(commit_at)})
        os.utime(repo / "work.txt", (commit_at.timestamp(), commit_at.timestamp()))
        return repo

    def test_table_a_busy_worker_with_a_new_commit_is_not_reported(self):
        repo = self.repository(T0 - timedelta(seconds=1))
        old = (T0 - timedelta(hours=3)).timestamp()
        os.utime(repo / "work.txt", (old, old))
        self.board.tickets[61] = [comment(1, "worker.started", 61,
                                          T0 - timedelta(hours=3), runner="herdr",
                                          session="h1", worktree=str(repo))]
        self.watchdog().round()
        self.assertEqual((self.send.calls, self.post.calls), ([], []))
        self.clock.moment += timedelta(seconds=3600)
        self.write("beat.json", {"at": stamp(self.clock()), "grace": 90})
        self.send.default = 3
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.clock.moment += timedelta(seconds=1)
        os.utime(repo / "work.txt", (self.clock().timestamp(), self.clock().timestamp()))
        self.send.default = 4
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1, "new file activity cancels the unsent idle alert")

    def test_table_a_reviewer_on_a_dialog_is_reported_with_its_line(self):
        self.children()
        self.board.tickets[61][-1] = comment(2, "reviewer.started", 61, T0,
                                             runner="orca", session="rv")
        (self.runners / "rv.state").write_text("dialog\tTrust this folder?\n")
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertEqual(self.send.calls[0][:2], ("orca", "term_main"))
        self.assertIn("reviewer", self.send.calls[0][2])
        self.assertIn("rv", self.send.calls[0][2])
        self.assertIn("Trust this folder?", self.send.calls[0][2])
        self.assertNotIn("\n", self.send.calls[0][2])
        self.assertEqual(self.post.calls, [])

    def test_table_an_idle_session_is_reported_once(self):
        self.idle_worker()
        self.send.default = 4
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.board.tickets[61].append(comment(2, "worker.decided", 61, T0))
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertEqual(self.send.calls[0][:2], ("orca", "term_main"))
        self.assertIn("h1", self.send.calls[0][2])
        self.send.calls.clear()
        (self.state / "watchdog.json").unlink()
        self.idle_worker(comment(2, "reviewer.started", 61, self.IDLE,
                                 runner="orca", session="rv"))
        (self.runners / "rv.state").write_text("working\n")
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])
        self.idle_worker()
        self.write("watchdog.json", {})
        with mock.patch.object(dog.briefs, "now_iso", return_value=stamp(self.IDLE)):
            batch = dog.briefs.create(self.state, "researcher", 1, "herdr", "h1",
                                      worktree=Path(self.tmp.name) / "missing-repo")
            dog.briefs.mark_started(self.state, batch, 1, {"runner": "orca", "session": "rv"})
        self.write("watches.json", {
            "spec:7": {"spec": 7, **MAIN},
            f"briefs:{batch}": {"briefs": batch, "runner": "herdr", "session": "h1"}})
        self.watchdog().round()
        self.assertEqual(self.send.calls, [], "a worker waiting on a brief is not idle")

    def test_table_an_unknown_state_is_reported_never_lost(self):
        self.silent_worker()
        for answer in ("unknown", "nonsense", "working\nidle", "dialog\t"):
            with self.subTest(answer=answer):
                self.send.calls.clear()
                (self.state / "watchdog.json").unlink(missing_ok=True)
                (self.runners / "h1.state").write_text(answer + "\n")
                self.watchdog().round()
                self.assertEqual(len(self.send.calls), 1)
                self.assertIn("unknown", self.send.calls[0][2])
                self.assertIn("h1", self.send.calls[0][2])
                self.assertEqual(self.post.calls, [])

    def test_table_a_stuck_turn_is_reported_once(self):
        self.board.tickets[61] = [comment(1, "worker.started", 61,
                                          T0 - timedelta(seconds=7200), runner="herdr",
                                          session="h1")]
        (self.runners / "h1.state").write_text("working\n")
        self.send.default = 4
        self.clock.moment = T0 - timedelta(seconds=1)
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])
        self.clock.moment = T0
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertIn("h1", self.send.calls[0][2])
        self.assertIn("stuck", self.send.calls[0][2])
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)

    def test_table_a_resumed_turn_starts_its_stuck_clock_anew(self):
        started = T0 - timedelta(hours=3)
        repo = self.repository(started)
        self.board.tickets[61] = [
            comment(1, "worker.started", 61, started, runner="herdr", session="h1", worktree=str(repo)),
            comment(2, "worker.resumed", 61, T0, runner="herdr", session="h1")]
        (self.runners / "h1.state").write_text("working\n")
        self.send.default = 4
        for elapsed in (0, 7199):
            self.clock.moment = T0 + timedelta(seconds=elapsed)
            self.write("beat.json", {"at": stamp(self.clock()), "grace": 90})
            self.watchdog().round()
            self.assertEqual(self.send.calls, [], "the resumed turn has not reached --stuck")
        self.clock.moment = T0 + timedelta(seconds=7200)
        self.write("beat.json", {"at": stamp(self.clock()), "grace": 90})
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertIn("stuck", self.send.calls[0][2])
        self.assertIn(stamp(T0), self.send.calls[0][2])
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.board.tickets[61].append(comment(3, "worker.decided", 61, self.clock()))
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1, "any newest ticket event resets the stuck clock")
        changed = T0 + timedelta(seconds=7201)
        os.utime(repo / "work.txt", (changed.timestamp(), changed.timestamp()))
        for elapsed, expected in ((14400, 1), (14401, 2)):
            self.clock.moment = T0 + timedelta(seconds=elapsed)
            self.write("beat.json", {"at": stamp(self.clock()), "grace": 90})
            self.watchdog().round()
            self.assertEqual(len(self.send.calls), expected, "later worktree activity wins")
        self.assertIn(stamp(changed), self.send.calls[-1][2])

    def test_an_unrouted_child_without_a_delivered_wake_is_not_reported(self):
        self.silent_worker()
        self.board.tickets[61].append(comment(2, "child.opened", 61, T0,
                                             child=1373, kind="contract", title="contract"))
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])

    def test_a_wake_acked_before_its_nudge_age_is_not_reported(self):
        (self.state / "queue.jsonl").write_text(json.dumps({
            "seq": 1, "ticket": 61, "event": "reviewer.reported", "to": "worker",
            "watch": "spec:7", "runner": "herdr", "session": "h1",
            "at": stamp(T0), "delivered": stamp(T0)}) + "\n")
        self.watchdog().round()
        dog.relay_mod.Relay(self.state).ack(("herdr", "h1"), 1)
        self.clock.moment += timedelta(seconds=1800)
        self.write("beat.json", {"at": stamp(self.clock()), "grace": 90})
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])

    def test_table_an_idle_researcher_is_reported(self):
        with mock.patch.object(dog.briefs, "now_iso", return_value=stamp(self.IDLE)):
            batch = dog.briefs.create(self.state, "researcher", 1,
                                      MAIN["runner"], MAIN["session"],
                                      worktree=Path(self.tmp.name) / "missing-repo")
            dog.briefs.mark_started(self.state, batch, 1, {
                "runner": "herdr", "session": "h1", "machine": HERE_MACHINE})
        self.write("watches.json", {f"briefs:{batch}": {"briefs": batch, **MAIN}})
        self.send.default = 4
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertIn(f"brief {batch}/1", self.send.calls[0][2])
        self.assertIn("researcher", self.send.calls[0][2])
        self.assertIn("h1", self.send.calls[0][2])
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertEqual(dog.briefs.briefs_of(self.state, batch)[0]["state"], "open")


    def test_a_worker_waits_for_the_lost_reviewer_wake(self):
        self.idle_worker(comment(2, "reviewer.started", 61, self.IDLE,
                                 runner="orca", session="rv"))
        self.ask.answers[("orca", "rv")] = "stopped"
        self.watchdog().round()
        self.assertEqual([c[1] for c in self.post.calls], ["reviewer"])
        self.assertEqual(self.send.calls, [], "reviewer.lost wakes the worker through the relay")

    def test_future_file_times_do_not_hide_idle_or_stuck_sessions(self):
        started = T0 - timedelta(hours=3)
        repo = self.repository(started)
        future = (T0 + timedelta(days=30)).timestamp()
        os.utime(repo / "work.txt", (future, future))
        self.board.tickets[61] = [comment(1, "worker.started", 61, started,
                                          runner="herdr", session="h1", worktree=str(repo))]
        for state in ("idle", "working"):
            with self.subTest(state=state):
                (self.state / "watchdog.json").unlink(missing_ok=True)
                self.send.calls.clear()
                (self.runners / "h1.state").write_text(state + "\n")
                self.watchdog().round()
                self.assertEqual(len(self.send.calls), 1)
                self.assertIn("h1", self.send.calls[0][2])
                self.assertIn("idle" if state == "idle" else "stuck", self.send.calls[0][2])

    def heartbeat(self) -> dict:
        return json.loads((self.state / "watchdog.json").read_text())

    def test_stopped_posts_worker_lost_for_that_pair_and_nothing_else(self):
        self.silent_worker()
        self.ask.answers[("herdr", "h1")] = "stopped"
        self.assertEqual(self.watchdog().round(), "watching")
        self.assertEqual(len(self.post.calls), 1)
        repo, kind, ticket, spec, runner, session, since = self.post.calls[0]
        self.assertEqual((repo, kind, ticket, spec, runner, session),
                         ("o/r", "worker", 61, 7, "herdr", "h1"))
        self.assertEqual(since, stamp(self.SILENT))
        self.assertEqual(self.send.calls, [], "worker.lost wakes the orchestrator through the relay")
        self.assertEqual(self.heartbeat()["lost"]["61"][0]["session"], "h1")

    def test_unknown_is_recorded_and_reported_never_posted(self):
        self.silent_worker()
        self.ask.answers[("herdr", "h1")] = "unknown"
        self.watchdog().round()
        self.assertEqual(self.post.calls, [])
        beat = self.heartbeat()
        self.assertEqual(beat["unknown"]["61"]["sessions"],
                         [{"kind": "worker", "runner": "herdr", "session": "h1"}])
        self.assertEqual(beat["held"], [61])
        self.assertEqual(len(self.send.calls), 1)
        runner, session, text = self.send.calls[0]
        self.assertEqual((runner, session), ("orca", "term_main"))
        self.assertIn("#61", text)

    def test_alive_does_nothing(self):
        self.silent_worker()
        self.watchdog().round()
        self.assertEqual((self.post.calls, self.send.calls), ([], []))
        self.assertEqual(self.heartbeat()["unknown"], {})

    def test_only_the_runner_its_worker_started_names_is_asked(self):
        # Another runner might answer for a stale binding; it is never consulted.
        self.silent_worker(runner="herdr", session="h1")
        self.watchdog().round()
        self.assertEqual(self.ask.calls, [("herdr", "h1")])

    def children(self, *extra):
        """A live worker, then a reviewer it started, then `extra`."""
        self.board.tickets[61] = [
            comment(1, "worker.started", 61, self.SILENT, runner="herdr", session="h1"),
            comment(2, "reviewer.started", 61, self.SILENT, runner="orca", session="rv"),
            *extra]

    def test_every_live_session_is_asked_through_its_own_runner(self):
        self.children()
        self.watchdog().round()
        self.assertEqual(sorted(self.ask.calls), [("herdr", "h1"), ("orca", "rv")])

    def test_a_stopped_reviewer_with_no_result_is_lost(self):
        self.children()
        self.ask.answers[("orca", "rv")] = "stopped"
        self.watchdog().round()
        posted = sorted((c[1], c[4], c[5]) for c in self.post.calls)
        self.assertEqual(posted, [("reviewer", "orca", "rv")])
        self.assertEqual(self.send.calls, [], "the relay wakes the worker")

    def test_a_reviewer_whose_report_is_in_is_not_asked(self):
        self.children(comment(4, "reviewer.reported", 61, self.SILENT))
        self.ask.default = "stopped"
        self.watchdog().round()
        self.assertEqual(sorted(self.ask.calls), [("herdr", "h1")])
        self.assertNotIn("reviewer", [c[1] for c in self.post.calls])

    def test_a_report_before_this_reviewer_started_does_not_count_for_it(self):
        self.board.tickets[61] = [
            comment(1, "worker.started", 61, self.SILENT, runner="herdr", session="h1"),
            comment(2, "reviewer.started", 61, self.SILENT, runner="orca", session="rv1"),
            comment(3, "reviewer.reported", 61, self.SILENT),
            comment(4, "reviewer.started", 61, self.SILENT, runner="orca", session="rv2")]
        self.watchdog().round()
        self.assertIn(("orca", "rv2"), self.ask.calls)
        self.assertNotIn(("orca", "rv1"), self.ask.calls)

    def test_an_unknown_reviewer_is_recorded_never_lost(self):
        self.children()
        self.ask.answers[("orca", "rv")] = "unknown"
        self.watchdog().round()
        self.assertEqual(self.post.calls, [])
        self.assertEqual(self.heartbeat()["unknown"]["61"]["sessions"],
                         [{"kind": "reviewer", "runner": "orca", "session": "rv"}])
        self.assertIn("rv", self.send.calls[0][2].split())

    def test_a_session_started_on_another_machine_is_unknown_never_asked_or_lost(self):
        self.board.tickets[61] = [comment(1, "worker.started", 61, self.SILENT, runner="orca",
                                          session="t9", machine="mac-2")]
        self.ask.default = "stopped"  # what this machine's Orca would say of a stranger
        self.watchdog().round()
        self.assertEqual((self.ask.calls, self.post.calls), ([], []))
        self.assertEqual(self.heartbeat()["unknown"]["61"]["sessions"],
                         [{"kind": "worker", "runner": "orca", "session": "t9", "machine": "mac-2"}])
        self.assertIn("mac-2", self.send.calls[0][2])
        self.assertIn("mac-1", self.send.calls[0][2])



    def test_a_recent_ticket_is_asked(self):
        self.board.tickets[61] = [comment(1, "worker.started", 61, T0 - timedelta(minutes=2),
                                          runner="herdr", session="h1")]
        self.watchdog().round()
        self.assertEqual(self.ask.calls, [("herdr", "h1")])

    def test_a_held_ticket_with_no_worker_session_is_reported(self):
        self.board.tickets[61] = [comment(1, "ticket.claimed", 61, self.SILENT)]
        self.watchdog().round()
        self.assertEqual(self.ask.calls, [])
        self.assertIn("#61", self.send.calls[0][2])

    def test_a_finding_is_reported_once_across_rounds_and_restarts(self):
        self.silent_worker()
        self.ask.default = "unknown"
        self.send.default = 4  # handed over, not confirmed: the watchdog keeps running
        self.assertEqual(self.watchdog().round(), "watching")
        self.watchdog().round()  # a new watchdog process reads what was reported
        self.assertEqual(len(self.send.calls), 1)
        self.board.tickets[61].append(comment(2, "worker.decided", 61, self.SILENT))
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 2)

    def test_a_send_that_did_not_happen_is_tried_next_round(self):
        self.silent_worker()
        self.ask.default = "unknown"
        self.send.default = 3
        wd = self.watchdog()
        wd.round()
        self.assertEqual(self.heartbeat()["pending"][0]["key"].split(":")[0], "unknown")
        self.send.default = 0
        self.assertEqual(wd.round(), "woke", "a confirmed wake ends this watchdog: the turn it "
                                             "started re-arms it")
        self.assertEqual(len(self.send.calls), 2)
        self.assertEqual(self.heartbeat()["pending"], [])

    def test_a_stale_relay_with_no_cycle_stamp_is_judged_on_its_last_good_poll(self):
        """A beat an older relay wrote carries no `cycle_at`, and then the last good poll
        is all there is to judge running by, as it was before that field existed."""
        self.write("beat.json", {"at": stamp(T0 - timedelta(seconds=91)), "delivering": 0,
                                 "grace": 90})
        self.watchdog().round()
        self.assertIn("relay down", self.send.calls[0][2])
        self.assertIn("90s", self.send.calls[0][2])


    def test_a_relay_that_stopped_cycling_is_down_and_says_when_it_last_cycled(self):
        self.write("beat.json", {"at": stamp(T0 - timedelta(seconds=200)),
                                 "cycle_at": stamp(T0 - timedelta(seconds=200)),
                                 "delivering": 0, "grace": 90, "interval": 30})
        self.watchdog().round()
        text = self.send.calls[0][2]
        self.assertIn("relay down", text)
        self.assertIn(stamp(T0 - timedelta(seconds=200)), text)

    def test_a_relay_cycling_and_reading_is_reported_to_nobody(self):
        self.write("beat.json", {"at": stamp(T0 - timedelta(seconds=20)),
                                 "cycle_at": stamp(T0), "delivering": 0, "grace": 90,
                                 "interval": 30})
        self.board.tickets[61] = []
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])

    def test_a_relay_just_started_is_given_its_grace(self):
        self.write("beat.json", {"at": None})
        self.write("relay.json", {"pid": os.getpid(), "started": stamp(T0 - timedelta(seconds=10))})
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])

    def test_a_closed_night_ends_the_watchdog(self):
        self.write("watches.json", {})
        self.assertEqual(self.watchdog().round(), "closed")
        self.assertTrue(self.heartbeat()["closed"])

    # ------------------------------------------------------------- several watches

    OTHER = {"runner": "paseo", "session": "main-b"}

    def two_watches(self):
        """The night on spec 7 (orchestrator term_main) and ticket #70 alone (main-b)."""
        self.open_watches({"spec": 7, **MAIN}, {"tickets": [70], **self.OTHER})

    def test_a_finding_about_a_ticket_goes_to_the_main_agent_of_its_watch_alone(self):
        self.two_watches()
        self.ask.default = "unknown"
        self.board.tickets[70] = [comment(1, "worker.started", 70, self.SILENT, runner="herdr",
                                          session="h70")]
        self.watchdog().round()
        self.assertEqual([(c[0], c[1]) for c in self.send.calls], [("paseo", "main-b")])
        self.assertIn("#70", self.send.calls[0][2])
        self.silent_worker()
        self.watchdog().round()
        self.assertEqual([(c[0], c[1]) for c in self.send.calls[1:]], [("orca", "term_main")])
        self.assertIn("#61", self.send.calls[1][2])

    def test_relay_down_goes_to_every_main_agent_once_each(self):
        self.two_watches()
        self.relay_lock.__exit__(None, None, None)
        self.write("relay.lock", {"pid": os.getpid(), "identity": "Mon Jan  1 00:00:00 2001"})
        self.watchdog().round()
        self.assertEqual(sorted((c[0], c[1]) for c in self.send.calls),
                         [("orca", "term_main"), ("paseo", "main-b")])
        self.assertTrue(all("watchdog: relay down" in c[2] for c in self.send.calls))
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 2, "each orchestrator is told once per stretch")

    def test_a_main_agent_that_was_not_told_is_told_next_round_and_the_other_not_again(self):
        self.two_watches()
        self.relay_lock.__exit__(None, None, None)
        self.write("relay.lock", {"pid": os.getpid(), "identity": "Mon Jan  1 00:00:00 2001"})
        self.send.answers[("paseo", "main-b")] = 3
        self.send.default = 4
        self.watchdog().round()
        self.send.answers.clear()
        self.watchdog().round()
        self.assertEqual([(c[0], c[1]) for c in self.send.calls],
                         [("orca", "term_main"), ("paseo", "main-b"), ("paseo", "main-b")])

    def test_a_closed_ticket_of_a_night_is_not_read_and_a_ticket_watched_alone_is(self):
        self.two_watches()
        self.board.spec_children[7] = [61, (62, "closed")]
        self.watchdog().round()
        self.assertEqual(sorted(self.board.read), [61, 70])

    # ------------------------------------------------------------- idle

    IDLE = T0 - timedelta(hours=1)

    def idle_worker(self, *extra):
        self.board.tickets[61] = [comment(1, "worker.started", 61, self.IDLE, runner="herdr",
                                          session="h1"), *extra]

    def test_a_live_worker_with_nothing_to_wait_on_for_an_hour_is_a_finding_once(self):
        self.idle_worker()
        self.send.default = 4
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertEqual(self.send.calls[0][:2], ("orca", "term_main"))
        text = self.send.calls[0][2]
        self.assertTrue(text.startswith("watchdog: #61 silent since 2026-09-10T00:00:00Z"), text)
        self.assertIn("h1", text.split())
        self.assertIn("herdr", text.split())
        self.assertIn("dispatch.sh", text)
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1, "once per ticket and newest event")

    def test_a_live_worker_silent_less_than_an_hour_is_not_idle(self):
        self.silent_worker()
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])

    def test_a_live_worker_waiting_on_something_is_not_idle(self):
        for why, extra in (
                ("a live reviewer", comment(2, "reviewer.started", 61, self.IDLE, runner="orca",
                                            session="rv")),
                ("the landing of its pass", comment(2, "ticket.passed", 61, self.IDLE))):
            with self.subTest(why=why):
                self.send.calls.clear()
                (self.state / "watchdog.json").unlink(missing_ok=True)
                self.idle_worker(extra)
                (self.runners / "rv.state").write_text("working\n")
                self.watchdog().round()
                self.assertEqual(self.send.calls, [])

    def test_a_worker_that_is_not_alive_is_no_idle_finding(self):
        self.idle_worker()
        self.ask.default = "stopped"
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])
        self.assertEqual([c[1] for c in self.post.calls], ["worker"])

    def test_the_heartbeat_names_this_process_and_its_poll(self):
        self.silent_worker()
        self.watchdog().round()
        beat = self.heartbeat()
        self.assertEqual((beat["pid"], beat["identity"]), (os.getpid(), statedir.own_identity()))
        self.assertEqual((beat["poll"], beat["tolerance"]), (60, 300))
        self.assertEqual(beat["at"], stamp(T0))

    def test_a_round_that_could_not_read_a_ticket_does_not_say_nothing_is_held(self):
        class Failing(FakeBoard):
            def comments(self, ticket, since):
                raise dog.relay_mod.PollError("gh exited 1: HTTP 502")
        self.board = Failing({}, {7: [61]})
        self.watchdog().round()
        self.assertIsNone(self.heartbeat()["held"])

    def test_watchdog_reads_comments_conditionally(self):
        calls = []
        rows = [comment(1, "worker.started", 61, T0 - timedelta(minutes=2),
                        runner="herdr", session="h1")]

        def list_gh(args):
            return [{"number": 61, "state": "open"}]

        def raw_gh(args):
            calls.append(args)
            if 'If-None-Match: "comments"' in args:
                return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304"
            return 0, ("HTTP/2 200 OK\nETag: \"comments\"\n\n"
                       + json.dumps(rows)), ""

        reader = dog.relay_mod.ghlist.ConditionalListReader(raw_gh)
        self.board = dog.relay_mod.Board("o/r", list_gh, reader)
        wd = self.watchdog()
        wd.round()
        self.assertEqual(self.heartbeat()["held"], [61])
        wd.round()
        self.assertIn('If-None-Match: "comments"', calls[-1])
        self.assertEqual(self.heartbeat()["held"], [61])

    def test_heartbeat_records_read_counts(self):
        rows = [comment(1, "worker.started", 61, T0 - timedelta(minutes=2),
                        runner="herdr", session="h1")]

        def raw_gh(args):
            if 'If-None-Match: "comments"' in args:
                return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304"
            return 0, "HTTP/2 200 OK\nETag: \"comments\"\n\n" + json.dumps(rows), ""

        reader = dog.relay_mod.ghlist.ConditionalListReader(raw_gh)
        self.board = dog.relay_mod.Board("o/r", lambda args: [{"number": 61, "state": "open"}],
                                         reader)
        wd = self.watchdog()
        wd.round()
        self.assertEqual(self.heartbeat()["reads"], {"billed": 1, "not_modified": 0})
        wd.round()
        self.assertEqual(self.heartbeat()["reads"], {"billed": 1, "not_modified": 1})


class NoAlertForReadOutage(StateCase):
    def test_tracker_outages_do_not_alert_or_make_a_beating_watchdog_unhealthy(self):
        self.open_watches({"spec": 7, **MAIN})
        clock = Clock()
        send = Recorder(default=4)
        for never_read in (False, True):
            for failing in ("comments", "children"):
                with self.subTest(never_read=never_read, failing=failing):
                    self.write("watchdog.json", {"read_at": stamp(T0 - timedelta(hours=1)),
                                                  "read_failure": "HTTP 502"})
                    self.write("relay.json", {"started": stamp(T0 - timedelta(hours=1))})
                    board = FakeBoard({}, {7: [61]})
                    with statedir.locked(self.state / "relay.lock", wait=0, purpose="test relay"), \
                            mock.patch.object(board, failing,
                                              side_effect=dog.relay_mod.PollError("HTTP 502")):
                        for elapsed in (0, 301, 3600):
                            clock.moment = T0 + timedelta(seconds=elapsed)
                            self.write("beat.json", {"at": None if never_read else stamp(T0),
                                                      "cycle_at": stamp(clock()), "grace": 90,
                                                      "failure": "HTTP 502"})
                            wd = dog.Watchdog(self.state, "o/r", board=board, send=send,
                                              clock=clock, err=io.StringIO())
                            wd.round()
                            self.assertEqual(send.calls, [])
                            holder = {"pid": wd.beat["pid"], "identity": wd.beat["identity"]}
                            self.assertTrue(dog.health(holder, wd.beat, clock())[0])


class WaitingAlertOncePerWake(StateCase):
    def test_each_delivered_wake_is_reported_only_after_its_nudge_age(self):
        self.open_watches({"tickets": [61], **MAIN})
        clock = Clock()
        rows = [{"seq": seq, "ticket": 61, "event": "ticket.passed", "to": "main",
                 "watch": "tickets:61", **MAIN, "at": stamp(T0), "delivered": delivered}
                for seq, delivered in ([(1, stamp(T0)), (205, None)] +
                                       [(seq, stamp(T0 + timedelta(seconds=1)))
                                        for seq in range(2, 205)])]
        (self.state / "queue.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        for code in (0, 4):
            with self.subTest(send=code):
                (self.state / "watchdog.json").unlink(missing_ok=True)
                send = Recorder(default=code)
                with statedir.locked(self.state / "relay.lock", wait=0, purpose="test relay"):
                    for elapsed, expected in ((0, 0), (1799, 0), (1800, 1), (1801, 2),
                                               (3601, 2), (7200, 2)):
                        clock.moment = T0 + timedelta(seconds=elapsed)
                        self.write("beat.json", {"at": stamp(clock()), "cycle_at": stamp(clock()),
                                                  "grace": 90})
                        wd = dog.Watchdog(self.state, "o/r", board=FakeBoard({}), send=send,
                                          clock=clock, err=io.StringIO())
                        wd.round()
                        self.assertEqual(len(send.calls), expected, elapsed)
                self.assertTrue(all(call[:2] == (MAIN["runner"], MAIN["session"])
                                    and "#61" in call[2] and "ack" in call[2]
                                    for call in send.calls))


class Arm(StateCase):
    def test_a_new_lock_holder_is_not_killed_for_the_previous_watchdogs_stale_beat(self):
        code = (
            "import json, sys; from pathlib import Path\n"
            "sys.path.insert(0, sys.argv[1]); import statedir, watchdog\n"
            "state = Path(sys.argv[2])\n"
            "with statedir.locked(state / 'watchdog.lock', wait=0, purpose='new watchdog'):\n"
            "    print('held', flush=True)\n"
            "    sys.stdin.readline()\n"
            "    watchdog.Watchdog(state, 'o/r').write_beat()\n"
            "    print('beating', flush=True)\n"
            "    sys.stdin.readline()\n")
        holder = subprocess.Popen([sys.executable, "-c", code, str(SCRIPTS), str(self.state)],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: (holder.kill(), holder.wait(), holder.stdin.close(),
                                 holder.stdout.close()))
        self.assertEqual(holder.stdout.readline().strip(), "held")
        self.write("watchdog.json", {"pid": 99999999, "identity": "previous watchdog",
                                     "at": stamp(dog.now_utc() - timedelta(seconds=400)), "poll": 60})
        starter = Path(self.tmp.name) / "nodog.py"
        starter.write_text("raise SystemExit(1)\n")
        with mock.patch.dict(os.environ, {"MMW_WATCHDOG_PY": str(starter)}):
            dog.arm(self.state, "o/r", wait=0.1)
        self.assertIsNone(holder.poll(), "arm killed the new watchdog before its first heartbeat")
        holder.stdin.write("beat\n")
        holder.stdin.flush()
        self.assertEqual(holder.stdout.readline().strip(), "beating")
        ok, why = dog.arm(self.state, "o/r", wait=0.1)
        self.assertTrue(ok, why)
        self.assertEqual(statedir.holder(self.state / "watchdog.lock")["pid"], holder.pid)

    def test_a_watchdog_that_beats_is_not_ended_for_failing_reads(self):
        # A live holder whose heartbeat is fresh is slow or blind, not hung.
        holder = subprocess.Popen([sys.executable, "-c", (
            "import sys, time; sys.path.insert(0, %r); import statedir\n"
            "with statedir.locked(__import__('pathlib').Path(%r), wait=0, purpose='test'):\n"
            "    print('held', flush=True); time.sleep(30)\n") % (str(SCRIPTS), str(self.state / "watchdog.lock"))],
            stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: (holder.kill(), holder.wait(), holder.stdout.close()))
        self.assertEqual(holder.stdout.readline().strip(), "held")
        record = statedir.holder(self.state / "watchdog.lock")
        now = dog.now_utc()
        self.write("watchdog.json", {"pid": record["pid"], "identity": record["identity"],
                                     "at": stamp(now), "poll": 60,
                                     "read_at": stamp(now - timedelta(seconds=400)),
                                     "read_failure": "#61: HTTP 502"})
        ok, why = dog.arm(self.state, "o/r", wait=1)
        self.assertTrue(ok, why)
        self.assertIsNone(holder.poll(), "arm ended a watchdog that was beating")


class LostEvent(unittest.TestCase):
    def test_the_body_is_a_worker_lost_event_naming_the_pair(self):
        what, payload = events.parse(dog.lost_body("worker", 61, 7, "herdr", "h1", stamp(T0)))
        self.assertEqual(what, "event")
        self.assertEqual((payload["event"], payload["actor"], payload["runner"],
                          payload["session"], payload["ticket"], payload["spec"]),
                         ("worker.lost", "judge", "herdr", "h1", 61, 7))
        fold = events.fold([comment(1, "worker.started", 61, T0, runner="herdr", session="h1"),
                            {"id": 2, "body": dog.lost_body("worker", 61, 7, "herdr", "h1", None)}],
                           issue=61)
        self.assertFalse(fold["held"], "worker.lost ends the hold of the pair it names")

    def test_reviewer_lost_ends_only_its_own_hold(self):
        what, payload = events.parse(dog.lost_body("reviewer", 61, 7, "orca", "s2", None))
        self.assertEqual((what, payload["event"], payload["actor"]),
                         ("event", "reviewer.lost", "judge"))
        fold = events.fold([
            comment(1, "worker.started", 61, T0, runner="herdr", session="h1"),
            comment(2, "reviewer.started", 61, T0, runner="orca", session="s2"),
            {"id": 3, "body": dog.lost_body("reviewer", 61, 7, "orca", "s2", None)}],
            issue=61)
        self.assertEqual([(r["kind"], r["session"]) for r in fold["holders"]],
                         [("worker", "h1")])


if __name__ == "__main__":
    unittest.main()
