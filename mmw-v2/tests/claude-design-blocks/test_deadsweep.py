"""deadsweep.py: a class only a hand-written page uses survives the sweep.

The seam is a miniature working directory — `src/` with one component source, one
`.dc.html` no source builds (the shape of an app page, or of a page written inside
Claude Design), `mk.py`, the fixtures and one stylesheet.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parents[2] / "skills" / "claude-design-blocks" / "scripts"
)
SCRIPT = SCRIPTS / "deadsweep.py"

SOURCE = '''NAME = "Component · list"
CSS = ["app.css"]
EXTRA_CSS = ""
PROPS = {}
TEMPLATE = """      <section class="list"></section>"""
LOGIC = """        renderVals() { return {}; }"""
'''

HAND_WRITTEN = """<!DOCTYPE html>
<html><body><x-dc>
<main class="board-head"></main>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{}'>
class Component extends DCLogic { renderVals() { return {}; } }
</script></body></html>
"""

CSS = """.list { color: red; }
.board-head { color: green; }
.gone { color: blue; }
"""


class Deadsweep(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name)
        (self.work / "src").mkdir()
        (self.work / "src" / "Component · list.py").write_text(SOURCE, encoding="utf-8")
        (self.work / "App · board.dc.html").write_text(HAND_WRITTEN, encoding="utf-8")
        (self.work / "data").mkdir()
        (self.work / "data" / "fixtures.js").write_text("window.FIXTURES = {};\n", encoding="utf-8")
        shutil.copy(SCRIPTS / "mk.py", self.work / "mk.py")
        self.css = self.work / "app.css"
        self.css.write_text(CSS, encoding="utf-8")
        self.addCleanup(self.tmp.cleanup)

    def sweep(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "src", "data/fixtures.js", "app.css"],
            cwd=self.work,
            capture_output=True,
            text=True,
        )

    def test_a_class_only_a_hand_written_page_uses_survives(self):
        result = self.sweep()
        self.assertEqual(result.returncode, 0, result.stderr)
        css = self.css.read_text(encoding="utf-8")
        self.assertIn(".list", css)
        self.assertIn(".board-head", css)
        self.assertNotIn(".gone", css)

    def test_the_same_class_is_swept_when_no_page_uses_it(self):
        (self.work / "App · board.dc.html").unlink()
        result = self.sweep()
        self.assertEqual(result.returncode, 0, result.stderr)
        css = self.css.read_text(encoding="utf-8")
        self.assertIn(".list", css)
        self.assertNotIn(".board-head", css)


if __name__ == "__main__":
    unittest.main()
