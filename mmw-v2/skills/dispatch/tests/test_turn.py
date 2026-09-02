"""Tests for turn.py: one host event in, the Herdr calls it makes out.

Every test drives the script the way a host's hook does — the event as JSON on stdin,
the pane in the environment — and reads back the `herdr` commands it ran, which are
the whole of what it does.

    python3 -m unittest discover -s mmw-v2/skills/dispatch/tests
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

TURN_PATH = Path(__file__).resolve().parent.parent / "scripts" / "turn.py"
_spec = importlib.util.spec_from_file_location("turn", TURN_PATH)
turn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(turn)

INSIDE = {"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p7"}


class Harness(unittest.TestCase):
    def setUp(self):
        self.calls: list[list[str]] = []
        self.pane_tokens: dict = {}
        self.saved = turn.run, turn.pane_tokens
        turn.run = lambda args: self.calls.append(list(args))
        turn.pane_tokens = lambda pane: dict(self.pane_tokens)

    def tearDown(self):
        turn.run, turn.pane_tokens = self.saved

    def fire(self, host: str, event: dict, env: dict | None = None) -> int:
        with mock.patch.dict(os.environ, INSIDE if env is None else env, clear=True), \
             mock.patch.object(turn.sys, "stdin", io.StringIO(json.dumps(event))), \
             redirect_stderr(io.StringIO()):
            return turn.main([host])

    def states(self) -> list[str]:
        return [c[c.index("--state") + 1] for c in self.calls if c[:2] == ["pane", "report-agent"]]

    def tokens(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for c in self.calls:
            if c[:2] != ["pane", "report-metadata"]:
                continue
            for i, part in enumerate(c):
                if part == "--token":
                    key, value = c[i + 1].split("=", 1)
                    out[key] = value
                if part == "--clear-token":
                    out[c[i + 1]] = None
        return out


class TheMapping(Harness):
    """One event, one state, one token."""

    def test_session_start_is_idle_and_ready(self):
        self.fire("grok", {"hookEventName": "session_start"})
        self.assertEqual(self.states(), ["idle"])
        self.assertEqual(self.tokens(), {"turn": "ready", "turn_id": None})

    def test_a_late_session_start_does_not_end_a_turn_under_way(self):
        """Grok fires SessionStart with the first prompt, after UserPromptSubmit."""
        self.pane_tokens = {"turn": "working", "turn_id": "p-1"}
        self.fire("grok", {"hookEventName": "session_start"})
        self.assertEqual(self.calls, [])

    def test_a_prompt_is_working_and_remembers_the_turn(self):
        self.fire("grok", {"hookEventName": "user_prompt_submit", "promptId": "p-9"})
        self.assertEqual(self.states(), ["working"])
        self.assertEqual(self.tokens(), {"turn": "working", "turn_id": "p-9"})

    def test_a_prompt_without_an_id_still_gets_one(self):
        self.fire("claude", {"hook_event_name": "UserPromptSubmit"})
        self.assertEqual(self.states(), ["working"])
        self.assertTrue(self.tokens()["turn_id"])

    def test_a_finished_turn_is_idle_and_ended(self):
        self.fire("grok", {"hookEventName": "stop", "reason": "end_turn", "promptId": "p-9"})
        self.assertEqual(self.states(), ["idle"])
        self.assertEqual(self.tokens(), {"turn": "ended"})

    def test_a_failed_turn_carries_the_error_class(self):
        self.fire("grok", {"hookEventName": "stop_failure", "error": "server_error"})
        self.assertEqual(self.states(), ["idle"])
        self.assertEqual(self.tokens(), {"turn": "failed:server_error"})

    def test_a_cancelled_turn_carries_the_reason(self):
        self.fire("grok", {"hookEventName": "stop_cancelled", "reason": "no_progress"})
        self.assertEqual(self.states(), ["idle"])
        self.assertEqual(self.tokens(), {"turn": "cancelled:no_progress"})

    def test_the_idle_ping_settles_the_state_and_leaves_the_token(self):
        self.fire("grok", {"hookEventName": "notification", "notificationType": "idle_prompt"})
        self.assertEqual(self.states(), ["idle"])
        self.assertEqual(self.tokens(), {})

    def test_another_notification_does_nothing(self):
        self.fire("grok", {"hookEventName": "notification",
                           "notificationType": "permission_prompt"})
        self.assertEqual(self.calls, [])

    def test_session_end_releases_the_authority_and_clears_the_token(self):
        self.fire("grok", {"hookEventName": "session_end"})
        self.assertEqual([c[:2] for c in self.calls],
                         [["pane", "release-agent"], ["pane", "report-metadata"]])
        self.assertEqual(self.tokens(), {"turn": None, "turn_id": None})

    def test_claudes_spelling_of_the_event_name_is_read_too(self):
        self.fire("claude", {"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual(self.states(), ["idle"])
        self.assertEqual(self.tokens(), {"turn": "ended"})


class WhatItReportsUnder(Harness):
    def test_one_source_per_host_and_a_rising_seq(self):
        self.fire("grok", {"hookEventName": "user_prompt_submit"})
        self.fire("grok", {"hookEventName": "stop", "reason": "end_turn"})
        reports = [c for c in self.calls if c[:2] == ["pane", "report-agent"]]
        for report in reports:
            self.assertEqual(report[2], "w1:p7")
            self.assertEqual(report[report.index("--source") + 1], "mmw:grok")
            self.assertEqual(report[report.index("--agent") + 1], "grok")
        seqs = [int(r[r.index("--seq") + 1]) for r in reports]
        self.assertLess(seqs[0], seqs[1])

    def test_tokens_go_under_the_pipelines_own_source_with_the_usual_ttl(self):
        self.fire("grok", {"hookEventName": "user_prompt_submit"})
        meta = next(c for c in self.calls if c[:2] == ["pane", "report-metadata"])
        self.assertEqual(meta[meta.index("--source") + 1], "mmw")
        self.assertEqual(meta[meta.index("--ttl-ms") + 1], "86400000")


class WhatItLeavesAlone(Harness):
    def test_outside_herdr_nothing_happens(self):
        for env in ({}, {"HERDR_ENV": "1"}, {"HERDR_PANE_ID": "w1:p7"}):
            with self.subTest(env=env):
                self.calls.clear()
                self.fire("grok", {"hookEventName": "user_prompt_submit"}, env=env)
                self.assertEqual(self.calls, [])

    def test_a_subagents_event_is_not_the_sessions(self):
        self.fire("grok", {"hookEventName": "stop", "reason": "end_turn", "subagentType": "explore"})
        self.fire("claude", {"hook_event_name": "Stop", "agent_id": "a1"})
        self.assertEqual(self.calls, [])

    def test_groks_session_end_stop_is_left_to_session_end(self):
        self.fire("grok", {"hookEventName": "stop", "reason": "channel_closed"})
        self.assertEqual(self.calls, [])

    def test_a_report_for_an_older_turn_is_dropped(self):
        """A cancelled turn's report can arrive after the next turn's prompt."""
        self.pane_tokens = {"turn_id": "p-10"}
        self.fire("grok", {"hookEventName": "stop_cancelled", "reason": "user_interrupt",
                           "promptId": "p-9"})
        self.assertEqual(self.calls, [])

    def test_a_report_with_no_prompt_id_always_lands(self):
        self.pane_tokens = {"turn_id": "p-10"}
        self.fire("grok", {"hookEventName": "stop", "reason": "end_turn"})
        self.assertEqual(self.states(), ["idle"])

    def test_a_turn_never_seen_starting_still_lands(self):
        self.pane_tokens = {}
        self.fire("grok", {"hookEventName": "stop", "reason": "end_turn", "promptId": "p-9"})
        self.assertEqual(self.states(), ["idle"])

    def test_an_unknown_host_or_event_or_unreadable_input_does_nothing(self):
        self.assertEqual(self.fire("emacs", {"hookEventName": "stop"}), 0)
        self.assertEqual(self.fire("grok", {"hookEventName": "pre_compact"}), 0)
        with mock.patch.dict(os.environ, INSIDE, clear=True), \
             mock.patch.object(turn.sys, "stdin", io.StringIO("not json")):
            self.assertEqual(turn.main(["grok"]), 0)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
