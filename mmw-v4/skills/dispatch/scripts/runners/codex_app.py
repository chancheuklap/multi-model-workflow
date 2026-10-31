#!/usr/bin/env python3
"""Codex App runner operations and its host-event observations.

Start, foreground state and stop use the adapter's tool executor through inherited
request/reply descriptors. Detached send uses the public persistent queue API.
Background state uses observed host events and process identity, never a different
app-server's in-memory thread status. Repository ticket state remains in the tracker.
"""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import select
import shlex
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import statedir  # noqa: E402

PREFIX = 'MMW_NATIVE_REQUEST '
SESSION = re.compile(r'^[A-Za-z0-9_-]{1,200}$')
RPC_TIMEOUT = 60


class Refusal(ValueError):
    pass


def binary():
    supplied = os.environ.get('CODEX_APP_RUNTIME_CLI_PATH')
    candidates = [supplied] if supplied else [
                  '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex',
                  '/Applications/Codex.app/Contents/Resources/codex']
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise Refusal('no Codex executable is available; install Codex App before selecting this runner')


def app_context():
    return bool(os.environ.get('CODEX_THREAD_ID') and
                os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') and
                os.environ.get('CODEX_APP_TOOLS_PIPE_PATH'))


def app_process():
    wanted = os.environ.get('CODEX_APP_RUNTIME_CLI_PATH')
    if not wanted:
        return None
    rows = {}
    run = subprocess.run(['ps', '-axo', 'pid,ppid,comm'], capture_output=True,
                         text=True, timeout=10, check=True)
    for line in run.stdout.splitlines()[1:]:
        parts = line.strip().split(None, 2)
        if len(parts) == 3:
            rows[int(parts[0])] = (int(parts[1]), parts[2])
    pid = os.getppid()
    while pid in rows and pid > 1:
        parent, executable = rows[pid]
        if executable == wanted:
            identity = statedir.process_identity(pid)
            return {'pid': pid, 'identity': identity} if identity else None
        pid = parent
    return None


def session_paths(session):
    if not SESSION.fullmatch(session):
        raise Refusal('invalid App session identity; use the identity returned by the App')
    root = statedir.home() / 'state'
    if not root.exists():
        return []
    return [directory / 'codex-app' / (session + '.json')
            for directory in root.iterdir()
            if directory.is_dir() and (directory / 'codex-app' / (session + '.json')).is_file()]


def observe(session, state=None, repo=None, cwd=None, force=False):
    process = app_process()
    paths = session_paths(session)
    if repo:
        directory = statedir.state_dir(repo) / 'codex-app'
        directory.mkdir(mode=0o700, exist_ok=True)
        path = directory / (session + '.json')
        if path not in paths:
            paths.append(path)
    for path in paths:
        with statedir.locked(path.parent / 'state.lock', purpose='App host observation'):
            previous = statedir.read_json(path, {})
            if previous.get('state') == 'stopped' and not force:
                continue
            record = {**previous, 'session': session,
                      'state': state or previous.get('state', 'working'),
                      'at': statedir.now_iso()}
            if process:
                record['process'] = process
                record['binary'] = binary()
                record['code_home'] = str(Path(os.environ.get('CODEX_HOME') or
                                               (Path.home() / '.codex')).resolve())
            if cwd:
                record['cwd'] = cwd
            statedir.write_atomic(path, json.dumps(record) + '\n')


def background_state(session):
    records = [statedir.read_json(path, {}) for path in session_paths(session)]
    if not records:
        return 'unknown'
    record = max(records, key=lambda record: record.get('at', ''))
    if record.get('state') == 'stopped':
        return 'stopped'
    process = record.get('process', {})
    if not process.get('identity') or statedir.process_identity(process.get('pid')) != process['identity']:
        return 'unknown'
    state = record.get('state')
    return state if state in ('working', 'idle') else 'unknown'


def has_executor():
    if os.environ.get('MMW_NATIVE_TOOLS') != '1':
        return False
    try:
        os.fstat(3)
        os.fstat(4)
    except OSError:
        return False
    return True


