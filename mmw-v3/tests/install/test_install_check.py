"""What --check reports on its own: the launcher copy, the skill-text checker, the runner adapters."""

import tempfile
import unittest
from pathlib import Path

from install_home import copy_mmw, run_install, write_fakes


class InstallCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = tempfile.TemporaryDirectory()
        scratch = Path(cls.raw.name)
        cls.mmw = copy_mmw(scratch)
        cls.home = scratch / "home"
        (cls.home / ".claude").mkdir(parents=True)
        (cls.home / ".codex").mkdir()
        cls.bin = scratch / "bin"
        write_fakes(cls.bin)
        result = run_install(cls.mmw / "install.sh", cls.home, cls.bin)
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.raw.cleanup()

    def check(self):
        return run_install(self.mmw / "install.sh", self.home, self.bin, "--check")

    def edited(self, path, text):
        original = path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        path.write_text(text, encoding="utf-8")

    def test_a_complete_install_checks_clean(self):
        result = self.check()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn("HOOKS-INSTALLED", result.stdout.splitlines())
        self.assertRegex(result.stdout, r"技能文本  OK \d+ files, 0 problems")
        self.assertIn("齐了：技能 2 处", result.stdout)

    def test_a_skill_text_problem_fails_the_check_and_is_printed(self):
        skill = self.mmw / "skills" / "wizard" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.edited(skill, text.replace("name: wizard", "name: not-wizard", 1))
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("wizard/SKILL.md: frontmatter name is 'not-wizard', not 'wizard'", result.stderr)
        self.assertIn("不一致  技能文本 FAIL", result.stderr)
        self.assertNotIn("NOT CHECKED", result.stderr)

    def test_a_skill_text_checker_that_cannot_run_is_reported_not_checked(self):
        checker = self.mmw / "skills/writing-skill-sets/scripts/check_skill_text.py"
        self.edited(checker, "raise RuntimeError('broken')\n")
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("没查  技能文本检查", result.stderr)
        self.assertIn("broken", result.stderr)

    def test_a_launcher_copy_that_differs_from_its_source_fails_the_check(self):
        launcher = self.home / ".mmw/bin/hook-launcher"
        self.edited(launcher, launcher.read_text() + "# edited\n")
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn(f"不一致  {launcher}", result.stderr)
        self.assertNotIn("HOOKS-INSTALLED", result.stdout)

    def test_an_adapter_flag_the_binary_lacks_is_reported(self):
        adapter = self.mmw / "skills/mmw-mode/scripts/runners/paseo.sh"
        text = adapter.read_text(encoding="utf-8")
        self.edited(adapter, text.replace("# MMW_USES: send --no-wait",
                                          "# MMW_USES: send --no-wait --no-such-flag", 1))
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn("不一致  适配器说它要用 send --no-such-flag", result.stderr)


if __name__ == "__main__":
    unittest.main()
