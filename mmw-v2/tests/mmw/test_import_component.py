"""Importer CLI effects on disposable git trees, never the live subtree."""

import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MMW = Path(__file__).resolve().parents[2]
SCRIPT = MMW / 'import' / 'import_component.py'
SUBTREE = 'mmw-v2/upstream-pstack'
MODE = 'mmw-v2/skills/mmw'
IMPORTS = MODE + '/imports.tsv'
REWRITES = 'mmw-v2/import/pstack-rewrites.tsv'
SPLIT = 'a' * 40
PRINCIPLE = ('---\nname: principle-one\n'
             'description: "First sentence. Another sentence."\n'
             'disable-model-invocation: true\n---\n# One\n\n'
             'Keep this wording. [Two](../principle-two/SKILL.md).\n')
OTHER = ('---\nname: principle-two\ndescription: Second principle.\n'
         'disable-model-invocation: true\n---\n# Two\n\nKeep this too.\n')
UPSTREAM_MODE = ('---\nname: Poteto Mode\n---\n# Poteto mode\n\n'
                 '## Non-negotiables\n\n- Trigger unchanged.\n\n'
                 '## Principles\n\n**Core**\n\n'
                 '- **One** (**principle-one**). First sentence.\n'
                 '\n**Architecture**\n\n'
                 '- **Two** (**principle-two**). Second principle.\n\n'
                 '## Comments\n\nKeep comments useful.\n\n'
                 '## Playbooks\n\nMatch a playbook.\n')
LOCAL_MODE = '# MMW\n\n## Non-negotiables\n\nKeep rules.\n\n## Playbooks\n\nKeep routes.\n'


