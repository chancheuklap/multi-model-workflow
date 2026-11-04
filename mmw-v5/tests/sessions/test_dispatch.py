from __future__ import annotations

import json
import fcntl
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import signal
import time
import unittest

from test_runner_adapters import VENDOR

TOOLS = Path(__file__).resolve().parents[2] / "tools/dispatch"
DISPATCH = TOOLS / "scripts/dispatch.sh"

PASEO = r'''#!/usr/bin/env python3
import fcntl, json, os, shlex, subprocess, sys
from pathlib import Path
p = Path(os.environ['FAKE_RUNNER_STATE'])
lock = open(str(p) + '.lock', 'a')
fcntl.flock(lock, fcntl.LOCK_EX)
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
    if os.environ.get('FAKE_EARLY_REPORT') == '1':
        prompt = shlex.split(a[-1])
        brief = Path(prompt[prompt.index('file') + 1])
        command = next(line for line in brief.read_text().splitlines() if line.startswith('MMW_HOME='))
        answer = p.with_name('early-answer.md')
        answer.write_text('42\n')
        child = subprocess.run(['bash', '-c', command.replace('<answer-file>', shlex.quote(str(answer)))],
            capture_output=True, text=True, env=dict(os.environ, PASEO_AGENT_ID=ident))
        s['early_report'] = {'returncode': child.returncode, 'stderr': child.stderr}
    print(json.dumps({'agentId': ident}))
elif a[:1] == ['ls']:
    print(json.dumps([{'id': 'parent', 'status': 'idle'}] + [{'id': k, **v} for k, v in s['sessions'].items()]))
    sys.exit(0)
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
temporary = p.with_name(p.name + '.tmp')
temporary.write_text(json.dumps(s))
temporary.replace(p)
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
            "from pathlib import Path\n"
            "if sys.argv[1:3] == ['repo','view']:\n"
            " assert sys.argv[3] == 'https://github.test/owner/project.git'\n"
            " assert 'GH_REPO' not in os.environ\n print('owner/project')\n"
            "elif sys.argv[1:3] == ['api','-i']:\n"
            " assert sys.argv[3].startswith('repos/owner/project/issues/61/comments?')\n"
            " print('HTTP/2 200 OK\\nETag: \\\"fixture\\\"\\n')\n"
            " print(Path(os.environ['FAKE_TICKET_COMMENTS']).read_text())\n"
            "else: raise AssertionError(sys.argv)\n")
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
        self.env["FAKE_TICKET_COMMENTS"] = str(self.root / "comments.json")
        Path(self.env["FAKE_TICKET_COMMENTS"]).write_text("[]")
        initialized = subprocess.run([sys.executable, str(TOOLS / "scripts/models.py"), "init"],
                                     env=self.env, capture_output=True, text=True)
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        config = json.loads((self.home / "models.json").read_text())
        config["runner"] = "paseo"
        config["rows"]["researcher"] = {"host": "codex", "model": "test-model", "effort": "high"}
        (self.home / "models.json").write_text(json.dumps(config))
        self.task = self.root / "任务 with 'quotes'.md"
        self.task.write_text("Read only this task.\nReturn the exact answer: 42.\n")
        self.addCleanup(self.stop_daemons)

    def stop_daemons(self):
        subprocess.run([sys.executable, str(TOOLS / "scripts/relay.py"), "stop", "--repo", "owner/project"],
                       env=self.env, capture_output=True, timeout=10)
        lock = self.home / "state/owner__project/watchdog.lock"
        text = lock.read_text() if lock.exists() else ""
        if text.strip():
            record = json.loads(text)
            try:
                os.kill(record["pid"], signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 5
            while lock.read_text().strip() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertFalse(lock.read_text().strip(), "owned test watchdog did not stop")

    def run_command(self, *args, env=None):
        return subprocess.run(["bash", str(DISPATCH), *map(str, args)], cwd=self.repo,
                              env=env or self.env, capture_output=True, text=True)

    def runner_data(self):
        with open(str(self.runner_state) + '.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return json.loads(self.runner_state.read_text())

    def write_runner(self, **values):
        with open(str(self.runner_state) + '.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads(self.runner_state.read_text())
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

    def cycle_after_stopping_owned_relay(self):
        state = self.home / "state/owner__project"
        lock = state / "relay.lock"
        text = lock.read_text() if lock.exists() else ""
        if text.strip():
            os.kill(json.loads(text)["pid"], signal.SIGTERM)
            deadline = time.monotonic() + 5
            while lock.read_text().strip() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertFalse(lock.read_text().strip())
        run = subprocess.run([sys.executable, str(TOOLS / "scripts/relay.py"), "run", "--repo", "owner/project", "--once"],
                             env=self.env, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def report_answer(self, brief, ident):
        answer = self.root / "answer.md"
        answer.write_text("42\n")
        run = self.run_command("report", brief, answer, env=dict(self.env, PASEO_AGENT_ID=ident))
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

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

    def test_each_brief_role_receives_dispatch_route_before_assignment_input(self):
        config = json.loads((self.home / "models.json").read_text())
        for role in ("researcher", "advisor", "candidate", "verifier"):
            config["rows"][role] = {"host": "codex", "model": "test-model", "effort": "high"}
        (self.home / "models.json").write_text(json.dumps(config))
        skill = TOOLS.parents[1] / "skills/dispatch/SKILL.md"
        for role in ("researcher", "advisor", "candidate", "verifier"):
            with self.subTest(role=role):
                sent = self.run_command("send", role, self.task)
                self.assertEqual(sent.returncode, 0, sent.stdout + sent.stderr)
                brief, ident = sent.stdout.strip().split("\t")
                prompt = self.runner_data()["sessions"][ident]["args"][-1]
                self.assertTrue(prompt.startswith(f"Assigned role: {role}."), prompt)
                route, assignment = prompt.split("\n\n", 1)
                self.assertIn(str(skill), shlex.split(route))
                self.assertIn("follow its route for your assigned role", route)
                self.assertIn("additional assignment input", route)
                self.assertEqual(prompt.count("Assigned role:"), 1)
                self.assertIn(str((self.batch_path(brief) / "1/brief.md").resolve()), shlex.split(assignment))

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

    def test_a_child_can_report_before_the_start_receipt_reaches_its_caller(self):
        run = self.run_command("send", "researcher", self.task, env=dict(self.env, FAKE_EARLY_REPORT="1"))
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        early = self.runner_data()["early_report"]
        self.assertEqual(early["returncode"], 0, early["stderr"])
        brief, ident = run.stdout.strip().split("\t")
        self.assertEqual((self.batch_path(brief) / "1/result.md").read_text(), "42\n")
        shown = self.run_command("brief", "show", brief.split("/")[0])
        self.assertIn("\treported\t", shown.stdout)

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
        self.assertEqual(json.loads((self.home / "state/owner__project/watches.json").read_text()), {})

    def test_all_answers_produce_one_recipient_notification_until_acknowledged(self):
        first, second = self.send(self.task, self.task)
        batch = first[0].split("/")[0]
        status = self.run_command("watchdog", "status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.report_answer(*first)
        self.cycle_after_stopping_owned_relay()
        queue = self.run_command("queue")
        self.assertEqual(queue.stdout, "")
        self.report_answer(*second)
        self.cycle_after_stopping_owned_relay()
        queue = self.run_command("queue")
        row = json.loads(queue.stdout)
        self.assertEqual((row["event"], row["runner"], row["session"]), ("brief.done", "paseo", "parent"))
        self.cycle_after_stopping_owned_relay()
        self.assertEqual(self.run_command("queue").stdout, queue.stdout)
        sends = [a for a in self.runner_data()["calls"] if a[0] == "send" and f"brief {batch} done" in a]
        self.assertEqual(len(sends), 1)
        acknowledged = self.run_command("ack", "brief", batch)
        self.assertEqual(acknowledged.returncode, 0, acknowledged.stderr)
        self.assertEqual(self.run_command("queue").stdout, "")
        self.assertNotEqual(self.run_command("ack", "brief", batch).returncode, 0)

    def test_another_session_cannot_acknowledge_the_waiting_sessions_result(self):
        [(brief, ident)] = self.send()
        self.report_answer(brief, ident)
        self.cycle_after_stopping_owned_relay()
        queued = self.run_command("queue").stdout
        self.assertTrue(queued)
        wrong = self.run_command("ack", "brief", brief.split("/")[0], env=dict(self.env, PASEO_AGENT_ID="other"))
        self.assertNotEqual(wrong.returncode, 0)
        self.assertEqual(self.run_command("queue").stdout, queued)

    def test_the_displayed_ticket_wake_can_be_acknowledged_with_its_hash_prefix(self):
        event = subprocess.run([sys.executable, str(TOOLS.parent / "verify-ticket/scripts/events.py"),
                                "emit", "ticket.passed", "--ticket", "61", "--line", "Complete"],
                               env=self.env, capture_output=True, text=True, check=True)
        Path(self.env["FAKE_TICKET_COMMENTS"]).write_text(json.dumps([
            {"id": 1, "body": event.stdout, "created_at": "2026-11-01T00:00:00Z", "updated_at": "2026-11-01T00:00:00Z"}]))
        opened = subprocess.run([sys.executable, str(TOOLS / "scripts/relay.py"), "add", "--repo", "owner/project",
                                 "--tickets", "61", "--runner", "paseo", "--session", "parent"],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(opened.returncode, 0, opened.stderr)
        self.cycle_after_stopping_owned_relay()
        self.assertEqual(json.loads(self.run_command("queue").stdout)["ticket"], 61)
        acknowledged = self.run_command("ack", "#61", "ticket.passed")
        self.assertEqual(acknowledged.returncode, 0, acknowledged.stdout + acknowledged.stderr)
        self.assertEqual(self.run_command("queue").stdout, "")

    def test_watchdog_start_failure_prevents_child_start_and_preserves_diagnostics(self):
        failed = self.root / "failed-watchdog.py"
        failed.write_text("raise SystemExit(1)\n")
        run = self.run_command("send", "researcher", self.task, env=dict(self.env, MMW_WATCHDOG_PY=str(failed)))
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertEqual(self.runner_data()["starts"], 0)
        state = self.home / "state/owner__project"
        self.assertEqual(json.loads((state / "watches.json").read_text()), {})
        self.assertEqual(len(list((state / "briefs").iterdir())), 1)
        self.assertIn("no child was started", run.stderr)

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
