import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from _load import load

vt = load()
SUMMARIES = vt.HERE / 'runner-summaries.json'
FIXTURES = Path(__file__).resolve().parent / 'fixtures/runner-expect'
LABELS = ['mmw:ticket', 'ready-for-agent', 'junior-worker']


def summaries():
    return json.loads(SUMMARIES.read_text())


def expect_matches(expect, output):
    script = r'''const {expect, output} = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const [, source, flags] = expect.match(/^\/([\s\S]*)\/([a-z]*)$/);
console.log(JSON.stringify(new RegExp(source, flags).test(output)));'''
    result = subprocess.run(['node', '-e', script], text=True, capture_output=True,
                            check=True, input=json.dumps({'expect': expect, 'output': output}))
    return json.loads(result.stdout)


def assert_wrong_summary(case, runner, expect, error):
    named = [sample for sample in summaries()[runner]['samples'] if sample['summary'] in error]
    case.assertTrue(named, error)
    for sample in named:
        case.assertNotEqual(expect_matches(expect, sample['output']), sample['success'], error)


def ticket(check, expect):
    command = ('  CHECK:\n  ```sh\n' + '\n'.join('  ' + line for line in check.splitlines())
               + '\n  ```' if '\n' in check else '  CHECK: ' + check)
    return ('## Parent\n\n#555, Implementation Decisions section 1\n\n'
            '## What to build\n\n1. Import the rows. AC1.\n\n## Acceptance criteria\n\n'
            '- [ ] AC1: the selected behaviour passes\n'
            f'{command}\n  EXPECT: {expect}\n  EVIDENCE: pending\n')


def lint(body, draft=False):
    with mock.patch.object(vt, 'fetch_body', side_effect=lambda n: body if n == 77 else
                           '## Implementation Decisions\n\n### 1. Runners\n\nRules\n'), \
         mock.patch.object(vt, 'fetch_ticket', return_value={
             'labels': [{'name': name} for name in LABELS]}), \
         mock.patch.object(vt, 'fetch_parent', return_value=None), \
         mock.patch.object(vt, 'fetch_sub_issues', return_value=[77]), \
         mock.patch.object(vt, 'fetch_blocked_by', return_value=[]), \
         redirect_stdout(io.StringIO()) as out:
        code = (vt.lint_criteria(0, body, LABELS, spec=555, name='T1') if draft
                else vt.main(['77', '--lint']))
    return code, out.getvalue()


