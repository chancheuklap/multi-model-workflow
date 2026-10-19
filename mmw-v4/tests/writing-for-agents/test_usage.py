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

    def test_a_path_with_a_line_number_counts_for_its_file(self):
        self.record(self.claude, 'lines.jsonl', {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': path}}
            for path in ('/x/skills/how/SKILL.md', '/x/skills/how/SKILL.md:155')]}})
        self.record(self.codex, 'lines.jsonl', {'type': 'response_item', 'payload': {
            'type': 'function_call', 'arguments': json.dumps({'cmd': 'cat /x/skills/how/SKILL.md:155'})}})
        output = self.run_usage()
        self.assertEqual([line for line in output.splitlines() if ' file ' in line], [
            'claude file skills/how/SKILL.md: 1 sessions',
            'codex file skills/how/SKILL.md: 1 sessions'])

    def test_trailing_punctuation_is_stripped_before_matching(self):
        for index, suffix in enumerate(('.', ':155,', ':155。', '；', '）', '】', '！', '．')):
            self.record(self.claude, f'punctuation-{index}.jsonl', {
                'type': 'assistant', 'message': {'content': [
                    {'type': 'tool_use', 'name': 'Read',
                     'input': {'file_path': '/x/skills/how/SKILL.md' + suffix}}]}})
        self.assertEqual([line for line in self.run_usage().splitlines() if ' file ' in line],
                         ['claude file skills/how/SKILL.md: 8 sessions'])

    def test_a_glob_or_variable_path_is_not_counted(self):
        (self.skills / 'how/guide').write_text('guide\n')
        (self.skills / 'how/$file').write_text('variable\n')
        for index, path in enumerate(('*.md', 'SKILL.md*', 'SKILL.md?', 'guide[ab]', '$file')):
            self.record(self.claude, f'pattern-{index}.jsonl', {
                'type': 'assistant', 'message': {'content': [
                    {'type': 'tool_use', 'name': 'Read',
                     'input': {'file_path': '/x/skills/how/' + path}}]}})
            self.record(self.codex, f'pattern-{index}.jsonl', {'type': 'response_item', 'payload': {
                'type': 'function_call', 'arguments': json.dumps({'cmd': 'cat /x/skills/how/' + path})}})
        output = self.run_usage()
        self.assertEqual(output.splitlines()[0],
                         'usage how: 0 text entries; claude 0 invoked, 5 read, 0 by subagents; codex 4 read')
        self.assertEqual([line for line in output.splitlines() if ' file ' in line], [])

    def test_a_path_to_no_existing_file_is_not_counted(self):
        (self.skills / 'how/directory').mkdir()
        (self.skills / 'other').mkdir()
        (self.skills / 'other/secret.md').write_text('outside the skill\n')
        (self.skills / 'how/link.md').symlink_to(self.skills / 'other/secret.md')
        self.record(self.claude, 'missing.jsonl', {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/skills/how/' + path}}
            for path in ('missing.md', 'directory', '../other/secret.md', 'link.md')]}})
        output = self.run_usage()
        self.assertIn('claude 0 invoked, 1 read, 0 by subagents', output)
        self.assertEqual([line for line in output.splitlines() if ' file ' in line], [])

    def test_first_line_is_the_summary(self):
        (self.repo / 'AGENTS.md').write_text('the how skill\n')
        self.assertEqual(self.run_usage().splitlines()[0],
                         'usage how: 1 text entries; claude 0 invoked, 0 read, 0 by subagents; codex 0 read')

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
        self.record(self.claude, 'project/other.jsonl', {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'however'}},
            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'other'}}]}})
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
        self.record(self.claude, 'project/other.jsonl', {'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/skills/however/SKILL.md'}},
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/x/skills/other/SKILL.md'}}]}})
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
        self.assertIn('skills/how/SKILL.md', output)

    def test_session_preview_is_only_the_first_user_line_cut_to_80(self):
        self.record(self.codex, 'preview.jsonl',
                    {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user',
                     'content': [{'type': 'input_text', 'text': 'Older owner request\nPRIVATE'}]}},
                    {'type': 'response_item', 'payload': {'type': 'function_call',
                     'arguments': json.dumps({'cmd': 'cat /x/skills/how/SKILL.md'})}})
        self.record(self.codex, 'long.jsonl',
                    {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'x' * 100}},
                    {'type': 'response_item', 'payload': {'type': 'function_call',
                     'arguments': json.dumps({'cmd': 'cat /x/skills/how/SKILL.md'})}})
        output = self.run_usage()
        self.assertIn('Older owner request', output)
        self.assertNotIn('PRIVATE', output)
        self.assertIn('x' * 80, output)
        self.assertNotIn('x' * 81, output)

    def test_reads_javascript_command_with_identity_escape(self):
        self.record(self.codex, 'escape.jsonl', {'type': 'response_item', 'payload': {
            'type': 'custom_tool_call', 'input':
                r'''await tools.exec_command({cmd: "cat /x/skills/how/SKILL.md; echo '\.md'"});'''}})
        self.assertIn('codex 1 read', self.run_usage())

    def test_missing_input_directory_refuses_instead_of_reporting_zero(self):
        for flag in ('--repo', '--claude', '--codex'):
            with self.subTest(flag=flag):
                missing = self.root / 'missing'
                result = subprocess.run([
                    sys.executable, str(SCRIPT), 'how', '--repo', str(self.repo),
                    '--claude', str(self.claude), '--codex', str(self.codex), flag, str(missing)],
                    text=True, capture_output=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(flag, result.stderr)
                self.assertIn(str(missing), result.stderr)
                self.assertNotIn('usage how: 0', result.stdout)

    def test_keeps_a_read_before_a_later_unbalanced_quote(self):
        self.record(self.codex, 'partial.jsonl', {'type': 'response_item', 'payload': {
            'type': 'function_call', 'arguments': json.dumps({'cmd':
                "cd x && sed -n '1,5p' /x/skills/how/guide.md\necho it's"})}})
        self.assertIn('codex 1 read', self.run_usage())

    def test_output_redirections_are_not_reads(self):
        for i, command in enumerate(["cat > /x/skills/how/SKILL.md <<'EOF'\nnew text\nEOF",
                                     'cat /tmp/source >> /x/skills/how/guide.md']):
            self.record(self.codex, f'write-{i}.jsonl', {'type': 'response_item', 'payload': {
                'type': 'function_call', 'arguments': json.dumps({'cmd': command})}})
        self.assertIn('codex 0 read', self.run_usage())

    def test_reads_shell_wrappers_and_environment_prefixes(self):
        for i, command in enumerate(["/bin/zsh -lc 'cat /x/skills/how/SKILL.md'",
                                     'FOO=1 cat /x/skills/how/SKILL.md']):
            self.record(self.codex, f'wrapper-{i}.jsonl', {'type': 'response_item', 'payload': {
                'type': 'function_call', 'arguments': json.dumps({'cmd': command})}})
        self.assertIn('codex 2 read', self.run_usage())

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
        (self.skills / 'how/guide.md').write_text('guide\n')
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
        (self.repo / 'AGENTS.md').write_text('the how skill\n')
        output = self.run_usage('how', '--since', '2026-10-12')
        self.assertLess(output.index('claude dates:'), output.index('AGENTS.md:1'))
        self.assertLess(output.index('codex file '), output.index('AGENTS.md:1'))


if __name__ == '__main__':
    unittest.main()
