import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNERS = Path(__file__).resolve().parents[2] / "skills/dispatch/scripts/runners"
SESSION = "term_screen"
FAKE_ORCA = r'''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["SCREEN_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")
verb = args[1]
if verb == "create":
    answer = {"result": {"handle": "term_screen"}}
elif verb == "list":
    answer = {"result": {"terminals": [{"handle": "term_screen", "agentIdentity": "codex"}]}}
elif verb == "wait":
    if args[args.index("--for") + 1] == "exit":
        answer = {"error": {"code": "timeout"}}
    else:
        print(os.environ.get("SCREEN_PROBE", "{}"))
        sys.exit(0)
elif verb == "read":
    print(os.environ["SCREEN_READ"])
    sys.exit(int(os.environ.get("SCREEN_READ_EXIT", "0")))
elif verb == "close":
    answer = {"ok": True}
else:
    sys.exit(99)
print(json.dumps(answer))
'''


class RunnerScreen(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "calls.jsonl"
        fake = self.root / "orca"
        fake.write_text(f"#!{sys.executable}\n" + FAKE_ORCA)
        fake.chmod(0o755)

    def run_orca(self, verb, screen, probe="{}", read_exit=0):
        self.log.unlink(missing_ok=True)
        env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"],
                   MMW_HOME=str(self.root / "mmw-home"), SCREEN_LOG=str(self.log),
                   SCREEN_READ=screen, SCREEN_PROBE=probe, SCREEN_READ_EXIT=str(read_exit))
        args = ["--host", "codex", "--model", "gpt-6.1-sol", "--effort", "medium",
                "--cwd", str(self.root), "--prompt", "Work the ticket"] if verb == "start" else [SESSION]
        result = subprocess.run(["bash", str(RUNNERS / "orca.sh"), verb, *args], env=env,
                                text=True, capture_output=True, timeout=10)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return result, calls

    def screen(self, *lines):
        return json.dumps({"result": {"terminal": {"tail": list(lines)}}})

    def test_screen_start_without_a_dialog_starts(self):
        result, calls = self.run_orca("start", self.screen("Working on the ticket"))
        self.assertEqual((result.returncode, result.stdout), (0, SESSION + "\n"), result.stderr)
        self.assertFalse(any(call[:2] == ["terminal", "close"] for call in calls))

    def test_screen_start_refuses_on_a_listed_dialog(self):
        for text in ["Do you trust this folder?", "Allow external imports?", "Trust this folder?"]:
            with self.subTest(text=text):
                line = "  > " + text
                result, calls = self.run_orca("start", self.screen("Welcome", line, "Enter to confirm"))
                self.assertEqual((result.returncode, result.stdout), (1, ""), result.stderr)
                self.assertEqual(result.stderr.splitlines()[0], line)
                self.assertEqual(len(result.stderr.splitlines()), 2)
                self.assertIn(str(self.root), result.stderr.splitlines()[1])
                self.assertTrue(any(call[:2] == ["terminal", "close"] for call in calls))

    def test_screen_state_reports_the_turn(self):
        for probe, expected in [
            ({"result": {"wait": {"satisfied": True, "status": "running"}}}, "idle"),
            ({"result": {"wait": {"satisfied": False, "status": "running"}}}, "working"),
            ({"error": {"code": "timeout"}}, "working"),
        ]:
            with self.subTest(expected=expected, probe=probe):
                result, _ = self.run_orca("state", self.screen("Work the ticket"), json.dumps(probe))
                self.assertEqual((result.returncode, result.stdout), (0, expected + "\n"), result.stderr)

    def test_screen_state_reports_a_dialog(self):
        for text in ["Do you trust this folder?", "Allow external imports?", "Trust this folder?"]:
            with self.subTest(text=text):
                line = "  > " + text
                result, _ = self.run_orca("state", self.screen("Welcome", line),
                                         json.dumps({"error": {"code": "timeout"}}))
                self.assertEqual((result.returncode, result.stdout), (0, "dialog\t" + line + "\n"), result.stderr)

    def test_screen_state_does_not_guess_from_unreadable_answers(self):
        for screen, probe, read_exit in [
            ("not-json", "{}", 0),
            (self.screen("Ready"), "not-json", 0),
            (self.screen("Ready"), '{"error":{"code":"timeout"}}', 1),
        ]:
            with self.subTest(screen=screen, probe=probe, read_exit=read_exit):
                result, _ = self.run_orca("state", screen, probe, read_exit)
                self.assertEqual((result.returncode, result.stdout), (0, "unknown\n"), result.stderr)

    def test_screen_other_runners_report_only_known_states(self):
        for runner, rows in [
            ("herdr", [("working", "working"), ("idle", "idle"), ("done", "idle"),
                       ("blocked", "unknown"), ("new-status", "unknown")]),
            ("paseo", [("running", "working"), ("idle", "idle"), ("closed", "stopped"),
                       ("error", "stopped"), ("initializing", "unknown"), ("new-status", "unknown")]),
        ]:
            fake = self.root / runner
            fake.write_text(f"#!{sys.executable}\nimport os\nprint(os.environ['SCREEN_LIST'])\n")
            fake.chmod(0o755)
            for status, expected in rows + [(None, "stopped"), ("malformed", "unknown")]:
                with self.subTest(runner=runner, status=status):
                    payload = ([{"id": SESSION, "status": status}] if runner == "paseo" else
                               {"result": {"agents": [{"name": SESSION, "agent_status": status}]}})
                    if status is None:
                        payload = [] if runner == "paseo" else {"result": {"agents": []}}
                    if status == "malformed":
                        payload = {}
                    env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"],
                               MMW_HOME=str(self.root / "mmw-home"), SCREEN_LIST=json.dumps(payload))
                    result = subprocess.run(["bash", str(RUNNERS / (runner + ".sh")), "state", SESSION],
                                            env=env, text=True, capture_output=True, timeout=10)
                    self.assertEqual((result.returncode, result.stdout), (0, expected + "\n"), result.stderr)
