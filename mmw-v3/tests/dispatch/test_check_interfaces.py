"""check-interfaces.py against a copy of the files it reads, each broken one way.

    python3 -m unittest discover -s mmw-v3/tests/dispatch -p test_check_interfaces.py

The check reads the start prompt's playbook names in dispatch.sh, the relay's WAKES,
events.py's EVENTS, verify-ticket.py's RESUME_STEPS, and the mode's route lines and
playbooks. Each case copies those files
into a temporary skills tree laid out as the real one, makes one change a later edit could
make, and runs the copied script there.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2] / "skills"
FILES = ("dispatch/scripts/check-interfaces.py", "dispatch/scripts/dispatch.sh",
         "dispatch/scripts/relay.py", "verify-ticket/scripts/events.py",
         "verify-ticket/scripts/verify-ticket.py", "mmw-mode/SKILL.md")


class CheckInterfaces(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for rel in FILES:
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SKILLS / rel, self.tmp / rel)
        shutil.copytree(SKILLS / "mmw-mode" / "playbooks", self.tmp / "mmw-mode" / "playbooks")

    def edit(self, rel, old, new):
        path = self.tmp / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"{rel} no longer holds the text this case changes")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def run_check(self):
        proc = subprocess.run([sys.executable, str(self.tmp / FILES[0])],
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
        self.edit("mmw-mode/playbooks/bug-fix.md", "`#<n> worker.lost`", "`a lost worker`")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("bug-fix.md: the relay wakes this playbook's session with #<n> worker.lost", out)

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


if __name__ == "__main__":
    unittest.main()
