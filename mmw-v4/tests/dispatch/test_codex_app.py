#!/usr/bin/env python3
"""Native runner receipts, detached delivery and host-event liveness in isolated homes."""

import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / 'skills/dispatch/scripts'
ADAPTER = SCRIPTS / 'runners/codex-app.sh'
spec = importlib.util.spec_from_file_location('codex_app_adapter', SCRIPTS / 'runners/codex_app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

SESSION = '01900000-1111-7111-8111-111111111111'


class AppRunnerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mmw-app-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.cwd = self.root / 'issue-12'
        self.cwd.mkdir()
        self.binary = self.root / 'codex'
        self.binary.write_text('''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
mode=os.environ.get('FAKE_QUEUE_MODE','ack')
for line in sys.stdin:
 p=json.loads(line)
 if p['method']=='initialize':
  if mode=='init-close': sys.exit()
  print(json.dumps({'id':p['id'],'result':{'userAgent':'fixture'}}),flush=True)
 elif p['method']=='thread/queue/add':
  Path(os.environ['FAKE_QUEUE_LOG']).write_text(json.dumps({'request':p,'code_home':os.environ['CODEX_HOME']}))
  if mode=='close': sys.exit()
  r=({'error':{'code':-32600,'message':'thread not found'}} if mode=='missing'
     else {'result':{'queuedSubmission':{'id':'queued-1'}}})
  print(json.dumps({'id':p['id'],**r}),flush=True)
 elif p['method']=='project/list':
  print(json.dumps({'id':p['id'],'error':{'message':'project display unavailable'}}),flush=True)
 elif p['method']=='thread/start':
  params=p['params']
  Path(os.environ['FAKE_QUEUE_LOG']).write_text(json.dumps(params))
  result={'thread':{'id':'prepared-chat','cwd':params['cwd']},
          'approvalPolicy':params.get('approvalPolicy'),
          'sandbox':{'type':'readOnly' if mode=='wrong-permissions' else 'dangerFullAccess'}}
  print(json.dumps({'id':p['id'],'result':result}),flush=True)
 elif p['method']=='thread/name/set':
  r=({'error':{'message':'title display unavailable'}} if mode=='title-failure' else {'result':{}})
  print(json.dumps({'id':p['id'],**r}),flush=True)
''')
        self.binary.chmod(0o700)
        self.log = self.root / 'queue.json'
        self.environment = {
            'PATH': os.environ['PATH'], 'HOME': str(self.root),
            'MMW_HOME': str(self.root / 'mmw'), 'CODEX_HOME': str(self.root / 'codex-home'),
            'GH_REPO': 'owner/repo', 'CODEX_THREAD_ID': SESSION,
            'CODEX_APP_RUNTIME_CLI_PATH': str(self.binary),
            'CODEX_APP_TOOLS_PIPE_PATH': str(self.root / 'unused-fixture-binding'),
            'CODEX_PERMISSION_PROFILE': ':danger-full-access',
            'FAKE_QUEUE_LOG': str(self.log)}
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, self.environment, clear=True).start()
        self.process = {'pid': os.getpid(), 'identity': app.statedir.process_identity(os.getpid())}
        patch.object(app, 'app_process', return_value=self.process).start()

    def run_adapter(self, *arguments, extra=None):
        return subprocess.run(['bash', str(ADAPTER), *arguments], cwd=self.cwd,
                              env={**os.environ, **(extra or {})}, capture_output=True,
                              text=True, timeout=15)

    def record(self, state='working'):
        app.observe(SESSION, state, repo='owner/repo', cwd=str(self.cwd))
        return app.session_paths(SESSION)[0]

    def exchange(self, arguments, result=None, error=None, wrong_id=False):
        request_read, request_write = os.pipe()
        reply_read, reply_write = os.pipe()
        command = f'exec 3>&{request_write} 4<&{reply_read}; exec "$@"'
        child = subprocess.Popen(['bash', '-c', command, 'native-fixture',
                                  'bash', str(ADAPTER), *arguments], cwd=self.cwd,
                                 env={**os.environ, 'MMW_NATIVE_TOOLS': '1'},
                                 pass_fds=(request_write, reply_read),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        os.close(request_write)
        os.close(reply_read)
        try:
            readable, _, _ = select.select([request_read], [], [], 10)
            self.assertTrue(readable, 'runner must request its native operation')
            with os.fdopen(request_read, encoding='utf-8') as requests:
                line = requests.readline()
            self.assertTrue(line.startswith(app.PREFIX), line)
            request = json.loads(line[len(app.PREFIX):])
            response = {'id': 'wrong' if wrong_id else request['id'],
                        'ok': error is None, 'result': result, 'error': error}
            os.write(reply_write, (json.dumps(response) + '\n').encode())
            stdout, stderr = child.communicate(timeout=10)
            return request, subprocess.CompletedProcess(arguments, child.returncode, stdout, stderr)
        finally:
            os.close(reply_write)
            if child.poll() is None:
                child.kill()
                child.wait()

    def start_arguments(self):
        return ['start', '--host', 'codex', '--model', 'model-1', '--effort', 'high',
                '--cwd', str(self.cwd), '--prompt', 'Dispatched: worker, ticket #12.',
                '--title', '#12 worker', '--skip-approval', '--env', 'GH_REPO=owner/repo']

    def test_start_preserves_requested_assignment_and_records_confirmed_identity(self):
        request, result = self.exchange(self.start_arguments(),
                                        {'session': SESSION, 'state': 'active'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), SESSION)
        self.assertEqual(request['operation'], 'start')
        self.assertEqual(request['arguments']['cwd'], str(self.cwd))
        self.assertEqual(request['arguments']['model'], 'model-1')
        self.assertEqual(request['arguments']['effort'], 'high')
        self.assertTrue(request['arguments']['prompt'].endswith('Dispatched: worker, ticket #12.'))
        self.assertIn('MMW_HOME=' + str(self.root / 'mmw'), request['arguments']['prompt'])
        self.assertIn(str(SCRIPTS.parent.parent), request['arguments']['prompt'])
        self.assertEqual(request['arguments']['title'], 'owner/repo #12 worker')
        record = json.loads(app.session_paths(SESSION)[0].read_text())
        self.assertEqual(record['session'], SESSION)
        self.assertEqual(record['cwd'], str(self.cwd))

    def test_plain_shell_refuses_native_start_without_reporting_a_session(self):
        result = self.run_adapter(*self.start_arguments())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('runner tool executor', result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(app.session_paths(SESSION), [])

    def test_start_refuses_a_different_host(self):
        arguments = self.start_arguments()
        arguments[2] = 'claude'
        result = self.run_adapter(*arguments)
        self.assertIn('codex host', result.stderr)
        self.assertEqual(app.session_paths(SESSION), [])

    def test_public_preparation_retains_directory_model_effort_and_permissions_before_dispatch(self):
        arguments = self.start_arguments()
        arguments[0] = 'prepare'
        result = self.run_adapter(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'session': 'prepared-chat', 'cwd': str(self.cwd)})
        request = json.loads(self.log.read_text())
        self.assertEqual(request['cwd'], str(self.cwd))
        self.assertEqual(request['model'], 'model-1')
        self.assertEqual(request['config']['model_reasoning_effort'], 'high')
        self.assertEqual(request['approvalPolicy'], 'never')
        self.assertEqual(request['sandbox'], 'danger-full-access')
        self.assertNotIn('input', request)

    def test_preparation_refuses_a_permission_receipt_that_does_not_match(self):
        arguments = self.start_arguments()
        arguments[0] = 'prepare'
        result = self.run_adapter(*arguments, extra={'FAKE_QUEUE_MODE': 'wrong-permissions'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('startup permissions', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_a_title_failure_does_not_discard_the_prepared_chat(self):
        arguments = self.start_arguments()
        arguments[0] = 'prepare'
        result = self.run_adapter(*arguments, extra={'FAKE_QUEUE_MODE': 'title-failure'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['session'], 'prepared-chat')

    def test_a_different_operation_receipt_never_registers_a_session(self):
        _, result = self.exchange(self.start_arguments(), {'session': SESSION}, wrong_id=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertEqual(app.session_paths(SESSION), [])

    def test_failed_stop_preserves_the_observation_and_confirmed_stop_is_terminal(self):
        path = self.record()
        before = path.read_bytes()
        _, result = self.exchange(['stop', SESSION], error='native archive refused')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), before)
        _, result = self.exchange(['stop', SESSION], {'session': SESSION, 'stopped': True})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(app.background_state(SESSION), 'stopped')
        app.observe(SESSION, 'idle')
        self.assertEqual(app.background_state(SESSION), 'stopped')
        self.assertEqual(self.run_adapter('stop', SESSION).returncode, 0)

    def test_host_events_change_turn_state_without_confusing_idle_with_stopped(self):
        self.record()
        self.assertEqual(app.background_state(SESSION), 'working')
        result = self.run_adapter('hook', 'idle')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(app.background_state(SESSION), 'idle')
        self.assertEqual(self.run_adapter('liveness', SESSION).stdout.strip(), 'alive')

    def test_unknown_or_reused_runtime_identity_never_proves_a_session_stopped(self):
        result = self.run_adapter('liveness', SESSION)
        self.assertEqual(result.stdout.strip(), 'unknown')
        path = self.record()
        record = json.loads(path.read_text())
        record['process']['identity'] = 'another process start time'
        path.write_text(json.dumps(record))
        self.assertEqual(app.background_state(SESSION), 'unknown')
        self.assertEqual(self.run_adapter('liveness', SESSION).stdout.strip(), 'unknown')

    def test_identity_queries_at_turn_end_preserve_idle_state(self):
        self.record('idle')
        result = self.run_adapter('self')
        self.assertEqual(result.stdout.strip(), SESSION)
        self.assertEqual(app.background_state(SESSION), 'idle')

    def test_a_stop_receipt_for_another_chat_does_not_release_the_requested_chat(self):
        path = self.record()
        before = path.read_bytes()
        _, result = self.exchange(['stop', SESSION], {'session': 'another-chat', 'stopped': True})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('different session', result.stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_hook_ignores_unregistered_chat_and_foreground_state_uses_native_receipt(self):
        self.assertEqual(self.run_adapter('hook', 'working').returncode, 0)
        self.assertEqual(app.session_paths(SESSION), [])
        request, result = self.exchange(['state', SESSION],
                                        {'session': SESSION, 'state': 'active', 'cwd': str(self.cwd)})
        self.assertEqual(request['operation'], 'state')
        self.assertEqual(result.stdout.strip(), 'working')

    def test_queue_acknowledgment_remains_unconfirmed_and_uses_recorded_code_home(self):
        self.record()
        result = self.run_adapter('send', SESSION, 'wake marker',
                                  extra={'CODEX_HOME': str(self.root / 'unrelated-home'),
                                         'CODEX_THREAD_ID': '', 'CODEX_APP_TOOLS_PIPE_PATH': '',
                                         'CODEX_APP_RUNTIME_CLI_PATH': ''})
        self.assertEqual(result.returncode, 4, result.stderr)
        sent = json.loads(self.log.read_text())
        self.assertEqual(sent['code_home'], self.environment['CODEX_HOME'])
        self.assertEqual(sent['request']['params']['threadId'], SESSION)
        self.assertEqual(sent['request']['params']['input'], [{'type': 'text', 'text': 'wake marker'}])

    def test_queue_missing_and_lost_receipt_are_distinct(self):
        self.record()
        result = self.run_adapter('send', SESSION, 'wake', extra={'FAKE_QUEUE_MODE': 'missing'})
        self.assertEqual(result.returncode, 2, result.stderr)
        result = self.run_adapter('send', SESSION, 'wake', extra={'FAKE_QUEUE_MODE': 'close'})
        self.assertEqual(result.returncode, 4, result.stderr)
        result = self.run_adapter('send', SESSION, 'wake', extra={'FAKE_QUEUE_MODE': 'init-close'})
        self.assertEqual(result.returncode, 3, result.stderr)


if __name__ == '__main__':
    unittest.main()
