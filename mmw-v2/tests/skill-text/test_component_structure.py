"""Exercise the structure lint CLI against disposable component trees."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'lib' / 'check_component_structure.py'
FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'structure'
# The acceptance contract, #602 What to build 2, fixes these 25 public rule ids.
RULE_IDS = {
    'mode-name', 'mode-sections', 'mode-imported-triggers', 'mode-principle-line',
    'mode-route-line', 'playbook-title', 'playbook-owner-line', 'playbook-steps',
    'playbook-where-table', 'step-title', 'step-done-when', 'step-names-component',
    'playbook-reply', 'principle-frontmatter', 'principle-applies', 'principle-body',
    'principle-direction', 'capability-next-step', 'capability-playbook-name',
    'numbered-cross-reference', 'host-name', 'no-dash', 'description-trigger',
    'description-content', 'skill-name',
}


class ComponentStructure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mmw-structure-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write('mmw-v2/skills.txt', 'self/example\nengineering/implement\nself/mmw\n')

    def write(self, path, text):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding='utf-8')

    def rule_ids(self, output):
        return re.findall(r'^.*\.md:\d+: ([\w-]+) ', output, re.M)

    def run_check(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), *args],
                              capture_output=True, text=True)

    def fixture(self, name, path):
        self.write(path, (FIXTURES / name).read_text(encoding='utf-8'))
        return path

    def test_well_formed_components_pass(self):
        samples = {
            'mode': 'mmw-v2/skills/mmw/SKILL.md',
            'short-playbook': 'mmw-v2/skills/mmw/playbooks/plan-a-change.md',
            'long-playbook': '.mmw/playbooks/long.md',
            'role-playbook': 'mmw-v2/skills/mmw/playbooks/work-a-ticket.md',
            'principle': 'mmw-v2/skills/mmw/principles/principle-evidence.md',
            'principle-no-why': 'mmw-v2/skills/mmw/principles/principle-other.md',
            'capability': 'mmw-v2/skills/example/SKILL.md',
        }
        for name, path in samples.items():
            text = (FIXTURES / (name + '.md')).read_text(encoding='utf-8')
            if name == 'principle-no-why':
                text = text.replace('name: principle-evidence', 'name: principle-other')
            self.write(path, text)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('STRUCTURE OK 7 files', result.stdout)

    def test_each_rule_fails_its_own_fixture(self):
        playbook = 'mmw-v2/skills/mmw/playbooks/plan-a-change.md'
        self.fixture('short-playbook.md', playbook)
        fixtures = sorted(FIXTURES.glob('*.bad.md'))
        self.assertEqual({f.name.removesuffix('.bad.md') for f in fixtures}, RULE_IDS)
        for fixture in fixtures:
            rule = fixture.name.removesuffix('.bad.md')
            if rule.startswith('mode-'):
                path = 'mmw-v2/skills/mmw/SKILL.md'
            elif rule.startswith(('playbook-', 'step-')):
                path = playbook
            elif rule.startswith('principle-') or rule == 'no-dash':
                path = 'mmw-v2/skills/mmw/principles/principle-evidence.md'
            else:
                path = 'mmw-v2/skills/example/SKILL.md'
            with self.subTest(rule=rule):
                self.fixture(fixture.name, path)
                result = self.run_check('--no-exceptions', path)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 1, output)
                self.assertEqual(self.rule_ids(output), [rule], output)
            self.fixture('short-playbook.md', playbook)

    def test_imported_playbook_keeps_its_own_steps(self):
        path = 'mmw-v2/skills/mmw/playbooks/imported.md'
        self.write(path, '### Imported\n\n1. Read rule 3 of another.md using Codex.\n\n**Reply:** evidence.\n')
        self.write('mmw-v2/skills/mmw/imports.tsv',
                   'type\tpath\tsource\tcommit\tmechanical\tjudgement\tbatch\n'
                   f'playbook\t{path}\tupstream.md\tabc123\t\t\tB1\n')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for text, rule in (('Imported\n\n**Reply:** evidence.\n', 'playbook-title'),
                           ('### Imported\n\n1. Inspect evidence.\n', 'playbook-reply')):
            self.write(path, text)
            result = self.run_check(path)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(self.rule_ids(result.stdout), [rule], result.stdout + result.stderr)
        self.write(path, 'An imported standard without Reply or H3.\n')
        self.write('mmw-v2/skills/mmw/imports.tsv',
                   'type\tpath\tsource\tcommit\tmechanical\tjudgement\tbatch\n'
                   f'playbook\t{path}\tupstream.md\tabc123\t\tstructure-exempt\tB1\n')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_where_you_are_fact_table(self):
        path = 'mmw-v2/skills/mmw/playbooks/plan-a-change.md'
        original = (FIXTURES / 'long-playbook.md').read_text(encoding='utf-8')
        mutations = [
            original.replace('Take the first line whose fact holds. ', ''),
            original.replace('→ **Judge the result**.', '→ **Unknown**.'),
            original.replace('- Anything else → **Read the evidence**.\n', ''),
            original.replace('- Anything else → **Read the evidence**.', '- Anything else → **Judge the result**.'),
        ]
        for text in mutations:
            with self.subTest(text=text):
                self.write(path, text)
                result = self.run_check(path)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(' playbook-where-table ', result.stdout)
        for role in ('run-a-night', 'land-one-ticket', 'work-a-ticket', 'review-a-ticket', 'research-a-question'):
            path = f'mmw-v2/skills/mmw/playbooks/{role}.md'
            self.write(path, mutations[0])
            result = self.run_check(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_numbered_rule_references(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        original = (FIXTURES / 'capability.md').read_text(encoding='utf-8')
        for prose in ('Read the `implement` skill\'s rule 3.',
                      'Follow rules 3 and 4 of the `implement` skill.',
                      'Read `other.md` rule 3.',
                      'Read `other.md` step 3.',
                      'Read `other.md` `## 5. Evidence`.'):
            with self.subTest(prose=prose):
                self.write(path, original + '\n' + prose + '\n')
                result = self.run_check(path)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(' numbered-cross-reference ', result.stdout)
        for prose in ('Read `shared.md` rule 3.', 'Read rule 3.', 'Read steps from step 2.',
                      'Follow rules 3 and 4.', 'Read the `example` skill\'s rule 3.',
                      'After step 2 write `result.md`.',
                      'Reporting in rules 3 to 5 invokes the `implement` skill.',
                      'Run `python3 scripts/check.py finalize` with the file step 1 saved.',
                      'Done when `bash scripts/check.sh close` succeeded for every product on the step 2 list.',
                      'Leave its workspace for implement; step 4 continues the batch.',
                      'The package was pulled and `pull-report.md` says `new controls`: lint as step 7 says.',
                      'Use `pages.<page>.viewports` (write that entry now; step 2 fills it).',
                      'A new page gets that size (step 2 fills it), so `other.md` receives the answer.'):
            with self.subTest(prose=prose):
                self.write(path, original + '\n' + prose + '\n')
                result = self.run_check(path)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_routing_patterns_and_plain_playbook_display_names(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        self.fixture('short-playbook.md', 'mmw-v2/skills/mmw/playbooks/plan-a-change.md')
        original = (FIXTURES / 'capability.md').read_text(encoding='utf-8')
        for prose in ('Return to the implement skill.', 'Hand it over to the `implement` skill.',
                      'Hand on to the implement skill.', 'This goes through the implement skill first.',
                      'These are steps of the implement skill.', 'The next step uses the implement skill.',
                      'Return to `implement`.', 'Hand on to implement.'):
            with self.subTest(prose=prose):
                self.write(path, original + '\n' + prose + '\n')
                result = self.run_check(path)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(' capability-next-step ', result.stdout)
        self.write(path, original + '\nRun Plan a change.\n')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(' capability-playbook-name ', result.stdout)

    def test_judgement_after_the_step_title(self):
        path = 'mmw-v2/skills/mmw/playbooks/plan-a-change.md'
        original = (FIXTURES / 'short-playbook.md').read_text(encoding='utf-8')
        self.write(path, original)
        self.assertEqual(self.run_check(path).returncode, 0)
        for replacement in ('', 'Later, (judgement) '):
            self.write(path, original.replace('(judgement) ', replacement))
            result = self.run_check(path)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(' step-names-component ', result.stdout)

    def _playbook_naming_only(self, step):
        # `.mmw` matches the skill name only when skills.txt lists mmw.
        self.write('mmw-v2/skills.txt', 'self/mmw\n')
        path = 'mmw-v2/skills/mmw/playbooks/plan-a-change.md'
        self.write(path, (
            '### Record the answer\n'
            '\n'
            f'1. **Do the step.** {step}\n'
            '   Done when the step is recorded.\n'
            '\n'
            '**Reply:** the recorded step.\n'
        ))
        return path

    def test_step_naming_only_a_dot_mmw_path_names_no_component(self):
        path = self._playbook_naming_only('Write the answer to `.mmw/stories/a.md`.')
        result = self.run_check(path)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn(' step-names-component ', result.stdout)

    def test_step_naming_only_a_path_through_references_names_no_component(self):
        path = self._playbook_naming_only('Open docs/foo/references/x.md and decide.')
        result = self.run_check(path)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn(' step-names-component ', result.stdout)

    def test_step_naming_the_skill_by_name_still_names_a_component(self):
        path = self._playbook_naming_only("Run the `mmw` skill's check.")
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_step_opening_a_references_path_still_names_a_component(self):
        path = self._playbook_naming_only('Read `references/notes.md` first.')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_structure_exceptions(self):
        path = 'mmw-v2/skills/example/references/notes.md'
        bad = 'Use Codex for the task.\n'
        self.write(path, bad)
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        table = 'mmw-v2/tests/lib/structure-exceptions.tsv'
        header = 'path\trule\texcerpt\tuntil\treason\n'
        row = f'{path}\thost-name\tUse Codex for the task.\tB2\tR18 B2\n'
        self.write(table, header + row)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('1 exceptions in use, 0 stale', result.stdout)
        result = self.run_check('--no-exceptions')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.write(path, bad + bad)
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count(' host-name '), 1)
        self.write(table, header + row + row)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_check('--batch', 'B1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for batch in ('B2', 'B3', 'B10'):
            result = self.run_check('--batch', batch)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        new = 'mmw-v2/skills/example/references/renamed.md'
        intermediate = 'mmw-v2/skills/example/references/middle.md'
        self.write('docs/specs/z-first/renames.tsv', f'kind\told\tnew\npath\t{path}\t{intermediate}\n')
        self.write('docs/specs/a-second/renames.tsv', f'kind\told\tnew\npath\t{intermediate}\t{new}\n')
        self.write(path, bad + bad)
        self.write(new, 'Inspect the result.\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (self.root / path).unlink()
        self.write(intermediate, bad + bad)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        (self.root / intermediate).unlink()
        self.write(new, bad + bad)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.write(new, 'Inspect the result.\n')
        result = self.run_check('--batch', 'B2')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count('WARN stale exception'), 2)
        self.write(new, bad)
        self.write(table, header + row.replace('\tB2\tR18 B2', '\tpermanent\tA literal button label'))
        result = self.run_check('--batch', 'B10')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('1 exceptions in use, 0 stale', result.stdout)
        self.write(table, header + row.replace('\tB2\tR18 B2', '\tpermanent\t'))
        result = self.run_check()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_exception_writer_and_long_line_excerpts(self):
        path = 'mmw-v2/skills/example/references/notes.md'
        line = 'Inspect the criterion ' * 6 + 'using Codex for the task.'
        self.write(path, line + '\n')
        result = self.run_check('--write-exceptions')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        table = (self.root / 'mmw-v2/tests/lib/structure-exceptions.tsv').read_text(encoding='utf-8')
        self.assertIn('Codex', table)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exception_writer_uses_the_moving_files_batch_for_unlisted_findings(self):
        skill = 'mmw-v2/skills/design-pages/SKILL.md'
        text = (FIXTURES / 'capability.md').read_text(encoding='utf-8')
        self.write(skill, text.replace('name: example', 'name: design-pages') + '\nRead `UI.md` step 6.\n')
        references = [f'mmw-v2/skills/design-pages/references/{name}.md'
                      for name in ('design-system', 'pull')]
        for path in references:
            self.write(path, 'Read `other.md` rule 1.\n')
        result = self.run_check('--write-exceptions')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('3 exceptions in use, 0 stale', result.stdout)
        for batch, expected in (('B1', [skill]), ('B2', [skill, *references])):
            result = self.run_check('--batch', batch)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            found = re.findall(r'^(.*\.md):\d+: numbered-cross-reference ', result.stdout, re.M)
            self.assertEqual(sorted(found), sorted(expected), result.stdout)

    def test_component_scope_and_fenced_examples(self):
        path = 'mmw-v2/skills/example/references/notes.md'
        self.write(path, 'Use `Codex` or [a runner](https://example.test/Orca).\n'
                         '```md\n## Next\nUse Codex.\n```\n')
        self.write('mmw-v2/skills/mmw/references/names.md', '```md\nUse Codex — here.\n```\n')
        for ignored in ('.mmw/playbooks/INDEX.md', '.mmw/playbooks/nested/notes.md',
                        'mmw-v2/skills/mmw/playbooks/nested/notes.md',
                        'mmw-v2/upstream-pstack/skills/example/SKILL.md'):
            self.write(ignored, 'Use Codex for the task.\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('STRUCTURE OK 2 files', result.stdout)

    def test_finding_excerpt_starts_at_a_wrapped_match(self):
        path = 'mmw-v2/skills/example/references/notes.md'
        self.write(path, 'Inspect the criterion ' * 6 + 'return to the\n   `implement` skill.\n')
        result = self.run_check('--no-exceptions', path)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(path + ':1: capability-next-step ', result.stdout)
        self.assertIn('| return to the', result.stdout)

    def test_shared_lints_run_the_structure_lint(self):
        lib = self.root / 'mmw-v2/tests/lib'
        lib.mkdir(parents=True)
        for file in SCRIPT.parent.iterdir():
            if file.suffix in ('.py', '.sh'):
                shutil.copy(file, lib / file.name)
        self.write('mmw-v2/skills.txt', 'self/example\n')
        self.fixture('capability.md', 'mmw-v2/skills/example/SKILL.md')
        self.write('mmw-v2/skills/example/references/notes.md', 'Use Codex for the task.\n')
        result = subprocess.run(['bash', str(lib / 'run_shared_lints.sh')], cwd=self.root,
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(' host-name ', result.stdout + result.stderr)

    def test_structure_checking_nothing_is_never_a_pass(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn('STRUCTURE OK', result.stdout)
        self.write('mmw-v2/upstream/skills/example/SKILL.md', '# Upstream\n')
        result = self.run_check('mmw-v2/upstream/skills/example/SKILL.md')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('0 findings in 0 files', result.stdout)
        self.assertNotIn('STRUCTURE OK', result.stdout)
        (self.root / 'mmw-v2/skills.txt').unlink()
        result = self.run_check()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn('STRUCTURE OK', result.stdout)

    def test_descriptions_allow_identity_and_heading_closing_marks(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        text = (FIXTURES / 'capability.md').read_text(encoding='utf-8')
        text = text.replace('Use when evidence needs inspection.',
                            'Inspect evidence for one criterion. Use when evidence needs inspection. Not for planning.')
        self.write(path, text)
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.write(path, text + '\n## Next ##\n')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(' capability-next-step ', result.stdout)

    def test_mode_direct_capability_lines_are_not_route_lines(self):
        path = 'mmw-v2/skills/mmw/SKILL.md'
        mode = (FIXTURES / 'mode.md').read_text(encoding='utf-8')
        direct = mode + '- A diagram → the `diagram-design` skill.\n'
        self.write(path, direct)
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        routed = direct + '- **Ship.** Build an installer.\n'
        self.write(path, routed)
        result = self.run_check(path)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertEqual(self.rule_ids(output), ['mode-route-line'], output)

        plain = direct + '* A diagram → the `diagram-design` skill.\n'
        self.write(path, plain)
        result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for marker in ('*', '+'):
            starred = direct + f'{marker} **Bug fix.** Fix it. `playbooks/bug.md`.\n'
            self.write(path, starred)
            result = self.run_check(path)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1, marker + '\n' + output)
            self.assertEqual(self.rule_ids(output), ['mode-route-line'], output)

    def test_description_skill_names_are_matched_as_written_and_not_inside_paths(self):
        self.write('mmw-v2/skills.txt', 'self/mmw\n')
        path = 'mmw-v2/skills/example/SKILL.md'
        body = '# Example\n\nInspect the criterion and record the result.\n'

        def described(description):
            self.write(path, f'---\nname: example\ndescription: {description}\n---\n{body}')
            return self.run_check(path)

        for description in (
            'Use when one MMW night is done.',
            'Use when filling `.mmw/target.json`.',
        ):
            result = described(description)
            self.assertEqual(result.returncode, 0, description + '\n' + result.stdout + result.stderr)
        result = described('Use when the `mmw` skill applies.')
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertEqual(self.rule_ids(output), ['description-content'], output)

    def test_unchecked_frontmatter_names_its_file_and_preserves_the_repair_path(self):
        path = 'mmw-v2/skills/example/SKILL.md'
        self.write(path, '---\nname: example\ndescription: unquoted: colon\n---\n')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(path, result.stderr)
        self.fixture('capability.md', path)
        self.write('mmw-v2/skills/mmw/imports.tsv', 'broken\n')
        result = self.run_check(path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        next_line = next(line for line in result.stderr.splitlines() if line.startswith('Next:'))
        self.assertIn('imports.tsv:1', next_line)
