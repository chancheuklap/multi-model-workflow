"""The registered roles, anchors, and paths used by later MMW readers."""

import ast
import importlib.util
import json
import re
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2] / "skills"


def locations_file():
    candidate = SKILLS / "mmw/scripts/locations.py"
    if candidate.is_file():
        return candidate
    raise AssertionError(
        f"{candidate} does not exist; shared text anchors and cross-skill paths "
        "cannot be resolved: run bash mmw-v2/install.sh --check")


def locations():
    spec = importlib.util.spec_from_file_location("locations", locations_file())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RolesAndLocationsTest(unittest.TestCase):
    def test_every_role_and_where_step_is_registered(self):
        registered = locations().PLAYBOOK_ANCHORS
        expected = {
            "work-a-ticket": {"Adopted ticket", "Claim", "Read yourself in",
                              "Write the code",
                              "Integrate and run every criterion", "Post the decisions",
                              "Get reviewed", "Run every criterion one final time",
                              "Audit against the ticket", "Tell the touched tickets",
                              "Draft the closing comment", "Close out",
                              "When the orchestrator resumes you",
                              "After the closeout of an adopted ticket",
                              "When something else wakes you", "While the product runs"},
            "review-a-ticket": {"Pin the diff", "Active Rules"},
            "run-a-night": {"Check and open", "Lint the batch", "Advance, then end your turn",
                            "Handle each wake", "Closing pass", "Close the Memory records",
                            "Reverify and summarize", "Retro"},
            "accept-the-night": {"Read the night out"},
            "land-one-ticket": {"Start the worker, then end your turn", "Handle each wake", "Land"},
            "research-a-question": {"Name the decision it feeds", "Run the research",
                                    "Commit the report", "Answer on the ticket",
                                    "Leave the map alone"},
        }
        self.assertEqual({slug: set(steps) for slug, steps in registered.items()}, expected)
        roles = json.loads((SKILLS / "mmw" / "roles.json").read_text())
        for role in roles.values():
            if "playbook" not in role:
                continue
            steps = registered[role["playbook"]]
            if "entry" in role:
                self.assertIn(role["entry"], steps)
            for step in role["wakes"].values():
                self.assertIn(step, steps)

    def test_locations_registers_ticket_headings_and_success_markers(self):
        module = locations()
        self.assertEqual(set(module.TICKET_HEADINGS), {
            "## Parent", "## Owns", "## Read first", "## Seam", "## Moves",
            "## Acceptance criteria", "## State list",
        })
        self.assertEqual(set(module.SUCCESS_MARKERS), {
            "STORY OK", "BOUNDARY OK", "JOURNEY OK", "HARNESS OK",
            "VERBATIM OK", "STRUCTURE OK", "DRAFTS OK",
        })
        self.assertEqual(module.PRODUCT_RUNNING_RULES, "## Five rules while the product is running")

    def test_where_rows_only_use_registered_roles_playbooks_and_steps(self):
        module = locations()
        roles = json.loads((SKILLS / "mmw" / "roles.json").read_text())
        self.assertEqual(set(module.WHERE_ROWS), {
            "worker", "adopting-worker", "reviewer", "night-orchestrator",
            "one-ticket-orchestrator",
        })
        for role, rows in module.WHERE_ROWS.items():
            for key, row in rows.items():
                with self.subTest(role=role, key=key):
                    steps = module.PLAYBOOK_ANCHORS[row.get("playbook", roles[role]["playbook"])]
                    self.assertIn(row["kind"], ("AT", "BETWEEN", "FRESH"))
                    self.assertIn(row["step"], steps)
                    self.assertEqual(row["kind"] == "BETWEEN", "until" in row)
                    if "until" in row:
                        self.assertIn(row["until"], steps)

    def test_locations_cross_skill_paths_exist(self):
        module = locations()
        for name in ("MODE_SCRIPTS", "EVENTS_PY", "VERIFY_TICKET_PY",
                     "ISSUE_TREE_PY", "UI_ACCEPTANCE_SCRIPTS"):
            with self.subTest(name=name):
                self.assertTrue((SKILLS / getattr(module, name)).exists())

    def test_locations_imports_no_module(self):
        source = locations_file().read_text()
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom))
                             for node in ast.walk(ast.parse(source))))

    def test_locations_governed_session_pattern_matches_tool_guard(self):
        module = locations()
        path = SKILLS / "mmw" / "scripts" / "tool-guard.py"
        spec = importlib.util.spec_from_file_location("tool_guard", path)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        self.assertEqual(module.GOVERNED_TICKET_DIR_PATTERN, guard.TICKET_DIR.pattern)
        self.assertEqual(re.compile(module.GOVERNED_TICKET_DIR_PATTERN).flags,
                         guard.TICKET_DIR.flags)


if __name__ == "__main__":
    unittest.main()
