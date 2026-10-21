import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


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
        dict(handle="term_recipient", connected=True, writable=True,
             **json.loads(os.environ["FAKE_ORCA_IDENTITY"]))
    ]}}))
elif args[:2] == ["terminal", "wait"]:
    print(os.environ["FAKE_ORCA_PROBE"])
    sys.exit(int(os.environ["FAKE_ORCA_PROBE_EXIT"]))
elif args[:2] == ["terminal", "send"]:
    answers = json.loads(os.environ["FAKE_ORCA_SENDS"])
    count = Path(os.environ["FAKE_ORCA_COUNT"])
    n = int(count.read_text()) if count.exists() else 0
    count.write_text(str(n + 1))
    answer = answers[min(n, len(answers) - 1)]
    print(json.dumps(answer, indent=2))
    sys.exit(0 if answer.get("ok", True) else 1)
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

    def send(self, probe, stages, probe_exit=0, identity=None, answers=None):
        self.log.unlink(missing_ok=True)
        (self.root / "count").unlink(missing_ok=True)
        env = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"],
                   MMW_HOME=str(self.root / "mmw-home"),
                   FAKE_ORCA_LOG=str(self.log), FAKE_ORCA_PROBE=probe,
                   FAKE_ORCA_IDENTITY=json.dumps(identity if identity is not None else {
                       "agentIdentity": "codex"}),
                   FAKE_ORCA_PROBE_EXIT=str(probe_exit),
                   FAKE_ORCA_COUNT=str(self.root / "count"),
                   FAKE_ORCA_SENDS=json.dumps(answers if answers is not None else [
                       {"result": {"send": {"prompt": {"stages": stages}}}}]))
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

    def test_send_types_into_a_terminal_with_no_agent_identity(self):
        probe = json.dumps({"error": {"code": "timeout"}})
        for terminal in [{}, {"agentIdentity": None}, {"agentIdentity": ""}]:
            with self.subTest(terminal=terminal):
                result, calls = self.send(probe, ["input_accepted"], probe_exit=1, identity=terminal)
                self.assertEqual(result.returncode, 4, result.stderr)
                self.assert_sent(calls)
                self.assertFalse(any(call[:2] == ["terminal", "wait"] for call in calls))

    def test_send_holds_the_text_when_an_agent_terminal_times_out(self):
        probe = json.dumps({"error": {"code": "timeout"}})
        result, calls = self.send(probe, ["input_accepted"], probe_exit=1)
        sends = [call for call in calls if call[:2] == ["terminal", "send"]]
        self.assertEqual((result.returncode, sends), (3, []), result.stderr)

    def test_send_types_the_text_when_orca_cannot_tell(self):
        probes = [
            "not-json",
            "{}",
            json.dumps({"error": {"code": "runtime_unavailable"}}),
        ]
        for probe in probes:
            with self.subTest(probe=probe):
                result, calls = self.send(probe, ["input_accepted"], probe_exit=1)
                self.assertEqual(result.returncode, 4, result.stderr)
                self.assert_sent(calls)

    def test_send_reads_the_identity_from_the_list_row(self):
        probe = json.dumps({"result": {"wait": {"satisfied": True}}})
        result, calls = self.send(probe, ["input_accepted", "turn_started"])
        shows = [call for call in calls if call[:2] == ["terminal", "show"]]
        self.assertEqual(shows, [])
        waits = [call for call in calls if call[:2] == ["terminal", "wait"]]
        self.assertEqual(len(waits), 1)
        wait = waits[0]
        self.assertEqual(wait[wait.index("--terminal") + 1], SESSION)
        self.assertEqual(wait[wait.index("--for") + 1], "tui-idle")
        self.assertIn("--json", wait)
        self.assertGreater(int(wait[wait.index("--timeout-ms") + 1]), 0)
        self.assertLessEqual(int(wait[wait.index("--timeout-ms") + 1]), 100)
        lists = [call for call in calls if call[:2] == ["terminal", "list"]]
        self.assertEqual(len(lists), 1)
        self.assertLess(calls.index(lists[0]), calls.index(wait))
        self.assertLess(calls.index(wait), next(i for i, call in enumerate(calls)
                                             if call[:2] == ["terminal", "send"]))
        self.assertEqual(result.returncode, 0, result.stderr)

    def request_ids(self, calls, count):
        sends = [call for call in calls if call[:2] == ["terminal", "send"]]
        self.assertEqual(len(sends), count)
        ids = []
        for call in sends:
            self.assertEqual(call.count("--retry-request"), 1)
            value = call[call.index("--retry-request") + 1]
            self.assertEqual(str(uuid.UUID(value)), value)
            ids.append(value)
        return ids

    def test_send_carries_one_request_id(self):
        ids = []
        for _ in range(2):
            result, calls = self.send("{}", ["input_accepted", "turn_started"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_sent(calls)
            ids.extend(self.request_ids(calls, 1))
        self.assertNotEqual(ids[0], ids[1])

    def test_send_treats_an_unknown_delivery_as_handed_over(self):
        for data in [{"deliveryOutcome": "unknown"}, {"retrySafe": False},
                     {"deliveryOutcome": "unknown", "retrySafe": False,
                      "orchestrationRequestId": "not-the-callers-id"}]:
            with self.subTest(data=data):
                answer = {"ok": False, "error": {"code": "runtime_error", "data": data,
                          "message": "Inspect the terminal; do not resend automatically."}}
                result, calls = self.send("{}", [], answers=[answer])
                self.assertEqual((result.returncode, result.stdout.strip()), (4, "unknown"))
                self.assertIn("text may be in the terminal", result.stderr)
                self.assertIn(answer["error"]["message"], result.stderr)
                self.assert_sent(calls)

    def test_send_replays_a_durable_error_under_the_same_id(self):
        durable = {"ok": False, "error": {"code": "runtime_unavailable", "data": {
            "orchestrationRequestId": "not-the-callers-id"}, "message": "Re-issue with the ID."}}
        cases = [
            ({"result": {"send": {"prompt": {"stages": ["turn_started"]}}}}, 0),
            ({"result": {"send": {"prompt": {"stages": ["input_accepted"]}}}}, 4),
            (durable, 3),
            ({"ok": False, "error": {"code": "runtime_unavailable", "message": "Unavailable."}}, 3),
            ({"ok": False, "error": {"code": "terminal_handle_stale"}}, 2),
            ({"ok": False, "error": {"code": "terminal_not_writable"}}, 2),
            ({"ok": False, "error": {"code": "runtime_error", "data": {
                "retrySafe": False}, "message": "Do not resend."}}, 4),
        ]
        for replay, code in cases:
            with self.subTest(replay=replay):
                result, calls = self.send("{}", [], answers=[durable, replay])
                self.assertEqual(result.returncode, code, result.stderr)
                if code == 4:
                    self.assertEqual(result.stdout.strip(), "unknown")
                if code == 3:
                    self.assertIn("delivery is unconfirmed", result.stderr)
                    self.assertNotIn("nothing was typed", result.stderr)
                ids = self.request_ids(calls, 2)
                self.assertEqual(ids[0], ids[1])
                sends = [call for call in calls if call[:2] == ["terminal", "send"]]
                self.assertEqual(sends[0], sends[1])

    def test_send_resends_after_a_plain_orca_error(self):
        for code in ["invalid_argument", "runtime_unavailable"]:
            with self.subTest(code=code):
                result, calls = self.send("{}", [], answers=[
                    {"ok": False, "error": {"code": code, "message": "Send refused."}}])
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assert_sent(calls)
