"""install.sh reads a skills.txt line as a path plus an optional marker."""

import os
import tempfile
import unittest
from pathlib import Path

from install_home import INSTALLER, MMW, copy_mmw, run_install, write_fakes

SKILLS_TXT = MMW / "skills.txt"
MARKER = "+model-invoked"


def marked_skill_names(skills_txt: Path) -> list[str]:
    names = []
    for raw in skills_txt.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        if len(tokens) == 2 and tokens[1] == MARKER:
            names.append(tokens[0].rsplit("/", 1)[-1])
    return names


class InstallSkillListTests(unittest.TestCase):
    def install_in(self, scratch: Path, installer: Path):
        home = scratch / "home"
        bin_dir = scratch / "bin"
        write_fakes(bin_dir)
        return home, run_install(installer, home, bin_dir)

    def test_every_marked_line_installs_its_skill(self):
        names = marked_skill_names(SKILLS_TXT)
        self.assertGreaterEqual(len(names), 1, SKILLS_TXT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as raw:
            home, proc = self.install_in(Path(raw), INSTALLER)
            self.assertEqual(0, proc.returncode, proc.stderr)
            for name in names:
                skill_md = home / ".agents" / "skills" / name / "SKILL.md"
                self.assertTrue(skill_md.is_file(), f"{name}: {proc.stderr}")
                skill_md.read_text(encoding="utf-8")

    def test_a_pstack_line_installs_from_the_pstack_subtree(self):
        name = "fixture-skill"
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            mmw = copy_mmw(scratch)
            skill_dir = mmw / "upstream-pstack" / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture-skill\ndescription: Fixture.\n---\n",
                encoding="utf-8",
            )
            (mmw / "skills.txt").write_text(f"pstack/{name}\n", encoding="utf-8")
            home, first = self.install_in(scratch, mmw / "install.sh")
            self.assertEqual(0, first.returncode, first.stderr)
            link = home / ".agents" / "skills" / name
            self.assertTrue(link.is_symlink(), first.stdout + first.stderr)
            target = os.readlink(link)
            self.assertTrue(
                target.endswith(f"/mmw-v2/upstream-pstack/skills/{name}"),
                target,
            )
            self.assertTrue((link / "SKILL.md").is_file())
            _home, second = self.install_in(scratch, mmw / "install.sh")
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertNotIn("冲突", second.stderr, second.stderr)

    def test_an_unknown_token_after_a_skill_stops_the_install_before_any_host_is_touched(self):
        line = "engineering/triage +model"
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            mmw = copy_mmw(scratch)
            (mmw / "skills.txt").write_text(line + "\n", encoding="utf-8")
            home, proc = self.install_in(scratch, mmw / "install.sh")
            self.assertNotEqual(0, proc.returncode, proc.stderr)
            self.assertIn(line, proc.stderr, proc.stderr)
            self.assertFalse((home / ".agents" / "skills").exists(), proc.stderr)

    def test_a_marker_on_an_own_skill_stops_the_install(self):
        line = "self/dispatch +model-invoked"
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            mmw = copy_mmw(scratch)
            (mmw / "skills.txt").write_text(line + "\n", encoding="utf-8")
            home, proc = self.install_in(scratch, mmw / "install.sh")
            self.assertNotEqual(0, proc.returncode, proc.stderr)
            self.assertIn(line, proc.stderr, proc.stderr)
            self.assertFalse((home / ".agents" / "skills").exists(), proc.stderr)


if __name__ == "__main__":
    unittest.main()
