"""A refusal names the session that refused, and ends that session's hold and no other.

A worker `advance` started whose preflight refuses does nothing more on the ticket. Its
`ticket.refused` carries its (runner, session) as the dispatch skill's `self` reads them,
so the fold ends that start's hold and the next `advance` can start the ticket again once
the reason is fixed. Another session's hold is untouched, and a refusal that could not
name its session ends nothing.
"""

import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

import test_preflight as tp
from _load import event, load, load_events

vt = load()
ev = load_events()

FACTS = dict(machine="mac-1", host="grok", model="grok-4.6", effort="high", grade="junior-worker",
             worktree="/repo/.worktrees/issue-77", branch="issue-77", base="0" * 40)


def started(runner, session):
    return event("worker.started", f"worker started on {runner}: session {session}",
                 runner=runner, session=session, **FACTS)


def refused(**pair):
    return event("ticket.refused", "NOT_READY: branch is main, not issue-77", reason="wrong-branch",
                 **pair)


def live(bodies):
    return [(r["runner"], r["session"]) for r in ev.fold(bodies)["sessions"] if r["live"]]


class TestTheRefusalNamesItsSession(unittest.TestCase):
    def test_a_refused_preflight_posts_the_refusing_runner_and_session(self):
        with mock.patch.object(tp.vt, "own_session", return_value=("orca", "term_w77")):
            code, posted, _, _ = tp.preflight(branch="main")
        self.assertEqual(code, 2)
        what, payload = ev.parse(posted[0][1])
        self.assertEqual((payload["event"], payload["runner"], payload["session"]),
                         ("ticket.refused", "orca", "term_w77"))

    def test_a_session_that_cannot_name_itself_posts_the_refusal_without_one(self):
        with mock.patch.object(tp.vt, "own_session", return_value=None):
            code, posted, _, _ = tp.preflight(branch="main")
        self.assertEqual(code, 2)
        payload = ev.parse(posted[0][1])[1]
        self.assertNotIn("session", payload)
        self.assertNotIn("runner", payload)

    def retract_line(self, err):
        return [row for row in err.splitlines() if "dispatch.sh retract 77" in row]

    def refusal_line(self, read, **attrs):
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(tp.vt, "read_self", return_value=read))
            for name, value in attrs.items():
                stack.enter_context(mock.patch.object(tp.vt, name, value))
            code, posted, err, _ = tp.preflight(branch="main")
        self.assertEqual(code, 2)
        payload = ev.parse(posted[0][1])[1]
        self.assertEqual(payload["event"], "ticket.refused")
        self.assertNotIn("runner", payload)
        self.assertNotIn("session", payload)
        line = self.retract_line(err)
        self.assertEqual(len(line), 1)
        return line[0]

    def test_a_refusal_without_dispatch_sh_says_why_on_stderr(self):
        line = self.refusal_line(tp.vt.SelfRead("/missing/dispatch.sh", None, "", "", None))
        self.assertIn("/missing/dispatch.sh", line)

    def test_a_refusal_whose_self_fails_names_its_exit_code_on_stderr(self):
        line = self.refusal_line(tp.vt.SelfRead(
            "/skills/dispatch/scripts/dispatch.sh", 17, "", "adapter-down", None))
        self.assertIn("17", line)
        self.assertIn("adapter-down", line)

    def test_a_refusal_whose_self_prints_no_session_names_that_exit_on_stderr(self):
        line = self.refusal_line(tp.vt.SelfRead(
            "/skills/dispatch/scripts/dispatch.sh", 0, "no-session-token", "", None))
        self.assertIn("0", line)
        self.assertIn("no-session-token", line)

    def test_a_refusal_whose_self_cannot_be_run_names_that_on_stderr(self):
        line = self.refusal_line(tp.vt.SelfRead(
            "/skills/dispatch/scripts/dispatch.sh", None, "", "", "timed out"))
        self.assertIn("/skills/dispatch/scripts/dispatch.sh", line)
        self.assertIn("timed out", line)

    def test_a_refusal_without_refusal_py_still_names_retract_on_stderr(self):
        line = self.refusal_line(
            tp.vt.SelfRead("/missing/dispatch.sh", None, "", "", None),
            _REFUSAL_PY=Path("/missing/refusal.py"))
        self.assertIn("/missing/dispatch.sh", line)

    def test_a_refusal_that_names_its_session_prints_no_session_line(self):
        with mock.patch.object(tp.vt, "own_session", return_value=("orca", "term_w77")):
            code, posted, err, _ = tp.preflight(branch="main")
        self.assertEqual(code, 2)
        payload = ev.parse(posted[0][1])[1]
        self.assertEqual((payload["event"], payload["runner"], payload["session"]),
                         ("ticket.refused", "orca", "term_w77"))
        self.assertNotIn("dispatch.sh retract", err)
        self.assertEqual(tp.vt.engine.events.first_line(posted[0][1]), err.strip())

    def test_own_session_is_what_the_dispatch_skill_reads_from_this_process(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ORCA_TERMINAL_HANDLE", "HERDR_ENV", "HERDR_PANE_ID", "TERM_PROGRAM")}
        inside = dict(env, PASEO_AGENT_ID="agt_self_test")
        with mock.patch.object(vt.engine, "GH_ENV", inside):
            self.assertEqual(vt.own_session(vt.read_self()), ("paseo", "agt_self_test"))
        with mock.patch.object(vt.engine, "GH_ENV", env):
            self.assertIsNone(vt.own_session(vt.read_self()))


class TestTheFoldEndsThatHoldOnly(unittest.TestCase):
    def test_a_refusal_ends_the_hold_of_the_session_it_names(self):
        self.assertEqual(live([started("paseo", "agt_a"), refused(runner="paseo", session="agt_a")]), [])

    def test_a_refusal_by_another_session_leaves_the_worker_holding(self):
        self.assertEqual(live([started("paseo", "agt_a"), refused(runner="paseo", session="agt_b")]),
                         [("paseo", "agt_a")])

    def test_the_same_id_on_another_runner_is_another_session(self):
        self.assertEqual(live([started("paseo", "agt_a"), refused(runner="orca", session="agt_a")]),
                         [("paseo", "agt_a")])

    def test_a_refusal_that_names_no_session_ends_nothing(self):
        self.assertEqual(live([started("paseo", "agt_a"), refused()]), [("paseo", "agt_a")])

    def test_a_refusal_that_names_half_a_pair_is_not_an_event(self):
        with self.assertRaises(ValueError):
            refused(session="agt_a")


if __name__ == "__main__":
    unittest.main()