def native(operation, arguments):
    if not has_executor():
        raise Refusal('this operation needs the runner tool executor; obtain it with '
                      'models.py executor and run the command through that executor')
    ident = str(uuid.uuid4())
    request = {'id': ident, 'operation': operation, 'arguments': arguments}
    os.write(3, (PREFIX + json.dumps(request) + '\n').encode())
    deadline = time.monotonic() + RPC_TIMEOUT
    line = bytearray()
    while not line.endswith(b'\n'):
        ready, _, _ = select.select([4], [], [], max(0, deadline - time.monotonic()))
        if not ready:
            raise Refusal('the native executor did not return a receipt; inspect the App before retrying')
        value = os.read(4, 1)
        if not value:
            raise Refusal('the native executor closed before returning a receipt; inspect the App')
        line.extend(value)
    response = json.loads(line)
    if response.get('id') != ident:
        raise Refusal('the native receipt identifies a different operation; nothing was confirmed')
    if not response.get('ok'):
        raise Refusal(str(response.get('error') or 'the native operation was refused'))
    result = response.get('result')
    if not isinstance(result, dict) or not SESSION.fullmatch(str(result.get('session', ''))):
        raise Refusal('the native operation returned no valid session identity')
    if operation != 'start' and result['session'] != arguments['session']:
        raise Refusal('the native receipt identifies a different session; nothing was confirmed')
    return result


@contextmanager
def public_server(command, environment):
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, env=environment) as server:
        def request(ident, method, params):
            packet = json.dumps({'id': ident, 'method': method, 'params': params}).encode() + b'\n'
            server.stdin.write(packet)
            server.stdin.flush()
            deadline = time.monotonic() + RPC_TIMEOUT
            line = bytearray()
            while True:
                ready, _, _ = select.select([server.stdout], [], [], max(0, deadline - time.monotonic()))
                if not ready:
                    raise TimeoutError('Codex public API receipt timed out')
                value = os.read(server.stdout.fileno(), 1)
                if not value:
                    raise ConnectionError('Codex public API connection closed')
                line.extend(value)
                if value != b'\n':
                    continue
                response = json.loads(line)
                line.clear()
                if response.get('id') == ident:
                    return response
        try:
            initialized = request(1, 'initialize', {
                'clientInfo': {'name': 'mmw_runner', 'version': '1'},
                'capabilities': {'experimentalApi': True}})
            if 'error' in initialized:
                raise Refusal('Codex public API refused initialization')
            server.stdin.write(b'{"method":"initialized"}\n')
            server.stdin.flush()
            yield request
        finally:
            server.stdin.close()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.terminate()
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


def prepare(args):
    cwd = str(Path(args.cwd).resolve(strict=True))
    params = {'cwd': cwd, 'ephemeral': False}
    if args.model and args.model != 'inherit':
        params['model'] = args.model
    if args.effort not in ('', 'inherit', '—', '-'):
        params['config'] = {'model_reasoning_effort': args.effort}
    if args.skip_approval:
        params.update(approvalPolicy='never', sandbox='danger-full-access')
    with public_server([binary(), 'app-server'], dict(os.environ)) as request:
        response = request(3, 'thread/start', params)
        if 'error' in response:
            raise Refusal('Codex refused the independent chat: ' + str(response['error']))
        result = response['result']
        thread = result['thread']
        if thread['cwd'] != cwd or (args.skip_approval and (
                result['approvalPolicy'] != 'never' or result['sandbox']['type'] != 'dangerFullAccess')):
            raise Refusal('Codex did not retain the requested directory and startup permissions')
        named = request(4, 'thread/name/set', {'threadId': thread['id'], 'name': args.title})
        if 'error' in named:
            print('codex-app: chat ' + thread['id'] + ' was prepared, but its title was not set',
                  file=sys.stderr)
        return {'session': thread['id'], 'cwd': cwd}


