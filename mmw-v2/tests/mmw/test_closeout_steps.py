"""Closeout reports untraced playbook steps without changing its result."""

import unittest
from unittest import mock

from _load import AT, checked, event, started
from test_closeout import MET, ME, UNMET, check, counts_line, draft, vt
from test_review import REPORT, run_review


CLAIM = event("ticket.claimed", "Claimed", login=ME, commit="0" * 40)
OWN_RUN = checked("self", [MET], outside_owns=[])
DECISIONS = event("worker.decided", "DECISIONS")
REVIEW = event("reviewer.reported", "REVIEW abcdef0..1234567\n\n## In-ticket\nNone",
               base="abcdef0", head="1234567")
TRACES = (CLAIM, OWN_RUN, DECISIONS, REVIEW)


def traced_draft():
    return (draft(counts=counts_line())
            + "\nAudited against the ticket: every requirement holds in the branch\n"
            + "\nReview findings:\nNone\n\nDecisions I made on my own\nNone\n")


def missing_steps(seen):
    body = seen["posted"][-1][1].split("\n\n<!-- mmw", 1)[0]
    if "\n\nSteps without a trace:\n" not in body:
        return []
    return body.split("\n\nSteps without a trace:\n", 1)[1].splitlines()


class TestCloseoutSteps(unittest.TestCase):
    def test_a_step_without_a_trace_is_listed_and_the_closeout_still_closes(self):
        code, err, seen = check(traced_draft(), comments=(CLAIM, OWN_RUN, REVIEW),
                                check_only=False, commits_since_claim="1")
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["closed"], [77])
        self.assertEqual(missing_steps(seen), ["- Post the decisions"])

    def test_a_skip_line_stands_in_for_a_missing_trace(self):
        text = traced_draft() + "- skip: Post the decisions: no independent choices were needed\n"
        code, err, seen = check(text, comments=(CLAIM, OWN_RUN, REVIEW),
                                check_only=False, commits_since_claim="1")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Steps without a trace:", seen["posted"][-1][1])

    def test_every_trace_present_adds_no_section(self):
        code, err, seen = check(traced_draft(), comments=TRACES,
                                check_only=False, commits_since_claim="1")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Steps without a trace:", seen["posted"][-1][1])

    def test_outside_owns_none_is_the_touched_trace(self):
        for files, expected in (([], []), (["README.md"], ["- Tell the touched tickets"])):
            with self.subTest(files=files), \
                 mock.patch.object(vt.engine, "spec_of", return_value=118), \
                 mock.patch.object(vt, "open_children_owns", return_value=[(78, ["README.md"])]):
                own = checked("self", [MET], outside_owns=files)
                code, err, seen = check(traced_draft(), comments=(CLAIM, own, DECISIONS, REVIEW),
                                        check_only=False, commits_since_claim="1")
                self.assertEqual(code, 0, err)
                self.assertEqual(missing_steps(seen), expected)

    def test_a_touched_sibling_is_the_touched_trace(self):
        own = checked("self", [MET], outside_owns=["README.md"])
        touched = event("worker.touched", "Touched", ticket=78, by=77, files=["README.md"])
        with mock.patch.object(vt.engine, "spec_of", return_value=118), \
             mock.patch.object(vt, "open_children_owns", return_value=[(78, ["README.md"])]):
            code, err, seen = check(traced_draft(), comments=(CLAIM, own, DECISIONS, REVIEW, touched),
                                    check_only=False, commits_since_claim="1")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Steps without a trace:", seen["posted"][-1][1])

    def test_manifest_notes_need_no_answer_in_the_closeout(self):
        report = REPORT.replace("Standards: 0 findings.",
                                "## Manifest notes\n\n"
                                "- Spec [wording] docs/contract.md:1 — revise this sentence — "
                                "source: docs/contract.md\n\nStandards: 0 findings.")
        report += "\nskip: Run the axes: no UI criterion\nprinciple-the-baseline-is-a-contract\n"
        code, err, fake = run_review(report)
        self.assertEqual(code, 0, err)
        review = fake.posted[0][1]
        code, err, seen = check(traced_draft(), comments=(CLAIM, OWN_RUN, DECISIONS, review),
                                check_only=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_only_exact_skips_with_reasons_after_the_decisions_line_count(self):
        cases = (
            ("skip: Post the decisions: explained", "after", []),
            ("  - skip: Post the decisions: explained  ", "after", []),
            ("skip: Post the decisions:   ", "after", ["- Post the decisions"]),
            ("skip: Post the decision: explained", "after", ["- Post the decisions"]),
            ("skip: Post the decisions: explained", "before", ["- Post the decisions"]),
        )
        for line, position, expected in cases:
            with self.subTest(line=line, position=position):
                text = (traced_draft() + line + "\n" if position == "after" else
                        traced_draft().replace("\nDecisions I made on my own",
                                               f"\n{line}\n\nDecisions I made on my own"))
                code, err, seen = check(text, comments=(CLAIM, OWN_RUN, REVIEW),
                                        check_only=False, commits_since_claim="1")
                self.assertEqual(code, 0, err)
                self.assertEqual(missing_steps(seen), expected)

    def test_a_claim_before_the_latest_start_cannot_supply_claim_or_code_traces(self):
        comments = (CLAIM, started(base="main", into="spec-337"), OWN_RUN, DECISIONS, REVIEW)
        code, err, seen = check(traced_draft(), comments=comments,
                                check_only=False, commits_since_claim="1")
        self.assertEqual(code, 0, err)
        self.assertEqual(missing_steps(seen), ["- Claim", "- Write the code"])

    def test_code_needs_a_claim_commit_and_a_positive_git_count(self):
        for claim, count in ((CLAIM, "0"), (CLAIM, ""), (CLAIM, "not a count"),
                             (event("ticket.claimed", "Claimed", login=ME), "1")):
            with self.subTest(claim=claim, count=count):
                code, err, seen = check(traced_draft(), comments=(claim, OWN_RUN, DECISIONS, REVIEW),
                                        check_only=False, commits_since_claim=count)
                self.assertEqual(code, 0, err)
                self.assertEqual(missing_steps(seen), ["- Write the code"])

    def test_unchecked_ownership_does_not_read_siblings_or_supply_a_touched_trace(self):
        for own in (checked("self", [MET], outside_owns_unchecked="main"), None):
            with self.subTest(own=own), \
                 mock.patch.object(vt.engine, "spec_of", side_effect=AssertionError("unexpected parent read")):
                comments = (CLAIM, DECISIONS, REVIEW) + ((own,) if own else ())
                code, err, seen = check(traced_draft(), comments=comments,
                                        check_only=False, commits_since_claim="1")
                self.assertEqual(code, 0, err)
                expected = (["- Read yourself in", "- Integrate and run every criterion"]
                            if own is None else []) + ["- Tell the touched tickets"]
                self.assertEqual(missing_steps(seen), expected)

    def test_only_a_current_notice_by_this_ticket_on_a_covered_sibling_counts(self):
        own = checked("self", [MET], outside_owns=["README.md"])
        notice = event("worker.touched", "Touched", ticket=78, by=77, files=["README.md"])
        cases = ((notice.replace('"by":77', '"by":79'), ["README.md"]),
                 (notice.replace(AT, "2026-09-09T00:00:00Z"), ["README.md"]),
                 (notice, ["src/**"]))
        for touched, globs in cases:
            with self.subTest(touched=touched, globs=globs), \
                 mock.patch.object(vt.engine, "spec_of", return_value=118), \
                 mock.patch.object(vt, "open_children_owns", return_value=[(78, globs)]):
                code, err, seen = check(traced_draft(), comments=(CLAIM, own, DECISIONS, REVIEW, touched),
                                        check_only=False, commits_since_claim="1")
                self.assertEqual(code, 0, err)
                self.assertEqual(missing_steps(seen), ["- Tell the touched tickets"])

    def test_a_tracker_read_failure_is_reported_without_preventing_closeout(self):
        own = checked("self", [MET], outside_owns=["README.md"])
        for error in (vt.engine.TrackerReadError(77, "parent", "tracker unavailable"),
                      vt.engine.SubIssuesUnreadable("tracker unavailable"),
                      vt.engine.ParentUnreadable("tracker unavailable")):
            with self.subTest(error=error), \
                 mock.patch.object(vt.engine, "spec_of", side_effect=error):
                code, err, seen = check(traced_draft(), comments=(CLAIM, own, DECISIONS, REVIEW),
                                        check_only=False, commits_since_claim="1")
                self.assertEqual(code, 0, err)
                self.assertEqual(seen["closed"], [77])
                self.assertEqual(missing_steps(seen), ["- Tell the touched tickets"])
                self.assertIn("parent of #77", err)
                self.assertIn("tracker unavailable", err)

    def test_check_only_and_rejected_drafts_do_not_read_step_traces(self):
        with mock.patch.object(vt.engine, "spec_of", side_effect=AssertionError("unexpected parent read")):
            own = checked("self", [MET], outside_owns=["README.md"])
            for check_only, text, expected_code in ((True, traced_draft(), 0),
                                                     (False, traced_draft() + "<fill>\n", 1)):
                with self.subTest(check_only=check_only):
                    code, err, seen = check(text, comments=(CLAIM, own, DECISIONS, REVIEW),
                                            check_only=check_only, commits_since_claim="1")
                    self.assertEqual(code, expected_code, err)
                    self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_a_deleted_or_empty_audit_line_is_listed_and_an_unfilled_one_is_rejected(self):
        audit = "Audited against the ticket: every requirement holds in the branch"
        for replacement, expected_code in (("", 0), ("Audited against the ticket:   ", 0),
                                           ("Audited against the ticket: <fill>", 1)):
            with self.subTest(replacement=replacement):
                code, err, seen = check(traced_draft().replace(audit, replacement), comments=TRACES,
                                        check_only=False, commits_since_claim="1")
                self.assertEqual(code, expected_code, err)
                if code == 0:
                    self.assertEqual(missing_steps(seen), ["- Audit against the ticket"])
                else:
                    self.assertEqual(seen["closed"], [])

    def test_an_unknown_registered_trace_is_listed(self):
        with mock.patch.dict(vt.locations.STEP_TRACES, {"Additional step": "unknown-trace"}):
            code, err, seen = check(traced_draft(), comments=TRACES,
                                    check_only=False, commits_since_claim="1")
        self.assertEqual(code, 0, err)
        self.assertEqual(missing_steps(seen), ["- Additional step"])

    def test_a_handoff_also_carries_the_missing_steps(self):
        text = draft(criteria=(UNMET,), abandons=("ABANDON: AC2 stuck endpoint unavailable",),
                     counts=counts_line(met=0, abandoned=1))
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["handed"], [77])
        self.assertEqual(missing_steps(seen), ["- Claim", "- Read yourself in", "- Write the code",
                                             "- Integrate and run every criterion", "- Post the decisions",
                                             "- Get reviewed", "- Audit against the ticket",
                                             "- Tell the touched tickets"])


if __name__ == "__main__":
    unittest.main()
