"""Installation copies keep source bytes except the invocation controls."""

import difflib
import os
import re
import tempfile
import unittest
from pathlib import Path

from install_home import INSTALLER, MMW, copy_mmw, run_install, write_fakes


def skill_entries(mmw=MMW):
    for raw in (mmw / "skills.txt").read_text().splitlines():
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        path = tokens[0]
        prefix, rest = path.split("/", 1)
        roots = {"self": "skills", "dd": "upstream-diagram-design/skills",
                 "pstack": "upstream-pstack/skills"}
        source = mmw / roots[prefix] / rest if prefix in roots else mmw / "upstream/skills" / path
        yield source, "+model-invoked" in tokens


def removed_lines(test, original, installed):
    """The lines of original that installed leaves out, once installed is shown to add nothing."""
    old = original.splitlines(keepends=True)
    new = installed.splitlines(keepends=True)
    removed = []
    for tag, i1, i2, _, _ in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        test.assertIn(tag, ("equal", "delete"), "the copy adds or changes a line")
        if tag == "delete":
            removed += old[i1:i2]
    return removed


class InstallSkillCopiesTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.home = self.root / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.bin = self.root / "bin"
        write_fakes(self.bin)

    def install(self, installer=INSTALLER):
        result = run_install(installer, self.home, self.bin)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def copy(self, source):
        return self.home / ".mmw/skill-copies" / source.name

    def test_a_marked_skill_s_copy_has_no_invocation_switch(self):
        self.install()
        switched = 0
        marked = 0
        for source, invoked in skill_entries():
            if not invoked:
                continue
            marked += 1
            original = source / "SKILL.md"
            installed = self.copy(source) / "SKILL.md"
            self.assertTrue(installed.is_file(), str(installed))
            self.assertFalse(installed.is_symlink(), str(installed))
            removed = removed_lines(self, original.read_bytes(), installed.read_bytes())
            self.assertEqual([], [l for l in removed if not re.match(rb"disable-model-invocation\s*:", l)],
                             source.name)
            switched += bool(removed)
            frontmatter = installed.read_bytes().split(b"---", 2)[1]
            self.assertNotRegex(frontmatter, rb"(?m)^disable-model-invocation\s*:")
        self.assertGreater(marked, 0)
        self.assertGreater(switched, 0, "no marked source exercises switch removal")

    def test_a_copy_s_openai_yaml_has_no_policy(self):
        self.install()
        policies = 0
        for source, invoked in skill_entries():
            if not invoked:
                continue
            original = source / "agents/openai.yaml"
            installed = self.copy(source) / "agents/openai.yaml"
            if not original.is_file():
                self.assertFalse(installed.exists())
                continue
            data = original.read_bytes()
            policies += bool(re.search(rb"^policy:", data, re.M))
            self.assertTrue(installed.is_file(), str(installed))
            self.assertFalse(installed.is_symlink(), str(installed))
            self.assertFalse(installed.parent.is_symlink(), str(installed.parent))
            removed = removed_lines(self, data, installed.read_bytes())
            self.assertEqual([], [l for l in removed if not re.match(rb"policy\s*:|[ \t]|\r?\n", l)], source.name)
            self.assertNotRegex(installed.read_bytes(), rb"(?m)^policy\s*:")
            if b"interface:" in data:
                self.assertIn(b"interface:", installed.read_bytes())
        self.assertGreater(policies, 0, "no marked source exercises policy removal")

    def test_every_other_entry_of_a_copy_links_back_to_the_source(self):
        self.install()
        links = 0
        for source, invoked in skill_entries():
            if not invoked:
                continue
            copy = self.copy(source)
            self.assertEqual({p.name for p in source.iterdir()}, {p.name for p in copy.iterdir()})
            for item in source.iterdir():
                if item.name == "SKILL.md":
                    continue
                if item.name == "agents":
                    self.assertFalse((copy / "agents").is_symlink())
                    self.assertEqual({p.name for p in item.iterdir()},
                                     {p.name for p in (copy / "agents").iterdir()})
                    entries = [p for p in item.iterdir() if p.name != "openai.yaml"]
                else:
                    entries = [item]
                for entry in entries:
                    installed = copy / entry.relative_to(source)
                    self.assertTrue(installed.is_symlink(), str(installed))
                    self.assertEqual(entry.resolve(), installed.resolve())
                    links += 1
        self.assertGreater(links, 0, "no source exercises linked support files")

    def test_host_links_of_a_marked_skill_point_at_its_copy(self):
        self.install()
        for source, invoked in skill_entries():
            for dest in (".agents/skills", ".claude/skills"):
                link = self.home / dest / source.name
                self.assertTrue(link.is_symlink(), str(link))
                expected = self.copy(source) if invoked else source
                self.assertEqual(str(expected), os.readlink(link))
        second = self.install()
        self.assertNotIn("冲突", second.stderr)

    def test_triage_is_installed_as_a_copy_without_its_switches(self):
        self.install()
        marked = {source.name: source for source, invoked in skill_entries() if invoked}
        self.assertIn("triage", marked)
        source = marked["triage"]
        copy = self.copy(source)
        self.assertRegex((source / "SKILL.md").read_bytes().split(b"---", 2)[1],
                         rb"(?m)^disable-model-invocation\s*:")
        self.assertRegex((source / "agents/openai.yaml").read_bytes(), rb"(?m)^policy\s*:")
        self.assertNotRegex((copy / "SKILL.md").read_bytes().split(b"---", 2)[1],
                            rb"(?m)^disable-model-invocation\s*:")
        self.assertNotRegex((copy / "agents/openai.yaml").read_bytes(), rb"(?m)^policy\s*:")

    def test_a_second_install_restores_a_changed_copy(self):
        self.install()
        first = {source: (self.copy(source) / "SKILL.md").read_bytes()
                 for source, invoked in skill_entries() if invoked}
        for source in first:
            (self.copy(source) / "SKILL.md").write_bytes(b"changed\n")
        self.install()
        for source, data in first.items():
            self.assertEqual(data, (self.copy(source) / "SKILL.md").read_bytes())

        mmw = copy_mmw(self.root)
        source = next(source for source, invoked in skill_entries(mmw) if invoked)
        support = source / "support.txt"
        support.write_bytes(b"live support\n")
        agents = source / "agents"
        agents.mkdir(exist_ok=True)
        other = agents / "other.yaml"
        other.write_bytes(b"other: true\n")
        self.install(mmw / "install.sh")
        installed = self.copy(source)
        self.assertEqual(b"live support\n", (installed / "support.txt").read_bytes())
        self.assertTrue((installed / "agents/other.yaml").is_symlink())
        support.write_bytes(b"live edit\n")
        self.assertEqual(b"live edit\n", (installed / "support.txt").read_bytes())
        support.unlink()
        other.unlink()
        (source / "agents/openai.yaml").unlink()
        (source / "new.txt").write_bytes(b"new\n")
        (installed / "extra").mkdir()
        (installed / "agents/openai.yaml").write_bytes(b"tampered\n")
        self.install(mmw / "install.sh")
        self.assertFalse((installed / "support.txt").is_symlink())
        self.assertFalse((installed / "agents/other.yaml").is_symlink())
        self.assertFalse((installed / "agents/openai.yaml").exists())
        self.assertFalse((installed / "extra").exists())
        self.assertTrue((installed / "new.txt").is_symlink())
        self.assertEqual(b"new\n", (installed / "new.txt").read_bytes())

    def test_only_top_level_invocation_controls_are_removed(self):
        mmw = copy_mmw(self.root)
        source = next(source for source, invoked in skill_entries(mmw) if invoked)
        skill = (b"---\r\nname: fixture\r\ndescription: Fixture.\r\n"
                 b"disable-model-invocation: true\r\n---\r\n"
                 b"disable-model-invocation: body text stays\r\n")
        yaml = (b"policy:\r\n  allow_implicit_invocation: false\r\n"
                b"  nested:\r\n    value: preserved in source only\r\n"
                b"interface:\r\n  display_name: Fixture\r\n"
                b"other:\r\n  policy: nested field stays\r\n")
        (source / "SKILL.md").write_bytes(skill)
        (source / "agents/openai.yaml").write_bytes(yaml)
        self.install(mmw / "install.sh")
        installed = self.copy(source)
        self.assertEqual(b"---\r\nname: fixture\r\ndescription: Fixture.\r\n---\r\n"
                         b"disable-model-invocation: body text stays\r\n",
                         (installed / "SKILL.md").read_bytes())
        self.assertEqual(b"interface:\r\n  display_name: Fixture\r\n"
                         b"other:\r\n  policy: nested field stays\r\n",
                         (installed / "agents/openai.yaml").read_bytes())
        self.assertEqual(skill, (source / "SKILL.md").read_bytes())
        self.assertEqual(yaml, (source / "agents/openai.yaml").read_bytes())

    def test_invalid_source_names_the_file_without_destroying_the_copy(self):
        mmw = copy_mmw(self.root)
        source = next(source for source, invoked in skill_entries(mmw) if invoked)
        self.install(mmw / "install.sh")
        installed = self.copy(source) / "SKILL.md"
        previous = installed.read_bytes()
        original = source / "SKILL.md"
        original.write_bytes(b"---\nname: invalid\n")
        for args in ((), ("--check",)):
            with self.subTest(args=args):
                result = run_install(mmw / "install.sh", self.home, self.bin, *args)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(str(original), result.stderr)
                self.assertEqual(previous, installed.read_bytes())


if __name__ == "__main__":
    unittest.main()
