"""The shared driver behind both judges, without a browser: the contract's screen
axis, the seven capabilities against a fake adapter, the box arithmetic, the `open`
chain, the tree's ancestor line, and the two read grammars.
"""

import importlib.util
import json
import os
import sys
import tempfile
import shutil
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts" / "screen_driver.py"
# Every command the driver declares runs with this run's lease in its environment, and
# claiming one writes to a registry `lease.py` fixes at import from `MMW_HOME`. Without a
# registry of its own here, the suite claims real slots and overwrites the record of a
# run that is live — after which `release` refuses, because the ports are still listened
# on, and that slot is lost for good.
HOME = tempfile.mkdtemp(prefix="mmw-screen-driver-home-")


def load():
    """A fresh `screen_driver`, and with it a `lease` bound to `HOME`."""
    with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
        spec = importlib.util.spec_from_file_location("screen_driver", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules["screen_driver"] = module
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
    """Enough of a Playwright page for `perform` and `navigate`.

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


class TestOpenChain(unittest.TestCase):
    ROWS = sd.rows_by_id(CONTRACT)

    def test_a_native_select_takes_select_option_not_fill(self):
        page = FakePage({("combobox", "商品主体图"): 1})
        page.tags = {("combobox", "商品主体图"): "SELECT"}
        sd.perform(page, [{"row": "create-project.subject", "value": "商品主体图 1"}],
                   self.ROWS, {})
        self.assertEqual(page.actions,
                         [("select_option", "combobox", "商品主体图", "商品主体图 1")])

    def test_a_combobox_that_is_not_a_select_still_takes_fill(self):
        page = FakePage({("combobox", "商品主体图"): 1})
        sd.perform(page, [{"row": "create-project.subject", "value": "商品主体图 1"}],
                   self.ROWS, {})
        self.assertEqual(page.actions,
                         [("fill", "combobox", "商品主体图", "商品主体图 1")])

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

    def test_two_same_name_controls_after_clicks_the_second(self):
        """Two buttons share a name. `after` (the previous named node) is the
        heading that sits between them; perform clicks the dialog confirm, not
        the footer. agentflow#675."""
        page = FakePage(named=[
            ("button", "放弃这次任务", "footer"),
            ("heading", "要放弃这次任务吗", "heading"),
            ("button", "放弃这次任务", "dialog"),
        ])
        rows = {"source-setup.abandon.confirm": {
            "trigger": {"role": "button", "name": "放弃这次任务"},
            "after": {"role": "heading", "name": "要放弃这次任务吗"},
        }}
        sd.perform(page, [{"row": "source-setup.abandon.confirm", "value": None}],
                   rows, {})
        self.assertEqual(page.actions, [("click", "button", "放弃这次任务", "dialog")])

    def test_a_digit_sibling_does_not_shift_the_exact_name_index(self):
        """`删除 1` and `删除 2` share a stem. The locator is exact, so the
        trigger `删除 2` is the only match; `after` must not count the sibling
        into `nth`."""
        page = FakePage(named=[
            ("button", "删除 1", "first"),
            ("heading", "确认", "heading"),
            ("button", "删除 2", "second"),
        ])
        rows = {"x.confirm": {
            "trigger": {"role": "button", "name": "删除 2"},
            "after": {"role": "heading", "name": "确认"},
        }}
        sd.perform(page, [{"row": "x.confirm", "value": None}], rows, {})
        self.assertEqual(page.actions, [("click", "button", "删除 2", "second")])

    def test_two_same_name_controls_without_after_stop_the_run(self):
        """The same two buttons with no `after`: the run stops and names the
        coordinate, instead of silently taking the first."""
        page = FakePage({("button", "放弃这次任务"): 2})
        rows = {"source-setup.abandon.confirm": {
            "trigger": {"role": "button", "name": "放弃这次任务"},
        }}
        with self.assertRaises(SystemExit) as raised:
            sd.perform(page, [{"row": "source-setup.abandon.confirm", "value": None}],
                       rows, {})
        self.assertIn('button "放弃这次任务"', str(raised.exception))
        self.assertIn("matches 2 controls", str(raised.exception))
        self.assertIn("after", str(raised.exception))
        self.assertEqual(page.actions, [])


class TestWaitingOnBothClocks(unittest.TestCase):
    """A view that appears when a response arrives, not when a timer fires.

    Running the controlled clock fires the page's timers and returns at once, so a wait
    counted only in virtual milliseconds hands a real request no time at all. Wall time
    is the second budget, spent together with the remaining virtual so a paint after
    the response can still be waited for. Spending wall time is safe: every timer on
    the page is under the controlled clock, so the handoff package's auto-advance
    cannot fire while it passes.
    """

    def setUp(self):
        self.budget = sd.WAIT_REAL_BUDGET_S
        sd.WAIT_REAL_BUDGET_S = 1.0
        self.addCleanup(setattr, sd, "WAIT_REAL_BUDGET_S", self.budget)
        self._clocked_before = set(sd._CLOCKED)
        self.addCleanup(self._drop_clocked)

    def _drop_clocked(self):
        for key in list(sd._CLOCKED):
            if key not in self._clocked_before:
                sd._CLOCKED.pop(key, None)

    def test_a_view_that_arrives_only_in_wall_time_is_found(self):
        page = FakePage({})
        at = time.monotonic() + 0.3
        sd.wait_until(page, lambda: time.monotonic() >= at, "never")

    def test_a_paint_after_a_response_is_found(self):
        """A control that paints on an animation frame after a response arrives.

        Virtual time spent before the response has nothing to paint. The paint
        needs the clock to run after wall time has passed.
        """
        page = FakePage({})
        response_at = time.monotonic() + 0.3
        painted = False

        def run_for(ms):
            nonlocal painted
            page.ran += ms
            if time.monotonic() >= response_at and ms >= sd.FRAME_MS:
                painted = True

        page.run_for = run_for
        sd.wait_until(page, lambda: painted, "no control")
        self.assertTrue(painted)
        self.assertLessEqual(page.ran, sd.SETTLE_BUDGET_MS)

    def test_the_virtual_cap_is_not_exceeded_however_long_the_wait_runs(self):
        """The reason the virtual budget exists — a scene captured one step past itself —
        does not weaken because the wait got longer."""
        page = FakePage({})
        at = time.monotonic() + 0.3
        sd.wait_until(page, lambda: time.monotonic() >= at, "never")
        self.assertLessEqual(page.ran, sd.SETTLE_BUDGET_MS)

    def test_running_out_names_both_budgets(self):
        page = FakePage({})
        with self.assertRaises(SystemExit) as raised:
            sd.wait_until(page, lambda: False, "no control \u767b\u5f55")
        said = str(raised.exception)
        self.assertIn("no control \u767b\u5f55", said, "the refusal names no fact")
        self.assertIn(f"{sd.SETTLE_VIRTUAL_MS + sd.SETTLE_BUDGET_MS} ms of controlled time", said)
        self.assertIn("1s of wall time", said, "a reader cannot tell which budget ran out")

    def test_a_condition_that_never_holds_times_out_within_both_budgets(self):
        page = FakePage({})
        started = time.monotonic()
        with self.assertRaises(SystemExit) as raised:
            sd.wait_until(page, lambda: False, "no control \u767b\u5f55")
        elapsed = time.monotonic() - started
        said = str(raised.exception)
        self.assertIn("no control \u767b\u5f55", said)
        self.assertIn(f"{sd.SETTLE_VIRTUAL_MS + sd.SETTLE_BUDGET_MS} ms of controlled time", said)
        self.assertIn("1s of wall time", said)
        self.assertLess(elapsed, sd.WAIT_REAL_BUDGET_S + 2 * sd.WAIT_REAL_STEP_S)
        self.assertGreaterEqual(elapsed, sd.WAIT_REAL_BUDGET_S - sd.WAIT_REAL_STEP_S)


class TestTimerBasedWaitStaysOffTheWall(unittest.TestCase):
    """A mount that appears on page timers is still found without sleeping on the wall.

    Production `WAIT_REAL_BUDGET_S` is 8 s. Holding the whole virtual budget back
    for frames across that window would stretch a 300 ms timer-based settle across
    seconds of wall time and slow every scene. This case runs at the shipped
    constants and fails if that happens.
    """

    def test_a_view_that_appears_on_timers_does_not_wait_on_the_wall(self):
        page = FakePage({})
        self.addCleanup(sd._CLOCKED.pop, id(page), None)
        started = time.monotonic()
        sd.wait_until(page, lambda: page.ran >= 300, "no mount")
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertLessEqual(page.ran, sd.SETTLE_BUDGET_MS)
        self.assertGreaterEqual(page.ran, 300)


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
    """The seven capabilities as a record of calls: the judges are tested against this
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

    def transport_off(self):
        self.calls.append(("transport_off",))

    def observe(self, line, values):
        self.calls.append(("observe", line))
        return True, None, ""


class TestSevenCapabilities(unittest.TestCase):
    def test_each_capability_is_one_call(self):
        a = FakeAdapter()
        values = a.transport(["seed:x"], {}, perturb=True)
        page = a.attach(None, values)
        self.assertTrue(a.ready()[0])
        self.assertEqual(a.address("#/project/{project_id}", values), "app://#/project/p1")
        self.assertTrue(a.observe("GET /x -> .a", values)[0])
        a.transport_off()
        a.release()
        self.assertIsInstance(page, FakePage)
        self.assertEqual([c[0] for c in a.calls],
                         ["transport", "attach", "ready", "address", "observe",
                          "transport_off", "release"])
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

    def test_a_row_trigger_index_is_exact_name_not_stem(self):
        """`get_by_role(..., exact=True)` sees one `删除 2`. Stem matching
        would also count `删除 1` and hand `nth(1)` an empty locator."""
        lines = sd.normalize_aria(
            '- button "删除 1"\n'
            '- heading "确认"\n'
            '- button "删除 2"\n'
        )
        pinned = sd.VolatileTrigger("button", "删除 2", ("heading", "确认"))
        self.assertEqual(sd.trigger_hit_indices(lines, pinned), [0])
        self.assertEqual(sd.count_trigger_hits(lines, pinned), 1)
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


class WhichClassADefectIs(unittest.TestCase):
    """`TriggerConflict.kind` is the one place a tree becomes a class, so the contract
    lint, the ticket lint and the merge rule cannot disagree about the same row."""

    def conflict(self, aria: str, role: str, name: str):
        lines = sd.normalize_aria(aria)
        trigger = sd.VolatileTrigger(role, name)
        return sd.TriggerConflict("r", "p", sd.count_trigger_hits(lines, trigger),
                                  sd.trigger_after_candidates(lines, trigger))

    def test_matches_with_different_neighbours_are_pinned_by_after(self):
        """The footer button and the dialog's follow different named nodes, and naming
        one says which control the row means."""
        c = self.conflict(
            '- heading "商品主体确认"\n'
            '- button "放弃这次任务"\n'
            '- heading "要放弃这次任务吗"\n'
            '- button "继续这次任务"\n'
            '- button "放弃这次任务"\n',
            "button", "放弃这次任务")
        self.assertEqual(c.hits, 2)
        self.assertEqual(c.kind, sd.PIN_AFTER)
        self.assertIn(("button", "继续这次任务"), c.candidates)

    def test_matches_in_repeated_blocks_have_no_named_node_to_pin(self):
        """Two config items the design draws identically: the node before each match is
        the same, so no `after` can split them."""
        c = self.conflict(
            '- text: 参考图\n'
            '- button "使用说明"\n'
            '- button "添加参考图"\n'
            '- text: 参考图\n'
            '- button "使用说明"\n'
            '- button "添加参考图"\n',
            "button", "添加参考图")
        self.assertEqual(c.hits, 2)
        self.assertEqual(c.kind, sd.PIN_OCCURRENCE)
        self.assertEqual([n for _, n in c.candidates], ["使用说明"])

    def test_a_match_with_nothing_before_it_is_still_told_apart_by_after(self):
        """The first named node of a scene has nothing before it, and every `after`
        excludes it — which is exactly how a row meaning the other match says so. What
        makes a row positional is every match following the *same* node, not one of them
        following none."""
        c = self.conflict(
            '- button "导出"\n'
            '- heading "任务详情"\n'
            '- button "导出"\n',
            "button", "导出")
        self.assertEqual(c.hits, 2)
        self.assertEqual(c.kind, sd.PIN_AFTER)

    def test_a_class_is_one_of_the_three_names_a_program_branches_on(self):
        self.assertEqual(
            sorted({sd.PIN_AFTER, sd.PIN_OCCURRENCE, sd.NEEDS_DECISION}),
            ["decision", "pin-after", "pin-occurrence"])


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



class TestInstanceIdentity(unittest.TestCase):
    """`ready` means answering **and** mine.

    Liveness is not identity, and on a machine running several worktrees the difference
    is the whole of the risk: a driver that accepts any answer measures another run's
    code and reports the verdict as this ticket's. It also skips `start`, so the
    repository's own "another checkout holds these ports" guard never runs.
    """

    def adapter(self, addresses, answer):
        a = FakeAdapter()
        a.addresses = addresses
        a.observe = lambda line, values: answer
        return a

    def test_a_target_that_declares_no_check_is_unchanged(self):
        a = self.adapter({}, (False, None, "never asked"))
        self.assertEqual(a.instance_ok(), (True, ""))

    def test_the_declared_check_passing_is_the_whole_of_it(self):
        a = self.adapter({"instance_check": "GET /health -> .token == \"abc\"",
                          "instance": "issue-640"}, (True, "abc", ""))
        self.assertEqual(a.instance_ok(), (True, ""))

    def test_another_run_holding_the_addresses_is_caught(self):
        a = self.adapter({"instance_check": "GET /health -> .token == \"abc\"",
                          "instance": "issue-640"}, (False, "zzz", ".token was \"zzz\""))
        ok, why = a.instance_ok()
        self.assertFalse(ok)
        self.assertIn("issue-640", why, "the refusal names no fact")
        self.assertIn("blocked", why, "the refusal names no next step")
        self.assertLessEqual(len(why), 256)

    def test_a_check_that_cannot_be_read_is_a_refusal_not_a_pass(self):
        a = FakeAdapter()
        a.addresses = {"instance_check": "GET /health -> .token", "instance": "issue-640"}

        def boom(line, values):
            raise RuntimeError("connection refused")

        a.observe = boom
        ok, why = a.instance_ok()
        self.assertFalse(ok, "an unreadable check must not read as a pass")
        self.assertIn("blocked", why)
        self.assertLessEqual(len(why), 256)

    def test_every_adapter_asks_it(self):
        """The hole was in the capability, not in one kind of product."""
        import inspect
        for cls in (sd.ElectronAdapter, sd.WebAdapter):
            with self.subTest(adapter=cls.__name__):
                self.assertIn("instance_ok", inspect.getsource(cls.ready))


class TestTargetCheck(unittest.TestCase):
    """`screen_driver.py target --check` is the setup-time bar for one repository: it
    names every field of `.mmw/target.json` still to answer, and passes once the file
    is complete. The runtime reader `target_config` keeps its smaller bar."""

    COMPLETE = {"start": "s", "stop": "t", "discover": "d", "reach": "r",
                "transport_off": "off", "transport_on": "on", "leaves_machine": []}

    def run_target(self, *argv):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sd.target_main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_kinds_are_the_adapters(self):
        code, out, _ = self.run_target("--kinds")
        self.assertEqual(code, 0)
        self.assertEqual(out.split(), sorted(sd.ADAPTERS))

    def test_a_repository_without_the_file_is_told_every_required_field(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = self.run_target("--check", "--repo", d, "--kind", "electron")
        self.assertEqual(code, 1)
        for f in sd.FIELDS:
            self.assertIn(("  missing  " if f.required else "  absent   ") + f.key, out)
        self.assertIn("ElectronAdapter", out)
        self.assertIn("cdp", out)
        self.assertIn("e.g.", out)

    def test_a_complete_file_passes_and_optional_keys_stay_optional(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            (Path(d) / ".mmw" / "target.json").write_text(json.dumps(self.COMPLETE))
            code, out, _ = self.run_target("--check", "--repo", d, "--kind", "web-spa")
            self.assertEqual(code, 0, out)
            self.assertIn("complete", out)
            code, out, _ = self.run_target("--validate", "--repo", d, "--kind", "web-spa")
            self.assertEqual(code, 0, out)

    def test_validate_names_the_first_problem_and_counts_the_rest(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            cfg = dict(self.COMPLETE)
            cfg["start"] = ""
            cfg["leaves_machine"] = "browser"
            (Path(d) / ".mmw" / "target.json").write_text(json.dumps(cfg))
            code, out, _ = self.run_target("--validate", "--repo", d, "--kind", "electron")
        self.assertEqual(code, 1)
        self.assertIn("start must be a non-empty command", out)
        self.assertIn("(+1 more)", out)

    def test_a_wrong_instance_shape_is_named(self):
        cfg = dict(self.COMPLETE)
        cfg["instance"] = {"max": 0}
        problems = sd.target_problems("electron", cfg)
        self.assertEqual([k for k, _ in problems], ["instance"])

    def test_a_file_that_is_not_json_is_a_fault_not_absence(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".mmw").mkdir()
            (Path(d) / ".mmw" / "target.json").write_text("{bad")
            code, _, err = self.run_target("--check", "--repo", d, "--kind", "electron")
        self.assertEqual(code, 2)
        self.assertIn("cannot be read as JSON", err)

    def test_an_unknown_kind_is_refused_first(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = self.run_target("--validate", "--repo", d, "--kind", "vt100")
        self.assertEqual(code, 1)
        self.assertIn("target.kind", out)

    def test_the_kind_is_read_from_the_one_contract(self):
        with tempfile.TemporaryDirectory() as d:
            spec = Path(d) / "docs" / "specs" / "x"
            spec.mkdir(parents=True)
            (spec / "screen-contract.yaml").write_text("target:\n  kind: web-server-rendered\n")
            code, out, _ = self.run_target("--check", "--repo", d)
        self.assertEqual(code, 1)
        self.assertIn("target.kind: web-server-rendered", out)

    def test_the_runtime_refusal_names_the_check_command(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit) as raised:
                sd.target_config(Path(d))
        self.assertIn("target --check", str(raised.exception))

