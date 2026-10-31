import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MMW = HERE.parents[1]
CHECK = HERE / 'check_host_neutrality.py'


class HostNeutralityTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.skills = self.root / 'mmw-v4/skills'
        shutil.copytree(MMW / 'skills', self.skills, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__'))
        (self.root / 'upstream').symlink_to(MMW.parent / 'upstream')
        self.reference = self.skills / 'mmw-mode/references/neutrality-test.md'

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECK), str(self.skills)],
                              text=True, capture_output=True)

    def test_a_host_name_in_a_reference_is_reported(self):
        for host in ('Claude Code', 'Codex', 'Grok', 'Cursor'):
            with self.subTest(host=host):
                self.reference.write_text(f'# Reference\nUse {host} for this step.\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(f'mmw-mode/references/neutrality-test.md:2: {host.split()[0]}', result.stdout)

    def test_a_tool_name_is_reported(self):
        for word in ('the Skill tool', 'the Task tool', 'orca', 'herdr', 'paseo',
                     'mcp__codex_app__create_thread'):
            with self.subTest(word=word):
                self.reference.write_text(f'Use {word}.\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(f'mmw-mode/references/neutrality-test.md:1: {word}', result.stdout)

    def test_a_file_name_passes(self):
        self.reference.write_text('Read CLAUDE.md and codex.md.\n'
                                  'Use .claude/skills/ and .cursor/rules/.\n'
                                  'Open Claude Design at claude.ai.\n')
        result = self.run_check()
        self.assertNotIn('neutrality-test.md:', result.stdout)
        self.reference.write_text('Read CLAUDE.md with Codex.\n')
        self.assertIn('neutrality-test.md:1: Codex', self.run_check().stdout)

    def test_the_two_whole_files_pass(self):
        for name in ('writing-for-agents/references/SKILL-MECHANICS.md', 'dispatch/references/editing-models.md',
                     'writing-for-agents/references/SKILL-SET-RULES.md'):
            (self.skills / name).write_text('Use Codex and the Task tool with orca.\n')
        result = self.run_check()
        for name in ('SKILL-MECHANICS.md', 'editing-models.md', 'SKILL-SET-RULES.md'):
            self.assertNotIn(name + ':', result.stdout)

    def test_an_upstream_mapped_file_passes_only_upstream_lines(self):
        upstream = self.root / 'fixture-upstream'
        upstream.mkdir()
        self.reference.write_text('Use Claude.\nUse Grok.\n')
        (upstream / 'reference.md').write_text('Use Claude.\nUse Codex.\n')
        (self.root / 'upstream').unlink()
        (self.root / 'upstream').mkdir()
        (self.root / 'upstream/fixture').symlink_to(upstream)
        mapping = self.skills / 'writing-for-agents/scripts/upstream-map.tsv'
        mapping.write_text('fixture\treference.md\tmmw-v4/skills/mmw-mode/references/neutrality-test.md\n')
        result = self.run_check()
        self.assertNotIn('neutrality-test.md:1:', result.stdout)
        self.assertIn('neutrality-test.md:2: Grok', result.stdout)

    def test_an_exception_matching_nothing_is_reported(self):
        checks = self.root / 'checks'
        checks.mkdir()
        shutil.copy(CHECK, checks / CHECK.name)
        exceptions = checks / 'host-neutrality-exceptions.tsv'
        exceptions.write_text('mmw-mode/references/neutrality-test.md\tUse the text cursor.\tOrdinary word.\n')
        self.reference.write_text('Use the text cursor.\n')
        command = [sys.executable, str(checks / CHECK.name), str(self.skills)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertNotIn('neutrality-test.md:', result.stdout)
        self.reference.write_text('Use the pointer.\n')
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('host-neutrality-exceptions.tsv:1:', result.stdout)
        self.assertIn('mmw-mode/references/neutrality-test.md', result.stdout)

    def test_paths_cannot_escape_a_skill_or_name_an_installed_skill_in_a_check(self):
        for text, word in (('Read ../../dispatch/SKILL.md.', '../../dispatch/SKILL.md'),
                           ('CHECK: python3 ~/.agents/skills/example/scripts/check.py', '~/.agents/skills/example/scripts/check.py'),
                           ('CHECK: python3 ~/.claude/skills/example/scripts/check.py', '~/.claude/skills/example/scripts/check.py')):
            with self.subTest(text=text):
                self.reference.write_text(text + '\n')
                self.assertIn(f'neutrality-test.md:1: {word}', self.run_check().stdout)
        self.reference.write_text('Read ../SKILL.md.\n')
        self.assertNotIn('neutrality-test.md:', self.run_check().stdout)


    def test_joined_host_and_runner_names_are_reported(self):
        for text, words in (('Use Claude/Codex/Grok here.', ('Claude', 'Codex', 'Grok')),
                            ('Run on orca/herdr/paseo.', ('orca', 'herdr', 'paseo')),
                            ('Open Cursor.Then go.', ('Cursor',))):
            with self.subTest(text=text):
                self.reference.write_text(text + '\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                for word in words:
                    self.assertIn(f'neutrality-test.md:1: {word}', result.stdout)

    def test_tool_names_with_markdown_or_line_wrapping_are_reported(self):
        for text in ('Use the `Skill` tool.', 'Use the Skill\ntool.',
                     'Use the **Task** tool.', 'Use the Task\ntool.'):
            with self.subTest(text=text):
                self.reference.write_text(text + '\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('neutrality-test.md:1: the ', result.stdout)

    def test_an_embedded_parent_path_cannot_escape_its_skill(self):
        self.reference.write_text('Read references/../../../b/SKILL.md.\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('neutrality-test.md:1: references/../../../b/SKILL.md', result.stdout)

    def test_a_check_cannot_name_a_repository_local_skill_path(self):
        self.reference.write_text('CHECK: bash mmw-v4/skills/verify-ticket/scripts/x.sh\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('neutrality-test.md:1: mmw-v4/skills/verify-ticket/scripts/x.sh', result.stdout)

    def test_an_empty_or_missing_skill_tree_is_not_a_pass(self):
        for name in ('missing', 'empty'):
            with self.subTest(name=name):
                skills = self.root / name
                if name == 'empty':
                    skills.mkdir()
                result = subprocess.run([sys.executable, str(CHECK), str(skills)],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(str(skills), result.stdout)
                self.assertNotIn('HOST NEUTRALITY OK', result.stdout)