class TestRunnerExpect(unittest.TestCase):
    def test_vitest_standard_needs_a_passed_test(self):
        expect = summaries()['vitest']['expect']
        for output, success in [('Tests  1 passed | 5 skipped (6)', True),
                                ('Tests  1 passed | 1 todo (2)', True),
                                ('Tests  5 skipped (5)', False),
                                ('Tests  1 todo (1)', False),
                                ('Tests  0 passed (0)', False),
                                ('Tests  1 failed | 1 passed (2)', False)]:
            with self.subTest(output=output):
                self.assertEqual(expect_matches(expect, output), success)

    def test_runner_summaries_standards_separate_real_success_and_failure(self):
        data = summaries()
        rows = [{'runner': name, 'expect': runner['expect'], **sample}
                for name, runner in data.items() for sample in runner['samples']]
        script = r'''
const rows = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
console.log(JSON.stringify(rows.map(row => {
  const [, source, flags] = row.expect.match(/^\/([\s\S]*)\/([a-z]*)$/);
  return [row.summary + '\n', row.output].map(text => new RegExp(source, flags).test(text));
})));
'''
        run = subprocess.run(['node', '-e', script], input=json.dumps(rows),
                             text=True, capture_output=True, check=True)
        self.assertTrue(rows)
        for row, matches in zip(rows, json.loads(run.stdout)):
            with self.subTest(runner=row['runner'], summary=row['summary']):
                self.assertEqual(matches, [row['success'], row['success']])

    def test_lint_runner_expect_rejects_wrong_success_and_failure_patterns(self):
        for runner, expect in [('pytest', r'/^=+ .*passed.*=+$/m'),
                               ('pytest', r'/^\d+ passed in [0-9.]+s$/m'),
                               ('pytest', r'/passed/'),
                               ('pytest', r'/3 passed/'),
                               ('vitest', r'/Tests\s+1 passed \(1\)/'),
                               ('vitest', r'/^[ \t]*Tests[ \t]+\d+ (?:passed|skipped|todo)(?:[ \t]+\|[ \t]+\d+ (?:passed|skipped|todo))*[ \t]+\(\d+\)[ \t]*$/m'),
                               ('vitest', r'/passed/'),
                               ('vitest', '/MY-MARKER/')]:
            for draft in (False, True):
                with self.subTest(runner=runner, expect=expect, draft=draft):
                    code, output = lint(ticket(f'{runner} run && echo MY-MARKER', expect), draft)
                    self.assertEqual(code, 1, output)
                    error = next((line for line in output.splitlines()
                                  if '[runner-expect]' in line), '')
                    self.assertIn('ERROR', error)
                    self.assertIn('AC1', error)
                    self.assertIn(summaries()[runner]['expect'], error)
                    assert_wrong_summary(self, runner, expect, error)

    def test_lint_runner_expect_accepts_standards_on_drafts_and_published_tickets(self):
        for runner, data in summaries().items():
            for draft in (False, True):
                with self.subTest(runner=runner, draft=draft):
                    code, output = lint(ticket(f'{runner} run', data['expect']), draft)
                    self.assertEqual(code, 0, output)
                    self.assertNotIn('[runner-expect]', output)

    def test_lint_runner_expect_requires_standard_even_for_equivalent_pattern(self):
        for runner, data in summaries().items():
            standard = data['expect']
            source, flags = standard[1:].rsplit('/', 1)
            equivalent = '/(?:' + source + ')/' + flags
            with self.subTest(runner=runner):
                code, output = lint(ticket(f'{runner} run', equivalent))
                self.assertEqual(code, 1, output)
                self.assertIn('[runner-expect]', output)
                self.assertIn(standard, output)

    def test_lint_runner_expect_reports_output_using_javascript_regex_flags(self):
        for expect in [summaries()['pytest']['expect'].removesuffix('m'),
                       r'/(?<count>\d+) passed/u']:
            with self.subTest(expect=expect):
                code, output = lint(ticket('uv run pytest -q', expect))
                self.assertEqual(code, 1, output)
                error = next(line for line in output.splitlines() if '[runner-expect]' in line)
                assert_wrong_summary(self, 'pytest', expect, error)

    def test_lint_runner_expect_checks_commands_behind_prefixes_and_in_each_stage(self):
        for check in ['pytest -q', 'uv run pytest -q', 'python -m pytest',
                      'uv run python3 -m pytest', 'pnpm vitest run', 'npx vitest run',
                      'pnpm exec vitest run', 'echo ready && pytest -q | cat',
                      'echo ready; npx vitest run', 'echo "x;vitest"\npytest -q']:
            for draft in (False, True):
                with self.subTest(check=check, draft=draft):
                    code, output = lint(ticket(check, '/OK/'), draft)
                    self.assertEqual(code, 1, output)
                    self.assertIn('[runner-expect]', output)

    def test_lint_runner_expect_ignores_runner_names_used_only_as_arguments(self):
        for check in ['grep -q vitest package.json && echo OK', 'pip install pytest',
                      'echo "pytest; vitest"', 'python report.py --runner pytest',
                      'echo "x|vitest" | grep pytest', 'cat pytest-results.txt',
                      'uv run report.py pytest', 'pnpm exec report vitest',
                      'echo OK # pytest; vitest', 'echo OK # ;pytest\necho ready']:
            for draft in (False, True):
                with self.subTest(check=check, draft=draft):
                    code, output = lint(ticket(check, '/OK/'), draft)
                    self.assertEqual(code, 0, output)
                    self.assertNotIn('[runner-expect]', output)

    def test_lint_runner_expect_requires_separate_criteria_for_different_runners(self):
        for check in ['pytest a && pnpm vitest run', 'uv run pytest | npx vitest run',
                      'python -m pytest\npnpm exec vitest run']:
            with self.subTest(check=check):
                code, output = lint(ticket(check, summaries()['pytest']['expect']))
                self.assertEqual(code, 1, output)
                error = next(line for line in output.splitlines() if '[runner-expect]' in line)
                self.assertIn('one criterion per runner', error)
                self.assertIn(summaries()['pytest']['expect'], error)
                self.assertIn(summaries()['vitest']['expect'], error)

    def test_lint_runner_expect_leaves_other_commands_unchanged(self):
        code, output = lint(ticket('node scripts/import.mjs', '/^6 rows$/m'))
        self.assertEqual(code, 0, output)
        self.assertNotIn('[runner-expect]', output)

    def test_replay_runner_expect_reports_original_pytest_patterns_and_wrong_lines(self):
        cases = [(1349, 'AC1', 24, r'/=+ \d+ passed(, \d+ deselected)? in [0-9.]+s =+/',
                  'test_cases.py::test_pass'),
                 (1125, 'AC9', 9, r'/^\d+ passed(, \d+ warnings?)? in [0-9.]+s$/m',
                  'test_cases.py::test_long')]
        data = summaries()['pytest']
        for number, gate_id, count, original, target in cases:
            body = (FIXTURES / f'agentflow-{number}.md').read_text()
            with self.subTest(issue=number):
                metadata = json.loads((FIXTURES / f'agentflow-{number}.json').read_text())
                self.assertEqual(metadata['query'], 'userContentEdits(last:1).nodes[0].diff')
                code, output = lint(body)
                self.assertEqual(code, 1, output)
                errors = [line for line in output.splitlines() if '[runner-expect]' in line]
                self.assertEqual(len(errors), count)
                error = next(line for line in errors if f'ERROR {gate_id}:' in line)
                self.assertIn(original, error)
                assert_wrong_summary(self, 'pytest', original, error)
                sample = next(sample for sample in data['samples']
                              if sample['command'].endswith('-q ' + target))
                self.assertFalse(expect_matches(original, sample['output']))


if __name__ == '__main__':
    unittest.main()
