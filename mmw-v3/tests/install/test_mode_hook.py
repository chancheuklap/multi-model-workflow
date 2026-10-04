"""Context injection by mode-hook.py through stdin/stdout, in disposable repositories."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from install_home import MMW

SCRIPTS = MMW.joinpath("skills", "mmw-mode", "scripts")
HOOK = SCRIPTS / "mode-hook.py"
EVENTS = {"session-start": "SessionStart", "subagent-start": "SubagentStart",
          "prompt-submit": "UserPromptSubmit"}


def principles_heading():
    spec = importlib.util.spec_from_file_location("mode_hook_test_locations", SCRIPTS / "locations.py")
    locations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(locations)
    return locations.MODE_PRINCIPLES


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

    def copied_hook(self):
        hook = self.scratch.joinpath("checkout", "mmw-v3", "skills", "mmw-mode", "scripts", HOOK.name)
        hook.parent.mkdir(parents=True)
        shutil.copy2(HOOK, hook)
        return hook

    def test_prompt_submit_in_an_mmw_repository_injects_the_mode_line(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.assertEqual(
                    "New task here? Playbook match or rigor needed → apply the mmw-mode skill. "
                    "Casual turn or user opts out → don't.",
                    self.context(self.call("prompt-submit", host), "prompt-submit"))

    def test_an_issue_tracker_file_without_mmw_prints_nothing(self):
        # setup-matt-pocock-skills writes this file in repositories that do not use MMW.
        (self.repo / ".mmw").rmdir()
        tracker = self.repo / "docs/agents/issue-tracker.md"
        tracker.parent.mkdir(parents=True)
        tracker.touch()
        for event in EVENTS:
            for host in ("claude", "codex"):
                with self.subTest(event=event, host=host):
                    self.silent(self.call(event, host))

    def test_session_start_injects_the_prompt_submit_line_and_runs_nothing_else(self):
        # A dispatch.sh beside the hook would leave a mark if the hook ran it.
        copied = self.copied_hook()
        shutil.copy2(SCRIPTS / "locations.py", copied.with_name("locations.py"))
        mark = self.scratch / "dispatch-ran"
        copied.with_name("dispatch.sh").write_text(f"touch '{mark}'\necho 'AT worker #61'\n")
        expected = self.context(self.call("prompt-submit", hook=copied), "prompt-submit")
        ticket = self.repo / "issue-61" / "subdirectory"
        ticket.mkdir(parents=True)
        for cwd in (self.repo, ticket):
            for host in ("claude", "codex"):
                for source in ("startup", "resume", "compact"):
                    with self.subTest(cwd=cwd.name, host=host, source=source):
                        result = self.call("session-start", host, cwd=cwd, hook=copied,
                                           payload=json.dumps({"cwd": str(cwd), "source": source}))
                        self.assertEqual(expected, self.context(result, "session-start"))
        self.assertFalse(mark.exists())

    def test_subagent_start_names_the_mode_skill_and_its_principles_heading(self):
        expected = (f"Use the mmw-mode skill: read its `{principles_heading()}` "
                    "and the step you serve.")
        self.assertEqual("Use the mmw-mode skill: read its `## Principles` and the step you serve.",
                         expected)
        for host in ("claude", "codex"):
            self.assertEqual(expected, self.context(self.call("subagent-start", host), "subagent-start"))
        copied = self.copied_hook()
        self.silent(self.call("subagent-start", hook=copied))
        registry = copied.with_name("locations.py")
        shutil.copy2(SCRIPTS / "locations.py", registry)
        self.context(self.call("subagent-start", hook=copied), "subagent-start")
        registry.write_text("raise SystemExit(2)\n")
        self.silent(self.call("subagent-start", hook=copied))

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
        # A scope check that crashes silently must not pass the same fixture.
        (self.repo / ".mmw").mkdir()
        (plain / ".mmw").mkdir()
        for event in EVENTS:
            for host in ("claude", "codex"):
                self.context(self.call(event, host, cwd=cwd), event)
                self.context(self.call(event, host, cwd=plain), event)

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


if __name__ == "__main__":
    unittest.main()
