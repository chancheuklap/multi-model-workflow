"""`--draft`: write the closing-comment skeleton, with two `<fill>` placeholders."""

import io
import json
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import checked, event, load, started

vt = load()

ME = "chancheuklap"
VERIFIED = "3f9c2e1adeadbeefcafe0123456789abcdef0123"
HEAD = "9b1d40c7feedface0011223344556677889900aa"


STARTED = started(into="spec-337")
STARTED_BEFORE_SWITCH = started()

BODY = """## Parent

#118, Implementation Decisions section 11

## Acceptance criteria

- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: pending
"""

LEDGER = """- [x] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=9"""


def self_run(ledger, summary, outside_owns=()):
    """The worker's own run of `ledger` as its `ticket.checked` event."""
    abandons = vt.parse_abandons(ledger)
    return checked("self", ledger, summary, outside_owns=list(outside_owns),
                   abandons=abandons or None)


MET_RUN = self_run(LEDGER, "ALL MET (1 met)")

FAILED_RUN = self_run("""- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: exit=1; EXPECT=missed; output-bytes=4
ABANDON: AC1 failed chromium kept crashing; tried the bundled build too""", "UNMET: 1 (met: 0)")

STUCK_RUN = self_run("""- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: pending
ABANDON: AC1 stuck the endpoint it checks does not exist yet""", "UNMET: 1 (met: 0)")

DECISION_RUN = self_run("""- [ ] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: 1 passed
  EVIDENCE: pending
ABANDON: AC1 decision which helper to keep""", "UNMET: 1 (met: 0)")

FILES_RUN = self_run(LEDGER, "ALL MET (1 met)", outside_owns=("src/helper.py",))

# The old run comment, typed by hand. It carries no event, so it is prose.
TYPED_SELF_RUN = ("self-run\nALL MET (1)\n\n" + LEDGER
                  + "\n\nOutside Owns: src/helper.py\n")

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

# The same reports as the scripts post them: each one an event.
REVIEW = event("reviewer.reported", REVIEW, base="abcdef0", head="1234567")
DECISIONS = event("worker.decided", DECISIONS)


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
        if cmd[:3] == ["gh", "api", "graphql"]:
            found = re.search(r"root=(\d+)", " ".join(cmd))
            number = int(found.group(1)) if found else 0
            kids = self.sub_issues if number == 77 else []
            result.stdout = json.dumps({"data": {"repository": {"issue": {
                "number": number, "title": "ticket", "state": "OPEN",
                "subIssuesSummary": {"total": len(kids), "completed": 0},
                "subIssues": {"nodes": [{"number": k, "title": f"child {k}",
                                         "state": "OPEN"} for k in kids]}}}}})
            return result
        if cmd[:3] == ["gh", "api", "user"]:
            result.stdout = ME + "\n"
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result


def run_draft(comments, body=BODY, sub_issues=(), started_event=STARTED):
    """Write a skeleton for ticket 77 to a named file; return (exit, stderr, text, fake)."""
    with TemporaryDirectory() as tmp:
        code, _, err, text, _, fake = draft_run(
            comments, Path(tmp) / "draft.md", body=body, sub_issues=sub_issues,
            started_event=started_event)
        return code, err, text, fake


def draft_run(comments, out_file, body=BODY, sub_issues=(), started_event=STARTED):
    """One `--draft` run for ticket 77, with `out_file` as its path argument (None asks
    the run to pick one); return (exit, stdout, stderr, text, path written, fake)."""
    starts = started_event if isinstance(started_event, tuple) else (started_event,)
    fake = FakeGh((*starts, *comments), body=body, sub_issues=sub_issues)
    with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = vt.run_draft(77, out_file)
    printed = out.getvalue()
    found = re.search(r"^DRAFT: wrote (.+)$", printed, flags=re.M)
    path = Path(found.group(1)) if found else out_file
    text = path.read_text(encoding="utf-8") if path and path.is_file() else ""
    return code, printed, err.getvalue(), text, path, fake


