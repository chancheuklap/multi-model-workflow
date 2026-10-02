#!/usr/bin/env python3
"""Orca CLI boundary with real stand-in processes, private inboxes and receipts.

Only terminal processes recorded in MMW_FAKE_ORCA_STATE can be stopped. The
command is parsed, never executed: a real model must not start in a rehearsal.
"""

from __future__ import annotations

import fcntl
import json
import os
import shlex
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

from fake_gh import Unhandled, atomic_write, log_call
from stand_in_agent import load

HERE = Path(__file__).resolve().parent


def runner_commands(adapter):
    rows = {}
    for line in adapter.read_text().splitlines():
        if line.startswith('# MMW_USES:'):
            words = line.split(':', 1)[1].split()
            command = ' '.join(word for word in words if not word.startswith('-'))
            rows[command] = tuple(word for word in words if word.startswith('-'))
    return rows


root = Path(os.environ.get('MMW_FAKE_ADAPTER_ROOT', HERE.parents[1]))
locations = load('fake_orca_locations', root / 'skills' / 'mmw' / 'scripts' / 'locations.py')
COMMAND_FLAGS = {command: tuple(flag.removeprefix('--') for flag in flags)
                 for command, flags in runner_commands(
                     root / 'skills' / locations.MODE_SCRIPTS / 'runners' / 'orca.sh').items()}
COMMAND_FLAGS.update({
    'project setups': ('json',),
    'repo list': ('json',),
    'agent-context': ('json',),
})


def clean_env(env):
    """Drop outer host identity and test controls; callers add their private controls."""
    prefixes = ('MMW_', 'NMEM_', 'PASEO_', 'ORCA_', 'HERDR_', 'GROK_', 'CURSOR_', 'PYTHON')
    exact = {'CODEX_HOME', 'PI_HOME', 'PI_CODING_AGENT_DIR'}
    return {key: value for key, value in env.items()
            if not key.startswith(prefixes) and key not in exact}


def process_command(pid):
    result = subprocess.run(['ps', '-p', str(pid), '-o', 'stat=', '-o', 'command='],
                            capture_output=True, text=True)
    line = result.stdout.strip().split(None, 1)
    return line[1] if len(line) == 2 and not line[0].startswith('Z') else ''


def alive(row):
    command = process_command(row['pid'])
    return str(HERE / 'stand_in_agent.py') in command and row['handle'] in command


def terminate(is_alive, send_signal, description):
    """Bounded shutdown after the caller verifies process ownership."""
    if not is_alive():
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            send_signal(sig)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + 5
        while is_alive() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not is_alive():
            return
    raise RuntimeError(f'{description} did not stop')


def stop(row):
    # The liveness predicate requires this fake's stand-in path and unique handle.
    terminate(lambda: alive(row), lambda sig: os.killpg(row['pid'], sig),
              f'stand-in {row["handle"]}')


def options(args, allowed):
    result = {}
    args = args.copy()
    while args:
        flag = args.pop(0)
        if not flag.startswith('--') or flag[2:] not in allowed:
            raise Unhandled()
        if flag in ('--json', '--enter'):
            result[flag] = True
        elif args:
            result[flag] = args.pop(0)
        else:
            raise Unhandled()
    return result


def line_prompt(command):
    words = shlex.split(command)
    if not words or words.pop(0) != 'exec':
        raise Unhandled()
    assignments = {}
    if words and words[0] == 'env':
        words.pop(0)
        while words and '=' in words[0] and not words[0].startswith('-'):
            key, value = words.pop(0).split('=', 1)
            assignments[key] = value
    if len(words) < 2 or Path(words[0]).name not in ('claude', 'codex', 'grok', 'cursor-agent'):
        raise Unhandled()
    prompt = words[-1]
    if '\n' in prompt or '\r' in prompt:
        raise Unhandled()
    return prompt, assignments


