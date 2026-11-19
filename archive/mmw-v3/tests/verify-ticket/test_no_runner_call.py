"""No run of `verify-ticket.py` tells anybody anything through a runner.

What a run posts on the ticket is the whole of its news: the relay of the dispatch skill
reads the event there and wakes the session waiting on it. So a run that lands a ticket,
refuses it, or posts a review calls no runner binary, even inside a runner's session —
where the old runs sent the session that started them a message.
"""

import re
import unittest
from unittest import mock

from _load import SCRIPT, load

import test_closeout
import test_preflight
import test_review

vt = load()

RUNNERS = ("paseo", "orca", "herdr")
INSIDE = {"PASEO_AGENT_ID": "agt_main", "ORCA_TERMINAL_HANDLE": "term_main",
          "HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p1"}


class RunnerCalls:
    """`subprocess.run` for the whole process: a runner binary is recorded and answered,
    anything else goes to the real one."""

    def __init__(self):
        self.real = vt.subprocess.run
        self.calls = []

    def __call__(self, argv, *args, **kwargs):
        if isinstance(argv, (list, tuple)) and argv and str(argv[0]) in RUNNERS:
            self.calls.append(list(argv))
            return mock.Mock(returncode=0, stdout='{"ParentAgentId": "agt_parent"}', stderr="")
        return self.real(argv, *args, **kwargs)


def inside_a_runner(fn, *args, **kwargs):
    calls = RunnerCalls()
    with mock.patch.dict(vt.os.environ, INSIDE), \
         mock.patch.object(vt.subprocess, "run", side_effect=calls):
        result = fn(*args, **kwargs)
    return result, calls.calls


class TestNoRunnerIsCalled(unittest.TestCase):
    def test_a_passed_closeout_calls_no_runner(self):
        (code, err, _), calls = inside_a_runner(
            test_closeout.check, test_closeout.draft(counts=test_closeout.counts_line()),
            check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(calls, [])

    def test_a_handed_back_closeout_calls_no_runner(self):
        text = test_closeout.draft(
            first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
            criteria=(test_closeout.MET, test_closeout.UNMET),
            abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
            counts=test_closeout.counts_line(met=1, abandoned=1, total=2))
        (code, err, _), calls = inside_a_runner(test_closeout.check, text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(calls, [])

    def test_a_refused_preflight_calls_no_runner(self):
        (code, posted, _, _), calls = inside_a_runner(test_preflight.preflight, branch="main")
        self.assertEqual(code, 2)
        self.assertEqual(len(posted), 1)
        self.assertEqual(calls, [])

    def test_a_posted_review_runs_gh_and_nothing_else(self):
        with mock.patch.dict(vt.os.environ, INSIDE):
            code, err, fake = test_review.run_review()
        self.assertEqual(code, 0, err)
        self.assertEqual({c[0] for c in fake.recorded}, {"gh"})

    def test_the_script_names_no_runner_binary_and_no_runner_session_variable(self):
        """The sub-issue path posts through `gh issue create`, which the fixtures here do
        not reach; the source is where every path of the script can be read at once."""
        source = SCRIPT.read_text(encoding="utf-8")
        for name in RUNNERS:
            self.assertIsNone(re.search(r"[\[(,]\s*[\"']" + name + r"[\"']", source),
                              f"verify-ticket.py runs {name}")
        for variable in ("PASEO_AGENT_ID", "ORCA_TERMINAL_HANDLE", "HERDR_PANE_ID"):
            self.assertNotIn(variable, source)


if __name__ == "__main__":
    unittest.main()
