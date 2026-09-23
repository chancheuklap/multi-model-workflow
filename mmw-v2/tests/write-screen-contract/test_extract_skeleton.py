"""The rendered skeleton is the screen-contract row inventory.

The fixture is a hand-written design package. These tests exercise the command's
public output through the real shared design renderer and headless Chromium.
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

UA_SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts"
WSC_SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "write-screen-contract" / "scripts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "extract"
HOME = tempfile.mkdtemp(prefix="mmw-extract-skeleton-home-")


def load(directory: Path, name: str, modname: str):
    with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
        spec = importlib.util.spec_from_file_location(modname, directory / name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)
    return module


load(UA_SCRIPTS, "design_render.py", "design_render")
es = load(WSC_SCRIPTS, "extract_skeleton.py", "extract_skeleton")


def tearDownModule():
    shutil.rmtree(HOME, ignore_errors=True)


class TestFindsUiAcceptanceWithoutTools(unittest.TestCase):
    """`extract_skeleton.py` finds the sibling skill's `design_render.py` with no --tools."""

    def test_the_skeleton_runs_without_tools(self):
        expected = (UA_SCRIPTS / "design_render.py").resolve()
        self.assertTrue(expected.is_file())
        self.assertEqual((es.SIBLING_UA / "design_render.py").resolve(), expected)
        saved = list(es.TOOLS)
        try:
            es.TOOLS[:] = []
            self.assertEqual(Path(es.load_driver().__file__).resolve(), expected)
        finally:
            es.TOOLS[:] = saved


class TestExtractSkeleton(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "skeleton.json"
        es.main(FIXTURE, cls.out, FIXTURE / "screen-contract.yaml")
        cls.skeleton = json.loads(cls.out.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def row(self, data_ui: str, page: str = "Component · Inventory.dc.html") -> dict:
        return next(row for row in self.skeleton["table"]
                    if row["id"] == data_ui and row["page"] == page)

    def test_the_skeleton_is_keyed_by_page_and_data_ui_id(self):
        matches = [row for row in self.skeleton["table"]
                   if row["id"] == "inventory.search"]
        self.assertEqual(
            [(row["page"], row["id"]) for row in matches],
            [("Component · Details.dc.html", "inventory.search"),
             ("Component · Inventory.dc.html", "inventory.search")],
        )
        row = self.row("inventory.search")
        self.assertEqual(row["page"], "Component · Inventory.dc.html")
        self.assertEqual(row["scenes"], ["inventory.ready", "inventory.empty"])
        self.assertTrue(row["interactive"])
        self.assertEqual(row["text"], [])
        self.assertEqual(row["names"], ["Search: items"])

    def test_a_disabled_control_records_the_scenes_it_is_disabled_in(self):
        row = self.row("details.close", page="Component · Details.dc.html")
        self.assertTrue(row["interactive"])
        self.assertEqual(row["disabled_in"], ["details.ready"])
        self.assertEqual(self.row("inventory.search")["disabled_in"], [])

    def test_a_repeated_id_in_a_list_is_recorded_once(self):
        matches = [row for row in self.skeleton["table"]
                   if row["id"] == "inventory.open"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["scenes"], ["inventory.ready"])
        self.assertEqual(matches[0]["text"], ["Open Alpha", "Open Beta", "Open Gamma"])
        self.assertEqual(matches[0]["names"], ["Open Alpha", "Open Beta", "Open Gamma"])

    def test_a_control_only_in_out_of_scope_values_is_not_required(self):
        source = (FIXTURE / "Component · Inventory.dc.html").read_text(encoding="utf-8")
        self.assertIn('"out_of_scope": ["future"]', source)
        self.assertIn('data-ui="inventory.future"', source)
        self.assertNotIn("inventory.future", {row["id"] for row in self.skeleton["table"]})
        self.assertEqual(set(self.skeleton["scene_pages"]),
                         {"inventory.ready", "inventory.empty", "details.ready"})

    def test_each_scene_renders_once_per_declared_viewport_in_the_contract_locale(self):
        self.assertEqual(self.skeleton["locale"], "en-US")
        self.assertEqual(self.skeleton["viewports"], ["320x240", "640x480"])
        self.assertEqual(self.skeleton["renders"], 6)
        self.assertEqual(self.row("inventory.viewport")["text"],
                         ["en-US 320x240", "en-US 640x480"])

    def test_a_page_with_its_own_viewports_renders_only_there(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "screen-contract.yaml"
            contract.write_text(
                (FIXTURE / "screen-contract.yaml").read_text(encoding="utf-8")
                + 'pages:\n  "Component · Details.dc.html":\n    viewports: [320x240]\n',
                encoding="utf-8")
            output = Path(directory) / "skeleton.json"
            es.main(FIXTURE, output, contract)
            skeleton = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(skeleton["renders"], 5)

    def test_a_contract_without_locale_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "skeleton.json"
            with self.assertRaises(SystemExit) as raised:
                es.main(FIXTURE, output, FIXTURE / "screen-contract-missing-locale.yaml")
            message = str(raised.exception)
            self.assertIn("screen-contract-missing-locale.yaml", message)
            self.assertIn("`locale` is missing", message)
            self.assertIn("does not invent the product language", message)
            self.assertIn("Add `locale`", message)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
