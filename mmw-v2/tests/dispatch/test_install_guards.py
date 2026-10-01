"""Install guards through install.sh, with disposable homes and service fakes."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from install_home import INSTALLER, run_install, write_fakes


class InstallGuardTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)
        self.home = self.scratch / "home"
        self.home.mkdir()
        self.bin = self.scratch / "bin"
        write_fakes(self.bin)
        self.log = self.scratch / "services.log"
        self.log.touch()
        for name in ("launchctl", "paseo"):
            self.executable(name, """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
with Path(os.environ['MMW_TEST_SERVICE_LOG']).open('a') as log:
    log.write(json.dumps([Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')
if Path(sys.argv[0]).name == 'launchctl':
    if sys.argv[1] == 'print':
        raise SystemExit(0)
    if sys.argv[1] == 'bootstrap' and os.environ.get('MMW_TEST_BOOTSTRAP_FAIL'):
        raise SystemExit(1)
print('{}')
""")
        # install.sh prepends ~/.local/bin for reload. Its bundled Paseo link
        # must also reach our fake when an isolation regression calls reload.
        self.executable("ln", """#!/usr/bin/env python3
import os, subprocess, sys
args = sys.argv[1:]
if '/Applications/Paseo.app/Contents/Resources/bin/paseo' in args:
    args = [os.environ['MMW_TEST_PASEO'] if arg ==
            '/Applications/Paseo.app/Contents/Resources/bin/paseo' else arg
            for arg in args]
raise SystemExit(subprocess.call([%r, *args]))
""" % shutil.which("ln"))
        self.executable("uname", "#!/bin/sh\necho Darwin\n")
        catalog = self.scratch / "catalog.json"
        offerings = {}
        defaults = json.loads((INSTALLER.parent / "skills/mmw/hosts.json").read_text())["defaults"]
        for row in defaults:
            name = row["model"].split("[")[0]
            offered = {"id": name.replace(" ", "-"), "name": name,
                       "thinkingOptionIds": ["low", "medium", "high", "xhigh"]}
            rows = offerings.setdefault(row["host"], [])
            if offered not in rows:
                rows.append(offered)
        catalog.write_text(json.dumps(offerings))
        self.env = {"HOME": str(self.home), "MMW_TEST_SERVICE_LOG": str(self.log),
                    "MMW_TEST_PASEO": str(self.bin / "paseo"),
                    "MMW_HOST_CATALOG": str(catalog)}

    def executable(self, name, content):
        path = self.bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def install(self, *args, **overrides):
        return run_install(INSTALLER, self.home, self.bin, *args,
                           env_overrides={**self.env, **overrides})

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def head(self):
        return subprocess.check_output(
            ["git", "-C", str(INSTALLER.parent), "rev-parse", "HEAD"], text=True).strip()

    def board_commit(self):
        return self.home / ".mmw/board-bootstrapped-commit"

    def watch(self, mmw_home=None, entry=None):
        state = (mmw_home or self.home / ".mmw") / "state/o__r"
        state.mkdir(parents=True, exist_ok=True)
        watch = entry or {"spec": 76, "kind": "night"}
        key = f"spec:{watch['spec']}" if watch.get("spec") else "tickets:61"
        (state / "watches.json").write_text(json.dumps(
            {key: {**watch, "runner": "orca", "session": "fake_main"}}))
        return state

    def test_isolated_install_with_home_set_to_the_same_directory_touches_no_service(self):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse([call for call in self.calls()
                          if call[1] in ("bootout", "bootstrap", "reload")], self.calls())

    def test_board_reload_is_announced_and_recorded_when_the_commit_changes(self):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"重载  com.mmw.board（无 → {self.head()}）", result.stdout)
        self.assertEqual(self.head(), self.board_commit().read_text().strip())
        previous = "0" * 40
        self.board_commit().write_text(previous + "\n")
        changed = self.install(MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, changed.returncode, changed.stderr)
        self.assertIn(f"重载  com.mmw.board（{previous} → {self.head()}）", changed.stdout)
        self.assertEqual(self.head(), self.board_commit().read_text().strip())
        board_calls = [call[1] for call in self.calls() if "com.mmw.board" in call[-1]]
        self.assertEqual(["bootout", "bootstrap"], board_calls)

    def test_board_reload_is_skipped_when_the_commit_is_unchanged(self):
        first = self.install(MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, first.returncode, first.stderr)
        self.log.write_text("")
        second = self.install(MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertNotIn("重载  com.mmw.board", second.stdout)
        self.assertEqual(["print"], [call[1] for call in self.calls()
                                     if "com.mmw.board" in call[-1]])
        self.assertEqual(self.head(), self.board_commit().read_text().strip())

    def test_full_install_refuses_while_a_watch_is_open(self):
        self.watch()
        before = sorted(path.relative_to(self.home) for path in self.home.rglob("*"))
        result = self.install()
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("o/r spec:76", result.stdout + result.stderr)
        self.assertRegex(result.stdout + result.stderr, r"dispatch.sh (suspend|close-night) 76")
        self.assertEqual(before, sorted(path.relative_to(self.home) for path in self.home.rglob("*")))
        self.assertFalse((self.home / ".mmw/installed-root").exists())
        self.assertEqual([], self.calls())

    def test_full_install_refuses_while_a_relay_lock_is_live(self):
        child = subprocess.Popen(["sleep", "100000"])
        self.addCleanup(lambda: (child.terminate(), child.wait()))
        identity = subprocess.check_output(
            ["ps", "-o", "lstart=", "-p", str(child.pid)], text=True,
            env={**os.environ, "LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
        state = self.home / ".mmw/state/o__r"
        state.mkdir(parents=True)
        for kind in ("relay", "watchdog"):
            with self.subTest(kind=kind):
                lock = state / f"{kind}.lock"
                lock.write_text(json.dumps(
                    {"pid": child.pid, "identity": " ".join(identity.split()),
                     "purpose": f"a stand-in {kind}"}))
                result = self.install()
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn(f"o/r {kind} pid {child.pid}", result.stdout + result.stderr)
                self.assertFalse((self.home / ".mmw/installed-root").exists())
                lock.unlink()

    def test_isolated_install_ignores_the_testers_own_watches(self):
        other = self.scratch / "other-mmw"
        self.watch(other)
        result = self.install(MMW_HOME=str(other))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.home / ".mmw/installed-root").is_file())

    def test_check_mode_is_not_refused_by_an_open_watch(self):
        self.watch()
        self.board_commit().write_text("0" * 40 + "\n")
        result = self.install("--check")
        self.assertNotEqual(2, result.returncode, result.stderr)
        self.assertIn("OPEN-WATCH o/r spec:76", result.stdout)
        self.assertIn("NOT-SAFE-TO-MOVE-INSTALLED", result.stdout)
        self.assertEqual([], [call for call in self.calls() if call[0] == "launchctl"])
        self.assertEqual("0" * 40 + "\n", self.board_commit().read_text())
        self.assertNotIn("重载  com.mmw.board", result.stdout)

    def test_a_failed_board_reload_records_no_commit(self):
        for previous in (None, "0" * 40):
            with self.subTest(previous=previous):
                if previous is not None:
                    self.board_commit().write_text(previous + "\n")
                self.log.write_text("")
                result = self.install(MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"),
                                      MMW_TEST_BOOTSTRAP_FAIL="1")
                self.assertEqual(1, result.returncode, result.stderr)
                if previous is None:
                    self.assertFalse(self.board_commit().exists())
                else:
                    self.assertEqual(previous + "\n", self.board_commit().read_text())
                self.assertEqual(["bootout", "bootstrap"],
                                 [call[1] for call in self.calls() if "com.mmw.board" in call[-1]])
                self.assertFalse([call for call in self.calls() if call[1] == "reload"])
        retry = self.install(MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, retry.returncode, retry.stderr)
        self.assertEqual(self.head(), self.board_commit().read_text().strip())

    def test_real_install_reads_watches_from_mmw_home(self):
        other = self.scratch / "other-mmw"
        self.watch(other)
        result = self.install(MMW_V2_HOME=None, MMW_HOME=str(other))
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertRegex(result.stdout + result.stderr, r"dispatch.sh (suspend|close-night) 76")
        self.assertEqual([], list(self.home.iterdir()))
        self.assertEqual([], self.calls())

    def test_launchctl_substitute_keeps_prompt_sync_under_the_install_target(self):
        other_home = self.scratch / "other-home"
        other_home.mkdir()
        result = self.install(HOME=str(other_home),
                              MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], list(other_home.iterdir()))
        self.assertTrue((self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist").is_file())

    def test_full_install_refuses_unreadable_watches_and_names_ticket_watch_close(self):
        state = self.watch(entry={"tickets": [61], "kind": "adopted-ticket"})
        result = self.install()
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("dispatch.sh land 61", result.stdout + result.stderr)
        (state / "watches.json").write_text("{broken")
        result = self.install()
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("UNREADABLE o/r", result.stdout + result.stderr)
        self.assertFalse((self.home / ".mmw/installed-root").exists())

    def test_unknown_commit_uses_plist_reload_and_does_not_record_a_commit(self):
        self.executable("git", "#!/bin/sh\necho HEAD\nexit 1\n")
        for attempt in range(2):
            self.log.write_text("")
            result = self.install(MMW_V2_LAUNCHCTL=str(self.bin / "launchctl"))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("重载  com.mmw.board（无 → 未知）", result.stdout)
            self.assertFalse(self.board_commit().exists())
            board_calls = [call[1] for call in self.calls() if "com.mmw.board" in call[-1]]
            self.assertEqual(["bootout", "print"] if attempt == 0 else ["print"], board_calls)


if __name__ == "__main__":
    unittest.main()
