"""The shared-lint entry exits non-zero when one of its checks fails, and this
suite's test process does not keep the worker session's ticket identity.
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
    def test_shared_lints_stop_on_a_failing_check(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "mmw-v2"
            lib = root / "tests" / "lib"
            lib.mkdir(parents=True)
            for name in ENTRY_FILES:
                shutil.copy(LIB / name, lib / name)
            planted = root / "skills"
            planted.mkdir()
            (planted / "names_a_missing_module.py").write_text(
                'helper = "missing_module.py"\n',
                encoding="utf-8",
            )
            completed = subprocess.run(
                ["bash", str(lib / "run_shared_lints.sh")],
                cwd=raw,
                capture_output=True,
                text=True,
            )
        combined = completed.stdout + completed.stderr
        self.assertIn("missing_module.py", completed.stdout, combined)
        self.assertNotIn("skills.txt", combined, combined)
        self.assertNotIn("Traceback", combined, combined)
        self.assertNotEqual(completed.returncode, 0, combined)

    def test_the_suite_runs_without_the_session_identity(self):
        present = [name for name in ("MMW_TICKET", "MMW_BASE_REF") if name in os.environ]
        present.extend(sorted(name for name in os.environ if name.startswith("NMEM_")))
        self.assertEqual(present, [])
