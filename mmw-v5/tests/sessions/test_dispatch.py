from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_runner_adapters import VENDOR

TOOLS = Path(__file__).resolve().parents[2] / "tools/dispatch"
DISPATCH = TOOLS / "scripts/dispatch.sh"

PASEO = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
p = Path(os.environ['FAKE_RUNNER_STATE'])
s = json.loads(p.read_text())
a = sys.argv[1:]
s['calls'].append(a)
if a[:1] == ['run']:
    s['starts'] += 1
    if s.get('fail_start') == s['starts']:
        p.write_text(json.dumps(s))
        print('start refused', file=sys.stderr)
        sys.exit(1)
    ident = 'child-' + str(s['starts'])
    s['sessions'][ident] = {'status': 'idle', 'args': a}
    print(json.dumps({'agentId': ident}))
elif a[:1] == ['ls']:
    print(json.dumps([{'id': k, **v} for k, v in s['sessions'].items()]))
elif a[:1] == ['archive']:
    ident = a[-1]
    if s.get('fail_stop') == ident:
        p.write_text(json.dumps(s))
        sys.exit(1)
    s['sessions'].pop(ident, None)
elif a[:1] == ['send']:
    print('sent')
else:
    raise AssertionError(a)
p.write_text(json.dumps(s))
'''


class DispatchCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin",
                        "https://github.test/owner/project.git"], check=True)
        self.home = self.root / "v5-home"
        self.home.mkdir()
        self.binary = self.root / "bin"
        self.binary.mkdir()
        (self.binary / "paseo").write_text(PASEO)
        (self.binary / "paseo").chmod(0o755)
        (self.binary / "gh").write_text("#!/usr/bin/env python3\nimport os,sys\n"
            "assert sys.argv[1:3] == ['repo','view']\n"
            "assert sys.argv[3] == 'https://github.test/owner/project.git'\n"
            "assert 'GH_REPO' not in os.environ\nprint('owner/project')\n")
        (self.binary / "gh").chmod(0o755)
        self.runner_state = self.root / "runner.json"
        self.runner_state.write_text(json.dumps({"calls": [], "starts": 0, "sessions": {}}))
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps({"paseo": {"codex": [
            {"id": "test-model", "name": "Test model", "thinkingOptionIds": ["medium", "high"]}]}}))
        self.env = dict(os.environ, MMW_HOME=str(self.home), MMW_RUNNER="paseo",
                        MMW_HOST_CATALOG=str(catalog), GH_REPO="wrong/repository",
                        PASEO_AGENT_ID="parent", FAKE_RUNNER_STATE=str(self.runner_state),
                        PATH=str(self.binary) + os.pathsep + os.environ["PATH"])
        initialized = subprocess.run([sys.executable, str(TOOLS / "scripts/models.py"), "init"],
                                     env=self.env, capture_output=True, text=True)
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        config = json.loads((self.home / "models.json").read_text())
        config["runner"] = "paseo"
        config["rows"]["researcher"] = {"host": "codex", "model": "test-model", "effort": "high"}
        (self.home / "models.json").write_text(json.dumps(config))
        self.task = self.root / "任务 with 'quotes'.md"
        self.task.write_text("Read only this task.\nReturn the exact answer: 42.\n")

    def run_command(self, *args, env=None):
        return subprocess.run(["bash", str(DISPATCH), *map(str, args)], cwd=self.repo,
                              env=env or self.env, capture_output=True, text=True)

    def runner_data(self):
        return json.loads(self.runner_state.read_text())

    def write_runner(self, **values):
        state = self.runner_data()
        state.update(values)
        self.runner_state.write_text(json.dumps(state))

    def send(self, *files, **options):
        args = ["send", "researcher"]
        if options.get("cwd"):
            args.extend(("--cwd", options["cwd"]))
        if options.get("follow"):
            args.extend(("--follow", options["follow"]))
        run = self.run_command(*args, *(files or [self.task]))
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        entries = [line.split("\t") for line in run.stdout.splitlines()]
        return entries

    def batch_path(self, brief):
        return self.home / "state/owner__project/briefs" / brief.split("/")[0]

    def test_task_model_directory_and_report_destination_reach_the_runner(self):
        folder = self.repo / "sub folder"
        folder.mkdir()
        follow = self.root / "rules.md"
        follow.write_text("Caller-supplied rules\n")
        [(brief, ident)] = self.send(cwd=folder, follow=follow)
        args = self.runner_data()["sessions"][ident]["args"]
        self.assertEqual(args[args.index("--provider") + 1], "codex/test-model")
        self.assertEqual(args[args.index("--thinking") + 1], "high")
        self.assertEqual(args[args.index("--cwd") + 1], str(folder.resolve()))
        values = [args[i+1] for i, arg in enumerate(args) if arg == "--env"]
        self.assertIn("GH_REPO=owner/project", values)
        self.assertIn("MMW_HOME=" + str(self.home.resolve()), values)
        self.assertIn("MMW_RUNNER=paseo", values)
        self.assertIn(str(follow), args[-1])
        copied = self.batch_path(brief) / "1/brief.md"
        text = copied.read_text()
        self.assertTrue(text.startswith(self.task.read_text() + "\n"))
        self.assertIn("report " + brief, text)
        self.assertIn(str(DISPATCH), text)
        for absent in ("mmw-mode", "register-problem", "## Problems", "playwright-cli", "work-a-ticket"):
            self.assertNotIn(absent, text + args[-1])

    def test_only_recorded_child_can_report_and_first_answer_is_kept(self):
        [(brief, ident)] = self.send()
        answer = self.root / "answer.md"
        answer.write_text("42\n")
        wrong = self.run_command("report", brief, answer)
        self.assertEqual(wrong.returncode, 2)
        self.assertFalse((self.batch_path(brief) / "1/result.md").exists())
        child = dict(self.env, PASEO_AGENT_ID=ident)
        right = self.run_command("report", brief, answer, env=child)
        self.assertEqual(right.returncode, 0, right.stderr)
        answer.write_text("changed\n")
        again = self.run_command("report", brief, answer, env=child)
        self.assertEqual(again.returncode, 2)
        self.assertEqual((self.batch_path(brief) / "1/result.md").read_text(), "42\n")
        shown = self.run_command("brief", "show", brief.split("/")[0])
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("\treported\t", shown.stdout)
        self.assertIn("result.md", shown.stdout)

    def test_resume_reuses_the_session_and_stop_records_loss_without_an_answer(self):
        [(brief, ident)] = self.send()
        resumed = self.run_command("resume", brief, "Continue with the caller's correction")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(self.runner_data()["starts"], 1)
        self.assertTrue(any(call[0] == "send" and ident in call for call in self.runner_data()["calls"]))
        stopped = self.run_command("stop", brief)
        self.assertEqual(stopped.returncode, 0, stopped.stderr)
        self.assertNotIn(ident, self.runner_data()["sessions"])
        self.assertTrue((self.batch_path(brief) / "1/lost.json").is_file())
        self.assertFalse((self.batch_path(brief) / "1/result.md").exists())
        self.assertEqual(self.run_command("resume", brief, "resume").returncode, 2)

    def test_resume_preserves_unconfirmed_delivery_instead_of_reporting_refusal(self):
        [(brief, ident)] = self.send()
        recorded = self.batch_path(brief) / "1/started.json"
        record = json.loads(recorded.read_text())
        record.update(runner="herdr", session="session-1")
        recorded.write_text(json.dumps(record))
        vendor = self.binary / "herdr"
        vendor.write_text(VENDOR)
        vendor.chmod(0o755)
        env = dict(self.env, VENDOR_LOG=str(self.root / "vendor.jsonl"), SEND_MODE="uncertain")
        run = self.run_command("resume", brief, "Continue", env=env)
        self.assertEqual(run.returncode, 4, run.stdout + run.stderr)

    def test_all_task_files_are_checked_before_any_session_starts(self):
        run = self.run_command("send", "researcher", self.task, self.root / "missing.md")
        self.assertEqual(run.returncode, 2)
        self.assertEqual(self.runner_data()["starts"], 0)
        self.assertFalse((self.home / "state/owner__project/briefs").exists())

    def test_second_start_failure_stops_the_first_without_retry(self):
        self.write_runner(fail_start=2)
        run = self.run_command("send", "researcher", self.task, self.task)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        state = self.runner_data()
        self.assertEqual(state["starts"], 2)
        self.assertEqual(state["sessions"], {})
        batches = list((self.home / "state/owner__project/briefs").iterdir())
        self.assertEqual(len(batches), 1)
        self.assertTrue((batches[0] / "1/lost.json").is_file())
        self.assertTrue((batches[0] / "2/lost.json").is_file())
        self.assertIn("start refused", (batches[0] / "2/start.stderr").read_text())
        self.assertEqual(run.stdout, "")

    def test_failed_cleanup_preserves_records_and_can_be_retried(self):
        [(brief, ident)] = self.send()
        self.write_runner(fail_stop=ident)
        batch = brief.split("/")[0]
        failed = self.run_command("brief", "close", batch)
        self.assertEqual(failed.returncode, 2)
        self.assertTrue(self.batch_path(brief).is_dir())
        self.write_runner(fail_stop=None)
        closed = self.run_command("brief", "close", batch)
        self.assertEqual(closed.returncode, 0, closed.stderr)
        self.assertFalse(self.batch_path(brief).exists())

    def test_empty_and_missing_config_do_not_start_a_session(self):
        self.task.write_text("")
        self.assertEqual(self.run_command("send", "researcher", self.task).returncode, 2)
        self.task.write_text("A task\n")
        (self.home / "models.json").unlink()
        run = self.run_command("send", "researcher", self.task)
        self.assertEqual(run.returncode, 2)
        self.assertIn("models.py init", run.stderr)
        self.assertEqual(self.runner_data()["starts"], 0)


if __name__ == "__main__":
    unittest.main()
