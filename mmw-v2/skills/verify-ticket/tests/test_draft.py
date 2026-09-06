"""`--draft`: write the closing-comment skeleton, with two `<fill>` placeholders."""

import io
import json
import re
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

STUCK_RUN = """self-run
UNMET: 1 (met: 0)

- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: pending
ABANDON: AC1 stuck the endpoint it checks does not exist yet

Outside Owns: None
"""

DECISION_RUN = """self-run
UNMET: 1 (met: 0)

- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: pending
ABANDON: AC1 decision which helper to keep

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


class FakeGh:
    """`gh` by argv, plus the `git` calls `--draft` and `draft_problems` make."""

    def __init__(self, comments, body=BODY, sub_issues=()):
        self.comments = list(comments)
        self.body = body
        self.sub_issues = list(sub_issues)
        self.recorded = []

    def git(self, args):
        if args[:2] == ["rev-parse", "HEAD"]:
            return HEAD
        if args[:1] == ["config"] and args[1].endswith(".mmw-base-branch"):
            return "herdr-to-paseo"
        if args[:1] == ["log"]:
            return HEAD
        if args[:2] == ["rev-parse", "--abbrev-ref"]:
            return "issue-77"
        if args[:2] == ["rev-parse", "--show-toplevel"]:
            return ""
        return ""

    def run(self, cmd, **kwargs):
        self.recorded.append(list(cmd))
        result = mock.Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        if cmd[:1] == ["git"]:
            result.stdout = self.git(cmd[1:])
            return result
        if cmd[:3] == ["gh", "issue", "view"]:
            fields = cmd[cmd.index("--json") + 1] if "--json" in cmd else ""
            if fields == "comments":
                result.stdout = json.dumps(
                    {"comments": [{"body": b} for b in self.comments]})
            elif fields == "body":
                result.stdout = self.body
            else:
                result.stdout = json.dumps({
                    "state": "OPEN", "labels": [],
                    "assignees": [{"login": ME}],
                    "blockedBy": {"nodes": []},
                })
            return result
        if cmd[:2] == ["gh", "api"] and any("sub_issues" in a for a in cmd):
            found = re.search(r"issues/(\d+)/sub_issues", " ".join(cmd))
            number = int(found.group(1)) if found else 0
            kids = self.sub_issues if number == 77 else []
            result.stdout = "\n".join(str(n) for n in kids) + ("\n" if kids else "")
            return result
        if cmd[:3] == ["gh", "api", "user"]:
            result.stdout = ME + "\n"
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result


def run_draft(comments, body=BODY, sub_issues=()):
    """Write a skeleton for ticket 77; return (exit, stderr, text, fake)."""
    fake = FakeGh(comments, body=body, sub_issues=sub_issues)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "draft.md"
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_draft(77, path)
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            return code, err.getvalue(), text, fake


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

    def test_handoff_when_the_self_run_abandons_as_stuck(self):
        code, err, text, _ = run_draft((STUCK_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        first = text.splitlines()[0]
        self.assertTrue(first.startswith("HANDOFF REQUIRED:"), first)
        self.assertIn("abandoned (stuck)", first)

    def test_all_met_when_the_self_run_abandons_as_decision(self):
        code, err, text, _ = run_draft((DECISION_RUN, VERDICT))
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")
        self.assertIn("ABANDON: AC1 decision", text)


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
        """The line lists every child of this ticket, queried on this ticket's number."""
        code, err, text, fake = run_draft(
            (MET_RUN, VERDICT),
            sub_issues=(90, 91),
        )
        self.assertEqual(code, 0, err)
        target = None
        for cmd in fake.recorded:
            if cmd[:2] == ["gh", "api"] and any("sub_issues" in a for a in cmd):
                found = re.search(r"issues/(\d+)/sub_issues", " ".join(cmd))
                target = int(found.group(1)) if found else None
        self.assertEqual(target, 77)
        line = next(l for l in text.splitlines() if l.startswith("Sub-issues opened:"))
        self.assertEqual(line, "Sub-issues opened: #90, #91")

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


class TestFilledDraftPassesCloseoutChecks(unittest.TestCase):
    def test_filling_both_placeholders_leaves_draft_problems_empty(self):
        comments = (MET_RUN, VERDICT)
        code, err, text, fake = run_draft(comments)
        self.assertEqual(code, 0, err)
        filled = text.replace(vt.FILL, "none")
        self.assertNotIn(vt.FILL, filled)
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            self.assertEqual(vt.draft_problems(filled, list(comments)), [])

    def test_no_verdict_is_named_by_draft_problems_on_an_all_met_draft(self):
        comments = (MET_RUN,)
        code, err, text, fake = run_draft(comments)
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")
        self.assertIn("Post-verdict: None", text)
        filled = text.replace(vt.FILL, "none")
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            problems = vt.draft_problems(filled, list(comments))
        self.assertTrue(any("carries no `VERDICT" in p for p in problems), problems)


class TestCloseoutRefusesTheUnfilledSkeleton(unittest.TestCase):
    def test_closeout_refuses_a_draft_that_still_has_fill(self):
        comments = (MET_RUN, VERDICT)
        code, err, text, fake = run_draft(comments)
        self.assertEqual(code, 0, err)
        self.assertIn("<fill>", text)
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            problems = vt.draft_problems(text, list(comments))
        self.assertTrue(any("<fill>" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
