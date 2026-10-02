"""The B2 role registry and the step-trace table the night reads."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[2] / "skills"
LIB = Path(__file__).resolve().parents[1] / "lib"
DISPATCH = SKILLS / "mmw" / "scripts" / "dispatch.sh"

# The seven names the earlier `case` in dispatch.sh still answers for one release.
OLD_SUBCOMMANDS = {
    "open", "open-ticket", "summary", "wait", "integrated", "memory-list", "route",
}

STEP_TRACE_TABLE = (
    ("Claim", "claimed-after-started"),
    ("Read yourself in", "own-checked"),
    ("Write the code", "commit-after-claim"),
    ("Integrate and run every criterion", "own-checked"),
    ("Post the decisions", "worker-decided"),
    ("Get reviewed", "reviewer-reported"),
    ("Run every criterion one final time", "worker-reverify-checked"),
    ("Audit against the ticket", "audited-line"),
    ("Tell the touched tickets", "outside-owns-none-or-touched"),
    ("Draft the closing comment", "draft-check"),
    ("Close out", "None"),
)

B2_ROLES = {
    "worker": {
        "playbook": "work-a-ticket",
        "models_row": ["junior-worker", "senior-worker"],
        "started_by": "dispatch.sh start <n> worker",
        "wakes": {
            "reviewer.reported": "Get reviewed",
            "reviewer.lost": "Get reviewed",
            "worker.queued": "Integrate and run every criterion",
            "resume": "When the orchestrator resumes you",
        },
    },
    "adopting-worker": {
        "playbook": "work-a-ticket",
        "entry": "Adopted ticket",
        "started_by": "dispatch.sh adopt <n>",
        "wakes": {
            "reviewer.reported": "Get reviewed",
            "reviewer.lost": "Get reviewed",
            "worker.queued": "Integrate and run every criterion",
            "ticket.passed": "After the closeout of an adopted ticket",
            "ticket.returned": "After the closeout of an adopted ticket",
            "*": "When something else wakes you",
        },
    },
    "reviewer": {
        "playbook": "review-a-ticket",
        "models_row": ["reviewer"],
        "started_by": "dispatch.sh start <n> reviewer",
        "wakes": {},
    },
    "night-orchestrator": {
        "playbook": "run-a-night",
        "started_by": "dispatch.sh open-night <spec>",
        "wakes": {"*": "Handle each wake"},
    },
    "one-ticket-orchestrator": {
        "playbook": "land-one-ticket",
        "started_by": "dispatch.sh open-ticket-watch <n>",
        "wakes": {"*": "Handle each wake"},
    },
    "advisor": {
        "skill": "advisor",
        "brief": "references/advising.md",
        "models_row": ["advisor"],
        "started_by": "dispatch.sh advise <file>",
        "wakes": {},
    },
    "researcher": {
        "playbook": "research-a-question",
        "models_row": ["researcher"],
        "started_by": "dispatch.sh research <n>",
        "wakes": {},
    },
}


def locations():
    spec = importlib.util.spec_from_file_location(
        "locations_under_registry_test", SKILLS / "mmw" / "scripts" / "locations.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_subcommand_names():
    sys.path.insert(0, str(LIB))
    from check_wiring import Wiring
    text = DISPATCH.read_text()
    return {name for _, name in Wiring.public_commands(str(DISPATCH), text)}


class RegistryTest(unittest.TestCase):
    def test_roles_json_registers_the_b2_roles(self):
        roles = json.loads((SKILLS / "mmw" / "roles.json").read_text())
        self.assertEqual(roles, B2_ROLES)

    def test_every_started_by_names_a_dispatch_subcommand(self):
        names = public_subcommand_names()
        self.assertTrue(names)
        roles = json.loads((SKILLS / "mmw" / "roles.json").read_text())
        for role, row in roles.items():
            with self.subTest(role=role):
                words = row["started_by"].split()
                self.assertEqual(words[0], "dispatch.sh")
                command = words[1]
                self.assertIn(command, names)
                self.assertNotIn(command, OLD_SUBCOMMANDS)

    def test_every_wake_step_is_a_registered_anchor(self):
        roles = json.loads((SKILLS / "mmw" / "roles.json").read_text())
        anchors = locations().PLAYBOOK_ANCHORS
        for role, row in roles.items():
            steps = list(row.get("wakes", {}).values())
            if "entry" in row:
                steps.append(row["entry"])
            if not steps:
                continue
            registered = anchors[row["playbook"]]
            for step in steps:
                with self.subTest(role=role, step=step):
                    self.assertIn(step, registered)

    def test_step_traces_cover_every_work_a_ticket_step(self):
        module = locations()
        traces = module.STEP_TRACES
        self.assertEqual(list(traces), [title for title, _ in STEP_TRACE_TABLE])
        self.assertEqual(list(traces.values()), [mark for _, mark in STEP_TRACE_TABLE])
        registered = module.PLAYBOOK_ANCHORS["work-a-ticket"]
        for title in traces:
            self.assertIn(title, registered)
        self.assertEqual(module.STEPS_WITHOUT_TRACE_HEADER, "Steps without a trace:")
        self.assertEqual(module.AUDITED_LINE, "Audited against the ticket:")


if __name__ == "__main__":
    unittest.main()
