"""Runner EXPECT contracts, lint errors and original-ticket replays, without GitHub."""

import io
import json
import subprocess
import tempfile
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


def ticket(check, expect):
    return ('## Parent\n\n#555, Implementation Decisions section 1\n\n'
            '## Acceptance criteria\n\n'
            '- [ ] AC1: the selected behaviour passes\n'
            f'  CHECK: {check}\n  EXPECT: {expect}\n  EVIDENCE: pending\n')


def lint(body, draft=False):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / 'T1.md').write_text('TITLE: Runner contract\n'
                                  'LABELS: mmw:ticket, ready-for-agent, junior-worker\n'
                                  'BLOCKED BY: (none)\n---\n' + body)
        with mock.patch.object(vt, 'fetch_body', side_effect=lambda n: body if n == 77 else
                               '## Implementation Decisions\n\n### 1. Runners\n\nRules\n'), \
             mock.patch.object(vt, 'fetch_ticket', return_value={
                 'labels': [{'name': name} for name in LABELS]}), \
             mock.patch.object(vt, 'fetch_parent', return_value=None), \
             mock.patch.object(vt, 'fetch_sub_issues', return_value=[77]), \
             mock.patch.object(vt, 'fetch_blocked_by', return_value=[]), \
             redirect_stdout(io.StringIO()) as out:
            code = vt.main(['555', '--lint', '--drafts', tmp] if draft else ['77', '--lint'])
    return code, out.getvalue()


class TestRunnerExpect(unittest.TestCase):
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
                    self.assertTrue('rejects success' in error or 'accepts failure' in error, error)
                    self.assertIn('mandatory', error)

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
                self.assertIn('mandatory', output)
                self.assertIn(standard, output)

    def test_lint_runner_expect_uses_javascript_flags_and_full_output(self):
        for expect in [summaries()['pytest']['expect'].removesuffix('m'),
                       r'/(?<count>\d+) passed/u', '/[/m']:
            with self.subTest(expect=expect):
                code, output = lint(ticket('uv run pytest -q', expect))
                self.assertEqual(code, 1, output)
                self.assertIn('[runner-expect]', output)

    def test_lint_runner_expect_leaves_other_commands_unchanged(self):
        code, output = lint(ticket('node scripts/import.mjs', '/^6 rows$/m'))
        self.assertEqual(code, 0, output)
        self.assertNotIn('[runner-expect]', output)

    def test_replay_runner_expect_reports_pytest_criteria_from_original_bodies(self):
        for number in (1349, 1125):
            body = (FIXTURES / f'agentflow-{number}.md').read_text()
            with self.subTest(issue=number):
                code, output = lint(body)
                self.assertEqual(code, 1, output)
                errors = '\n'.join(line for line in output.splitlines() if '[runner-expect]' in line)
                for gate_id, check, _ in vt.criteria_lines(body):
                    if 'pytest' in check:
                        self.assertIn(gate_id + ':', errors)
                self.assertIn(summaries()['pytest']['expect'], errors)


if __name__ == '__main__':
    unittest.main()
