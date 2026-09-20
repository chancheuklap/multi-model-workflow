"""Ways a criterion is written that gate-lint does not look at.

All of them come from what gate-check actually does with a criterion. It hands the
CHECK's whole output to the EXPECT regex (`gate-check.mjs:586`), it requires exit 0 as
well as a matched EXPECT, and it runs the criteria one at a time in ledger order, each
in its own shell (`gate-check.mjs:638-640`, `--jobs` defaults to 1).
"""

import unittest

from _load import load

vt = load()


def ticket(*criteria):
    return "## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"


def gate(gate_id="AC1", check="pytest -q", expect="/^OK$/m"):
    return (f"- [ ] {gate_id}: something a stranger could judge\n"
            f"  CHECK: {check}\n  EXPECT: {expect}\n  EVIDENCE: pending")


class TestDollarWithoutM(unittest.TestCase):
    def test_a_trailing_dollar_without_the_m_flag_is_an_error(self):
        findings = vt.lint_expectations(ticket(gate(expect="/OK$/")))
        self.assertEqual(len(findings), 1)
        self.assertIn("never matches", findings[0])

    def test_the_finding_spells_out_the_replacement(self):
        findings = vt.lint_expectations(ticket(gate(expect="/OK$/")))
        self.assertIn("/^OK$/m", findings[0])

    def test_the_m_flag_makes_it_fine(self):
        self.assertEqual(vt.lint_expectations(ticket(gate(expect="/^OK$/m"))), [])

    def test_a_regex_with_no_anchor_is_fine(self):
        self.assertEqual(vt.lint_expectations(ticket(gate(expect=r"/\d+ passed/"))), [])

    def test_an_escaped_dollar_is_a_literal_not_an_anchor(self):
        self.assertEqual(vt.lint_expectations(ticket(gate(expect=r"/cost is 5\$/"))), [])

    def test_plain_text_is_matched_as_a_substring_and_never_flagged(self):
        self.assertEqual(vt.lint_expectations(ticket(gate(expect="PARITY OK 4/4"))), [])

    def test_every_criterion_is_reported_by_its_own_id(self):
        findings = vt.lint_expectations(ticket(
            gate("AC1", expect="/OK$/"), gate("AC2", expect="/^OK$/m"),
            gate("AC3", expect="/passed$/")))
        self.assertEqual([f.split(":")[0] for f in findings], ["AC1", "AC3"])


class TestSharedState(unittest.TestCase):
    def test_switching_branches_is_reported(self):
        findings = vt.lint_check_effects(ticket(gate(check="git checkout -B issue-77 && pytest")))
        self.assertEqual(len(findings), 1)
        self.assertIn("git checkout", findings[0])
        self.assertIn("--reverify", findings[0])

    def test_closing_a_ticket_is_reported(self):
        findings = vt.lint_check_effects(ticket(gate(check="gh issue close 77 --reason completed")))
        self.assertEqual(len(findings), 1)
        self.assertIn("gh issue close", findings[0])

    def test_a_plain_test_run_is_not_reported(self):
        self.assertEqual(vt.lint_check_effects(ticket(gate(check="pytest -q tests/"))), [])

    def test_reading_the_ticket_is_not_reported(self):
        check = "gh issue view 77 --json state --jq .state"
        self.assertEqual(vt.lint_check_effects(ticket(gate(check=check))), [])


class TestUndecidableChecks(unittest.TestCase):
    """The two shapes from #449 AC9 and #472 AC6, each written as the night met it."""

    def test_a_counting_grep_expecting_zero_can_never_pass(self):
        check = r"grep -c 'harness-guard\|harness_guard' tests/test_journey.py"
        findings = vt.lint_undecidable_checks(ticket(gate(check=check, expect="/^0$/m")))
        self.assertEqual(len(findings), 1)
        self.assertIn("grep exits 1", findings[0])

    def test_the_finding_names_the_counting_stage_that_keeps_the_exit_code(self):
        check = r"grep -c 'x' f"
        findings = vt.lint_undecidable_checks(ticket(gate(check=check, expect="/^0$/m")))
        self.assertIn("wc -l", findings[0])

    def test_the_same_count_through_wc_is_fine(self):
        check = "git grep -l -e 'old-name' -- . | wc -l | tr -d ' '"
        self.assertEqual(
            vt.lint_undecidable_checks(ticket(gate(check=check, expect="/^0$/m"))), [])

    def test_a_grep_given_a_zero_exit_of_its_own_is_fine(self):
        check = "grep -c 'x' f || true"
        self.assertEqual(
            vt.lint_undecidable_checks(ticket(gate(check=check, expect="/^0$/m"))), [])

    def test_a_grep_expecting_a_count_it_only_prints_after_selecting_is_fine(self):
        self.assertEqual(
            vt.lint_undecidable_checks(ticket(gate(check="grep -c 'x' f",
                                                   expect="/^3$/m"))), [])

    def test_an_echoed_exit_code_over_discarded_output_is_reported(self):
        check = 'bash tests/run.sh --bogus >/dev/null 2>&1; echo "exit $?"'
        findings = vt.lint_undecidable_checks(
            ticket(gate(check=check, expect="/^exit 2$/m")))
        self.assertEqual(len(findings), 1)
        self.assertIn("failed for another reason", findings[0])

    def test_keeping_the_output_and_requiring_the_line_is_fine(self):
        check = ('out="$(bash tests/run.sh --bogus 2>&1)"; code=$?; '
                 "printf '%s\\n' \"$out\" | grep -q '^usage: ' && echo \"usage exit $code\"")
        self.assertEqual(
            vt.lint_undecidable_checks(ticket(gate(check=check, expect="/^usage exit 2$/m"))),
            [])

    def test_discarding_output_without_echoing_the_exit_code_is_fine(self):
        check = "cmd >/dev/null 2>&1; echo done"
        self.assertEqual(
            vt.lint_undecidable_checks(ticket(gate(check=check, expect="/^done$/m"))), [])

    def test_every_criterion_is_reported_by_its_own_id(self):
        findings = vt.lint_undecidable_checks(ticket(
            gate("AC1", check="pytest -q", expect="/^ok$/m"),
            gate("AC2", check="grep -c 'x' f", expect="/^0$/m")))
        self.assertEqual([f.split(":")[0] for f in findings], ["AC2"])


class TestFinalStage(unittest.TestCase):
    def test_a_separator_inside_a_grep_pattern_is_not_a_separator(self):
        self.assertEqual(vt.final_stage(r"grep -c 'a\|b' f"), r"grep -c 'a\|b' f")

    def test_the_last_pipeline_stage_is_the_one_that_answers(self):
        self.assertEqual(vt.final_stage("git grep -l x | wc -l | tr -d ' '"), "tr -d ' '")

    def test_a_command_with_no_separator_is_its_own_last_stage(self):
        self.assertEqual(vt.final_stage("pytest -q tests/"), "pytest -q tests/")


class TestCriteriaLines(unittest.TestCase):
    def test_a_criterion_without_a_check_reads_as_empty(self):
        body = ticket("- [ ] AC1: the empty state carries the placeholder\n  EVIDENCE: pending")
        self.assertEqual(vt.criteria_lines(body), [("AC1", "", "")])

    def test_the_check_and_expect_are_read_off_their_own_criterion(self):
        body = ticket(gate("AC1", check="a", expect="/^x$/m"),
                      gate("AC2", check="b", expect="/^y$/m"))
        self.assertEqual(vt.criteria_lines(body),
                         [("AC1", "a", "/^x$/m"), ("AC2", "b", "/^y$/m")])


if __name__ == "__main__":
    unittest.main()
