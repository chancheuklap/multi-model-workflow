"""check-interfaces.py against a copy of the files it reads, each broken one way.

    python3 -m unittest discover -s mmw-v3/tests/dispatch -p test_check_interfaces.py

The check reads the start prompt's playbook names in dispatch.sh, the relay's WAKES,
events.py's EVENTS, verify-ticket.py's RESUME_STEPS, the mode's route lines and
playbooks, the role table and hosts.json, and every skill's SKILL.md and the files the
role table names. Each case copies the skills tree into a temporary directory, makes one
change a later edit could make, and runs the copied script there.
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

    def test_a_start_prompt_naming_a_playbook_with_no_route_line_is_found(self):
        self.edit("dispatch/scripts/dispatch.sh", 'WORKER_PLAYBOOK="Work a ticket"',
                  'WORKER_PLAYBOOK="Implement a ticket"')
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("no route line for **Implement a ticket.**", out)

    def test_a_wake_the_orchestrator_has_no_step_for_is_found(self):
        self.edit("mmw-mode/playbooks/run-one-ticket.md", "`#<n> worker.lost`", "`a lost worker`")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("run-one-ticket.md: the relay wakes this playbook's session with #<n> worker.lost", out)

    def test_a_step_waiting_for_a_wake_nobody_sends_is_found(self):
        self.edit("mmw-mode/playbooks/work-a-ticket.md", "When `#<n> reviewer.reported` wakes you",
                  "When `#<n> reviewer.reported` or `#<n> reviewer.started` wakes you")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("waits for #<n> reviewer.started", out)

    def test_a_resume_step_the_worker_playbook_lost_is_found(self):
        self.edit("mmw-mode/playbooks/work-a-ticket.md", "**Read the review.**", "**Read the report.**")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("a RESUME: line can name the step **Read the review.**", out)

    def test_a_wake_for_an_event_no_ticket_can_carry_is_found(self):
        self.edit("dispatch/scripts/relay.py", '    "worker.lost": {"to": MAIN},\n',
                  '    "worker.lost": {"to": MAIN},\n    "worker.vanished": {"to": MAIN},\n')
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("worker.vanished wakes a session", out)

    def test_a_skill_that_routes_its_caller_is_found(self):
        skill = self.tmp / "grilling" / "SKILL.md"
        skill.write_text("# Advisor\n\n## Find your moment\n\n| You are | Read |\n| --- | --- |\n",
                         encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("grilling/SKILL.md: `## Find your moment` routes its reader", out)
        self.assertIn("grilling/SKILL.md: a table headed `You are` routes its reader", out)

    def test_a_session_role_with_no_default_model_is_found(self):
        path = self.tmp / "dispatch" / "hosts.json"
        hosts = json.loads(path.read_text(encoding="utf-8"))
        hosts["defaults"] = [row for row in hosts["defaults"] if row["agent"] != "synthesizer"]
        path.write_text(json.dumps(hosts), encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("the session role synthesizer has no row in `defaults`", out)

    def test_a_file_the_role_table_names_that_is_gone_is_found(self):
        (self.tmp / "how" / "references" / "explainer-prompt.md").unlink()
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("explainer names how/references/explainer-prompt.md, which does not exist", out)

    def test_a_skill_the_table_says_starts_a_role_and_does_not_is_found(self):
        self.edit("why/SKILL.md", "start one synthesizer with `dispatch.sh brief synthesizer`",
                  "start one synthesizer")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("why/SKILL.md: dispatch/roles.json says this file starts the synthesizer", out)

    def test_a_brief_of_a_role_the_table_does_not_have_is_found(self):
        self.edit("how/SKILL.md", "start one explainer with `dispatch.sh brief explainer`",
                  "start one narrator with `dispatch.sh brief narrator`")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("how/SKILL.md: `dispatch.sh brief narrator` names no `brief` role", out)

    def test_a_skill_that_sends_a_subagent_with_no_row_is_found(self):
        skill = self.tmp / "to-questionnaire" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nSend one subagent to scan the plan.\n",
                         encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("to-questionnaire/SKILL.md: sends out a subagent, and no subagent row", out)

    def test_a_playbook_the_table_says_starts_a_role_and_does_not_is_found(self):
        self.edit("mmw-mode/playbooks/chart-a-map.md", "one `dispatch.sh brief researcher <file>...` call",
                  "one call")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("mmw-mode/playbooks/chart-a-map.md: dispatch/roles.json says this file starts the "
                      "researcher", out)

    def test_a_playbook_that_sends_a_subagent_with_no_row_is_found(self):
        playbook = self.tmp / "mmw-mode" / "playbooks" / "bug-fix.md"
        playbook.write_text(playbook.read_text(encoding="utf-8") + "\nSend one subagent to scan the repro.\n",
                            encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("mmw-mode/playbooks/bug-fix.md: sends out a subagent, and no subagent row", out)

    def test_a_playbook_the_table_says_sends_a_subagent_that_never_names_its_prompt_is_found(self):
        self.edit("mmw-mode/playbooks/cut-tickets.md", "references/ambiguity-scan.md", "the scan")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("mmw-mode/playbooks/cut-tickets.md: sends the ambiguity scanner subagent, and "
                      "never names its prompt references/ambiguity-scan.md", out)


if __name__ == "__main__":
    unittest.main()
