"""Host hooks through mmw-v3/hook-launcher.py, against an isolated checkout and home."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from install_home import MMW

LAUNCHER = MMW / "hook-launcher.py"


class HookPayload:
    """The answers a launched hook gives. The ticket number comes from the cwd."""

    def silent(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def injected(self, result, event):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], event)
        self.assertIn("mmw-mode", output["additionalContext"])

    def missing_line(self, result, name, code):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)
        self.assertIn(name, result.stderr)
        self.assertIn("bash mmw-v3/install.sh --check", result.stderr)


class HookLauncher(HookPayload, unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / "checkout" / "mmw-v3"
        self.scripts = self.checkout / "skills" / "mmw-mode" / "scripts"
        shutil.copytree(MMW / "skills" / "mmw-mode" / "scripts", self.scripts,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.home = self.root / "home"
        self.home.mkdir()
        (self.home / "installed-root").write_text(str(self.checkout) + "\n")
        self.ticket = self.root / "issue-608"
        self.workspace = self.root / "workspace"
        self.ticket.mkdir()
        (self.workspace / ".mmw").mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("MMW_", "NMEM_", "PASEO_", "ORCA_", "HERDR_",
                                         "GROK_", "CURSOR_", "PYTHON"))}
        self.env["MMW_HOME"] = str(self.home)

    def launch(self, hook, *args, managed=True, payload=None, env=None):
        return subprocess.run([sys.executable, str(LAUNCHER), hook, *args],
                              input=json.dumps(payload or {}), capture_output=True, text=True,
                              cwd=self.ticket if managed else self.workspace,
                              env={**self.env, **(env or {})}, timeout=15)

    def test_the_mode_hook_of_the_installed_checkout_injects_its_line(self):
        result = self.launch("mode-hook", "prompt-submit", "claude", managed=False,
                             payload={"cwd": str(self.workspace)})
        self.injected(result, "UserPromptSubmit")

    def test_a_missing_mode_hook_prints_nothing_and_exits_0(self):
        (self.scripts / "mode-hook.py").unlink()
        self.silent(self.launch("mode-hook", "prompt-submit", "claude", managed=False,
                                payload={"cwd": str(self.workspace)}))

    def test_tool_guard_has_no_script_and_refuses_only_in_a_ticket_worktree(self):
        self.assertFalse((self.scripts / "tool-guard.py").exists())
        self.missing_line(self.launch("tool-guard", "pretool", "claude"), "tool-guard", 2)
        self.silent(self.launch("tool-guard", "pretool", "claude", managed=False))

    def test_tool_guard_is_also_governed_by_the_paseo_session_directory(self):
        result = self.launch("tool-guard", "question", "claude", managed=False,
                             env={"PASEO_AGENT_CWD": str(self.ticket)})
        self.missing_line(result, "tool-guard", 2)

    def test_turn_guard_has_no_script_and_prints_one_line_and_exits_0(self):
        self.assertFalse((self.scripts / "turn-guard.py").exists())
        result = self.launch("turn-guard", "stop", "claude")
        self.missing_line(result, "turn-guard", 0)
        self.assertIn(str(self.checkout), result.stderr)

    def marker_diagnostic(self, status):
        marker = self.home / "installed-root"
        for hook, code in (("tool-guard", 2), ("turn-guard", 0)):
            with self.subTest(hook=hook):
                result = self.launch(hook)
                self.missing_line(result, hook, code)
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

    def test_the_launcher_looks_only_in_the_mmw_mode_scripts(self):
        legacy = self.checkout / "skills" / "mmw" / "scripts"
        legacy.mkdir(parents=True)
        (legacy / "turn-guard.py").write_text("print('legacy')\n")
        self.missing_line(self.launch("turn-guard", "stop", "claude"), "turn-guard", 0)
        (self.scripts / "turn-guard.py").write_text("import sys\nprint('mode')\nsys.exit(17)\n")
        result = self.launch("turn-guard", "stop", "claude")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (17, "mode\n", ""))

    def test_the_launcher_preserves_arguments_stdin_and_both_output_streams(self):
        (self.scripts / "mode-hook.py").write_text(
            "import sys\nprint(repr(sys.argv[1:]))\n"
            "print(sys.stdin.read())\nsys.stderr.write('target-stderr\\n')\nsys.exit(1)\n")
        result = self.launch("mode-hook", "prompt-submit", "claude", "two words",
                             payload={"key": "value"})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout,
                         "['prompt-submit', 'claude', 'two words']\n{\"key\": \"value\"}\n")
        self.assertEqual(result.stderr, "target-stderr\n")

    def test_an_unknown_hook_name_prints_the_usage_and_exits_0(self):
        result = self.launch("dispatch")
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("usage: hook-launcher", result.stderr)


if __name__ == "__main__":
    unittest.main()
