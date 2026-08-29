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


class TestRegions(unittest.TestCase):
    """A scene can differ in a hundred places; one box around all of them is the whole
    page again, which is what the reader was already looking at."""

    SIZE = (1440, 900)

    def test_places_far_apart_stay_apart(self):
        far = [{"box": [100, 100, 110, 110], "count": 9},
               {"box": [100, 700, 110, 710], "count": 4},
               {"box": [1300, 100, 1310, 110], "count": 1}]
        self.assertEqual(len(vp.merge_regions(far, self.SIZE)), 3)

    def test_places_that_would_show_the_same_picture_become_one(self):
        near = [{"box": [100, 100, 110, 110], "count": 9, "parts": [[100, 100, 110, 110]]},
                {"box": [130, 105, 140, 115], "count": 4, "parts": [[130, 105, 140, 115]]}]
        merged = vp.merge_regions(near, self.SIZE)
        self.assertEqual([(m["box"], m["count"]) for m in merged],
                         [([100, 100, 140, 115], 13)])

    def test_a_merged_place_still_knows_its_separate_blocks(self):
        """The picture is cropped around all of them together, but the ring is drawn
        around each one: a rectangle enclosing two changes several rows apart would
        circle rows that did not change."""
        near = [{"box": [100, 100, 110, 110], "count": 9, "parts": [[100, 100, 110, 110]]},
                {"box": [130, 105, 140, 115], "count": 4, "parts": [[130, 105, 140, 115]]}]
        self.assertEqual(vp.merge_regions(near, self.SIZE)[0]["parts"],
                         [[100, 100, 110, 110], [130, 105, 140, 115]])

    def test_a_merge_that_brings_a_third_into_reach_keeps_going(self):
        """The middle place is read last, so only after it has been folded into the
        left one do the left and right ones reach each other. A single pass stops
        one merge short."""
        out_of_order = [{"box": [100, 100, 110, 110], "count": 1},
                        {"box": [420, 100, 430, 110], "count": 4},
                        {"box": [260, 100, 270, 110], "count": 2}]
        merged = vp.merge_regions(out_of_order, self.SIZE)
        self.assertEqual([(m["box"], m["count"]) for m in merged],
                         [([100, 100, 430, 110], 7)])

    def test_a_place_read_after_a_merge_is_not_dropped(self):
        """The first two places merge; the third is nowhere near them and has to
        survive. Restarting the scan on the merged list alone loses it, and the
        scene silently reports fewer differing pixels than it has."""
        places = [{"box": [10, 10, 20, 20], "count": 1},
                  {"box": [40, 10, 50, 20], "count": 2},
                  {"box": [1200, 800, 1210, 810], "count": 99}]
        merged = vp.merge_regions(places, self.SIZE)
        self.assertEqual(len(merged), 2)
        self.assertEqual(sum(m["count"] for m in merged), 102)

    def test_a_small_place_is_blown_up_and_a_whole_page_is_not(self):
        self.assertGreater(vp.zoom_for(vp.pad_box([122, 129, 133, 140], self.SIZE)), 1)
        self.assertEqual(vp.zoom_for((0, 0, 1440, 900)), 1)

    def test_a_shown_area_never_leaves_the_image(self):
        for box in ([0, 0, 2, 2], [1438, 898, 1439, 899], [700, 400, 701, 401]):
            x0, y0, x1, y1 = vp.pad_box(box, self.SIZE)
            self.assertTrue(0 <= x0 < x1 <= 1440 and 0 <= y0 < y1 <= 900, box)


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
