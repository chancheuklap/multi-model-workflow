"""Exercise the manifest CLI in real, disposable git repositories."""
import os
import random
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'lib' / 'check_verbatim_moves.py'


class VerbatimCompare(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-verbatim-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.write('source.md', '')
        self.base = self.commit()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, text=True,
                              capture_output=True, check=True).stdout.strip()

    def write(self, path, text):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding='utf-8')

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture', '--allow-empty')
        return self.git('rev-parse', 'HEAD')

    def source(self, text, path='source.md'):
        self.write(path, text)
        self.base = self.commit()

    def check(self, lines, code=0, token=None, all_findings=False):
        self.commit()
        self.write('manifest', f'from {self.base}\n' + lines + '\n')
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('MMW_', 'NMEM_'))}
        args = [sys.executable, str(SCRIPT), '--manifest', 'manifest']
        if all_findings:
            args.append('--all')
        result = subprocess.run(args, cwd=self.root, env=env, text=True,
                                capture_output=True)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, code, output)
        if token:
            self.assertIn(token, output)
        if code:
            self.assertNotIn('VERBATIM OK', output)
        else:
            self.assertTrue(output.startswith('VERBATIM OK'), output)
        return output

    def test_a_reflowed_move_is_verbatim(self):
        self.source('## 1. Claim\n\nKeep the wording. Read the\nreason.\n\n- Retain the rule.\n+ Preserve its order.\n')
        self.write('source.md', '')
        self.write('target.md', '1. **Claim.** Keep the\n   wording.\n\n   Read the reason.\n\n   * Retain the rule.\n   2) Preserve its order.\n')
        self.check('move source.md#Claim -> target.md#Claim')

    def test_one_changed_word_is_changed(self):
        self.source('Keep the original wording.\n')
        self.write('target.md', 'Keep the improved wording.\n')
        output = self.check('copy source.md -> target.md', 1, 'CHANGED')
        self.assertIn('- original', output)
        self.assertIn('+ improved', output)
        self.assertIn('target.md:1:', output)
        self.source('Go.\n')
        self.write('target.md', 'Stop.\n')
        self.check('copy source.md -> target.md', 1, 'CHANGED')

    def test_a_missing_sentence_is_deleted_unless_dropped(self):
        self.source('## Claim\n\nKeep the rule. Explain the reason.\n')
        self.write('source.md', '## Other\n\nExplain the reason.\n')
        self.write('target.md', '## Claim\n\nKeep the rule.\n\n## Elsewhere\n\nExplain the reason.\n')
        output = self.check('move source.md#Claim -> target.md#Claim', 1, 'DELETED')
        self.assertIn('found in target.md:7', output)
        self.check('move source.md#Claim -> target.md#Claim\n'
                   'drop source.md#Claim "Explain the reason." : Other carries it')

    def test_an_unlisted_sentence_is_added_unless_new(self):
        self.source('Keep the rule.\n')
        self.write('target.md', 'Keep the rule. Explain the reason.\n\n## Finish\n')
        self.check('copy source.md -> target.md', 1, 'ADDED')
        lines = ('copy source.md -> target.md\n'
                 'new target.md "Explain the reason." : Spec reason\n'
                 'new target.md title "Finish" : Spec skeleton')
        self.check(lines)
        output = self.check('copy source.md -> target.md\nnew target.md : R20 §5.2 Reply')
        self.assertIn('NEW target.md:1: Explain the reason.', output)
        self.assertIn('NEW target.md:3: Finish', output)
        self.check(lines + '\nnew target.md "Never present." : Spec', 1, 'MISSING-NEW')
        # An allowance is one instance, not an unlimited text whitelist.
        self.write('target.md', 'Keep the rule. Explain the reason. Explain the reason.\n\n## Finish\n')
        self.check(lines, 1, 'ADDED')

    def test_units_are_matched_by_count_and_order(self):
        self.source('Stop. Stop.\n')
        self.write('target.md', 'Stop.\n')
        self.check('copy source.md -> target.md', 1, 'DELETED')
        self.source('Stop.\n')
        self.write('target.md', 'Stop. Stop.\n')
        self.check('copy source.md -> target.md', 1, 'ADDED')
        self.source('## Claim\n\nStop.\n\n## Other\n\nStop.\n')
        self.write('target.md', '## Claim\n\nStop.\n')
        self.check('move source.md#Claim -> target.md#Claim', 1, 'NOT-REMOVED')
        self.write('source.md', '## Other\n\nStop.\n')
        self.check('move source.md#Claim -> target.md#Claim')
        self.source('First keep the rule. Then retain the reason.\n')
        self.write('target.md', 'Then retain the reason. First keep the rule.\n')
        self.check('copy source.md -> target.md', 1, 'OUT-OF-ORDER')
        self.check('copy source.md -> target.md any-order')

    def test_mechanical_rewrites(self):
        src = 'mmw-v2/skills/demo/SKILL.md'
        dst = 'mmw-v2/skills/other/SKILL.md'
        self.write('mmw-v2/skills/demo/references/rule.md', 'Rules.\n')
        self.write('mmw-v2/skills/demo/references/other.md', 'Other.\n')
        self.source('Read `references/rule.md`.\n', src)
        self.write(dst, 'Read [Rule](../demo/references/rule.md).\n')
        self.check(f'copy {src} -> {dst}')
        self.write(dst, "Read the `demo` skill's `references/rule.md`.\n")
        self.check(f'copy {src} -> {dst}')
        for target in ('Read [Rule](../demo/references/other.md).\n',
                       'Read [Rule](../demo/references/missing.md).\n'):
            self.write(dst, target)
            self.check(f'copy {src} -> {dst}', 1, 'CHANGED')
        self.source('Read `missing/rule.md`.\n', src)
        self.write(dst, 'Read `missing/rule.md`.\n')
        self.check(f'copy {src} -> {dst}')  # both unresolved: literal comparison
        self.source('Read `references/rule.md`.\n', src)
        self.write(dst, 'Read [Rule](references/rule.md).\n')
        self.write('mmw-v2/skills/other/references/rule.md', 'Rules.\n')
        self.check(f'copy {src} -> {dst}\nrename path mmw-v2/skills/demo/references/rule.md -> mmw-v2/skills/other/references/rule.md')
        # An entire file relocation carries its own implicit path mapping.
        self.source('Read [Self](SKILL.md).\n', src)
        (self.root / src).unlink()
        self.write(dst, 'Read [Self](SKILL.md).\n')
        self.check(f'move {src} -> {dst}')
        self.source('Run `--preflight` and `dispatch.sh wait`.\n')
        self.write('target.md', 'Run `--claim` and `dispatch.sh result`.\n')
        self.check('copy source.md -> target.md', 1, 'CHANGED')
        rules = ('rename token --preflight -> --claim in target.md\n'
                 'rename text "dispatch.sh wait" -> "dispatch.sh result" in target.md\n')
        self.check(rules + 'copy source.md -> target.md')
        self.check(rules.replace('in target.md', 'in elsewhere/**') + 'copy source.md -> target.md', 1, 'CHANGED')
        self.source('Keep the original rule.\n')
        self.write('target.md', 'Keep the original rule (**principle-verbatim**).\n')
        self.check('copy source.md -> target.md', 1, 'CHANGED')
        self.write('mmw-v2/skills/mmw/principles/principle-verbatim.md', '# Verbatim\n')
        self.check('copy source.md -> target.md')

    def test_whole_file_targets_have_no_prior_text_allowance(self):
        self.write('target.md', 'Existing local advice.\n')
        self.source('Keep the imported rule.\n')
        self.write('target.md', 'Keep the imported rule. Existing local advice.\n')
        self.check('copy source.md -> target.md', 1, 'ADDED')
        self.write('target.md', '## Claim\n\nExisting local advice.\n')
        self.source('Keep the imported rule.\n')
        self.write('target.md', '## Claim\n\nExisting local advice. Keep the imported rule.\n')
        self.check('copy source.md -> target.md#Claim')

    def test_nothing_checked_is_never_a_pass(self):
        self.source('## Claim\n\nKeep the rule.\n')
        self.write('target.md', '## Claim\n\nKeep the rule.\n')
        invalid = [
            'copy source.md#Absent -> target.md',
            'copy source.md -> target.md#Absent',
            'copy source.md -> target.md\nreplace "Absent" -> "Changed" : Spec',
            'copy source.md -> target.md\ndrop source.md "Absent" : Spec',
            'copy source.md -> target.md\nreplace "Keep" -> "Changed"',
            'nonsense source.md -> target.md',
            'new target.md "Sentence." :',
            'copy source.md -> target.md:L1',
        ]
        for lines in invalid:
            with self.subTest(lines=lines):
                self.check(lines, 2)
        self.write('target.md', '## Claim\n\nKeep the rule.\n\n## Claim\n\nKeep the rule.\n')
        self.check('copy source.md -> target.md#Claim', 2)
        self.source('Keep the rule. Keep the rule.\n')
        self.check('copy source.md -> target.md\nreplace "Keep" -> "Retain" : Spec', 2, 'STALE')
        self.check('copy source.md -> target.md\ndrop source.md "Keep" : Spec', 2, 'STALE')
        self.base = 'no-such-commit'
        self.check('copy source.md -> target.md', 2)
        self.base = self.git('rev-parse', 'HEAD')
        self.write('empty.md', '')
        self.base = self.commit()
        self.check('copy empty.md -> empty.md', 1, 'VERBATIM FAIL checked nothing')
        self.check('rename text Old -> New', 1, 'VERBATIM FAIL checked nothing')
        self.check('from HEAD', 2)

    def test_a_failure_leads_with_summary_next_and_why(self):
        self.source('Preserve the original wording.\n')
        self.write('target.md', 'Preserve the improved wording.\n')
        output = self.check('copy source.md -> target.md', 1, 'CHANGED')
        self.assertEqual([line.split()[0] for line in output.splitlines()[:3]],
                         ['VERBATIM', 'Next:', 'Why:'])
        self.write('target.md', 'Preserve the original wording.\n\n' +
                   '\n\n'.join(f'Added advice number {i}.' for i in range(45)) + '\n')
        output = self.check('copy source.md -> target.md', 1, 'ADDED')
        self.assertEqual(sum(': ADDED' in line for line in output.splitlines()), 40)
        self.assertIn('45', output.splitlines()[-1])
        self.assertIn('--all', output.splitlines()[-1])
        output = self.check('copy source.md -> target.md', 1, 'ADDED', all_findings=True)
        self.assertEqual(sum(': ADDED' in line for line in output.splitlines()), 45)

    @staticmethod
    def mutations(text, mode):
        """Pick only sentence bodies, never titles, list markers or block starts."""
        result = []
        lines = text.splitlines(keepends=True)
        frontmatter = bool(lines and lines[0].strip() == '---')
        fenced = False
        for index, line in enumerate(lines):
            if frontmatter:
                if index and line.strip() == '---':
                    frontmatter = False
                continue
            body = line.strip()
            if body.startswith('```'):
                fenced = not fenced
                continue
            if fenced:
                continue
            if not body or body.startswith(('#', '|', '```', '**')):
                continue
            words = list(re.finditer(r'\b[A-Za-z]+\b', line))
            if len(words) < 5:
                continue
            word = words[2]
            start, end = word.span()
            changed = None
            if mode == 0:
                changed = line[:start] + 'differentword' + line[end:]
            elif mode == 1:
                changed = line[:start] + line[end:]
            elif mode == 2:
                changed = line[:start] + 'not ' + line[start:]
            elif mode == 3:
                number = re.search(r'(?<=\s)\d+', line)
                if number and number.start() > words[0].end():
                    changed = line[:number.start()] + str(int(number.group()) + 1) + line[number.end():]
            elif mode == 4:
                code = re.search(r'`([^`]+)`', line)
                if code:
                    changed = line[:code.start(1)] + 'changed-code' + line[code.end(1):]
            elif mode in (5, 6):
                # These fixture sentences have a literal period + uppercase boundary.
                prefix = re.match(r'^\s*(?:(?:[-*+]|\d+[.)])\s+)?', line).group()
                pieces = re.split(r'(?<=[.?!])\s+(?=[A-Z])', line[len(prefix):].rstrip('\n'))
                if len(pieces) > 1 and re.match(r'^[A-Z][a-z]', pieces[0]) and all(p.endswith(('.', '!', '?')) for p in pieces):
                    changed = prefix + (' '.join(pieces[:1] + pieces[2:]) if mode == 5 else
                               ' '.join([pieces[1], pieces[0], *pieces[2:]])) + '\n'
            elif mode == 7:
                changed = line[:start] + '**' + line[start:end] + '**' + line[end:]
            elif mode == 8:
                punctuation = re.search(r'[,;.!?]', line[word.end():])
                if punctuation:
                    pos = word.end() + punctuation.start()
                    changed = line[:pos] + ':' + line[pos+1:]
            if changed and changed != line:
                copy = lines.copy()
                copy[index] = changed
                result.append((''.join(copy), index + 1))
        return result

    def test_every_seeded_mutation_is_reported(self):
        fixtures = Path(__file__).parent / 'fixtures' / 'verbatim'
        texts = [(fixtures / f'{name}.md').read_text() for name in ('advisor', 'retro')]
        randomizer = random.Random(600)
        for text in texts:
            self.source(text)
            self.write('target.md', text)
            self.check('copy source.md -> target.md')
        for iteration in range(30):
            mode = iteration % 9
            pool = [(text, change, row) for text in texts
                    for change, row in self.mutations(text, mode)]
            self.assertTrue(pool, f'no real-skill candidate for mutation {mode}')
            text, change, row = randomizer.choice(pool)
            with self.subTest(real_skill_iteration=iteration, mutation=mode):
                self.source(text)
                self.write('target.md', change)
                output = self.check('copy source.md -> target.md', 1)
                self.assertRegex(output, rf'(?:source|target)\.md:{row}:')
        source = (fixtures / 'reflow-source.md').read_text()
        target = (fixtures / 'reflow-target.md').read_text()
        self.source(source)
        self.write('source.md', '')
        self.write('target.md', target)
        self.check('move source.md -> target.md')
        for iteration in range(20):
            mode = iteration % 9
            pool = self.mutations(target, mode)
            self.assertTrue(pool, f'no reflow candidate for mutation {mode}')
            change, row = randomizer.choice(pool)
            with self.subTest(reflow_iteration=iteration, mutation=mode):
                self.write('target.md', change)
                output = self.check('move source.md -> target.md', 1)
                if mode not in (5, 6):
                    self.assertIn(f'target.md:{row}:', output)
                else:
                    self.assertRegex(output, r'(?:DELETED|OUT-OF-ORDER|CHANGED)')

    def test_markdown_units_and_locations(self):
        original = ('---\nname: fixture\ndescription: "Keep the rule. Read the reason."\n---\n'
                    '\n## Start\n\n> Keep the rule. Read the reason.\n\n'
                    '| Rule | Why |\n| --- | --- |\n| Keep it. | Avoid loss. |\n\n'
                    '<!-- Keep this entire comment. -->\n<issue-template>\n\n'
                    '```sh\nprintf "original"\n```\n')
        self.source(original)
        self.write('target.md', original.replace('description: "Keep the rule. Read the reason."',
                                                'description: >-\n  Keep the rule. Read the reason.'))
        self.check('copy source.md -> target.md')
        # Scope reads a YAML key, a line range, a heading or a labelled paragraph.
        self.write('target.md', 'Keep the rule. Read the reason.\n')
        self.check('copy source.md@description -> target.md')
        self.write('target.md', '1. **Start.** Keep the rule. Read the reason.\n')
        self.check('copy source.md:L6-L8 -> target.md')
        self.source('**Where you are.** Keep the rule.\n\nRead the reason.\n\n**Other.** Not carried.\n')
        self.write('target.md', '**Where you are.** Keep the rule. Read the reason.\n')
        self.check('copy "source.md#Where you are" -> "target.md#Where you are"')
        self.check('copy source.md#Where you are -> target.md#Where you are')
        self.source("## Reader's decision\n\nKeep the rule.\n")
        self.write('target.md', "## Reader's decision\n\nKeep the rule. Record this : reason.\n")
        self.check("copy source.md#Reader's decision -> target.md#Reader's decision\n"
                   "new target.md#Reader's decision \"Record this : reason.\" : Owner's decision")
        self.source('## Start\n\nKeep the original rule.\n')
        pinned = self.base
        self.source('Never use this replacement source.\n')
        self.write('target.md', '## Start\n\nKeep the original rule.\n')
        self.check(f'copy {pinned}:source.md -> target.md')

    def test_code_and_markup_are_not_silently_rewritten(self):
        self.source('```sh\nrun --preflight\n```\n\nKeep the exact wording.\n')
        self.write('target.md', '```sh\nrun --claim\n```\n\nKeep the exact wording.\n')
        self.check('rename token --preflight -> --claim\ncopy source.md -> target.md')
        self.write('target.md', '```sh\n run --claim\n```\n\nKeep the exact wording.\n')
        self.check('rename token --preflight -> --claim\ncopy source.md -> target.md', 1, 'CHANGED')
        for text in ('Keep the **exact** wording.', 'keep the exact wording.',
                     'Keep the exact wording!', 'Keep the exact original wording.'):
            self.source('Keep the exact wording.\n')
            self.write('target.md', text + '\n')
            self.check('copy source.md -> target.md', 1, 'CHANGED')

    def test_replacements_and_scoped_renames(self):
        self.source('Keep the original\nwording.\n')
        self.write('target.md', 'Keep the approved wording.\n')
        self.check('copy source.md -> target.md\nreplace "original wording" -> "approved wording" : Spec')
        self.source('Keep the rule. Read the reason.\n')
        self.write('target.md', 'Keep the rule. Retain the reason.\n')
        self.check('copy source.md -> target.md\nreplace "rule. Read" -> "rule. Retain" : Spec')
        self.source('## Claim\n\nKeep the rule.\n')
        self.write('target.md', '## Begin\n\nRetain the rule.\n')
        self.check('copy source.md -> target.md\nreplace "Claim Keep" -> "Begin Retain" : Spec')
        self.source('Use `old` and `older` and `old-name`. Say old in prose.\n')
        self.write('target.md', 'Use `new` and `older` and `old-name`. Say old in prose.\n')
        self.check('rename token old -> new\ncopy source.md -> target.md')
        self.write('target.md', 'Use `new` and `newer` and `old-name`. Say new in prose.\n')
        self.check('rename token old -> new\ncopy source.md -> target.md', 1, 'CHANGED')
        self.source('Run `dispatch.sh wait`.\n')
        self.write('target.md', 'Run `dispatch.sh result`.\n')
        self.check('rename text dispatch.sh wait -> dispatch.sh result\ncopy source.md -> target.md')
        src = 'mmw-v2/skills/demo/SKILL.md'
        dst = 'mmw-v2/skills/demo/COPY.md'
        self.write('mmw-v2/skills/demo/references/sub-issues.md', 'Rules.\n')
        self.source('Read `references/sub-issues.md`.\n', src)
        self.write('mmw-v2/skills/demo/references/child-issues.md', 'Rules.\n')
        self.write(dst, 'Read `references/child-issues.md`.\n')
        self.check('rename token sub-issues.md -> child-issues.md\n'
                   'rename path mmw-v2/skills/demo/references/sub-issues.md -> mmw-v2/skills/demo/references/child-issues.md\n'
                   f'copy {src} -> {dst}')

    def test_scoped_targets_share_instances_and_keep_existing_counts(self):
        self.source('## Claim\n\nKeep the rule.\n\n## Finish\n\nRead the reason.\n')
        self.write('target.md', '## Claim\n\nKeep the rule.\n\n## Finish\n\nRead the reason.\n')
        # Two transfers to the same containing section account for its union.
        self.check('copy source.md#Claim -> target.md\ncopy source.md#Finish -> target.md')
        # One target instance cannot satisfy two transfer entries.
        self.check('copy source.md#Claim -> target.md#Claim\n'
                   'copy source.md#Claim -> target.md#Claim', 1, 'DELETED')
        self.write('target.md', '## Claim\n\nKeep the rule.\n')
        self.source('Read the reason.\n')
        self.write('target.md', '## Claim\n\nKeep the rule. Keep the rule. Read the reason.\n')
        self.check('copy source.md -> target.md#Claim', 1, 'ADDED')

    def test_missing_or_malformed_import_registry(self):
        self.source('Keep the rule.\n')
        self.write('target.md', 'Keep the rule.\n')
        self.check('copy source.md -> target.md')
        self.write('mmw-v2/skills/mmw/imports.tsv',
                   'type\tlocal\tsource\tcommit\tmechanical\tjudgment\tbatch\n'
                   '\n# note\nplaybook\n')
        self.check('copy source.md -> target.md', 2, 'imports.tsv:4:')
        self.write('mmw-v2/skills/mmw/imports.tsv',
                   'type\tlocal\tsource\tcommit\tmechanical\tjudgment\tbatch\n'
                   'playbook\tmmw-v2/skills/mmw/playbooks/imported.md\tx\tsha\t\tstructure-exempt\tB1\n')
        self.check('copy source.md -> target.md')
