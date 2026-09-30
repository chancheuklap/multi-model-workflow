"""The shared-lint entry exits non-zero when any one of its checks fails, and
this suite's test process does not keep the worker session's ticket identity.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib"
ENTRY_FILES = (
    "run_shared_lints.sh",
    "check_module_paths.py",
    "check_upstream_em_dashes.py",
    "check_own_skill_frontmatter.py",
)


class SharedLints(unittest.TestCase):
    def run_copied_entry(self, plant):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "mmw-v2"
            lib = root / "tests" / "lib"
            lib.mkdir(parents=True)
            for name in ENTRY_FILES:
                shutil.copy(LIB / name, lib / name)
            plant(root)
            return subprocess.run(
                ["bash", str(lib / "run_shared_lints.sh")],
                cwd=raw,
                capture_output=True,
                text=True,
            )

    def test_shared_lints_stop_on_a_failing_check(self):
        def plant(root):
            planted = root / "skills"
            planted.mkdir()
            (planted / "names_a_missing_module.py").write_text(
                'helper = "missing_module.py"\n',
                encoding="utf-8",
            )

        completed = self.run_copied_entry(plant)
        combined = completed.stdout + completed.stderr
        self.assertIn("missing_module.py", completed.stdout, combined)
        self.assertNotIn("skills.txt", combined)
        self.assertNotIn("Traceback", combined)
        self.assertNotEqual(completed.returncode, 0, combined)

    def test_shared_lints_stop_on_a_failing_check_em_dash(self):
        def plant(root):
            prose = root / "upstream" / "skills"
            prose.mkdir(parents=True)
            (prose / "prose.md").write_text("one line \u2014 here\n", encoding="utf-8")

        completed = self.run_copied_entry(plant)
        combined = completed.stdout + completed.stderr
        self.assertIn("mmw-v2/upstream/skills/prose.md", combined)
        self.assertNotIn("skills.txt", combined)
        self.assertNotIn("Traceback", combined)
        self.assertNotEqual(completed.returncode, 0, combined)

    def test_shared_lints_stop_on_a_failing_check_frontmatter(self):
        def plant(root):
            (root / "skills.txt").write_text("self/not-a-skill\n", encoding="utf-8")

        completed = self.run_copied_entry(plant)
        combined = completed.stdout + completed.stderr
        self.assertIn("mmw-v2/skills/not-a-skill/SKILL.md", combined)
        self.assertNotEqual(completed.returncode, 0, combined)

    def test_the_suite_runs_without_the_session_identity(self):
        present = [name for name in ("MMW_TICKET", "MMW_BASE_REF") if name in os.environ]
        present.extend(sorted(name for name in os.environ if name.startswith("NMEM_")))
        self.assertEqual(present, [])
