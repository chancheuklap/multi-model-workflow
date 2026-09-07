"""Everything in `visual-parity.py` that decides an outcome without a browser.

The ARIA fragments are copied from the run recorded in
`prototypes/code-landing/ui-gate/EXP/README.md` under "round-2 — 2026-08-28",
whose trees are written to `.scratch/code-landing/ui-gate/evidence/round-2/media/`
by `prototypes/code-landing/ui-gate/EXP/run.py`.
"""

import importlib.util
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts" / "visual-parity.py"


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


class TestJoinJs(unittest.TestCase):
    """Two scripts joined must be two statements, not one call on the first."""

    A = "(() => { globalThis.a = 1; })()"
    B = "(() => { globalThis.b = 2; })()"

    def test_two_iifes_run_as_two_statements(self):
        joined = vp._join_js(self.A, self.B)
        node = shutil.which("node")
        if node is None:
            self.skipTest("no node on this machine to parse the joined script")
        run = subprocess.run(
            [node, "-e", f"{joined};\nprocess.stdout.write(`${{globalThis.a}},${{globalThis.b}}`)"],
            capture_output=True, text=True)
        # Joined by a newline alone this is `})()(() => …)()`: a call on what the
        # first IIFE returned, which is how the debt-gate mount crashed the judge.
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, "1,2")

    def test_one_part_is_returned_as_is_and_none_stays_none(self):
        self.assertEqual(vp._join_js(self.A, None), self.A)
        self.assertIsNone(vp._join_js(None, None))


class TestNormalize(unittest.TestCase):
    """The tree is read as the flat sequence of named nodes, in reading order."""

    FLAT_HEAD = [
        "- text: 变色龙商品图助手 商品项目库",
        "- status: 服务正常",
        "- text: 鸭豆余额 12,480",
        '- tabpanel "商品项目库"',
    ]

    def test_drops_unnamed_wrappers(self):
        """The round-2 trees carry no bare wrapper line, so `generic`, `group` and
        `list` are inserted into the round-2 card; every other line is the recorded
        one, and the sequence comes out the same."""
        lines = ROUND2_CARD.splitlines()
        with_noise = "\n".join([lines[0], "  - generic", "  - list:", lines[1],
                                "    - group", "    - listitem:", lines[2]])
        self.assertEqual(vp.normalize_aria(with_noise), vp.normalize_aria(ROUND2_CARD))
        self.assertEqual(vp.normalize_aria(ROUND2_CARD), [
            '- button "最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08"',
            '- heading "山野净洗洁精" [level=2] < button "最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08"',
            '- strong: 2 张 < button "最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08"',
        ])

    def test_drops_landmark_name(self):
        self.assertEqual(vp.normalize_aria(ROUND2_IMPL_HEAD), self.FLAT_HEAD)

    def test_nesting_does_not_matter(self):
        """The app page wraps the component in a second `main`; the product page
        labels its one `main`. Read flat, the two round-2 heads are the same."""
        self.assertEqual(vp.normalize_aria(ROUND2_BASELINE_HEAD),
                         vp.normalize_aria(ROUND2_IMPL_HEAD))
        self.assertEqual(vp.normalize_aria(ROUND2_BASELINE_HEAD), self.FLAT_HEAD)

    def test_a_named_group_and_a_state_stay(self):
        self.assertEqual(vp.normalize_aria('- group "筛选"\n  - checkbox "仅进行中" [checked]\n'
                                           '  - switch [checked]'),
                         ['- group "筛选"', '- checkbox "仅进行中" [checked] < group "筛选"',
                          '- switch [checked] < group "筛选"'])

    def test_the_nearest_named_ancestor_rides_along(self):
        """A button that moved out of its dialog shows on screen, so the tree says
        where each node sits: its closest ancestor that carries a name. Unnamed
        wrappers and landmarks are not ancestors."""
        inside = '- main "页面":\n  - generic:\n    - dialog "确认删除":\n      - list:\n        - button "删除"'
        outside = '- main "页面":\n  - dialog "确认删除":\n    - text: 真的删？\n  - button "删除"'
        self.assertEqual(vp.normalize_aria(inside),
                         ['- dialog "确认删除"', '- button "删除" < dialog "确认删除"'])
        self.assertEqual(vp.normalize_aria(outside),
                         ['- dialog "确认删除"', '- text: 真的删？ < dialog "确认删除"',
                          '- button "删除"'])
        self.assertNotEqual(vp.normalize_aria(inside)[-1], vp.normalize_aria(outside)[-1])


