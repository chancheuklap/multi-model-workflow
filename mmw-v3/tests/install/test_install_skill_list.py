"""install.sh reads skills.txt as one skill name per line, each a directory of mmw-v3/skills/."""

import os
import tempfile
import unittest
from pathlib import Path

from install_home import INSTALLER, MMW, SKILLS, copy_mmw, listed_skills, run_install, write_fakes


class InstallSkillListTests(unittest.TestCase):
    def install_in(self, scratch: Path, installer: Path, *args):
        home = scratch / "home"
        bin_dir = scratch / "bin"
        if not bin_dir.exists():
            write_fakes(bin_dir)
        (home / ".claude").mkdir(parents=True, exist_ok=True)
        return home, run_install(installer, home, bin_dir, *args)

    def test_skills_txt_lists_every_skill_directory_once(self):
        names = listed_skills()
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file()),
                         sorted(names))

    def test_every_listed_skill_is_linked_in_both_directories_and_readable(self):
        names = listed_skills()
        with tempfile.TemporaryDirectory() as raw:
            home, proc = self.install_in(Path(raw), INSTALLER)
            self.assertEqual(0, proc.returncode, proc.stderr)
            for dest in (home / ".agents/skills", home / ".claude/skills"):
                for name in names:
                    with self.subTest(dest=dest.name, name=name):
                        link = dest / name
                        self.assertEqual(str(MMW / "skills" / name), os.readlink(link))
                        self.assertTrue((link / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((home / ".mmw/skill-copies").exists())

    def test_a_line_that_is_not_a_bare_name_stops_the_install_before_any_host_is_touched(self):
        for line in ("triage +model-invoked", "engineering/tdd", "no-such-skill"):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as raw:
                scratch = Path(raw)
                mmw = copy_mmw(scratch)
                (mmw / "skills.txt").write_text("tdd\n" + line + "\n", encoding="utf-8")
                home, proc = self.install_in(scratch, mmw / "install.sh")
                self.assertNotEqual(0, proc.returncode, proc.stderr)
                self.assertIn(line.split()[0], proc.stderr, proc.stderr)
                self.assertFalse((home / ".agents" / "skills").exists(), proc.stderr)

    def test_a_name_listed_twice_stops_the_install(self):
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            mmw = copy_mmw(scratch)
            (mmw / "skills.txt").write_text("tdd\n# comment\n\ntdd\n", encoding="utf-8")
            home, proc = self.install_in(scratch, mmw / "install.sh")
            self.assertNotEqual(0, proc.returncode, proc.stderr)
            self.assertIn("重名技能：tdd", proc.stderr)
            self.assertFalse((home / ".agents" / "skills").exists(), proc.stderr)

    def test_a_skill_taken_off_the_list_is_unlinked_and_check_reports_it_until_then(self):
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            mmw = copy_mmw(scratch)
            home, first = self.install_in(scratch, mmw / "install.sh")
            self.assertEqual(0, first.returncode, first.stderr)
            names = [name for name in listed_skills(mmw / "skills.txt") if name != "wizard"]
            (mmw / "skills.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
            _, check = self.install_in(scratch, mmw / "install.sh", "--check")
            self.assertEqual(1, check.returncode)
            self.assertIn(f"残留  {home}/.agents/skills/wizard 指回本仓库，skills.txt 里却没有它", check.stderr)
            _, second = self.install_in(scratch, mmw / "install.sh")
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertIn(f"摘掉  {home}/.agents/skills/wizard", second.stdout)
            self.assertFalse(os.path.lexists(home / ".agents/skills/wizard"))
            self.assertFalse(os.path.lexists(home / ".claude/skills/wizard"))


if __name__ == "__main__":
    unittest.main()
