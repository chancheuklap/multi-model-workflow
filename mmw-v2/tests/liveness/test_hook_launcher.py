"""Host hooks through the installed launcher, against an isolated checkout and home."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
LAUNCHER = MMW / "hook-launcher.py"


def load_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HookPayload:
    """Host payloads and the deny or allow answer. The ticket number comes from the cwd."""

    def _close_command(self):
        directory = self.ticket if hasattr(self, "ticket") else self.issue
        return f"gh issue close {directory.name.removeprefix('issue-')}"

    def commands(self):
        command = self._close_command()
        return {
            "claude": {"tool_name": "Bash", "tool_input": {"command": command}},
            "codex": {"tool_name": "Bash", "tool_input": {"command": command}},
            "grok": {"toolName": "run_terminal_command", "toolInput": {"command": command}},
            "cursor": {"command": command, "cursor_version": "2026.09.08"},
            "pi": {"tool_name": "bash", "tool_input": {"command": command}},
        }

    def questions(self):
        return {
            "claude": {"tool_name": "AskUserQuestion", "tool_input": {}},
            "codex": {"tool_name": "request_user_input", "tool_input": {}},
            "grok": {"toolName": "ask_user_question", "toolInput": {}},
        }

    def denied(self, result, host):
        self.assertEqual(result.returncode, 0, result.stderr)
        answer = json.loads(result.stdout)
        if host in ("claude", "codex"):
            self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")
        elif host == "grok":
            self.assertEqual(answer["decision"], "deny")
        elif host == "cursor":
            self.assertEqual(answer["permission"], "deny")
        else:
            self.assertIs(answer["block"], True)
        self.assertEqual(result.stderr, "")

    def silent(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


class HookLauncher(HookPayload, unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / "checkout" / "mmw-v2"
        self.scripts = self.checkout / "skills" / "mmw" / "scripts"
        shutil.copytree(MMW / "skills" / "mmw" / "scripts", self.scripts,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.refusal = self.checkout / "skills" / "ui-acceptance" / "scripts" / "refusal.py"
        self.refusal.parent.mkdir(parents=True)
        shutil.copy2(MMW / "skills" / "ui-acceptance" / "scripts" / "refusal.py", self.refusal)
        self.home = self.root / "home"
        self.home.mkdir()
        (self.home / "installed-root").write_text(str(self.checkout) + "\n")
        self.ticket = self.root / "issue-608"
        self.workspace = self.root / "workspace"
        self.ticket.mkdir()
        self.workspace.mkdir()
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("MMW_", "NMEM_", "PASEO_", "ORCA_", "HERDR_",
                                         "GROK_", "CURSOR_", "PYTHON"))}
        self.env["MMW_HOME"] = str(self.home)

    def launch(self, hook, *args, managed=True, payload=None, env=None):
        return subprocess.run([sys.executable, str(LAUNCHER), hook, *args],
                              input=json.dumps(payload or {}), capture_output=True, text=True,
                              cwd=self.ticket if managed else self.workspace,
                              env={**self.env, **(env or {})}, timeout=15)

    def diagnostic(self, result, name, code):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)
        self.assertIn(name, result.stderr)
        self.assertIn("install.sh --check", result.stderr)

    def test_a_missing_tool_guard_refuses_in_a_ticket_worktree(self):
        (self.scripts / "tool-guard.py").unlink()
        result = self.launch("tool-guard", "pretool", "claude")
        self.diagnostic(result, "tool-guard", 2)

    def test_via_the_launcher_gh_issue_close_is_refused_in_a_ticket_worktree(self):
        for host, payload in self.commands().items():
            with self.subTest(host=host):
                result = self.launch("tool-guard", "pretool", host, payload=payload)
                self.denied(result, host)

    def test_the_launcher_prefers_the_mmw_scripts_candidate(self):
        preferred = self.checkout / "skills" / "mmw" / "scripts"
        (preferred / "tool-guard.py").write_text(
            "import sys\nprint('preferred')\nsys.exit(17)\n")
        legacy = self.checkout / "skills" / "dispatch" / "scripts"
        legacy.mkdir(parents=True)
        (legacy / "tool-guard.py").write_text("print('legacy')\n")
        result = self.launch("tool-guard", "pretool", "claude")
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(result.stdout, "preferred\n")
        self.assertEqual(result.stderr, "")
        (preferred / "tool-guard.py").unlink()
        fallback = self.launch("tool-guard", "pretool", "claude")
        self.assertEqual(fallback.returncode, 0, fallback.stderr)
        self.assertEqual(fallback.stdout, "legacy\n")
        self.assertEqual(fallback.stderr, "")

    def test_tool_guard_without_refusal_refuses_in_a_ticket_worktree(self):
        self.refusal.unlink()
        result = self.launch("tool-guard", "pretool", "claude")
        self.diagnostic(result, "refusal", 2)

    def test_turn_guard_without_statedir_prints_one_line_and_exits_0(self):
        (self.scripts / "statedir.py").unlink()
        result = self.launch("turn-guard", "stop", "claude")
        self.diagnostic(result, "statedir", 0)

    def test_via_the_launcher_gh_issue_close_passes_outside_a_ticket_worktree(self):
        for host, payload in self.commands().items():
            with self.subTest(host=host):
                self.silent(self.launch("tool-guard", "pretool", host,
                                        managed=False, payload=payload))

    def test_via_the_launcher_a_question_is_refused_in_a_ticket_worktree(self):
        for host, payload in self.questions().items():
            with self.subTest(host=host):
                self.denied(self.launch("tool-guard", "question", host, payload=payload), host)

    def test_via_the_launcher_a_question_passes_outside_a_ticket_worktree(self):
        for host, payload in self.questions().items():
            with self.subTest(host=host):
                self.silent(self.launch("tool-guard", "question", host,
                                        managed=False, payload=payload))

    def test_a_missing_tool_guard_passes_outside_a_ticket_worktree(self):
        (self.scripts / "tool-guard.py").unlink()
        self.silent(self.launch("tool-guard", "pretool", "claude", managed=False))

    def test_a_missing_turn_guard_prints_one_line_and_exits_0(self):
        (self.scripts / "turn-guard.py").unlink()
        result = self.launch("turn-guard", "stop", "claude")
        self.diagnostic(result, "turn-guard", 0)
        self.assertIn(str(self.checkout), result.stderr)

    def test_a_missing_mode_hook_prints_nothing_and_exits_0(self):
        (self.scripts / "mode-hook.py").unlink()
        self.silent(self.launch("mode-hook"))

    def marker_diagnostic(self, status):
        marker = self.home / "installed-root"
        for hook, code in (("tool-guard", 2), ("turn-guard", 0)):
            with self.subTest(hook=hook):
                result = self.launch(hook)
                self.diagnostic(result, hook, code)
                self.assertIn(str(marker), result.stderr)
                self.assertIn(status, result.stderr)
        self.silent(self.launch("tool-guard", managed=False))
        self.silent(self.launch("mode-hook"))

    def test_a_missing_installed_root_reports_the_marker_and_preserves_each_hooks_policy(self):
        (self.home / "installed-root").unlink()
        self.marker_diagnostic("missing")

    def test_an_empty_installed_root_reports_the_marker_and_preserves_each_hooks_policy(self):
        (self.home / "installed-root").write_text(" \n\t")
        self.marker_diagnostic("empty")

    def test_an_unreadable_installed_root_reports_the_marker_and_preserves_each_hooks_policy(self):
        marker = self.home / "installed-root"
        marker.unlink()
        marker.mkdir()
        self.marker_diagnostic("unreadable")

    def test_tool_guard_without_refusal_passes_outside_a_ticket_worktree(self):
        self.refusal.unlink()
        self.silent(self.launch("tool-guard", "pretool", "claude", managed=False))

    def test_both_hooks_import_every_companion_from_the_installed_layout(self):
        self.denied(self.launch("tool-guard", "pretool", "claude",
                               payload=self.commands()["claude"]), "claude")
        state = self.home / "state" / "o__r"
        state.mkdir(parents=True)
        (state / "watches.json").write_text(json.dumps({"tickets:608": {
            "tickets": [608], "runner": "fake", "session": "main-1"}}))
        runners = self.root / "runners"
        runners.mkdir()
        (runners / "fake.sh").write_text("#!/bin/sh\n[ \"$1\" = self ] && echo main-1\n")
        nodog = self.root / "nodog.py"
        nodog.write_text("import sys\nsys.exit(1)\n")
        result = self.launch("turn-guard", "stop", "claude", env={
            "MMW_RUNNERS_DIR": str(runners), "MMW_WATCHDOG_PY": str(nodog)},
            payload={"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("MMW turn guard:", result.stderr)
        self.assertNotIn("could not import", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        self.assertTrue((state / "guard.log").is_file())

    def companions(self, filename):
        """Local modules this hook imports or loads by path, and the ones those load."""
        scripts = self.scripts
        pending = [scripts / filename]
        seen = set()
        while pending:
            path = pending.pop()
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names.append(node.module.split(".")[0])
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if "/" not in node.value and node.value.endswith(".py"):
                        pending.append(scripts / node.value)
                for name in names:
                    pending.append(scripts / f"{name}.py")
        return {path.stem for path in seen if path.name != filename}

    def test_both_hooks_import_every_companion_from_mmw_scripts(self):
        tool = self.companions("tool-guard.py")
        turn = self.companions("turn-guard.py")
        self.assertIn("locations", tool)
        self.assertTrue({"statedir", "relay", "events"}.issubset(turn))
        self.test_both_hooks_import_every_companion_from_the_installed_layout()

    def test_the_managed_session_pattern_is_the_same_in_three_places(self):
        launcher = load_script(LAUNCHER, "mmw_launcher_pattern")
        guard = load_script(MMW / "skills" / "mmw" / "scripts" / "tool-guard.py",
                            "mmw_guard_pattern")
        locations = load_script(MMW / "skills" / "mmw" / "scripts" / "locations.py",
                                "mmw_locations_pattern")
        self.assertEqual(launcher.TICKET_DIR.pattern, guard.TICKET_DIR.pattern)
        self.assertEqual(launcher.TICKET_DIR.pattern, locations.GOVERNED_TICKET_DIR_PATTERN)

    def test_missing_tool_guard_also_governs_the_paseo_session_directory(self):
        (self.scripts / "tool-guard.py").unlink()
        result = self.launch("tool-guard", "question", "claude", managed=False,
                             env={"PASEO_AGENT_CWD": str(self.ticket)})
        self.diagnostic(result, "tool-guard", 2)

    def test_refusal_import_failure_also_governs_the_paseo_session_directory(self):
        self.refusal.unlink()
        result = self.launch("tool-guard", "question", "claude", managed=False,
                             env={"PASEO_AGENT_CWD": str(self.ticket)})
        self.diagnostic(result, "refusal", 2)

    def test_the_launcher_preserves_arguments_stdin_and_both_output_streams(self):
        (self.scripts / "tool-guard.py").write_text(
            "import sys\nprint(repr(sys.argv[1:]))\n"
            "print(sys.stdin.read())\nsys.stderr.write('target-stderr\\n')\nsys.exit(1)\n")
        result = self.launch("tool-guard", "pretool", "claude", "two words",
                             payload={"key": "value"})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout,
                         "['pretool', 'claude', 'two words']\n{\"key\": \"value\"}\n")
        self.assertEqual(result.stderr, "target-stderr\n")


if __name__ == "__main__":
    unittest.main()
