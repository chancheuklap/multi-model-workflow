"""pixel_diff.py writes evidence images and makes no parity decision."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[2]
          / "skills" / "ui-acceptance" / "scripts" / "pixel_diff.py")


def load():
    spec = importlib.util.spec_from_file_location("pixel_diff", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["pixel_diff"] = module
    spec.loader.exec_module(module)
    return module


vp = load()


class TestPixelDiff(unittest.TestCase):
    def test_a_difference_image_is_written_for_equal_sized_renders(self):
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="pixel-diff-") as td:
            root = Path(td)
            design = root / "design.png"
            product = root / "product.png"
            out = root / "diff.png"
            Image.new("RGB", (8, 8), "white").save(design)
            changed = Image.new("RGB", (8, 8), "white")
            changed.putpixel((3, 4), (255, 0, 0))
            changed.save(product)
            self.assertEqual(vp.pixel_diff(design, product, out), out)
            self.assertTrue(out.is_file())
            self.assertNotEqual(Image.open(out).getpixel((3, 4)), (0, 0, 0))

    def test_a_difference_image_is_written_for_unequal_sized_renders(self):
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="pixel-diff-size-") as td:
            root = Path(td)
            design = root / "design.png"
            product = root / "product.png"
            out = root / "diff.png"
            Image.new("RGB", (8, 8), "white").save(design)
            Image.new("RGB", (10, 6), "white").save(product)
            vp.pixel_diff(design, product, out)
            self.assertEqual(Image.open(out).size, (10, 8))

    def test_command_exits_2_and_names_story_parity(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("story-parity.py", proc.stderr)


if __name__ == "__main__":
    unittest.main()
