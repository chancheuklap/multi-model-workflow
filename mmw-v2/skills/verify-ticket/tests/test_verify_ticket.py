"""Ledger behaviour, run against fixed ticket bodies. Never calls the tracker."""

from __future__ import annotations

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

    def run_ticket(self, body: str, reverify: bool = False, previous: list[str] | None = None,
                   comments: list[str] | None = None):
        posted: list[str] = []
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_comments", return_value=comments or []), \
             mock.patch.object(vt, "previous_ledger", return_value=previous or []), \
             mock.patch.object(vt, "outside_owns", return_value=[]), \
             mock.patch.object(vt, "current_branch", return_value="issue-1"), \
             mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_checks(1, reverify, None)
        return code, (posted[0] if posted else ""), out.getvalue()


class TestACheckMaySpanLines(LedgerRun):
    """A CHECK is a shell command; a command longer than a line goes in a fenced block."""

    def test_the_lines_inside_the_fence_are_the_command(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK:",
            "  ```sh",
            "  python3 -c \"",
            "rows = 6",
            "print('wrote', rows, 'rows')\"",
            "  ```",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0, comment)
        self.assertIn("- [x] AC1:", comment)

    def test_the_evidence_lands_after_the_closing_fence(self):
        _, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK:",
            "  ```sh",
            "  python3 -c \"print('wrote 6 rows')\"",
            "  ```",
            "  EXPECT: wrote 6 rows",
        ))
        body = comment.splitlines()
        evidence = next(i for i, l in enumerate(body) if l.strip().startswith("EVIDENCE:"))
        command = next(i for i, l in enumerate(body) if "wrote 6 rows" in l and "print" in l)
        self.assertGreater(evidence, command)

    def test_a_bare_line_under_a_check_says_to_use_a_fence(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: python3 -c \"",
            "print('wrote 6 rows')\"",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 2)
        self.assertEqual(comment, "", "a ledger it could not read is not a result to post")
        self.assertIn("fenced block", printed)


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

    def test_a_criterion_with_no_check_is_never_run_and_never_ticked(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
            "- [ ] AC2: the empty-state copy matches the baseline word for word",
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


class TestMmwTicketInCheckEnv(LedgerRun):
    """The CHECK shell sees the ticket number, not an empty leftover from the host."""

    def test_mmw_ticket_in_check_env(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the check shell sees the ticket number",
            "  CHECK: echo T=$MMW_TICKET",
            "  EXPECT: T=1",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0, comment)
        self.assertIn("- [x] AC1:", comment)


class TestNoRoundCap(LedgerRun):
    """How many rounds a criterion gets is the worker's own judgement: no run names a
    limit, however many self-runs the ticket already carries."""

    FAILING = ("- [ ] AC1: the importer writes six rows\n"
               "  CHECK: echo 'wrote 4 rows'; exit 1\n"
               "  EXPECT: wrote 6 rows\n"
               "  EVIDENCE: pending")

    def prior_runs(self, rounds: int) -> list[str]:
        return ["\n".join(["self-run", "UNMET: 1", "", self.FAILING])] * rounds

    def test_no_run_names_a_limit(self):
        for rounds in (0, 2, 5):
            with self.subTest(rounds=rounds):
                _, comment, _ = self.run_ticket(ticket(self.FAILING),
                                                comments=self.prior_runs(rounds))
                self.assertNotIn("ROUND LIMIT", comment)
                self.assertNotIn("ABANDON", comment)


class TestCheckTimeout(LedgerRun):
    """One number per ticket, read off the ticket body, never lowered."""

    def body(self, *timeouts: str) -> str:
        lines = []
        for i, t in enumerate(timeouts, 1):
            lines += [f"- [ ] AC{i}: thing {i}", f"  CHECK: echo ok{i}", f"  EXPECT: ok{i}",
                      "  EVIDENCE: pending"]
            if t:
                lines.append(f"  TIMEOUT: {t}")
        return ticket(*lines)

    def test_the_default_is_ten_minutes(self):
        self.assertEqual(vt.check_timeout(self.body(""), None), 600)

    def test_a_ticket_raises_it_with_the_largest_timeout_line(self):
        self.assertEqual(vt.check_timeout(self.body("900", "", "1500"), None), 1500)

    def test_a_ticket_cannot_lower_it(self):
        self.assertEqual(vt.check_timeout(self.body("30"), None), 600)

    def test_the_command_line_raises_it_too(self):
        self.assertEqual(vt.check_timeout(self.body("900"), 2000), 2000)
        self.assertEqual(vt.check_timeout(self.body("900"), 100), 900)

    def test_the_ledger_handed_to_gate_check_carries_no_timeout_line(self):
        import tempfile
        from pathlib import Path as P
        with tempfile.TemporaryDirectory() as tmp:
            ledger = vt.write_ledger(self.body("900"), P(tmp))
            text = ledger.read_text(encoding="utf-8")
        self.assertNotIn("TIMEOUT", text)
        self.assertIn("CHECK: echo ok1", text)

    def test_gate_check_is_always_given_the_number(self):
        seen: list[list[str]] = []
        real = vt.subprocess.run

        def spy(cmd, *a, **kw):
            seen.append(list(cmd))
            return real(cmd, *a, **kw)

        with mock.patch.object(vt.subprocess, "run", side_effect=spy):
            code, comment, _ = self.run_ticket(self.body("1200"))
        gate = next(c for c in seen if any(str(x).endswith("gate-check.mjs") for x in c))
        self.assertIn("--timeout", gate)
        self.assertEqual(gate[gate.index("--timeout") + 1], "1200")
        self.assertEqual(code, 0)
        self.assertIn("[x] AC1", comment)

    def test_a_reverify_reads_the_same_number_off_the_body(self):
        seen: list[list[str]] = []
        real = vt.subprocess.run

        def spy(cmd, *a, **kw):
            seen.append(list(cmd))
            return real(cmd, *a, **kw)

        previous = ["- [x] AC1: thing 1", "  CHECK: echo ok1", "  EXPECT: ok1",
                    "  EVIDENCE: exit=0; EXPECT=matched"]
        with mock.patch.object(vt.subprocess, "run", side_effect=spy):
            self.run_ticket(self.body("1200"), reverify=True, previous=previous)
        gate = next(c for c in seen if any(str(x).endswith("gate-check.mjs") for x in c))
        self.assertEqual(gate[gate.index("--timeout") + 1], "1200")

    def test_lint_refuses_a_timeout_that_is_not_seconds(self):
        for bad in ("0", "-5", "ten", "1.5"):
            with self.subTest(value=bad):
                findings = vt.lint_timeouts(self.body(bad))
                self.assertEqual(len(findings), 1)
                self.assertIn("AC1", findings[0])
        self.assertEqual(vt.lint_timeouts(self.body("120")), [])


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
            "  CHECK: false\n"
            "  EXPECT: b\n"
            "  EVIDENCE: pending\n"
            "\n"
            "Outside Owns: None\n"
        )
        self.assertEqual(vt.ledger_from_comment(comment), [
            "- [x] AC1: a", "  CHECK: true", "  EXPECT: a",
            "  EVIDENCE: exit=0; shell=/bin/sh",
            "- [ ] AC2: b", "  CHECK: false", "  EXPECT: b", "  EVIDENCE: pending",
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

    def test_a_weak_expectation_is_reported_without_failing_the_run(self):
        """A warning is for a person to weigh, so it must not decide the exit code."""
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("weak-expect", printed)

    def test_a_ticket_with_no_criteria_section_is_not_a_finding(self):
        """A `ready-for-human` ticket holds one thing to look at, and no criteria."""
        body = "## Parent\n\n#76\n\n## Blocked by\n\n- #96\n"
        with mock.patch.object(vt, "lint_ticket_graph", return_value=0):
            code, printed = self.lint(body)
        self.assertEqual(code, 0)
        self.assertIn("carries no `## Acceptance criteria`", printed)
        self.assertNotIn("zero live gates", printed)

    def test_a_criterion_with_no_command_fails_the_run(self):
        """Nobody but the ticket's own author decides it, which the section forbids."""
        code, printed = self.lint(ticket(
            "- [ ] AC1: the wording reads well",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("manual-gate", printed)
        self.assertIn("ERROR", printed)

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


class TestCarriedLedger(unittest.TestCase):
    """`--reverify` carries the last run's ledger, unless the ticket has been rewritten."""

    BODY = ("## Acceptance criteria\n\n"
            "- [ ] AC1: the importer writes six rows\n"
            "  CHECK: pytest test_importer_v5.py\n"
            "  EXPECT: /^\\d+ passed/m\n"
            "  EVIDENCE: pending\n\n"
            "## Blocked by\n")

    def carried(self, previous):
        with mock.patch.object(vt, "previous_ledger", return_value=previous):
            return vt.carried_ledger(1, self.BODY)

    def test_a_ledger_of_the_same_criteria_is_carried(self):
        same = ["- [x] AC1: the importer writes six rows",
                "  CHECK: pytest test_importer_v5.py",
                "  EXPECT: /^\\d+ passed/m",
                "  EVIDENCE: exit=0; EXPECT=matched"]
        self.assertEqual(self.carried(same), same)

    def test_a_ledger_whose_command_the_ticket_has_rewritten_is_dropped(self):
        """The old command names a file a later decision renamed: the body wins."""
        stale = ["- [x] AC1: the importer writes six rows",
                 "  CHECK: pytest test_importer_v4.py",
                 "  EXPECT: /^\\d+ passed/m",
                 "  EVIDENCE: exit=0; EXPECT=matched"]
        self.assertEqual(self.carried(stale), [])


class TestOutsideOwns(unittest.TestCase):
    """`outside_owns` counts this ticket's own commits, not what a merge rides in."""

    def repo(self, tmp):
        import subprocess

        def sh(*args, **kw):
            subprocess.run(args, cwd=tmp, check=True, capture_output=True, **kw)

        sh("git", "init", "-q", "-b", "main")
        sh("git", "config", "user.email", "t@t")
        sh("git", "config", "user.name", "t")
        (tmp / "base.txt").write_text("base\n")
        sh("git", "add", "-A")
        sh("git", "commit", "-qm", "base")
        return sh

    def test_a_merged_branch_does_not_count_as_this_tickets_work(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            # The earlier ticket's branch commits its own file.
            sh("git", "checkout", "-qb", "issue-2")
            (tmp / "theirs.txt").write_text("theirs\n")
            sh("git", "add", "-A")
            sh("git", "commit", "-qm", "issue-2 work")
            # This ticket's branch commits one file inside Owns, one outside...
            sh("git", "checkout", "-q", "main")
            sh("git", "checkout", "-qb", "issue-4")
            (tmp / "mine.txt").write_text("mine\n")
            (tmp / "stray.txt").write_text("stray\n")
            sh("git", "add", "-A")
            sh("git", "commit", "-qm", "issue-4 work")
            # ...then merges the earlier ticket's branch to build on it.
            sh("git", "merge", "-q", "--no-ff", "-m", "merge issue-2", "issue-2")
            self.assertEqual(vt.outside_owns(["mine.txt"], tmp), ["stray.txt"])

    def test_the_line_is_answered_on_the_tickets_own_branch(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("git", "checkout", "-qb", "issue-4")
            (tmp / "stray.txt").write_text("stray\n")
            sh("git", "add", "-A")
            sh("git", "commit", "-qm", "issue-4 work")
            self.assertEqual(vt.outside_owns_line(4, ["mine.txt"], tmp),
                             "Outside Owns: stray.txt")

    def test_the_line_is_left_unanswered_on_the_branch_tickets_merge_into(self):
        """A re-run there is walking every ticket's commits, which answers nothing."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("git", "checkout", "-qb", "spec-branch")
            (tmp / "stray.txt").write_text("stray\n")
            sh("git", "add", "-A")
            sh("git", "commit", "-qm", "somebody else's work")
            self.assertEqual(
                vt.outside_owns_line(4, ["mine.txt"], tmp),
                "Outside Owns: not checked on spec-branch, which carries more than "
                "this ticket")
