"""mk.py: the generated <script data-dc-script> is valid JavaScript.

The seam is the same miniature handoff package as test_export_scene_data.py:
mk.py writes a page, Node checks the script body, no browser.

MMW_MK_MUTATE=1: this file copies mk.py and deletes one character from the
wrapper (`super(props);` → `super(props;`) so node --check fails. This file
reads it. The standing suite also has a case that always applies that
mutation, so run.sh exercises both directions.
"""

import os
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
EXPORT_JS = MK.with_name("export_scene.js")
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "handoff"
SRC = Path("src") / "Component · list.py"
PAGE = "Component · list.dc.html"
BREAK = ("super(props);", "super(props;")


def script_body(html: str) -> str:
    match = re.search(
        r"<script\b[^>]*\bdata-dc-script\b[^>]*>(.*?)</script>",
        html,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("generated page has no <script data-dc-script>")
    return match.group(1)


def shared_js() -> str:
    text = EXPORT_JS.read_text(encoding="utf-8")
    start, end = "// SHARED_BEGIN\n", "\n// SHARED_END"
    i, j = text.find(start), text.find(end)
    if i < 0 or j < 0:
        raise AssertionError("export_scene.js missing SHARED block")
    block = text[i + len(start) : j]
    if not block.strip():
        raise AssertionError("export_scene.js SHARED block is empty")
    return block


class MkPage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.handoff = Path(self.tmp.name) / "h"
        shutil.copytree(FIXTURE, self.handoff)
        self.scripts = Path(self.tmp.name) / "scripts"
        self.scripts.mkdir()
        shutil.copy(EXPORT_JS, self.scripts / "export_scene.js")
        self.addCleanup(self.tmp.cleanup)

    def write_mk(self, mutate: bool) -> Path:
        text = MK.read_text(encoding="utf-8")
        if mutate:
            broken = text.replace(BREAK[0], BREAK[1], 1)
            if broken == text:
                self.fail(f"mk.py has no {BREAK[0]!r} to break")
            text = broken
        dest = self.scripts / "mk.py"
        dest.write_text(text, encoding="utf-8")
        return dest

    def generate(self, mutate: bool) -> str:
        if shutil.which("node") is None:
            self.fail("node is not on PATH")
        mk = self.write_mk(mutate)
        env = os.environ.copy()
        env.pop("MMW_MK_MUTATE", None)
        result = subprocess.run(
            [sys.executable, str(mk), str(self.handoff / SRC)],
            cwd=self.handoff,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        page = self.handoff / PAGE
        self.assertTrue(page.is_file(), result.stdout)
        return script_body(page.read_text(encoding="utf-8"))

    def check_js(self, body: str) -> subprocess.CompletedProcess:
        script = self.handoff / "generated-script.js"
        script.write_text(body, encoding="utf-8")
        return subprocess.run(
            ["node", "--check", str(script)],
            capture_output=True,
            text=True,
        )

    def test_generated_script_is_valid_javascript(self):
        body = self.generate(mutate=os.environ.get("MMW_MK_MUTATE") == "1")
        self.assertIn(shared_js(), body)
        check = self.check_js(body)
        self.assertEqual(check.returncode, 0, check.stderr or check.stdout)

    def test_a_broken_generator_fails_node_check(self):
        body = self.generate(mutate=True)
        check = self.check_js(body)
        self.assertNotEqual(check.returncode, 0, check.stderr or check.stdout)


if __name__ == "__main__":
    unittest.main()
