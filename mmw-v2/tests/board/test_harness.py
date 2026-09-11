from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GH = ROOT / ".mmw" / "harness" / "bin" / "gh"


class HarnessTest(unittest.TestCase):
    def test_fake_gh_reads_exact_fixture_and_records_every_call(self):
        with tempfile.TemporaryDirectory() as data_dir:
            env = {**os.environ, "MMW_DATA_DIR": data_dir}
            known = subprocess.run([str(GH), "api", "test"], env=env, text=True,
                                   capture_output=True)
            self.assertEqual((known.returncode, known.stdout), (0, "fixture-ok\n"))
            missing = subprocess.run([str(GH), "api", "unknown"], env=env, text=True,
                                     capture_output=True)
            self.assertEqual(missing.returncode, 2)
            self.assertIn("no gh response", missing.stderr)
            calls = (Path(data_dir) / "gh-calls").read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls, [
                json.dumps(["api", "test"], separators=(",", ":")),
                json.dumps(["api", "unknown"], separators=(",", ":")),
            ])


if __name__ == "__main__":
    unittest.main()