class TestAria(unittest.TestCase):
    def test_one_renamed_button_is_a_difference(self):
        renamed = ROUND2_CARD.replace("山野净洗洁精 1 个任务进行中",
                                      "山野净洗洁精 2 个任务进行中", 1)
        self.assertEqual(vp.aria_diff(ROUND2_CARD, ROUND2_CARD)["changed"], 0)
        # The button's own line and the two lines that name it as their ancestor.
        self.assertEqual(vp.aria_diff(ROUND2_CARD, renamed)["changed"], 6)

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


def _has_imaging() -> bool:
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


@unittest.skipUnless(_has_imaging(), "needs numpy and Pillow: "
                     "uv run --with numpy --with pillow python -m unittest")
class TestShrunkPixels(unittest.TestCase):
    """Pixels are compared after both images are shrunk by `PIXEL_SCALE`. The one
    test here that opens real images; everything else in this file runs on the
    standard library alone."""

    def image(self, paint):
        from PIL import Image

        img = Image.new("RGB", (160, 80), (255, 255, 255))
        paint(img)
        return img

    def rows(self):
        """A page of text-like rows: the shape whose ink a shift moves in and out of
        every cell it touches."""
        from PIL import ImageDraw

        def paint(img):
            d = ImageDraw.Draw(img)
            # Kept clear of the borders: a shift pushes content off the edge, and on a
            # 160×80 fixture that border row is a large share of the cells. A real render
            # has margins; this one needs them to be about the shift and nothing else.
            for y in range(15, 66, 6):
                d.line((10, y, 149, y), fill=(20, 20, 20))
        return self.image(paint)

    def moved(self, img, px: int):
        """The same page, `px` pixels lower. A translation of the whole render, which is
        what a padding or line-height difference actually produces."""
        from PIL import Image

        out = Image.new("RGB", img.size, (255, 255, 255))
        out.paste(img.crop((0, 0, img.width, img.height - px)), (0, px))
        return out

    def test_a_sub_cell_shift_is_not_a_difference(self):
        """A 1-to-3 px offset is what glyph hinting and rounding produce; nobody sees it,
        and it used to spend a whole criterion. Whole-cell offsets still count."""
        base = self.rows()
        for px in (1, 2, 3):
            with self.subTest(px=px):
                r = vp.diff_images(base, self.moved(base, px))
                self.assertEqual(r["pct"], 0.0)
                self.assertGreater(r["pct_unaligned"], r["pct"],
                                   "the unaligned number is what it would have judged")

    def test_a_shift_of_a_whole_cell_or_more_still_counts(self):
        """The tolerance is sub-cell, not free: a visible move is still a difference."""
        base = self.rows()
        self.assertGreater(vp.diff_images(base, self.moved(base, 8))["pct"], 3.0)

    def test_a_shift_does_not_absolve_a_real_difference(self):
        """Otherwise adding an offset would be a way to make any failure go green."""
        from PIL import ImageDraw

        base = self.rows()
        both = self.moved(base, 2)
        ImageDraw.Draw(both).rectangle((40, 20, 79, 59), fill=(255, 45, 85))
        self.assertGreater(vp.diff_images(base, both)["pct"], 3.0)

    def test_glyph_edges_vanish_and_a_block_stays(self):
        """One-pixel-wide lines, the shape of a glyph edge or a card border, average
        away inside a 4×4 cell; a 40×40 block of another colour does not."""
        from PIL import ImageDraw

        base = self.image(lambda img: None)
        edges = self.image(lambda img: [ImageDraw.Draw(img).line((0, y, 159, y),
                                                                  fill=(200, 200, 200))
                                        for y in range(0, 80, 8)])
        block = self.image(lambda img: ImageDraw.Draw(img).rectangle((40, 20, 79, 59),
                                                                     fill=(255, 45, 85)))
        self.assertEqual(vp.diff_images(base, edges)["pct"], 0.0)
        self.assertGreater(vp.diff_images(base, edges, scale=1)["pct"], 10.0)
        blocked = vp.diff_images(base, block)
        # The block is 10×10 cells. Alignment gives one boundary cell back — a cell at the
        # edge of a solid block finds a match a sub-cell shift away — and that is the
        # tolerance's price, paid at boundaries and nowhere else.
        self.assertEqual((blocked["count"], blocked["total"]), (99, 800))
        self.assertEqual(blocked["box"], [40, 20, 79, 59])
        self.assertGreater(blocked["pct"], 12.0)
        self.assertAlmostEqual(blocked["pct_unaligned"], 100 * (10 * 10) / (40 * 20),
                               places=1)


