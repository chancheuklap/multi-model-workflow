"""The screen-contract rules: what `--lint` reports under `[screen-contract]`, and the
closeout refusal when the Spec axis reported a `Missing` against a row the draft ignores.
"""

import unittest

from tests._load import load

vt = load()

WIRING = ("uv run ~/.agents/skills/verify-ticket/scripts/wiring-check.py --contract "
          "docs/specs/x/screen-contract.yaml --rows create-project.add-material --cdp "
          "http://127.0.0.1:9229 --impl http://127.0.0.1:5173/ --backend http://127.0.0.1:8794")
PARITY = ("uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --baseline d "
          "--impl http://127.0.0.1:5173/ --scenes empty")


def gate(gate_id, check):
    return (f"- [ ] {gate_id}: something a stranger could judge\n"
            f"  CHECK: {check}\n  EXPECT: /^OK$/m\n  EVIDENCE: pending")


def ticket(read_first, *criteria):
    return ("## Read first\n\n" + read_first + "\n\n## Acceptance criteria\n\n"
            + "\n".join(criteria) + "\n")


ROWS = "- docs/specs/x/screen-contract.yaml rows: create-project.add-material (baseline)"


class TestLintScreenContract(unittest.TestCase):
    def test_an_interface_ticket_without_row_ids_is_an_error(self):
        findings = vt.lint_screen_contract(ticket("- README (baseline)", gate("AC1", PARITY)))
        self.assertEqual(len(findings), 1)
        self.assertIn("names no", findings[0])

    def test_a_row_with_calls_needs_a_wiring_criterion(self):
        findings = vt.lint_screen_contract(ticket(ROWS, gate("AC1", PARITY)))
        self.assertEqual(len(findings), 1)
        self.assertIn("create-project.add-material", findings[0])
        self.assertIn("wiring-check.py", findings[0])

    def test_a_wiring_criterion_naming_the_row_satisfies_it(self):
        findings = vt.lint_screen_contract(ticket(ROWS, gate("AC1", PARITY), gate("AC2", WIRING)))
        self.assertEqual(findings, [])

    def test_a_check_that_stubs_fetch_is_an_error(self):
        stubbed = "pnpm vitest run src/__tests__/live.spec.ts  # vi.stubGlobal('fetch', ...)"
        findings = vt.lint_screen_contract(ticket(ROWS, gate("AC1", WIRING), gate("AC2", stubbed)))
        self.assertEqual(len(findings), 1)
        self.assertIn("AC2", findings[0])

    def test_a_ticket_without_interface_or_rows_has_nothing_to_say(self):
        self.assertEqual(vt.lint_screen_contract(ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))), [])


REVIEW = ("REVIEW abc..def\n\n## Standards\n\nnone\n\n## Spec\n\n### Missing\n\n"
          "1. **create-project.add-material calls nothing.** The button toggles a boolean.\n\n"
          "## Tests\n\nnone\n")
BODY = ticket(ROWS, gate("AC1", WIRING))


class TestReviewProblems(unittest.TestCase):
    def test_a_missing_against_an_owned_row_the_draft_ignores_is_refused(self):
        problems = vt.review_problems("ALL MET\nBranch: x\n", BODY, [REVIEW])
        self.assertEqual(len(problems), 1)
        self.assertIn("create-project.add-material", problems[0])

    def test_naming_the_row_in_the_draft_answers_it(self):
        draft = "ALL MET\nPost-verdict: 1234567 — create-project.add-material wired (review finding)\n"
        self.assertEqual(vt.review_problems(draft, BODY, [REVIEW]), [])

    def test_no_review_no_problem(self):
        self.assertEqual(vt.review_problems("ALL MET\n", BODY, ["self-run\nALL MET (1 met)"]), [])

    def test_a_ticket_without_rows_is_not_held_to_it(self):
        body = ticket("- ADR-0013 (baseline)", gate("AC1", "pytest -q"))
        self.assertEqual(vt.review_problems("ALL MET\n", body, [REVIEW]), [])


if __name__ == "__main__":
    unittest.main()


class TestContractPathInBackticks(unittest.TestCase):
    """A Read first line usually wraps the path in backticks; the contract is still read,
    so a row whose calls are [none] asks for no wiring criterion."""

    def test_backticked_path_is_opened_and_none_rows_need_no_wiring(self):
        import os
        import tempfile
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("pyyaml not importable; the lint then falls back to every row")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "screen-contract.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write("rows:\n- id: a.view\n  calls: [none]\n- id: a.save\n  calls: ['POST /x']\n")
            read_first = f"- `{path} rows: a.view, a.save`（基线）"
            wiring = WIRING.replace("create-project.add-material", "a.save")
            findings = vt.lint_screen_contract(ticket(read_first, gate("AC1", PARITY), gate("AC2", wiring)))
        self.assertEqual(findings, [])
