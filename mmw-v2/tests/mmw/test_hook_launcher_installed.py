"""The hook launcher an isolated install writes, against that install's checkout."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
REPO = MMW.parent
DISPATCH_TESTS = Path(__file__).resolve().parents[1] / "dispatch"
LIVENESS = Path(__file__).resolve().parents[1] / "liveness"
sys.path.insert(0, str(DISPATCH_TESTS))
sys.path.insert(0, str(LIVENESS))
from install_home import run_install, write_fakes
from test_hook_launcher import HookPayload, load_script

_STRIP_PREFIXES = ("MMW_", "NMEM_", "PASEO_", "ORCA_", "HERDR_", "GROK_", "CURSOR_", "PYTHON")
_STRIP_EXACT = {"CODEX_HOME", "PI_HOME", "PI_CODING_AGENT_DIR"}


def _clean_env() -> dict:
    return {key: value for key, value in os.environ.items()
            if not key.startswith(_STRIP_PREFIXES) and key not in _STRIP_EXACT}


def _remove_tree(path: Path) -> None:
    """Delete a tree. macOS rmdir reports ENOTEMPTY when an entry appears mid-walk."""
    last = None
    for _ in range(8):
        if not path.exists():
            return
        try:
            shutil.rmtree(path)
        except OSError as err:
            last = err
            time.sleep(0.1)
            continue
        if not path.exists():
            return
    raise AssertionError(f"could not remove {path}: {last}")


def _record_fakes(bin_dir: Path, log: Path) -> None:
    """Fakes install.sh calls, first on PATH. nmem and orca answer as install_home does."""
    bin_dir.mkdir(parents=True)
    write_fakes(bin_dir)
    for name in ("nmem", "orca"):
        body = bin_dir / f".{name}-body"
        (bin_dir / name).rename(body)
        wrapper = bin_dir / name
        wrapper.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"{name} $*\" >> \"{log}\"\n"
            f"exec \"{body}\" \"$@\"\n",
            encoding="utf-8")
        wrapper.chmod(0o755)
    for name in ("paseo", "herdr", "launchctl", "gh"):
        path = bin_dir / name
        path.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"{name} $*\" >> \"{log}\"\n"
            "exit 0\n",
            encoding="utf-8")
        path.chmod(0o755)


class InstalledLauncher(HookPayload, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp())
        cls.addClassCleanup(_remove_tree, cls.root)
        cls.home = cls.root / "home"
        cls.clone = cls.root / "clone"
        cls.log = cls.root / "install-calls.log"
        cls.issue = cls.root / "issue-61"
        cls.workspace = cls.root / "workspace"
        cls.issue.mkdir()
        cls.workspace.mkdir()
        cls.nodog = cls.root / "nodog.py"
        cls.nodog.write_text(
            "import sys\nsys.stderr.write('this watchdog does not start\\n')\nsys.exit(1)\n",
            encoding="utf-8")
        head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()
        subprocess.run(["git", "clone", "--local", "--no-checkout", str(REPO), str(cls.clone)],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(cls.clone), "checkout", "--detach", head],
                       check=True, capture_output=True, text=True)
        _record_fakes(cls.root / "bin", cls.log)
        # run_install keeps this process's hook and interpreter variables.
        # install.sh must not see them: a PASEO_ or PYTHON* value would change
        # what the install records, and GROK_* makes a host hook stand down.
        saved = {key: os.environ.pop(key) for key in list(os.environ)
                 if key.startswith(_STRIP_PREFIXES) or key in _STRIP_EXACT}
        try:
            result = run_install(cls.clone / "mmw-v2" / "install.sh", cls.home, cls.root / "bin")
        finally:
            os.environ.update(saved)
        if result.returncode != 0:
            raise AssertionError(
                f"install exited {result.returncode}\n{result.stderr[-4000:]}\n{result.stdout[-2000:]}")
        calls = cls.log.read_text(encoding="utf-8") if cls.log.is_file() else ""
        if "nmem " not in calls or "orca " not in calls:
            raise AssertionError(f"install did not call the fake nmem and orca:\n{calls}")
        for forbidden in ("launchctl bootout", "launchctl bootstrap", "paseo reload"):
            if forbidden in calls:
                raise AssertionError(f"install called {forbidden}:\n{calls}")
        cls.launcher = cls.home / ".mmw" / "bin" / "hook-launcher"
        if not cls.launcher.is_file() or cls.launcher.is_symlink():
            raise AssertionError(f"installed launcher missing: {cls.launcher}")
        recorded = Path((cls.home / ".mmw" / "installed-root").read_text(encoding="utf-8").strip())
        expected = (cls.clone / "mmw-v2").resolve()
        if recorded.resolve() != expected:
            raise AssertionError(
                f"installed-root does not name this clone's scripts: {recorded} != {expected}")
        cls.installed_root = expected
        cls.scripts = cls.installed_root / "skills" / "mmw" / "scripts"
        # The fake nmem is only for install.sh. Left on disk, a later call
        # recreates the log while the tree is being removed.
        _remove_tree(cls.root / "bin")
        cls.env = _clean_env()
        cls.env["HOME"] = str(cls.home)
        cls.env["MMW_HOME"] = str(cls.home / ".mmw")
        cls.env["MMW_WATCHDOG_PY"] = str(cls.nodog)

    def launch(self, hook, *args, managed=True, payload=None):
        return subprocess.run(
            [sys.executable, str(self.launcher), hook, *args],
            input=json.dumps(payload or {}), capture_output=True, text=True,
            cwd=self.issue if managed else self.workspace, env=self.env, timeout=20)

    def missing_line(self, result, name, code):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)
        self.assertIn(name, result.stderr)
        self.assertIn("install.sh --check", result.stderr)

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

    def test_installed_launcher_refuses_gh_issue_close_in_a_ticket_worktree(self):
        for host, payload in self.commands().items():
            with self.subTest(host=host):
                self.denied(self.launch("tool-guard", "pretool", host, payload=payload), host)

    def test_installed_launcher_passes_gh_issue_close_elsewhere(self):
        for host, payload in self.commands().items():
            with self.subTest(host=host):
                self.silent(self.launch("tool-guard", "pretool", host, managed=False, payload=payload))

    def test_installed_launcher_refuses_a_question_in_a_ticket_worktree(self):
        for host, payload in self.questions().items():
            with self.subTest(host=host):
                self.denied(self.launch("tool-guard", "question", host, payload=payload), host)

    def test_installed_launcher_passes_a_question_elsewhere(self):
        for host, payload in self.questions().items():
            with self.subTest(host=host):
                self.silent(self.launch("tool-guard", "question", host, managed=False, payload=payload))

    def test_installed_launcher_with_mode_hook_removed_passes_silently(self):
        payload = {"cwd": str(self.clone)}
        present = self.launch("mode-hook", "prompt-submit", "claude", payload=payload)
        self.assertEqual(present.returncode, 0, present.stderr)
        self.assertIn("additionalContext", present.stdout)
        self.assertEqual(present.stderr, "")
        with self.moved("mode-hook.py"):
            self.silent(self.launch("mode-hook", "prompt-submit", "claude", payload=payload))

    def test_installed_launcher_with_turn_guard_removed_prints_one_line_and_passes(self):
        with self.moved("turn-guard.py"):
            result = self.launch("turn-guard", "stop", "claude")
        self.missing_line(result, "turn-guard", 0)

    def test_installed_launcher_with_tool_guard_removed_refuses_only_in_a_ticket_worktree(self):
        with self.moved("tool-guard.py"):
            refused = self.launch("tool-guard", "pretool", "claude")
            passed = self.launch("tool-guard", "pretool", "claude", managed=False)
        self.missing_line(refused, "tool-guard", 2)
        self.silent(passed)

    def test_launcher_and_tool_guard_share_the_governed_pattern(self):
        launcher = load_script(self.installed_root / "hook-launcher.py", "installed_launcher_pattern")
        guard = load_script(self.scripts / "tool-guard.py", "installed_guard_pattern")
        locations = load_script(self.scripts / "locations.py", "installed_locations_pattern")
        self.assertEqual(launcher.TICKET_DIR.pattern, guard.TICKET_DIR.pattern)
        self.assertEqual(launcher.TICKET_DIR.pattern, locations.GOVERNED_TICKET_DIR_PATTERN)


if __name__ == "__main__":
    unittest.main()