@unittest.skipUnless(_has_imaging(), "needs numpy and Pillow: "
                     "uv run --with numpy --with pillow python -m unittest")
class TestAround(unittest.TestCase):
    """A pixel failure names the elements the differing cells are actually in.

    Needs numpy because the ranking reads the differing-cell mask, which is the array the
    judge already built — the alternative is a second, hand-rolled mask that would drift
    from the one that decides the verdict."""

    ELEMENTS = [
        {"label": 'main "页面"', "x": 0, "y": 0, "w": 1440, "h": 900},
        {"label": 'button "开始生成"', "x": 100, "y": 100, "w": 120, "h": 40},
        {"label": 'heading "任务队列"', "x": 100, "y": 20, "w": 300, "h": 30},
        {"label": 'button "设置"', "x": 1300, "y": 20, "w": 80, "h": 30},
    ]

    def pixel(self, cells: list[tuple[int, int]]):
        """A pixel result whose differing cells are exactly the ones named, in the
        judge's 4-px grid."""
        import numpy as np
        mask = np.zeros((225, 360), dtype=bool)
        for x, y in cells:
            mask[y // 4, x // 4] = True
        return {"mask": mask, "scale": 4}

    def test_the_element_the_cells_are_in_comes_first_and_the_page_last(self):
        self.assertEqual(vp.around(self.pixel([(140, 110), (150, 120)]), self.ELEMENTS),
                         ['button "开始生成"', 'main "页面"'])

    def test_an_element_the_cells_are_not_in_is_not_named(self):
        """The old ranking took the bounding box of every differing cell and returned the
        smallest elements touching it, so a difference in one corner named elements in
        the other. Two far-apart differences must still name only their own elements."""
        names = vp.around(self.pixel([(140, 110), (1340, 30)]), self.ELEMENTS)
        self.assertIn('button "开始生成"', names)
        self.assertIn('button "设置"', names)
        self.assertNotIn('heading "任务队列"', names)

    def test_limit_and_nothing_to_rank(self):
        self.assertEqual(vp.around({"mask": None, "scale": 4}, self.ELEMENTS), [])
        self.assertEqual(vp.around(self.pixel([]), self.ELEMENTS), [])
        self.assertEqual(
            len(vp.around(self.pixel([(140, 110), (1340, 30)]), self.ELEMENTS, limit=1)), 1)

    def test_the_diff_line_carries_both_numbers_and_the_names(self):
        """Both high is drawn wrong; only the unaligned one high is merely out of
        position. That is the layout/rendering split, without a second threshold."""
        pixel = dict(self.pixel([(140, 110), (150, 120)]),
                     size_equal=True, pct=12.5, pct_unaligned=31.0, count=100,
                     total=800, box=[90, 90, 240, 150],
                     size_a=(10, 10), size_b=(10, 10))
        c = comparison(pixel=pixel)
        c.impl_elements = self.ELEMENTS
        control = comparison(scene="__negative_control__",
                             pixel={"size_equal": True, "pct": 23.4, "count": 9,
                                    "total": 100, "box": [0, 0, 9, 9],
                                    "size_a": (10, 10), "size_b": (10, 10)})
        code, lines = vp.gate(control, [c], 3.0, 0)
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["DIFF default 1440x900 12.5% box=[90, 90, 240, 150] "
                                 "— pixel 12.5% > 3.0% (unaligned 31.0%) "
                                 "around: button \"开始生成\", main \"页面\""])

    def test_an_aria_failure_names_nothing(self):
        c = comparison(aria=vp.aria_diff(ROUND2_CARD, ROUND2_CARD.replace("2 张", "3 张", 1)))
        c.impl_elements = self.ELEMENTS
        control = comparison(scene="__negative_control__",
                             pixel={"size_equal": True, "pct": 23.4, "count": 9,
                                    "total": 100, "box": [0, 0, 9, 9],
                                    "size_a": (10, 10), "size_b": (10, 10)})
        self.assertNotIn("around:", vp.gate(control, [c], 3.0, 0)[1][0])


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
            "  baseline  strong 2 张 (in button \"最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08\")",
            "  impl      strong 3 张 (in button \"最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08\")",
        ])

    def test_a_line_only_one_side_has_says_which_side(self):
        shorter = "\n".join(ROUND2_CARD.splitlines()[:2]) + "\n"
        diff = vp.aria_diff(ROUND2_CARD, shorter)["diff"]
        self.assertEqual(vp.change_lines(diff), [
            "  only in baseline  strong 2 张 (in button \"最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08\")"])

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
        self.assertEqual(lines[1:], [
            "  baseline  strong 2 张 (in button \"最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08\")",
            "  impl      strong 3 张 (in button \"最近使用 山野净洗洁精 1 个任务进行中 PRJ-240716-C08\")"])


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
                         (0, ["PARITY OK 2/2 pixel<=0.0%"]))

    def test_the_ok_line_carries_the_worst_pixel_share(self):
        """A difference under the threshold passes and is still on record, so the
        `EXPECT: PARITY OK <passed>/<total>` on a ticket keeps matching as a prefix."""
        caught = comparison(scene="__negative_control__",
                            pixel={"size_equal": True, "pct": 23.4, "count": 9,
                                   "total": 100, "box": [0, 0, 9, 9],
                                   "size_a": (10, 10), "size_b": (10, 10)},
                            aria={"changed": 28, "lines_a": 30, "lines_b": 2,
                                  "diff": ""})
        near = comparison(pixel={"size_equal": True, "pct": 1.52, "count": 3,
                                 "total": 200, "box": [0, 0, 9, 9],
                                 "size_a": (10, 10), "size_b": (10, 10)})
        self.assertEqual(vp.gate(caught, [comparison(), near], 3.0, 0),
                         (0, ["PARITY OK 2/2 pixel<=1.52%"]))


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


