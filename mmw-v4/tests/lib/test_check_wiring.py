"""check_wiring.py on a copy of mmw-v4/skills/ broken one way per case.

    python3 -m unittest discover -s mmw-v4/tests/lib -p 'test_*.py'

Each case breaks one pointer the way an edit would and expects the check to name it;
the first case is the copy as it is, which must pass, so a case that fails is a finding
and not a broken copy.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE / "check_wiring.py"
MMW = HERE.parents[1]


class WiringTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "mmw-v4"
        shutil.copytree(MMW / "skills", root / "skills", symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
        (root.parent / "upstream").symlink_to(MMW.parent / "upstream")
        self.skills = root / "skills"
        self.mode = self.skills / "mmw-mode" / "SKILL.md"
        self.routes = self.skills / "mmw-mode" / "references" / "handling-a-request.md"

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECK), str(self.skills)],
                              capture_output=True, text=True)

    def edit(self, path: Path, old: str, new: str):
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(old), 1, old)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def line_with(self, path: Path, needle: str) -> str:
        return next(l for l in path.read_text(encoding="utf-8").splitlines() if needle in l)

    def assertFinds(self, fact: str):
        """Exit 1, and a finding names this fact (a path or a name)."""
        r = self.run_check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(fact, r.stdout)

    def test_the_copy_as_it_is_passes(self):
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_intent_home_naming_a_missing_step(self):
        path = self.skills / "writing-for-agents/references/DESIGN-INTENTS.md"
        self.edit(path, "**Authoring or modifying a skill**'s **Prove it, once**",
                  "**Authoring or modifying a skill**'s **A step that does not exist**")
        line = next(n for n, text in enumerate(path.read_text().splitlines(), 1)
                    if "A step that does not exist" in text)
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(f"writing-for-agents/references/DESIGN-INTENTS.md:{line}:", result.stdout)
        self.assertIn("A step that does not exist", result.stdout)

    def test_an_upstream_row_naming_a_missing_intent(self):
        path = self.skills / "writing-for-agents/references/UPSTREAM.md"
        path.write_text("| Id | Kind | Intent | Source | MMW |\n"
                        "| --- | --- | --- | --- | --- |\n"
                        "| M1 | written | Align | source | 1, kept (999 examples); 999, adapted (missing) |\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("writing-for-agents/references/UPSTREAM.md:3:", result.stdout)
        self.assertIn("999", result.stdout)

    def test_intent_homes_require_existing_playbooks_skills_and_files(self):
        path = self.skills / "writing-for-agents/references/DESIGN-INTENTS.md"
        original = path.read_text()
        for old, new, finding in (("**Develop a change**", "**Missing playbook**",
                                  "Home names playbook **Missing playbook**"),
                         ("`principle-prove-it-works`", "`principle-missing`",
                          "Home names principle-missing"),
                         ("`scripts/relay.py`", "`scripts/missing.py`",
                          "Home names scripts/missing.py"),
                         ("[`SKILL-SET-COMPONENTS.md`](SKILL-SET-COMPONENTS.md)",
                          "[`MISSING.md`](MISSING.md)", "Home names MISSING.md")):
            with self.subTest(new=new):
                path.write_text(original.replace(old, new))
                self.assertFinds(finding)

    def test_intent_homes_refuse_when_no_home_lines_match(self):
        path = self.skills / "writing-for-agents/references/DESIGN-INTENTS.md"
        path.write_text(path.read_text().replace("Home:", "Destination:"))
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("writing-for-agents/references/DESIGN-INTENTS.md:1: no Home: lines", result.stdout)

    def test_upstream_destinations_refuse_when_no_rows_match(self):
        path = self.skills / "writing-for-agents/references/UPSTREAM.md"
        path.write_text(re.sub(r"^\| ([MP]\d+) \|", r"| `\1` |", path.read_text(), flags=re.M))
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("writing-for-agents/references/UPSTREAM.md:1: no upstream intent rows", result.stdout)

    def test_upstream_entries_use_only_leading_tokens_and_registered_departures(self):
        path = self.skills / "writing-for-agents/references/UPSTREAM.md"
        path.write_text("| Id | Kind | Intent | Source | MMW |\n"
                        "| --- | --- | --- | --- | --- |\n"
                        "| M1 | written | Align | source | 1, kept (999 examples); 2, adapted (999 cases) |\n"
                        "| P12 | written | No plan | source | Departure (owner decides) |\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.edit(path, "| P12 |", "| M2 |")
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("writing-for-agents/references/UPSTREAM.md:4:", result.stdout)
        self.assertIn("M2", result.stdout)

    def test_a_route_line_whose_file_is_gone(self):
        (self.skills / "mmw-mode/playbooks/investigation.md").unlink()
        self.assertFinds("playbooks/investigation.md")

    def test_a_new_playbook_with_no_route_line(self):
        (self.skills / "mmw-mode/playbooks/new-thing.md").write_text("### New thing\n")
        self.assertFinds("playbooks/new-thing.md")

    def test_a_route_name_that_is_not_the_title(self):
        (self.skills / "mmw-mode/playbooks/new-thing.md").write_text("# New thing\n")
        self.edit(self.routes, "## Playbooks\n",
                  "## Playbooks\n\n- **Something else.** Read `playbooks/new-thing.md`.\n")
        self.assertFinds("'New thing'")

    def test_a_principle_with_no_index_line(self):
        line = self.line_with(self.mode, "- **principle-prove-it-works**.")
        self.edit(self.mode, line + "\n", "")
        self.assertFinds("principle-prove-it-works")

    def test_a_principle_that_is_gone(self):
        shutil.rmtree(self.skills / "principle-prove-it-works")
        self.assertFinds("principle-prove-it-works")

    def test_bare_skill_file_ignores_scripts_and_flags(self):
        path = self.skills / "mmw-mode/playbooks/authoring-a-skill.md"
        text = path.read_text(encoding="utf-8")
        for name in ("missing-script.sh", "--lint"):
            with self.subTest(name=name):
                path.write_text(text + f"\nThe command is the `dispatch` skill's `{name}`.\n",
                                encoding="utf-8")
                r = self.run_check()
                self.assertEqual(r.returncode, 0, r.stdout)
                self.assertEqual(r.stdout, "WIRING OK\n")
        path.write_text(text + "\nRead the `dispatch` skill's `missing-file.md`.\n",
                        encoding="utf-8")
        self.assertFinds("dispatch/missing-file.md")

    def test_bare_skill_file_with_a_missing_skill_reports_the_skill(self):
        path = self.skills / "mmw-mode/playbooks/authoring-a-skill.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "\nRead the `tdx` skill's `tests.md`.\n",
                        encoding="utf-8")
        r = self.run_check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("tdx", r.stdout)
        self.assertNotIn("tdx/tests.md", r.stdout)

    def test_a_step_naming_a_script_that_is_not_there(self):
        (self.skills / "mmw-mode/scripts/worktree-audit.sh").unlink()
        self.assertFinds("scripts/worktree-audit.sh")

    def test_a_dispatch_command_that_is_not_there(self):
        path = self.skills / "mmw-mode/playbooks/run-a-night.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nRun `dispatch.sh progress`.\n",
                        encoding="utf-8")
        self.assertFinds("dispatch.sh progress")

    def test_a_step_naming_a_row_that_is_not_there(self):
        path = self.skills / "mmw-mode/playbooks/run-a-night.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "\nSend a subagent on the `writer` row.\n", encoding="utf-8")
        r = self.run_check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(f"mmw-v4/skills/mmw-mode/playbooks/run-a-night.md:{text.count(chr(10)) + 2}:", r.stdout)
        self.assertIn("writer", r.stdout)

    def test_a_row_no_step_names(self):
        path = self.skills / "dispatch/roles.json"
        roles = json.loads(path.read_text(encoding="utf-8"))
        roles["subagents"].append({"name": "unused", "what": "has no dispatch step"})
        path.write_text(json.dumps(roles, indent=2) + "\n", encoding="utf-8")
        r = self.run_check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("unused", r.stdout)
        line = next(n for n, text in enumerate(path.read_text().splitlines(), 1)
                    if '"name": "unused"' in text)
        self.assertIn(f"mmw-v4/skills/dispatch/roles.json:{line}:", r.stdout)


if __name__ == "__main__":
    unittest.main()
