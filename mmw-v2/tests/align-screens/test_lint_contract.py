"""The screen-axis rules of `lint_contract.py`: one positive and one negative case each,
over a small handoff package written into a temporary repository."""

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest

import yaml
from contextlib import redirect_stdout
import subprocess
import io
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "align-screens" / "scripts" / "lint_contract.py"
spec = importlib.util.spec_from_file_location("lint_contract", SCRIPT)
lc = importlib.util.module_from_spec(spec)
sys.modules["lint_contract"] = lc
spec.loader.exec_module(lc)

# The drive-target scripts the lint asks for its matching and its target kinds.
TOOLS_DIR = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts"

PAGE_A = "Component · 新建商品项目.dc.html"
PAGE_B = "Component · 壳头.dc.html"
PAGE_APP = "App · 商品项目库.dc.html"

SKELETON = {
    "scene_pages": {"empty": PAGE_A, "material-added": PAGE_A, "shell-header.ready": PAGE_B,
                    "library.ready": PAGE_APP},
    "table": [
        {"page": PAGE_A, "role": "button", "name": "添加商品素材", "scenes": ["empty"]},
        {"page": PAGE_A, "role": "textbox", "name": "商品名称", "scenes": ["empty", "material-added"]},
        {"page": PAGE_B, "role": "button", "name": "登录", "scenes": ["shell-header.ready"]},
    ],
}


def contract():
    return {
        "effort": "x",
        "baselines": {"look": "handoff"},
        "target": {"kind": "electron"},
        "viewports": ["1440x900", "1180x720"],
        "pages": {
            PAGE_A: {"mount": "create-project", "route": "#/new-project",
                     "component": "features/project-setup/CreateProjectView"},
            PAGE_B: {"mount": "shell-header", "route": "#/",
                     "component": "renderer/components/ShellHeader"},
            PAGE_APP: {"mount": "library-app", "route": "#/"},
        },
        "mechanisms": {
            "seed:library-ready": {"via": "api", "built_by": "#637"},
            "seed:draft-existing": {"via": "storage", "built_by": "#639", "proven_by": "#639 AC4"},
        },
        "scenes": {
            "empty": {"page": PAGE_A, "reach": ["seed:library-ready"]},
            "material-added": {"page": PAGE_A, "reach": ["seed:draft-existing"],
                               "open": [{"row": "create-project.name", "value": "x"}]},
            "shell-header.ready": {"page": PAGE_B, "reach": ["seed:library-ready"]},
            "library.ready": {"page": PAGE_APP, "reach": ["seed:library-ready"]},
        },
        "rows": [
            {"id": "create-project.add-material",
             "component": "features/project-setup/CreateProjectView",
             "trigger": {"role": "button", "name": "添加商品素材"}, "precondition": {},
             "scenes": ["empty"], "calls": ["ipc x"], "shows": {}, "next": "material-added",
             "route": "#/new-project", "observe": [],
             "on_failure": {"cancelled": "stay"},
             "source": ["#537 Implementation Decisions 2", "ADR-0021"],
             "reach": "seed:library-ready", "gap": "aligned"},
            {"id": "create-project.name",
             "component": "features/project-setup/CreateProjectView",
             "trigger": {"role": "textbox", "name": "商品名称"}, "precondition": {},
             "scenes": ["empty", "material-added"], "calls": ["none"], "shows": {},
             "next": "material-added", "source": ["#537 Implementation Decisions 2"],
             "reach": "seed:library-ready", "gap": "aligned"},
            {"id": "shell.sign-in", "component": "renderer/components/ShellHeader",
             "trigger": {"role": "button", "name": "登录"}, "precondition": {},
             "scenes": ["shell-header.ready"], "calls": ["ipc y"], "shows": {},
             "next": "app-awaiting-browser", "route": "#/", "observe": [],
             "on_failure": {"failed": "toast"},
             "source": ["#536 Implementation Decisions 3"],
             "reach": "seed:library-ready", "gap": "aligned"},
        ],
    }