def answer(state, rows, command, opts):
    if command == 'agent-context':
        return {'schemaVersion': 1, 'commandCount': len(COMMAND_FLAGS),
                'commands': [{'command': key, 'flags': list(flags)}
                             for key, flags in COMMAND_FLAGS.items()]}, 0
    if command == 'project setups':
        return {'setups': []}, 0
    if command == 'repo list':
        return {'repos': []}, 0
    if command == 'worktree set':
        if '--worktree' not in opts or not ({'--issue', '--parent-worktree'} & opts.keys()):
            raise Unhandled()
        path = state / 'worktrees.json'
        worktrees = json.loads(path.read_text()) if path.exists() else {}
        worktrees.setdefault(opts['--worktree'], {}).update(opts)
        atomic_write(path, worktrees)
        return {}, 0
    if command == 'tab create':
        if not {'--url', '--worktree'} <= opts.keys():
            raise Unhandled()
        return {'tab': {'id': 'tab_' + uuid.uuid4().hex}}, 0
    if command == 'terminal create':
        if not {'--worktree', '--command', '--title'} <= opts.keys():
            raise Unhandled()
        prompt, assignments = line_prompt(opts['--command'])
        cwd = opts['--worktree'].removeprefix('path:')
        if not opts['--worktree'].startswith('path:') or not Path(cwd).is_dir():
            raise Unhandled()
        handle = 'term_' + uuid.uuid4().hex
        inbox = state / f'{handle}.inbox'
        inbox.write_text(prompt + '\n', encoding='utf-8')
        # Keep only this fixture's private environment, then the adapter's new identity.
        env = clean_env(os.environ)
        env.update({key: value for key, value in os.environ.items()
                    if key.startswith('MMW_FAKE_') or key in
                    ('MMW_HOME', 'MMW_V2_HOME', 'MMW_WATCHDOG_PY', 'MMW_LEASE_PORT_BASE',
                     'MMW_HOST_CATALOG') or key.startswith('RETRO_')})
        allowed = {'MMW_ROLE', 'MMW_TICKET', 'MMW_SPEC', 'MMW_TASK_SCOPE',
                   'NMEM_SPACE', 'NMEM_AGENT_ID'}
        env.update({key: value for key, value in assignments.items() if key in allowed})
        env['ORCA_TERMINAL_HANDLE'] = handle
        with (state / f'{handle}.stdout').open('w') as out, (state / f'{handle}.stderr').open('w') as err:
            child = subprocess.Popen([sys.executable, '-u', str(HERE / 'stand_in_agent.py'),
                                      '--handle', handle, '--inbox', str(inbox)],
                                     cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                     stdout=out, stderr=err, start_new_session=True)
        row = {'handle': handle, 'pid': child.pid, 'worktree': opts['--worktree'],
               'worktreeId': 'rehearsal::' + cwd, 'title': opts['--title'],
               'command': opts['--command']}
        rows.append(row)
        atomic_write(state / 'terminals.json', rows)
        return {'handle': handle, 'pid': child.pid, 'connected': True, 'writable': True}, 0
    if command == 'terminal list':
        return {'terminals': [{**row, 'connected': alive(row), 'writable': alive(row),
                               'status': 'running' if alive(row) else 'exited'} for row in rows],
                'truncated': False}, 0
    handle = opts.get('--terminal')
    row = next((row for row in rows if row['handle'] == handle), None)
    if row is None:
        return {'error': {'code': 'terminal_handle_stale', 'message': 'terminal_handle_stale'}}, 1
    if command == 'terminal close':
        row['healthyBeforeClose'] = alive(row)
        row['closed'] = True
        atomic_write(state / 'terminals.json', rows)
        stop(row)
        return {'closed': handle}, 0
    if command == 'terminal read':
        tail = []
        for suffix in ('stdout', 'stderr'):
            path = state / f'{handle}.{suffix}'
            if path.exists():
                tail.extend(path.read_text().splitlines()[-10:])
        return {'terminal': {'handle': handle, 'status': 'running' if alive(row) else 'exited',
                             'tail': tail}}, 0
    if command == 'terminal wait':
        condition = opts.get('--for')
        if condition not in ('exit', 'tui-idle'):
            raise Unhandled()
        running = alive(row)
        if running and condition == 'exit':
            return {'error': {'code': 'timeout', 'message': 'timeout'}}, 1
        return {'wait': {'handle': handle, 'condition': condition,
                         'satisfied': True, 'status': 'running' if running else 'exited'}}, 0
    if command == 'terminal send':
        text = opts.get('--text')
        if text is None or '\n' in text or '\r' in text:
            raise Unhandled()
        if not alive(row):
            return {'error': {'code': 'terminal_not_writable', 'message': 'terminal_not_writable'}}, 1
        with (state / f'{handle}.inbox').open('a', encoding='utf-8') as stream:
            stream.write(text + '\n')
        return {'send': {'handle': handle, 'accepted': True,
                         'prompt': {'stages': ['input_accepted', 'turn_started']}}, 'warnings': []}, 0
    raise Unhandled()


def main():
    args = sys.argv[1:]
    state = Path(os.environ['MMW_FAKE_ORCA_STATE'])
    state.mkdir(parents=True, exist_ok=True)
    log = Path(os.environ.get('MMW_FAKE_ORCA_LOG', state / 'calls.log'))
    command = ' '.join(args[:1] if args[:1] == ['agent-context'] else args[:2])
    with (state / 'state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if command not in COMMAND_FLAGS:
                raise Unhandled()
            count = 1 if command == 'agent-context' else 2
            opts = options(args[count:], COMMAND_FLAGS[command])
            path = state / 'terminals.json'
            rows = json.loads(path.read_text()) if path.exists() else []
            result, code = answer(state, rows, command, opts)
        except Unhandled:
            log_call(log, args, True, program='orca')
            print('UNHANDLED ' + ' '.join(args), file=sys.stderr)
            return 2
        log_call(log, args, program='orca')
    if command == 'agent-context':
        print(json.dumps(result))
    elif 'error' in result:
        print(json.dumps({'ok': False, **result}))
    else:
        print(json.dumps({'ok': True, 'result': result}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
