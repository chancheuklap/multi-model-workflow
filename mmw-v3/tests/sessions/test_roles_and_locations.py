"""The registered roles, anchors, and paths used by the mmw-mode skill's scripts."""

import ast
import importlib.util
import json
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2] / "skills"
MODE = SKILLS / "mmw-mode"


def locations_file():
    candidate = MODE / "scripts/locations.py"
    if candidate.is_file():
        return candidate
    raise AssertionError(
        f"{candidate} does not exist; shared text anchors and cross-skill paths "
        "cannot be resolved: run bash mmw-v3/install.sh --check")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def locations():
    return load("locations", locations_file())


class RolesAndLocationsTest(unittest.TestCase):
    def test_every_role_and_step_is_registered(self):
        registered = locations().PLAYBOOK_ANCHORS
        expected = {
            "research-a-question": {"Name the decision it feeds", "Run the research",
                                    "Commit the report", "Answer on the ticket",
                                    "Leave the map alone"},
        }
        self.assertEqual({slug: set(steps) for slug, steps in registered.items()}, expected)
        roles = json.loads((MODE / "roles.json").read_text())
        self.assertEqual(set(roles), {"researcher"})
        for role in roles.values():
            steps = registered[role["playbook"]]
            if "entry" in role:
                self.assertIn(role["entry"], steps)
            for step in role["wakes"].values():
                self.assertIn(step, steps)

    def test_every_models_row_of_a_role_is_a_models_py_role(self):
        models = load("roles_models", MODE / "scripts/models.py")
        roles = json.loads((MODE / "roles.json").read_text())
        for role in roles.values():
            for row in role.get("models_row", []):
                self.assertIn(row, models.ALLOWED_AGENTS)

    def test_every_models_py_role_has_a_hosts_json_default(self):
        models = load("defaults_models", MODE / "scripts/models.py")
        self.assertEqual(set(models.default_local_config()["rows"]), set(models.ALLOWED_AGENTS))

    def test_locations_mode_paths_exist(self):
        module = locations()
        for name in ("MODE_DIRECTORY", "MODE_SCRIPTS", "MODE_PRINCIPLES_DIRECTORY",
                     "MODE_PLAYBOOKS_DIRECTORY"):
            with self.subTest(name=name):
                self.assertTrue((SKILLS / getattr(module, name)).is_dir())
        self.assertTrue((SKILLS / module.MODE_SCRIPTS / "dispatch.sh").is_file())

    def test_locations_imports_no_module(self):
        source = locations_file().read_text()
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom))
                             for node in ast.walk(ast.parse(source))))


if __name__ == "__main__":
    unittest.main()
