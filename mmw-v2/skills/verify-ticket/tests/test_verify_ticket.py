"""Ledger behaviour, run against fixed ticket bodies. Never calls the tracker."""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests._load import load

vt = load()


def ticket(*criteria: str, owns: str = "- src/**") -> str:
    return "## Owns\n\n" + owns + "\n\n## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"


class LedgerRun(unittest.TestCase):
    """Runs the real gate-check against a fixed body and captures the comment."""

    def run_ticket(self, body: str, reverify: bool = False, previous: list[str] | None = None):
        posted: list[str] = []
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "previous_ledger", return_value=previous or []), \
             mock.patch.object(vt, "outside_owns", return_value=[]), \
             mock.patch.object(vt, "report_phase", return_value=False), \
             mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_checks(1, reverify, None)
        return code, (posted[0] if posted else ""), out.getvalue()


class TestACheckMaySpanLines(LedgerRun):
    """A CHECK is a shell command, and a shell command may be several lines long."""

    def test_the_lines_under_a_check_are_part_of_the_command(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: python3 -c \"",
            "rows = 6",
            "print('wrote', rows, 'rows')\"",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("- [x] AC1:", comment)

    def test_the_evidence_lands_after_the_whole_command(self):
        _, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: python3 -c \"",
            "print('wrote 6 rows')\"",
            "  EXPECT: wrote 6 rows",
        ))
        body = comment.splitlines()
        evidence = next(i for i, l in enumerate(body) if l.strip().startswith("EVIDENCE:"))
        command = next(i for i, l in enumerate(body) if l.strip().startswith("print("))
        self.assertGreater(evidence, command)


class TestDoubleCondition(LedgerRun):
    def test_expected_text_does_not_pass_a_failed_process(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer reports the row count it wrote",
            "  CHECK: echo ok; exit 3",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] AC1:", comment)
        self.assertIn("EVIDENCE: pending", comment)

    def test_exit_zero_with_unmatched_output_does_not_pass(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 5 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] AC1:", comment)

    def test_exit_zero_and_matching_output_passes_with_evidence(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("- [x] AC1:", comment)
        self.assertIn("EVIDENCE: exit=0;", comment)

    def test_a_manual_criterion_is_never_run(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
            "- [ ] AC2: the empty-state copy matches the baseline word for word",
            "  MANUAL: the user reads the baseline scene beside the page",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertNotIn("RUN  AC:AC2", printed)
        self.assertIn("- [ ] AC2:", comment)

    def test_the_comment_carries_the_first_line_and_the_owns_list(self):
        _, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertTrue(comment.startswith("self-run"))
        self.assertIn("Outside Owns: None", comment)


class TestReverify(LedgerRun):
    def test_reverify_reruns_what_the_last_run_ticked(self):
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        )
        previous = [
            "- [x] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: exit=0; shell=/bin/sh; cwd=.; EXPECT=matched",
        ]
        code, comment, printed = self.run_ticket(body, reverify=True, previous=previous)
        self.assertEqual(code, 0)
        self.assertTrue(comment.startswith("reverify"))
        self.assertIn("previously met reverified: 1", printed)


class TestLedgerFromComment(unittest.TestCase):
    def test_a_previous_comment_yields_its_gate_lines_only(self):
        comment = (
            "self-run\n"
            "UNMET: 1 (met: 1)\n"
            "\n"
            "- [x] AC1: a\n"
            "  CHECK: true\n"
            "  EXPECT: a\n"
            "  EVIDENCE: exit=0; shell=/bin/sh\n"
            "- [ ] AC2: b\n"
            "  MANUAL: someone looks\n"
            "  EVIDENCE: pending\n"
            "\n"
            "Outside Owns: None\n"
        )
        self.assertEqual(vt.ledger_from_comment(comment), [
            "- [x] AC1: a", "  CHECK: true", "  EXPECT: a",
            "  EVIDENCE: exit=0; shell=/bin/sh",
            "- [ ] AC2: b", "  MANUAL: someone looks", "  EVIDENCE: pending",
        ])

    def test_a_comment_without_gate_lines_yields_nothing(self):
        self.assertEqual(vt.ledger_from_comment("VERDICT abc unit-test-verified"), [])


class TestOwns(unittest.TestCase):
    def test_globs_drop_the_new_marker_and_the_none_line(self):
        body = "## Owns\n\n- src/import/**\n- src/import/ui/** (new)\n\n## Acceptance criteria\n"
        self.assertEqual(vt.owns_globs(body), ["src/import/**", "src/import/ui/**"])
        self.assertEqual(vt.owns_globs("## Owns\n\n- None\n\n## Blocked by\n"), [])


class TestLint(unittest.TestCase):
    def lint(self, body: str):
        with mock.patch.object(vt, "fetch_body", return_value=body):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_lint(1)
        return code, out.getvalue()

    def test_a_weak_expectation_is_a_strict_finding(self):
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("weak-expect", printed)

    def test_lint_runs_no_check_and_posts_no_comment(self):
        posted: list[str] = []
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo LINT-MUST-NOT-RUN-THIS",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        )
        with mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            _, printed = self.lint(body)
        self.assertNotIn("LINT-MUST-NOT-RUN-THIS\n", printed.replace("CHECK: echo LINT-MUST-NOT-RUN-THIS", ""))
        self.assertEqual(posted, [])

    def test_a_sound_ledger_is_clean(self):
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: /wrote 6 rows/",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("LINT OK", printed)


if __name__ == "__main__":
    unittest.main()