class TestVolatileValues(unittest.TestCase):
    """The pixel judge's paint script is generated from the same implicit-role
    table the tree uses for matching, including table cells."""

    def test_volatile_paint_js_includes_the_cell_role_the_tree_would_see(self):
        self.assertEqual(vp.sd.VOLATILE_IMPLICIT_ROLES["TD"], "cell")
        js = vp.sd.volatile_paint_js([vp.sd.VolatileTrigger("text", "鸭豆余额 12,480")])
        self.assertIn('TD: "cell"', js)
        self.assertIn(vp.sd.VOLATILE_DIGITS.pattern, js)
        self.assertIn(vp.sd.VOLATILE_FILL, js)


class TestOverCdp(unittest.TestCase):
    """An implementation that is already running is connected to, not opened.

    The three things that differ from a browser this program launched are all here: the
    size and the pixel ratio go down as a device-metrics override because the context
    belongs to the application, the reduced-motion setting is put on the page for the
    same reason, and the page is picked out of the application's own windows by title.
    """

    class Session:
        def __init__(self):
            self.sent = []

        def send(self, method, params):
            self.sent.append((method, params))

    class Page:
        def __init__(self, title="", url="http://127.0.0.1:5173/"):
            self.session = TestOverCdp.Session()
            self.context = type("Ctx", (), {
                "new_cdp_session": lambda _self, page: page.session})()
            self.sized = None
            self.media = None
            self._title = title
            self.url = url

        def set_viewport_size(self, size):
            self.sized = size

        def emulate_media(self, **kwargs):
            self.media = kwargs

        def title(self):
            return self._title

    def test_a_launched_page_is_given_its_viewport_directly(self):
        page = self.Page()
        vp.resize(page, (1440, 900), over_cdp=False)
        self.assertEqual(page.sized, {"width": 1440, "height": 900})
        self.assertEqual(page.session.sent, [])

    def test_a_connected_page_is_sent_its_metrics_with_the_ratio_pinned(self):
        page = self.Page()
        vp.resize(page, (1180, 720), over_cdp=True)
        self.assertIsNone(page.sized)
        self.assertEqual(page.session.sent, [(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1180, "height": 720, "deviceScaleFactor": 1, "mobile": False})])
        self.assertEqual(page.media, {"reduced_motion": "reduce"})

    def browser(self, *pages):
        context = type("Ctx", (), {"pages": list(pages)})()
        return type("Browser", (), {"contexts": [context]})()

    def test_with_no_title_asked_for_the_first_page_is_taken(self):
        first = self.Page(title="the app")
        found = vp.impl_page_over_cdp(self.browser(first, self.Page(title="other")), None)
        self.assertIs(found, first)

    def test_a_title_substring_picks_the_window(self):
        wanted = self.Page(title="商品工作台 — Chameleon")
        found = vp.impl_page_over_cdp(
            self.browser(self.Page(title="DevTools"), wanted), "Chameleon")
        self.assertIs(found, wanted)

    def test_no_such_window_says_what_was_there(self):
        with self.assertRaises(SystemExit) as raised:
            vp.impl_page_over_cdp(self.browser(self.Page(title="DevTools")),
                                  "Chameleon", timeout_seconds=0)
        self.assertIn("DevTools", str(raised.exception))


