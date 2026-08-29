"""Where a CHECK ends is written down, not inferred.

A command longer than one line goes in a fenced block under `CHECK:`. Everything in
this file is about the one thing that buys: a criterion's boundary is a delimiter a
reader either sees or does not, instead of a rule each reader has to reproduce.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests._load import load

vt = load()

FENCED = """- [ ] AC1: the queue page counts its tasks
  CHECK:
  ```sh
  cat <<'PROBE'
  - [ ] X1: a line the command prints, not the next criterion

  EVIDENCE: nor is this the criterion's evidence
  PROBE
  echo counted 6
  ```
  EXPECT: counted 6
  EVIDENCE: exit=0; matched "counted 6"
- [ ] AC2: the empty state is judged by eye
  MANUAL: the user reads the baseline scene
  EVIDENCE: pending"""


class TestTheThreeReaders(unittest.TestCase):
    """One parser now, so there is no third reading to get wrong."""

    def setUp(self):
        self.criteria = vt.parse_criteria(FENCED)

    def test_the_fence_holds_one_criterion_not_two(self):
        self.assertEqual([c["id"] for c in self.criteria], ["AC1", "AC2"])

    def test_the_command_is_what_the_fence_held(self):
        command = self.criteria[0]["check"]
        self.assertTrue(command.startswith("cat <<'PROBE'"), command)
        self.assertIn("- [ ] X1:", command)
        self.assertIn("\n\n", command, "a blank line inside the command survives")
        self.assertTrue(command.endswith("echo counted 6"), command)

    def test_the_fence_is_stripped_of_its_own_indentation(self):
        for row in self.criteria[0]["check"].splitlines():
            self.assertFalse(row.startswith("  "), row)

    def test_an_evidence_line_inside_the_fence_is_not_the_evidence(self):
        self.assertEqual(self.criteria[0]["evidence"], 'exit=0; matched "counted 6"')

    def test_the_attributes_after_the_fence_still_attach(self):
        self.assertEqual(self.criteria[0]["expect"], "counted 6")

    def test_the_criterion_after_the_fence_is_read_whole(self):
        self.assertTrue(self.criteria[1]["manual"])
        self.assertEqual(self.criteria[1]["evidence"], "pending")

    def test_count_gates_reads_the_same_ledger(self):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "AC.md"
            ledger.write_text(FENCED.replace("- [ ] AC1:", "- [x] AC1:") + "\n", encoding="utf-8")
            self.assertEqual(vt.count_gates(ledger), (1, 2))

    def test_criteria_lines_reads_the_same_ledger(self):
        body = "## Acceptance criteria\n\n" + FENCED + "\n"
        rows = vt.criteria_lines(body)
        self.assertEqual([row[0] for row in rows], ["AC1", "AC2"])
        self.assertIn("echo counted 6", rows[0][1])
        self.assertEqual(rows[0][2], "counted 6")


class TestOtherFencesAreStillSkipped(unittest.TestCase):
    """A ticket quotes an example criterion; quoting one must not declare one."""

    PROSE = """本票要产出的账本长这样：

```
- [ ] X9: 一条示例标准
  CHECK: echo nope
  EVIDENCE: pending
```

- [ ] AC1: the real one
  CHECK: echo real
  EXPECT: real
  EVIDENCE: pending"""

    def test_a_fence_that_is_not_under_a_check_declares_nothing(self):
        criteria = vt.parse_criteria(self.PROSE)
        self.assertEqual([c["id"] for c in criteria], ["AC1"])
        self.assertEqual(criteria[0]["check"], "echo real")


class TestUnfencedContinuationIsAnError(unittest.TestCase):
    """The implicit rule is gone, and its absence is said out loud."""

    LEDGER = """- [ ] AC1: the importer writes six rows
  CHECK: python3 - <<'EOF'
print("wrote 6 rows")
EOF
  EXPECT: wrote 6 rows
  EVIDENCE: pending"""

    def run_lint(self, text):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "AC.md"
            ledger.write_text(text + "\n", encoding="utf-8")
            import subprocess
            return subprocess.run(
                ["node", str(vt.GATE_LINT), "--strict", str(ledger)],
                capture_output=True, text=True)

    def test_a_bare_line_under_a_check_is_refused(self):
        result = self.run_lint(self.LEDGER)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fenced block", result.stdout + result.stderr)

    def test_a_one_line_check_is_untouched(self):
        """Most commands fit on a line, and nothing about them changed."""
        result = self.run_lint("- [ ] AC1: rows\n  CHECK: echo six\n  EXPECT: six\n"
                               "  EVIDENCE: pending")
        self.assertNotIn("continues its CHECK", result.stdout + result.stderr)
        self.assertNotIn("fenced block", result.stdout + result.stderr)

    def test_a_check_cannot_have_both_a_value_and_a_fence(self):
        result = self.run_lint("- [ ] AC1: rows\n  CHECK: echo six\n  ```sh\n  echo other\n  ```\n"
                               "  EXPECT: six\n  EVIDENCE: pending")
        self.assertIn("one or the other", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
