"""The closing gate: what a closing comment must say before the ticket may close."""

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

MET = """- [x] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: /\\d+ passed/
  EVIDENCE: 3f9c2e1a; cwd=.; exit=0; matched "6 passed"; 2026-08-29"""

UNMET = """- [ ] AC2: the expiry page says the link is stale
  CHECK: pytest -q tests/test_expiry.py
  EXPECT: 2 passed
  EVIDENCE: exit 1; "1 passed, 1 failed\""""

MANUAL = """- [ ] AC3: the empty state reads 还没有生成任务
  MANUAL: 用户 读本票上 visual-parity 的证据评论
  EVIDENCE: pending"""


def draft(first="ALL MET", criteria=(MET,), abandons=(), counts=None,
          post_verdict="Post-verdict: None", sub_issues="Sub-issues opened: none"):
    """Assemble a closing comment in the shape #60 section 9 step 5 fixes."""
    body = [first, "", "Branch: issue-77  Commit: 9b1d40c7  PR: none", ""]
    if post_verdict is not None:
        body += [post_verdict, ""]
    for i, block in enumerate(criteria):
        body.append(block)
        for line in abandons:
            if line.split()[1] == vt.parse_criteria(block)[0]["id"]:
                body.append(line)
    body += ["", "Outside Owns: None", "", sub_issues]
    if counts is not None:
        body += ["", counts]
    return "\n".join(body) + "\n"


def counts_line(met=1, unmet=0, abandoned=0, manual=0, total=1):
    return f"Counts: {met} met, {unmet} unmet, {abandoned} abandoned, {manual} manual of {total}"


def check(text, comments=(f"VERDICT {VERIFIED} unit-test-verified by opus",),
          verdict_reachable=True, head=HEAD, dirty=(), main_merged=True, diff="src/app.py",
          state="OPEN", assignees=(ME,), check_only=True):
    """Run --closeout against a made-up ticket; return (exit code, stderr, side effects)."""
    seen = {"posted": [], "closed": [], "handed": []}

    def fake_git(*args, cwd=None):
        if args[:2] == ("rev-parse", "HEAD"):
            return head
        if args[0] == "merge-base" and "--is-ancestor" not in args:
            return "0d19a4f3"
        if args[0] == "status":
            return "\n".join(dirty)
        if args[0] == "diff":
            return diff
        return ""

    def fake_is_ancestor(commit, descendant, root=None):
        return main_merged if commit == "main" else verdict_reachable

    ticket = {"state": state, "labels": [], "assignees": [{"login": a} for a in assignees],
              "blockedBy": {"nodes": []}}
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "closeout.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
             mock.patch.object(vt, "fetch_ticket", return_value=ticket), \
             mock.patch.object(vt, "gh_login", return_value=ME), \
             mock.patch.object(vt, "repo_root", return_value=None), \
             mock.patch.object(vt, "report_phase", return_value=False), \
             mock.patch.object(vt, "git", side_effect=fake_git), \
             mock.patch.object(vt, "is_ancestor", side_effect=fake_is_ancestor), \
             mock.patch.object(vt, "dirty_tracked", side_effect=lambda root=None: list(dirty)), \
             mock.patch.object(vt, "post_comment",
                               side_effect=lambda n, b: seen["posted"].append((n, b))), \
             mock.patch.object(vt, "close_ticket",
                               side_effect=lambda n: seen["closed"].append(n)), \
             mock.patch.object(vt, "hand_to_human",
                               side_effect=lambda n: seen["handed"].append(n)):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_closeout(77, path, check_only)
    return code, err.getvalue(), seen


