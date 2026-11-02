from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from test_watchdog import SCRIPTS, StateCase, dog


class WatchdogCommands(StateCase):
    def setUp(self):
        super().setUp()
        self.runners = Path(self.tmp.name) / "runners"
        self.runners.mkdir()
        (self.runners / "fake.sh").write_text(
            'case "$1" in\n'
            '  liveness) echo stopped ;;\n'
            '  state) echo idle ;;\n'
            '  send) printf "%s\\n" "$2:$3" >> "$FAKE_SEND_LOG"; exit "${FAKE_SEND_EXIT:-4}" ;;\n'
            '  *) exit 3 ;;\n'
            'esac\n')
        binaries = Path(self.tmp.name) / "bin"
        binaries.mkdir()
        gh = binaries / "gh"
        gh.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GH_LOG"\nexit 88\n')
        gh.chmod(0o755)
        self.env = {**os.environ, "MMW_HOME": self.tmp.name,
                    "MMW_RUNNERS_DIR": str(self.runners),
                    "FAKE_SEND_LOG": str(Path(self.tmp.name) / "sent.log"),
                    "FAKE_GH_LOG": str(Path(self.tmp.name) / "gh.log"),
                    "PATH": str(binaries) + os.pathsep + os.environ.get("PATH", "")}

    def command(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "watchdog.py"), *args],
                              capture_output=True, text=True, env=self.env, timeout=5)

    def test_run_once_observes_a_stopped_brief_through_the_fake_runner(self):
        batch = dog.briefs.create(self.state, "researcher", 1, "fake", "parent")
        dog.briefs.mark_started(self.state, batch, 1, {
            "runner": "fake", "session": "child", "host": "codex",
            "model": "fake-model", "effort": "high"})
        self.write("watches.json", {f"briefs:{batch}": {
            "briefs": batch, "runner": "fake", "session": "parent"}})
        result = self.command("run", "--repo", "o/r", "--once")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(dog.briefs.briefs_of(self.state, batch)[0]["state"], "lost")
        beat = json.loads((self.state / "watchdog.json").read_text())
        self.assertEqual((beat["round"], beat["briefs"]), (1, []))
        self.assertTrue((Path(self.tmp.name) / "sent.log").read_text().startswith("parent:"))
        self.assertFalse((Path(self.tmp.name) / "gh.log").exists())

    def test_status_distinguishes_an_open_watch_from_a_running_watchdog(self):
        self.open_watches({"tickets": [61], "runner": "fake", "session": "parent"})
        result = self.command("status", "--repo", "o/r")
        self.assertEqual(result.returncode, 3, result.stderr)
        status = json.loads(result.stdout)
        self.assertFalse(status["healthy"])
        self.assertTrue(status["night_open"])
        self.assertIn("no watchdog is running", status["why"])

    def test_explicit_arm_reports_a_failed_test_process_without_starting_a_daemon(self):
        starter = Path(self.tmp.name) / "failed_watchdog.py"
        starter.write_text('print("deliberate startup failure")\nraise SystemExit(1)\n')
        self.env["MMW_WATCHDOG_PY"] = str(starter)
        result = self.command("arm", "--repo", "o/r", "--wait", "1")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("deliberate startup failure", result.stderr)
        self.assertIn("exited 1", result.stderr)
        self.assertIn("deliberate startup failure", (self.state / "watchdog.log").read_text())

    def test_run_once_with_no_watches_exits_and_records_closure(self):
        result = self.command("run", "--repo", "o/r", "--once")
        self.assertEqual(result.returncode, 0, result.stderr)
        beat = json.loads((self.state / "watchdog.json").read_text())
        self.assertTrue(beat["closed"])
        self.assertFalse((Path(self.tmp.name) / "gh.log").exists())

    def test_one_foreground_process_detects_a_later_loss_after_a_confirmed_alert(self):
        def new_batch():
            batch = dog.briefs.create(self.state, "researcher", 1, "fake", "parent")
            dog.briefs.mark_started(self.state, batch, 1, {
                "runner": "fake", "session": f"child-{batch}", "host": "codex",
                "model": "fake-model", "effort": "high"})
            watches = dog.statedir.read_json(self.state / "watches.json", {})
            watches[f"briefs:{batch}"] = {"briefs": batch, "runner": "fake", "session": "parent"}
            dog.statedir.write_atomic(self.state / "watches.json", json.dumps(watches))
            return batch

        first = new_batch()
        self.env["FAKE_SEND_EXIT"] = "0"
        process = subprocess.Popen(
            [sys.executable, str(SCRIPTS / "watchdog.py"), "run", "--repo", "o/r", "--poll", "1"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=self.env, cwd=self.state)

        def cleanup():
            if process.poll() is None:
                process.kill()
            process.communicate()

        self.addCleanup(cleanup)

        def wait_for(predicate):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                self.assertIsNone(process.poll(), "watchdog exited before the watches closed")
                if predicate():
                    return
                time.sleep(0.02)
            self.fail("isolated watchdog did not observe the expected state within 5 seconds")

        wait_for(lambda: (Path(self.tmp.name) / "sent.log").exists())
        self.assertEqual(dog.briefs.briefs_of(self.state, first)[0]["state"], "lost")
        second = new_batch()
        wait_for(lambda: dog.briefs.briefs_of(self.state, second)[0]["state"] == "lost")
        self.assertEqual(dog.statedir.holder(self.state / "watchdog.lock")["pid"], process.pid)
        self.assertEqual(len((Path(self.tmp.name) / "sent.log").read_text().splitlines()), 1)
        dog.statedir.write_atomic(self.state / "watches.json", "{}\n")
        output, errors = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, errors)
        self.assertIn("closed", output)
        self.assertFalse((Path(self.tmp.name) / "gh.log").exists())
