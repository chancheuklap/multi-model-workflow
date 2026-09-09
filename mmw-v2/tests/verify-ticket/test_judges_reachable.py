"""A run refuses when a `CHECK:` names a judge no `--tools` directory holds.

The failure this prevents is not a loud one. A judge that is not on the shell's PATH
makes its criterion fail `command not found`, gate-check records one more unmet gate,
and the run exits 1 — indistinguishable from work that did not pass. `dispatch.sh
reverify` was found on 2026-09-08 running with no `--tools` at all, which reads as a
whole batch of interface tickets failing at once.
"""

import io
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import load

vt = load()

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts"


def ticket(check: str) -> str:
    return ("## Acceptance criteria\n\n"
            f"- [ ] AC1: the page matches its design\n  CHECK: {check}\n"
            "  EXPECT: /^STORY OK/m\n  EVIDENCE: pending\n")


STORY = ("story-parity.py --contract docs/specs/x/screen-contract.yaml "
         "--pages create-project")


class RequireJudges(unittest.TestCase):
    def tearDown(self):
        vt.TOOLS[:] = []

    def test_a_judge_in_no_tools_directory_and_not_on_path_is_refused(self):
        with self.assertRaises(vt.JudgeUnreachable) as caught:
            vt.require_judges(ticket(STORY))
        self.assertIn("story-parity.py", str(caught.exception))
        self.assertIn("--tools", str(caught.exception))

    def test_the_tools_directory_answers(self):
        vt.TOOLS[:] = [SCRIPTS]
        self.assertIsNone(vt.require_judges(ticket(STORY)))

    def test_a_judge_on_path_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "story-parity.py"
            fake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
            with mock.patch.dict(os.environ, {"PATH": tmp + os.pathsep + os.environ["PATH"]}):
                self.assertIsNone(vt.require_judges(ticket(STORY)))

    def test_a_ticket_naming_no_judge_is_not_refused(self):
        self.assertIsNone(vt.require_judges(ticket("pnpm vitest run tests/a.test.ts")))

    def test_every_missing_judge_is_named_at_once(self):
        body = ("## Acceptance criteria\n\n"
                f"- [ ] AC1: look\n  CHECK: {STORY}\n  EXPECT: /^STORY OK/m\n"
                "  EVIDENCE: pending\n"
                "- [ ] AC2: the click calls\n  CHECK: boundary-check.py --run \"pnpm t\"\n"
                "  EXPECT: /^BOUNDARY OK/m\n  EVIDENCE: pending\n"
                "- [ ] AC3: the journey\n  CHECK: journey.py run smoke\n"
                "  EXPECT: JOURNEY OK smoke\n  EVIDENCE: pending\n"
                "- [ ] AC4: the harness\n  CHECK: harness-guard.py src\n"
                "  EXPECT: HARNESS OK\n  EVIDENCE: pending\n")
        with self.assertRaises(vt.JudgeUnreachable) as caught:
            vt.require_judges(body)
        for judge in ("story-parity.py", "boundary-check.py", "journey.py",
                      "harness-guard.py"):
            self.assertIn(judge, str(caught.exception))

    def test_the_harness_guard_is_a_judge_like_the_other_three(self):
        """A `CHECK:` naming it that the shell cannot answer is refused, not run and failed."""
        with self.assertRaises(vt.JudgeUnreachable) as caught:
            vt.require_judges(ticket("harness-guard.py src"))
        self.assertIn("harness-guard.py", str(caught.exception))


class NothingIsWritten(unittest.TestCase):
    """The refusal comes before the run, so the ticket is left exactly as it was.

    Both runs pass `--tools` at an empty directory: `main()` otherwise resolves the
    `drive-target` skill's `scripts/` beside this checkout, where the judges really are.
    """

    def tearDown(self):
        vt.TOOLS[:] = []

    def test_run_checks_exits_2_and_posts_no_comment(self):
        posted = []
        with tempfile.TemporaryDirectory() as empty, \
             mock.patch.object(vt, "fetch_body", return_value=ticket(STORY)), \
             mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = vt.main(["1", "--tools", empty])
        self.assertEqual(code, 2)
        self.assertEqual(posted, [])
        self.assertIn("story-parity.py", err.getvalue())

    def test_run_lint_exits_2_rather_than_reporting_a_finding(self):
        with tempfile.TemporaryDirectory() as empty, \
             mock.patch.object(vt, "fetch_body", return_value=ticket(STORY)), \
             mock.patch.object(vt, "ticket_labels", return_value=["ready-for-agent",
                                                                  "junior-worker"]):
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = vt.main(["1", "--lint", "--tools", empty])
        self.assertEqual(code, 2)
        self.assertIn("story-parity.py", err.getvalue())


if __name__ == "__main__":
    unittest.main()
