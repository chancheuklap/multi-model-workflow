"""harness-guard.py at its command-line and repository-tree seam."""

from __future__ import annotations

import importlib.util
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts"
GUARD = SCRIPTS / "harness-guard.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "harness"

spec = importlib.util.spec_from_file_location("mmw_harness_guard", GUARD)
hg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hg)


class HarnessGuard(unittest.TestCase):
    def test_the_leaky_fixture_names_the_leak_and_not_the_legal_hit(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = hg.main([str(FIXTURE / "leaky")])
        self.assertEqual(code, 1)
        text = out.getvalue()
        self.assertRegex(text, r"^HARNESS LEAK ")
        self.assertIn("src/app.js", text)
        self.assertNotIn("src/note.js", text)
        self.assertNotIn("tests/", text)
        self.assertNotIn("scripts/dev/", text)
        self.assertNotIn("tools/opened.py", text)

    def test_a_clean_repo_prints_ok(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = hg.main([str(FIXTURE / "clean")])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "HARNESS OK\n")


class WhatTheGuardReads(unittest.TestCase):
    """What the repository keeps, not what happens to be lying in the directory."""

    LEAK = 'const port = process.env.MMW_PORT_BASE;\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "src").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def guard(self) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = hg.main([str(self.root)])
        return code, out.getvalue()

    def test_a_file_git_ignores_is_not_judged(self):
        """A log the product wrote while the criteria ran, a scratch copy of a ticket.
        Read, they make the same commit green or red by how recently anyone ran the
        product — which is what agentflow #703 and #704 hit on 2026-09-08."""
        self.write(".gitignore", "logs/\n")
        self.write("logs/app.log", self.LEAK)
        self.assertEqual(self.guard(), (0, "HARNESS OK\n"))

    def test_a_file_that_is_there_and_not_committed_yet_is_judged(self):
        """It is the work the ticket is being judged on."""
        self.write("src/app.js", self.LEAK)
        code, text = self.guard()
        self.assertEqual(code, 1)
        self.assertIn("HARNESS LEAK src/app.js:1", text)

    def test_a_test_file_beside_the_code_it_tests_may_read_the_names(self):
        """No release carries it, and `leaves_machine` would say it reaches past this
        machine, which it does not. A repository left with no way to say so writes the
        variable name in pieces to get past the check, and that hides the real leaks."""
        self.write("src/__tests__/support/interact.ts", self.LEAK)
        self.write("src/widget.spec.ts", self.LEAK)
        self.write("src/widget.test.tsx", self.LEAK)
        self.assertEqual(self.guard(), (0, "HARNESS OK\n"))

    def test_the_code_beside_those_tests_is_still_judged(self):
        self.write("src/__tests__/support/interact.ts", self.LEAK)
        self.write("src/widget.ts", self.LEAK)
        code, text = self.guard()
        self.assertEqual(code, 1)
        self.assertIn("src/widget.ts:1", text)
        self.assertNotIn("interact.ts", text)


if __name__ == "__main__":
    unittest.main()
