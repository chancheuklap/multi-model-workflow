"""The hook launcher an isolated install writes, against that install's checkout."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from install_home import calls, copy_mmw, run_install, write_fakes
from test_hook_launcher import HookPayload

_STRIP_PREFIXES = ("MMW_", "NMEM_", "PASEO_", "ORCA_", "HERDR_", "GROK_", "CURSOR_", "PYTHON")
_STRIP_EXACT = {"CODEX_HOME", "PI_HOME", "PI_CODING_AGENT_DIR"}


class InstalledLauncher(HookPayload, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = tempfile.TemporaryDirectory()
        cls.root = Path(cls.raw.name)
        cls.home = cls.root / "home"
        (cls.home / ".claude").mkdir(parents=True)
        cls.issue = cls.root / "issue-61"
        cls.workspace = cls.root / "workspace"
        cls.issue.mkdir()
        (cls.workspace / ".mmw").mkdir(parents=True)
        cls.checkout = copy_mmw(cls.root)
        bin_dir = cls.root / "bin"
        write_fakes(bin_dir)
        log = cls.root / "install-calls.log"
        result = run_install(cls.checkout / "install.sh", cls.home, bin_dir,
                             env_overrides={"MMW_TEST_SERVICE_LOG": str(log)})
        if result.returncode != 0:
            raise AssertionError(
                f"install exited {result.returncode}\n{result.stderr[-4000:]}\n{result.stdout[-2000:]}")
        made = calls(log)
        if not [call for call in made if call[0] == "orca"]:
            raise AssertionError(f"install did not call the fake orca: {made}")
        forbidden = [call for call in made if call[0] in ("launchctl", "nmem") or "reload" in call]
        if forbidden:
            raise AssertionError(f"install called a service it must not: {forbidden}")
        cls.launcher = cls.home / ".mmw" / "bin" / "hook-launcher"
        if not cls.launcher.is_file() or cls.launcher.is_symlink():
            raise AssertionError(f"installed launcher missing: {cls.launcher}")
        if cls.launcher.read_bytes() != (cls.checkout / "hook-launcher.py").read_bytes():
            raise AssertionError("installed launcher differs from its source")
        recorded = Path((cls.home / ".mmw" / "installed-root").read_text(encoding="utf-8").strip())
        if recorded.resolve() != cls.checkout.resolve():
            raise AssertionError(f"installed-root does not name this copy: {recorded} != {cls.checkout}")
        cls.scripts = cls.checkout / "skills" / "mmw-mode" / "scripts"
        cls.env = {key: value for key, value in os.environ.items()
                   if not key.startswith(_STRIP_PREFIXES) and key not in _STRIP_EXACT}
        cls.env["HOME"] = str(cls.home)
        cls.env["MMW_HOME"] = str(cls.home / ".mmw")

    @classmethod
    def tearDownClass(cls):
        cls.raw.cleanup()

    def launch(self, hook, *args, managed=True, payload=None):
        return subprocess.run(
            [sys.executable, str(self.launcher), hook, *args],
            input=json.dumps(payload or {}), capture_output=True, text=True,
            cwd=self.issue if managed else self.workspace, env=self.env, timeout=20)

    @contextmanager
    def moved(self, name):
        path = self.scripts / name
        held = path.with_name(path.name + ".held")
        path.rename(held)
        try:
            yield
        finally:
            if held.exists() and not path.exists():
                held.rename(path)

    def test_installed_launcher_injects_the_mode_line_and_passes_silently_without_it(self):
        payload = {"cwd": str(self.workspace)}
        for event, name in (("session-start", "SessionStart"), ("subagent-start", "SubagentStart"),
                            ("prompt-submit", "UserPromptSubmit")):
            with self.subTest(event=event):
                self.injected(self.launch("mode-hook", event, "claude", payload=payload), name)
        with self.moved("mode-hook.py"):
            self.silent(self.launch("mode-hook", "prompt-submit", "claude", payload=payload))

    def test_installed_launcher_refuses_tool_guard_only_in_a_ticket_worktree(self):
        self.missing_line(self.launch("tool-guard", "pretool", "claude"), "tool-guard", 2)
        self.silent(self.launch("tool-guard", "pretool", "claude", managed=False))

    def test_installed_launcher_reports_turn_guard_in_one_line_and_passes(self):
        self.missing_line(self.launch("turn-guard", "stop", "claude"), "turn-guard", 0)


if __name__ == "__main__":
    unittest.main()
