import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/writing-for-agents/scripts/usage.py'


class Usage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.skills = self.repo / 'mmw-v4/skills'
        (self.skills / 'how').mkdir(parents=True)
        (self.skills / 'how/SKILL.md').write_text('the how skill\n')
        self.claude = self.root / 'claude'
        self.codex = self.root / 'codex'
        self.claude.mkdir()
        self.codex.mkdir()

    def record(self, host, path, *rows):
        target = host / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def run_usage(self, skill='how', *args):
        result = subprocess.run([sys.executable, str(SCRIPT), skill, '--repo', str(self.repo),
                                 '--claude', str(self.claude), '--codex', str(self.codex), *args],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_first_line_is_the_summary(self):
        self.assertEqual(self.run_usage().splitlines()[0],
                         'usage how: 0 text entries; claude 0 invoked, 0 read, 0 by subagents; codex 0 read')

    def test_lists_text_entries(self):
        (self.skills / 'other').mkdir()
        (self.skills / 'other/SKILL.md').write_text(
            'how to do this\n' + '\n'.join(['the how skill', '**how**', '/how', '`how`', 'skills/how/'])
            + '\n/however **however** `however` skills/however/\n')
        (self.repo / 'AGENTS.md').write_text('the how skill\n')
        (self.repo / 'CLAUDE.md').write_text('`how`\n')
        output = self.run_usage()
        self.assertIn('usage how: 3 text entries;', output)
        for line in range(2, 7):
            self.assertIn(f'mmw-v4/skills/other/SKILL.md:{line}\n', output)
        self.assertIn('AGENTS.md:1\n', output)
        self.assertIn('CLAUDE.md:1\n', output)
        self.assertNotIn('SKILL.md:1\n', output)
        self.assertNotIn('SKILL.md:7\n', output)

    def test_counts_a_skill_invocation(self):
        self.record(self.claude, 'project/session.jsonl',
                    {'type': 'user', 'timestamp': '2026-10-12T00:00:00Z',
                     'message': {'role': 'user', 'content': 'Owner request\nPRIVATE SECOND LINE'}},
                    {'type': 'assistant', 'message': {'content': [
                        {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'how'}},
                        {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'how'}},
                        {'type': 'text', 'text': 'PRIVATE ASSISTANT TEXT'}]}})
        output = self.run_usage()
        self.assertIn('claude 1 invoked, 0 read, 0 by subagents', output)
        self.assertIn('2026-10-12', output)
        self.assertIn('Owner request', output)
        self.assertNotIn('PRIVATE', output)

    def test_counts_a_file_read_by_path(self):
        self.record(self.claude, 'project/session.jsonl',
                    {'type': 'assistant', 'message': {'content': [
                        {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/home/me/.agents/skills/how/SKILL.md'}},
                        {'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'cat /repo/mmw-v4/skills/how/guide.md'}},
                        {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/home/me/.agents/skills/how/SKILL.md'}}]}})
        output = self.run_usage()
        self.assertIn('claude 0 invoked, 1 read, 0 by subagents', output)
        self.assertIn('skills/how/SKILL.md', output)
        self.assertIn('skills/how/guide.md', output)

    def test_counts_a_codex_read_command(self):
        for i, command in enumerate(['cat /x/skills/how/SKILL.md',
                                     "sed -n '1,20p' /x/skills/how/guide.md",
                                     'nl -ba /x/skills/how/guide.md',
                                     'head -20 /x/skills/how/guide.md',
                                     'tail -n 20 /x/skills/how/guide.md']):
            self.record(self.codex, f'2026/10/{i}.jsonl',
                        {'type': 'session_meta', 'payload': {'timestamp': '2026-10-12T00:00:00Z'}},
                        {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'x' * 100}},
                        {'type': 'response_item', 'payload': {'type': 'function_call',
                         'name': 'exec_command', 'arguments': json.dumps({'cmd': command})}})
        self.record(self.codex, 'custom.jsonl', {'type': 'response_item', 'payload': {
            'type': 'custom_tool_call', 'name': 'exec',
            'input': 'const r = await tools.exec_command({cmd: "cat /x/skills/how/SKILL.md"});'}})
        self.record(self.codex, 'single-quoted.jsonl',
                    {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                     'content': [{'type': 'input_text', 'text': 'Older owner request\nPRIVATE'}]}},
                    {'type': 'response_item', 'payload': {'type': 'custom_tool_call', 'name': 'exec',
                     'input': "await tools.exec_command({cmd: 'cat /x/skills/how/SKILL.md'});"}})
        output = self.run_usage()
        self.assertIn('codex 7 read', output)
        self.assertIn('Older owner request', output)
        self.assertNotIn('PRIVATE', output)
        self.assertIn('skills/how/SKILL.md', output)
        self.assertIn('2026-10-12', output)
        self.assertIn('x' * 80, output)
        self.assertNotIn('x' * 81, output)

    def test_ignores_a_bare_mention(self):
        self.record(self.claude, 'mention.jsonl', {'type': 'assistant', 'message': {
            'content': [{'type': 'text', 'text': 'Read /x/skills/how/SKILL.md'}]}})
        self.record(self.codex, 'mentions.jsonl',
                    {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant',
                     'content': [{'type': 'output_text', 'text': 'cat /x/skills/how/SKILL.md'}]}},
                    *[{'type': 'response_item', 'payload': {'type': 'function_call',
                       'arguments': json.dumps({'cmd': command})}} for command in [
                           'echo /x/skills/how/SKILL.md', "echo 'cat /x/skills/how/SKILL.md'",
                           'rg pattern /x/skills/how/SKILL.md', 'ls /x/skills/how/SKILL.md',
                           'cat /x/skills/however/SKILL.md']])
        self.assertIn('claude 0 invoked, 0 read, 0 by subagents; codex 0 read', self.run_usage())

    def test_folds_a_subagent_into_its_session(self):
        self.record(self.claude, 'project/parent.jsonl',
                    {'type': 'user', 'timestamp': '2026-10-12T00:00:00Z',
                     'message': {'content': 'Owner question'}})
        for agent in ('agent-a', 'agent-b'):
            self.record(self.claude, f'project/parent/subagents/{agent}.jsonl',
                        {'type': 'user', 'message': {'content': 'PRIVATE SUBAGENT BRIEF'}},
                        {'type': 'assistant', 'message': {'content': [
                            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/skills/how/guide.md'}},
                            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'how'}}]}})
        output = self.run_usage()
        self.assertIn('claude 1 invoked, 1 read, 2 by subagents', output)
        self.assertEqual(output.count('Owner question'), 1)
        self.assertNotIn('PRIVATE', output)

    def test_accepts_a_file(self):
        (self.skills / 'how/guide.md').write_text('guide\n')
        (self.skills / 'other').mkdir()
        (self.skills / 'other/SKILL.md').write_text('how\nSee guide.md\n')
        self.record(self.claude, 'guide.jsonl', {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/skills/how/guide.md'}}]}})
        self.record(self.claude, 'skill.jsonl', {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/skills/how/SKILL.md'}},
            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'how'}}]}})
        self.record(self.codex, 'skill.jsonl', {'type': 'response_item', 'payload': {
            'type': 'function_call', 'arguments': json.dumps({'cmd': 'cat /x/skills/how/SKILL.md'})}})
        for name in ('mmw-v4/skills/how/guide.md', str(self.skills / 'how/guide.md')):
            output = self.run_usage(name)
            self.assertIn(f'usage {name}: 1 text entries; claude 0 invoked, 1 read, 0 by subagents; codex 0 read', output)
            self.assertIn('mmw-v4/skills/other/SKILL.md:2\n', output)
            self.assertNotIn('skills/how/SKILL.md', output)

    def test_since_limits_sessions_and_reports_file_counts_and_dates(self):
        for day in ('11', '12', '13'):
            self.record(self.claude, f'project/{day}.jsonl',
                        {'timestamp': f'2026-10-{day}T12:00:00Z', 'type': 'assistant',
                         'message': {'content': [{'type': 'tool_use', 'name': 'Read',
                             'input': {'file_path': '/x/skills/how/SKILL.md'}}]}})
            self.record(self.codex, f'{day}.jsonl',
                        {'timestamp': f'2026-10-{day}T12:00:00Z', 'type': 'response_item',
                         'payload': {'type': 'function_call',
                                     'arguments': json.dumps({'cmd': 'cat /x/skills/how/guide.md'})}})
        output = self.run_usage('how', '--since', '2026-10-12')
        self.assertIn('claude 0 invoked, 2 read, 0 by subagents; codex 2 read', output)
        self.assertNotIn('2026-10-11', output)
        self.assertIn('claude dates: 2026-10-12 to 2026-10-13', output)
        self.assertIn('claude file skills/how/SKILL.md: 2 sessions', output)
        self.assertIn('codex file skills/how/guide.md: 2 sessions', output)


if __name__ == '__main__':
    unittest.main()