class TestFirstLine(unittest.TestCase):
    def test_a_first_line_in_neither_shape_is_refused(self):
        code, err, _ = check(draft(first="done!", counts=counts_line()))
        self.assertEqual(code, 1)
        self.assertIn("first line is neither", err)

    def test_all_met_over_a_failed_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 failed code-review found it, one fix round did not",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("only `decision` may be abandoned", err)

    def test_all_met_over_a_blocked_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 blocked chromium is not installed; tried …",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        self.assertEqual(check(text)[0], 1)

    def test_all_met_over_an_impossible_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 impossible the API has no such field; see #58",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        self.assertEqual(check(text)[0], 1)

    def test_all_met_over_a_decision_abandon_passes(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 decision both wordings are legal; opened #58",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 0, err)

    def test_a_well_formed_handoff_first_line_passes(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 failed three self-run rounds did not fix it",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 0, err)


class TestBody(unittest.TestCase):
    def test_an_unknown_abandon_kind_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 giveup nothing worked",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("must be one of failed, blocked, impossible, decision", err)

    def test_an_abandon_pointing_at_no_criterion_is_refused(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 1 met of 1",
                     criteria=(MET,), counts=counts_line())
        text += "ABANDON: AC9 failed there is no AC9 on this ticket\n"
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("points at a criterion the draft does not list", err)

    def test_a_tick_with_pending_evidence_is_refused(self):
        ticked_but_empty = MET.replace(
            'EVIDENCE: 3f9c2e1a; cwd=.; exit=0; matched "6 passed"; 2026-08-29',
            "EVIDENCE: pending")
        code, err, _ = check(draft(criteria=(ticked_but_empty,), counts=counts_line(met=0, unmet=1)))
        self.assertEqual(code, 1)
        self.assertIn("is ticked but its EVIDENCE is pending", err)

    def test_counts_that_disagree_with_the_body_are_refused(self):
        code, err, _ = check(draft(criteria=(MET,), counts=counts_line(met=4, total=4)))
        self.assertEqual(code, 1)
        self.assertIn("the draft reads 1 met", err)

    def test_a_missing_counts_line_is_refused(self):
        code, err, _ = check(draft(criteria=(MET,), counts=None))
        self.assertEqual(code, 1)
        self.assertIn("no `Counts:", err)

    def test_a_first_line_that_disagrees_with_counts_is_refused(self):
        text = draft(first="HANDOFF REQUIRED: 2 abandoned (failed), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 failed three rounds did not fix it",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("first line's numbers do not match", err)


class TestVerdict(unittest.TestCase):
    def test_a_ticket_with_no_verdict_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), comments=("self-run\nsomething",))
        self.assertEqual(code, 1)
        self.assertIn("carries no `VERDICT", err)

    def test_a_verdict_commit_no_longer_in_history_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), verdict_reachable=False)
        self.assertEqual(code, 1)
        self.assertIn("reverted or rewritten", err)

    def test_an_ancestor_verdict_passes_when_post_verdict_is_there(self):
        code, err, _ = check(draft(counts=counts_line(),
                                   post_verdict="Post-verdict: 9b1d40c7 (code-review found AC1)"))
        self.assertEqual(code, 0, err)

    def test_an_ancestor_verdict_without_post_verdict_is_refused(self):
        code, err, _ = check(draft(counts=counts_line(), post_verdict=None))
        self.assertEqual(code, 1)
        self.assertIn("add a `Post-verdict:` line", err)

    def test_a_verdict_on_head_needs_no_post_verdict(self):
        code, err, _ = check(draft(counts=counts_line(), post_verdict=None), head=VERIFIED)
        self.assertEqual(code, 0, err)

    def test_the_newest_verdict_is_the_one_checked(self):
        comments = ("VERDICT 0000000deadbeef unit-test-verified by opus",
                    f"VERDICT {VERIFIED} live-ui-verified by opus")
        code, err, _ = check(draft(counts=counts_line()), comments=comments, head=VERIFIED)
        self.assertEqual(code, 0, err)


class TestGit(unittest.TestCase):
    def test_uncommitted_changes_to_tracked_files_are_refused(self):
        code, err, _ = check(draft(counts=counts_line()), dirty=[" M src/app.py"])
        self.assertEqual(code, 1)
        self.assertIn("uncommitted changes", err)

    def test_a_branch_that_does_not_contain_main_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), main_merged=False)
        self.assertEqual(code, 1)
        self.assertIn("does not contain main", err)

    def test_a_branch_that_changed_no_files_only_warns(self):
        code, err, _ = check(draft(counts=counts_line()), diff="")
        self.assertEqual(code, 0)
        self.assertIn("warning: this branch changes no files", err)

    def test_untracked_files_alone_do_not_refuse(self):
        code, err, _ = check(draft(counts=counts_line()), dirty=[])
        self.assertEqual(code, 0, err)


class TestManual(unittest.TestCase):
    def test_an_unfilled_manual_criterion_is_neither_met_nor_unmet(self):
        text = draft(criteria=(MET, MANUAL),
                     sub_issues="Sub-issues opened: #78 (AC3 的空态文案要人看)",
                     counts=counts_line(met=1, manual=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 0, err)

    def test_a_manual_criterion_without_its_sub_issue_is_refused(self):
        text = draft(criteria=(MET, MANUAL), sub_issues="Sub-issues opened: none",
                     counts=counts_line(met=1, manual=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("open one per criterion", err)

    def test_the_manual_count_must_match_the_body(self):
        text = draft(criteria=(MET, MANUAL),
                     sub_issues="Sub-issues opened: #78 (AC3 的空态文案要人看)",
                     counts=counts_line(met=1, unmet=1, manual=0, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("1 manual of 2", err)

    def test_a_filled_manual_criterion_needs_no_sub_issue(self):
        filled = MANUAL.replace("- [ ]", "- [x]").replace(
            "EVIDENCE: pending", "EVIDENCE: 用户读过证据评论，认可; 2026-08-29")
        text = draft(criteria=(MET, filled), counts=counts_line(met=2, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 0, err)


class TestNoSideEffectOnFail(unittest.TestCase):
    """A refused draft leaves the ticket exactly as it was."""

    def test_a_refused_draft_posts_nothing_and_closes_nothing(self):
        text = draft(criteria=(MET,), counts=counts_line(met=9, total=9))
        code, _, seen = check(text, check_only=False)
        self.assertEqual(code, 1)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_check_only_passes_without_touching_the_ticket(self):
        code, err, seen = check(draft(counts=counts_line()), check_only=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_all_met_posts_the_draft_and_closes(self):
        text = draft(counts=counts_line())
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["posted"], [(77, text)])
        self.assertEqual(seen["closed"], [77])
        self.assertEqual(seen["handed"], [])

    def test_handoff_posts_the_draft_and_swaps_the_label(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 failed three self-run rounds did not fix it",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["posted"], [(77, text)])
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [77])

    def test_a_ticket_someone_else_holds_is_refused(self):
        code, err, seen = check(draft(counts=counts_line()), assignees=("someone-else",),
                                check_only=False)
        self.assertEqual(code, 1)
        self.assertIn("not assigned to you", err)
        self.assertEqual(seen["posted"], [])

    def test_an_already_closed_ticket_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), state="CLOSED", check_only=False)
        self.assertEqual(code, 1)
        self.assertIn("already CLOSED", err)


if __name__ == "__main__":
    unittest.main()