class ImportComponent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-import-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(('MMW_', 'NMEM_')) and k not in
                    ('PASEO_AGENT_ID', 'ORCA_TERMINAL_HANDLE', 'HERDR_PANE_ID')}
        self.env['MMW_HOME'] = str(self.root / 'test-home')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Importer fixture')
        self.git('config', 'user.email', 'importer@example.test')
        self.write('mmw-v2/skills.txt', '# Fixture skills\n')
        self.write(IMPORTS, 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch\n')
        self.write(REWRITES, 'kind\told\tnew\tscope\n')
        self.write(SUBTREE + '/skills/principle-one/SKILL.md', PRINCIPLE)
        self.write(SUBTREE + '/skills/principle-two/SKILL.md', OTHER)
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md', UPSTREAM_MODE)
        self.pin()

    def write(self, path, content):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content.encode('utf-8') if isinstance(content, str) else content)
        return file

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, env=self.env,
                              text=True, capture_output=True, check=True).stdout.strip()

    def pin(self, split=SPLIT, trailers=True):
        self.git('add', '.')
        message = 'Fixture source'
        if trailers:
            message += f'\n\ngit-subtree-dir: {SUBTREE}\ngit-subtree-split: {split}'
        self.git('commit', '-qm', message, '--allow-empty')
        return self.git('rev-parse', 'HEAD')

    def run_import(self, *args, code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), *args, '--root', str(self.root)],
                                cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def rows(self, path=IMPORTS):
        with (self.root / path).open(newline='', encoding='utf-8') as file:
            return list(csv.reader(file, delimiter='\t'))[1:]

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): (p.read_bytes(), p.stat().st_mode)
                for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}

    def test_a_principle_lands_with_its_switch_line_removed_and_its_links_rewritten(self):
        self.run_import('principle', 'principle-one')
        self.assertEqual((self.root / MODE / 'principles/principle-one.md').read_bytes(),
                         b'---\nname: principle-one\ndescription: "First sentence. Another sentence."\n'
                         b'---\n# One\n\nKeep this wording. [Two](principle-two.md).\n')
        self.assertEqual((self.root / SUBTREE / 'skills/principle-one/SKILL.md').read_bytes(),
                         PRINCIPLE.encode())

    def test_a_principle_import_prints_its_index_line(self):
        self.write(MODE + '/SKILL.md', LOCAL_MODE)
        result = self.run_import('principle', 'principle-one')
        self.assertIn('INDEX\tCore\t- **One** (**principle-one**). First sentence.\n', result.stdout)
        self.assertIn('INDEX\tArchitecture\t- **Two** (**principle-two**). Second principle.\n', result.stdout)
        self.assertEqual((self.root / MODE / 'SKILL.md').read_bytes(), LOCAL_MODE.encode())

    def test_an_import_registers_one_row_of_seven_columns(self):
        self.run_import('principle', 'principle-one', '--batch', 'B1')
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][:4], ['principle', MODE + '/principles/principle-one.md',
                                      SUBTREE + '/skills/principle-one/SKILL.md', SPLIT])
        for row in rows:
            self.assertEqual(len(row), 7)
            self.assertTrue(row[4])
            self.assertEqual(row[5:], ['', 'B1'])
        self.write(SUBTREE + '/skills/helper/SKILL.md', '# Helper\n')
        self.run_import('skill', 'helper')
        self.assertEqual(self.rows()[-1][-1], 'on-demand')

    def test_a_rerun_adds_no_row_and_changes_nothing(self):
        self.run_import('principle', 'principle-one')
        before = self.snapshot()
        times = {p: (self.root / p).stat().st_mtime_ns for p in before}
        result = self.run_import('principle', 'principle-one')
        self.assertNotIn('REWRITE\t', result.stdout)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual({p: (self.root / p).stat().st_mtime_ns for p in before}, times)
        self.assertEqual(len(self.rows()), 2)
        self.assertEqual(len(self.rows(REWRITES)), 1)

    def test_an_unmapped_slot_keyword_stops_the_import(self):
        self.write(SUBTREE + '/skills/principle-two/SKILL.md',
                   OTHER + '\nUse AskQuestion and `gh`; Spawn Comment Sicko.\n')
        before = self.snapshot()
        result = self.run_import('principle', 'principle-one', code=1)
        for keyword in ('AskQuestion', 'gh', 'Spawn Comment Sicko'):
            self.assertIn(SUBTREE + '/skills/principle-two/SKILL.md:10: ' + keyword, result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.write(MODE + '/references/pstack-names.md',
                   '| pstack | MMW |\n|---|---|\n| `AskQuestion` | autonomy |\n'
                   '| `gh` | tracker |\n| Spawn Comment Sicko | a brief |\n')
        self.run_import('principle', 'principle-one')
        (self.root / MODE / 'references/pstack-names.md').unlink()
        self.write(SUBTREE + '/agents/helper.md',
                   '---\nname: helper\ndescription: Help.\nis_background: true\nmodel: special\n'
                   '---\n# Helper\n\nAskQuestion\n')
        before = self.snapshot()
        result = self.run_import('agent', 'helper', code=1)
        self.assertIn(SUBTREE + '/agents/helper.md:9: AskQuestion', result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_components_an_imported_file_names_are_imported_with_it(self):
        self.write(SUBTREE + '/skills/principle-two/SKILL.md',
                   OTHER + '\nApply the **one** principle, and the **show-me-your-work** skill.\n')
        self.write(SUBTREE + '/skills/show-me-your-work/SKILL.md', '# Show work\n\nKeep a record.\n')
        result = self.run_import('principle', 'principle-one')
        self.assertEqual({row[0] + ':' + row[2] for row in self.rows()}, {
            'principle:' + SUBTREE + '/skills/principle-one/SKILL.md',
            'principle:' + SUBTREE + '/skills/principle-two/SKILL.md',
            'skill:' + SUBTREE + '/skills/show-me-your-work/SKILL.md'})
        self.assertIn('IMPORTED\t3\n', result.stdout)
        self.assertIn('pstack/show-me-your-work\n', (self.root / 'mmw-v2/skills.txt').read_text())
        self.assertEqual((self.root / MODE / 'principles/principle-two.md').read_bytes(),
                         b'---\nname: principle-two\ndescription: Second principle.\n---\n# Two\n\n'
                         b'Keep this too.\n\nApply the **one** principle, and the **show-me-your-work** skill.\n')

    def test_a_name_the_set_already_has_or_pstack_names_maps_is_not_imported(self):
        self.write(MODE + '/principles/principle-two.md', '# MMW Two\n')
        self.write('mmw-v2/skills.txt', 'self/teach\n')
        self.write(SUBTREE + '/skills/principle-one/SKILL.md',
                   PRINCIPLE + '\nUse the **teach** skill and the **show-me-your-work** skill.\n')
        self.write(SUBTREE + '/skills/show-me-your-work/SKILL.md', '# Record\n')
        self.write(MODE + '/references/pstack-names.md',
                   '| pstack name | MMW |\n|---|---|\n| the **show-me-your-work** skill | ticket events |\n')
        result = self.run_import('principle', 'principle-one')
        self.assertEqual(len(self.rows()), 1)
        self.assertIn('IMPORTED\t1\n', result.stdout)
        self.assertEqual((self.root / MODE / 'principles/principle-two.md').read_bytes(), b'# MMW Two\n')
        self.assertEqual((self.root / 'mmw-v2/skills.txt').read_text(), 'self/teach\n')

    def test_a_dangling_dependency_is_refused_by_name(self):
        self.write(SUBTREE + '/skills/principle-one/SKILL.md',
                   PRINCIPLE + '\nRead **principle-absent**.\n')
        before = self.snapshot()
        result = self.run_import('principle', 'principle-one', code=1)
        self.assertIn(SUBTREE + '/skills/principle-one/SKILL.md:', result.stderr)
        self.assertIn('principle-absent', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.write(MODE + '/SKILL.md', LOCAL_MODE)
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md',
                   '# Source\n\n## Non-negotiables\n\n- Read principle-absent.\n\n'
                   '## Comments\n\nRead principle-absent.\n\n## Playbooks\n')
        for kind, name, line in (('mode-trigger', 'L5', 5), ('mode-section', 'Comments', 9)):
            with self.subTest(kind=kind):
                before = self.snapshot()
                result = self.run_import(kind, name, code=1)
                self.assertIn(SUBTREE + '/skills/poteto-mode/SKILL.md:' + str(line) +
                              ': dangling dependency principle-absent', result.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_a_row_with_a_judgement_change_is_not_overwritten(self):
        self.run_import('principle', 'principle-one')
        rows = self.rows()
        rows[0][5] = 'manual merge'
        self.write(IMPORTS, 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch\n' +
                   ''.join('\t'.join(row) + '\n' for row in rows))
        before = self.snapshot()
        result = self.run_import('principle', 'principle-one', code=1)
        self.assertIn(IMPORTS + ':2', result.stderr)
        self.assertIn(MODE + '/principles/principle-one.md', result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_a_playbook_lands_with_its_reference_and_script_paths_rewritten(self):
        source = ('### Sample\n\nRead [Notes](../references/notes.md).\n'
                  'Run `scripts/task.sh`. Use the **helper** skill.\n')
        self.write(SUBTREE + '/skills/poteto-mode/playbooks/sample.md', source)
        self.write(SUBTREE + '/skills/poteto-mode/references/notes.md', '# Notes\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/task.sh', '#!/bin/sh\nprintf done\n')
        self.write(SUBTREE + '/skills/helper/SKILL.md', '# Helper\n')
        result = self.run_import('playbook', 'sample')
        self.assertEqual((self.root / MODE / 'playbooks/sample.md').read_bytes(),
                         b'### Sample\n\nRead [Notes](../references/pstack/notes.md).\n'
                         b'Run `scripts/pstack/task.sh`. Use the **helper** skill.\n')
        self.assertEqual({r[0] for r in self.rows()},
                         {'playbook', 'mode-reference', 'mode-script', 'skill'})
        self.assertIn('IMPORTED\t4\n', result.stdout)

    def test_a_skill_becomes_a_skills_txt_line_marked_when_named(self):
        self.write(SUBTREE + '/skills/helper/SKILL.md', '# Helper\n')
        self.write(SUBTREE + '/skills/helper/references/leaf.md', '# Leaf\n')
        before_files = set(self.snapshot())
        self.run_import('skill', 'helper')
        self.assertEqual((self.root / 'mmw-v2/skills.txt').read_text(),
                         '# Fixture skills\npstack/helper\n')
        self.assertEqual(set(self.snapshot()), before_files)
        self.assertEqual(self.rows()[0][1:3], [SUBTREE + '/skills/helper/SKILL.md'] * 2)
        self.assertEqual(self.rows()[0][4:6], ['', ''])
        self.write(MODE + '/SKILL.md', LOCAL_MODE + '\nUse the **helper** skill.\n')
        self.run_import('skill', 'helper')
        self.assertEqual((self.root / 'mmw-v2/skills.txt').read_text(),
                         '# Fixture skills\npstack/helper +model-invoked\n')
        self.assertEqual(len(self.rows()), 1)
        (self.root / MODE / 'SKILL.md').unlink()
        self.write(MODE + '/playbooks/local.md', 'Use the **helper** skill.\n')
        self.run_import('skill', 'helper')
        self.assertIn('pstack/helper +model-invoked\n', (self.root / 'mmw-v2/skills.txt').read_text())
        self.write(SUBTREE + '/skills/new-helper/SKILL.md', '# New helper\n')
        self.write(SUBTREE + '/skills/poteto-mode/playbooks/new.md', 'Use the **new-helper** skill.\n')
        self.run_import('playbook', 'new')
        self.assertIn('pstack/new-helper +model-invoked\n', (self.root / 'mmw-v2/skills.txt').read_text())
        (self.root / MODE / 'playbooks/local.md').unlink()
        source = UPSTREAM_MODE.replace('- Trigger unchanged.', '- Use the **helper** skill.').replace(
            'Keep comments useful.', 'Use the **helper** skill.')
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md', source)
        self.write(SUBTREE + '/skills/poteto-mode/playbooks/later.md', 'Use the **helper** skill.\n')
        for kind, name in (('playbook', 'later'), ('mode-trigger', 'L8'), ('mode-section', 'Comments')):
            with self.subTest(later_import=kind):
                self.write(MODE + '/SKILL.md', LOCAL_MODE)
                self.write('mmw-v2/skills.txt', 'pstack/helper\npstack/new-helper +model-invoked\nself/native\n')
                before = self.snapshot()
                self.run_import(kind, name, '--dry-run')
                self.assertEqual(self.snapshot(), before)
                result = self.run_import(kind, name)
                self.assertIn('SKILLS\tpstack/helper +model-invoked\n', result.stdout)
                self.assertEqual((self.root / 'mmw-v2/skills.txt').read_text(),
                                 'pstack/helper +model-invoked\npstack/new-helper +model-invoked\nself/native\n')
                self.assertEqual(len([row for row in self.rows() if row[0] == 'skill' and
                                      row[2].endswith('/helper/SKILL.md')]), 1)
                (self.root / MODE / 'playbooks/later.md').unlink(missing_ok=True)

    def test_a_mode_reference_and_a_mode_script_land_under_pstack(self):
        self.write(SUBTREE + '/skills/poteto-mode/references/notes.md', '# Notes\n\nKeep bytes.\n')
        script = self.write(SUBTREE + '/skills/poteto-mode/scripts/task.sh',
                            '#!/bin/sh\n. "$(dirname "$0")/helper.sh"\nprintf done\n')
        script.chmod(0o755)
        self.write(SUBTREE + '/skills/poteto-mode/scripts/helper.sh', 'answer=done\n')
        self.run_import('mode-reference', 'notes.md')
        self.run_import('mode-script', 'task.sh')
        self.assertEqual((self.root / MODE / 'references/pstack/notes.md').read_bytes(),
                         b'# Notes\n\nKeep bytes.\n')
        self.assertEqual((self.root / MODE / 'scripts/pstack/task.sh').read_bytes(), script.read_bytes())
        self.assertEqual((self.root / MODE / 'scripts/pstack/task.sh').stat().st_mode & 0o777, 0o755)
        self.assertEqual((self.root / MODE / 'scripts/pstack/helper.sh').read_bytes(), b'answer=done\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/tool/main.py', 'import helper\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/tool/helper.py', 'answer = 42\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/tool/asset.bin', b'\xff\x00\x10')
        self.run_import('mode-script', 'tool')
        self.assertEqual((self.root / MODE / 'scripts/pstack/tool/asset.bin').read_bytes(), b'\xff\x00\x10')
        self.assertEqual(len(self.rows()), 6)
        self.assertEqual({r[2].split('/')[-1] for r in self.rows()},
                         {'notes.md', 'task.sh', 'helper.sh', 'main.py', 'helper.py', 'asset.bin'})
        self.write(SUBTREE + '/skills/poteto-mode/scripts/python-task.py', 'from python_helper import answer\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/python_helper.py', 'answer = 42\n')
        self.run_import('mode-script', 'python-task.py')
        self.assertEqual((self.root / MODE / 'scripts/pstack/python_helper.py').read_bytes(), b'answer = 42\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/js-task.mjs', 'import { answer } from "./js-helper.mjs";\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/js-helper.mjs', 'export const answer = 42;\n')
        self.run_import('mode-script', 'js-task.mjs')
        self.assertEqual((self.root / MODE / 'scripts/pstack/js-helper.mjs').read_bytes(), b'export const answer = 42;\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/broken.py', 'def broken(\n')
        before = self.snapshot()
        result = self.run_import('mode-script', 'broken.py', code=2)
        self.assertIn(SUBTREE + '/skills/poteto-mode/scripts/broken.py:1', result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_an_agent_lands_as_a_brief_without_host_fields(self):
        source = ('---\nname: helper-agent\ndescription: >-\n  Help carefully.\n  Read the brief.\n'
                  'is_background: true\nmodel: special\ntools:\n  - Shell\n---\n\n# Brief\n\nKeep this body.\n')
        self.write(SUBTREE + '/agents/helper-agent.md', source)
        self.run_import('agent', 'helper-agent')
        self.assertEqual((self.root / MODE / 'references/pstack/agents/helper-agent.md').read_bytes(),
                         b'---\nname: helper-agent\ndescription: >-\n  Help carefully.\n  Read the brief.\n'
                         b'---\n\n# Brief\n\nKeep this body.\n')
        row = self.rows()[0]
        self.assertEqual(row[:3], ['agent', MODE + '/references/pstack/agents/helper-agent.md',
                                  SUBTREE + '/agents/helper-agent.md'])
        self.assertTrue(row[4])
        self.assertEqual(self.rows(REWRITES), [])

    def test_a_mode_trigger_lands_under_imported_triggers(self):
        self.write(MODE + '/SKILL.md', LOCAL_MODE)
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md',
                   UPSTREAM_MODE.replace('- Trigger unchanged.\n', '- Trigger unchanged.\n- Another trigger.\n'))
        result = self.run_import('mode-trigger', 'L8')
        wanted = ('# MMW\n\n## Non-negotiables\n\nKeep rules.\n\n'
                  '### Imported triggers\n\n- Trigger unchanged.\n\n'
                  '## Playbooks\n\nKeep routes.\n')
        self.assertEqual((self.root / MODE / 'SKILL.md').read_bytes(), wanted.encode())
        self.assertEqual(self.rows()[0][:3], ['mode-trigger', MODE + '/SKILL.md#Imported triggers',
                                            SUBTREE + '/skills/poteto-mode/SKILL.md:L8'])
        self.assertIn('MODE\t' + MODE + '/SKILL.md#Imported triggers\n', result.stdout)
        before = self.snapshot()
        self.run_import('mode-trigger', 'L8')
        self.assertEqual(self.snapshot(), before)
        self.run_import('mode-trigger', 'L9')
        self.assertEqual(len(self.rows()), 2)
        self.assertEqual((self.root / MODE / 'SKILL.md').read_text().count('### Imported triggers'), 1)
        self.run_import('mode-trigger', 'L10')
        source = (self.root / SUBTREE / 'skills/poteto-mode/SKILL.md').read_text()
        number = len(source.splitlines()) + 1
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md', source + '- Last trigger.\n')
        self.run_import('mode-trigger', f'L{number}')
        self.assertIn('- Another trigger.\n\n- Last trigger.\n\n',
                      (self.root / MODE / 'SKILL.md').read_text())
        self.assertIn('REFRESH\t4\t0\t0\n', self.run_import('--refresh').stdout)

    def test_a_mode_section_lands_before_playbooks(self):
        self.write(MODE + '/SKILL.md', LOCAL_MODE)
        self.run_import('mode-section', 'Comments')
        wanted = ('# MMW\n\n## Non-negotiables\n\nKeep rules.\n\n'
                  '## Comments\n\nKeep comments useful.\n\n'
                  '## Playbooks\n\nKeep routes.\n')
        self.assertEqual((self.root / MODE / 'SKILL.md').read_bytes(), wanted.encode())
        self.assertEqual(self.rows()[0][:3], ['mode-section', MODE + '/SKILL.md#Comments',
                                            SUBTREE + '/skills/poteto-mode/SKILL.md'])
        before = self.snapshot()
        self.run_import('mode-section', 'Comments')
        self.assertEqual(self.snapshot(), before)
        self.write(IMPORTS, 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch\n')
        before = self.snapshot()
        result = self.run_import('mode-section', 'Comments', code=1)
        self.assertIn(MODE + '/SKILL.md#Comments', result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_mode_types_need_the_mode_file(self):
        for kind, name in (('mode-trigger', 'L8'), ('mode-section', 'Comments')):
            with self.subTest(kind=kind):
                before = self.snapshot()
                result = self.run_import(kind, name, code=2)
                self.assertIn(MODE + '/SKILL.md', result.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_refresh_lists_imports_the_subtree_has_changed(self):
        self.run_import('principle', 'principle-one')
        before = self.snapshot()
        result = self.run_import('--refresh')
        self.assertIn('REFRESH\t2\t0\t0\n', result.stdout)
        self.assertEqual(self.snapshot(), before)
        rows = self.rows()
        rows[1][5] = 'manual change'
        header = 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch\n'
        self.write(IMPORTS, header + ''.join('\t'.join(row) + '\n' for row in rows))
        before = self.snapshot()
        result = self.run_import('--refresh')
        self.assertIn('REFRESH\t2\t0\t0\n', result.stdout)
        self.assertNotIn('REVIEW\t', result.stdout)
        self.assertEqual(self.snapshot(), before)
        rows[1][5] = ''
        self.write(IMPORTS, header + ''.join('\t'.join(row) + '\n' for row in rows))
        self.write(SUBTREE + '/skills/principle-one/SKILL.md', PRINCIPLE + '\nNew source content.\n')
        self.pin(split='b' * 40)
        before = self.snapshot()
        result = self.run_import('--refresh', code=1)
        self.assertIn('STALE\t' + MODE + '/principles/principle-one.md\t' +
                      SUBTREE + '/skills/principle-one/SKILL.md\n', result.stdout)
        self.assertIn('REFRESH\t2\t1\t0\n', result.stdout)
        self.assertEqual(self.snapshot(), before)
        rows = self.rows()
        rows[1][5] = 'manual change'
        self.write(IMPORTS, 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch\n' +
                   ''.join('\t'.join(row) + '\n' for row in rows))
        before = self.snapshot()
        result = self.run_import('--refresh', code=1)
        self.assertIn('REVIEW\t' + MODE + '/principles/principle-two.md\t' +
                      SUBTREE + '/skills/principle-two/SKILL.md\n', result.stdout)
        self.assertIn('REFRESH\t2\t1\t1\n', result.stdout)
        self.assertEqual(self.snapshot(), before)


    def test_a_same_name_component_is_refused_by_name(self):
        self.write(MODE + '/principles/principle-one.md', '# MMW One\n')
        self.write(SUBTREE + '/skills/poteto-mode/playbooks/sample.md', '### Sample\n')
        self.write(MODE + '/playbooks/sample.md', '### MMW Sample\n')
        self.write(SUBTREE + '/skills/helper/SKILL.md', '# Helper\n')
        self.write('mmw-v2/skills.txt', 'self/helper\n')
        for kind, name, path in (('principle', 'principle-one', MODE + '/principles/principle-one.md'),
                                 ('playbook', 'sample', MODE + '/playbooks/sample.md'),
                                 ('skill', 'helper', 'mmw-v2/skills.txt')):
            with self.subTest(kind=kind):
                before = self.snapshot()
                result = self.run_import(kind, name, code=1)
                self.assertIn(path, result.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_a_missing_subtree_squash_commit_or_component_exits_2(self):
        self.check_unreadable_registry_or_unknown_type_writes_nothing()
        before = self.snapshot()
        result = self.run_import('principle', 'principle-absent', code=2)
        self.assertIn('principle-absent', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.git('checkout', '--orphan', 'no-provenance')
        self.pin(trailers=False)
        before = self.snapshot()
        result = self.run_import('principle', 'principle-one', code=2)
        self.assertIn('git-subtree-split', result.stderr)
        self.assertEqual(self.snapshot(), before)
        (self.root / SUBTREE).rename(self.root / 'not-a-subtree')
        before = self.snapshot()
        result = self.run_import('principle', 'principle-one', code=2)
        self.assertIn(SUBTREE, result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_prints_the_plan_and_writes_nothing(self):
        before = self.snapshot()
        status = self.git('status', '--porcelain')
        result = self.run_import('principle', 'principle-one', '--dry-run')
        self.assertIn('COPY\t' + SUBTREE + '/skills/principle-one/SKILL.md\t' +
                      MODE + '/principles/principle-one.md\n', result.stdout)
        self.assertIn('REWRITE\tpath\t' + SUBTREE + '/skills/principle-two/SKILL.md\t' +
                      MODE + '/principles/principle-two.md\t\n', result.stdout)
        self.assertIn('REGISTER\tprinciple\t' + MODE + '/principles/principle-one.md\t', result.stdout)
        self.assertIn('DRY-RUN\t2\n', result.stdout)
        self.assertEqual(self.git('status', '--porcelain'), status)
        self.assertEqual(self.snapshot(), before)

    def test_rewrite_rows_are_accepted_by_lint_drafts(self):
        revision = self.git('rev-parse', 'HEAD')
        self.run_import('principle', 'principle-one')
        rows = self.rows(REWRITES)
        self.assertEqual(rows, [['path', SUBTREE + '/skills/principle-two/SKILL.md',
                                 MODE + '/principles/principle-two.md', '']])
        drafts = self.root / 'drafts'
        drafts.mkdir()
        rename_lines = '\n'.join('rename ' + row[0] + ' ' + row[1] + ' -> ' + row[2] +
                                 (' in ' + row[3] if row[3] else '') for row in rows)
        draft = ('TITLE: fixture\nLABELS: mmw:ticket, ready-for-agent, junior-worker\n'
                 'BLOCKED BY: (none)\n---\n## Owns\n\n- file\n\n## Moves\n\n'
                 f'```moves\nfrom {revision}\n{rename_lines}\n```\n')
        (drafts / 'fixture.md').write_text(draft, encoding='utf-8')
        command = ['uv', 'run', '--quiet', '--with', 'pyyaml', 'python',
                   str(MMW / 'tests/lib/check_verbatim_moves.py'), '--lint-drafts', str(drafts),
                   '--renames-table', str(self.root / REWRITES)]
        result = subprocess.run(command, cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('DRAFTS OK', result.stdout)
        (drafts / 'fixture.md').write_text(draft.replace('```\n',
            'rename token missing.md -> absent.md\n```\n'), encoding='utf-8')
        result = subprocess.run(command, cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertRegex(result.stdout, r'(?m)^fixture\.md:\d+: L5\b')


    def test_an_unusable_dependency_destination_leaves_no_partial_import(self):
        self.write(SUBTREE + '/skills/poteto-mode/playbooks/sample.md',
                   '### Sample\n\nRead [Notes](../references/notes.md).\n')
        self.write(SUBTREE + '/skills/poteto-mode/references/notes.md', '# Notes\n')
        self.write(MODE + '/references', 'not a directory\n')
        before = self.snapshot()
        result = self.run_import('playbook', 'sample', code=2)
        self.assertIn(MODE + '/references', result.stderr)
        self.assertEqual(self.snapshot(), before)
        result = self.run_import('playbook', 'sample', '--dry-run', code=2)
        self.assertIn(MODE + '/references', result.stderr)
        self.assertEqual(self.snapshot(), before)


    def test_a_mode_section_keeps_headings_inside_code_fences(self):
        source = UPSTREAM_MODE.replace('Keep comments useful.',
                                       'Keep comments useful.\n\n```markdown\n## Playbooks\n```')
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md', source)
        self.write(MODE + '/SKILL.md', LOCAL_MODE)
        self.run_import('mode-section', 'Comments')
        self.assertIn('## Comments\n\nKeep comments useful.\n\n```markdown\n## Playbooks\n```\n\n'
                      '## Playbooks\n\nKeep routes.\n',
                      (self.root / MODE / 'SKILL.md').read_text())


    def test_each_slot_keyword_requires_a_first_column_mapping(self):
        keywords = ('control skill', 'Opening a PR', 'gh', 'origin', 'gt', 'subagent_type',
                    'your configured code model', 'pstack-models.mdc', 'AskQuestion', '/loop',
                    '/goal', 'cloud', 'agent-transcripts', 'git show origin/main:', 'Spawn Comment Sicko')
        path = SUBTREE + '/skills/poteto-mode/references/slots.md'
        self.write(path, '\n'.join(keywords) + '\n')
        self.write(MODE + '/references/pstack-names.md',
                   '| source | destination |\n|---|---|\n| no match | ' + ' '.join(keywords) + ' |\n')
        before = self.snapshot()
        result = self.run_import('mode-reference', 'slots.md', code=1)
        for line, word in enumerate(keywords, 1):
            key = 'configured … model' if 'configured' in word else word
            self.assertIn(f'{path}:{line}: {key}', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.write(MODE + '/references/pstack-names.md', '| source | destination |\n|---|---|\n' +
                   ''.join('| ' + word + ' | mapped |\n' for word in keywords))
        self.run_import('mode-reference', 'slots.md')

    def test_refresh_compares_skills_mode_fragments_and_other_file_types(self):
        self.write(MODE + '/SKILL.md', LOCAL_MODE)
        self.write(SUBTREE + '/skills/helper/SKILL.md', '# Helper\n')
        self.write(SUBTREE + '/agents/helper.md', '---\nname: helper\ndescription: Help.\n---\n# Help\n')
        self.write(SUBTREE + '/skills/poteto-mode/references/notes.md', '# Notes\n')
        self.write(SUBTREE + '/skills/poteto-mode/scripts/task.sh', '#!/bin/sh\nprintf done\n')
        self.write(SUBTREE + '/skills/poteto-mode/playbooks/sample.md', '### Sample\n')
        components = (('skill', 'helper'), ('mode-trigger', 'L8'), ('mode-section', 'Comments'),
                      ('agent', 'helper'), ('mode-reference', 'notes.md'),
                      ('mode-script', 'task.sh'), ('playbook', 'sample'))
        for kind, name in components:
            self.run_import(kind, name)
        before = self.snapshot()
        result = self.run_import('--refresh')
        self.assertIn('REFRESH\t7\t0\t0\n', result.stdout)
        self.assertEqual(self.snapshot(), before)
        self.write(SUBTREE + '/skills/poteto-mode/SKILL.md',
                   UPSTREAM_MODE.replace('- Trigger unchanged.', '- Updated trigger.').replace(
                       'Keep comments useful.', 'Changed source comments.'))
        for kind, name in components[3:]:
            row = next(row for row in self.rows() if row[0] == kind)
            path = self.root / row[2]
            path.write_bytes(path.read_bytes() + b'\nSource changed.\n')
        self.write(MODE + '/SKILL.md', LOCAL_MODE + '\nUse the **helper** skill.\n')
        self.pin(split='c' * 40)
        before = self.snapshot()
        result = self.run_import('--refresh', code=1)
        self.assertIn('REFRESH\t7\t7\t0\n', result.stdout)
        self.assertEqual(self.snapshot(), before)
        (self.root / MODE / 'SKILL.md').unlink()
        before = self.snapshot()
        self.assertIn('REFRESH\t7\t6\t0\n', self.run_import('--refresh', code=1).stdout)
        self.assertEqual(self.snapshot(), before)


    def check_unreadable_registry_or_unknown_type_writes_nothing(self):
        header = 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch\n'
        bad_rows = ('broken\n', header + 'not-a-type\tlocal\tsource\t' + SPLIT + '\t\t\tB1\n',
                    header + 'mode-trigger\t' + MODE + '/SKILL.md#Imported triggers\t' +
                    SUBTREE + '/skills/poteto-mode/SKILL.md\t' + SPLIT + '\t\t\tB1\n')
        for content in bad_rows:
            with self.subTest(content=content):
                self.write(IMPORTS, content)
                before = self.snapshot()
                result = self.run_import('principle', 'principle-one', code=2)
                self.assertIn(IMPORTS, result.stderr)
                self.assertEqual(self.snapshot(), before)
        self.write(IMPORTS, header)
        before = self.snapshot()
        result = self.run_import('not-a-type', 'principle-one', code=2)
        self.assertIn('not-a-type', result.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
