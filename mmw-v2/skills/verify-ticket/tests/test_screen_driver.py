"""The shared driver behind both judges, without a browser: the contract's screen
axis, the six capabilities against a fake adapter, the box arithmetic, the `open`
chain, the tree's ancestor line, and the two read grammars.
"""

import importlib.util
import json
import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "screen_driver.py"


def load():
    spec = importlib.util.spec_from_file_location("screen_driver", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["screen_driver"] = module
    spec.loader.exec_module(module)
    return module


sd = load()

CONTRACT = {
    "target": {"kind": "electron", "adapter": "verify-ticket/references/targets/electron.md"},
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
                                   "route": "#/new-project", "mount": "create-project",
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
    """`mount` and `route` are declared once per page; a scene may override them."""

    def test_page_defaults_flow_into_scenes(self):
        scenes = sd.scenes_of(CONTRACT, CATALOGUE)
        s = scenes["library-delete-confirm"]
        self.assertEqual((s.mount, s.route), ("workbench-shell", "#/project/{project_id}"))
        self.assertEqual(s.reach, ["seed:project-with-subjects"])
        self.assertEqual(s.open, [{"row": "workbench-shell.delete.preview.allowed", "value": None}])
        self.assertEqual(s.props, {"scenario": "library-delete-confirm"})

    def test_a_scene_overrides_its_page(self):
        s = sd.scenes_of(CONTRACT, CATALOGUE)["library-name-duplicate"]
        self.assertEqual(s.route, "#/new-project")
        self.assertEqual(s.open, [{"row": "create-project.name",
                                   "value": "{existing_project_name}"}])

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

    def test_mechanisms_read_as_list_or_mapping(self):
        self.assertEqual(sd.mechanisms_of({"mechanisms": ["seed:a"]}), {"seed:a": {}})
        self.assertEqual(sd.mechanisms_of(CONTRACT)["seed:project-with-subjects"]["built_by"],
                         "#639")

    def test_retired_triggers_and_placeholders(self):
        self.assertEqual(sd.retired_triggers(CONTRACT), [("button", "查看账务状态")])
        scoped = {"retired_ids": [{"id": "a", "page": "Component · 自由模式.dc.html",
                                   "trigger": {"role": "button", "name": "查看"}}]}
        self.assertEqual(sd.retired_triggers(scoped, "Component · 自由模式.dc.html"), [("button", "查看")])
        self.assertEqual(sd.retired_triggers(scoped, "Component · 任务详情.dc.html"), [])
        self.assertIsNone(sd.hide_js_for(scoped, "Component · 任务详情.dc.html"))
        self.assertEqual(sd.fill("#/project/{project_id}", {"project_id": "p1"}), "#/project/p1")
        self.assertEqual(sd.fill("#/x/{missing}", {}), "#/x/{missing}")


class FakePage:
    """Enough of a Playwright page for `perform` and `navigate`."""

    def __init__(self, controls):
        self.controls = controls  # (role, name) -> count
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

    def get_by_role(self, role, name=None, exact=False):
        page = self
        count = self.controls.get((role, name), 0)

        class Locator:
            def count(self_inner):
                return count

            @property
            def first(self_inner):
                return self_inner

            def click(self_inner, timeout=None):
                page.actions.append(("click", role, name))

            def fill(self_inner, value, timeout=None):
                page.actions.append(("fill", role, name, value))

        return Locator()


class TestOpenChain(unittest.TestCase):
    ROWS = sd.rows_by_id(CONTRACT)

    def test_a_click_step_and_a_fill_step(self):
        page = FakePage({("button", "删除商品项目"): 1, ("textbox", "商品名称"): 1})
        sd.perform(page, [{"row": "workbench-shell.delete.preview.allowed", "value": None},
                          {"row": "create-project.name", "value": "{existing_project_name}"}],
                   self.ROWS, {"existing_project_name": "山野净洗洁精"})
        self.assertEqual(page.actions, [("click", "button", "删除商品项目"),
                                        ("fill", "textbox", "商品名称", "山野净洗洁精")])
        self.assertEqual(page.ran, 2 * sd.SETTLE_VIRTUAL_MS)

    def test_what_a_step_types_becomes_a_value(self):
        page = FakePage({("textbox", "商品名称"): 1})
        values = {"existing_project_name": "山野净洗洁精"}
        sd.perform(page, [{"row": "create-project.name", "value": "{existing_project_name}"}],
                   self.ROWS, values)
        self.assertEqual(values["typed"], "山野净洗洁精")
        self.assertEqual(values["typed_name"], "山野净洗洁精")

    def test_a_missing_control_stops_the_run_and_names_it(self):
        page = FakePage({})
        with self.assertRaises(SystemExit) as raised:
            sd.perform(page, [{"row": "workbench-shell.delete.preview.allowed", "value": None}],
                       self.ROWS, {})
        self.assertIn('button "删除商品项目"', str(raised.exception))
        # the control is waited for in clock steps up to the budget before giving up
        self.assertEqual(page.ran, sd.SETTLE_BUDGET_MS)

    def test_an_unknown_row_stops_the_run(self):
        with self.assertRaises(SystemExit):
            sd.perform(FakePage({}), [{"row": "no.such", "value": None}], self.ROWS, {})


class TestClockAndNavigation(unittest.TestCase):
    def test_the_clock_is_installed_once_paused_and_moved_forward_only(self):
        page = FakePage({})
        sd.navigate(page, "http://x/#/a", reload=True)
        first = page.paused
        self.assertTrue(page.installed)
        self.assertEqual(page.actions, [("goto", "http://x/#/a"), "reload"])
        self.assertEqual(page.ran, sd.SETTLE_VIRTUAL_MS)
        page.installed = False
        sd.navigate(page, "http://x/#/b")
        self.assertFalse(page.installed)  # not installed a second time
        self.assertGreater(page.paused, first)
        sd._CLOCKED.pop(id(page), None)

    def test_restore_resumes_the_clock_on_a_page_it_clocked(self):
        page = FakePage({})
        page.context = type("Ctx", (), {"new_cdp_session": lambda _s, p: None})()
        sd.navigate(page, "http://x/")
        sd.restore(page, "http://x/")
        self.assertIn("resume", page.actions)
        self.assertNotIn(id(page), sd._CLOCKED)


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

    def test_tree_expression_grammar(self):
        tree = ['- button "撤销分配" < table "成员"', '- text: 三个成员']
        self.assertEqual(sd.evaluate_tree('node button "撤销分配" exists', tree)[0], True)
        self.assertEqual(sd.evaluate_tree('node button "撤销" exists', tree)[0], False)
        self.assertEqual(sd.evaluate_tree('node button "撤销分配" absent', tree)[0], False)
        self.assertEqual(sd.evaluate_tree("node text exists", tree)[0], True)
        with self.assertRaises(ValueError):
            sd.evaluate_tree(".a == 1", tree)

    def test_json_expression_grammar(self):
        body = {"a": {"b": [{"c": "x"}]}, "n": 1, "s": "hello"}
        self.assertEqual(sd.evaluate('.a.b[0].c == "x"', body), (True, "x"))
        self.assertEqual(sd.evaluate(".n != 1", body), (False, 1))
        self.assertEqual(sd.evaluate('.s contains "ell"', body), (True, "hello"))

    @unittest.skipIf(shutil.which("jq") is None, "jq not on PATH")
    def test_a_jq_program_runs_with_values_bound_as_variables(self):
        body = {"projects": [{"name": "a", "id": "P1"}, {"name": "b", "id": "P2"}], "n": 2}
        ok, got = sd.evaluate("([.projects[] | select(.id == $project_id)] | length) == 1",
                              body, {"project_id": "P1"})
        self.assertEqual((ok, got), (True, True))
        ok, got = sd.evaluate(".n == $before", body, {"before": "3"})
        self.assertEqual((ok, got), (False, False))
        ok, _ = sd.evaluate("any(.projects[]; .name == $typed_name)", body, {"typed_name": "b"})
        self.assertTrue(ok)

    def test_an_unbound_variable_names_itself(self):
        with self.assertRaises(SystemExit) as raised:
            sd.evaluate(".n == $requested_count", {"n": 1}, {})
        self.assertIn("$requested_count", str(raised.exception))

    def test_exists_and_truthiness_and_a_trailing_note(self):
        body = {"a": {"b": [{"c": "x"}]}, "n": 1, "s": "hello"}
        self.assertEqual(sd.evaluate(".zz exists", body), (False, None))
        self.assertEqual(sd.evaluate(".a", body)[0], True)
        self.assertEqual(sd.evaluate(".n == 1  # the seed lays one", body), (True, 1))


class TestClassSets(unittest.TestCase):
    def test_diff_names_the_element_that_wears_the_class(self):
        d = sd.class_diff({"btn": 'button "开始"', "hot": 'span "!"'}, {"btn": 'button "开始"'})
        self.assertEqual(d["only_in_baseline"], [("hot", 'span "!"')])
        self.assertEqual(d["only_in_impl"], [])
        self.assertEqual(d["changed"], 1)

    def test_runtime_prefixes_are_not_design(self):
        self.assertTrue(all(p in ("sc-", "dc-") for p in sd.RUNTIME_CLASS_PREFIXES))


class FakeAdapter(sd.Adapter):
    """The six capabilities as a record of calls: the judges are tested against this
    shape, so a change to what they ask of an adapter shows here first."""

    kind = "fake"
    reach_before_attach = True

    def __init__(self):
        super().__init__({"reach": "echo", "transport_off": "true", "transport_on": "true"},
                         {}, Path("."))
        self.calls = []

    def transport(self, mechanisms, values, perturb=False):
        self.calls.append(("transport", tuple(mechanisms), perturb))
        return {**values, "project_id": "p1"}

    def attach(self, pw, values):
        self.calls.append(("attach", values.get("project_id")))
        return FakePage({})

    def ready(self):
        self.calls.append(("ready",))
        return True, ""

    def address(self, route, values):
        self.calls.append(("address", route))
        return "app://" + sd.fill(route, values)

    def release(self):
        self.calls.append(("release",))

    def observe(self, line, values):
        self.calls.append(("observe", line))
        return True, None, ""


class TestSixCapabilities(unittest.TestCase):
    def test_each_capability_is_one_call(self):
        a = FakeAdapter()
        values = a.transport(["seed:x"], {}, perturb=True)
        page = a.attach(None, values)
        self.assertTrue(a.ready()[0])
        self.assertEqual(a.address("#/project/{project_id}", values), "app://#/project/p1")
        self.assertTrue(a.observe("GET /x -> .a", values)[0])
        a.release()
        self.assertIsInstance(page, FakePage)
        self.assertEqual([c[0] for c in a.calls],
                         ["transport", "attach", "ready", "address", "observe", "release"])
        self.assertEqual(a.calls[0], ("transport", ("seed:x",), True))

    def test_the_base_transport_runs_the_reach_command_and_reads_key_values(self):
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / "reach.sh"
            script.write_text("#!/bin/sh\necho project_id=p9\necho \"args=$*\"\n")
            script.chmod(0o755)
            a = sd.Adapter({"reach": str(script)}, {}, Path(d))
            values = a.transport(["seed:a", "dev:b"], {"k": "v"}, perturb=True)
        self.assertEqual(values, {"k": "v", "project_id": "p9", "args": "seed:a dev:b --perturb"})
        self.assertEqual(a.transport([], {"k": "v"}), {"k": "v"})

    def test_a_missing_transport_off_is_named(self):
        a = sd.Adapter({"reach": "true"}, {}, Path("."))
        with self.assertRaises(SystemExit) as raised:
            a.transport_off()
        self.assertIn("transport_off", str(raised.exception))

    def test_an_address_the_discover_did_not_print_is_named(self):
        a = sd.ElectronAdapter({"reach": "true"}, {"impl": "http://x/"}, Path("."))
        with self.assertRaises(SystemExit) as raised:
            a.need("cdp")
        self.assertIn("cdp", str(raised.exception))
        self.assertEqual(a.address("#/project/{project_id}", {"project_id": "p1"}),
                         "http://x/#/project/p1")

    def test_the_electron_adapter_refuses_a_tree_observe(self):
        a = sd.ElectronAdapter({"reach": "true"}, {"backend": "http://127.0.0.1:1"}, Path("."))
        ok, _, why = a.observe('GET /x -> node button "y" exists', {})
        self.assertFalse(ok)
        self.assertIn("JSON read surface", why)

    def test_adapter_for_reads_kind_and_refuses_an_unknown_one(self):
        self.assertIn("electron", sd.ADAPTERS)
        self.assertIn("web-server-rendered", sd.ADAPTERS)
        self.assertIn("chrome-extension", sd.ADAPTERS)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit) as raised:
                sd.adapter_for({"target": {"kind": "vt100"}}, Path(d))
            self.assertIn("vt100", str(raised.exception))


class TestTargetConfig(unittest.TestCase):
    def test_target_json_is_required_and_read(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(SystemExit) as raised:
                sd.target_config(root)
            self.assertIn("target.json", str(raised.exception))
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(json.dumps(
                {"discover": "printf %s '{\"cdp\": \"http://127.0.0.1:9229\"}'", "reach": "echo"}))
            cfg = sd.target_config(root)
            self.assertEqual(sd.discover(cfg, root), {"cdp": "http://127.0.0.1:9229"})

    def test_key_values(self):
        self.assertEqual(sd.key_values("project_id=p1\nnoise\ncookie=a=b\n"),
                         {"project_id": "p1", "cookie": "a=b"})


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
        triggers = [("text", "鸭豆余额 12,480")]
        design = '- main:\n  - text: 鸭豆余额 12,480\n  - button "新建商品项目"\n'
        product = '- main:\n  - text: 鸭豆余额 20\n  - button "新建商品项目"\n'
        masked_d = sd.mask_volatile(sd.normalize_aria(design), triggers)
        masked_p = sd.mask_volatile(sd.normalize_aria(product), triggers)
        self.assertEqual(masked_d, masked_p)
        self.assertTrue(any("<volatile>" in line for line in masked_d))
        self.assertFalse(any("12,480" in line or " 20" in line for line in masked_d))
        self.assertEqual(sd.aria_diff(design, product, volatile=triggers)["changed"], 0)
        self.assertGreater(sd.aria_diff(design, product)["changed"], 0)

    def test_volatile_paint_js_fills_the_matching_box_on_both_sides(self):
        js = sd.volatile_paint_js([("text", "鸭豆余额 12,480")])
        self.assertIn(sd.VOLATILE_FILL, js)
        self.assertIn("鸭豆余额 12,480", js)
        self.assertIn("backgroundColor", js)
        scoped = {"volatile_values": [
            {"page": "App · 商品项目库.dc.html",
             "trigger": {"role": "text", "name": "鸭豆余额 12,480"},
             "reason": "wallet balance is an external account; seed does not write it"}]}
        self.assertEqual(sd.volatile_triggers(scoped, "App · 商品项目库.dc.html"),
                         [("text", "鸭豆余额 12,480")])
        self.assertEqual(sd.volatile_triggers(scoped, "Component · 工作台壳.dc.html"), [])

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


class TestBringUp(unittest.TestCase):
    class Stub:
        def __init__(self, answers, cfg, root):
            self.answers, self.cfg, self.root, self.addresses = list(answers), cfg, root, {}

        def ready(self):
            return self.answers.pop(0)

    def test_an_answering_product_is_left_alone(self):
        a = self.Stub([(True, "")], {}, Path("."))
        sd.bring_up(a)

    def test_no_start_declared_names_what_to_declare(self):
        a = self.Stub([(False, "no backend")], {"discover": "x"}, Path("."))
        with self.assertRaises(SystemExit) as raised:
            sd.bring_up(a)
        self.assertIn("`start`", str(raised.exception))

    def test_start_is_run_once_then_discover_and_ready_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {"start": "true",
                   "discover": "printf %s '{\"cdp\": \"http://127.0.0.1:1\"}'"}
            a = self.Stub([(False, "down"), (True, "")], cfg, root)
            sd.bring_up(a)
            self.assertEqual(a.addresses, {"cdp": "http://127.0.0.1:1"})
            self.assertEqual(a.answers, [])

    def test_a_start_that_returns_but_leaves_it_down_is_reported(self):
        cfg = {"start": "true", "discover": "printf %s '{}'"}
        a = self.Stub([(False, "down"), (False, "still down")], cfg, Path("."))
        with self.assertRaises(SystemExit) as raised:
            sd.bring_up(a)
        self.assertIn("still down", str(raised.exception))

