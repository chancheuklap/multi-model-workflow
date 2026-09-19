"""Design-side rendering without a browser: the contract's screen axis, the box
arithmetic, the tree's ancestor line, and the baseline server.
"""

import importlib.util
import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts" / "design_render.py"
HOME = tempfile.mkdtemp(prefix="mmw-design-render-home-")


def load():
    """A fresh `design_render`."""
    with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
        spec = importlib.util.spec_from_file_location("design_render", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules["design_render"] = module
        spec.loader.exec_module(module)
    return module


sd = load()


def tearDownModule():
    shutil.rmtree(HOME, ignore_errors=True)

CONTRACT = {
    "target": {"kind": "electron"},
    "viewports": ["1440x900", "1180x720"],
    "baselines": {"look": "handoff"},
    "pages": {
        "App · 商品项目库.dc.html": {"mount": "library-app", "route": "#/"},
        "Component · 工作台壳.dc.html": {"mount": "workbench-shell",
                                        "route": "#/project/{project_id}"},
        "Component · 新建商品项目.dc.html": {"mount": "create-project", "route": "#/new-project"},
    },
    "mechanisms": {"seed:project-with-subjects": {"via": "api", "built_by": "#639"}},
    "scenes": {
        "library.ready": {"page": "App · 商品项目库.dc.html", "reach": ["seed:library-ready"]},
        "library-delete-confirm": {"page": "Component · 工作台壳.dc.html",
                                   "reach": ["seed:project-with-subjects"],
                                   "open": ["workbench-shell.delete.preview.allowed"]},
        "library-name-duplicate": {"page": "Component · 新建商品项目.dc.html",
                                   "route": "#/new-project",
                                   "reach": ["seed:library-ready"],
                                   "open": [{"row": "create-project.name",
                                             "value": "{existing_project_name}"}]},
        "workbench-shell.default": {"page": "Component · 工作台壳.dc.html",
                                    "reach": ["seed:project-with-subjects"]},
    },
    "retired_ids": [{"id": "x.y", "note": "n", "trigger": {"role": "button", "name": "查看账务状态"}}],
    "rows": [
        {"id": "workbench-shell.delete.preview.allowed",
         "trigger": {"role": "button", "name": "删除商品项目"}, "next": "library-delete-confirm"},
        {"id": "create-project.name", "trigger": {"role": "textbox", "name": "商品名称"},
         "next": "library-name-duplicate"},
        {"id": "create-project.subject", "trigger": {"role": "combobox", "name": "商品主体图"},
         "next": "create-project-subject-chosen"},
    ],
}
CATALOGUE = {
    "library.ready": {"name": "library.ready", "page": "App · 商品项目库.dc.html",
                      "props": {"scenario": "ready"}},
    "library-delete-confirm": {"name": "library-delete-confirm",
                               "page": "Component · 工作台壳.dc.html",
                               "props": {"scenario": "library-delete-confirm"}},
    "library-name-duplicate": {"name": "library-name-duplicate",
                               "page": "Component · 新建商品项目.dc.html",
                               "props": {"scenario": "library-name-duplicate"}},
    "workbench-shell.default": {"name": "workbench-shell.default",
                                "page": "Component · 工作台壳.dc.html",
                                "props": {"scenario": "default"}},
}


class TestScreenAxis(unittest.TestCase):
    """`mount` is declared on the page, and only there; a scene takes its page's."""

    def test_page_defaults_flow_into_scenes(self):
        scenes = sd.scenes_of(CONTRACT, CATALOGUE)
        s = scenes["library-delete-confirm"]
        self.assertEqual(s.mount, "workbench-shell")
        self.assertEqual(s.props, {"scenario": "library-delete-confirm"})

    def test_a_mount_written_on_a_scene_is_not_read(self):
        contract = dict(CONTRACT, scenes=dict(CONTRACT["scenes"]))
        contract["scenes"]["library-name-duplicate"] = dict(
            contract["scenes"]["library-name-duplicate"], mount="workbench-shell")
        s = sd.scenes_of(contract, CATALOGUE)["library-name-duplicate"]
        self.assertEqual(s.mount, "create-project")
        self.assertEqual(s.props, {"scenario": "library-name-duplicate"})

    def test_the_plan_is_derived_from_mounts(self):
        plan = sd.scene_plan(CONTRACT, CATALOGUE, ["workbench-shell"], None)
        self.assertEqual(sorted(s.name for s in plan),
                         ["library-delete-confirm", "workbench-shell.default"])

    def test_explicit_scenes_narrow_the_plan_and_must_be_inside_it(self):
        plan = sd.scene_plan(CONTRACT, CATALOGUE, ["workbench-shell"], ["workbench-shell.default"])
        self.assertEqual([s.name for s in plan], ["workbench-shell.default"])
        with self.assertRaises(SystemExit) as raised:
            sd.scene_plan(CONTRACT, CATALOGUE, ["workbench-shell"], ["library.ready"])
        self.assertIn("outside mount", str(raised.exception))

    def test_a_mount_nobody_declares_is_refused(self):
        with self.assertRaises(SystemExit):
            sd.scene_plan(CONTRACT, CATALOGUE, ["nowhere"], None)

    def test_a_contract_without_the_axis_is_refused(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("rows: []\n")
        try:
            with self.assertRaises(SystemExit) as raised:
                sd.load_contract(Path(f.name))
            self.assertIn("target", str(raised.exception))
        finally:
            os.unlink(f.name)

    def test_retired_triggers_are_scoped_to_a_page(self):
        self.assertEqual(sd.retired_triggers(CONTRACT), [("button", "查看账务状态")])
        scoped = {"retired_ids": [{"id": "a", "page": "Component · 自由模式.dc.html",
                                   "trigger": {"role": "button", "name": "查看"}}]}
        self.assertEqual(sd.retired_triggers(scoped, "Component · 自由模式.dc.html"), [("button", "查看")])
        self.assertEqual(sd.retired_triggers(scoped, "Component · 任务详情.dc.html"), [])
        self.assertIsNone(sd.hide_js_for(scoped, "Component · 任务详情.dc.html"))


class FakePage:
    """Enough of a Playwright page for `navigate`.

    `named` is the accessibility tree in reading order: `(role, name)` or
    `(role, name, identity)`. When it is set, `get_by_role` and
    `aria_snapshot` both read it, so `nth` resolves to a node rather than
    an integer the test invented."""

    def __init__(self, controls=None, named=None):
        self.named = list(named or [])
        self.controls = dict(controls or {})
        self.actions = []
        self.clock = self
        self.installed = False
        self.paused = None
        self.ran = 0

    # clock
    def install(self, time=None):
        self.installed = True

    def pause_at(self, t):
        self.paused = t

    def run_for(self, ms):
        self.ran += ms

    def resume(self):
        self.actions.append("resume")

    # navigation
    def goto(self, url, wait_until=None):
        self.actions.append(("goto", url))

    def reload(self, wait_until=None):
        self.actions.append("reload")

    def locator(self, selector):
        page = self

        class Root:
            def aria_snapshot(self_inner):
                lines = []
                for entry in page.named:
                    lines.append(f'- {entry[0]} "{entry[1]}"')
                return "\n".join(lines)

        return Root()

    def get_by_role(self, role, name=None, exact=False):
        page = self
        matches = [e for e in self.named if e[0] == role and e[1] == name]
        count = len(matches) if self.named else self.controls.get((role, name), 0)
        # `tags` names the elements that are not what their role suggests: a
        # `combobox` that is a native `<select>` takes select_option, not fill.
        tag = getattr(self, "tags", {}).get((role, name), "")

        class Locator:
            def __init__(self_inner, index=None):
                self_inner._index = index

            def count(self_inner):
                return count

            @property
            def first(self_inner):
                return self_inner

            def nth(self_inner, n):
                return Locator(n)

            def click(self_inner, timeout=None):
                if matches:
                    idx = 0 if self_inner._index is None else self_inner._index
                    if idx < 0 or idx >= len(matches):
                        raise Exception(f"nth({idx}) out of range ({len(matches)})")
                    entry = matches[idx]
                    ident = entry[2] if len(entry) > 2 else idx
                    page.actions.append(("click", role, name, ident))
                    return
                if self_inner._index is None:
                    page.actions.append(("click", role, name))
                else:
                    page.actions.append(("click", role, name, self_inner._index))

            def fill(self_inner, value, timeout=None):
                page.actions.append(("fill", role, name, value))

            def select_option(self_inner, label=None, timeout=None):
                page.actions.append(("select_option", role, name, label))

            def evaluate(self_inner, js):
                if not tag:
                    raise AttributeError("no evaluate on this double")
                return tag

        return Locator()








class TestClockAndNavigation(unittest.TestCase):
    def test_the_clock_is_installed_once_and_each_navigate_settles(self):
        page = FakePage({})
        self.addCleanup(sd._CLOCK_PAGES.discard, id(page))
        sd.navigate(page, "http://x/#/a", reload=True)
        self.assertTrue(page.installed)
        self.assertEqual(page.paused, sd.CLOCK_EPOCH_MS)
        self.assertEqual(page.actions, [("goto", "http://x/#/a"), "reload"])
        self.assertEqual(page.ran, sd.SETTLE_VIRTUAL_MS)
        page.installed = False
        sd.navigate(page, "http://x/#/b")
        self.assertFalse(page.installed)
        self.assertEqual(page.paused, sd.CLOCK_EPOCH_MS)
        self.assertEqual(page.ran, 2 * sd.SETTLE_VIRTUAL_MS)


class TestBoxes(unittest.TestCase):
    """The pixel judge sees the mount's layout box intersected with the viewport."""

    class Page:
        """`mount_rect` is one page evaluation; the fake answers it with a fixed box."""

        def __init__(self, rect):
            self.rect = rect

        def evaluate(self, js, selector=None):
            assert js is sd.MOUNT_RECT_JS
            return self.rect

    def test_a_component_below_a_header_keeps_its_own_box(self):
        page = self.Page({"x": 0, "y": 46, "width": 1440, "height": 854})
        self.assertEqual(sd.visible_box(page, "[data-screen=x]", (1440, 900)), (0, 46, 1440, 854))

    def test_a_long_table_is_cut_at_the_fold(self):
        page = self.Page({"x": 0, "y": 100, "width": 1440, "height": 3000})
        self.assertEqual(sd.visible_box(page, "[data-screen=x]", (1440, 900)), (0, 100, 1440, 800))

    def test_an_element_partly_off_screen(self):
        page = self.Page({"x": -20, "y": 0, "width": 1500, "height": 900})
        self.assertEqual(sd.visible_box(page, "[data-screen=x]", (1440, 900)), (0, 0, 1440, 900))

    def test_a_mount_without_a_box_is_not_on_screen(self):
        with self.assertRaises(SystemExit):
            sd.visible_box(self.Page(None), "[data-screen=x]", (1440, 900))

    def test_frame_box_pins_the_design_to_the_measured_size(self):
        self.assertIn("width:1440px !important;height:854px !important", sd.frame_box((1440, 854)))


class TestTree(unittest.TestCase):
    def test_nearest_named_ancestor_not_landmark_not_wrapper(self):
        tree = ('- main "页面":\n  - list:\n    - dialog "确认":\n      - generic:\n'
                '        - button "删除"\n  - button "取消"')
        self.assertEqual(sd.normalize_aria(tree),
                         ['- dialog "确认"', '- button "删除" < dialog "确认"', '- button "取消"'])


class TestClassSets(unittest.TestCase):
    def test_diff_names_the_element_that_wears_the_class(self):
        d = sd.class_diff({"btn": 'button "开始"', "hot": 'span "!"'}, {"btn": 'button "开始"'})
        self.assertEqual(d["only_in_baseline"], [("hot", 'span "!"')])
        self.assertEqual(d["only_in_impl"], [])
        self.assertEqual(d["changed"], 1)

    def test_runtime_prefixes_are_not_design(self):
        self.assertTrue(all(p in ("sc-", "dc-") for p in sd.RUNTIME_CLASS_PREFIXES))






class TestBaselineServing(unittest.TestCase):
    def test_vendor_copy_wins_over_the_cache(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d)
            self.assertIsNone(sd.vendor_path(baseline, sd.CDN_PREFIX + "react@18.3.1/umd/react.production.min.js"))
            (baseline / sd.VENDOR_DIR).mkdir()
            (baseline / sd.VENDOR_DIR / "react.production.min.js").write_text("//")
            self.assertEqual(sd.vendor_path(baseline, sd.CDN_PREFIX + "react@18.3.1/umd/react.production.min.js"),
                             baseline / sd.VENDOR_DIR / "react.production.min.js")

    def test_hide_retired_js_names_the_controls(self):
        js = sd.hide_retired_js([("button", "查看账务状态")])
        self.assertIn('"查看账务状态"', js)
        self.assertIn("display = 'none'", js)

    def test_volatile_values_replace_the_name_with_the_same_token_on_both_sides(self):
        """A wallet balance is an external account; the seed does not write it. The
        two judges replace the node's text with one token so 12,480 and 20 compare
        equal. The trigger is the handoff's role and accessible name; a product
        node matches when its role is the same and the non-digit stem of the name
        is the same."""
        triggers = [sd.VolatileTrigger("text", "鸭豆余额 12,480")]
        design = '- main:\n  - text: 鸭豆余额 12,480\n  - button "新建商品项目"\n'
        product = '- main:\n  - text: 鸭豆余额 20\n  - button "新建商品项目"\n'
        masked_d = sd.mask_volatile(sd.normalize_aria(design), triggers)
        masked_p = sd.mask_volatile(sd.normalize_aria(product), triggers)
        self.assertEqual(masked_d, masked_p)
        self.assertTrue(any("<volatile>" in line for line in masked_d))
        self.assertFalse(any("12,480" in line or " 20" in line for line in masked_d))
        self.assertEqual(sd.aria_diff(design, product, volatile=triggers)["changed"], 0)
        self.assertGreater(sd.aria_diff(design, product)["changed"], 0)

    def test_volatile_values_replace_the_name_on_ancestor_suffixes_too(self):
        triggers = [sd.VolatileTrigger("status", "鸭豆余额 12,480")]
        design = '- status "鸭豆余额 12,480"\n  - text: 可用\n'
        product = '- status "鸭豆余额 20"\n  - text: 可用\n'
        masked = sd.mask_volatile(sd.normalize_aria(design), triggers)
        self.assertEqual(masked, sd.mask_volatile(sd.normalize_aria(product), triggers))
        self.assertTrue(any("<volatile>" in line for line in masked))
        self.assertFalse(any("12,480" in line for line in masked))
        self.assertFalse(any("鸭豆余额 20" in line for line in masked))
        self.assertTrue(any("可用" in line and "<volatile>" in line for line in masked))

    def test_volatile_paint_puts_the_triggers_digits_in_the_node_before_painting(self):
        """A painted box is as wide as the string in it, so `0 鸭豆` and `3,220 鸭豆`
        painted over still move what follows them — and the design side shows its own
        other number on some scenes. Both sides take the trigger's digits into the
        first digit-bearing text node, then the paint; a node named by aria-label is
        left as it is."""
        js = sd.volatile_paint_js([sd.VolatileTrigger("strong", "3,220 鸭豆")])
        self.assertIn("createTreeWalker(el, NodeFilter.SHOW_TEXT)", js)
        self.assertIn("node.nodeValue.replace(/[\\d,]+/, target)", js)
        self.assertIn("el.getAttribute('aria-label')) return", js)
        self.assertLess(js.index("retext(el, w)"), js.index("el.style.backgroundColor"))

    def test_volatile_paint_js_maps_a_table_cell_for_a_text_trigger(self):
        self.assertEqual(sd.VOLATILE_IMPLICIT_ROLES["TD"], "cell")
        self.assertIn("cell", sd.VOLATILE_TEXT_LIKE)
        js = sd.volatile_paint_js([sd.VolatileTrigger("text", "鸭豆余额 12,480")])
        self.assertIn(sd.VOLATILE_FILL, js)
        self.assertIn(sd.VOLATILE_DIGITS.pattern, js)
        self.assertIn('TD: "cell"', js)
        cell_lines = sd.normalize_aria("- cell: 鸭豆余额 12,480\n")
        self.assertEqual(sd.count_volatile_hits(cell_lines, [sd.VolatileTrigger("text", "鸭豆余额 12,480")]), 1)
        scoped = {"volatile_values": [
            {"page": "App · 商品项目库.dc.html",
             "trigger": {"role": "text", "name": "鸭豆余额 12,480"},
             "reason": "wallet balance is an external account; seed does not write it"}]}
        self.assertEqual(sd.volatile_triggers(scoped, "App · 商品项目库.dc.html"),
                         [sd.VolatileTrigger("text", "鸭豆余额 12,480")])
        self.assertEqual(sd.volatile_triggers(scoped, "Component · 工作台壳.dc.html"), [])

    def test_three_same_stem_siblings_the_after_coordinate_hits_one(self):
        """Three strongs share the stem 鸭豆. A trigger with no second coordinate
        matches all three; `after` (the previous named node) matches only the
        one that follows that node — agentflow#654's free-gate counterexample."""
        tree = (
            "- text: 每张费用\n"
            "- strong: 20 鸭豆\n"
            "- text: 最大预扣\n"
            "- strong: 40 鸭豆\n"
            "- text: 当前余额\n"
            "- strong: 12,480 鸭豆\n"
        )
        lines = sd.normalize_aria(tree)
        bare = [sd.VolatileTrigger("strong", "12,480 鸭豆")]
        pinned = [sd.VolatileTrigger("strong", "12,480 鸭豆", ("text", "当前余额"))]
        self.assertEqual(sd.count_volatile_hits(lines, bare), 3)
        self.assertEqual(sd.count_volatile_hits(lines, pinned), 1)
        unique = sd.normalize_aria("- text: 当前余额\n- strong: 12,480 鸭豆\n")
        mixed = ["## scene free-gate", *lines, "## scene free-hold-unknown", *unique]
        self.assertEqual(sd.count_volatile_hits(mixed, bare), 3)
        self.assertEqual(sd.count_volatile_hits(mixed, pinned), 1)
        masked_bare = sd.mask_volatile(lines, bare)
        masked_pinned = sd.mask_volatile(lines, pinned)
        self.assertEqual(sum("<volatile>" in ln for ln in masked_bare), 3)
        self.assertEqual(sum("<volatile>" in ln for ln in masked_pinned), 1)
        self.assertTrue(any("20 鸭豆" in ln for ln in masked_pinned))
        self.assertTrue(any("40 鸭豆" in ln for ln in masked_pinned))
        self.assertFalse(any("12,480" in ln for ln in masked_pinned))
        js = sd.volatile_paint_js(pinned)
        self.assertIn("if (!w.after) return true;", js)
        self.assertIn("if (!prev) return false;", js)
        self.assertIn("prev = {role, nm};", js)
        nested = sd.normalize_aria(
            "- strong: 20 鸭豆\n"
            "  - text: 每张\n"
            "- text: 当前余额\n"
            "- strong: 12,480 鸭豆\n"
            "  - text: 可用\n"
        )
        nested_masked = sd.mask_volatile(nested, pinned)
        self.assertTrue(any("20 鸭豆" in ln for ln in nested_masked))
        self.assertFalse(any("12,480" in ln for ln in nested_masked))
        self.assertTrue(any("<volatile>" in ln and "可用" in ln for ln in nested_masked))
        scoped = {"volatile_values": [
            {"page": "Component · 自由模式.dc.html",
             "trigger": {"role": "strong", "name": "12,480 鸭豆"},
             "after": {"role": "text", "name": "当前余额"},
             "reason": "wallet balance is an external account; seed does not write it"}]}
        got = sd.volatile_triggers(scoped, "Component · 自由模式.dc.html")
        self.assertEqual(got, [sd.VolatileTrigger("strong", "12,480 鸭豆",
                                                  ("text", "当前余额"))])
        self.assertEqual(got[0].after, ("text", "当前余额"))
        self.assertEqual(sd.mask_volatile(lines, got), masked_pinned)
        self.assertEqual(sd.volatile_paint_js(got), js)

    def test_volatile_hits_count_same_stem_names(self):
        """`count_volatile_hits` matches on role plus the non-digit stem, so
        `删除 2` also counts `删除 1`."""
        lines = sd.normalize_aria(
            '- button "删除 1"\n'
            '- heading "确认"\n'
            '- button "删除 2"\n'
        )
        self.assertEqual(
            sd.count_volatile_hits(lines, [sd.VolatileTrigger("button", "删除 2")]), 2)

    def test_wrapper_page_carries_inline_head_and_scene(self):
        page = sd.wrapper_page("Component · 壳头", {"scenario": "ready", "standalone": False},
                               "<style>x</style>")
        self.assertIn('scenario="ready"', page)
        self.assertIn("standalone=\"{{ false }}\"", page)
        self.assertIn("<style>x</style>", page)
        self.assertEqual(sd.wrapper_path("a.b"), "/__parity-a.b.dc.html")
        self.assertEqual(sd.component_of("Component · 壳头.dc.html"), "Component · 壳头")













if __name__ == "__main__":
    unittest.main()
