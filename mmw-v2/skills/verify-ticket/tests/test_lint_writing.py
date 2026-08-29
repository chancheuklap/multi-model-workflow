"""Two ways a criterion is written that gate-lint does not look at.

Both come from what gate-check actually does with a criterion. It hands the CHECK's
whole output to the EXPECT regex (`gate-check.mjs:586`), and it runs the criteria one
at a time in ledger order, each in its own shell (`gate-check.mjs:638-640`, `--jobs`
defaults to 1).
"""

import unittest

from tests._load import load

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


class TestCriteriaLines(unittest.TestCase):
    def test_a_criterion_without_a_check_reads_as_empty(self):
        body = ticket("- [ ] AC1: judged by eye\n  MANUAL: 用户 读基线\n  EVIDENCE: pending")
        self.assertEqual(vt.criteria_lines(body), [("AC1", "", "")])

    def test_the_check_and_expect_are_read_off_their_own_criterion(self):
        body = ticket(gate("AC1", check="a", expect="/^x$/m"),
                      gate("AC2", check="b", expect="/^y$/m"))
        self.assertEqual(vt.criteria_lines(body),
                         [("AC1", "a", "/^x$/m"), ("AC2", "b", "/^y$/m")])


if __name__ == "__main__":
    unittest.main()
