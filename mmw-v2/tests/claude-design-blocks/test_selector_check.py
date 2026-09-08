"""selector_check.py: which selectors the Claude Design editor can direct-edit.

The rule under test is the one `get_claude_design_prompt` states under Styling —
`.a`, `.a.b`, `.a .b`, pseudo-classes allowed, nothing deeper. Both directions are
checked: a stylesheet written that way exits clean, and each shape that breaks the
rule is named with its reason.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "claude-design-blocks"
    / "scripts"
    / "selector_check.py"
)

CLEAN = """:root { --ink: #222; }
body { margin: 0; }
.card { padding: 8px; }
.card-title { font-size: 18px; }
.tab.on { color: var(--ink); }
.dark .lead { color: #fff; }
.btn:hover { opacity: .9; }
.btn.on::after { content: ""; }
@media (max-width: 600px) { .card { padding: 4px; } }
@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }
"""

BROKEN = """.card header h2 { font-size: 18px; }
.a .b .c { color: red; }
.tab[aria-selected="true"] { color: blue; }
#view { display: grid; }
.a.b.c { color: green; }
"""


class SelectorCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def check(self, css: str) -> subprocess.CompletedProcess:
        path = self.dir / "app.css"
        path.write_text(css, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True
        )

    def test_a_stylesheet_written_to_the_rule_exits_clean(self):
        result = self.check(CLEAN)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("every selector is editor-resolvable", result.stdout)

    def test_each_shape_past_the_rule_is_named_with_its_reason(self):
        result = self.check(BROKEN)
        self.assertEqual(result.returncode, 1, result.stdout)
        out = result.stdout
        self.assertIn("5 selectors the editor cannot reach", out)
        self.assertIn("element in the selector", out)
        self.assertIn("3 levels deep", out)
        self.assertIn("attribute selector", out)
        self.assertIn("id selector", out)
        self.assertIn("more than two classes", out)

    def test_a_keyframe_step_is_not_a_selector(self):
        result = self.check("@keyframes spin { from { opacity: 0; } to { opacity: 1; } }\n")
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
