"""self_check.py on the shipped example pages, each edited one way."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "skills" / "diagram-design"
SELF_CHECK = SKILL / "scripts" / "self_check.py"
STATIC = (SKILL / "assets" / "example-architecture.html").read_text(encoding="utf-8")
ANIMATED = (SKILL / "assets" / "example-policy-trace-animated.html").read_text(encoding="utf-8")


def exit_code(source):
    with tempfile.TemporaryDirectory() as scratch:
        page = Path(scratch) / "page.html"
        page.write_text(source, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SELF_CHECK), str(page)], capture_output=True, text=True
        ).returncode


class SelfCheck(unittest.TestCase):
    def test_static_page_with_inline_interaction_script_passes(self):
        page = STATIC.replace(
            "</body>", "<script>document.querySelector('svg').dataset.ready = '1';</script></body>", 1
        )
        self.assertEqual(exit_code(page), 0)

    def test_script_loaded_from_outside_the_file_fails(self):
        page = STATIC.replace("</body>", '<script src="https://cdn.example/app.js"></script></body>', 1)
        self.assertEqual(exit_code(page), 1)

    def test_animated_page_with_a_second_script_fails(self):
        self.assertEqual(exit_code(ANIMATED), 0)
        page = ANIMATED.replace("</body>", "<script>window.extra = 1;</script></body>", 1)
        self.assertEqual(exit_code(page), 1)

    def test_executable_attribute_still_fails(self):
        page = STATIC.replace("<body>", '<body onload="fetch(1)">', 1)
        self.assertEqual(exit_code(page), 1)

    def test_truncated_shell_and_unbalanced_content_fail(self):
        for page in (STATIC.removesuffix('\n').replace('</html>', ''),
                     STATIC.replace('</body>', '<section></body>', 1)):
            with self.subTest(page=page[-80:]):
                self.assertEqual(exit_code(page), 1)
        self.assertEqual(exit_code(STATIC + '\n<!-- source note -->\n'), 0)

    def test_source_links_are_navigation_not_remote_assets(self):
        page = STATIC.replace('</body>', '<a href="https://example.com/source">Source</a></body>', 1)
        self.assertEqual(exit_code(page), 0)
        self.assertEqual(exit_code(page.replace('https://example.com/source', 'javascript:alert(1)')), 1)


if __name__ == "__main__":
    unittest.main()
