"""The verdict line `--lint` prints for one ticket is its last line, and counts every
finding above it.

gate-lint prints `LINT OK` for the criteria it reads, and the screen-contract, worker and
other rules of `verify-ticket.py` report after it. Printed as it came, a ticket read
`LINT OK` and then an `ERROR` under it. `lint_criteria` takes gate-lint's own verdict out
and prints one of its own after the last finding.
"""

import io
import unittest
from contextlib import redirect_stdout

from _load import load

vt = load()

HEAD = "## Parent\n\n#216\n\n## Acceptance criteria\n\n"
CLEAN = (HEAD + "- [ ] AC1: the importer writes six rows\n"
         "  CHECK: node scripts/import.mjs fixtures/valid.json\n"
         "  EXPECT: /^6 rows$/m\n  EVIDENCE: pending\n")
# gate-lint has nothing to say about this criterion; the `$` without `m` is found after it.
DOLLAR = (HEAD + "- [ ] AC1: the importer writes six rows\n"
          "  CHECK: node scripts/import.mjs fixtures/valid.json\n"
          "  EXPECT: /^6 rows$/\n  EVIDENCE: pending\n")
AGENT = ["ready-for-agent", "junior-worker"]


def lint(body, labels=AGENT, **kwargs):
    with redirect_stdout(io.StringIO()) as out:
        code = vt.lint_criteria(301, body, labels, **kwargs)
    return code, out.getvalue().splitlines()


class TestVerdictLine(unittest.TestCase):
    def test_a_clean_ticket_ends_on_lint_ok(self):
        code, lines = lint(CLEAN)
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "#301 LINT OK")

    def test_a_finding_after_gate_lint_turns_the_verdict_and_comes_before_it(self):
        code, lines = lint(DOLLAR)
        self.assertEqual(code, 1)
        self.assertNotIn("LINT OK", "\n".join(lines))
        error = next(i for i, line in enumerate(lines) if "[dollar-without-m]" in line)
        self.assertEqual(lines[-1], "#301 LINT FINDINGS: 1 error(s), 0 warning(s)")
        self.assertLess(error, len(lines) - 1)

    def test_warnings_are_counted_into_the_verdict(self):
        code, lines = lint(CLEAN, labels=["ready-for-agent"])
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "#301 LINT OK (1 warning(s))")

    def test_gate_lint_findings_are_counted_too(self):
        manual = HEAD + "- [ ] AC1: the wording reads well\n  EVIDENCE: pending\n"
        code, lines = lint(manual, labels=["ready-for-agent", "junior-worker", "senior-worker"])
        self.assertEqual(code, 1)
        self.assertTrue(lines[-1].startswith("#301 LINT FINDINGS: "), lines[-1])
        errors = int(lines[-1].split(": ")[1].split(" ")[0])
        self.assertGreaterEqual(errors, 2)  # gate-lint's manual-gate, plus the worker label
        self.assertEqual(sum(1 for line in lines if line.startswith("LINT ")), 0)

    def test_a_criteria_less_ticket_ends_on_a_verdict_too(self):
        code, lines = lint("## Parent\n\n#216\n", labels=["mmw:ticket", "ready-for-human"])
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], "#301 LINT OK")

    def test_a_parent_order_finding_is_counted(self):
        body = CLEAN.replace("#216", "#318 Implementation Decisions section 4; #216")
        code, lines = lint(body, spec=216)
        self.assertEqual(code, 1)
        self.assertTrue(any("[parent-order]" in line for line in lines), lines)
        self.assertEqual(lines[-1], "#301 LINT FINDINGS: 1 error(s), 0 warning(s)")


if __name__ == "__main__":
    unittest.main()
