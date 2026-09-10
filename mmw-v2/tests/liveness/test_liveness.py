"""Tests for the three layers of liveness: turn-guard.py's predicate, watchdog.py's
heartbeat, tolerance and lock, and the third layer's three answers. No tracker, no runner,
no network, no waiting for a real poll.

The seam is this machine's state directory plus the runner: `MMW_HOME` points at a
temporary directory holding the heartbeat, the locks and the relay's files, the board is a
fake `Board` answering from a dict of comments, and the runner's `liveness` and `send`
verbs, and the `worker.lost` post, are functions here that record what they were handed.
What is asserted is what an outsider sees: whether a turn end is blocked, whether a
watchdog reads as healthy, what was posted on which ticket, who was asked, and what the
main agent was sent.

    python3 -m unittest discover -s mmw-v2/tests/liveness -p 'test_*.py'
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
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


REQUIRED = {
    "worker.started": {"host": "claude", "model": "m", "effort": "high", "grade": "junior-worker",
                       "worktree": "/repo/.worktrees/issue-61", "branch": "issue-61",
                       "base": "0" * 40},
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
    def __init__(self, tickets: dict[int, list[dict]], spec_children=None):
        self.tickets = tickets
        self.spec_children = spec_children or {}

    def comments(self, ticket, since):
        return list(self.tickets.get(ticket, []))

    def sub_issues(self, number):
        return list(self.spec_children.get(number, []))


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


# ----------------------------------------------------------------- tolerance and health

class Tolerance(unittest.TestCase):
    def test_short_polls_keep_the_floor(self):
        self.assertEqual(dog.tolerance(60), 300)
        self.assertEqual(dog.tolerance(240), 300)

    def test_it_grows_with_the_poll_once_the_poll_passes_the_floor(self):
        # A fixed 300 would read a healthy watchdog polling every 300s as dead mid-wait.
        self.assertEqual(dog.tolerance(300), 360)
        self.assertEqual(dog.tolerance(1000), 1060)

    def test_an_unreadable_poll_takes_the_default(self):
        self.assertEqual(dog.tolerance(None), 300)
        self.assertEqual(dog.tolerance("x"), 300)


class Health(unittest.TestCase):
    HOLDER = {"pid": 4242, "identity": "Thu Sep 10 01:00:00 2026"}

    def beat(self, age: int, poll: int = 60, **over) -> dict:
        return {"pid": 4242, "identity": "Thu Sep 10 01:00:00 2026",
                "at": stamp(T0 - timedelta(seconds=age)), "poll": poll, **over}

    def test_no_live_holder_is_not_healthy_whatever_the_heartbeat_says(self):
        ok, why = dog.health(None, self.beat(1), T0)
        self.assertFalse(ok)
        self.assertIn("no watchdog is running", why)

    def test_a_live_holder_with_no_heartbeat_is_not_healthy(self):
        self.assertFalse(dog.health(self.HOLDER, None, T0)[0])
        self.assertFalse(dog.health(self.HOLDER, {}, T0)[0])

    def test_a_heartbeat_another_process_wrote_proves_nothing(self):
        ok, why = dog.health(self.HOLDER, self.beat(1, pid=999), T0)
        self.assertFalse(ok)
        self.assertIn("pid 999", why)
        ok, _ = dog.health(self.HOLDER, self.beat(1, identity="another start"), T0)
        self.assertFalse(ok)

    def test_fresh_within_the_tolerance_and_stale_past_it(self):
        self.assertTrue(dog.health(self.HOLDER, self.beat(300), T0)[0])
        ok, why = dog.health(self.HOLDER, self.beat(301), T0)
        self.assertFalse(ok)
        self.assertIn("301s ago, past its tolerance of 300s", why)

    def test_a_long_poll_is_not_read_as_stale_mid_wait(self):
        # poll 400: the tolerance is 460, so a heartbeat 400s old is a watchdog asleep.
        self.assertTrue(dog.health(self.HOLDER, self.beat(400, poll=400), T0)[0])
        self.assertFalse(dog.health(self.HOLDER, self.beat(461, poll=400), T0)[0])


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
        ok, why, _ = dog.read_health(self.state)
        self.assertFalse(ok)
        self.assertIn("no watchdog is running", why)

    def test_a_recycled_pid_is_not_the_watchdog(self):
        # A live pid whose process started at another time than the one recorded: the pid
        # was handed to another process, and a pid-only check would call it the watchdog.
        self.write("watchdog.lock", {"pid": os.getpid(), "identity": "Mon Jan  1 00:00:00 2001"})
        self.heartbeat_by(os.getpid(), "Mon Jan  1 00:00:00 2001")
        ok, why, _ = dog.read_health(self.state)
        self.assertFalse(ok)
        self.assertIn("no watchdog is running", why)

    def test_the_running_watchdog_holds_its_lock_with_its_identity(self):
        with statedir.locked(self.state / "watchdog.lock", wait=0, purpose="test"):
            record = statedir.holder(self.state / "watchdog.lock")
            self.assertEqual(record["pid"], os.getpid())
            self.assertEqual(record["identity"], statedir.process_identity(os.getpid()))


# ----------------------------------------------------------------- the guard predicate

class Verdict(unittest.TestCase):
    def test_a_healthy_watchdog_lets_the_turn_end(self):
        self.assertEqual(guard.verdict([61], True, "fine"), (False, "fine"))

    def test_held_tickets_and_no_healthy_watchdog_block(self):
        block, why = guard.verdict([61, 62], False, "no watchdog is running")
        self.assertTrue(block)
        self.assertEqual(why, "no watchdog is running")

    def test_not_knowing_what_is_held_blocks(self):
        # No heartbeat, or a round that could not read every ticket, is not "nothing held".
        self.assertTrue(guard.verdict(None, False, "x")[0])

    def test_nothing_held_at_the_last_round_lets_the_turn_end(self):
        block, why = guard.verdict([], False, "no watchdog is running")
        self.assertFalse(block)
        self.assertIn("nothing is held", why)


class HostSide(unittest.TestCase):
    def test_the_claude_copy_stands_down_on_either_grok_marker(self):
        self.assertTrue(guard.stands_down("claude", {}, {"GROK_AGENT": "1"}))
        self.assertTrue(guard.stands_down("claude", {}, {"GROK_HOOK_EVENT": "stop"}))

    def test_the_claude_copy_never_stands_down_on_grok_session_id(self):
        self.assertIsNone(guard.stands_down("claude", {}, {"GROK_SESSION_ID": "s"}))

    def test_cursor_is_told_by_its_payload_never_its_environment(self):
        self.assertTrue(guard.stands_down("claude", {"cursor_version": "2026.09.08"}, {}))
        self.assertIsNone(guard.stands_down("claude", {}, {"CURSOR_VERSION": "x",
                                                            "CURSOR_INVOKED_AS": "cursor-agent"}))
        self.assertIsNone(guard.stands_down("cursor", {"cursor_version": "2026.09.08"}, {}))
        self.assertTrue(guard.stands_down("cursor", {"hookEventName": "stop"}, {"GROK_HOOK_EVENT": "stop"}))

    def test_the_grok_and_codex_copies_do_not_stand_down_on_the_grok_markers(self):
        self.assertIsNone(guard.stands_down("grok", {}, {"GROK_HOOK_EVENT": "stop"}))
        self.assertIsNone(guard.stands_down("codex", {}, {}))

    def test_a_stop_forced_by_an_earlier_block_is_let_through(self):
        self.assertTrue(guard.continuation("claude", {"stop_hook_active": True}))
        self.assertFalse(guard.continuation("claude", {"stop_hook_active": False}))
        self.assertTrue(guard.continuation("codex", {"stop_hook_active": True}))
        self.assertTrue(guard.continuation("grok", {"stopHookActive": True}))
        # The camel-case field wins when both are there.
        self.assertFalse(guard.continuation("grok", {"stopHookActive": False, "stop_hook_active": True}))
        self.assertTrue(guard.continuation("grok", {"stop_hook_active": True}))
        self.assertFalse(guard.continuation("cursor", {"loop_count": 0}))
        self.assertTrue(guard.continuation("cursor", {"loop_count": 1}))
        self.assertFalse(guard.continuation("pi", {"stop_hook_active": True}))

    def test_groks_session_end_fire_is_not_a_turn(self):
        self.assertTrue(guard.session_end("grok", {"reason": "shutdown"}))
        self.assertFalse(guard.session_end("grok", {"reason": "end_turn"}))
        self.assertFalse(guard.session_end("grok", {}))
        self.assertFalse(guard.session_end("claude", {"reason": "shutdown"}))

    def test_each_host_is_answered_in_its_own_terms(self):
        self.assertEqual(guard.answer("claude", True, "why"), (2, "", "why\n"))
        self.assertEqual(guard.answer("pi", True, "why"), (2, "", "why\n"))
        code, out, err = guard.answer("cursor", True, "why")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), {"followup_message": "why"})
        self.assertEqual(guard.answer("cursor", False, "why"), (0, "", ""))


# ----------------------------------------------------------------- the night

class NightOpen(StateCase):
    def test_a_running_or_dead_relays_record_is_an_open_night(self):
        self.write("relay.json", {"pid": 1, "watch": {"spec": 7}})
        self.assertTrue(dog.night_open(self.state))

    def test_a_last_good_poll_without_a_record_is_an_open_night(self):
        # A relay that exited on an error removed relay.json and left its last good poll.
        self.write("beat.json", {"at": stamp(T0)})
        self.assertTrue(dog.night_open(self.state))

    def test_a_relay_stopped_on_purpose_closes_the_night(self):
        self.write("beat.json", {"at": None, "stopped": stamp(T0)})
        self.assertFalse(dog.night_open(self.state))
        self.assertFalse(dog.night_open(statedir.state_dir("o/never")))

    def test_an_unreadable_beat_is_not_a_closed_night(self):
        (self.state / "beat.json").write_text("{not json", encoding="utf-8")
        self.assertTrue(dog.night_open(self.state))


# ----------------------------------------------------------------- the third layer

class Judge(unittest.TestCase):
    def fold(self, *comments):
        return events.fold(list(comments), issue=61)

    def test_a_ticket_nobody_holds_is_free(self):
        f = self.fold(comment(1, "worker.started", 61, T0, runner="orca", session="t1"),
                      comment(2, "ticket.landed", 61, T0))
        self.assertEqual(dog.judge(f, T0 + timedelta(hours=5), 600)["state"], "free")

    def test_the_waiting_step_is_not_silence(self):
        # The fold's `waiting` (spec #315 section 9) is the worker.queued its run waits under.
        fold = {"held": True, "unreadable": [], "last": {"event": "worker.queued",
                "at": stamp(T0)}, "waiting": {"event": "worker.queued", "at": stamp(T0)},
                "live_workers": [{"runner": "orca", "session": "t1"}]}
        self.assertEqual(dog.judge(fold, T0 + timedelta(hours=5), 600)["state"], "waiting")
        fold["waiting"] = None
        self.assertEqual(dog.judge(fold, T0 + timedelta(hours=5), 600)["state"], "silent")

    def test_waiting_ends_at_the_next_run(self):
        # The real fold: worker.queued makes the ticket wait, a later event that is not
        # ticket.checked leaves it waiting, and ticket.checked ends the wait.
        started = comment(1, "worker.started", 61, T0, runner="orca", session="t1")
        queued = comment(2, "worker.queued", 61, T0, reason="product-full", run="self")
        decided = comment(3, "worker.decided", 61, T0)
        checked = comment(4, "ticket.checked", 61, T0, run="self", commit="a" * 40, result="met")
        later = T0 + timedelta(hours=2)
        self.assertEqual(dog.judge(self.fold(started, queued), later, 600)["state"], "waiting")
        self.assertEqual(dog.judge(self.fold(started, queued, decided), later, 600)["state"], "waiting")
        self.assertEqual(dog.judge(self.fold(started, queued, checked), later, 600)["state"], "silent")

    def test_a_recent_event_is_not_silence(self):
        f = self.fold(comment(1, "worker.started", 61, T0, runner="orca", session="t1"))
        self.assertEqual(dog.judge(f, T0 + timedelta(seconds=599), 600)["state"], "recent")
        verdict = dog.judge(f, T0 + timedelta(seconds=600), 600)
        self.assertEqual(verdict["state"], "silent")
        self.assertEqual(verdict["pairs"], [("orca", "t1")])

    def test_only_the_live_workers_pair_is_named(self):
        f = self.fold(comment(1, "worker.started", 61, T0, runner="herdr", session="h1"),
                      comment(2, "worker.replaced", 61, T0, runner="herdr", session="h1"),
                      comment(3, "worker.started", 61, T0, runner="orca", session="t2"))
        self.assertEqual(dog.judge(f, T0 + timedelta(hours=1), 600)["pairs"], [("orca", "t2")])

    def test_an_unreadable_event_is_its_own_answer(self):
        f = events.fold(["prose", "x\n\n<!-- mmw {not json} -->"], issue=61)
        self.assertEqual(dog.judge(f, T0, 600)["state"], "unreadable")


class Rounds(StateCase):
    """Watchdog.round over a fake board, fake runner verbs and a fake post."""

    SILENT = T0 - timedelta(minutes=30)

    def setUp(self):
        super().setUp()
        self.write("recipient.json", MAIN)
        # An open night whose relay is healthy: this process holds the relay's lock with its
        # own identity, and the relay polled a moment ago.
        self.relay_lock = statedir.locked(self.state / "relay.lock", wait=0, purpose="test relay")
        self.relay_lock.__enter__()
        self.addCleanup(self.relay_lock.__exit__, None, None, None)
        self.write("relay.json", {"pid": os.getpid(), "identity": statedir.own_identity(),
                                  "watch": {"spec": 7}, "started": stamp(T0 - timedelta(hours=1))})
        self.write("beat.json", {"at": stamp(T0), "delivering": 0, "grace": 90, "interval": 30})
        self.board = FakeBoard({}, {7: [61]})
        self.ask = Recorder(default="alive")
        self.send = Recorder(default=0)
        self.post = Recorder(default=(True, ""))
        self.clock = Clock()

    def watchdog(self) -> "dog.Watchdog":
        return dog.Watchdog(self.state, "o/r", board=self.board, ask=self.ask, send=self.send,
                            post=self.post, clock=self.clock, pid=os.getpid(),
                            identity=statedir.own_identity(), err=io.StringIO())

    def silent_worker(self, runner="herdr", session="h1"):
        self.board.tickets[61] = [comment(1, "worker.started", 61, self.SILENT, runner=runner,
                                          session=session)]

    def heartbeat(self) -> dict:
        return json.loads((self.state / "watchdog.json").read_text())

    def test_stopped_posts_worker_lost_for_that_pair_and_nothing_else(self):
        self.silent_worker()
        self.ask.answers[("herdr", "h1")] = "stopped"
        self.assertEqual(self.watchdog().round(), "watching")
        self.assertEqual(len(self.post.calls), 1)
        repo, ticket, spec, runner, session, since = self.post.calls[0]
        self.assertEqual((repo, ticket, spec, runner, session), ("o/r", 61, 7, "herdr", "h1"))
        self.assertEqual(since, stamp(self.SILENT))
        self.assertEqual(self.send.calls, [], "worker.lost wakes the main agent through the relay")
        self.assertEqual(self.heartbeat()["lost"]["61"]["session"], "h1")

    def test_unknown_is_recorded_and_reported_never_posted(self):
        self.silent_worker()
        self.ask.answers[("herdr", "h1")] = "unknown"
        self.watchdog().round()
        self.assertEqual(self.post.calls, [])
        beat = self.heartbeat()
        self.assertEqual(beat["unknown"]["61"]["session"], "h1")
        self.assertEqual(beat["held"], [61])
        self.assertEqual(len(self.send.calls), 1)
        runner, session, text = self.send.calls[0]
        self.assertEqual((runner, session), ("orca", "term_main"))
        self.assertIn("#61 liveness unknown", text)
        self.assertNotIn("alive", text.replace("is alive", ""))

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

    def test_a_ticket_waiting_for_a_slot_is_not_asked(self):
        self.silent_worker()
        self.board.tickets[61].append(comment(2, "worker.queued", 61, self.SILENT,
                                              reason="machine-full", run="self"))
        self.ask.default = "stopped"
        self.watchdog().round()
        self.assertEqual((self.ask.calls, self.post.calls, self.send.calls), ([], [], []))
        beat = self.heartbeat()
        self.assertEqual((beat["held"], beat["waiting"]), ([61], [61]))

    def test_a_recent_ticket_is_not_asked(self):
        self.board.tickets[61] = [comment(1, "worker.started", 61, T0 - timedelta(minutes=2),
                                          runner="herdr", session="h1")]
        self.watchdog().round()
        self.assertEqual(self.ask.calls, [])

    def test_a_held_ticket_with_no_worker_session_is_reported(self):
        self.board.tickets[61] = [comment(1, "ticket.claimed", 61, self.SILENT)]
        self.watchdog().round()
        self.assertEqual(self.ask.calls, [])
        self.assertIn("#61 is held with no worker session to ask", self.send.calls[0][2])

    def test_a_finding_is_reported_once_across_rounds_and_restarts(self):
        self.silent_worker()
        self.ask.default = "unknown"
        self.send.default = 4  # handed over, not confirmed: the watchdog keeps running
        self.assertEqual(self.watchdog().round(), "watching")
        self.watchdog().round()  # a new watchdog process reads what was reported
        self.assertEqual(len(self.send.calls), 1)
        # A new event starts a new stretch: silent again, asked again, reported again.
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

    def test_a_dead_relay_is_reported_the_way_a_stalled_ticket_is(self):
        self.relay_lock.__exit__(None, None, None)
        self.write("relay.lock", {"pid": os.getpid(), "identity": "Mon Jan  1 00:00:00 2001"})
        self.board.tickets[61] = []
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1)
        self.assertIn("watchdog: relay down (no relay is running", self.send.calls[0][2])
        self.watchdog().round()
        self.assertEqual(len(self.send.calls), 1, "one report per stretch")

    def test_a_stale_relay_is_reported(self):
        self.write("beat.json", {"at": stamp(T0 - timedelta(seconds=91)), "delivering": 0,
                                 "grace": 90})
        self.watchdog().round()
        self.assertIn("past its grace of 90s", self.send.calls[0][2])

    def test_a_relay_just_started_is_given_its_grace(self):
        self.write("beat.json", {"at": None})
        self.write("relay.json", {"pid": os.getpid(), "watch": {"spec": 7},
                                  "started": stamp(T0 - timedelta(seconds=10))})
        self.watchdog().round()
        self.assertEqual(self.send.calls, [])

    def test_a_closed_night_ends_the_watchdog(self):
        (self.state / "relay.json").unlink()
        self.write("beat.json", {"at": None, "stopped": stamp(T0)})
        self.assertEqual(self.watchdog().round(), "closed")
        self.assertTrue(self.heartbeat()["closed"])

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


class LostEvent(unittest.TestCase):
    def test_the_body_is_a_worker_lost_event_naming_the_pair(self):
        what, payload = events.parse(dog.lost_body(61, 7, "herdr", "h1", stamp(T0)))
        self.assertEqual(what, "event")
        self.assertEqual((payload["event"], payload["actor"], payload["runner"],
                          payload["session"], payload["ticket"], payload["spec"]),
                         ("worker.lost", "judge", "herdr", "h1", 61, 7))
        fold = events.fold([comment(1, "worker.started", 61, T0, runner="herdr", session="h1"),
                            {"id": 2, "body": dog.lost_body(61, 7, "herdr", "h1", None)}], issue=61)
        self.assertFalse(fold["held"], "worker.lost ends the hold of the pair it names")


if __name__ == "__main__":
    unittest.main()