def queue_message(session, message):
    records = [statedir.read_json(path, {}) for path in session_paths(session)]
    record = max(records, key=lambda record: record.get('at', '')) if records else {}
    if record.get('binary') and record.get('code_home'):
        command = [record['binary'], 'app-server']
        environment = dict(os.environ, CODEX_HOME=record['code_home'])
    elif app_context():
        command = [binary(), 'app-server']
        environment = dict(os.environ)
    else:
        print('codex-app: no recorded App transport for this session; inspect it in the App '
              'before sending from a detached process', file=sys.stderr)
        return 3
    try:
        with public_server(command, environment) as request:
            try:
                response = request(2, 'thread/queue/add', {
                    'threadId': session, 'clientUserMessageId': 'mmw-wake-' + str(uuid.uuid4()),
                    'input': [{'type': 'text', 'text': message}]})
            except (OSError, ValueError):
                return 4
            if 'result' in response and response['result'].get('queuedSubmission'):
                return 4
            error = response.get('error', {})
            if error.get('code') in (-32600, -32603) and any(
                    text in str(error.get('message', '')).lower()
                    for text in ('thread not found', 'no rollout found', 'thread is archived')):
                return 2
            return 3 if 'error' in response else 4
    except (OSError, ValueError):
        return 3


def await_wake(repo, session):
    if not has_executor():
        raise Refusal('waiting needs the runner tool executor')
    if session != os.environ.get('CODEX_THREAD_ID'):
        raise Refusal('wait for wakes in the calling App chat')
    import relay
    ident = 1
    with public_server([binary(), 'app-server'], dict(os.environ)) as request:
        while True:
            cursor = None
            notified = 0
            while True:
                ident += 1
                response = request(ident, 'thread/queue/list', {
                    'threadId': session, 'cursor': cursor, 'limit': 100})
                if 'error' in response:
                    raise Refusal('could not read pending App notifications: ' + str(response['error']))
                page = response['result']
                for item in page['data']:
                    if not item.get('clientUserMessageId', '').startswith('mmw-wake-'):
                        continue
                    inputs = item.get('input', [])
                    if len(inputs) != 1 or inputs[0].get('type') != 'text':
                        continue
                    text = inputs[0]['text']
                    ticket = re.fullmatch(r'#\d+ ([a-z.]+)', text)
                    if not ((ticket and ticket[1] in relay.WAKES) or
                            re.fullmatch(r'brief [A-Za-z0-9_-]+ done', text) or
                            text.startswith('watchdog:')):
                        continue
                    receipt = native('send', {'session': session, 'text': text})
                    if receipt.get('accepted') is not True:
                        raise Refusal('App did not accept the pending notification')
                    ident += 1
                    deleted = request(ident, 'thread/queue/delete', {
                        'threadId': session, 'queuedSubmissionId': item['id']})
                    if not deleted.get('result', {}).get('deleted'):
                        raise Refusal('notification was sent, but its pending App copy was not removed; '
                                      'inspect the queue before sending it again')
                    print(text, flush=True)
                    notified += 1
                cursor = page.get('nextCursor')
                if not cursor:
                    break
            if notified:
                return 0
            if not relay.read_watches(statedir.state_dir(repo)):
                print('codex-app: no MMW watch remains open', file=sys.stderr)
                return 3
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='verb', required=True)
    for verb in ('start', 'prepare'):
        start = commands.add_parser(verb)
        for name in ('host', 'model', 'effort', 'cwd', 'prompt', 'title'):
            start.add_argument('--' + name, default='')
        start.add_argument('--env', action='append', default=[])
        start.add_argument('--skip-approval', action='store_true')
    for verb in ('state', 'liveness', 'stop'):
        commands.add_parser(verb).add_argument('session')
    send = commands.add_parser('send')
    send.add_argument('session')
    send.add_argument('text')
    commands.add_parser('self')
    commands.add_parser('available')
    waiting = commands.add_parser('await-wake')
    waiting.add_argument('--repo', required=True)
    waiting.add_argument('--session', required=True)
    for verb in ('catalog-models', 'catalog-version'):
        commands.add_parser(verb).add_argument('host', choices=('codex',))
    hook = commands.add_parser('hook')
    hook.add_argument('state', choices=('working', 'idle', 'unknown'))
    args = parser.parse_args()
    if args.verb == 'prepare':
        print(json.dumps(prepare(args)))
    elif args.verb == 'await-wake':
        return await_wake(args.repo, args.session)
    elif args.verb == 'catalog-version':
        print(subprocess.check_output([binary(), '--version'], text=True).strip())
    elif args.verb == 'catalog-models':
        import models
        print(json.dumps(models._parse_codex_model_list(models._codex_model_list(binary()))))
    elif args.verb == 'available':
        print(binary())
    elif args.verb == 'self':
        if not app_context():
            return 3
        session = os.environ['CODEX_THREAD_ID']
        repo = os.environ.get('GH_REPO')
        observe(session, repo=repo, cwd=os.getcwd())
        print(session)
    elif args.verb == 'hook':
        if os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') and os.environ.get('CODEX_APP_TOOLS_PIPE_PATH'):
            payload = json.loads(sys.stdin.read() or '{}')
            session = payload.get('session_id') or os.environ.get('CODEX_THREAD_ID')
            if session:
                observe(session, args.state, force=args.state == 'working')
    elif args.verb == 'start':
        if not all((args.host, args.model, args.cwd, args.prompt)):
            raise Refusal('start needs host, model, an existing directory and an initial prompt')
        if args.host != 'codex':
            raise Refusal('this runner starts the codex host; choose a Codex model row')
        cwd = str(Path(args.cwd).resolve(strict=True))
        environment = dict(value.split('=', 1) for value in args.env)
        extra = set(environment) - {'GH_REPO', 'MMW_SPEC', 'MMW_TICKET'}
        if extra:
            raise Refusal('unsupported native startup environment: ' + ', '.join(sorted(extra)))
        environment['MMW_HOME'] = str(statedir.home())
        if os.environ.get('MMW_RUNNER'):
            environment['MMW_RUNNER'] = os.environ['MMW_RUNNER']
        context = ('MMW skills for this session: ' + str(HERE.parents[2]) +
                   '. Resolve MMW skill names in this directory.\nMMW command environment: ' +
                   ' '.join(key + '=' + shlex.quote(value) for key, value in environment.items()))
        response = native('start', {'cwd': cwd, 'helper': str(Path(__file__).resolve()),
            'skip_approval': args.skip_approval,
            'model': args.model, 'effort': args.effort, 'prompt': context + '\n\n' + args.prompt,
            'title': ' '.join(filter(None, (environment.get('GH_REPO'), args.title)))})
        session = response['session']
        observe(session, 'working', repo=environment.get('GH_REPO'), cwd=cwd, force=True)
        print(session)
    elif args.verb == 'send':
        if background_state(args.session) == 'stopped':
            return 2
        if has_executor():
            response = native('send', {'session': args.session, 'text': args.text})
            return 0 if response.get('accepted') is True else 3
        return queue_message(args.session, args.text)
    elif args.verb == 'stop':
        if has_executor() or background_state(args.session) != 'stopped':
            response = native('stop', {'session': args.session})
            if response.get('stopped') is not True:
                raise Refusal('the native executor did not confirm a stopped chat')
            observe(args.session, 'stopped')
    else:
        if has_executor():
            response = native('state', {'session': args.session})
            state = {'active': 'working', 'idle': 'idle'}.get(response.get('state'))
            if state:
                observe(args.session, state, repo=os.environ.get('GH_REPO'),
                        cwd=response.get('cwd'), force=True)
            else:
                state = 'stopped' if background_state(args.session) == 'stopped' else 'unknown'
        else:
            state = background_state(args.session)
        if args.verb == 'state':
            print(state)
        else:
            print('alive' if state in ('working', 'idle') else state)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('codex-app: ' + str(error), file=sys.stderr)
        sys.exit(1)
