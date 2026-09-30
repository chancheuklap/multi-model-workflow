"""Exercise context injection through stdin/stdout in disposable repositories."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


MMW = Path(__file__).resolve().parents[2]
HOOK = MMW.joinpath("skills", "mmw", "scripts", "mode-hook.py")
DISPATCH = MMW.joinpath("skills", "dispatch", "scripts", "dispatch.sh")
EVENTS = {"session-start": "SessionStart", "subagent-start": "SubagentStart",
          "prompt-submit": "UserPromptSubmit"}


class ModeHookTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)
        self.repo = self.scratch / "repo"
        (self.repo / ".git").mkdir(parents=True)
        (self.repo / ".mmw").mkdir()
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("MMW_", "NMEM_", "PASEO_", "HERDR_", "ORCA_"))
                    and k != "TERM_PROGRAM"}
        self.env["MMW_HOME"] = str(self.scratch / "state-home")

    def call(self, event, host="claude", *, cwd=None, payload=None, hook=HOOK):
        cwd = cwd or self.repo
        if payload is None:
            payload = json.dumps({"cwd": str(cwd)})
        return subprocess.run([sys.executable, str(hook), event, host], cwd=cwd,
                              env=self.env, input=payload, capture_output=True,
                              text=True, timeout=30)

    def context(self, result, event):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout, "hook did not inject context")
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], EVENTS[event])
        line = output["additionalContext"]
        self.assertIsInstance(line, str)
        self.assertTrue(line.strip())
        self.assertNotIn("\n", line)
        self.assertNotIn("\r", line)
        return line

    def silent(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def tracker(self):
        spec = importlib.util.spec_from_file_location(
            "mode_hook_events", MMW.joinpath("skills", "verify-ticket", "scripts", "events.py"))
        events = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(events)
        comment = events.build(
            "worker.started", ticket=61, line="worker started", at="2026-09-30T00:00:00Z",
            runner="paseo", session="me", machine="fixture", host="codex", model="fixture",
            effort="high", grade="senior-worker", worktree=str(self.repo / "issue-61"),
            branch="issue-61", base="0" * 40)
        self.ticket_file = self.scratch / "ticket.json"
        self.ticket_file.write_text(json.dumps({
            "number": 61, "state": "OPEN", "title": "Fixture", "body": "",
            "labels": [{"name": "ready-for-agent"}], "assignees": [],
            "blockedBy": {"nodes": []}, "comments": [{"body": comment}]}))
        self.calls = self.scratch / "gh-calls"
        bin_dir = self.scratch / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['FAKE_CALLS'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
if args[:2] == ['repo', 'view']:
    print('o/r')
elif args[:3] == ['issue', 'view', '61']:
    print(Path(os.environ['FAKE_TICKET']).read_text())
else:
    raise SystemExit(2)
""")
        gh.chmod(0o755)
        self.env.update(PATH=str(bin_dir) + os.pathsep + self.env.get("PATH", ""),
                        FAKE_CALLS=str(self.calls), FAKE_TICKET=str(self.ticket_file),
                        PASEO_AGENT_ID="me")

    def where(self, cwd):
        result = subprocess.run(["bash", str(DISPATCH), "where"], cwd=cwd, env=self.env,
                                text=True, capture_output=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertTrue(result.stdout.startswith(("FRESH ", "AT ", "BETWEEN ")))
        return result.stdout.rstrip("\n")

    def watch(self, *, runner="paseo", session="me", repository="o__r"):
        path = Path(self.env["MMW_HOME"]) / "state" / repository / "watches.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"fixture": {
            "runner": runner, "session": session, "kind": "ticket", "tickets": [61]}}))

    def copied_hook(self):
        hook = self.scratch.joinpath("checkout", "mmw-v2", "skills", "mmw", "scripts", HOOK.name)
        hook.parent.mkdir(parents=True)
        shutil.copy2(HOOK, hook)
        return hook

    def test_prompt_submit_in_an_mmw_repository_injects_one_line(self):
        for marker in (".mmw", "tracker"):
            if marker == "tracker":
                (self.repo / ".mmw").rmdir()
                tracker = self.repo / "docs/agents/issue-tracker.md"
                tracker.parent.mkdir(parents=True)
                tracker.touch()
            for host in ("claude", "codex"):
                with self.subTest(marker=marker, host=host):
                    self.context(self.call("prompt-submit", host), "prompt-submit")

    def test_session_start_in_a_ticket_worktree_injects_the_where_line(self):
        self.tracker()
        cwd = self.repo / "issue-61/subdirectory"
        cwd.mkdir(parents=True)
        expected = self.where(cwd)
        for host in ("claude", "codex"):
            for source in ("startup", "resume", "compact"):
                with self.subTest(host=host, source=source):
                    result = self.call("session-start", host, cwd=cwd,
                                       payload=json.dumps({"cwd": str(cwd), "source": source}))
                    self.assertEqual(self.context(result, "session-start"), expected)

    def test_outside_an_mmw_repository_every_event_prints_nothing(self):
        (self.repo / ".mmw").rmdir()
        (self.scratch / ".mmw").mkdir()
        cwd = self.repo / "child"
        cwd.mkdir()
        for event in EVENTS:
            for host in ("claude", "codex"):
                with self.subTest(event=event, host=host):
                    self.silent(self.call(event, host, cwd=cwd))
        # With no git ancestor, only the current directory is in scope.
        plain = self.scratch / "plain"
        plain.mkdir()
        for event in EVENTS:
            self.silent(self.call(event, cwd=plain))

    def test_subagent_start_in_an_mmw_repository_injects_one_line(self):
        for host in ("claude", "codex"):
            self.context(self.call("subagent-start", host), "subagent-start")

    def test_session_start_of_a_watch_s_orchestrator_injects_the_where_line(self):
        self.tracker()
        self.watch()
        expected = self.where(self.repo)
        for host in ("claude", "codex"):
            self.assertEqual(self.context(self.call("session-start", host), "session-start"), expected)

    def test_session_start_outside_the_pipeline_injects_the_reminder_and_asks_no_tracker(self):
        self.tracker()
        expected = self.context(self.call("prompt-submit"), "prompt-submit")
        for identity in ("me", None):
            if identity is None:
                self.env.pop("PASEO_AGENT_ID")
            for host in ("claude", "codex"):
                self.assertEqual(self.context(self.call("session-start", host), "session-start"), expected)
        self.watch(runner="orca")
        self.env["PASEO_AGENT_ID"] = "me"
        self.assertEqual(self.context(self.call("session-start"), "session-start"), expected)
        self.watch(session="someone-else")
        self.assertEqual(self.context(self.call("session-start"), "session-start"), expected)
        self.assertFalse(self.calls.exists(), "ordinary sessions contacted the tracker")

    def test_a_where_that_cannot_answer_prints_nothing_and_exits_zero(self):
        self.tracker()
        cwd = self.repo / "issue-61"
        cwd.mkdir()
        self.context(self.call("session-start", cwd=cwd), "session-start")
        self.env.pop("PASEO_AGENT_ID")
        result = subprocess.run(["bash", str(DISPATCH), "where"], cwd=cwd, env=self.env,
                                capture_output=True, text=True, timeout=25)
        self.assertNotEqual(result.returncode, 0)
        for host in ("claude", "codex"):
            self.silent(self.call("session-start", host, cwd=cwd))

    def test_a_checkout_without_dispatch_prints_nothing_and_exits_zero(self):
        self.tracker()
        cwd = self.repo / "issue-61"
        cwd.mkdir()
        self.context(self.call("session-start", cwd=cwd), "session-start")
        copied = self.copied_hook()
        self.silent(self.call("session-start", cwd=cwd, hook=copied))
        shutil.copy2(DISPATCH.with_name("locations.py"), copied.with_name("locations.py"))
        self.silent(self.call("session-start", cwd=cwd, hook=copied))
        copied.with_name("locations.py").write_text("raise SystemExit(2)\n")
        self.silent(self.call("session-start", cwd=cwd, hook=copied))

    def test_an_unreadable_payload_prints_nothing_and_exits_zero(self):
        for event in EVENTS:
            for host in ("claude", "codex"):
                self.context(self.call(event, host), event)
                for payload in ("not json", "[]", "null", '{"cwd": 1}'):
                    self.silent(self.call(event, host, payload=payload))

    def test_the_launcher_reaches_the_mode_hook_of_the_installed_checkout(self):
        marker = Path(self.env["MMW_HOME"]) / "installed-root"
        marker.parent.mkdir()
        marker.write_text(str(MMW) + "\n")
        for host in ("claude", "codex"):
            result = subprocess.run([sys.executable, str(MMW / "hook-launcher.py"),
                                     "mode-hook", "prompt-submit", host], cwd=self.repo,
                                    env=self.env, input=json.dumps({"cwd": str(self.repo)}),
                                    text=True, capture_output=True, timeout=25)
            self.context(result, "prompt-submit")

    def test_payload_cwd_and_process_cwd_are_scoped_without_host_environment_inference(self):
        child = self.repo / "child"
        child.mkdir()
        self.env.update(GROK_AGENT="inherited", CURSOR_AGENT="inherited")
        self.context(self.call("prompt-submit", cwd=child, payload="{}"), "prompt-submit")
        outside = self.scratch / "outside"
        (outside / ".git").mkdir(parents=True)
        self.silent(self.call("prompt-submit", payload=json.dumps({"cwd": str(outside)})))
        plain = self.scratch / "plain-mmw"
        (plain / ".mmw").mkdir(parents=True)
        self.context(self.call("prompt-submit", cwd=plain), "prompt-submit")
        for event, host in (("unknown", "claude"), ("prompt-submit", "unknown")):
            self.silent(self.call(event, host))

    def test_watch_lookup_scans_other_repositories_and_bad_state_is_silent(self):
        self.tracker()
        self.watch(repository="else__where")
        # Candidate detection spans all repositories; where still uses this repo.
        # Its nonzero UNKNOWN response must not be injected as a reminder.
        self.silent(self.call("session-start"))
        path = Path(self.env["MMW_HOME"]) / "state/else__where/watches.json"
        path.write_text("not json")
        self.silent(self.call("session-start"))

    def test_a_stalled_where_times_out_silently_before_the_host_deadline(self):
        copied = self.copied_hook()
        shutil.copy2(DISPATCH.with_name("locations.py"), copied.with_name("locations.py"))
        scripts = copied.parents[2] / "dispatch/scripts"
        scripts.mkdir(parents=True)
        dispatch = scripts / "dispatch.sh"
        dispatch.write_text("echo 'AT worker #61'\n")
        cwd = self.repo / "issue-61"
        cwd.mkdir()
        self.context(self.call("session-start", cwd=cwd, hook=copied), "session-start")
        # A child retains bash's pipes: the deadline must terminate descendants too.
        dispatch.write_text("python3 -c 'import time; time.sleep(60)'\n")
        before = time.monotonic()
        self.silent(self.call("session-start", cwd=cwd, hook=copied))
        elapsed = time.monotonic() - before
        self.assertGreaterEqual(elapsed, 19)
        self.assertLess(elapsed, 25)


if __name__ == "__main__":
    unittest.main()
