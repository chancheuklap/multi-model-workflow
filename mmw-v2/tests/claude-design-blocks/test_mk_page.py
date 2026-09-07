"""mk.py: the generated <script data-dc-script> is valid JavaScript.

The seam is the same miniature handoff package as test_export_scene_data.py:
mk.py writes a page, Node checks the script body, no browser.

MMW_MK_MUTATE=1: mk.py inserts one extra character into the generated
<script data-dc-script> so node --check fails. mk.py reads it.
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MK = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "claude-design-blocks"
    / "scripts"
    / "mk.py"
)
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "handoff"
SRC = Path("src") / "Component · list.py"
PAGE = "Component · list.dc.html"


def script_body(html: str) -> str:
    match = re.search(
        r"<script\b[^>]*\bdata-dc-script\b[^>]*>(.*?)</script>",
        html,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("generated page has no <script data-dc-script>")
    return match.group(1)


class MkPage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.handoff = Path(self.tmp.name) / "h"
        shutil.copytree(FIXTURE, self.handoff)
        self.addCleanup(self.tmp.cleanup)

    def test_generated_script_is_valid_javascript(self):
        if shutil.which("node") is None:
            self.fail("node is not on PATH")
        result = subprocess.run(
            [sys.executable, str(MK), str(self.handoff / SRC)],
            cwd=self.handoff,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        page = self.handoff / PAGE
        self.assertTrue(page.is_file(), result.stdout)
        body = script_body(page.read_text(encoding="utf-8"))
        self.assertIn("STATE_SEED", body)
        self.assertIn("class Component", body)
        script = self.handoff / "generated-script.js"
        script.write_text(body, encoding="utf-8")
        check = subprocess.run(
            ["node", "--check", str(script)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(check.returncode, 0, check.stderr or check.stdout)


if __name__ == "__main__":
    unittest.main()
