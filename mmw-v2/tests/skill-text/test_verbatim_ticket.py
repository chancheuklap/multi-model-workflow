"""Ticket manifests and untouched text through the public CLI and disposable Git."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'lib' / 'check_verbatim_moves.py'
FIXTURES = HERE / 'fixtures' / 'verbatim-ticket'
SKILL = 'mmw-v2/skills/example/SKILL.md'


class VerbatimTicket(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-verbatim-ticket-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(('MMW_', 'NMEM_', 'GIT_'))}
        self.git('init', '-qb', 'base')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.write('source.md', 'Carry this sentence.\n')
        self.write(SKILL, '## Allowed\n\nKeep this rule.\n\n## Other\n\nKeep this reason.\n')
        self.base = self.commit()
        self.git('checkout', '-qb', 'issue-603')
        self.write('target.md', 'Carry this sentence.\n')
        self.commit()
        self.manifest = f'from {self.base}\ncopy source.md -> target.md\n'
        self.env.update(MMW_TICKET='603', MMW_BASE_REF='base')

    def git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.root, env=self.env,
                              capture_output=True, text=True, check=True).stdout.strip()

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')

    def commit(self, message='Fixture'):
        self.git('add', '.')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def check(self, *args, code=0, token=None):
        self.write('manifest', self.manifest)
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                                env=self.env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, code, output)
        if token:
            self.assertIn(token, output)
        if code:
            self.assertNotIn('VERBATIM OK', output)
        else:
            self.assertTrue(output.startswith('VERBATIM OK'), output)
        return output

    def test_untouched_text_outside_the_manifest_is_reported(self):
        original = self.git('rev-parse', 'HEAD')
        self.write(SKILL, '## Allowed\n\nKeep this rule.\n\n## Other\n\nChange this reason.\n')
        self.commit()
        self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')
        self.git('reset', '--hard', original)
        self.write('source.md', '')
        self.write(SKILL, '## Allowed\n\nKeep this rule. Carry this sentence.\n\n## Other\n\nKeep this reason.\n')
        self.commit()
        self.manifest = f'from {self.base}\nmove source.md -> {SKILL}#Allowed\n'
        self.check('--manifest', 'manifest')
        self.write(SKILL, '## Allowed\n\nKeep this rule. Carry this sentence.\n\n## Other\n\nChange this reason.\n')
        self.commit()
        self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')
        self.git('reset', '--hard', original)
        self.manifest = f'from {self.base}\ncopy source.md -> target.md\n'
        baseline_manifest = self.manifest
        for path in ('mmw-v2/upstream-other/skills/tool/SKILL.md',
                     '.mmw/playbooks/local.md'):
            with self.subTest(path=path):
                self.git('reset', '--hard', original)
                self.write(path, 'Unlisted sentence.\n')
                self.commit()
                self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')
        self.git('reset', '--hard', original)
        self.write('docs/note.md', 'A document outside skill text.\n')
        self.commit()
        self.check('--manifest', 'manifest')
        # Each kind of listed rename is allowed in place, with scope enforced.
        for kind, old, new in (('text', 'Keep this reason', 'Retain this reason'),
                               ('token', 'old-command', 'new-command'),
                               ('path', 'mmw-v2/skills/example/references/old.md',
                                'mmw-v2/skills/example/references/new.md')):
            with self.subTest(kind=kind):
                self.git('reset', '--hard', original)
                text = f'## Allowed\n\nKeep this rule.\n\n## Other\n\nUse `{old}`.\n'
                self.write(SKILL, text)
                if kind == 'path':
                    self.write(old, 'Reference.\n')
                    self.write(new, 'Reference.\n')
                self.commit()
                self.git('branch', '-f', 'base', 'HEAD')
                self.write(SKILL, text.replace(old, new))
                self.commit()
                scope = f' in {SKILL}' if kind != 'path' else ''
                self.manifest = baseline_manifest + f'rename {kind} `{old}` -> `{new}`{scope}\n'
                self.check('--manifest', 'manifest')
                if kind != 'path':
                    self.manifest = baseline_manifest + f'rename {kind} `{old}` -> `{new}` in no-match/**\n'
                    self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')
        # A sentence drop grants only that instance, not the whole section.
        self.git('reset', '--hard', original)
        self.git('branch', '-f', 'base', self.base)
        self.manifest = baseline_manifest + f'drop {SKILL}#Other "Keep this reason." : Spec\n'
        self.write(SKILL, '## Allowed\n\nKeep this rule.\n\n## Other\n')
        self.commit()
        self.check('--manifest', 'manifest')
        self.write(SKILL, '## Allowed\n\nKeep this rule.\n\n## Other\n\nUnlisted new instruction.\n')
        self.commit()
        self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')

    def ticket_body(self, text=None):
        body = text if text is not None else (FIXTURES / 'body.md').read_text(encoding='utf-8')
        body = body.replace('{{MANIFEST}}', self.manifest.rstrip('\n'))
        (self.root / 'body.md').write_bytes(body.replace('\n', '\r\n').encode('utf-8'))
        bin_dir = self.root / 'bin'
        bin_dir.mkdir(exist_ok=True)
        fake = bin_dir / 'gh'
        fake.write_text('#!' + sys.executable + '\n' +
                        (FIXTURES / 'fake_gh.py').read_text(encoding='utf-8'), encoding='utf-8')
        fake.chmod(0o755)
        self.env.update(PATH=str(bin_dir) + os.pathsep + self.env.get('PATH', ''),
                        VERBATIM_GH_BODY=str(self.root / 'body.md'),
                        VERBATIM_GH_CALL=str(self.root / 'gh-call.json'))

    def test_ticket_body_gives_the_same_manifest(self):
        self.ticket_body()
        expected = self.check('--manifest', 'manifest')
        actual = self.check('--ticket', '603')
        self.assertEqual(actual, expected)
        self.assertEqual(json.loads((self.root / 'gh-call.json').read_text()),
                         ['issue', 'view', '603', '--json', 'body'])

    def test_ticket_body_without_one_moves_fence_exits_2(self):
        bodies = (
            '## Owns\n\n```moves\n{{MANIFEST}}\n```\n',
            '## Moves\n\n```text\n{{MANIFEST}}\n```\n',
            '## Moves\n\n```moves\n{{MANIFEST}}\n```\n\n```moves\n{{MANIFEST}}\n```\n',
            '## Moves\n\n```moves\n{{MANIFEST}}\n',
            '```markdown\n## Moves\n```\n',
        )
        for body in bodies:
            with self.subTest(body=body):
                self.ticket_body(body)
                self.check('--ticket', '603', code=2, token='VERBATIM ERROR')
        self.ticket_body()
        self.env['VERBATIM_GH_FAIL'] = '1'
        self.check('--ticket', '603', code=2, token='VERBATIM ERROR')

    def test_untouched_text_needs_a_base(self):
        self.env.pop('MMW_BASE_REF')
        self.check('--manifest', 'manifest', code=2, token='--base')
        self.check('--manifest', 'manifest', '--base', 'base', token='untouched text:')
        self.env['MMW_BASE_REF'] = 'no-such-ref'
        self.check('--manifest', 'manifest', '--base', 'base')
        self.check('--manifest', 'manifest', code=2, token='VERBATIM ERROR')
        # merge-base, not the tip of a base that has advanced independently.
        worker = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-q', 'base')
        self.write(SKILL, 'Base-only changes.\n')
        self.commit()
        self.git('checkout', '-q', 'issue-603')
        self.assertEqual(self.git('rev-parse', 'HEAD'), worker)
        self.env['MMW_BASE_REF'] = 'base'
        self.check('--manifest', 'manifest')

    def test_untouched_text_off_the_ticket_branch_is_not_checked(self):
        self.write(SKILL, 'Changed outside this manifest.\n')
        self.commit()
        for identity in ('999', ''):
            self.env['MMW_TICKET'] = identity
            self.env.pop('MMW_BASE_REF', None)
            self.check('--manifest', 'manifest', token="untouched text: not checked, not on this ticket's branch")
        self.env['MMW_TICKET'] = '603'
        self.git('checkout', '-qb', 'closing-base')
        self.check('--manifest', 'manifest', token="untouched text: not checked, not on this ticket's branch")
        self.git('checkout', '-q', '--detach')
        self.check('--manifest', 'manifest', token='not checked')
        self.git('checkout', '-qb', 'issue-999')
        self.env['MMW_TICKET'] = '999'
        self.ticket_body()
        self.check('--ticket', '603', token="untouched text: not checked, not on this ticket's branch")
        # Being off the ticket branch does not skip the manifest comparison.
        self.write('target.md', 'Changed carried sentence.\n')
        self.commit()
        self.check('--manifest', 'manifest', code=1, token='CHANGED')

    def test_untouched_text_skips_a_squashed_subtree(self):
        upstream_tmp = tempfile.TemporaryDirectory(prefix='mmw-verbatim-upstream-')
        self.addCleanup(upstream_tmp.cleanup)
        upstream = Path(upstream_tmp.name)
        self.git('init', '-qb', 'main', cwd=upstream)
        self.git('config', 'user.name', 'Fixture', cwd=upstream)
        self.git('config', 'user.email', 'fixture@example.test', cwd=upstream)
        (upstream / 'skills').mkdir()
        (upstream / 'skills' / 'guide.md').write_text('Upstream wording.\n')
        self.git('add', '.', cwd=upstream)
        self.git('commit', '-qm', 'Upstream fixture', cwd=upstream)
        prefix = 'mmw-v2/upstream-fixture'
        self.git('subtree', 'add', '--prefix', prefix, str(upstream), 'main', '--squash')
        self.write(prefix + '/skills/guide.md', 'Locally changed upstream wording.\n')
        self.commit()
        self.check('--manifest', 'manifest', token='subtree pulled: ' + prefix)
        self.write(SKILL, 'Changed outside subtree.\n')
        self.commit()
        self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')

    def test_untouched_units_cannot_use_unlisted_mechanical_rewrites(self):
        principle = 'mmw-v2/skills/mmw/principles/principle-example.md'
        self.write(principle, 'Principle.\n')
        self.write(SKILL, 'Read [the reference](references/old.md).\n')
        self.write('mmw-v2/skills/example/references/old.md', 'Reference.\n')
        self.commit()
        self.git('branch', '-f', 'base', 'HEAD')
        original = self.git('rev-parse', 'HEAD')
        for text in ('Read [the reference](references/old.md). (**principle-example**)\n',
                     'Read `references/old.md`.\n'):
            with self.subTest(text=text):
                self.git('reset', '--hard', original)
                self.write(SKILL, text)
                self.commit()
                self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')

    def test_source_line_scopes_do_not_mask_shifted_untouched_text(self):
        self.write('source.md', '## Allowed\n\nCarry this sentence.\n\n## Other\n\nKeep this reason.\n')
        self.base = self.commit()
        self.git('branch', '-f', 'base', 'HEAD')
        self.manifest = f'from {self.base}\nmove source.md:L3 -> target.md\n'
        self.write('source.md', '## Allowed\n\n## Other\n\nKeep this reason.\n')
        self.commit()
        self.check('--manifest', 'manifest')
        self.write('source.md', '## Allowed\n\n## Other\n\nChange this reason.\n')
        self.commit()
        self.check('--manifest', 'manifest', code=1, token='UNTOUCHED-CHANGED')
