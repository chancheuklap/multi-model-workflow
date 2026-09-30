"""Exercise --lint-drafts against disposable drafts and a committed snapshot."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'lib' / 'check_verbatim_moves.py'
HEADER = 'kind\told\tnew\tscope\n'
KEY_ROW = 'token\tkey.md\trelease-manifest.md\tmmw-v2/skills/exe-release/**\n'
EDIT_ROW = 'token\tedit-pages.md\tset-up-and-sign-off.md\n'


class VerbatimLintDrafts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-lint-drafts-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.drafts = Path(self.tmp.name) / 'drafts'
        self.root.mkdir()
        self.drafts.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.sha = self.pin()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, text=True,
                              capture_output=True, check=True).stdout.strip()

    def write(self, path, text):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding='utf-8')

    def pin(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture', '--allow-empty')
        self.sha = self.git('rev-parse', 'HEAD')
        return self.sha

    def begin(self):
        for child in self.drafts.iterdir():
            if child.is_file():
                child.unlink()

    def draft(self, name, moves, blocked='(none)'):
        text = (
            f'TITLE: {name}\n'
            'LABELS: mmw:ticket, ready-for-agent, junior-worker\n'
            f'BLOCKED BY: {blocked}\n'
            '---\n'
            '## Owns\n\n'
            '- file\n\n'
            '## Moves\n\n'
            '```moves\n'
            f'{moves.strip()}\n'
            '```\n'
        )
        (self.drafts / f'{name}.md').write_text(text, encoding='utf-8')

    def draft_without_moves(self, name, blocked='(none)'):
        text = (
            f'TITLE: {name}\n'
            'LABELS: mmw:ticket, ready-for-agent, junior-worker\n'
            f'BLOCKED BY: {blocked}\n'
            '---\n'
            '## Owns\n\n'
            '- file\n'
        )
        (self.drafts / f'{name}.md').write_text(text, encoding='utf-8')

    def table(self, name, body):
        path = Path(self.tmp.name) / name
        path.write_text(HEADER + body, encoding='utf-8')
        return path

    def lint(self, code=0, token=None, tables=(), message=''):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('MMW_', 'NMEM_'))}
        args = [sys.executable, str(SCRIPT), '--lint-drafts', str(self.drafts)]
        for path in tables:
            args.extend(['--renames-table', str(path)])
        result = subprocess.run(args, cwd=self.root, env=env, text=True,
                                capture_output=True)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, code, message + '\n' + output)
        if token:
            self.assertIn(token, output, message)
        if code == 0:
            self.assertRegex(output, r'(?m)^DRAFTS OK \d+ drafts, \d+ moves checked$')
        else:
            self.assertNotIn('DRAFTS OK', output, message)
        return output

    def test_lint_drafts_locations_and_provenance(self):
        claim = '## Claim\n\nKeep the wording.\n\n## Other\n\nLeave this sentence.\n\n## Claim\n\nKeep it again.\n'
        self.write('source.md', claim)
        self.write('dest.md', '## Place\n\nAlready here.\n')
        self.pin()

        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove source.md#Claim -> dest.md#Place')
        output = self.lint(1, 'L1', message='a heading that matches twice')
        self.assertIn('source.md', output)

        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove source.md#Missing -> dest.md#Place')
        self.lint(1, 'L1', message='a heading that matches nothing')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove absent.md -> dest.md')
        self.lint(1, 'L1', message='a source file that is not on from')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove source.md#Other -> dest.md#Place')
        # dest.md has one Place. Give the target two anchors of that name.
        self.write('dest.md', '## Place\n\nOne.\n\n## Place\n\nTwo.\n')
        self.pin()
        self.draft('alpha', f'from {self.sha}\nmove source.md#Other -> dest.md#Place')
        self.lint(1, 'L1', message='a target heading that matches twice')

        prose = '## Claim\n\nStop now. Continue later.\n'
        self.write('range.md', prose)
        self.pin()
        self.begin()
        self.draft('alpha', (
            f'from {self.sha}\n'
            'move range.md#Claim -> range.md#Claim\n'
            'replace "Nowhere to be seen" -> "Seen once." : R18 §3'
        ))
        self.lint(1, 'L2', message='replace old string matches nothing')

        self.write('range.md', '## Claim\n\nStop now. Stop now.\n')
        self.pin()
        self.begin()
        self.draft('alpha', (
            f'from {self.sha}\n'
            'move range.md#Claim -> range.md#Claim\n'
            'replace "Stop now." -> "Go now." : R18 §3'
        ))
        self.lint(1, 'L2', message='replace old string matches twice')

        self.begin()
        self.draft('alpha', f'from {self.sha}\ndrop range.md#Claim "Absent prefix" : kept elsewhere')
        self.lint(1, 'L2', message='drop prefix matches nothing')

        self.begin()
        self.draft('alpha', f'from {self.sha}\ndrop range.md#Claim "Stop now." : kept elsewhere')
        self.lint(1, 'L2', message='drop prefix matches two sentences')

        self.begin()
        self.draft('alpha', (
            f'from {self.sha}\n'
            'move range.md#Claim -> range.md#Claim\n'
            'replace "Stop now." -> "Go now."'
        ))
        self.lint(1, 'L3', message='replace without provenance')

        self.write('range.md', '## Claim\n\nStop now. Continue later.\n')
        self.pin()
        self.begin()
        self.draft('alpha', f'from {self.sha}\ndrop range.md#Claim "Stop now." :')
        self.lint(1, 'L3', message='drop without provenance')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nnew range.md#Claim :')
        self.lint(1, 'L3', message='new without provenance')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nnew range.md#Claim : Spec skeleton')
        self.lint(1, 'L3', message='open new whose provenance is not an R20 section')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nnew range.md#Claim : R20 §5.2')
        self.lint(1, 'L3', message='open new whose provenance has no section name')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nnew range.md#Claim : R20 §5.2 Reply')
        self.lint(0, message='open new naming an R20 section')

        self.begin()
        self.draft('alpha', (
            f'from {self.sha}\n'
            'new range.md#Claim "A fresh sentence." : Spec allows this sentence\n'
            'new range.md#Claim title "Extra" : Spec skeleton'
        ))
        self.lint(0, message='a whole sentence and a title need only a non-empty provenance')

    def test_lint_drafts_batch_overlap(self):
        self.write('left.md', ''.join(f'Line {i} stays here.\n' for i in range(1, 7)))
        self.write('src.md', '## Claim\n\nKeep the wording.\n\n## Other\n\nKeep the other wording.\n')
        self.write('dest.md', '## Claim\n\nOld wording stays.\n')
        self.pin()

        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove left.md:L1-L4 -> out-a.md')
        self.draft('beta', f'from {self.sha}\nmove left.md:L3-L6 -> out-b.md')
        self.lint(1, 'L4', message='source ranges overlap')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove src.md#Claim -> dest.md#Claim')
        self.draft('beta', f'from {self.sha}\nmove src.md#Other -> dest.md#Claim')
        self.lint(1, 'L4', message='target locations repeat')

        self.begin()
        self.draft('alpha', f'from {self.sha}\ncopy src.md -> dest.md')
        self.draft('beta', f'from {self.sha}\nnew dest.md#Claim "A further sentence." : R20 §5.2 Reply')
        self.lint(1, 'L4', message='a whole-file target shares the file with a section target')

    def test_lint_drafts_renames(self):
        skill = 'mmw-v2/skills/exe-release/SKILL.md'
        self.write(skill, '## One\n\nRead `key.md` now.\n\n## Two\n\nRead `key.md` later.\n')
        self.write('demo.md', 'Read `edit-pages.md` before editing.\n')
        self.write('notes.md', 'Read `key.md` in a note.\n')
        self.write('mmw-v2/skills/demo/old.md', 'Keep the wording.\n')
        self.write('plain.md', '## Claim\n\nNothing renamed here.\n')
        self.pin()
        edit = self.table('edit.tsv', EDIT_ROW)
        key = self.table('key.tsv', KEY_ROW)
        both = self.table('both.tsv', KEY_ROW + EDIT_ROW)

        self.begin()
        self.draft('alpha', f'from {self.sha}\nrename token missing.md -> gone.md')
        output = self.lint(1, 'L5', tables=(both,), message='rename row absent from the table')
        self.assertIn('RENAME-NOT-IN-TABLE', output)

        self.begin()
        self.draft('alpha', f'from {self.sha}\nrename token key.md -> release-manifest.md')
        output = self.lint(1, 'L5', tables=(key,), message='same names with a different scope')
        self.assertIn('RENAME-NOT-IN-TABLE', output)

        second = self.table('second.tsv', 'token\tother.md\telsewhere.md\n')
        self.begin()
        self.draft('alpha', f'from {self.sha}\nrename token other.md -> elsewhere.md')
        self.lint(1, 'L5', tables=(key,), message='row not in the only table')
        self.lint(0, tables=(key, second), message='row present in a second table')

        self.begin()
        self.draft('alpha', f'from {self.sha}\nrename token edit-pages.md -> set-up-and-sign-off.md')
        self.draft('beta', f'from {self.sha}\nmove demo.md -> demo.md')
        output = self.lint(1, 'L6', tables=(edit,), message='another draft keeps the old token')
        self.assertIn('RENAME-NOT-CARRIED', output)

        self.begin()
        self.draft('alpha', f'from {self.sha}\nrename token edit-pages.md -> set-up-and-sign-off.md')
        self.draft('beta', f'from {self.sha}\nnew fresh.md "See `edit-pages.md` here." : Spec note')
        self.lint(1, 'L6', tables=(edit,), message='a new sentence keeps the old token')

        path_row = 'path\tmmw-v2/skills/demo/old.md\tmmw-v2/skills/demo/new.md\n'
        paths = self.table('paths.tsv', path_row)
        self.begin()
        self.draft('alpha', (
            f'from {self.sha}\n'
            'rename path mmw-v2/skills/demo/old.md -> mmw-v2/skills/demo/new.md'
        ))
        self.draft('beta', f'from {self.sha}\nmove mmw-v2/skills/demo/old.md -> kept.md')
        self.lint(1, 'L6', tables=(paths,), message='a source path is the renamed path')

        self.begin()
        self.draft('alpha', (
            f'from {self.sha}\n'
            f'rename token key.md -> release-manifest.md in mmw-v2/skills/exe-release/**'
        ))
        self.draft('beta', f'from {self.sha}\nmove notes.md -> notes.md')
        self.lint(0, tables=(key,), message='old token outside the rename scope')

        carried = f'rename token edit-pages.md -> set-up-and-sign-off.md'
        self.begin()
        self.draft('alpha', f'from {self.sha}\n{carried}')
        self.draft('beta', f'from {self.sha}\n{carried}')
        self.lint(1, 'L7', tables=(edit,), message='two drafts carry one rename and can run together')

        self.begin()
        self.draft_without_moves('alpha')
        self.draft('beta', f'from {self.sha}\n{carried}', blocked='alpha')
        self.draft('gamma', f'from {self.sha}\n{carried}', blocked='alpha')
        self.lint(1, 'L7', tables=(edit,), message='siblings blocked by one draft can still run together')

        self.begin()
        self.draft('alpha', f'from {self.sha}\n{carried}')
        self.draft_without_moves('beta', blocked='alpha')
        self.draft('gamma', f'from {self.sha}\n{carried}', blocked='beta')
        self.lint(0, tables=(edit,), message='a chain through another draft orders the rename')

        scoped = 'rename token key.md -> release-manifest.md in mmw-v2/skills/exe-release/**'
        self.begin()
        self.draft('alpha', f'from {self.sha}\nmove {skill}#One -> mmw-v2/skills/exe-release/one.md\n{scoped}')
        self.draft('beta', (
            f'from {self.sha}\n'
            f'move {skill}#Two -> mmw-v2/skills/exe-release/two.md\n'
            f'{scoped}'
        ), blocked='alpha')
        output = self.lint(0, tables=(key,), message='table, carried line and blocking edge all hold')
        self.assertRegex(output, r'(?m)^DRAFTS OK 2 drafts, 4 moves checked$')

    def test_lint_drafts_that_cannot_be_read_exit_2(self):
        missing = self.drafts / 'no-such-directory'
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('MMW_', 'NMEM_'))}
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--lint-drafts', str(missing)],
            cwd=self.root, env=env, text=True, capture_output=True)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 2, output)
        self.assertNotIn('DRAFTS OK', output)

        self.begin()
        self.draft('alpha', 'from 1111111111111111111111111111111111111111\nmove source.md -> dest.md')
        output = self.lint(2, message='from is not a commit')
        self.assertNotIn('DRAFTS OK', output)
