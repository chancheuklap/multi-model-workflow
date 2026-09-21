"""The remaining rules of `lint_screen_contract.py`: one positive and one negative case each,
over a small handoff package written into a temporary repository."""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "write-screen-contract" / "scripts" / "lint_screen_contract.py"
spec = importlib.util.spec_from_file_location("lint_screen_contract", SCRIPT)
lc = importlib.util.module_from_spec(spec)
sys.modules["lint_screen_contract"] = lc
spec.loader.exec_module(lc)

# The ui-acceptance scripts the lint asks to validate `.mmw/target.json`.
TOOLS_DIR = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts"

PAGE_A = "Component · 新建商品项目.dc.html"
PAGE_B = "Component · 壳头.dc.html"
PAGE_APP = "App · 商品项目库.dc.html"

SKELETON = {
    "scene_pages": {"empty": PAGE_A, "material-added": PAGE_A, "shell-header.ready": PAGE_B,
                    "library.ready": PAGE_APP},
    "table": [
        {"page": PAGE_A, "id": "create-project.add-material",
         "scenes": ["empty"], "interactive": True},
        {"page": PAGE_A, "id": "create-project.name",
         "scenes": ["empty", "material-added"], "interactive": True},
        {"page": PAGE_B, "id": "shell.sign-in",
         "scenes": ["shell-header.ready"], "interactive": True},
    ],
}


