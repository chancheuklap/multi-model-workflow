import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/mmw-mode/scripts/session-start.py"
START = "Read the mmw-mode skill in full before anything else."
COMPACT = ("Your context was compacted: read the mmw-mode skill again in full, then the file "
           "you work by and every file its current step names, before you take that step.")


class SessionStart(unittest.TestCase):
    def run_hook(self, host, payload):
        return subprocess.run([sys.executable, str(SCRIPT), host], input=payload,
                              capture_output=True, text=True, timeout=5)

    def test_start_and_compaction_context_for_each_host(self):
        for host in ("claude", "codex"):
            for source in ("startup", "resume", "clear", "compact", "unknown", None):
                with self.subTest(host=host, source=source):
                    payload = {"hook_event_name": "SessionStart"}
                    if source is not None:
                        payload["source"] = source
                    run = self.run_hook(host, json.dumps(payload))
                    self.assertEqual((run.returncode, run.stderr), (0, ""))
                    output = json.loads(run.stdout) if run.stdout else {}
                    self.assertEqual(output.get("hookSpecificOutput"), {
                        "hookEventName": "SessionStart",
                        "additionalContext": COMPACT if source == "compact" else START})
                    self.assertEqual(len(run.stdout.splitlines()), 1)

    def test_errors_never_block_or_add_context(self):
        for host in ("claude", "codex", "unknown"):
            for payload in ("", "{", "[]", "null", '"compact"'):
                run = self.run_hook(host, payload)
                self.assertEqual((run.returncode, run.stdout), (0, ""))
        run = subprocess.run([sys.executable, str(SCRIPT)], input="{}",
                             capture_output=True, text=True, timeout=5)
        self.assertEqual((run.returncode, run.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
