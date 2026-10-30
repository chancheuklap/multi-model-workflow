import os
import datetime
import json
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

    def test_recent_transcripts_with_gnu_and_bsd_tools(self):
        fakebin = Path(self.env['PATH'].split(os.pathsep)[0])
        stat = fakebin / 'stat'
        stat.write_text('''#!/usr/bin/env python3
import os, sys
flag, form, path = sys.argv[1:]
expected = ('-c', '%Y') if os.environ['AUDIT_TOOL_STYLE'] == 'gnu' else ('-f', '%m')
if (flag, form) != expected:
    sys.exit(1)
print(int(os.stat(path).st_mtime))
''')
        stat.chmod(0o755)
        date = fakebin / 'date'
        date.write_text('''#!/usr/bin/env python3
import datetime, os, sys, time
if sys.argv[1:] == ['+%s']:
    print(int(time.time()))
else:
    flag, stamp, form = sys.argv[1:]
    if os.environ['AUDIT_TOOL_STYLE'] == 'gnu':
        if flag != '-d' or not stamp.startswith('@'):
            sys.exit(1)
        stamp = stamp[1:]
    elif flag != '-r':
        sys.exit(1)
    print(datetime.datetime.fromtimestamp(int(stamp)).strftime(form.removeprefix('+')))
''')
        date.chmod(0o755)
        home = Path(self.env['HOME'])
        paths = {
            'codex': home / '.codex/sessions/2026/10/30/chat.jsonl',
            'claude': home / '.claude/projects' / str(self.worktree).replace('/', '-').replace('.', '-') / 'chat.jsonl',
            'grok': home / '.grok/sessions' / str(self.worktree).replace('/', '%2F') / 'chat.jsonl',
            'cursor': home / '.cursor/projects' / str(self.repo).lstrip('/').replace('/', '-') / 'agent-transcripts/chat.jsonl',
        }
        for style in ('gnu', 'bsd'):
            self.env['AUDIT_TOOL_STYLE'] = style
            for host, path in paths.items():
                with self.subTest(style=style, host=host):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps({'cwd': str(self.worktree)}, separators=(',', ':')) + '\n')
                    try:
                        result, row = self.audit()
                        self.assertEqual(row[6], datetime.date.today().isoformat(), result.stderr)
                        self.assertEqual(row[7], 'verify-recent-chat', result.stderr)
                    finally:
                        path.unlink()


if __name__ == '__main__':
    unittest.main()
