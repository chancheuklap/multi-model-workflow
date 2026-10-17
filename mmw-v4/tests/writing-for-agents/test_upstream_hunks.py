import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/writing-for-agents/scripts/upstream-hunks.py'


class UpstreamHunks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.com')
        self.git('config', 'user.name', 'Test')
        self.upstream = self.repo / 'upstream/x/skill.md'
        self.copy = self.repo / 'copies/skill.md'
        self.upstream.parent.mkdir(parents=True)
        self.copy.parent.mkdir()
        self.mapping = self.repo / 'map.tsv'
        self.mapping.write_text('x\tskill.md\tcopies/skill.md\n')
        self.keep = self.repo / 'keep.tsv'
        self.keep.write_text('')
        self.baseline('heading\nold rule\nend\n')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], text=True,
                              capture_output=True, check=True).stdout.strip()

    def baseline(self, text, local=None):
        self.upstream.write_text(text)
        self.copy.write_text(text if local is None else local)
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')
        self.base = self.git('rev-parse', 'HEAD')

    def update_upstream(self, text):
        self.upstream.write_text(text)
        self.git('add', 'upstream')
        self.git('commit', '-qm', 'upstream update')

    def check(self, *args, upstream='x'):
        return subprocess.run([sys.executable, str(SCRIPT), upstream, '--repo', str(self.repo),
                               '--base', self.base, '--mmw', self.base,
                               '--map', str(self.mapping), '--keep', str(self.keep),
                               '--check', *args], text=True, capture_output=True)

    def test_mattpocock_row_is_compared(self):
        self.upstream = self.repo / 'upstream/mattpocock/skills/productivity/writing-for-agents/SKILL.md'
        self.upstream.parent.mkdir(parents=True)
        self.mapping.write_text('mattpocock\tskills/productivity/writing-for-agents/SKILL.md\tcopies/skill.md\n')
        self.baseline('heading\nold rule\nend\n')
        self.update_upstream('heading\nnew rule\nend\n')
        missing = self.check(upstream='mattpocock')
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertIn('MISSING copies/skill.md:2 new rule', missing.stdout)
        self.copy.write_text(self.upstream.read_text())
        carried = self.check(upstream='mattpocock')
        self.assertEqual(carried.returncode, 0, carried.stdout + carried.stderr)
        self.assertIn('UPSTREAM OK 1 carried, 0 kept, 0 merge', carried.stdout)

    def test_missing_carry_names_copy_and_upstream_line(self):
        self.update_upstream('heading\nnew rule\nend\n')
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('copies/skill.md:2', result.stdout)
        self.assertIn('new rule', result.stdout)

    def test_carried_replacement_passes(self):
        self.update_upstream('heading\nnew rule\nend\n')
        self.copy.write_text(self.upstream.read_text())
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('UPSTREAM OK 1 carried, 0 kept, 0 merge', result.stdout)

    def test_local_rewrite_is_reported_as_merge_not_missing(self):
        self.baseline('heading\nold rule\nend\n', 'heading\nlocal rule\nend\n')
        self.update_upstream('heading\nnew rule\nend\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MERGE copies/skill.md:2 old rule', result.stdout)
        self.assertIn('UPSTREAM OK 0 carried, 0 kept, 1 merge', result.stdout)

    def test_listed_exception_passes(self):
        self.update_upstream('heading\nnew rule\nend\n')
        self.keep.write_text('x\tskill.md\told rule\towner\tKeep the owner rule.\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('UPSTREAM OK 0 carried, 1 kept, 0 merge', result.stdout)

    def test_keep_row_matching_no_take_hunk_refuses_with_row_and_file(self):
        self.update_upstream('heading\nnew rule\nend\n')
        self.keep.write_text('x\tskill.md\twrong marker\towner\tKeep the owner rule.\n')
        result = self.check()
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('keep.tsv:1', result.stderr)
        self.assertIn('skill.md', result.stderr)

    def test_keep_row_matching_two_take_hunks_refuses(self):
        self.baseline('heading\nold rule\nmiddle\nold rule\nend\n')
        self.update_upstream('heading\nnew rule\nmiddle\nother rule\nend\n')
        self.keep.write_text('x\tskill.md\told rule\towner\tKeep the owner rule.\n')
        result = self.check()
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('keep.tsv:1', result.stderr)
        self.assertIn('skill.md', result.stderr)
        self.assertIn('2 take hunks', result.stderr)

    def test_unknown_ref_refuses_naming_it(self):
        for flag in ('--base', '--mmw'):
            with self.subTest(flag=flag):
                result = self.check(flag, 'unknown-revision')
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn('unknown-revision', result.stderr)

    def test_missing_mapped_path_refuses_naming_it(self):
        self.upstream.unlink()
        result = self.check()
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('upstream/x/skill.md', result.stderr)

    def test_deletion_must_be_carried(self):
        self.update_upstream('heading\nend\n')
        missing = self.check()
        self.assertEqual(missing.returncode, 1, missing.stdout)
        self.assertIn('copies/skill.md:2', missing.stdout)
        self.copy.write_text(self.upstream.read_text())
        carried = self.check()
        self.assertEqual(carried.returncode, 0, carried.stderr)
        self.assertIn('UPSTREAM OK 1 carried, 0 kept, 0 merge', carried.stdout)

    def test_pure_insertion_uses_new_marker_for_keep(self):
        self.update_upstream('heading\ninserted rule\nold rule\nend\n')
        self.keep.write_text('x\tskill.md\tinserted rule\trule-3\tKeep body rule.\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('UPSTREAM OK 0 carried, 1 kept, 0 merge', result.stdout)

    def test_replaced_line_left_beside_its_replacement_is_missing(self):
        self.update_upstream('heading\nnew rule\nend\n')
        for local in ('heading\nnew rule\nold rule\nend\n', 'heading\nold rule\nnew rule\nend\n'):
            with self.subTest(local=local):
                self.copy.write_text(local)
                result = self.check()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('MISSING copies/skill.md:2 new rule', result.stdout)

    def test_local_addition_beside_a_carried_line_passes(self):
        self.update_upstream('heading\nnew rule\nend\n')
        self.copy.write_text('heading\nnew rule\nlocal addition\nend\n')
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('UPSTREAM OK 1 carried, 0 kept, 0 merge', result.stdout)


if __name__ == '__main__':
    unittest.main()
