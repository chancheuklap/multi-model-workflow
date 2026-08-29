"""Everything in `visual-parity.py` that decides an outcome without a browser.

The ARIA fragments are copied from the run recorded in
`prototypes/code-landing/ui-gate/EXP/README.md` under "round-2 — 2026-08-28",
whose trees are written to `.scratch/code-landing/ui-gate/evidence/round-2/media/`
by `prototypes/code-landing/ui-gate/EXP/run.py`.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "visual-parity.py"


def load():
    """`visual-parity.py` is not a Python identifier, and its dataclasses need the
    module to be in `sys.modules` while it executes."""
    spec = importlib.util.spec_from_file_location("visual_parity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["visual_parity"] = module
    spec.loader.exec_module(module)
    return module


vp = load()

# round-2 `baseline-1440x900.aria.yml`, first six lines: the app page wraps the
# imported component, whose own root is a `main`, in a second `main`.
ROUND2_BASELINE_HEAD = """- main:
  - main:
    - text: 变色龙商品图助手 商品项目库
    - status: 服务正常
    - text: 鸭豆余额 12,480
  - tabpanel "商品项目库":
"""

# round-2 `impl-1440x900.aria.yml`, first five lines: the product page labels its
# `<main>`; the component page has no name to give one.
ROUND2_IMPL_HEAD = """- main "变色龙商品项目库原型":
  - text: 变色龙商品图助手 商品项目库
  - status: 服务正常
  - text: 鸭豆余额 12,480
  - tabpanel "商品项目库":
"""

# round-2 `baseline-1440x900.aria.yml`, the first project card.
ROUND2_CARD = """- button "最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08":
  - heading "山野净洗洁精" [level=2]
  - strong: 2 张
