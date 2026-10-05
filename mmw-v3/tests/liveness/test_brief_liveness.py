"""The watchdog and the turn guard for briefs: a session `dispatch.sh brief` started that dies,
or ends its turn, without reporting.

    python3 -m unittest discover -s mmw-v3/tests/liveness -p test_brief_liveness.py
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_liveness import MAIN, Clock, FakeBoard, Recorder, StateCase, dog, guard  # noqa: E402

import briefs  # noqa: E402


class BriefCase(StateCase):
    """A batch of two researchers on the fake runner, briefed by MAIN, its watch open."""

    def setUp(self):
        super().setUp()
        self.batch = briefs.create(self.state, "researcher", 2, MAIN["runner"], MAIN["session"])
        for n in (1, 2):
            briefs.mark_started(self.state, self.batch, n, {
                "runner": "fake", "session": f"child-{n}", "host": "grok",
                "model": "grok-4.7", "effort": "high"})
        self.write("watches.json", {f"briefs:{self.batch}": {"briefs": self.batch, **MAIN}})
        runners = Path(self.tmp.name) / "runners"
        runners.mkdir()
        (runners / "fake.sh").write_text(
            'case "$1" in self) printf "%s\\n" "$FAKE_SELF" ;; *) exit 3 ;; esac\n')
        self.env("MMW_RUNNERS_DIR", str(runners))

    def env(self, name: str, value: str) -> None:
        old = os.environ.get(name)
        os.environ[name] = value
        self.addCleanup(lambda: os.environ.pop(name) if old is None
                        else os.environ.__setitem__(name, old))

    def states(self):
        return [b["state"] for b in briefs.briefs_of(self.state, self.batch)]


class BriefRounds(BriefCase):
    def watchdog(self, ask):
        return dog.Watchdog(self.state, "o/r", board=FakeBoard({}), ask=ask, send=Recorder(default=0),
                            post=Recorder(default=(True, "")), clock=Clock(), pid=os.getpid(),
                            identity="test", err=io.StringIO())

    def test_a_stopped_child_is_marked_lost_and_a_live_one_stays_open(self):
        ask = Recorder({("fake", "child-1"): "stopped"}, default="alive")
        board = self.watchdog(ask)
        board.round()
        self.assertEqual(self.states(), ["lost", "open"])
        self.assertEqual(board.beat["briefs"], [f"{self.batch}/2"])
        self.assertEqual(board.beat["held"], [])

    def test_an_unknown_answer_is_not_a_death(self):
        board = self.watchdog(Recorder(default="unknown"))
        board.round()
        self.assertEqual(self.states(), ["open", "open"])

    def test_a_child_that_reported_is_not_asked(self):
        answer = Path(self.tmp.name) / "a.md"
        answer.write_text("found\n")
        briefs.report(self.state, self.batch, 1, answer, "fake", "child-1")
        ask = Recorder(default="alive")
        self.watchdog(ask).round()
        self.assertEqual([call[:2] for call in ask.calls], [("fake", "child-2")])


class BriefTurnEnd(BriefCase):
    def test_a_child_ending_its_turn_without_reporting_is_blocked_once_with_the_command(self):
        self.env("FAKE_SELF", "child-1")
        blocks = guard.guard("claude")
        self.assertEqual(len(blocks), 1)
        self.assertIn(f"report {self.batch}/1 <file>", blocks[0])
        self.assertEqual(guard.guard("claude", forced=True), [])

    def test_a_child_that_reported_ends_its_turn(self):
        answer = Path(self.tmp.name) / "a.md"
        answer.write_text("found\n")
        briefs.report(self.state, self.batch, 1, answer, "fake", "child-1")
        self.env("FAKE_SELF", "child-1")
        self.assertEqual(guard.guard("claude"), [])

    def test_a_session_that_is_no_child_is_not_held_by_the_batch(self):
        self.env("FAKE_SELF", "someone-else")
        self.assertEqual(guard.guard("claude"), [])

    def test_open_briefs_hold_the_parent_while_the_watchdog_is_not_healthy(self):
        # The parent runs on the fake runner; no watchdog runs and arming it fails.
        self.write("watches.json", {f"briefs:{self.batch}": {
            "briefs": self.batch, "runner": "fake", "session": "parent"}})
        self.write("watchdog.json", {"held": [], "briefs": [f"{self.batch}/1"]})
        self.env("FAKE_SELF", "parent")
        real_arm = dog.arm
        dog.arm = lambda state, repo, wait: (False, "it did not come up")
        self.addCleanup(setattr, dog, "arm", real_arm)
        real_load = guard.load_watchdog
        guard.load_watchdog = lambda: dog
        self.addCleanup(setattr, guard, "load_watchdog", real_load)
        blocks = guard.guard("claude")
        self.assertEqual(len(blocks), 1)
        self.assertIn(f"brief {self.batch}/1", blocks[0])


if __name__ == "__main__":
    unittest.main()
