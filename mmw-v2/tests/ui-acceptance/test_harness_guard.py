"""harness-guard.py at its command-line and repository-tree seam."""

from __future__ import annotations

import importlib.util
import io
import json
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
        self.err = ""
        self.declare()

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def declare(self, markers=(), *, stories="true", omit_markers=False) -> None:
        cfg = {
            "start": "true",
            "stop": "true",
            "discover": "true",
            "stories": stories,
            "leaves_machine": [],
        }
        if not omit_markers:
            cfg["harness_markers"] = list(markers)
        self.write(".mmw/target.json", json.dumps(cfg) + "\n")

    def guard(self) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = hg.main([str(self.root)])
        self.err = err.getvalue()
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

    def test_a_target_json_without_harness_markers_exits_2_naming_it(self):
        """The refusal names `target_config.py --check`. This test does not load
        that script and does not claim a lease, so it does not set MMW_HOME."""
        self.declare(omit_markers=True)
        code, out = self.guard()
        self.assertEqual(code, 2)
        combined = out + self.err
        self.assertIn("harness_markers", combined)
        self.assertIn("target_config.py --check", combined)
        self.assertIn(f"--repo {self.root}", combined)
        self.assertIn("has no harness_markers", self.err)

    def test_a_missing_target_json_names_that_the_file_is_not_there(self):
        (self.root / ".mmw" / "target.json").unlink()
        code, _ = self.guard()
        self.assertEqual(code, 2)
        self.assertIn(".mmw/target.json is not there", self.err)
        self.assertNotIn("has no harness_markers", self.err)

    def test_unreadable_target_json_names_that_it_cannot_be_read(self):
        self.write(".mmw/target.json", "{bad\n")
        code, _ = self.guard()
        self.assertEqual(code, 2)
        self.assertIn("cannot be read as JSON", self.err)
        self.assertNotIn("has no harness_markers", self.err)

    def test_a_non_list_harness_markers_names_the_shape(self):
        self.declare()
        cfg = json.loads((self.root / ".mmw" / "target.json").read_text(encoding="utf-8"))
        cfg["harness_markers"] = "nope"
        self.write(".mmw/target.json", json.dumps(cfg) + "\n")
        code, _ = self.guard()
        self.assertEqual(code, 2)
        self.assertIn("must be a list of strings", self.err)
        self.assertNotIn("has no harness_markers", self.err)

    def test_a_declared_marker_outside_the_allowed_places_is_a_leak(self):
        self.declare(markers=["__backdoor__"])
        self.write("src/app.js", "const x = '__backdoor__';\n")
        code, text = self.guard()
        self.assertEqual(code, 1)
        self.assertIn("HARNESS LEAK src/app.js:1", text)

    def test_an_old_builtin_marker_not_declared_is_not_a_leak(self):
        self.write("src/app.js", 'console.log("transport off");\n')
        self.assertEqual(self.guard(), (0, "HARNESS OK\n"))

    def test_an_empty_marker_list_still_judges_mmw_reads(self):
        self.write("src/app.js", self.LEAK)
        code, text = self.guard()
        self.assertEqual(code, 1)
        self.assertIn("HARNESS LEAK src/app.js:1", text)

    def test_a_story_service_file_naming_a_dc_html_is_one_line_per_file(self):
        self.write(".mmw/stories/serve.py", 'a = "Foo.dc.html"\nb = "Bar.dc.html"\n')
        self.write(".mmw/stories/other.py", 'c = "Baz.dc.html"\n')
        code, text = self.guard()
        self.assertEqual(code, 1)
        lines = [ln for ln in text.splitlines() if ln.startswith("HARNESS DESIGN PAGE ")]
        self.assertEqual(len(lines), 2, text)
        self.assertIn("HARNESS DESIGN PAGE .mmw/stories/serve.py:1", lines)
        self.assertIn("HARNESS DESIGN PAGE .mmw/stories/other.py:1", lines)
        self.assertNotIn("serve.py:2", text)

    def test_a_file_the_stories_command_names_is_read_as_story_service(self):
        self.declare(stories="python3 src/story_server.py")
        self.write("src/story_server.py", 'open("Demo.dc.html")\n')
        self.write("src/other.py", 'x = "Other.dc.html"\n')
        code, text = self.guard()
        self.assertEqual(code, 1)
        self.assertEqual(text, "HARNESS DESIGN PAGE src/story_server.py:1\n")

    def test_a_root_level_file_the_stories_command_names_is_story_service(self):
        self.declare(stories="node story.mjs")
        self.write("story.mjs", 'import x from "./A.dc.html";\n')
        self.write("src/other.py", 'x = "Other.dc.html"\n')
        code, text = self.guard()
        self.assertEqual(code, 1)
        self.assertEqual(text, "HARNESS DESIGN PAGE story.mjs:1\n")

    def test_a_story_service_reading_scenes_json_only_is_ok(self):
        self.write(".mmw/stories/serve.py", 'scenes = "scenes.json"\n')
        self.assertEqual(self.guard(), (0, "HARNESS OK\n"))


if __name__ == "__main__":
    unittest.main()
