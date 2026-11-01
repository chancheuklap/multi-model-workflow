"""Native App startup cleanup through the host tool executor boundary."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

EXECUTOR = Path(__file__).resolve().parents[2] / 'tools/dispatch/scripts/runners/codex-app-tools.js'

FIXTURE = r'''
import {readFileSync} from 'node:fs';
const execute = eval(readFileSync(process.argv[1], 'utf8'));
const mode = process.argv[2];
const calls = [];
let active = false;
let invoked = 0;
let response;
const receipt = value => ({content: [{type: 'text', text: JSON.stringify(value)}]});
const tools = {
  async exec_command() {
    invoked++;
    if (invoked === 1)
      return {session_id: 1, output: 'MMW_NATIVE_REQUEST ' + JSON.stringify({
        id: 'startup-1', operation: 'start', arguments: {
          helper: '/runtime/helper.py', cwd: '/task', model: 'chosen-model',
          effort: 'high', title: 'bounded task', prompt: 'Do the task'
        }}) + '\n'};
    return {exit_code: 0, output: JSON.stringify({session: 'prepared-chat', cwd: '/task'}) + '\n'};
  },
  async write_stdin(args) {
    response = JSON.parse(args.chars);
    return {exit_code: 1, output: ''};
  },
  async mcp__codex_app__send_message_to_thread(args) {
    calls.push(['send', args.threadId]);
    active = true;
    if (mode === 'mismatch') return receipt({threadId: 'unrelated-chat'});
    throw new Error('initial send failed after chat preparation');
  },
  async mcp__codex_app__set_thread_archived(args) {
    calls.push(['archive', args.threadId]);
    if (mode === 'cleanup-failed') throw new Error('archive refused');
    active = false;
    return receipt({threadId: args.threadId, archived: true});
  },
  async mcp__codex_app__read_thread(args) {
    calls.push(['inspect', args.threadId]);
    return receipt({thread: {id: args.threadId, cwd: '/task',
      status: {type: active ? 'active' : 'notLoaded'}},
      turns: [{id: 'turn', status: active ? 'inProgress' : 'interrupted'}]});
  }
};
await execute(tools, 'adapter start');
process.stdout.write(JSON.stringify({calls, active, response}));
'''


@unittest.skipUnless(shutil.which('node'), 'native executor tests need Node.js')
class AppExecutorStartup(unittest.TestCase):
    def run_start(self, mode):
        result = subprocess.run(['node', '--input-type=module', '-e', FIXTURE,
                                 str(EXECUTOR), mode], env=dict(os.environ),
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_initial_send_failure_stops_only_the_prepared_chat(self):
        for mode in ('send-failed', 'mismatch'):
            with self.subTest(mode=mode):
                result = self.run_start(mode)
                self.assertFalse(result['response']['ok'])
                self.assertFalse(result['active'])
                self.assertEqual(result['calls'], [['send', 'prepared-chat'],
                                                   ['archive', 'prepared-chat'],
                                                   ['inspect', 'prepared-chat']])
                self.assertIn('prepared-chat was stopped', result['response']['error'])

    def test_failed_start_cleanup_keeps_the_exact_chat_identity_for_recovery(self):
        result = self.run_start('cleanup-failed')
        self.assertFalse(result['response']['ok'])
        self.assertTrue(result['active'])
        self.assertEqual(result['calls'], [['send', 'prepared-chat'], ['archive', 'prepared-chat']])
        self.assertIn('prepared-chat', result['response']['error'])
        self.assertIn('could not confirm cleanup', result['response']['error'])
        self.assertIn('archive refused', result['response']['error'])


if __name__ == '__main__':
    unittest.main()
