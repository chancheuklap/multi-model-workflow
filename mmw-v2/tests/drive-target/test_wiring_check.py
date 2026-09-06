"""The wiring check's negative control, without a browser.

`transport_off` is the row's own write, not the path that put the control on
screen; a row that never reaches an observe assertion does not stop the rest;
a positive run does not break the transport.
"""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import yaml

from test_screen_driver import FakeAdapter, FakePage

SCRIPT = (Path(__file__).resolve().parents[2] / "skills" / "drive-target"
          / "scripts" / "wiring-check.py")


def load():
    spec = importlib.util.spec_from_file_location("wiring_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["wiring_check"] = module
    spec.loader.exec_module(module)
    return module


wc = load()


def _playwright_modules():
    pw = types.ModuleType("playwright")
    sync = types.ModuleType("playwright.sync_api")

    class _CM:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    sync.sync_playwright = lambda: _CM()
    return {"playwright": pw, "playwright.sync_api": sync}


class DrivePage(FakePage):
    """The existing fake page, with a mount box and clicks on the adapter timeline."""

    def __init__(self, calls, *, mount=True, named=None):
        super().__init__(named=named)
        self.calls = calls
        self.mount_present = mount

    def set_viewport_size(self, size):
        self.calls.append(("resize", size["width"], size["height"]))

    def evaluate(self, js, selector=None):
        if self.mount_present:
            return {"x": 0, "y": 0, "width": 100, "height": 100}
        return None

    def get_by_role(self, role, name=None, exact=False):
        locator = super().get_by_role(role, name, exact)
        calls = self.calls
        orig = locator.click

        def click(timeout=None):
            calls.append(("click", role, name))
            return orig(timeout=timeout)

        locator.click = click
        return locator


class RecordingAdapter(FakeAdapter):
    """FakeAdapter plus `transport_on`, a broken flag, and a queue of pages."""

    def __init__(self, pages, calls, *, hold_when_broken=(), surface_error=(),
                 refuse_reach=False):
        super().__init__()
        self.calls = calls
        self._pages = list(pages)
        self.broken = False
        self.hold_when_broken = set(hold_when_broken)
        self.surface_error = set(surface_error)
        self.refuse_reach = refuse_reach

    def attach(self, pw, values):
        self.calls.append(("attach",))
        if len(self._pages) > 1:
            return self._pages.pop(0)
        return self._pages[0]

    def transport(self, mechanisms, values, perturb=False):
        if self.refuse_reach:
            raise SystemExit(wc.sd.refusal(
                "`reach` exited 1: boom",
                "The repository's declared command did not succeed.",
                wc.sd.REPORT_BLOCKED))
        return super().transport(mechanisms, values, perturb)

    def transport_off(self):
        self.calls.append(("transport_off",))
        self.broken = True

    def transport_on(self):
        self.calls.append(("transport_on",))
        self.broken = False

    def observe(self, line, values):
        self.calls.append(("observe", str(line), self.broken))
        if str(line) in self.surface_error:
            op = str(line).split(" ->", 1)[0].strip()
            return False, 503, f"{op} answered 503"
        if self.broken and str(line) not in self.hold_when_broken:
            return False, None, f"{line} was missing"
        return True, None, ""


DOC = {
    "target": {"kind": "electron"},
    "viewports": ["1440x900"],
    "baselines": {"look": "handoff"},
    "pages": {
        "Component · 门禁一.dc.html": {"mount": "gate-one",
                                      "route": "#/gate/{project_id}"},
        "Component · 通过.dc.html": {"mount": "ok-screen",
                                    "route": "#/ok/{project_id}"},
    },
    "scenes": {
        "gate.one": {"page": "Component · 门禁一.dc.html", "reach": ["seed:gate"]},
        "ok.scene": {"page": "Component · 通过.dc.html", "reach": ["seed:ok"]},
    },
    "rows": [
        {"id": "gate-one.confirm",
         "trigger": {"role": "button", "name": "确认报价"},
         "scenes": ["gate.one"],
         "drive": {"open": ["gate-one.reveal"]},
         "observe": ["GET /quote -> .price exists"]},
        {"id": "gate-one.reveal",
         "trigger": {"role": "button", "name": "打开报价"},
         "scenes": ["gate.one"]},
        {"id": "ok.save",
         "trigger": {"role": "button", "name": "保存"},
         "scenes": ["ok.scene"],
         "observe": ["GET /y -> .saved == true"]},
    ],
}

SCENES_JSON = [
    {"name": "gate.one", "page": "Component · 门禁一.dc.html",
     "props": {"scenario": "default"}},
    {"name": "ok.scene", "page": "Component · 通过.dc.html",
     "props": {"scenario": "default"}},
]


class TestNegativeControl(unittest.TestCase):
    def setUp(self):
        self._clocked_before = set(wc.sd._CLOCKED)
        self.addCleanup(self._drop_clocked)
        self._observe_budget = wc.OBSERVE_BUDGET_S
        self._observe_step = wc.OBSERVE_STEP_S
        self._wait = wc.sd.WAIT_REAL_BUDGET_S
        wc.OBSERVE_BUDGET_S = 0
        wc.OBSERVE_STEP_S = 0
        wc.sd.WAIT_REAL_BUDGET_S = 0
        self.addCleanup(setattr, wc, "OBSERVE_BUDGET_S", self._observe_budget)
        self.addCleanup(setattr, wc, "OBSERVE_STEP_S", self._observe_step)
        self.addCleanup(setattr, wc.sd, "WAIT_REAL_BUDGET_S", self._wait)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "handoff").mkdir()
        (root / "handoff" / "scenes.json").write_text(
            json.dumps(SCENES_JSON), encoding="utf-8")
        self.contract = root / "screen-contract.yaml"
        self.contract.write_text(
            yaml.safe_dump(DOC, allow_unicode=True, sort_keys=False),
            encoding="utf-8")
        self.root = root

    def _drop_clocked(self):
        for key in list(wc.sd._CLOCKED):
            if key not in self._clocked_before:
                wc.sd._CLOCKED.pop(key, None)

    def _run(self, adapter, rows, negative=False):
        argv = ["--contract", str(self.contract), "--rows", rows]
        if negative:
            argv.append("--negative")
        with mock.patch.dict(sys.modules, _playwright_modules()), \
             mock.patch.object(wc.sd, "adapter_for", return_value=adapter), \
             mock.patch.object(wc.sd, "repo_root", return_value=self.root):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = wc.main(argv)
                except SystemExit as exc:
                    if isinstance(exc.code, int):
                        code = exc.code
                    else:
                        code = 1
                        if exc.code:
                            err.write(str(exc.code) + "\n")
        return code, out.getvalue(), err.getvalue()

    def test_transport_off_runs_after_reach_before_the_row_action(self):
        """Reach and `drive.open` write; the row's own click and `observe` do not."""
        calls = []
        page = DrivePage(calls, named=[
            ("button", "打开报价"),
            ("button", "确认报价"),
            ("button", "保存"),
        ])
        adapter = RecordingAdapter([page], calls)
        code, out, err = self._run(adapter, "gate-one.confirm,ok.save", negative=True)
        self.assertEqual(code, 0, err + out)
        self.assertIn("WIRING NEGATIVE OK 2/2", out)
        kinds = [c[0] if isinstance(c, tuple) else c for c in calls]
        off = kinds.index("transport_off")
        self.assertEqual(kinds[:off].count("transport"), 1, calls)
        self.assertIn(("click", "button", "打开报价"), calls[:off])
        self.assertNotIn(("click", "button", "确认报价"), calls[:off])
        self.assertEqual(calls[off], ("transport_off",))
        after = calls[off + 1:]
        self.assertIn(("click", "button", "确认报价"), after)
        self.assertIn(("observe", "GET /quote -> .price exists", True), after)
        on = kinds.index("transport_on")
        second_off = kinds.index("transport_off", on)
        self.assertIn(("transport", ("seed:ok",), False), calls[on:second_off])
        self.assertTrue(calls[kinds.index("observe", second_off)][2])
        self.assertEqual(kinds.count("transport_off"), 2, calls)
        self.assertEqual(kinds.count("transport_on"), 2, calls)
        last_on = max(i for i, k in enumerate(kinds) if k == "transport_on")
        last_release = max(i for i, k in enumerate(kinds) if k == "release")
        self.assertLess(last_on, last_release, calls)

    def test_an_unevaluated_row_does_not_stop_the_rest_and_exits_2(self):
        """A mount that never appears is one unevaluated row, not the whole run."""
        calls = []
        missing = DrivePage(calls, mount=False, named=[("button", "确认报价"),
                                                       ("button", "打开报价")])
        present = DrivePage(calls, named=[("button", "保存")])
        adapter = RecordingAdapter([missing, present], calls)
        code, out, err = self._run(adapter, "gate-one.confirm,ok.save", negative=True)
        self.assertEqual(code, 2, err + out)
        self.assertIn("negative control proved nothing", err)
        self.assertIn("no observe line was evaluated for gate-one.confirm (", err)
        self.assertIn(("observe", "GET /y -> .saved == true", True), calls)
        self.assertNotIn(("observe", "GET /quote -> .price exists", True), calls)
        self.assertNotIn(("observe", "GET /quote -> .price exists", False), calls)

    def test_a_missing_trigger_restores_the_transport_before_the_next_reach(self):
        """The row's own click fails after `transport_off`; the next reach is intact."""
        calls = []
        no_trigger = DrivePage(calls, named=[("button", "打开报价")])
        present = DrivePage(calls, named=[("button", "保存")])
        adapter = RecordingAdapter([no_trigger, present], calls)
        code, out, err = self._run(adapter, "gate-one.confirm,ok.save", negative=True)
        self.assertEqual(code, 2, err + out)
        self.assertIn("no observe line was evaluated for gate-one.confirm (", err)
        kinds = [c[0] if isinstance(c, tuple) else c for c in calls]
        off = kinds.index("transport_off")
        on = kinds.index("transport_on")
        self.assertLess(off, on, calls)
        self.assertIn(("transport", ("seed:ok",), False), calls[on:])
        self.assertIn(("observe", "GET /y -> .saved == true", True), calls)

    def test_a_positive_run_does_not_break_the_transport(self):
        calls = []
        page = DrivePage(calls, named=[
            ("button", "打开报价"),
            ("button", "确认报价"),
        ])
        adapter = RecordingAdapter([page], calls)
        code, out, err = self._run(adapter, "gate-one.confirm")
        self.assertEqual(code, 0, err + out)
        self.assertIn("WIRING OK 1/1", out)
        kinds = [c[0] if isinstance(c, tuple) else c for c in calls]
        self.assertNotIn("transport_off", kinds)
        self.assertNotIn("transport_on", kinds)
        self.assertIn(("observe", "GET /quote -> .price exists", False), calls)
        self.assertIn(("click", "button", "确认报价"), calls)
        self.assertIn(("click", "button", "打开报价"), calls)
        self.assertLess(kinds.index("transport"), kinds.index("observe"))

    def test_a_positive_run_still_stops_on_an_unreachable_row(self):
        calls = []
        missing = DrivePage(calls, mount=False, named=[("button", "打开报价"),
                                                       ("button", "确认报价")])
        present = DrivePage(calls, named=[("button", "保存")])
        adapter = RecordingAdapter([missing, present], calls)
        code, out, err = self._run(adapter, "gate-one.confirm,ok.save")
        self.assertNotEqual(code, 0, err + out)
        self.assertIn("no visible element matches", err)
        self.assertNotIn(("transport", ("seed:ok",), False), calls)
        self.assertNotIn("transport_off", [c[0] if isinstance(c, tuple) else c
                                           for c in calls])

    def test_a_read_surface_error_is_not_an_observe_assertion(self):
        calls = []
        page = DrivePage(calls, named=[
            ("button", "打开报价"),
            ("button", "确认报价"),
        ])
        adapter = RecordingAdapter(
            [page], calls, surface_error={"GET /quote -> .price exists"})
        code, out, err = self._run(adapter, "gate-one.confirm", negative=True)
        self.assertEqual(code, 2, err + out)
        self.assertIn("no observe line was evaluated for gate-one.confirm (", err)
        self.assertIn("answered 503", err)
        self.assertNotIn("WIRING NEGATIVE OK", out)

    def test_exit_2_names_a_row_that_stayed_green(self):
        calls = []
        missing = DrivePage(calls, mount=False, named=[("button", "打开报价"),
                                                       ("button", "确认报价")])
        present = DrivePage(calls, named=[("button", "保存")])
        adapter = RecordingAdapter(
            [missing, present], calls,
            hold_when_broken={"GET /y -> .saved == true"})
        code, out, err = self._run(adapter, "gate-one.confirm,ok.save", negative=True)
        self.assertEqual(code, 2, err + out)
        self.assertIn("no observe line was evaluated for gate-one.confirm (", err)
        self.assertIn("GREEN WITHOUT TRANSPORT ok.save", err)

    def test_a_reach_refusal_does_not_tell_the_run_to_stop(self):
        calls = []
        page = DrivePage(calls, named=[("button", "保存")])
        adapter = RecordingAdapter([page], calls, refuse_reach=True)
        code, out, err = self._run(adapter, "ok.save", negative=True)
        self.assertEqual(code, 2, err + out)
        self.assertIn("MISS ok.save", err)
        self.assertNotIn("Report the ticket blocked", err)
