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


if __name__ == "__main__":
    unittest.main()