"""


def comparison(pixel=None, aria=None, console_baseline=(), console_impl=(),
               scene="default", viewport="1440x900"):
    return vp.Comparison(
        scene, viewport,
        pixel or {"size_equal": True, "pct": 0.0, "count": 0, "total": 100,
                  "box": None, "size_a": (10, 10), "size_b": (10, 10)},
        aria or {"changed": 0, "lines_a": 5, "lines_b": 5, "diff": ""},
        list(console_baseline), list(console_impl))


class TestNormalize(unittest.TestCase):
    def test_drops_generic_and_group_wrappers(self):
        """Rule 1. The round-2 trees carry no bare `- generic` / `- group` line, so
        the two lines under test are inserted into the round-2 card the rule would
        strip them from; every other line is the recorded one."""
        lines = ROUND2_CARD.splitlines()
        with_noise = "\n".join([lines[0], "  - generic", lines[1], "  - group",
                                lines[2]])
        self.assertEqual(vp.normalize_aria(with_noise),
                         vp.normalize_aria(ROUND2_CARD))
        self.assertNotIn("  - generic", vp.normalize_aria(with_noise))
        self.assertNotIn("  - group", vp.normalize_aria(with_noise))

    def test_drops_landmark_name(self):
        """Rule 2."""
        self.assertEqual(vp.normalize_aria(ROUND2_IMPL_HEAD)[0], "- main:")

    def test_hoists_main_nested_in_main(self):
        """Rule 3: the inner `main` goes and its children come up one level, which
        is what makes the two round-2 heads the same tree."""
        self.assertEqual(vp.normalize_aria(ROUND2_BASELINE_HEAD),
                         vp.normalize_aria(ROUND2_IMPL_HEAD))
        self.assertEqual(vp.normalize_aria(ROUND2_BASELINE_HEAD), [
            "- main:",
            "  - text: 变色龙商品图助手 商品项目库",
            "  - status: 服务正常",
            "  - text: 鸭豆余额 12,480",
            '  - tabpanel "商品项目库":',
        ])


class TestAria(unittest.TestCase):
    def test_one_renamed_button_is_a_difference(self):
        renamed = ROUND2_CARD.replace("山野净洗洁精 1 个任务进行中",
                                      "山野净洗洁精 2 个任务进行中", 1)
        self.assertEqual(vp.aria_diff(ROUND2_CARD, ROUND2_CARD)["changed"], 0)
        self.assertEqual(vp.aria_diff(ROUND2_CARD, renamed)["changed"], 2)

    def test_renamed_button_fails_even_with_identical_pixels(self):
        """A name a screen reader reads out is not a pixel; the two checks are not
        the same check, and either one is enough to fail a scene."""
        c = comparison(aria=vp.aria_diff(ROUND2_CARD,
                                         ROUND2_CARD.replace("2 张", "3 张", 1)))
        self.assertEqual(c.pixel["pct"], 0.0)
        reasons = vp.failures(c, max_pct=1.0, console_limit=0)
        self.assertEqual([r.kind for r in reasons], ["aria"])
        self.assertEqual(vp.gate(comparison(aria={"changed": 4, "lines_a": 1,
                                                  "lines_b": 1, "diff": ""}),
                                 [c], 1.0, 0)[0], 1)


class _Render:
    """A screenshot that has been loaded; `diff_images` reads `size` before it reads
    a single pixel."""

    def __init__(self, size):
        self.size = size


class TestSizeMismatch(unittest.TestCase):
    def test_unequal_sizes_never_reach_the_pixels(self):
        result = vp.diff_images(_Render((1440, 900)), _Render((1440, 1180)))
        self.assertFalse(result["size_equal"])
        self.assertEqual(result["pct"], 100.0)
        self.assertIsNone(result["count"])
        self.assertEqual((result["size_a"], result["size_b"]),
                         ((1440, 900), (1440, 1180)))

    def test_unequal_sizes_fail_the_scene(self):
        reasons = vp.failures(comparison(pixel=vp.diff_images(_Render((1440, 900)),
                                                              _Render((1440, 1180)))),
                              max_pct=100.0, console_limit=0)
        self.assertEqual([r.kind for r in reasons], ["size"])


class TestChangeLines(unittest.TestCase):
    """What a failing scene prints under its `DIFF` line: the text that differs, so
    the reader is told what to change rather than sent to compare two pictures."""

    def test_a_renamed_button_prints_both_names(self):
        diff = vp.aria_diff(ROUND2_CARD, ROUND2_CARD.replace("2 张", "3 张", 1))["diff"]
        self.assertEqual(vp.change_lines(diff), [
            "  baseline  strong 2 张",
            "  impl      strong 3 张",
        ])

    def test_a_line_only_one_side_has_says_which_side(self):
        shorter = "\n".join(ROUND2_CARD.splitlines()[:2]) + "\n"
        diff = vp.aria_diff(ROUND2_CARD, shorter)["diff"]
        self.assertEqual(vp.change_lines(diff), ["  only in baseline  strong 2 张"])

    def test_an_identical_tree_prints_nothing(self):
        self.assertEqual(vp.change_lines(vp.aria_diff(ROUND2_CARD, ROUND2_CARD)["diff"]),
                         [])

    def test_the_lines_ride_along_with_the_diff_line(self):
        c = comparison(aria=vp.aria_diff(ROUND2_CARD,
                                         ROUND2_CARD.replace("2 张", "3 张", 1)))
        control = comparison(scene="__negative_control__",
                             pixel={"size_equal": True, "pct": 23.4, "count": 9,
                                    "total": 100, "box": [0, 0, 9, 9],
                                    "size_a": (10, 10), "size_b": (10, 10)},
                             aria={"changed": 28, "lines_a": 30, "lines_b": 2,
                                   "diff": ""})
        code, lines = vp.gate(control, [c], 1.0, 0)
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("DIFF default 1440x900"))
        self.assertEqual(lines[1:], ["  baseline  strong 2 张", "  impl      strong 3 张"])


class TestNegativeControl(unittest.TestCase):
    def test_a_control_that_passed_stops_the_run(self):
        passing_control = comparison(scene="__negative_control__")
        code, lines = vp.gate(passing_control, [comparison()], 1.0, 0)
        self.assertEqual(code, 2)
        self.assertTrue(lines[0].startswith("NEGATIVE CONTROL FAILED"))
        self.assertFalse(any("PARITY" in ln for ln in lines))

    def test_a_control_that_failed_lets_the_scenes_be_read(self):
        caught = comparison(scene="__negative_control__",
                            pixel={"size_equal": True, "pct": 23.4, "count": 9,
                                   "total": 100, "box": [0, 0, 9, 9],
                                   "size_a": (10, 10), "size_b": (10, 10)},
                            aria={"changed": 28, "lines_a": 30, "lines_b": 2,
                                  "diff": ""})
        self.assertEqual(vp.gate(caught, [comparison(), comparison(scene="empty")],
                                 1.0, 0),
                         (0, ["PARITY OK 2/2"]))


class TestConsole(unittest.TestCase):
    def test_an_error_on_the_implementation_fails_the_scene(self):
        message = "error: Uncaught TypeError: wb.tasks is not a function"
        reasons = vp.failures(comparison(console_impl=[message]), max_pct=1.0,
                              console_limit=0)
        self.assertEqual([r.kind for r in reasons], ["console"])
        self.assertIn(message, reasons[0].en)
        self.assertIn(message, reasons[0].zh)

    def test_the_allowance_is_what_console_errors_says(self):
        c = comparison(console_impl=["error: one"])
        self.assertEqual(vp.failures(c, max_pct=1.0, console_limit=1), [])
        self.assertEqual(len(vp.failures(c, max_pct=1.0, console_limit=0)), 1)

    def test_zero_is_the_default(self):
        args = vp.build_parser().parse_args(
            ["--baseline", "b", "--impl", "u", "--scenes", "default"])
        self.assertEqual(args.console_errors, 0)


class TestArguments(unittest.TestCase):
    def test_defaults(self):
        args = vp.build_parser().parse_args(
            ["--baseline", "b", "--impl", "http://x/", "--scenes", "a,b"])
        self.assertEqual(args.max_pct, 1.0)
        self.assertEqual(args.viewports, "1440x900,1180x720")

    def test_viewports_are_read_as_pairs(self):
        self.assertEqual(vp.parse_viewports("1440x900,1180x720"),
                         [(1440, 900), (1180, 720)])
        with self.assertRaises(ValueError):
            vp.parse_viewports("1440*900")

    def test_scene_props_reach_both_sides(self):
        self.assertEqual(vp.impl_url("http://127.0.0.1:8765/index.html",
                                     {"scenario": "queue-empty"}),
                         "http://127.0.0.1:8765/index.html?scenario=queue-empty")
        self.assertIn('scenario="queue-empty"',
                      vp.wrapper_page("Component · 任务队列",
                                      {"scenario": "queue-empty"}))


if __name__ == "__main__":
    unittest.main()