def contract():
    return {
        "effort": "x",
        "baselines": {"look": "handoff"},
        "locale": "zh-CN",
        "viewports": ["1440x900", "1180x720"],
        "pages": {
            PAGE_A: {"mount": "create-project",
                     "component": "features/project-setup/CreateProjectView"},
            PAGE_B: {"mount": "shell-header",
                     "component": "renderer/components/ShellHeader"},
            PAGE_APP: {"mount": "library-app"},
        },
        "scenes": {
            "empty": {"page": PAGE_A},
            "material-added": {"page": PAGE_A},
            "shell-header.ready": {"page": PAGE_B},
            "library.ready": {"page": PAGE_APP},
        },
        "states": ["app-awaiting-browser"],
        "rows": [
            {"id": "create-project.add-material",
             "component": "features/project-setup/CreateProjectView",
             "trigger": "create-project.add-material", "precondition": {},
             "scenes": ["empty"], "calls": ["ipc x"], "shows": {}, "next": "material-added",
             "on_failure": {"cancelled": "stay"},
             "source": ["#537 Implementation Decisions 2", "ADR-0021"],
             "gap": "aligned"},
            {"id": "create-project.name",
             "component": "features/project-setup/CreateProjectView",
             "trigger": "create-project.name", "precondition": {},
             "scenes": ["empty", "material-added"], "calls": ["none"], "shows": {},
             "next": "material-added", "source": ["#537 Implementation Decisions 2"],
             "gap": "aligned"},
            {"id": "shell.sign-in", "component": "renderer/components/ShellHeader",
             "trigger": "shell.sign-in", "precondition": {},
             "scenes": ["shell-header.ready"], "calls": ["ipc y"], "shows": {},
             "next": "app-awaiting-browser",
             "on_failure": {"failed": "toast:SIGN_IN_FAILED"},
             "source": ["#536 Implementation Decisions 3"],
             "gap": "aligned"},
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
            props = ('{"scene":{"editor":"enum","options":["ready"]}}'
                     if page.startswith("Component · ") else '{}')
            (self.baseline / page).write_text(
                f'<html><body><button data-ui="fixture.action">Action</button>'
                f'<input data-ui="fixture.editor">'
                f'<script type="text/x-dc" data-dc-script data-props=\'{props}\'></script>'
                f'</body></html>')
        self.spec_dir = self.root / "docs" / "specs" / "x"
        self.spec_dir.mkdir(parents=True)
        self.contract = self.spec_dir / "screen-contract.yaml"
        mmw = self.root / ".mmw"
        mmw.mkdir()
        (mmw / "target.json").write_text(json.dumps({
            "start": "s", "stop": "t", "discover": "d",
            "stories": "st", "leaves_machine": [], "harness_markers": [],
        }))

    def cleanup(self):
        self.dir.cleanup()


class TestScreenAxis(unittest.TestCase):
    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def lint(self, doc):
        errors, warnings = lc.lint_declarations(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        return errors, warnings

    def test_a_contract_outside_the_repository_resolves_against_the_run_directory(self):
        with tempfile.TemporaryDirectory() as scratch:
            outside = Path(scratch) / "screen-contract.yaml"
            outside.write_text("effort: x\n")
            nested = self.repo.root / "docs"
            before = os.getcwd()
            os.chdir(nested)
            try:
                self.assertEqual(lc.repo_root(outside).resolve(), self.repo.root.resolve())
            finally:
                os.chdir(before)

    def test_a_scene_input_must_name_a_package_file_and_a_value(self):
        (self.repo.baseline / "data").mkdir()
        (self.repo.baseline / "data" / "scenes.js").write_text("window.S = {};")
        doc = contract()
        name = next(iter(doc["scenes"]))
        decl = doc["scenes"][name]
        decl["input"] = {"file": "data/scenes.js", "value": "S.ready", "with": {"select": {"node": 3}}}
        errors, _ = self.lint(doc)
        self.assertFalse(any("input" in e for e in errors), errors)
        decl["input"] = {"file": "data/missing.js", "value": "S.ready"}
        self.assertTrue(any("input file 'data/missing.js'" in e for e in self.lint(doc)[0]))
        decl["input"] = {"file": "data/scenes.js"}
        self.assertTrue(any("needs file and value" in e for e in self.lint(doc)[0]))
        decl["input"] = {"file": "../outside.js", "value": "S.ready"}
        self.assertTrue(any("not in the handoff package" in e for e in self.lint(doc)[0]))
        decl["input"] = {"file": "data/scenes.js", "value": "S.ready", "with": "x", "extra": 1}
        errs = self.lint(doc)[0]
        self.assertTrue(any("input.with must be a mapping" in e for e in errs), errs)
        self.assertTrue(any("input.extra is not a contract field" in e for e in errs), errs)
        decl["input"] = "data/scenes.js S.ready"
        self.assertTrue(any("input must be a mapping" in e for e in self.lint(doc)[0]))

    def test_a_page_may_declare_its_own_viewports(self):
        doc = contract()
        page = next(iter(doc["pages"]))
        doc["pages"][page]["viewports"] = ["236x848"]
        self.assertFalse(any("viewports" in e for e in self.lint(doc)[0]))
        doc["pages"][page]["viewports"] = ["wide"]
        self.assertTrue(any("viewports entry 'wide'" in e for e in self.lint(doc)[0]))
        doc["pages"][page]["viewports"] = ["1100x720"]
        self.assertTrue(any("width 1100 is a breakpoint" in e for e in self.lint(doc)[0]))

    def test_a_complete_contract_has_no_errors(self):
        errors, warnings = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertEqual(errors, [])
        self.assertFalse(any("story" in w for w in warnings), warnings)

    def test_missing_target_json_is_a_warning(self):
        (self.repo.root / ".mmw" / "target.json").unlink()
        errors, warnings = self.lint(contract())
        self.assertFalse(any("target.json" in e for e in errors), errors)
        self.assertTrue(any("no .mmw/target.json" in w and "target_config.py --check" in w
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

    def test_a_page_root_without_data_ui_is_an_error(self):
        page = self.repo.baseline / "Component · Rooted.dc.html"
        page.write_text(
            "<html><body><x-dc><helmet><link rel=\"stylesheet\" href=\"a.css\"></helmet>"
            "<header class=\"bar\"><span data-ui=\"rooted.title\">T</span></header></x-dc>"
            "<script type=\"text/x-dc\" data-dc-script data-props='{\"scene\":{}}'></script>"
            "</body></html>")
        errors, _ = self.lint(contract())
        self.assertTrue(any("Component · Rooted.dc.html:1: the page's root <header> has no data-ui"
                            in e for e in errors), errors)
        page.write_text(page.read_text().replace('<header class="bar">',
                                                 '<header class="bar" data-ui="rooted.root">'))
        errors, _ = self.lint(contract())
        self.assertFalse(any("root <header>" in e for e in errors), errors)

    def test_a_component_page_without_a_scene_prop_is_an_error(self):
        (self.repo.baseline / "Component · Unaccepted.dc.html").write_text(
            '<html><body><script type="text/x-dc" data-dc-script data-props=\'{}\'></script></body></html>')
        errors, _ = self.lint(contract())
        self.assertTrue(any("Component · Unaccepted.dc.html: Component page has no scene prop" in e
                            for e in errors), errors)

    def test_a_breakpoint_in_the_design_system_or_a_page_style_block_counts(self):
        ds = self.repo.baseline / "_ds" / "kit-1234" / "components"
        ds.mkdir(parents=True)
        (ds / "bar.css").write_text("@media (min-width: 900px) { a { b: c } }")
        (self.repo.baseline / "Component · Styled.dc.html").write_text(
            "<style>@media (max-width: 640px) { a { b: c } }</style>")
        doc = contract()
        for width in ("900", "640"):
            doc["viewports"] = [f"{width}x720"]
            errors, _ = self.lint(doc)
            self.assertTrue(any(f"{width} is a breakpoint" in e for e in errors), errors)

    def test_a_missing_handoff_package_path_is_an_error(self):
        for child in sorted(self.repo.baseline.rglob("*"), reverse=True):
            child.unlink() if child.is_file() else child.rmdir()
        self.repo.baseline.rmdir()
        errors, _ = self.lint(contract())
        self.assertTrue(any("baselines.look" in error and "does not exist" in error
                            for error in errors), errors)

    def test_a_contract_without_locale_is_an_error(self):
        doc = contract()
        del doc["locale"]
        errors, _ = self.lint(doc)
        self.assertTrue(any("locale" in error and "missing" in error for error in errors),
                        errors)
        doc["locale"] = "not a locale"
        errors, _ = self.lint(doc)
        self.assertTrue(any("locale" in error and "BCP 47" in error for error in errors),
                        errors)
        doc["locale"] = "en"
        errors, _ = self.lint(doc)
        self.assertFalse(any("locale" in error for error in errors), errors)

    def test_a_clickable_control_without_a_data_ui_id_is_an_error(self):
        page = self.repo.baseline / PAGE_A
        good = page.read_text()
        page.write_text(good.replace(' data-ui="fixture.action"', ""))
        errors, _ = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any(PAGE_A in error and "button" in error and "data-ui" in error
                            for error in errors), errors)
        page.write_text(good)
        errors, _ = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("data-ui" in error for error in errors), errors)

    def test_editable_and_aria_controls_without_a_data_ui_id_are_errors(self):
        page = self.repo.baseline / PAGE_A
        good = page.read_text()
        for control in ('<input>', '<div role="checkbox"></div>'):
            page.write_text(good.replace(
                '<input data-ui="fixture.editor">', control))
            errors, _ = self.lint(contract())
            self.assertTrue(any("data-ui" in error for error in errors),
                            (control, errors))

    def test_a_hidden_input_without_a_data_ui_id_is_ignored(self):
        page = self.repo.baseline / PAGE_A
        page.write_text(page.read_text().replace(
            '<input data-ui="fixture.editor">', '<input type="hidden">'))
        errors, _ = self.lint(contract())
        self.assertFalse(any("input" in error and "data-ui" in error for error in errors),
                         errors)

    def test_controls_on_one_line_report_distinct_columns(self):
        page = self.repo.baseline / PAGE_A
        page.write_text(page.read_text().replace(
            '<button data-ui="fixture.action">Action</button>',
            '<button>First</button><button>Second</button>'))
        errors, _ = self.lint(contract())
        missing = [error for error in errors if "button has no data-ui" in error]
        self.assertEqual(len(missing), 2, errors)
        self.assertNotEqual(missing[0].split(":", 3)[:3], missing[1].split(":", 3)[:3])

    def test_every_page_named_by_scenes_json_must_exist(self):
        (self.repo.baseline / PAGE_B).unlink()
        errors, _ = self.lint(contract())
        self.assertTrue(any(PAGE_B in error and "missing" in error for error in errors), errors)

    def test_pages_not_named_by_scenes_json_are_not_audit_targets(self):
        (self.repo.baseline / "Overview.dc.html").write_text("<button>Overview</button>")
        errors, _ = self.lint(contract())
        self.assertFalse(any("Overview.dc.html" in error for error in errors), errors)

    def test_a_component_page_without_a_scene_prop_is_an_error(self):
        page = self.repo.baseline / PAGE_A
        good = page.read_text()
        page.write_text(good.replace(
            '{"scene":{"editor":"enum","options":["ready"]}}', '{}'))
        errors, _ = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any(PAGE_A in error and "scene prop" in error for error in errors),
                        errors)
        page.write_text(good)
        errors, _ = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("scene prop" in error for error in errors), errors)

    def test_every_page_declares_mount(self):
        doc = contract()
        del doc["pages"][PAGE_B]
        errors, _ = self.lint(doc)
        self.assertTrue(any(f"no declaration for {PAGE_B!r}" in e for e in errors))
        doc = contract()
        doc["pages"][PAGE_A]["mount"] = ""
        self.assertTrue(any("mount" in e for e in self.lint(doc)[0]))

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

    def test_on_failure_outcomes_and_shows_bindings_have_a_checked_shape(self):
        doc = contract()
        row = doc["rows"][0]
        row["on_failure"] = {"x_4xx": "stay — the page shows nothing",
                             "y_4xx": "toast:SAVE_FAILED",
                             "z_4xx": "material-added — the list shows the new item"}
        row["shows"] = {"count": "items@ipc x → the #547 lamp count"}
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertFalse(any("on_failure" in e or "shows" in e for e in errors), errors)
        row["on_failure"] = {"x_4xx": "the page shakes"}
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("on_failure.x_4xx starts with 'the page shakes'" in e for e in errors), errors)
        row["on_failure"] = "toast:X"
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("on_failure must map" in e for e in errors), errors)
        row["shows"] = {"count": "items@ipc 3 → x"}
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("carries a literal number" in e for e in errors), errors)

    def test_a_disabled_state_needs_a_row_that_calls_nothing_and_stays(self):
        import copy
        skeleton = copy.deepcopy(SKELETON)
        skeleton["table"][0]["scenes"] = ["empty", "material-added"]
        skeleton["table"][0]["disabled_in"] = ["material-added"]
        doc = contract()
        errors, _ = lc.lint(doc, skeleton, None)
        self.assertTrue(any("disabled state without a row: create-project.add-material" in e
                            for e in errors), errors)
        doc["rows"].append({
            "id": "create-project.add-material-disabled",
            "component": doc["rows"][0]["component"],
            "trigger": "create-project.add-material", "precondition": {"material": "added"},
            "scenes": ["material-added"], "calls": ["none"], "shows": {}, "next": "stay",
            "source": ["#537 Implementation Decisions 2"], "gap": "aligned"})
        errors, _ = lc.lint(doc, skeleton, None)
        self.assertFalse(any("disabled state" in e for e in errors), errors)

    def test_next_rejects_unknown_and_accepts_rows_scenes_states_and_stay(self):
        doc = contract()
        doc["states"] = ["app-awaiting-browser"]
        allowed = [
            "create-project.name",
            "material-added",
            "app-awaiting-browser",
            "stay",
        ]
        for value in allowed:
            doc["rows"][0]["next"] = value
            errors, _ = lc.lint(doc, SKELETON, None)
            self.assertFalse(any(": next " in error for error in errors), (value, errors))
        doc["rows"][0]["next"] = "not-declared"
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("create-project.add-material: next 'not-declared'" in error
                            for error in errors), errors)

    def test_next_without_states_accepts_only_rows_scenes_and_stay(self):
        doc = contract()
        del doc["states"]
        doc["rows"][2]["next"] = "stay"
        for value in ("create-project.name", "material-added", "stay"):
            doc["rows"][0]["next"] = value
            errors, _ = lc.lint(doc, SKELETON, None)
            self.assertFalse(any(": next " in error for error in errors), (value, errors))
        doc["rows"][0]["next"] = "app-awaiting-browser"
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("next 'app-awaiting-browser'" in error for error in errors), errors)

    def test_missing_next_has_an_explicit_diagnostic(self):
        doc = contract()
        del doc["rows"][0]["next"]
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertIn("create-project.add-material: next missing (use a row id, scene, state, or stay)",
                      errors)

    def test_duplicate_row_identity_is_an_error(self):
        doc = contract()
        duplicate = dict(doc["rows"][0])
        duplicate["id"] = "create-project.add-material-again"
        doc["rows"].append(duplicate)
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("trigger 'create-project.add-material': rows share a precondition"
                            in error for error in errors), errors)

        doc = contract()
        doc["rows"][1]["id"] = doc["rows"][0]["id"]
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertTrue(any("create-project.add-material: duplicate id" in error
                            for error in errors), errors)

        doc = contract()
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertFalse(any("duplicate id" in error or "rows share a precondition" in error
                             for error in errors), errors)

    def test_one_trigger_with_distinct_preconditions_is_clean(self):
        doc = contract()
        second = dict(doc["rows"][0])
        second["id"] = "create-project.add-material-again"
        second["precondition"] = {"material": "present"}
        doc["rows"].append(second)
        errors, _ = lc.lint(doc, SKELETON, None)
        self.assertFalse(any("rows share a precondition" in error for error in errors), errors)


