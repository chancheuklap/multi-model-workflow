"""Own-script layer for vocab-lint.py: a fixed CONTEXT.md, fixed files, no host."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "vocab-lint.py"
sys.path.insert(0, str(HOOK.parent))
import importlib.util

spec = importlib.util.spec_from_file_location("vocab_lint", HOOK)
vl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vl)

CONTEXT = """# T

## Language

**closing comment**:
The comment a worker leaves.
_Avoid_: 收尾评论, handoff comment, draft (as a term)

**board**:
The night's agent.
_Avoid_: night board, BOARD (as a label)

**worker grade**:
Which worker.
_Avoid_: seat
"""


class LoadAvoid(unittest.TestCase):
    def test_items_without_a_note_only(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "CONTEXT.md"
            c.write_text(CONTEXT, encoding="utf-8")
            self.assertEqual(vl.load_avoid(c), [
                ("收尾评论", "closing comment"), ("handoff comment", "closing comment"),
                ("night board", "board"), ("seat", "worker grade")])


class LintText(unittest.TestCase):
    avoid = [("收尾评论", "closing comment"), ("handoff comment", "closing comment"),
             ("night board", "board"), ("seat", "worker grade")]

    def hits(self, text):
        return [(n, w) for n, w, _ in vl.lint_text(text, self.avoid)]

    def test_whole_word_case_insensitive(self):
        self.assertEqual(self.hits("The Night Board wakes it.\nseat\nseats\n"), [(1, "night board"), (2, "seat")])

    def test_cjk_substring(self):
        self.assertEqual(self.hits("先写收尾评论草稿。"), [(1, "收尾评论")])

    def test_skips_code_and_quotes(self):
        text = "```\nnight board\n```\nsay `night board` here\n上游叫「收尾评论」\n_Avoid_: seat\n"
        self.assertEqual(self.hits(text), [])

    def test_skips_identifiers(self):
        self.assertEqual(self.hits("x=$seat\nseat=1\n{seat}\nseat(1)\nthe seat's\nthe seat is"), [(6, "seat")])

    def test_code_files_search_comments_and_docstrings_only(self):
        text = 'local seat\n# the seat is\n"""\nnight board\n"""\nx = "night board"\n'
        self.assertEqual([(n, w) for n, w, _ in vl.lint_text(text, self.avoid, code=True)],
                         [(2, "seat"), (4, "night board")])


class Files(unittest.TestCase):
    def test_nearest_context_and_skip_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "CONTEXT.md").write_text(CONTEXT, encoding="utf-8")
            (root / "docs" / "adr").mkdir(parents=True)
            (root / "docs" / "adr" / "0001.md").write_text("night board", encoding="utf-8")
            (root / "a").mkdir()
            (root / "a" / "note.md").write_text("the night board\n", encoding="utf-8")
            (root / "a" / "tests").mkdir()
            (root / "a" / "tests" / "t.md").write_text("the night board\n", encoding="utf-8")
            self.assertEqual(vl.lint_file(root / "docs" / "adr" / "0001.md"), [])
            self.assertEqual(vl.lint_file(root / "a" / "tests" / "t.md"), [])
            self.assertEqual(vl.lint_file(root / "a" / "note.md"), [(1, "night board", "board")])

    def test_cli_exit_code_and_hook_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "CONTEXT.md").write_text(CONTEXT, encoding="utf-8")
            f = root / "x.md"
            f.write_text("a handoff comment\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(HOOK), str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("x.md:1: handoff comment -> closing comment", r.stdout)
            payload = json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Write",
                                  "tool_input": {"file_path": str(f)}})
            r = subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            out = json.loads(r.stdout)
            self.assertIn("handoff comment -> closing comment", out["hookSpecificOutput"]["additionalContext"])
            f.write_text("clean\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(HOOK), str(f)], capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