class Repo:
    """A temporary repository: `.git`, a handoff package with two pages and a stylesheet
    carrying a breakpoint, and the spec directory the contract lives in."""

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".git").mkdir()
        self.baseline = self.root / "handoff"
        (self.baseline / "styles").mkdir(parents=True)
        (self.baseline / "styles" / "w.css").write_text(
            "@media (max-width: 1100px) { a { b: c } }\n@media (prefers-reduced-motion: reduce) {}")
        scenes = [{"name": n, "page": p, "props": {}} for n, p in SKELETON["scene_pages"].items()]
        (self.baseline / "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False))
        for page in (PAGE_A, PAGE_B, PAGE_APP):
            (self.baseline / page).write_text(f"<html>{page}</html>")
        self.spec_dir = self.root / "docs" / "specs" / "x"
        self.spec_dir.mkdir(parents=True)
        self.contract = self.spec_dir / "screen-contract.yaml"
        mmw = self.root / ".mmw"
        mmw.mkdir()
        (mmw / "target.json").write_text(json.dumps({
            "start": "s", "stop": "t", "discover": "d", "reach": "r",
            "transport_off": "off", "transport_on": "on", "leaves_machine": [],
        }))

    def write_targets(self, stale_page=None):
        targets = self.spec_dir / "targets"
        targets.mkdir(exist_ok=True)
        scenes_hash = hashlib.sha256((self.baseline / "scenes.json").read_bytes()).hexdigest()
        for page in (PAGE_A, PAGE_B, PAGE_APP):
            page_hash = hashlib.sha256((self.baseline / page).read_bytes()).hexdigest()
            if page == stale_page:
                page_hash = "0" * 64
            for suffix in (".aria", ".classes"):
                (targets / (page[:-len(".dc.html")] + suffix)).write_text(
                    f"# x\n# derived\n# scenes.json sha256={scenes_hash}\n# page sha256={page_hash}\n")

    def cleanup(self):
        self.dir.cleanup()


class TestScreenAxis(unittest.TestCase):
    def setUp(self):
        # The target kinds and the .mmw/target.json check are the drive-target skill's;
        # the lint reaches them through --tools, the way the agent passes them.
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()

    def tearDown(self):
        self.repo.cleanup()

    def lint(self, doc):
        errors, warnings = lc.lint_screen_axis(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        return errors, warnings

    def test_a_complete_contract_has_no_errors(self):
        errors, _ = self.lint(contract())
        self.assertEqual(errors, [])

    def test_target_kind_is_checked_and_adapter_is_an_error(self):
        doc = contract()
        doc["target"] = {"kind": "vt100", "adapter": "verify-ticket/references/targets/nope.md"}
        errors, warnings = self.lint(doc)
        self.assertTrue(any("target.kind" in e for e in errors))
        self.assertTrue(any("target.adapter" in e for e in errors))
        self.assertFalse(any("target.adapter" in w for w in warnings))

    def test_missing_target_json_is_a_warning(self):
        (self.repo.root / ".mmw" / "target.json").unlink()
        errors, warnings = self.lint(contract())
        self.assertFalse(any("target.json" in e for e in errors), errors)
        self.assertTrue(any("no .mmw/target.json" in w and "target --check" in w
                            for w in warnings), warnings)

    def test_an_incomplete_target_json_is_an_error(self):
        (self.repo.root / ".mmw" / "target.json").write_text('{"start": "s"}')
        errors, _ = self.lint(contract())
        self.assertTrue(any("start" in e or "missing" in e or "target.json" in e
                            for e in errors), errors)

    def test_target_validate_exit_2_is_an_error(self):
        (self.repo.root / ".mmw" / "target.json").write_text("{bad")
        errors, _ = self.lint(contract())
        self.assertTrue(any("cannot be read as JSON" in e or "exited 2" in e for e in errors),
                        errors)

    def test_a_viewport_on_a_breakpoint(self):
        doc = contract()
        doc["viewports"] = ["1100x720"]
        errors, _ = self.lint(doc)
        self.assertTrue(any("1100 is a breakpoint" in e for e in errors))
        doc["viewports"] = ["1440x900"]
        self.assertFalse(any("breakpoint" in e for e in self.lint(doc)[0]))

    def test_every_page_declares_mount_and_route(self):
        doc = contract()
        del doc["pages"][PAGE_B]
        errors, _ = self.lint(doc)
        self.assertTrue(any(f"no declaration for {PAGE_B!r}" in e for e in errors))
        doc = contract()
        doc["pages"][PAGE_A]["route"] = ""
        self.assertTrue(any("has no route" in e for e in self.lint(doc)[0]))

    def test_component_pages_map_one_to_one_onto_component_values(self):
        doc = contract()
        doc["pages"][PAGE_B]["component"] = "features/project-setup/CreateProjectView"
        errors, _ = self.lint(doc)
        self.assertTrue(any("claimed by both" in e for e in errors))
        self.assertTrue(any("renderer/components/ShellHeader" in e and "belongs to no Component page" in e
                            for e in errors))
        doc = contract()
        del doc["pages"][PAGE_B]["component"]
        self.assertTrue(any("names no `component`" in e for e in self.lint(doc)[0]))

    def test_app_pages_are_exempt_from_the_component_rule(self):
        doc = contract()
        self.assertNotIn("component", doc["pages"][PAGE_APP])
        self.assertEqual(self.lint(doc)[0], [])

    def test_two_pages_cannot_share_a_mount(self):
        doc = contract()
        doc["pages"][PAGE_B]["mount"] = "create-project"
        self.assertTrue(any("declared by both" in e for e in self.lint(doc)[0]))

    def test_every_scene_once_and_on_its_page(self):
        doc = contract()
        del doc["scenes"]["empty"]
        self.assertTrue(any("no declaration for 'empty'" in e for e in self.lint(doc)[0]))
        doc = contract()
        doc["scenes"]["ghost"] = {"page": PAGE_A}
        self.assertTrue(any("'ghost' is not in scenes.json" in e for e in self.lint(doc)[0]))
        doc = contract()
        doc["scenes"]["empty"]["page"] = PAGE_B
        self.assertTrue(any("scenes.json has" in e for e in self.lint(doc)[0]))

    def test_a_scene_mount_override_must_be_declared_somewhere(self):
        doc = contract()
        doc["scenes"]["material-added"]["mount"] = "library-app"
        self.assertEqual(self.lint(doc)[0], [])
        doc["scenes"]["material-added"]["mount"] = "nowhere"
        self.assertTrue(any("declared by no page" in e for e in self.lint(doc)[0]))

    def test_reach_resolves_to_the_mechanism_table(self):
        doc = contract()
        doc["scenes"]["empty"]["reach"] = ["seed:unknown"]
        self.assertTrue(any("not in mechanisms" in e for e in self.lint(doc)[0]))

    def test_the_open_chain(self):
        doc = contract()
        doc["scenes"]["material-added"]["open"] = ["no.such"]
        self.assertTrue(any("names no row" in e for e in self.lint(doc)[0]))
        doc = contract()
        doc["scenes"]["material-added"]["open"] = ["create-project.name"]
        self.assertTrue(any("carries no value" in e for e in self.lint(doc)[0]))
        doc = contract()
        doc["scenes"]["empty"]["open"] = ["shell.sign-in"]   # lands another page, not visible here
        errors, _ = self.lint(doc)
        self.assertTrue(any("does not land this scene" in e for e in errors))

    def test_an_observed_row_must_be_actionable_on_its_driving_scene(self):
        skeleton = dict(SKELETON)
        skeleton["trees"] = {"empty": ['- button "添加商品素材" [disabled]', '- textbox "商品名称"'],
                             "material-added": ['- button "添加商品素材"', "- textbox: 晨雾保温杯"]}
        doc = contract()
        doc["rows"][0]["observe"] = ["GET /api/x -> .ok == true"]
        errors, warnings = lc.lint_screen_axis(doc, skeleton, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("[disabled] on its driving scene empty" in e for e in errors), errors)
        # a drive.open makes it actionable
        doc["rows"][0]["drive"] = {"open": [{"row": "create-project.name", "value": "x"}]}
        errors, _ = lc.lint_screen_axis(doc, skeleton, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("driving scene" in e for e in errors), errors)
        # or another driving scene where the design shows it enabled
        doc["rows"][0]["drive"] = {"scene": "material-added"}
        doc["rows"][0]["scenes"] = ["empty", "material-added"]
        errors, _ = lc.lint_screen_axis(doc, skeleton, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("driving scene" in e for e in errors), errors)
        doc["rows"][0]["drive"] = {"scene": "shell-header.ready"}
        errors, _ = lc.lint_screen_axis(doc, skeleton, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("not one of the row's scenes" in e for e in errors))
        doc["rows"][0]["drive"] = {"scene": "no-such-scene", "open": ["create-project.name"]}
        errors, _ = lc.lint_screen_axis(doc, skeleton, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("not a declared scene" in e for e in errors))

    def test_a_typed_value_the_design_shows_needs_an_open_step(self):
        skeleton = dict(SKELETON)
        skeleton["trees"] = {"empty": ["- textbox: 晨雾保温杯"], "material-added": ["- textbox: 晨雾保温杯"]}
        _, warnings = lc.lint_screen_axis(contract(), skeleton, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("scene empty:" in w and "types anything" in w for w in warnings), warnings)
        self.assertFalse(any("scene material-added:" in w for w in warnings), warnings)

    def test_open_may_land_through_a_failure_or_the_same_page(self):
        doc = contract()
        doc["rows"][0]["next"] = "material-added"
        doc["rows"][0]["on_failure"] = {"dup": "empty (form kept)"}
        doc["scenes"]["empty"]["open"] = ["create-project.add-material"]   # on_failure names it
        self.assertEqual(self.lint(doc)[0], [])
        doc["rows"][0]["on_failure"] = {"dup": "other"}
        self.assertEqual(self.lint(doc)[0], [])   # next is a scene on the same page
        doc["scenes"]["shell-header.ready"]["open"] = ["create-project.add-material"]
        errors, _ = self.lint(doc)
        self.assertTrue(any("shell-header.ready" in e and "does not land this scene" in e for e in errors))
        del doc["scenes"]["shell-header.ready"]["open"]
        doc["scenes"]["library.ready"]["open"] = ["create-project.add-material"]
        self.assertFalse(any("library.ready" in e and "land" in e for e in self.lint(doc)[0]))  # App page

    def test_clock_is_whole_milliseconds(self):
        doc = contract()
        doc["scenes"]["empty"]["clock"] = 3000
        self.assertEqual(self.lint(doc)[0], [])
        doc["scenes"]["empty"]["clock"] = "later"
        self.assertTrue(any("clock" in e for e in self.lint(doc)[0]))

    def test_mechanisms_carry_via_and_built_by(self):
        doc = contract()
        doc["mechanisms"] = ["seed:library-ready", "seed:draft-existing"]
        self.assertTrue(any("mechanisms is a list" in e for e in self.lint(doc)[0]))
        doc = contract()
        doc["mechanisms"]["seed:library-ready"] = {"via": "api"}
        self.assertTrue(any("built_by ''" in e for e in self.lint(doc)[0]))
        doc = contract()
        del doc["mechanisms"]["seed:draft-existing"]["proven_by"]
        self.assertTrue(any("needs proven_by" in e for e in self.lint(doc)[0]))
        doc = contract()
        doc["mechanisms"]["seed:library-ready"]["via"] = "magic"
        self.assertTrue(any("not api or storage" in e for e in self.lint(doc)[0]))

    def test_stale_or_missing_target_trees(self):
        self.repo.write_targets(stale_page=PAGE_B)
        errors, _ = self.lint(contract())
        self.assertTrue(any("is stale" in e and "壳头" in e for e in errors))
        os.remove(self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria"))
        errors, _ = self.lint(contract())
        self.assertTrue(any("missing; run extract_skeleton.py" in e for e in errors))


class TestSources(unittest.TestCase):
    def test_a_story_source_is_a_warning_not_an_error(self):
        doc = contract()
        doc["rows"][0]["source"] = ["#537 story 2", "ADR-0021"]
        errors, warnings = lc.lint(doc, SKELETON, None)
        self.assertFalse(any("story" in e for e in errors))
        self.assertTrue(any("is a story; no worker reads a story" in w for w in warnings))

    def test_an_unrecognised_source_shape_is_a_warning(self):
        doc = contract()
        doc["rows"][0]["source"] = ["somebody said so"]
        _, warnings = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("no recognised shape" in w for w in warnings))

    def test_recognised_shapes_are_silent(self):
        for src in ("#420", "#537 Implementation Decisions 2", "#537 Testing Decisions",
                    "ADR-0021", "docs/context/chameleon-product.md 新建商品项目",
                    "README §4.1", "code:src/x.py"):
            self.assertNotEqual(lc.source_shape(src), "unknown", src)
        self.assertEqual(lc.source_shape("#537 story 2"), "story")


class TestObserve(unittest.TestCase):
    """A row whose calls are all non-HTTP may leave observe empty (a warning).
    A row that names an HTTP operation still errors without one."""

    def test_missing_observe_on_chrome_runtime_sendMessage_is_a_warning(self):
        doc = contract()
        doc["rows"][0]["calls"] = ["chrome.runtime.sendMessage x"]
        openapi = {"paths": {"/api/notes": {"post": {}}}}
        errors, warnings = lc.lint(doc, SKELETON, openapi)
        self.assertFalse(any("create-project.add-material" in e and "observe" in e
                            for e in errors), errors)
        self.assertFalse(any("create-project.add-material" in e and "call not in openapi" in e
                            for e in errors), errors)
        self.assertTrue(any("create-project.add-material" in w and "observe is empty" in w
                            and "non-HTTP" in w for w in warnings), warnings)

    def test_missing_observe_on_an_http_call_is_an_error(self):
        doc = contract()
        doc["rows"][0]["calls"] = ["POST /api/notes"]
        openapi = {"paths": {"/api/notes": {"post": {}}}}
        errors, warnings = lc.lint(doc, SKELETON, openapi)
        self.assertTrue(any("create-project.add-material" in e and "observe missing" in e
                            for e in errors), errors)
        self.assertFalse(any("create-project.add-material" in w and "observe is empty" in w
                             for w in warnings), warnings)

    def test_missing_observe_on_an_ipc_call_stays_a_warning(self):
        errors, warnings = lc.lint(contract(), SKELETON, None)
        self.assertFalse(any("observe" in e for e in errors), errors)
        self.assertTrue(any("observe is empty" in w and "non-HTTP" in w for w in warnings),
                        warnings)

    def test_a_mixed_row_missing_observe_is_an_error(self):
        doc = contract()
        doc["rows"][0]["calls"] = ["ipc x", "POST /api/notes"]
        openapi = {"paths": {"/api/notes": {"post": {}}}}
        errors, warnings = lc.lint(doc, SKELETON, openapi)
        self.assertTrue(any("create-project.add-material" in e and "observe missing" in e
                            for e in errors), errors)
        self.assertFalse(any("create-project.add-material" in w and "observe is empty" in w
                             for w in warnings), warnings)

    def test_a_malformed_http_call_missing_observe_is_an_error(self):
        doc = contract()
        doc["rows"][0]["calls"] = ["POST api/notes"]
        openapi = {"paths": {"/api/notes": {"post": {}}}}
        errors, warnings = lc.lint(doc, SKELETON, openapi)
        self.assertTrue(any("create-project.add-material" in e and "observe missing" in e
                            for e in errors), errors)
        self.assertTrue(any("create-project.add-material" in e and "call not in openapi" in e
                            for e in errors), errors)
        self.assertFalse(any("create-project.add-material" in w and "observe is empty" in w
                             for w in warnings), warnings)


class TestRetiredPrinted(unittest.TestCase):

    def test_every_retired_entry_is_a_line(self):
        doc = {"retired_ids": [{"id": "a.b", "note": "retired 2026-09-03 — verdict 2"}, "c.d"]}
        self.assertEqual(lc.retired_lines(doc),
                         ["RETIRED a.b: retired 2026-09-03 — verdict 2", "RETIRED c.d: (no note)"])


class TestVolatileValues(unittest.TestCase):
    """`volatile_values` is printed on every run, like `retired_ids`. An entry whose
    trigger is not in that page's target tree is a WARN — it cannot be what the
    judges will replace. An entry that matches more than one node on its page is
    an ERROR — the judges would mask every sibling that shares the stem."""

    ENTRY = {
        "page": PAGE_A,
        "trigger": {"role": "text", "name": "鸭豆余额 12,480"},
        "reason": "wallet balance is an external account; seed does not write it",
    }
    SIBLINGS = (
        "- text: 每张费用\n"
        "- strong: 20 鸭豆\n"
        "- text: 最大预扣\n"
        "- strong: 40 鸭豆\n"
        "- text: 当前余额\n"
        "- strong: 12,480 鸭豆\n"
    )
    AMBIGUOUS = {
        "page": PAGE_A,
        "trigger": {"role": "strong", "name": "12,480 鸭豆"},
        "reason": "wallet balance is an external account; seed does not write it",
    }

    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()

    def tearDown(self):
        self.repo.cleanup()

    def test_volatile_values_are_printed_every_run(self):
        doc = {"volatile_values": [self.ENTRY]}
        self.assertEqual(
            lc.volatile_lines(doc),
            ['VOLATILE Component · 新建商品项目.dc.html text "鸭豆余额 12,480": '
             "wallet balance is an external account; seed does not write it"])

    def test_a_volatile_value_missing_from_the_target_tree_is_a_warning(self):
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        aria.write_text(aria.read_text(encoding="utf-8") + '- button "添加商品素材"\n',
                        encoding="utf-8")
        doc = contract()
        doc["volatile_values"] = [self.ENTRY]
        _, warnings = lc.lint_screen_axis(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("volatile_values" in w and "鸭豆余额 12,480" in w
                            and "not in the target tree" in w for w in warnings), warnings)

        aria.write_text(aria.read_text(encoding="utf-8") + '- text: 鸭豆余额 12,480\n',
                        encoding="utf-8")
        _, warnings = lc.lint_screen_axis(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("volatile_values" in w for w in warnings), warnings)

    def test_an_entry_that_matches_several_nodes_is_an_error(self):
        """Same three strongs as the driver test. Without `after` the entry
        matches all three and the lint errors; with `after` it matches one
        and does not."""
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        unique = "- text: 当前余额\n- strong: 12,480 鸭豆\n"
        aria.write_text(
            aria.read_text(encoding="utf-8")
            + "## scene free-gate\n" + self.SIBLINGS
            + "## scene free-hold-unknown\n" + unique,
            encoding="utf-8")
        doc = contract()
        doc["volatile_values"] = [dict(self.AMBIGUOUS)]
        errors, warnings = lc.lint_screen_axis(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("volatile_values" in e and "12,480 鸭豆" in e
                            and "matches 3 nodes" in e for e in errors), errors)
        self.assertFalse(any("volatile_values" in w for w in warnings), warnings)

        doc["volatile_values"][0]["after"] = {"role": "text", "name": "当前余额"}
        errors, warnings = lc.lint_screen_axis(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("volatile_values" in e for e in errors), errors)
        self.assertFalse(any("volatile_values" in w for w in warnings), warnings)


class TestTriggerAfter(unittest.TestCase):
    """A row whose trigger hits more than one named node on a scene, with no
    `after`, is an ERROR — the same rule as `volatile_values`. With `after` it
    matches one and does not."""

    TREE = (
        '- button "放弃这次任务"\n'
        '- heading "要放弃这次任务吗"\n'
        '- button "放弃这次任务"\n'
    )
    ROW = {
        "id": "create-project.abandon.confirm",
        "component": "features/project-setup/CreateProjectView",
        "trigger": {"role": "button", "name": "放弃这次任务"},
        "precondition": {},
        "scenes": ["empty"],
        "calls": ["none"],
        "shows": {},
        "next": "stay",
        "source": ["#537 Implementation Decisions 2"],
        "reach": "seed:library-ready",
        "gap": "aligned",
    }

    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()

    def tearDown(self):
        self.repo.cleanup()

    def test_a_trigger_that_matches_several_nodes_is_an_error(self):
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        aria.write_text(
            aria.read_text(encoding="utf-8") + "## scene empty\n" + self.TREE,
            encoding="utf-8")
        doc = contract()
        doc["rows"] = [*doc["rows"], dict(self.ROW)]
        errors, warnings = lc.lint_screen_axis(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("create-project.abandon.confirm" in e
                            and "放弃这次任务" in e
                            and "matches 2 nodes" in e
                            and "after" in e for e in errors), errors)
        self.assertFalse(any("create-project.abandon.confirm" in w for w in warnings),
                         warnings)

        doc["rows"][-1]["after"] = {"role": "heading", "name": "要放弃这次任务吗"}
        errors, warnings = lc.lint_screen_axis(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("create-project.abandon.confirm" in e for e in errors),
                         errors)
        self.assertFalse(any("create-project.abandon.confirm" in w for w in warnings),
                         warnings)

    def test_a_same_stem_sibling_is_not_a_second_hit(self):
        """A row trigger is exact. `确认` next to `确认 2` is one hit, so the
        lint does not demand `after`."""
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        aria.write_text(
            aria.read_text(encoding="utf-8")
            + "## scene empty\n"
            + '- button "确认 2"\n'
            + '- heading "标题"\n'
            + '- button "确认"\n',
            encoding="utf-8")
        doc = contract()
        row = dict(self.ROW)
        row["trigger"] = {"role": "button", "name": "确认"}
        doc["rows"] = [*doc["rows"], row]
        errors, _ = lc.lint_screen_axis(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("create-project.abandon.confirm" in e for e in errors),
                         errors)

    def test_after_on_a_missing_trigger_is_not_this_rule(self):
        """`after` present and zero hits is not the uniqueness ERROR: the
        ticket only errors when the trigger matches more than one node and
        the row has no coordinate."""
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        aria.write_text(
            aria.read_text(encoding="utf-8") + "## scene empty\n- heading \"其他\"\n",
            encoding="utf-8")
        doc = contract()
        row = dict(self.ROW)
        row["after"] = {"role": "heading", "name": "要放弃这次任务吗"}
        doc["rows"] = [*doc["rows"], row]
        errors, _ = lc.lint_screen_axis(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("create-project.abandon.confirm" in e
                             and "matches 0 nodes" in e for e in errors), errors)


class TestOccurrencePin(unittest.TestCase):
    """A positional pin is only safe because the lint holds it. These are the holds."""

    # Two blocks the design draws identically: every match follows the same node, so no
    # `after` exists and `occurrence` is the only pin that can address them.
    TREE = (
        '- text: 参考图\n'
        '- button "使用说明"\n'
        '- button "添加参考图"\n'
        '- text: 参考图\n'
        '- button "使用说明"\n'
        '- button "添加参考图"\n'
        '- button "下一步"\n'
    )
    ROW = {
        "id": "create-project.abandon.confirm",
        "component": "features/project-setup/CreateProjectView",
        "trigger": {"role": "button", "name": "添加参考图"},
        "precondition": {},
        "scenes": ["empty"],
        "calls": ["none"],
        "shows": {},
        "next": "stay",
        "source": ["#537 Implementation Decisions 2"],
        "reach": "seed:library-ready",
        "gap": "aligned",
    }

    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        aria.write_text(aria.read_text(encoding="utf-8") + "## scene empty\n" + self.TREE,
                        encoding="utf-8")

    def tearDown(self):
        self.repo.cleanup()

    def errors_for(self, pin: dict, **row_extra) -> list[str]:
        """`occurrence` and `of` sit on the row, beside `after`: one home for pins."""
        doc = contract()
        row = dict(self.ROW, **row_extra)
        name = pin.pop("name", None)
        if name is not None:
            row["trigger"] = dict(self.ROW["trigger"], name=name)
        row.update(pin)
        doc["rows"] = [*doc["rows"], row]
        errors, _ = lc.lint_screen_axis(doc, SKELETON, self.repo.baseline,
                                        self.repo.spec_dir)
        return [e for e in errors if self.ROW["id"] in e]

    def test_a_repeated_block_takes_the_positional_pin_and_then_resolves(self):
        self.assertTrue(self.errors_for({}), "unpinned, this row is undrivable")
        self.assertEqual(self.errors_for({"occurrence": 1, "of": 2}), [])

    def test_the_count_the_pin_was_written_against_is_held(self):
        """A positional pin means nothing against a number that has moved."""
        wrong = self.errors_for({"occurrence": 1, "of": 3})
        self.assertTrue(any("of 3" in e for e in wrong), wrong)

    def test_an_index_outside_the_matches_is_an_error(self):
        out = self.errors_for({"occurrence": 3, "of": 2}, source=["#537 Implementation Decisions 2"])
        self.assertTrue(any("outside" in e for e in out), out)

    def test_a_pin_past_the_first_match_has_to_say_where_it_came_from(self):
        """`occurrence: 1` is what the repair command writes, blind to the product.
        Anything else is a judgement about which block the row means."""
        row = dict(self.ROW)
        row.pop("source")
        self.assertTrue(any("source" in e for e in
                            self.errors_for({"occurrence": 2, "of": 2}, source=[])),
                        "a non-default index with no source must be refused")
        self.assertEqual(self.errors_for({"occurrence": 2, "of": 2}), [])

    def test_a_row_carries_one_pin(self):
        both = self.errors_for({"occurrence": 1, "of": 2},
                               after={"role": "button", "name": "使用说明"})
        self.assertTrue(any("both after and occurrence" in e for e in both), both)

    def test_a_positional_pin_on_an_unambiguous_trigger_is_refused(self):
        out = self.errors_for({"name": "下一步", "occurrence": 1, "of": 1})
        self.assertTrue(any("does not have" in e for e in out), out)


class TestPinCommand(unittest.TestCase):
    """`--pin` repairs a locator and proves it before keeping it. The proof is the whole
    reason an agent is allowed to touch a contract at all."""

    TREE = (
        '- text: 参考图\n'
        '- button "使用说明"\n'
        '- button "添加参考图"\n'
        '- text: 参考图\n'
        '- button "使用说明"\n'
        '- button "添加参考图"\n'
    )
    ROW = {
        "id": "create-project.abandon.confirm",
        "component": "features/project-setup/CreateProjectView",
        "trigger": {"role": "button", "name": "添加参考图"},
        "precondition": {},
        "scenes": ["empty"],
        "calls": ["none"],
        "shows": {},
        "next": "stay",
        "source": ["#537 Implementation Decisions 2"],
        "reach": "seed:library-ready",
        "gap": "aligned",
    }

    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()
        aria = self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria")
        aria.write_text(aria.read_text(encoding="utf-8") + "## scene empty\n" + self.TREE,
                        encoding="utf-8")

    def tearDown(self):
        self.repo.cleanup()

    def commit(self, doc) -> Path:
        """The contract on disk and in a commit, because the proof reads the committed one."""
        path = self.repo.spec_dir / "screen-contract.yaml"
        path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
        root = self.repo.root
        for cmd in (["init", "-q", "-b", "main"], ["add", "-A"],
                    ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "c"]):
            subprocess.run(["git", "-C", str(root), *cmd], check=False,
                           capture_output=True)
        return path

    def run_pin(self, path: Path) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = lc.main(["lint_contract.py", "--tools", str(TOOLS_DIR), "--pin", str(path)])
        return code, out.getvalue()

    def test_a_repeated_block_is_pinned_and_the_write_is_kept(self):
        doc = contract()
        doc["rows"] = [*doc["rows"], dict(self.ROW)]
        path = self.commit(doc)
        code, said = self.run_pin(path)
        self.assertIn("PINNED", said)
        self.assertIn("occurrence: 1", said)
        written = path.read_text(encoding="utf-8")
        self.assertIn("occurrence: 1", written)
        self.assertIn("of: 2", written)
        self.assertEqual(code, 0, said)

    def test_a_row_the_committed_contract_resolved_is_not_repaired(self):
        """The one way a repair could change meaning: delete a hand-written pin, let the
        command write a different one, and each write passes its own proof while the pair
        moves the row to another node. The committed contract is what says it was fine."""
        doc = contract()
        pinned = dict(self.ROW, occurrence=2, of=2)
        doc["rows"] = [*doc["rows"], pinned]
        path = self.commit(doc)

        broken = contract()
        broken["rows"] = [*broken["rows"], dict(self.ROW)]     # the pin deleted
        path.write_text(yaml.safe_dump(broken, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
        code, said = self.run_pin(path)
        self.assertIn("the working copy broke it", said)
        self.assertNotIn("PINNED", said)
        self.assertNotIn("occurrence", path.read_text(encoding="utf-8"))

    def test_nothing_is_written_when_the_proof_fails(self):
        """Whatever the reason, a failed proof leaves the file exactly as it was."""
        doc = contract()
        doc["rows"] = [*doc["rows"], dict(self.ROW, scenes=["empty", "ready"])]
        path = self.commit(doc)
        before = path.read_text(encoding="utf-8")
        code, said = self.run_pin(path)
        if "PINNED" not in said:
            self.assertEqual(path.read_text(encoding="utf-8"), before, said)


if __name__ == "__main__":
    unittest.main()