class TestArguments(unittest.TestCase):
    """Helpers the story judge still uses."""

    def test_viewports_are_read_as_pairs(self):
        self.assertEqual(vp.parse_viewports(["1440x900", "1180x720"]),
                         [(1440, 900), (1180, 720)])
        self.assertEqual(vp.parse_viewports("1440x900,1180x720"),
                         [(1440, 900), (1180, 720)])
        with self.assertRaises(ValueError):
            vp.parse_viewports("1440*900")

    def test_the_wrapper_pins_the_scene(self):
        self.assertIn('scenario="queue-empty"',
                      vp.wrapper_page("Component · 任务队列", {"scenario": "queue-empty"}))

    def test_the_negative_control_error_is_in_the_served_bytes(self):
        """The control's banner rides inside the page the server sends, so an
        implementation chain that reads the baseline server gets the banner too."""
        page = vp.wrapper_page("Component · 任务队列", {}, vp.NEGATIVE_CONTROL_HEAD)
        self.assertIn("NEGATIVE CONTROL", page)
        self.assertNotIn("NEGATIVE CONTROL", vp.wrapper_page("Component · 任务队列", {}))


class TestClasses(unittest.TestCase):
    """The third judge: the class set of the subtree, compared as a set."""

    def test_a_missing_class_fails_the_scene_and_names_the_element(self):
        c = comparison()
        c.classes = vp.sd.class_diff({"btn": 'button "开始生成"', "btn-primary": 'button "开始生成"'},
                                     {"btn": 'button "开始生成"'})
        reasons = vp.failures(c, max_pct=3.0, console_limit=0)
        self.assertEqual([r.kind for r in reasons], ["classes"])
        self.assertEqual(vp.class_lines(c.classes),
                         ['  class only in baseline  btn-primary  (on button "开始生成")'])

    def test_equal_sets_are_no_reason(self):
        c = comparison()
        c.classes = vp.sd.class_diff({"a": "x"}, {"a": "y"})
        self.assertEqual(vp.failures(c, max_pct=3.0, console_limit=0), [])


class TestFrameBox(unittest.TestCase):
    """The design is pinned to the box the product measured, never to a declared size."""

    def test_frame_box_pins_dc_root_to_the_measured_size(self):
        css = vp.frame_box((1440, 854))
        self.assertIn("width:1440px !important", css)
        self.assertIn("height:854px !important", css)
        self.assertNotIn("900", css)


if __name__ == "__main__":
    unittest.main()
