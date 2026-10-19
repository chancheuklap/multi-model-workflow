import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ADAPTER = Path(__file__).resolve().parents[2] / "skills/dispatch/scripts/runners/orca.sh"
SESSION = "term_recipient"
TEXT = "#993 ticket.passed"
FAKE_ORCA = r'''
import json, os, sys
from pathlib import Path

args = sys.argv[1:]
with Path(os.environ["FAKE_ORCA_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")
if args[:2] == ["terminal", "list"]:
    print(json.dumps({"result": {"terminals": [
        {"handle": "term_recipient", "connected": True, "writable": True}
    ]}}))
elif args[:2] == ["terminal", "wait"]:
    print(os.environ["FAKE_ORCA_PROBE"])
    sys.exit(int(os.environ["FAKE_ORCA_PROBE_EXIT"]))
elif args[:2] == ["terminal", "send"]:
    print(json.dumps({"result": {"send": {"prompt": {
        "stages": json.loads(os.environ["FAKE_ORCA_STAGES"])
    }}}}))
else:
    sys.exit(99)
'''


class OrcaSend(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "calls.jsonl"
        fake = self.root / "orca"
        fake.write_text(f"#!{sys.executable}\n" + FAKE_ORCA)
        fake.chmod(0o755)

    def send(self, probe, stages, probe_exit=0):
        self.log.unlink(missing_ok=True)
        env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"],
                   MMW_HOME=str(self.root / "mmw-home"),
                   FAKE_ORCA_LOG=str(self.log), FAKE_ORCA_PROBE=probe,
                   FAKE_ORCA_PROBE_EXIT=str(probe_exit), FAKE_ORCA_STAGES=json.dumps(stages))
        result = subprocess.run(["bash", str(ADAPTER), "send", SESSION, TEXT],
                                env=env, capture_output=True, text=True, timeout=10)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result, calls

    def test_send_types_nothing_while_the_program_is_mid_turn(self):
        probes = [
            (json.dumps({"result": {"wait": {"satisfied": False, "status": "running"}}}), 0),
            (json.dumps({"error": {"code": "timeout"}}), 1),
        ]
        for probe, code in probes:
            with self.subTest(probe=probe):
                result, calls = self.send(probe, ["input_accepted"], code)
                sends = [call for call in calls if call[:2] == ["terminal", "send"]]
                self.assertEqual((result.returncode, sends), (3, []), result.stderr)

    def assert_sent(self, calls):
        sends = [call for call in calls if call[:2] == ["terminal", "send"]]
        self.assertEqual(len(sends), 1)
        self.assertEqual(sends[0][sends[0].index("--terminal") + 1], SESSION)
        self.assertEqual(sends[0][sends[0].index("--text") + 1], TEXT)
        self.assertIn("--enter", sends[0])

    def test_send_types_the_text_when_the_program_is_idle(self):
        probe = json.dumps({"result": {"wait": {"satisfied": True, "status": "running"}}})
        result, calls = self.send(probe, ["input_accepted", "turn_started"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_sent(calls)

    def test_send_types_the_text_when_orca_cannot_tell(self):
        probes = [
            "not-json",
            "{}",
            json.dumps({"result": {"wait": {"satisfied": False, "observation": "unsupported"}}}),
            json.dumps({"error": {"code": "runtime_unavailable"}}),
        ]
        for probe in probes:
            with self.subTest(probe=probe):
                result, calls = self.send(probe, ["input_accepted"], probe_exit=1)
                self.assertEqual(result.returncode, 4, result.stderr)
                self.assert_sent(calls)

    def test_send_probes_the_session_it_was_given(self):
        probe = json.dumps({"result": {"wait": {"satisfied": True}}})
        result, calls = self.send(probe, ["input_accepted", "turn_started"])
        waits = [call for call in calls if call[:2] == ["terminal", "wait"]]
        self.assertEqual(len(waits), 1)
        wait = waits[0]
        self.assertEqual(wait[wait.index("--terminal") + 1], SESSION)
        self.assertEqual(wait[wait.index("--for") + 1], "tui-idle")
        self.assertIn("--json", wait)
        self.assertGreater(int(wait[wait.index("--timeout-ms") + 1]), 0)
        self.assertLessEqual(int(wait[wait.index("--timeout-ms") + 1]), 100)
        self.assertLess(calls.index(wait), next(i for i, call in enumerate(calls)
                                             if call[:2] == ["terminal", "send"]))
        self.assertEqual(result.returncode, 0, result.stderr)