class TestRemovedFields(unittest.TestCase):
    """A deleted field is an error that names the migration note."""

    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def lint(self, doc):
        e1, w1 = lc.lint(doc, SKELETON, None)
        e2, w2 = lc.lint_declarations(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        return e1 + e2, w1 + w2

    def test_a_row_with_observe_or_after_is_an_error(self):
        doc = contract()
        doc["rows"][0]["observe"] = ["GET /api/x -> .ok == true"]
        doc["rows"][0]["after"] = {"role": "heading", "name": "标题"}
        errors, _ = self.lint(doc)
        self.assertTrue(any("observe" in e and "create-project.add-material" in e
                            for e in errors), errors)
        self.assertTrue(any("after" in e and "create-project.add-material" in e
                            for e in errors), errors)

    def test_a_scene_with_mount_is_an_error(self):
        doc = contract()
        doc["scenes"]["empty"]["mount"] = "create-project"
        errors, _ = self.lint(doc)
        self.assertTrue(any("mount" in e and "empty" in e for e in errors), errors)

    def test_a_removed_page_route_is_an_error(self):
        doc = contract()
        doc["pages"][PAGE_A]["route"] = "#/new-project"
        errors, _ = self.lint(doc)
        self.assertTrue(any("route" in e and PAGE_A in e for e in errors), errors)
        doc = contract()
        doc["rows"][0]["app"] = PAGE_APP
        doc["rows"][0]["next"] = "shell-header.ready"
        self.assertEqual(self.lint(doc)[0], [])

    def test_story_coverage_warns_for_app_pages_too(self):
        older = self.repo.spec_dir / "story-shots-old" / "media"
        older.mkdir(parents=True)
        for name in ("empty", "material-added", "shell-header.ready"):
            png = older / f"{name}-1440x900-impl.png"
            png.write_bytes(b"x")
            os.utime(png, (1, 1))
        media = self.repo.spec_dir / "story-shots" / "media"
        media.mkdir(parents=True)
        (media / "empty-1440x900-impl.png").write_bytes(b"x")
        (media / "shell-header.ready-1440x900-impl.png").write_bytes(b"x")
        errors, warnings = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        story = [w for w in warnings if w.startswith("story coverage:")]
        self.assertEqual(story, [
            f"story coverage: {PAGE_APP} scenes library.ready are not "
            f"in the latest element parity --out inventory",
            f"story coverage: {PAGE_A} scenes material-added are not "
            f"in the latest element parity --out inventory",
        ], warnings)
        self.assertFalse(any("empty" in w and "story coverage:" in w for w in warnings),
                         warnings)
        self.assertFalse(any("shell-header.ready" in w for w in warnings), warnings)
        self.assertTrue(any("library.ready" in w for w in warnings), warnings)
        self.assertFalse(any("story" in e for e in errors), errors)

    def test_a_removed_key_is_an_error_naming_the_migration_note(self):
        doc = contract()
        doc["target"] = {"kind": "web-spa"}
        doc["volatile_values"] = []
        doc["readme_dispositions"] = []
        doc["pages"][PAGE_A]["route"] = "/create"
        doc["retired_ids"] = [{"id": "old.save", "note": "retired",
                                "page": PAGE_A, "trigger": "create-project.save"}]
        errors, _ = lc.lint_declarations(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        row_errors, _ = lc.lint(doc, SKELETON, {"paths": {}})
        errors += row_errors
        expected = (
            "target was removed",
            "volatile_values was removed",
            "readme_dispositions was removed",
            f"pages: {PAGE_A!r} route was removed",
            "retired_ids old.save: page was removed",
            "retired_ids old.save: trigger was removed",
        )
        note = (
            Path(__file__).resolve().parents[2]
            / "downstream-notes" / "494-screen-contract-format.md"
        )
        self.assertTrue(note.is_file(), note)
        for finding in expected:
            self.assertTrue(any(finding in error and
                                "mmw-v2/downstream-notes/494-screen-contract-format.md"
                                in error for error in errors), (finding, errors))

        errors, _ = lc.lint_declarations(
            contract(), SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("removed" in error for error in errors), errors)


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

    def test_a_conversation_source_is_accepted(self):
        self.assertEqual(lc.source_shape("conversation 2026-09-19 — states confirmed"),
                         "conversation")


class TestCallInventory(unittest.TestCase):
    def test_an_operation_with_no_row_and_no_entry_is_an_error(self):
        doc = contract()
        doc["rows"][0]["calls"] = ["POST /items"]
        openapi = {"paths": {"/items": {"post": {}}, "/orphan": {"get": {}}}}
        errors, _ = lc.lint(doc, SKELETON, openapi)
        self.assertFalse(any("POST /items" in error for error in errors), errors)
        self.assertTrue(any("GET /orphan" in error and "no row" in error
                            for error in errors), errors)
        doc["backend_without_ui"] = ["GET /orphan — startup refresh"]
        errors, _ = lc.lint(doc, SKELETON, openapi)
        self.assertFalse(any("GET /orphan" in error for error in errors), errors)
        del doc["backend_without_ui"]
        doc["proposed_operations"] = ["GET /orphan"]
        errors, _ = lc.lint(doc, SKELETON, openapi)
        self.assertFalse(any("GET /orphan" in error for error in errors), errors)

    def test_a_non_http_call_is_unverified_and_not_red(self):
        errors, warnings = lc.lint(contract(), SKELETON, {"paths": {}})
        self.assertFalse(any("ipc x" in error or "ipc y" in error for error in errors), errors)
        self.assertEqual([warning for warning in warnings if warning.startswith("UNVERIFIED")], [
            "UNVERIFIED create-project.add-material: no machine-readable source for ipc x",
            "UNVERIFIED shell.sign-in: no machine-readable source for ipc y",
        ])

    def test_without_an_openapi_the_reverse_sweep_is_unverified(self):
        errors, warnings = lc.lint(contract(), SKELETON, None)
        self.assertFalse(any("reverse sweep" in error for error in errors), errors)
        self.assertTrue(any(warning.startswith("UNVERIFIED") and "reverse sweep" in warning
                            and "machine-readable interface inventory" in warning
                            for warning in warnings), warnings)


class TestCommandOutput(unittest.TestCase):
    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()

    def tearDown(self):
        self.repo.cleanup()

    def run_lint(self, doc):
        doc = json.loads(json.dumps(doc))
        doc["baselines"]["look"] = "handoff"
        self.repo.contract.write_text(lc.yaml.safe_dump(doc, allow_unicode=True))
        skeleton = self.repo.spec_dir / "skeleton.json"
        skeleton.write_text(json.dumps(SKELETON, ensure_ascii=False))
        argv = [str(SCRIPT), str(self.repo.contract), str(skeleton)]
        openapi_path = self.repo.spec_dir / "openapi.json"
        openapi_path.write_text(json.dumps({"paths": {}}))
        argv.append(str(openapi_path))
        output = io.StringIO()
        with redirect_stdout(output):
            code = lc.main(argv)
        return code, output.getvalue().splitlines()

    def test_a_clean_contract_exits_0_with_the_count_line(self):
        doc = contract()
        doc["rows"][0]["app"] = PAGE_APP
        doc["rows"][0]["next"] = "shell-header.ready"
        code, lines = self.run_lint(doc)
        self.assertEqual(code, 0, lines)
        self.assertRegex(lines[-1], r"^0 errors, \d+ warnings over 3 rows$")


class TestCrossComponentRows(unittest.TestCase):
    def composed_skeleton(self):
        skeleton = json.loads(json.dumps(SKELETON))
        skeleton["table"].append({
            "page": PAGE_APP,
            "id": "create-project.add-material",
            "scenes": ["library.ready"],
            "interactive": True,
        })
        return skeleton

    def test_a_cross_component_row_pointing_at_another_region_is_clean(self):
        doc = contract()
        doc["rows"][0]["app"] = PAGE_APP
        doc["rows"][0]["next"] = "shell-header.ready"
        errors, _ = lc.lint(doc, self.composed_skeleton(), {"paths": {}})
        self.assertEqual(errors, [])

    def test_a_cross_component_row_pointing_at_its_own_region_is_an_error(self):
        doc = contract()
        doc["rows"][0]["app"] = PAGE_APP
        doc["rows"][0]["next"] = "material-added"
        errors, _ = lc.lint(doc, self.composed_skeleton(), {"paths": {}})
        self.assertTrue(any("create-project.add-material: cross-component next" in error
                            and PAGE_A in error for error in errors), errors)

    def test_a_design_page_with_no_row_is_an_error(self):
        doc = contract()
        errors, _ = lc.lint(doc, self.composed_skeleton(), {"paths": {}})
        self.assertTrue(any(f"page has no rows: {PAGE_APP}" in error for error in errors),
                        errors)
        doc["rows"][0]["app"] = PAGE_APP
        doc["rows"][0]["next"] = "shell-header.ready"
        errors, _ = lc.lint(doc, self.composed_skeleton(), {"paths": {}})
        self.assertFalse(any("page has no rows" in error for error in errors), errors)

    def test_page_coverage_uses_table_fallback_without_scene_pages(self):
        skeleton = self.composed_skeleton()
        del skeleton["scene_pages"]
        doc = contract()
        doc["rows"] = [row for row in doc["rows"] if row["trigger"] != "shell.sign-in"]
        errors, _ = lc.lint(doc, skeleton, {"paths": {}})
        self.assertTrue(any(f"page has no rows: {PAGE_B}" in error for error in errors), errors)


class TestRetiredPrinted(unittest.TestCase):

    def test_every_retired_entry_is_a_line(self):
        doc = {"retired_ids": [{"id": "a.b", "note": "retired 2026-09-03 — verdict 2"}, "c.d"]}
        self.assertEqual(lc.retired_lines(doc),
                         ["RETIRED a.b: retired 2026-09-03 — verdict 2", "RETIRED c.d: (no note)"])


class TestFindsUiAcceptanceWithoutTools(unittest.TestCase):
    """The lint finds ui-acceptance `target_config.py` with TOOLS empty."""

    def test_the_lint_runs_without_tools(self):
        expected = (
            Path(__file__).resolve().parents[2]
            / "skills" / "ui-acceptance" / "scripts" / "target_config.py"
        ).resolve()
        self.assertTrue(expected.is_file())
        self.assertEqual((lc.SIBLING_UA / "target_config.py").resolve(), expected)
        saved_lc_tools = list(lc.TOOLS)
        saved_tc = sys.modules.pop("target_config", None)
        try:
            lc.TOOLS[:] = []
            tc = lc.target_config_mod()
            self.assertEqual(Path(tc.__file__).resolve(), expected)
            fixture = Path(__file__).resolve().parent / "fixtures" / "removed-fields"
            output = io.StringIO()
            with redirect_stdout(output):
                code = lc.main([
                    str(SCRIPT),
                    str(fixture / "screen-contract.yaml"),
                    str(fixture / "skeleton.json"),
                ])
            self.assertEqual(code, 1)
            self.assertRegex(output.getvalue().splitlines()[-1],
                             r"^\d+ errors, \d+ warnings over 1 rows$")
        finally:
            lc.TOOLS[:] = saved_lc_tools
            if saved_tc is not None:
                sys.modules["target_config"] = saved_tc

    def test_explicit_tools_forms_reach_main(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "removed-fields"
        forms = (["--tools", str(TOOLS_DIR)], [f"--tools={TOOLS_DIR}"])
        for form in forms:
            with self.subTest(form=form):
                output = io.StringIO()
                with redirect_stdout(output):
                    code = lc.main([
                        str(SCRIPT), *form,
                        str(fixture / "screen-contract.yaml"),
                        str(fixture / "skeleton.json"),
                    ])
                self.assertEqual(code, 1, output.getvalue())
                self.assertEqual(lc.TOOLS, [TOOLS_DIR.resolve()])


if __name__ == "__main__":
    unittest.main()
