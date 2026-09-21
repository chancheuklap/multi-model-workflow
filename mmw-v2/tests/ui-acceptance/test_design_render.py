"""Design-side rendering without a browser: the contract's screen axis, the box
arithmetic, the tree's ancestor line, and the baseline server.
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts" / "design_render.py"


def load():
    """A fresh `design_render`."""
    spec = importlib.util.spec_from_file_location("design_render", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["design_render"] = module
    spec.loader.exec_module(module)
    return module


dr = load()

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
        scenes = dr.scenes_of(CONTRACT, CATALOGUE)
        s = scenes["library-delete-confirm"]
        self.assertEqual(s.mount, "workbench-shell")
        self.assertEqual(s.props, {"scenario": "library-delete-confirm"})

    def test_a_mount_written_on_a_scene_is_not_read(self):
        contract = dict(CONTRACT, scenes=dict(CONTRACT["scenes"]))
        contract["scenes"]["library-name-duplicate"] = dict(
            contract["scenes"]["library-name-duplicate"], mount="workbench-shell")
        s = dr.scenes_of(contract, CATALOGUE)["library-name-duplicate"]
        self.assertEqual(s.mount, "create-project")
        self.assertEqual(s.props, {"scenario": "library-name-duplicate"})

    def test_a_page_s_own_viewports_flow_into_its_scenes(self):
        pages = {k: dict(v) for k, v in CONTRACT["pages"].items()}
        first = next(iter(pages))
        pages[first]["viewports"] = ["236x848"]
        contract = dict(CONTRACT, pages=pages)
        scenes = dr.scenes_of(contract, CATALOGUE)
        for s in scenes.values():
            self.assertEqual(s.viewports, ((236, 848),) if s.page == first else ())

    def test_the_plan_is_derived_from_mounts(self):
        plan = dr.scene_plan(CONTRACT, CATALOGUE, ["workbench-shell"], None)
        self.assertEqual(sorted(s.name for s in plan),
                         ["library-delete-confirm", "workbench-shell.default"])

    def test_explicit_scenes_narrow_the_plan_and_must_be_inside_it(self):
        plan = dr.scene_plan(CONTRACT, CATALOGUE, ["workbench-shell"], ["workbench-shell.default"])
        self.assertEqual([s.name for s in plan], ["workbench-shell.default"])
        with self.assertRaises(SystemExit) as raised:
            dr.scene_plan(CONTRACT, CATALOGUE, ["workbench-shell"], ["library.ready"])
        self.assertIn("outside mount", str(raised.exception))

    def test_a_mount_nobody_declares_is_refused(self):
        with self.assertRaises(SystemExit):
            dr.scene_plan(CONTRACT, CATALOGUE, ["nowhere"], None)

    def test_a_contract_without_pages_is_refused(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("scenes: {}\nrows: []\n")
        try:
            with self.assertRaises(SystemExit) as raised:
                dr.load_contract(Path(f.name))
            self.assertIn("pages", str(raised.exception))
        finally:
            os.unlink(f.name)

    def test_a_contract_does_not_need_target_kind(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("pages: {}\nscenes: {}\n")
        try:
            self.assertEqual(dr.load_contract(Path(f.name)), {"pages": {}, "scenes": {}})
        finally:
            os.unlink(f.name)

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
        self.addCleanup(dr._CLOCK_PAGES.discard, id(page))
        dr.navigate(page, "http://x/#/a", reload=True)
        self.assertTrue(page.installed)
        self.assertEqual(page.paused, dr.CLOCK_EPOCH_MS)
        self.assertEqual(page.actions, [("goto", "http://x/#/a"), "reload"])
        self.assertEqual(page.ran, dr.SETTLE_VIRTUAL_MS)
        page.installed = False
        dr.navigate(page, "http://x/#/b")
        self.assertFalse(page.installed)
        self.assertEqual(page.paused, dr.CLOCK_EPOCH_MS)
        self.assertEqual(page.ran, 2 * dr.SETTLE_VIRTUAL_MS)


class TestBoxes(unittest.TestCase):
    """The pixel judge sees the mount's layout box intersected with the viewport."""

    class Page:
        """`mount_rect` is one page evaluation; the fake answers it with a fixed box."""

        def __init__(self, rect):
            self.rect = rect

        def evaluate(self, js, selector=None):
            assert js is dr.MOUNT_RECT_JS
            return self.rect

    def test_a_component_below_a_header_keeps_its_own_box(self):
        page = self.Page({"x": 0, "y": 46, "width": 1440, "height": 854})
        self.assertEqual(dr.visible_box(page, "[data-screen=x]", (1440, 900)), (0, 46, 1440, 854))

    def test_a_long_table_is_cut_at_the_fold(self):
        page = self.Page({"x": 0, "y": 100, "width": 1440, "height": 3000})
        self.assertEqual(dr.visible_box(page, "[data-screen=x]", (1440, 900)), (0, 100, 1440, 800))

    def test_an_element_partly_off_screen(self):
        page = self.Page({"x": -20, "y": 0, "width": 1500, "height": 900})
        self.assertEqual(dr.visible_box(page, "[data-screen=x]", (1440, 900)), (0, 0, 1440, 900))

    def test_a_mount_without_a_box_is_not_on_screen(self):
        with self.assertRaises(SystemExit):
            dr.visible_box(self.Page(None), "[data-screen=x]", (1440, 900))


class TestAccessibleNames(unittest.TestCase):
    def test_a_quoted_option_key_is_named_from_the_dom(self):
        tree = "  - 'option \"Credit: main\" [selected]'"
        self.assertEqual(
            dr.name_options_from_dom(tree, ["Credit: main"]),
            '  - option "Credit: main" [selected]',
        )






class TestBaselineServing(unittest.TestCase):
    def test_vendor_copy_wins_over_the_cache(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d)
            self.assertIsNone(dr.vendor_path(baseline, dr.CDN_PREFIX + "react@18.3.1/umd/react.production.min.js"))
            (baseline / dr.VENDOR_DIR).mkdir()
            (baseline / dr.VENDOR_DIR / "react.production.min.js").write_text("//")
            self.assertEqual(dr.vendor_path(baseline, dr.CDN_PREFIX + "react@18.3.1/umd/react.production.min.js"),
                             baseline / dr.VENDOR_DIR / "react.production.min.js")

    def test_wrapper_page_carries_inline_head_and_scene(self):
        page = dr.wrapper_page("Component · 壳头", {"scenario": "ready", "standalone": False},
                               "<style>x</style>")
        self.assertIn('scenario="ready"', page)
        self.assertIn("standalone=\"{{ false }}\"", page)
        self.assertIn("<style>x</style>", page)
        self.assertEqual(dr.wrapper_path("a.b"), "/__parity-a.b.dc.html")
        self.assertEqual(dr.component_of("Component · 壳头.dc.html"), "Component · 壳头")


class TestUiValues(unittest.TestCase):
    """The values file path and the JSON array `--render-only` writes."""

    def test_values_path_joins_mount_scene_and_viewport(self):
        path = dr.values_path(Path("/out"), "library-app", "alpha", (400, 300))
        self.assertEqual(
            path, Path("/out") / "values" / "library-app" / "alpha-400x300.json")

    def test_write_values_writes_a_json_array(self):
        with tempfile.TemporaryDirectory() as d:
            path = dr.values_path(Path(d), "demo", "alpha", (400, 300))
            dr.write_values(path, [{"id": "title", "visible": True}])
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                [{"id": "title", "visible": True}])













if __name__ == "__main__":
    unittest.main()
