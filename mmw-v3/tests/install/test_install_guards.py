"""What an isolated install may call and where it writes, with disposable homes and service fakes."""

import json
import tempfile
import unittest
from pathlib import Path

from install_home import INSTALLER, calls, run_install, write_fakes


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
        self.state = self.scratch / "launchd.json"
        self.env = {"MMW_TEST_SERVICE_LOG": str(self.log),
                    "MMW_TEST_LAUNCHD_STATE": str(self.state)}
        self.plist = self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist"

    def install(self, *args, **overrides):
        return run_install(INSTALLER, self.home, self.bin, *args,
                           env_overrides={**self.env, **overrides})

    def launchctl(self):
        return [call[1] for call in calls(self.log) if call[0] == "launchctl"]

    def test_isolated_install_with_home_set_to_the_same_directory_touches_no_service(self):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        made = calls(self.log)
        self.assertEqual([], self.launchctl(), made)
        self.assertFalse([call for call in made if call[0] == "paseo" and "reload" in call], made)
        self.assertFalse([call for call in made if call[0] == "nmem"], made)
        self.assertFalse(self.plist.exists())

    def test_launchctl_substitute_keeps_prompt_sync_under_the_install_target(self):
        other_home = self.scratch / "other-home"
        other_home.mkdir()
        result = self.install(HOME=str(other_home), MMW_V3_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], list(other_home.iterdir()))
        self.assertTrue(self.plist.is_file())
        self.assertEqual(["bootout", "print", "bootstrap"], self.launchctl())

    def test_an_unchanged_plist_is_not_reloaded_and_a_changed_one_is(self):
        launchctl = str(self.bin / "launchctl")
        self.assertEqual(0, self.install(MMW_V3_LAUNCHCTL=launchctl).returncode)
        self.log.write_text("")
        self.assertEqual(0, self.install(MMW_V3_LAUNCHCTL=launchctl).returncode)
        self.assertEqual(["print"], self.launchctl())
        self.plist.write_text("<plist>an older checkout</plist>\n")
        self.log.write_text("")
        result = self.install(MMW_V3_LAUNCHCTL=launchctl)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["bootout", "print", "bootstrap"], self.launchctl())
        self.assertIn("com.mmw.prompt-sync", json.loads(self.state.read_text()))

    def test_a_failed_bootstrap_fails_the_install(self):
        result = self.install(MMW_V3_LAUNCHCTL=str(self.bin / "launchctl"),
                              MMW_TEST_BOOTSTRAP_FAIL="1")
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn("launchd 任务装不上", result.stderr)

    def test_install_writes_no_task_board_agent_and_asks_no_memory_service(self):
        result = self.install(MMW_V3_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse((self.home / "Library/LaunchAgents/com.mmw.board.plist").exists())
        self.assertFalse((self.home / ".mmw/board-bootstrapped-commit").exists())
        self.assertFalse([call for call in calls(self.log)
                          if call[0] == "nmem" or "com.mmw.board" in " ".join(call)])
        check = self.install("--check", MMW_V3_LAUNCHCTL=str(self.bin / "launchctl"))
        self.assertEqual(0, check.returncode, check.stderr)
        for absent in ("OPEN-WATCH", "LIVE-LOCK", "SAFE-TO-MOVE-INSTALLED", "Nowledge Mem"):
            self.assertNotIn(absent, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