class TestWhereTheDraftLands(unittest.TestCase):
    """The skeleton names every path and file name the ticket names — that is what a
    closing comment says — and `--closeout` runs the repository's own `checks` over the
    tree straight after. A draft written into the repository is content those checks read:
    agentflow-hq/agentflow #831 was held open by a guard that found two reference file
    names in `.mmw/closeout-831.md`, the draft it had just written. So a run given no path
    picks one outside every repository and prints it."""

    def test_no_path_writes_outside_the_repository_and_prints_where(self):
        code, out, err, text, path, _ = draft_run((MET_RUN,), None)
        self.addCleanup(shutil.rmtree, path.parent, ignore_errors=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")
        self.assertIn(f"DRAFT: wrote {path}", out)
        resolved = path.resolve()
        self.assertIn(Path(tempfile.gettempdir()).resolve(), resolved.parents)
        self.assertNotIn(Path.cwd().resolve(), resolved.parents)

    def test_a_path_given_is_the_path_written(self):
        with TemporaryDirectory() as tmp:
            asked = Path(tmp) / "mine" / "closeout-77.md"
            code, out, err, text, path, _ = draft_run((MET_RUN,), asked)
            self.assertEqual(code, 0, err)
            self.assertEqual(path, asked)
            self.assertEqual(text.splitlines()[0], "ALL MET")

    def test_a_refused_run_makes_no_file_anywhere(self):
        code, out, err, text, path, _ = draft_run(
            (MET_RUN,), None, started_event=STARTED_BEFORE_SWITCH)
        self.assertNotEqual(code, 0)
        self.assertEqual(out, "")
        self.assertIn("newest worker.started carries no `into`", err)


class TestFirstLine(unittest.TestCase):
    def test_all_met_when_the_self_run_has_no_failed_or_stuck_abandon(self):
        code, err, text, _ = run_draft((MET_RUN,))
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")

    def test_handoff_when_the_self_run_abandons_as_failed(self):
        code, err, text, _ = run_draft((FAILED_RUN,))
        self.assertEqual(code, 0, err)
        first = text.splitlines()[0]
        self.assertTrue(first.startswith("HANDOFF REQUIRED:"), first)
        self.assertIn("abandoned (failed)", first)
        self.assertIn("0 unmet", first)
        self.assertIn("0 met of 1", first)

    def test_handoff_when_the_self_run_abandons_as_stuck(self):
        code, err, text, _ = run_draft((STUCK_RUN,))
        self.assertEqual(code, 0, err)
        first = text.splitlines()[0]
        self.assertTrue(first.startswith("HANDOFF REQUIRED:"), first)
        self.assertIn("abandoned (stuck)", first)

    def test_all_met_when_the_self_run_abandons_as_decision(self):
        code, err, text, _ = run_draft((DECISION_RUN,))
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")
        self.assertIn("ABANDON: AC1 decision", text)


class TestOnlyTheRunsEventIsRead(unittest.TestCase):
    def test_a_typed_self_run_comment_is_not_a_run(self):
        """A comment whose first line is `self-run` and that carries no event is prose:
        the skeleton takes its ticks and its Outside Owns from nothing."""
        code, err, text, _ = run_draft((TYPED_SELF_RUN,))
        self.assertEqual(code, 0, err)
        self.assertIn("- [ ] AC1: the importer writes six rows", text)
        self.assertIn("EVIDENCE: pending", text)
        self.assertIn("Outside Owns: None", text)

    def test_the_newest_self_run_is_the_one_read(self):
        code, err, text, _ = run_draft((FILES_RUN, MET_RUN))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: None", text)


class TestFixedLines(unittest.TestCase):
    def test_draft_names_into_from_worker_started(self):
        code, err, text, _ = run_draft(
            (MET_RUN,), started_event=(started(into="main"), STARTED))
        self.assertEqual(code, 0, err)
        self.assertIn(
            f"Branch: issue-77 Commit: {HEAD} PR: none — will be merged into "
            "spec-337 by dispatch.sh advance",
            text,
        )

    def test_draft_refuses_a_ticket_started_without_into(self):
        code, err, text, _ = run_draft(
            (MET_RUN,),
            started_event=(started(into="main"), STARTED_BEFORE_SWITCH))
        self.assertNotEqual(code, 0)
        self.assertEqual(text, "")
        self.assertIn("newest worker.started carries no `into`", err)
        self.assertIn("dispatch.sh start 77 worker", err)

    def test_the_draft_carries_no_line_about_commits_after_the_verdict(self):
        """A worker's account of its own commits settled nothing, so the skeleton
        stopped asking for one."""
        code, err, text, _ = run_draft((MET_RUN,))
        self.assertEqual(code, 0, err)
        self.assertNotIn("Post-verdict:", text)

    def test_each_criterion_carries_four_lines_and_the_self_run_evidence(self):
        code, err, text, _ = run_draft((MET_RUN,))
        self.assertEqual(code, 0, err)
        self.assertIn("- [x] AC1: the importer writes six rows", text)
        self.assertIn("CHECK: pytest -q tests/test_import.py", text)
        self.assertIn("EXPECT: 1 passed", text)
        self.assertIn("EVIDENCE: exit=0; EXPECT=matched; output-bytes=9", text)

    def test_outside_owns_none_is_copied(self):
        code, err, text, _ = run_draft((MET_RUN, REVIEW))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: None", text)

    def test_outside_owns_files_carry_the_spec_axis_judgement(self):
        code, err, text, _ = run_draft((FILES_RUN, REVIEW, DECISIONS))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: src/helper.py (reasonable)", text)

    def test_a_should_not_judgement_is_copied(self):
        review = REVIEW.replace("reasonable", "should not")
        code, err, text, _ = run_draft((FILES_RUN, review, DECISIONS))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: src/helper.py (should not)", text)
        self.assertNotIn("(reasonable)", text)

    def test_a_review_that_names_no_line_for_the_file_invents_no_judgement(self):
        silent = event("reviewer.reported", """REVIEW abcdef0..1234567

## Spec

None

## Tests

None
""", base="abcdef0", head="1234567")
        code, err, text, _ = run_draft((FILES_RUN, silent, DECISIONS))
        self.assertEqual(code, 0, err)
        self.assertIn("Outside Owns: src/helper.py", text)
        self.assertNotIn("(reasonable)", text)
        self.assertNotIn("(should not)", text)

    def test_sub_issues_from_the_ticket(self):
        """The line lists every child of this ticket, queried on this ticket's number."""
        code, err, text, fake = run_draft(
            (MET_RUN,),
            sub_issues=(90, 91),
        )
        self.assertEqual(code, 0, err)
        asked = [cmd for cmd in fake.recorded if cmd[:3] == ["gh", "api", "graphql"]]
        self.assertEqual(len(asked), 1)
        self.assertIn("root=77", asked[0])
        line = next(l for l in text.splitlines() if l.startswith("Sub-issues opened:"))
        self.assertEqual(line, "Sub-issues opened: #90, #91")

    def test_counts_agrees_with_the_body(self):
        code, err, text, _ = run_draft((MET_RUN,))
        self.assertEqual(code, 0, err)
        self.assertIn("Counts: 1 met, 0 unmet, 0 abandoned of 1", text)

    def test_skipped_and_decisions_are_left_as_fill(self):
        code, err, text, _ = run_draft((MET_RUN,))
        self.assertEqual(code, 0, err)
        self.assertIn("skipped: <fill>", text)
        self.assertIn("Decisions I made on my own", text)
        self.assertIn("<fill>", text)


class TestFilledDraftPassesCloseoutChecks(unittest.TestCase):
    def test_filling_both_placeholders_leaves_draft_problems_empty(self):
        comments = (MET_RUN,)
        code, err, text, fake = run_draft(comments)
        self.assertEqual(code, 0, err)
        filled = text.replace(vt.FILL, "none")
        self.assertNotIn(vt.FILL, filled)
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            self.assertEqual(vt.draft_problems(filled, list(comments)), [])

    def test_no_final_worker_run_is_named_on_an_all_met_draft(self):
        """A skeleton is well formed on its face while the closing gate still requires
        the worker's final full run."""
        comments = (MET_RUN,)
        code, err, text, fake = run_draft(comments)
        self.assertEqual(code, 0, err)
        self.assertEqual(text.splitlines()[0], "ALL MET")
        filled = text.replace(vt.FILL, "none")
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            self.assertEqual(vt.draft_problems(filled, list(comments)), [])
            problems = vt.verified_problems(filled, "", list(comments))
        self.assertTrue(any("carries no worker reverify `ticket.checked`" in p for p in problems),
                        problems)


class TestCloseoutRefusesTheUnfilledSkeleton(unittest.TestCase):
    def test_closeout_refuses_a_draft_that_still_has_fill(self):
        comments = (MET_RUN,)
        code, err, text, fake = run_draft(comments)
        self.assertEqual(code, 0, err)
        self.assertIn("<fill>", text)
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            problems = vt.draft_problems(text, list(comments))
        self.assertTrue(any("<fill>" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
