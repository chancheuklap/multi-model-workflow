"""story-parity.py: the gate without a browser, and the fixture through Chromium.

The gate tests are the shape of `test_visual_parity.py`'s `TestNegativeControl`.
The fixture tests are the seam this ticket is tested at: real Chromium, real
files under `fixtures/story/`.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills" / "drive-target" / "scripts" / "story-parity.py"
)
REPO = Path(__file__).resolve().parent / "fixtures" / "story" / "repo"
CONTRACT = "docs/specs/story/screen-contract.yaml"


def load():
    spec = importlib.util.spec_from_file_location("story_parity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["story_parity"] = module
    spec.loader.exec_module(module)
    return module


sp = load()


def comparison(pixel=None, aria=None, scene="default", viewport="400x300"):
    return sp.Comparison(
        scene, viewport,
        pixel or {"size_equal": True, "pct": 0.0, "pct_unaligned": 0.0,
                  "count": 0, "total": 100, "box": None,
                  "size_a": (10, 10), "size_b": (10, 10)},
        aria or {"changed": 0, "lines_a": 5, "lines_b": 5, "diff": ""},
        [], [], [],
        sp.empty_classes())


class TestParseOrigin(unittest.TestCase):
    def test_origin_equals_form(self):
        self.assertEqual(sp.parse_origin("origin=http://127.0.0.1:21020\n"),
                         "http://127.0.0.1:21020")

    def test_json_form(self):
        self.assertEqual(sp.parse_origin('{"origin": "http://127.0.0.1:9"}\n'),
                         "http://127.0.0.1:9")

    def test_bare_url(self):
        self.assertEqual(sp.parse_origin("http://127.0.0.1:8\n"),
                         "http://127.0.0.1:8")

    def test_empty(self):
        self.assertIsNone(sp.parse_origin(""))
        self.assertIsNone(sp.parse_origin("listening\n"))


class TestArguments(unittest.TestCase):
    def test_defaults(self):
        args = sp.build_parser().parse_args(
            ["--contract", "c.yaml", "--pages", "demo"])
        self.assertEqual(args.max_pct, 3.0)
        self.assertIsNone(args.scenes)
        self.assertFalse(args.render_only)

    def test_pages_is_required(self):
        with self.assertRaises(SystemExit):
            sp.build_parser().parse_args(["--contract", "c.yaml"])


class TestStoryGate(unittest.TestCase):
    """The printed line and the three exit codes, with no browser."""

    def caught(self):
        return comparison(
            scene="__negative_control__",
            pixel={"size_equal": True, "pct": 23.4, "pct_unaligned": 31.0,
                   "count": 9, "total": 100, "box": [0, 0, 9, 9],
                   "size_a": (10, 10), "size_b": (10, 10)},
            aria={"changed": 28, "lines_a": 30, "lines_b": 2, "diff": ""})

    def test_a_control_that_passed_stops_the_run(self):
        code, lines = sp.story_gate(comparison(scene="__negative_control__"),
                                    [comparison()], 1.0, 0)
        self.assertEqual(code, 2)
        self.assertTrue(lines[0].startswith("NEGATIVE CONTROL FAILED"))
        self.assertFalse(any("STORY" in ln for ln in lines))

    def test_a_control_that_failed_lets_the_scenes_be_read(self):
        self.assertEqual(
            sp.story_gate(self.caught(), [comparison(), comparison(scene="empty")],
                          1.0, 0),
            (0, ["STORY OK 2/2 pixel<=0.0%"]))

    def test_the_ok_line_carries_the_worst_pixel_share(self):
        near = comparison(pixel={"size_equal": True, "pct": 1.52,
                                 "pct_unaligned": 4.0, "count": 3,
                                 "total": 200, "box": [0, 0, 9, 9],
                                 "size_a": (10, 10), "size_b": (10, 10)})
        self.assertEqual(
            sp.story_gate(self.caught(), [comparison(), near], 3.0, 0),
            (0, ["STORY OK 2/2 pixel<=1.52%"]))

    def test_a_diff_line_names_unaligned_and_not_the_class_set(self):
        aria = sp.sd.aria_diff("- paragraph: Alpha scene copy\n",
                               "- paragraph: Alpha scene COPY\n")
        c = comparison(aria=aria)
        c.classes = {"only_in_baseline": [("btn", 'button "Continue"')],
                     "only_in_impl": [], "changed": 0}
        code, lines = sp.story_gate(self.caught(), [c], 3.0, 0)
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("DIFF default 400x300 0.0% (unaligned 0.0%)"))
        self.assertIn("aria 2 changed lines", lines[0])
        self.assertNotIn("classes", lines[0])
        self.assertNotIn("class only", "\n".join(lines))
        self.assertEqual(lines[1:], [
            "  baseline  paragraph Alpha scene copy",
            "  impl      paragraph Alpha scene COPY",
        ])

    @unittest.skipUnless(
        __import__("importlib").util.find_spec("numpy") is not None,
        "around ranks a numpy mask; the fixture tests cover the pixel failure")
    def test_a_pixel_failure_uses_the_shared_around(self):
        import numpy as np
        mask = np.zeros((50, 80), dtype=bool)
        mask[5, 10] = True
        c = comparison(
            pixel={"size_equal": True, "pct": 12.5, "pct_unaligned": 31.0,
                   "count": 100, "total": 800, "box": [40, 20, 79, 59],
                   "mask": mask, "scale": 4,
                   "size_a": (10, 10), "size_b": (10, 10)})
        c.impl_elements = [
            {"label": 'heading "Demo card"', "x": 0, "y": 0, "w": 320, "h": 200},
            {"label": 'button "Continue"', "x": 40, "y": 20, "w": 80, "h": 24},
        ]
        code, lines = sp.story_gate(self.caught(), [c], 3.0, 0)
        self.assertEqual(code, 1)
        self.assertIn("pixel 12.5% > 3.0% (unaligned 31.0%)", lines[0])
        self.assertIn("around:", lines[0])


@unittest.skipUnless(shutil.which("uv"), "uv is how the criterion runs this script")
class TestStoryFixture(unittest.TestCase):
    """Real Chromium against the committed fixture. Precedent: TestShrunkPixels."""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="mmw-story-parity-home-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    def run_story(self, extra_env=None, timeout=180):
        env = dict(os.environ)
        env["MMW_HOME"] = self.home
        env["MMW_LEASE_PORT_BASE"] = "28000"
        env.pop("STORY_MUTATE", None)
        if extra_env:
            env.update(extra_env)
        out = tempfile.mkdtemp(prefix="story-out-")
        try:
            return subprocess.run(
                ["uv", "run", "python", str(SCRIPT),
                 "--contract", CONTRACT, "--pages", "demo", "--out", out],
                cwd=REPO, capture_output=True, text=True, env=env, timeout=timeout,
            )
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_three_equal_scenes_print_story_ok(self):
        proc = self.run_story()
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertRegex(proc.stdout, r"^STORY OK 3/3 pixel<=")
        self.assertNotIn("NEGATIVE CONTROL FAILED", proc.stdout)

    def test_a_changed_word_prints_two_tree_lines_and_exits_1(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "copy"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertRegex(proc.stdout, r"(?m)^DIFF .* aria 2 changed lines")
        self.assertRegex(proc.stdout, r"(?m)^  baseline  .+")
        self.assertRegex(proc.stdout, r"(?m)^  impl      .+")

    def test_a_changed_colour_fails_on_pixels(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "color"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertRegex(proc.stdout, r"(?m)^DIFF .* pixel [0-9.]+% > 3\.0%")

    def test_a_mount_the_contract_does_not_declare_exits_2(self):
        env = dict(os.environ)
        env["MMW_HOME"] = self.home
        proc = subprocess.run(
            ["uv", "run", "python", str(SCRIPT),
             "--contract", CONTRACT, "--pages", "no-such-page"],
            cwd=REPO, capture_output=True, text=True, env=env, timeout=60,
        )
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("does not declare", proc.stderr)


if __name__ == "__main__":
    unittest.main()
