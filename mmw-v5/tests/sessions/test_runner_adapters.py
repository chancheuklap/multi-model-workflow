"""Terminal runner protocol contracts with vendor CLIs replaced at the process boundary."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

RUNNERS = Path(os.environ.get('RUNNERS_UNDER_TEST') or
               Path(__file__).resolve().parents[2] / 'tools/dispatch/scripts/runners')

VENDOR = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['VENDOR_LOG'], 'a') as log:
    log.write(json.dumps({'vendor': name, 'args': args,
                          'workspace': os.environ.get('PASEO_WORKSPACE_ID')}) + '\n')
name_file = Path(os.environ['VENDOR_LOG'] + '.name')
mode = os.environ.get('LIST_MODE', 'present')
if args[:1] == ['ls'] or args[:2] in (['agent', 'list'], ['terminal', 'list']):
    if mode == 'failed': sys.exit(1)
    if mode == 'malformed': print('{}'); sys.exit()
    status = os.environ.get('SESSION_STATUS', {'paseo': 'idle', 'herdr': 'idle', 'orca': 'running'}[name])
    session_name = name_file.read_text() if name_file.exists() else 'session-1'
    rows = [] if mode == 'absent' or (os.environ.get('STARTED_ONLY') and not name_file.exists()) else [{'id': session_name, 'name': session_name, 'handle': session_name,
                                       'pane_id': 'pane-1', 'status': status, 'agent_status': status,
                                       'agentIdentity': os.environ.get('SESSION_IDENTITY', 'codex')}]
    if name == 'paseo': result = rows
    elif name == 'herdr': result = {'result': {'agents': rows}}
    else: result = {'result': {'terminals': rows, 'truncated': mode == 'truncated'}}
    print(json.dumps(result)); sys.exit()
if args[:2] == ['terminal', 'read']:
    tail = ['Trust this folder?', '1. Trust', '2. Cancel'] if os.environ.get('START_DIALOG') else ['Ready for input']
    print(json.dumps({'result': {'terminal': {'tail': tail}}})); sys.exit()
if args[:2] == ['terminal', 'wait']:
    condition = args[args.index('--for') + 1]
    if condition == 'exit' or os.environ.get('SEND_MODE') == 'busy':
        print(json.dumps({'error': {'code': 'timeout'}}))
    else:
        print(json.dumps({'result': {'wait': {'satisfied': True, 'status': 'running'}}}))
    sys.exit()
if args[:2] == ['terminal', 'create']:
    print(json.dumps({'result': {'terminal': {'handle': 'session-1'}}})); sys.exit()
if args[:2] == ['tab', 'create']:
    print(json.dumps({'result': {'root_pane': {'pane_id': 'pane-1'}}})); sys.exit()
if args[:2] == ['agent', 'start']:
    name_file.write_text(args[2]); sys.exit(1 if os.environ.get('FAIL_AGENT_START') else 0)
if args[:1] == ['run']:
    print(json.dumps({'agentId': 'session-1'})); sys.exit()
if args[:2] in (['terminal', 'send'], ['agent', 'prompt']) or args[:1] == ['send']:
    sending = os.environ.get('SEND_MODE', 'confirmed')
    if sending == 'failed': sys.exit(1)
    if name == 'orca':
        if sending == 'unsafe': result = {'error': {'code': 'error', 'data': {'retrySafe': False}}}
        else: result = {'result': {'send': {'prompt': {'stages': ['input_accepted' if sending == 'accepted' else 'turn_started']}}}}
        print(json.dumps(result))
    elif name == 'herdr' and sending == 'uncertain':
        print(json.dumps({'error': {'code': 'timeout'}})); sys.exit(1)
    sys.exit()
if args[:1] == ['archive'] or args[:2] in (['pane', 'close'], ['terminal', 'close']):
    if os.environ.get('FAIL_CLOSE'): sys.exit(1)
    name_file.unlink(missing_ok=True); sys.exit()
sys.exit(2)
'''


class TerminalRunners(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='mmw-v5-runners-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.scripts = self.root / 'scripts'
        shutil.copytree(RUNNERS.parent, self.scripts)
        for name in ('hosts.json', 'roles.json'):
            shutil.copy2(RUNNERS.parent.parent / name, self.root / name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for vendor in ('paseo', 'herdr', 'orca'):
            path = self.bin / vendor
            path.write_text(VENDOR)
            path.chmod(0o700)
        self.cwd = self.root / 'assignment'
        self.cwd.mkdir()
        self.log = self.root / 'vendor.jsonl'
        self.environment = {'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                            'HOME': str(self.root), 'MMW_HOME': str(self.root / 'runtime'),
                            'VENDOR_LOG': str(self.log)}

    def run_adapter(self, vendor, *arguments, **environment):
        return subprocess.run(['bash', str(self.scripts / 'runners' / (vendor + '.sh')),
                               *arguments], env={**self.environment, **environment},
                              capture_output=True, text=True, timeout=10)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def start_arguments(self):
        return ['start', '--host', 'codex', '--model', 'chosen-model', '--effort', 'high',
                '--cwd', str(self.cwd), '--prompt', 'Implement the bounded assignment.',
                '--title', 'assignment worker']

    def test_herdr_closes_created_pane_when_initial_delivery_is_unconfirmed(self):
        result = self.run_adapter('herdr', *self.start_arguments(), SEND_MODE='uncertain', STARTED_ONLY='1')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertTrue(any(call['args'] == ['pane', 'close', 'pane-1'] for call in self.calls()))
        alive = self.run_adapter('herdr', 'liveness', 'assignment-worker', STARTED_ONLY='1')
        self.assertEqual(alive.stdout.strip(), 'stopped')

    def test_herdr_closes_created_pane_after_agent_start_failure(self):
        result = self.run_adapter('herdr', *self.start_arguments(), FAIL_AGENT_START='1', STARTED_ONLY='1')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertTrue(any(call['args'] == ['pane', 'close', 'pane-1'] for call in self.calls()))
        self.assertEqual(self.run_adapter('herdr', 'liveness', 'assignment-worker',
                                          STARTED_ONLY='1').stdout.strip(), 'stopped')

    def test_herdr_retains_recovery_identity_when_start_cleanup_fails(self):
        result = self.run_adapter('herdr', *self.start_arguments(), SEND_MODE='uncertain',
                                  FAIL_CLOSE='1', STARTED_ONLY='1')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('could not close pane pane-1', result.stderr)
        self.assertIn('assignment-worker', result.stderr)
        self.assertIn('herdr pane close pane-1', result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(self.run_adapter('herdr', 'liveness', 'assignment-worker',
                                          STARTED_ONLY='1').stdout.strip(), 'alive')

    def test_orca_retains_recovery_handle_when_dialog_cleanup_fails(self):
        result = self.run_adapter('orca', *self.start_arguments(), START_DIALOG='1', FAIL_CLOSE='1')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertIn('could not close terminal session-1', result.stderr)
        self.assertIn('orca terminal close --terminal session-1', result.stderr)
        self.assertEqual(sum(call['args'][:2] == ['terminal', 'create'] for call in self.calls()), 1)

    def test_present_idle_and_absent_sessions_have_distinct_liveness(self):
        for vendor in ('paseo', 'herdr', 'orca'):
            with self.subTest(vendor=vendor):
                result = self.run_adapter(vendor, 'liveness', 'session-1')
                self.assertEqual((result.returncode, result.stdout.strip()), (0, 'alive'), result.stderr)
                result = self.run_adapter(vendor, 'liveness', 'session-1', LIST_MODE='absent')
                self.assertEqual((result.returncode, result.stdout.strip()), (0, 'stopped'), result.stderr)

    def test_failed_or_malformed_lists_never_prove_a_session_stopped(self):
        for vendor in ('paseo', 'herdr', 'orca'):
            for mode in ('failed', 'malformed'):
                with self.subTest(vendor=vendor, mode=mode):
                    result = self.run_adapter(vendor, 'liveness', 'session-1', LIST_MODE=mode)
                    self.assertEqual((result.returncode, result.stdout.strip()), (0, 'unknown'))
                    result = self.run_adapter(vendor, 'send', 'session-1', 'continue', LIST_MODE=mode)
                    self.assertEqual(result.returncode, 3, result.stderr)

    def test_send_distinguishes_missing_session_and_confirmed_delivery(self):
        for vendor in ('paseo', 'herdr', 'orca'):
            with self.subTest(vendor=vendor):
                result = self.run_adapter(vendor, 'send', 'session-1', 'continue', LIST_MODE='absent')
                self.assertEqual(result.returncode, 2, result.stderr)
                result = self.run_adapter(vendor, 'send', 'session-1', 'continue')
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_uncertain_delivery_is_never_safe_to_send_again(self):
        for vendor, mode in (('orca', 'unsafe'), ('herdr', 'uncertain')):
            with self.subTest(vendor=vendor):
                result = self.run_adapter(vendor, 'send', 'session-1', 'continue', SEND_MODE=mode)
                self.assertEqual(result.returncode, 4, result.stderr)

    def test_orca_accepts_codex_mid_turn_but_waits_for_other_active_hosts(self):
        result = self.run_adapter('orca', 'send', 'session-1', 'continue', SEND_MODE='accepted')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_adapter('orca', 'send', 'session-1', 'continue', SEND_MODE='busy',
                                  SESSION_IDENTITY='claude')
        self.assertEqual(result.returncode, 3, result.stderr)

    def test_session_identity_comes_from_each_runner_environment(self):
        for vendor, environment in (('paseo', {'PASEO_AGENT_ID': 'session-1'}),
                                     ('herdr', {'HERDR_ENV': '1', 'HERDR_PANE_ID': 'pane-1'}),
                                     ('orca', {'ORCA_TERMINAL_HANDLE': 'session-1'})):
            with self.subTest(vendor=vendor):
                result = self.run_adapter(vendor, 'self', **environment)
                self.assertEqual((result.returncode, result.stdout.strip()), (0, 'session-1'))
                self.assertEqual(self.run_adapter(vendor, 'self').returncode, 3)

    def test_start_preserves_assignment_and_explicit_runtime_environment(self):
        for vendor in ('paseo', 'herdr', 'orca'):
            with self.subTest(vendor=vendor):
                self.log.unlink(missing_ok=True)
                result = self.run_adapter(vendor, 'start', '--host', 'codex', '--model', 'chosen-model',
                                          '--effort', 'high', '--cwd', str(self.cwd),
                                          '--prompt', 'Implement the bounded assignment.',
                                          '--title', 'assignment worker', '--env', 'MMW_HOME=/v5/runtime',
                                          '--env', 'MMW_RUNNER=' + vendor, PASEO_WORKSPACE_ID='ambient-workspace')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip())
                calls = self.calls()
                combined = json.dumps(calls)
                self.assertIn('Implement the bounded assignment.', combined)
                self.assertIn('MMW_HOME=/v5/runtime', combined)
                self.assertIn('MMW_RUNNER=' + vendor, combined)
                self.assertNotIn('Read the mmw-mode skill', combined)
                self.assertNotIn('mmw-v4', combined)
                if vendor == 'paseo':
                    launched = next(call for call in calls if call['args'][0] == 'run')
                    self.assertIsNone(launched['workspace'])


if __name__ == '__main__':
    unittest.main()
