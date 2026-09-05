"""`--draft`: write the closing-comment skeleton, with two `<fill>` placeholders."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests._load import load

vt = load()

ME = "chancheuklap"
VERIFIED = "3f9c2e1adeadbeefcafe0123456789abcdef0123"
HEAD = "9b1d40c7feedface0011223344556677889900aa"

BODY = """## Parent

#118, Implementation Decisions section 11

## Acceptance criteria

- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: pending
"""

MET_RUN = """self-run
ALL MET (1)

- [x] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=9

Outside Owns: None
"""

FAILED_RUN = """self-run
UNMET: 1 (met: 0)

- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: exit=1; EXPECT=missed; output-bytes=4
ABANDON: AC1 failed chromium kept crashing; tried the bundled build too

Outside Owns: None
"""

FILES_RUN = MET_RUN.replace("Outside Owns: None", "Outside Owns: src/helper.py")

VERDICT = f"VERDICT {VERIFIED} by opus — the importer writes six rows"

REVIEW = """REVIEW abcdef0..1234567

## Spec

### Decisions

- `src/helper.py`: reasonable — the ticket left the helper unnamed

## Tests

None
"""

DECISIONS = """DECISIONS

## Decisions I made on my own

picked the existing helper

## Outside Owns

Outside Owns: src/helper.py
src/helper.py was required for AC1
"""


def fake_git(*args, cwd=None):
    if args[:2] == ("rev-parse", "HEAD"):
        return HEAD
    if args[:1] == ("config",) and args[1].endswith(".mmw-base-branch"):
        return "herdr-to-paseo"
    if args[0] == "log":
        return HEAD
    if args[:2] == ("rev-parse", "--abbrev-ref"):
        return "issue-77"
    return ""


def run_draft(comments, body=BODY, children=(), child_bodies=None, check_closeout=False,
              sub_issues_by_parent=None):
    """Write a skeleton for ticket 77; return (exit, stderr, text, closeout-exit)."""
    child_bodies = child_bodies or {}
    closeout_code = None
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "draft.md"

        def fake_body(n):
            if n == 77:
                return body
            return child_bodies.get(n, "")

        def fake_ticket(n):
            return {"state": "OPEN", "labels": [],
                    "assignees": [{"login": ME}]}

        def fake_sub_issues(n):
            if sub_issues_by_parent is not None:
                return list(sub_issues_by_parent.get(n, ()))
            return list(children)

        with mock.patch.object(vt, "fetch_body", side_effect=fake_body), \
             mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
             mock.patch.object(vt, "fetch_sub_issues", side_effect=fake_sub_issues), \
             mock.patch.object(vt, "fetch_ticket", side_effect=fake_ticket), \
             mock.patch.object(vt, "gh_login", return_value=ME), \
             mock.patch.object(vt, "repo_root", return_value=None), \
             mock.patch.object(vt, "git", side_effect=fake_git), \
             mock.patch.object(vt, "is_ancestor", return_value=True), \
             mock.patch.object(vt, "dirty_tracked", return_value=[]):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_draft(77, path)
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            if check_closeout and path.is_file():
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    closeout_code = vt.run_closeout(77, path, True)
    return code, err.getvalue(), text, closeout_code


class TestFirstLine(unittest.TestCase):
    def test_all_met_when_the_self_run_has_no_failed_or_stuck_abandon(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")

    def test_handoff_when_the_self_run_abandons_as_failed(self):
        code, err, text, _ = run_draft((FAILED_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        first = text.splitlines()[0]
        self.assertTrue(first.startswith("HANDOFF REQUIRED:"), first)
        self.assertIn("abandoned (failed)", first)
        self.assertIn("0 unmet", first)
        self.assertIn("0 met of 1", first)


class TestFixedLines(unittest.TestCase):
    def test_the_branch_line_names_head_and_the_base_branch(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertIn(
            f"Branch: issue-77 Commit: {HEAD} PR: none — will be merged into "
            "herdr-to-paseo by dispatch.sh advance",
            text,
        )

    def test_post_verdict_lists_the_first_parent_chain_after_the_verdict(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertIn(f"Post-verdict: {HEAD}", text)

    def test_each_criterion_carries_four_lines_and_the_self_run_evidence(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertIn("- [x] AC1: the importer writes six rows", text)
        self.assertIn("CHECK: pytest -q tests/test_import.py", text)
        self.assertIn("EXPECT: 1 passed", text)
        self.assertIn("EVIDENCE: exit=0; EXPECT=matched; output-bytes=9", text)

    def test_outside_owns_none_is_copied(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT, REVIEW))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: None", text)

    def test_outside_owns_files_carry_the_spec_axis_judgement(self):
        code, err, text, _ = run_draft((FILES_RUN, VERDICT, REVIEW, DECISIONS))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: src/helper.py (reasonable)", text)

    def test_a_should_not_judgement_is_copied(self):
        review = REVIEW.replace("reasonable", "should not")
        code, err, text, _ = run_draft((FILES_RUN, VERDICT, review, DECISIONS))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: src/helper.py (should not)", text)
        self.assertNotIn("(reasonable)", text)

    def test_a_review_that_names_no_line_for_the_file_invents_no_judgement(self):
        silent = """REVIEW abcdef0..1234567

## Spec

None

## Tests

None
"""
        code, err, text, _ = run_draft((FILES_RUN, VERDICT, silent, DECISIONS))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: src/helper.py", text)
        self.assertNotIn("(reasonable)", text)
        self.assertNotIn("(should not)", text)

    def test_sub_issues_from_the_ticket(self):
        """The line lists every child of this ticket, and none of the spec's other children."""
        ours = "SUB-ISSUE baseline from #77\n\nthe handoff and the spec disagree\n"
        unmarked = "something else entirely\n"
        spec_other = "SUB-ISSUE review from #80\n\nnot this ticket's\n"
        code, err, text, _ = run_draft(
            (MET_RUN, VERDICT),
            child_bodies={90: ours, 91: unmarked, 92: spec_other},
            sub_issues_by_parent={77: (90, 91), 118: (77, 92)},
        )
        self.assertEqual(code, 0, err)
        line = next(l for l in text.splitlines() if l.startswith("Sub-issues opened:"))
        self.assertEqual(line, "Sub-issues opened: #90, #91")
        self.assertNotIn("#92", line)
        self.assertNotIn("#77", line)

    def test_counts_agrees_with_the_body(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertIn("Counts: 1 met, 0 unmet, 0 abandoned of 1", text)

    def test_skipped_and_decisions_are_left_as_fill(self):
        code, err, text, _ = run_draft((MET_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertIn("skipped: <fill>", text)
        self.assertIn("Decisions I made on my own", text)
        self.assertIn("<fill>", text)


class TestCloseoutRefusesTheUnfilledSkeleton(unittest.TestCase):
    def test_closeout_refuses_a_draft_that_still_has_fill(self):
        code, err, text, closeout = run_draft((MET_RUN, VERDICT), check_closeout=True)
        self.assertEqual(code, 0, err)
        self.assertIn("<fill>", text)
        self.assertEqual(closeout, 1)


if __name__ == "__main__":
    unittest.main()
