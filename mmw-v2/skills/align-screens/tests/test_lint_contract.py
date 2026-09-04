"""The screen-axis rules of `lint_contract.py`: one positive and one negative case each,
over a small handoff package written into a temporary repository."""

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "lint_contract.py"
spec = importlib.util.spec_from_file_location("lint_contract", SCRIPT)
lc = importlib.util.module_from_spec(spec)
sys.modules["lint_contract"] = lc
spec.loader.exec_module(lc)

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
        "target": {"kind": "electron", "adapter": "verify-ticket/references/targets/electron.md"},
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

    def test_target_kind_and_adapter(self):
        doc = contract()
        doc["target"] = {"kind": "vt100", "adapter": "verify-ticket/references/targets/nope.md"}
        errors, _ = self.lint(doc)
        self.assertTrue(any("target.kind" in e for e in errors))
        self.assertTrue(any("target.adapter" in e and "does not exist" in e for e in errors))

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


class TestRetiredPrinted(unittest.TestCase):
    def test_every_retired_entry_is_a_line(self):
        doc = {"retired_ids": [{"id": "a.b", "note": "retired 2026-09-03 — verdict 2"}, "c.d"]}
        self.assertEqual(lc.retired_lines(doc),
                         ["RETIRED a.b: retired 2026-09-03 — verdict 2", "RETIRED c.d: (no note)"])


if __name__ == "__main__":
    unittest.main()
