import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/mmw-mode/scripts/worktree-audit.sh'


class WorktreeAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.origin = self.root / 'origin.git'
        self.repo = self.root / 'repo'
        self.git('init', '--bare', '-q', str(self.origin))
        self.git('clone', '-q', str(self.origin), str(self.repo))
        self.git('-C', str(self.repo), 'config', 'user.email', 'test@example.com')
        self.git('-C', str(self.repo), 'config', 'user.name', 'Test')
        self.git('-C', str(self.repo), 'checkout', '-qb', 'main')
        (self.repo / 'notes').write_text('main\n')
        self.commit('main')
        self.git('-C', str(self.repo), 'push', '-q', 'origin', 'main')
        self.git('-C', str(self.repo), 'checkout', '-qb', 'topic')
        (self.repo / 'notes').write_text('topic\n')
        self.commit('topic')
        self.git('-C', str(self.repo), 'checkout', '-qb', 'dev', 'main')
        self.git('-C', str(self.repo), 'merge', '--no-ff', '-qm', 'merge topic', 'topic')
        self.git('-C', str(self.repo), 'push', '-q', 'origin', 'dev')
        self.git('-C', str(self.origin), 'symbolic-ref', 'HEAD', 'refs/heads/dev')
        self.git('-C', str(self.repo), 'remote', 'set-head', 'origin', '-a')
        self.worktree = self.root / 'topic'
        self.git('-C', str(self.repo), 'worktree', 'add', '-q', str(self.worktree), 'topic')
        fakebin = self.root / 'bin'
        fakebin.mkdir()
        gh = fakebin / 'gh'
        gh.write_text('#!/bin/sh\ncat "$AUDIT_TEST_PRS"\n')
        gh.chmod(0o755)
        self.prs = self.root / 'prs.json'
        self.prs.write_text('[]')
        isolated_home = self.root / 'home'
        isolated_home.mkdir()
        self.env = dict(os.environ, HOME=str(isolated_home), AUDIT_TEST_PRS=str(self.prs),
                        PATH=str(fakebin) + os.pathsep + os.environ['PATH'])

    def git(self, *args):
        return subprocess.run(['git', *args], capture_output=True, text=True, check=True).stdout

    def commit(self, message):
        self.git('-C', str(self.repo), 'add', '.')
        self.git('-C', str(self.repo), 'commit', '-qm', message)

    def audit(self, *args):
        result = subprocess.run(['bash', str(SCRIPT), *args, str(self.repo)], env=self.env,
                                capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        row = next(line.split('\t') for line in lines if line.endswith('\t' + str(self.worktree)))
        return result, row

    def test_default_branch_recognizes_topic_merged_into_dev(self):
        result, row = self.audit()
        self.assertEqual(result.stdout.splitlines()[0], '# base: origin/dev')
        self.assertEqual(row[2], 'YES')
        self.assertIn('origin/dev', result.stderr)

    def test_explicit_main_does_not_mark_dev_topic_merged(self):
        result, row = self.audit('-b', 'origin/main')
        self.assertEqual(result.stdout.splitlines()[0], '# base: origin/main')
        self.assertEqual(row[2], 'no')

    def test_open_and_draft_prs_are_held(self):
        for state in ('OPEN', 'DRAFT'):
            with self.subTest(state=state):
                self.prs.write_text('[{"number": 7, "state": "' + state + '", "headRefName": "topic"}]')
                _, row = self.audit()
                self.assertEqual(row[5], '#7/' + state.lower())
                self.assertEqual(row[7], 'hold-open-pr')


if __name__ == '__main__':
    unittest.main()
