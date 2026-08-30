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
- [ ] AC2: the empty state carries the placeholder line
  CHECK: pytest -q tests/test_empty.py
  EXPECT: 1 passed
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
        self.assertEqual(self.criteria[1]["check"], "pytest -q tests/test_empty.py")
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


class TestBothReadersOpenAFenceTheSameWay(unittest.TestCase):
    """Two readers disagreeing about where a fence opens is the fault this format ends.

    `gates.mjs` does not treat a ``` line as a fence when its info string carries
    another backtick. A reader that did would open a fence there, swallow the criterion
    after it, and report a different count than the engine that ran the checks.
    """

    LEDGER = """- [ ] AC1: the first one
  CHECK: echo one
  EXPECT: one
  EVIDENCE: exit=0
不是围栏，因为反引号后面还有反引号：```` `x` ````
- [ ] AC2: the second one
  CHECK: echo two
  EXPECT: two
  EVIDENCE: exit=0"""

    def test_python_sees_both_criteria(self):
        self.assertEqual([c["id"] for c in vt.parse_criteria(self.LEDGER)], ["AC1", "AC2"])

    def test_the_engine_sees_both_criteria(self):
        import json
        import subprocess
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "AC.md"
            ledger.write_text(self.LEDGER + "\n", encoding="utf-8")
            probe = Path(tmp) / "probe.mjs"
            probe.write_text(
                f"import {{ parseGates }} from {json.dumps(str(vt.GATE_CHECK.parent / 'lib' / 'gates.mjs'))};\n"
                "import fs from 'node:fs';\n"
                f"const r = parseGates(fs.readFileSync({json.dumps(str(ledger))}, 'utf8'));\n"
                "console.log(r.gates.map((g) => g.id).join(','));\n", encoding="utf-8")
            out = subprocess.run(["node", str(probe)], capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "AC1,AC2", out.stderr)


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

    def test_a_fenced_script_is_not_called_a_tautological_check(self):
        """`echo` on line one does not make the whole script a command with fixed output."""
        result = self.run_lint(
            "- [ ] AC1: the install lands in five places\n"
            "  CHECK:\n"
            "  ```sh\n"
            "  echo probing\n"
            "  python3 -c \"import json; print('HOOKS-INSTALLED')\"\n"
            "  ```\n"
            "  EXPECT: HOOKS-INSTALLED\n"
            "  EVIDENCE: pending")
        self.assertNotIn("tautological-check", result.stdout + result.stderr)

    def test_a_script_that_only_prints_is_still_called_one(self):
        result = self.run_lint(
            "- [ ] AC1: nothing is really checked\n"
            "  CHECK:\n"
            "  ```sh\n"
            "  echo ok\n"
            "  printf 'ok\\n'\n"
            "  ```\n"
            "  EXPECT: ok\n"
            "  EVIDENCE: pending")
        self.assertIn("tautological-check", result.stdout + result.stderr)

    def test_a_check_cannot_have_both_a_value_and_a_fence(self):
        result = self.run_lint("- [ ] AC1: rows\n  CHECK: echo six\n  ```sh\n  echo other\n  ```\n"
                               "  EXPECT: six\n  EVIDENCE: pending")
        self.assertIn("one or the other", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
