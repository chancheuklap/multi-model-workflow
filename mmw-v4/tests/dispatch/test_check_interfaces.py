"""check-interfaces.py against a copy of the files it reads, each broken one way.

    python3 -m unittest discover -s mmw-v4/tests/dispatch -p test_check_interfaces.py

The check reads the relay's WAKES, events.py's EVENTS, verify-ticket.py's RESUME_STEPS,
the mode's route lines and playbooks, the role table and hosts.json, and every skill's
SKILL.md. Each case copies the skills tree into a temporary directory, makes one change
a later edit could make, and runs the copied script there.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2] / "skills"
CHECK = "dispatch/scripts/check-interfaces.py"


class CheckInterfaces(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        self.tmp = root / "skills"
        shutil.copytree(SKILLS, self.tmp, ignore=shutil.ignore_patterns("__pycache__"))

    def edit(self, rel, old, new):
        path = self.tmp / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"{rel} no longer holds the text this case changes")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def run_check(self):
        proc = subprocess.run([sys.executable, str(self.tmp / CHECK)],
                              capture_output=True, text=True)
        return proc.returncode, proc.stdout

    def test_the_set_as_it_is_passes(self):
        self.assertEqual(self.run_check(), (0, "INTERFACES OK\n"))

    def append(self, rel, line):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        path.write_text(old + "\n" + line + "\n", encoding="utf-8")

    def finding(self, out, *facts):
        """The finding line that names every one of these facts, or a failure."""
        lines = [line for line in out.splitlines() if all(f in line for f in facts)]
        self.assertTrue(lines, f"no finding names {facts}:\n{out}")

    def test_a_wake_the_orchestrator_has_no_step_for_is_found(self):
        (self.tmp / "mmw-mode/playbooks/run-a-night.md").write_text("# Run a night\n", encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "run-a-night.md", "worker.lost")

    def test_a_step_waiting_for_a_wake_nobody_sends_is_found(self):
        self.append("mmw-mode/playbooks/work-a-ticket.md", "When `#<n> reviewer.started` wakes you, stop.")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "reviewer.started")

    def test_a_resume_step_the_worker_playbook_lost_is_found(self):
        (self.tmp / "mmw-mode/playbooks/work-a-ticket.md").write_text(
            "# Work a ticket\n\n1. **Start the reviewer.** Start it.\n", encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "RESUME:", "Read the review")

    def test_a_wake_for_an_event_no_ticket_can_carry_is_found(self):
        self.edit("dispatch/scripts/relay.py", '    "worker.lost": {"to": MAIN},\n',
                  '    "worker.lost": {"to": MAIN},\n    "worker.vanished": {"to": MAIN},\n')
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "worker.vanished")

    def test_a_skill_that_routes_its_caller_to_a_playbook_is_found(self):
        skill = self.tmp / "grilling" / "SKILL.md"
        skill.write_text("# Grilling\n\n## Find your moment\n\n| You are | Read |\n| --- | --- |\n"
                         "| Grilling a plan | `playbooks/grill-with-docs.md` |\n", encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "grilling/SKILL.md")

    def test_a_moment_table_into_the_skills_own_references_passes(self):
        self.append("synthetic-skill/SKILL.md", "# Synthetic\n\n## Find your moment\n\n| You are | Read |\n"
                    "| --- | --- |\n| Doing x | `references/x.md` |")
        self.assertEqual(self.run_check(), (0, "INTERFACES OK\n"))

    def test_a_role_with_no_default_model_is_found(self):
        path = self.tmp / "dispatch" / "hosts.json"
        hosts = json.loads(path.read_text(encoding="utf-8"))
        hosts["defaults"] = [row for row in hosts["defaults"] if row["agent"] != "candidate"]
        path.write_text(json.dumps(hosts), encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "candidate")

    def test_a_send_of_a_role_the_table_does_not_have_is_found(self):
        self.append("how/SKILL.md", "Send it with `dispatch.sh send narrator <brief>`.")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "dispatch.sh send narrator")

    def test_a_brief_role_nothing_sends_is_found(self):
        roles_path = self.tmp / "dispatch" / "roles.json"
        roles = json.loads(roles_path.read_text(encoding="utf-8"))
        roles["roles"].append({"name": "synthetic-brief", "sent_with": "brief", "what": "x", "returns": "x"})
        roles_path.write_text(json.dumps(roles), encoding="utf-8")
        hosts_path = self.tmp / "dispatch" / "hosts.json"
        hosts = json.loads(hosts_path.read_text(encoding="utf-8"))
        hosts["defaults"].append({"agent": "synthetic-brief", "host": "codex", "model": "x", "effort": "high"})
        hosts_path.write_text(json.dumps(hosts), encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.finding(out, "synthetic-brief")


if __name__ == "__main__":
    unittest.main()
