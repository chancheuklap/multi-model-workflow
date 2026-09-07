"""The remaining rules of `lint_contract.py`: one positive and one negative case each,
over a small handoff package written into a temporary repository."""

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "align-screens" / "scripts" / "lint_contract.py"
spec = importlib.util.spec_from_file_location("lint_contract", SCRIPT)
lc = importlib.util.module_from_spec(spec)
sys.modules["lint_contract"] = lc
spec.loader.exec_module(lc)

# The drive-target scripts the lint asks for target kinds and volatile matching.
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
            PAGE_A: {"mount": "create-project",
                     "component": "features/project-setup/CreateProjectView"},
            PAGE_B: {"mount": "shell-header",
                     "component": "renderer/components/ShellHeader"},
            PAGE_APP: {"mount": "library-app", "route": "#/"},
        },
        "scenes": {
            "empty": {"page": PAGE_A},
            "material-added": {"page": PAGE_A},
            "shell-header.ready": {"page": PAGE_B},
            "library.ready": {"page": PAGE_APP},
        },
        "rows": [
            {"id": "create-project.add-material",
             "component": "features/project-setup/CreateProjectView",
             "trigger": {"role": "button", "name": "添加商品素材"}, "precondition": {},
             "scenes": ["empty"], "calls": ["ipc x"], "shows": {}, "next": "material-added",
             "on_failure": {"cancelled": "stay"},
             "source": ["#537 Implementation Decisions 2", "ADR-0021"],
             "gap": "aligned"},
            {"id": "create-project.name",
             "component": "features/project-setup/CreateProjectView",
             "trigger": {"role": "textbox", "name": "商品名称"}, "precondition": {},
             "scenes": ["empty", "material-added"], "calls": ["none"], "shows": {},
             "next": "material-added", "source": ["#537 Implementation Decisions 2"],
             "gap": "aligned"},
            {"id": "shell.sign-in", "component": "renderer/components/ShellHeader",
             "trigger": {"role": "button", "name": "登录"}, "precondition": {},
             "scenes": ["shell-header.ready"], "calls": ["ipc y"], "shows": {},
             "next": "app-awaiting-browser",
             "on_failure": {"failed": "toast"},
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
            (self.baseline / page).write_text(f"<html>{page}</html>")
        self.spec_dir = self.root / "docs" / "specs" / "x"
        self.spec_dir.mkdir(parents=True)
        self.contract = self.spec_dir / "screen-contract.yaml"
        mmw = self.root / ".mmw"
        mmw.mkdir()
        (mmw / "target.json").write_text(json.dumps({
            "start": "s", "stop": "t", "discover": "d",
            "stories": "st", "leaves_machine": [],
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
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()

    def tearDown(self):
        self.repo.cleanup()

    def lint(self, doc):
        errors, warnings = lc.lint_declarations(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        return errors, warnings

    def test_a_complete_contract_has_no_errors(self):
        errors, warnings = self.lint(contract())
        self.assertEqual(errors, [])
        self.assertFalse(any("story" in w for w in warnings), warnings)

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

    def test_stale_or_missing_target_trees(self):
        self.repo.write_targets(stale_page=PAGE_B)
        errors, _ = self.lint(contract())
        self.assertTrue(any("is stale" in e and "壳头" in e for e in errors))
        os.remove(self.repo.spec_dir / "targets" / (PAGE_A[:-len(".dc.html")] + ".aria"))
        errors, _ = self.lint(contract())
        self.assertTrue(any("missing; run extract_skeleton.py" in e for e in errors))


class TestRemovedFields(unittest.TestCase):
    """A deleted field on a row, or `route` on a non-App page, is an error that names it."""

    def setUp(self):
        lc.TOOLS[:] = [TOOLS_DIR]
        self.repo = Repo()
        self.repo.write_targets()

    def tearDown(self):
        self.repo.cleanup()

    def lint(self, doc):
        e1, w1 = lc.lint(doc, SKELETON, None)
        e2, w2 = lc.lint_declarations(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
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

    def test_a_non_app_page_with_route_is_an_error(self):
        doc = contract()
        doc["pages"][PAGE_A]["route"] = "#/new-project"
        errors, _ = self.lint(doc)
        self.assertTrue(any("route" in e and PAGE_A in e for e in errors), errors)
        doc = contract()
        self.assertEqual(self.lint(doc)[0], [])

    def test_story_coverage_warns_when_a_page_scene_is_missing(self):
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
        errors, warnings = self.lint(contract())
        story = [w for w in warnings if w.startswith("story coverage:")]
        self.assertEqual(story, [
            f"story coverage: {PAGE_A} scenes material-added are not "
            f"in the latest story-parity --out inventory",
        ], warnings)
        self.assertFalse(any("empty" in w and "story coverage:" in w for w in warnings),
                         warnings)
        self.assertFalse(any("shell-header.ready" in w for w in warnings), warnings)
        self.assertFalse(any("library.ready" in w for w in warnings), warnings)
        self.assertFalse(any("story" in e for e in errors), errors)


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
        _, warnings = lc.lint_declarations(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("volatile_values" in w and "鸭豆余额 12,480" in w
                            and "not in the target tree" in w for w in warnings), warnings)

        aria.write_text(aria.read_text(encoding="utf-8") + '- text: 鸭豆余额 12,480\n',
                        encoding="utf-8")
        _, warnings = lc.lint_declarations(doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
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
        errors, warnings = lc.lint_declarations(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertTrue(any("volatile_values" in e and "12,480 鸭豆" in e
                            and "matches 3 nodes" in e for e in errors), errors)
        self.assertFalse(any("volatile_values" in w for w in warnings), warnings)

        doc["volatile_values"][0]["after"] = {"role": "text", "name": "当前余额"}
        errors, warnings = lc.lint_declarations(
            doc, SKELETON, self.repo.baseline, self.repo.spec_dir)
        self.assertFalse(any("volatile_values" in e for e in errors), errors)
        self.assertFalse(any("volatile_values" in w for w in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
