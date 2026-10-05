"""check_wiring.py on a copy of mmw-v3/skills/ broken one way per case.

    python3 -m unittest discover -s mmw-v3/tests/lib -p 'test_*.py'

Each case breaks one pointer the way an edit would and expects the check to name it;
the first case is the copy as it is, which must pass, so a case that fails is a finding
and not a broken copy.
"""

from __future__ import annotations

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
        root = Path(tmp.name) / "mmw-v3"
        shutil.copytree(MMW / "skills", root / "skills",
                        ignore=shutil.ignore_patterns("__pycache__"))
        for upstream in MMW.glob("upstream-*"):
            (root / upstream.name).symlink_to(upstream)
        self.skills = root / "skills"
        self.mode = self.skills / "mmw-mode" / "SKILL.md"

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECK), str(self.skills)],
                              capture_output=True, text=True)

    def edit(self, path: Path, old: str, new: str):
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(old), 1, old)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def line_with(self, path: Path, needle: str) -> str:
        return next(l for l in path.read_text(encoding="utf-8").splitlines() if needle in l)

    def assertFinds(self, needle: str):
        r = self.run_check()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(needle, r.stdout)

    def test_the_copy_as_it_is_passes(self):
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_playbook_with_no_route_line(self):
        self.edit(self.mode, self.line_with(self.mode, "`playbooks/triage.md`") + "\n", "")
        self.assertFinds("no route line for playbooks/triage.md")

    def test_a_route_line_whose_file_is_gone(self):
        (self.skills / "mmw-mode/playbooks/investigation.md").unlink()
        self.assertFinds("names playbooks/investigation.md, which does not exist")

    def test_a_new_playbook_with_no_route_line(self):
        (self.skills / "mmw-mode/playbooks/new-thing.md").write_text("### New thing\n")
        self.assertFinds("no route line for playbooks/new-thing.md")

    def test_a_route_name_that_is_not_the_title(self):
        self.edit(self.mode, "- **Triage.**", "- **Triage the queue.**")
        self.assertFinds("is titled 'Triage'")

    def test_a_principle_with_no_index_line(self):
        line = self.line_with(self.mode, "(**principle-prove-it-works**)")
        self.edit(self.mode, line + "\n", "")
        self.assertFinds("no index line for principle-prove-it-works")

    def test_a_principle_that_is_gone(self):
        shutil.rmtree(self.skills / "principle-prove-it-works")
        self.assertFinds("names principle-prove-it-works, which is not a skill")

    def test_a_step_naming_a_skill_that_is_not_there(self):
        self.edit(self.skills / "mmw-mode/playbooks/triage.md", "the `triage` skill's `## Show",
                  "the `triaging` skill's `## Show")
        self.assertFinds("names the triaging skill, which is not a skill")

    def test_a_step_naming_a_reference_that_is_not_there(self):
        self.edit(self.skills / "mmw-mode/playbooks/triage.md", "`references/pipeline-issues.md`",
                  "`references/pipeline.md`")
        self.assertFinds("names references/pipeline.md, which is not there")

    def test_a_step_naming_a_script_that_is_not_there(self):
        (self.skills / "write-screen-contract/scripts/extract_skeleton.py").unlink()
        self.assertFinds("names scripts/extract_skeleton.py, which is not there")

    def test_a_dispatch_command_that_is_not_there(self):
        path = self.skills / "mmw-mode/playbooks/run-a-night.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(re.sub(r"dispatch\.sh advance\b", "dispatch.sh progress", text, count=1),
                        encoding="utf-8")
        self.assertFinds("names `dispatch.sh progress`, which dispatch.sh does not have")


if __name__ == "__main__":
    unittest.main()
