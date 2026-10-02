#!/usr/bin/env python3
"""Disposable installed MMW, tracker and consuming Git origin for a night rehearsal.

Use ``with Rehearsal(source, ref) as night``. ``build()`` alone only installs and
seeds the repositories: it never opens a watch or starts the product. The later
night test releases recorded agent starts and injects watchdog rounds, leaving
the background relay on its production interval. relay_once() is only for times
without a live relay lock holder. Commands resolve from the disposable installed-root.
"""

from __future__ import annotations

import fcntl
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fake_gh import atomic_write, log_call
from fake_orca import clean_env, process_command, runner_commands, stop, terminate
from stand_in_agent import load

HERE = Path(__file__).resolve().parent


def _processes():
    for line in subprocess.check_output(['ps', '-axo', 'pid=,command='], text=True).splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) == 2:
            yield int(fields[0]), fields[1]


class Rehearsal:
    repository = 'sample/rehearsal'

    def __init__(self, source=None, ref='HEAD'):
        self.source = Path(source or HERE.parents[2]).resolve()
        self.ref = ref
        self.root = Path(tempfile.mkdtemp(prefix='mmw-night-rehearsal-')).resolve()
        self.home = self.root / 'home'
        self.clone = self.root / 'installed-clone'
        self.origin = self.root / (self.repository + '.git')
        self.consumer = self.root / 'consumer'
        self.bin = self.root / 'bin'
        self.gh_state = self.root / 'gh.json'
        self.orca_state = self.root / 'orca'
        self.pids = []
        self.closed = False
        self.built = False
        self.env = clean_env(os.environ)
        for key in list(self.env):
            if key.startswith(('GIT_', 'RETRO_')):
                self.env.pop(key)
        self.env.update(HOME=str(self.home), MMW_HOME=str(self.home / '.mmw'),
                        MMW_V2_HOME=str(self.home), TMPDIR=str(self.root / 'tmp'),
                        XDG_CONFIG_HOME=str(self.home / '.config'),
                        XDG_CACHE_HOME=str(self.home / '.cache'),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        PATH=str(self.bin) + os.pathsep + os.defpath,
                        MMW_FAKE_GH_STATE=str(self.gh_state), MMW_FAKE_GH_LOG=str(self.root / 'gh.log'),
                        MMW_FAKE_ORCA_STATE=str(self.orca_state), MMW_FAKE_ORCA_LOG=str(self.root / 'orca.log'),
                        MMW_FAKE_NMEM_STATE=str(self.root / 'nmem.json'),
                        MMW_FAKE_HELP=str(self.root / 'help.json'), MMW_FAKE_LOG=str(self.root / 'boundary.log'),
                        MMW_FAKE_AGENT_PAUSED='1', RETRO_NMEM_STATE=str(self.root / 'memories.json'),
                        RETRO_TRACE_PATH=str(self.root / 'memory-trace.jsonl'))
        if os.environ.get('MMW_LEASE_PORT_BASE'):
            self.env['MMW_LEASE_PORT_BASE'] = os.environ['MMW_LEASE_PORT_BASE']

    def __enter__(self):
        result = self.build()
        if result.returncode:
            self.close()
            raise RuntimeError(result.stderr + result.stdout)
        return self

    def __exit__(self, *exc):
        self.close()

    def run(self, command, *, cwd=None, input=None, timeout=120):
        return subprocess.run([str(arg) for arg in command], cwd=cwd or self.consumer,
                              env=self.env, input=input, capture_output=True, text=True, timeout=timeout)

    def checked(self, command, **kwargs):
        result = self.run(command, **kwargs)
        if result.returncode:
            raise RuntimeError(f'COMMAND FAILED {result.returncode}: {command}\n{result.stderr}\n{result.stdout}')
        return result.stdout.strip()

    def gh(self, *args, input=None):
        return self.run(['gh', *args], cwd=self.consumer if self.consumer.exists() else self.root, input=input)

    def orca(self, *args):
        return self.run(['orca', *args], cwd=self.consumer)

    def _wrapper(self, name, program, *args):
        target = self.bin / name
        target.write_text('#!/bin/sh\nexec ' + ' '.join(shlex.quote(str(arg)) for arg in
                          (sys.executable, program, *args)) + ' "$@"\n')
        target.chmod(0o755)

    def _boundaries(self):
        self.bin.mkdir()
        self.home.mkdir()
        (self.root / 'tmp').mkdir()
        self.orca_state.mkdir()
        (self.bin / 'python3').symlink_to(sys.executable)
        for name in ('node', 'uv'):
            executable = shutil.which(name)
            if executable is None:
                raise RuntimeError(f'rehearsal needs {name} on the test process PATH')
            (self.bin / name).symlink_to(executable)
        for name, source in (('gh', 'fake_gh.py'), ('orca', 'fake_orca.py')):
            self._wrapper(name, HERE / source)
        for name in ('nmem', 'paseo', 'herdr', 'launchctl'):
            self._wrapper(name, HERE / 'rehearsal.py', '_boundary', name)
        atomic_write(self.gh_state, {'repository': self.repository, 'issues': {}, 'next_comment': 5000})
        atomic_write(self.root / 'nmem.json', {'spaces': {
            'mmw-toolbox': {'id': 'mmw-toolbox', 'name': 'MMW Toolbox',
                            'defaultRetrievalMode': 'strict', 'sharedSpaceIds': []},
            'sample__rehearsal': {'id': 'sample__rehearsal', 'name': self.repository,
                                  'defaultRetrievalMode': 'shared',
                                  'sharedSpaceIds': ['mmw-toolbox']}},
            'agents': {f'mmw-{role}': {'id': f'mmw-{role}', 'displayName': 'MMW ' + role.title(),
                                      'role': role, 'defaultSpaceId': 'mmw-toolbox'}
                       for role in ('worker', 'reviewer')}})
        atomic_write(self.root / 'memories.json', {'memories': {}, 'calls': []})
        nodog = self.root / 'no-watchdog.py'
        nodog.write_text('raise SystemExit(0)\n')
        self.env['MMW_WATCHDOG_PY'] = str(nodog)

    def build(self):
        if self.built:
            raise RuntimeError('rehearsal already built')
        try:
            self._boundaries()
            head = self.checked(['git', '-C', self.source, 'rev-parse', self.ref], cwd=self.root)
            self.checked(['git', 'clone', '--local', '--no-checkout', self.source, self.clone], cwd=self.root)
            self.checked(['git', '-C', self.clone, 'checkout', '--detach', head], cwd=self.root)
            self.installed = self.clone / 'mmw-v2'
            locations = load('rehearsal_locations', self.installed / 'skills' / 'mmw' / 'scripts' / 'locations.py')
            self.scripts = self.installed / 'skills' / locations.MODE_SCRIPTS
            self.env['MMW_FAKE_ADAPTER_ROOT'] = str(self.installed)
            self.env['MMW_FAKE_RETRO_NMEM'] = str(self.installed / 'tests' / 'retro' / 'fake_nmem.py')
            catalog = {}
            defaults = json.loads((self.scripts.parent / 'hosts.json').read_text())['defaults']
            for row in defaults:
                model = row['model'].split('[', 1)[0]
                offering = {'id': model.replace(' ', '-'), 'name': model,
                            'thinkingOptionIds': ['off', 'low', 'medium', 'high', 'xhigh', 'max']}
                rows = catalog.setdefault(row['host'], [])
                if not any(item['id'] == offering['id'] for item in rows):
                    rows.append(offering)
            atomic_write(self.root / 'host-catalog.json', catalog)
            self.env['MMW_HOST_CATALOG'] = str(self.root / 'host-catalog.json')
            # These are the documented help probes, not permissive command substitutes.
            help_rows = {}
            for name in ('paseo', 'herdr'):
                help_rows[name] = runner_commands(self.scripts / 'runners' / f'{name}.sh')
            atomic_write(self.root / 'help.json', help_rows)
            install = self.run(['bash', self.installed / 'install.sh'], cwd=self.clone, timeout=600)
            (self.root / 'install.stdout').write_text(install.stdout)
            (self.root / 'install.stderr').write_text(install.stderr)
            if install.returncode:
                return install
            marker = self.home / '.mmw' / 'installed-root'
            if Path(marker.read_text().strip()).resolve() != self.installed.resolve():
                raise RuntimeError('installed-root does not name the disposable clone')
            self.dispatch = self.scripts / 'dispatch.sh'
            self.statedir = load('rehearsal_statedir', self.scripts / 'statedir.py')
            self.events_module = load('rehearsal_events', self.scripts / 'events.py')
            if self.checked([sys.executable, self.scripts / 'models.py', 'runner'], cwd=self.clone) != 'orca':
                raise RuntimeError('disposable models.json did not select orca')
            self._consumer()
            self._issues()
            self.built = True
            return subprocess.CompletedProcess(['rehearsal', 'build'], 0,
                                                f'REHEARSAL BUILT {head} spec #{self.spec}\n', '')
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            return subprocess.CompletedProcess(['rehearsal', 'build'], 2, '', f'REHEARSAL BUILD FAILED {exc}\n')

    def _consumer(self):
        self.checked(['git', 'init', '--bare', self.origin], cwd=self.root)
        self.checked(['git', 'clone', self.origin, self.consumer], cwd=self.root)
        for key, value in (('user.email', 'rehearsal@example.invalid'), ('user.name', 'Rehearsal'),
                           ('commit.gpgsign', 'false'), ('core.hooksPath', str(self.root / 'no-hooks'))):
            self.checked(['git', 'config', key, value])
        self.checked(['git', 'checkout', '-b', 'project'])
        (self.consumer / '.mmw').mkdir()
        (self.consumer / 'docs' / 'agents').mkdir(parents=True)
        (self.consumer / 'docs' / 'specs').mkdir()
        target = {'start': 'true', 'stop': 'true',
                  'discover': "python3 -c 'import json; print(json.dumps({\"origin\": \"http://127.0.0.1\", \"instance\": \"rehearsal\"}))'",
                  'stories': 'true', 'leaves_machine': [], 'harness_markers': [], 'delivery': 'commit'}
        atomic_write(self.consumer / '.mmw' / 'target.json', target)
        (self.consumer / 'docs' / 'agents' / 'issue-tracker.md').write_text(
            '# Issue tracker: GitHub\n\nRehearsal tracker: sample/rehearsal. Use gh for all operations.\n\n'
            '## Three label sets\n\nLayer: mmw:spec, mmw:ticket, mmw:child.\n'
            'Queue: ready-for-agent, needs-triage. Grade: senior-worker.\n')
        (self.consumer / 'README.md').write_text('Isolated MMW consuming repository.\n')

    def _create(self, title, body, *extra):
        url = self.checked(['gh', 'issue', 'create', '--title', title, '--body-file', '-', *extra], input=body)
        return int(url.rsplit('/', 1)[-1])

    def _issues(self):
        spec_body = ('## Problem Statement\nExercise an isolated night.\n\n## Solution\n'
                'Three independently checkable tickets, with B blocked by A.\n\n'
                '## Testing Decisions\nCheck committed ticket artifacts.\n\n## Out of Scope\nReal models and services.\n')
        self.spec = self._create('Rehearsal spec', spec_body, '--label', 'mmw:spec')
        self.tickets = []
        for title in ('A', 'B', 'C'):
            # The fake tracker allocates consecutive numbers, also known to the CHECK.
            number = self.spec + len(self.tickets) + 1
            body = self._ticket_body(self.spec, number)
            ticket = self._create(title, body, '--parent', str(self.spec),
                                  '--label', 'mmw:ticket,ready-for-agent,senior-worker')
            if ticket != number:
                raise RuntimeError('tracker allocated an unexpected ticket number')
            self.tickets.append(ticket)
        ident = self.checked(['gh', 'api', f'repos/{{owner}}/{{repo}}/issues/{self.tickets[0]}', '--jq', '.id'])
        self.checked(['gh', 'api', '--method', 'POST',
                      f'repos/{{owner}}/{{repo}}/issues/{self.tickets[1]}/dependencies/blocked_by',
                      '-F', 'issue_id=' + ident])
        self.other_spec = self._create('Unwatched spec', spec_body, '--label', 'mmw:spec')
        self.adopted_ticket = self._create('D', self._ticket_body(self.other_spec, self.other_spec + 1),
                                           '--parent', str(self.other_spec),
                                           '--label', 'mmw:ticket,ready-for-agent,senior-worker')
        self.env['MMW_FAKE_FINDING_TICKET'] = str(self.tickets[2])
        (self.consumer / 'docs' / 'specs' / 'rehearsal.md').write_text(
            f'# Rehearsal spec #{self.spec}\n\nTickets: ' + ', '.join(f'#{n}' for n in self.tickets) + '\n')
        self.checked(['git', 'add', 'README.md', '.mmw/target.json', 'docs'])
        self.checked(['git', 'commit', '-m', 'Seed consuming repository and rehearsal spec'])
        self.checked(['git', 'push', 'origin', 'project'])
        self.checked(['git', 'branch', 'main'])
        self.checked(['git', 'push', 'origin', 'main'])
        self.checked(['git', '--git-dir', self.origin, 'symbolic-ref', 'HEAD', 'refs/heads/main'])
        self.checked(['git', 'remote', 'set-head', 'origin', 'main'])
        self.checked(['git', 'checkout', '-b', 'night'])
        self.checked(['git', 'config', 'branch.night.vscode-merge-base', 'project'])
        self.checked(['git', 'push', 'origin', 'night'])

    @staticmethod
    def _ticket_body(spec, number):
        return (f'## Parent\n#{spec}\n\n## What to build\n'
                f'Write ticket-{number}.txt with the ticket implementation.\n\n'
                '## Read first\nREADME.md\n\n## Seam\nThe consuming repository artifact.\n\n'
                f'## Owns\n- ticket-{number}.txt\n\n## Acceptance criteria\n'
                f'- [ ] AC1: The implementation artifact exists\n'
                f'  CHECK: test -f ticket-{number}.txt && printf "TICKET {number} OK\\n"\n'
                f'  EXPECT: /^TICKET {number} OK$/m\n  EVIDENCE: pending\n')

    def release_agent(self, handle):
        """Allow the first turn only after the fixture has recorded dispatch's start."""
        inbox = self.orca_state / f'{handle}.inbox'
        if not inbox.is_file():
            raise RuntimeError(f'unknown rehearsal terminal {handle}')
        inbox.with_suffix('.go').touch()

    def terminals(self):
        path = self.orca_state / 'terminals.json'
        return json.loads(path.read_text()) if path.exists() else []

    def events(self, number, name=None):
        state = json.loads(self.gh_state.read_text())
        result = []
        for comment in state['issues'][str(number)]['comments']:
            kind, event = self.events_module.parse(comment['body'])
            if kind == 'unreadable':
                raise RuntimeError(f'#{number}: {event}')
            if kind == 'event' and (name is None or event['event'] == name):
                result.append(event)
        return result

    def release_started_agents(self, *, hold=()):
        """Release only sessions whose real started event is visible in the tracker."""
        state = json.loads(self.gh_state.read_text())
        started = {event['session'] for number in state['issues']
                   for event in self.events(number)
                   if event['event'] in ('worker.started', 'reviewer.started')}
        for row in self.terminals():
            if row['handle'] in started and row['handle'] not in hold:
                self.release_agent(row['handle'])

    def relay_once(self):
        return self.run([sys.executable, self.scripts / 'relay.py', 'run', '--repo', self.repository, '--once'])

    def watchdog_once(self):
        return self.run([sys.executable, self.scripts / 'watchdog.py', 'run', '--repo', self.repository,
                         '--once', '--silence', '1', '--idle', '2'])

    def turn_guard(self, payload=None, *, cwd=None):
        launcher = self.home / '.mmw' / 'bin' / 'hook-launcher'
        return self.run([sys.executable, launcher, 'turn-guard', 'stop', 'claude'], cwd=cwd,
                        input=json.dumps(payload or {'hook_event_name': 'Stop',
                                                     'cwd': str(cwd or self.consumer),
                                                     'stop_hook_active': False}))

    def _stop_pid(self, pid):
        if not process_command(pid):
            return
        if str(self.root) not in process_command(pid):
            raise RuntimeError(f'pid {pid} is not owned by this rehearsal')
        if pid not in self.pids:
            self.pids.append(pid)
        terminate(lambda: bool(process_command(pid)), lambda sig: os.kill(pid, sig), f'owned pid {pid}')

    def stop_background_relay(self):
        state = self.home / '.mmw' / 'state' / self.repository.replace('/', '__')
        lock = state / 'relay.lock'
        if lock.exists():
            holder = self.statedir.holder(lock)
            if holder:
                self._stop_pid(holder['pid'])

    def remaining_processes(self):
        return [pid for pid, command in _processes()
                if str(self.root) in command and pid != os.getpid()]

    def close(self):
        if self.closed:
            return
        for row in self.terminals():
            if row['pid'] not in self.pids:
                self.pids.append(row['pid'])
            stop(row)
        state = self.home / '.mmw' / 'state'
        if state.exists() and hasattr(self, 'statedir'):
            for lock in state.glob('*/*.lock'):
                if lock.name in ('relay.lock', 'watchdog.lock'):
                    holder = self.statedir.holder(lock)
                    if holder:
                        self._stop_pid(holder['pid'])
        boards = self.home / '.mmw' / 'boards.json'
        if boards.exists():
            ports = json.loads(boards.read_text()).values()
            # Both the disposable checkout's server path and its registered port must match.
            server = str(self.installed / 'board' / 'server.py')
            for pid, command in _processes():
                if server in command and any('--port ' + str(port) in command for port in ports):
                    self._stop_pid(pid)
        for pid in self.remaining_processes():
            self._stop_pid(pid)
        if self.remaining_processes():
            raise RuntimeError('rehearsal cleanup left owned processes')
        last = None
        for _ in range(8):
            if not self.root.exists():
                self.closed = True
                return
            try:
                shutil.rmtree(self.root)
            except OSError as exc:
                last = exc
                time.sleep(0.1)
        if self.root.exists():
            raise RuntimeError(f'rehearsal cleanup could not delete {self.root}: {last}')
        self.closed = True


def _nmem(args):
    args = [arg for arg in args if arg != '--json']
    path = Path(os.environ['MMW_FAKE_NMEM_STATE'])
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(path.read_text())
        command = args[:2]
        if command[0] == 'memories':
            # Use the existing stateful retro fake, with the same private Memory file.
            if command == ['memories', 'search'] and '--' in args:
                query = args[args.index('--') + 1]
                args = args[:2] + [query] + args[2:args.index('--')]
            return subprocess.call([sys.executable, os.environ['MMW_FAKE_RETRO_NMEM'], *args])
        def opt(name, default=''):
            return args[args.index(name) + 1] if name in args else default
        if command in (['spaces', 'show'], ['agents', 'show']):
            row = state[command[0]].get(args[2])
            if row is None:
                print('not found', file=sys.stderr)
                return 1
        elif command == ['spaces', 'create']:
            row = {'id': opt('--id'), 'name': args[2],
                   'defaultRetrievalMode': opt('--retrieval-mode'),
                   'sharedSpaceIds': [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == '--share-with']}
            state['spaces'][row['id']] = row
        elif command in (['spaces', 'update'], ['agents', 'set']):
            row = state[command[0]][args[2]]
            mapping = ({'--name': 'name', '--retrieval-mode': 'defaultRetrievalMode'}
                       if command[0] == 'spaces' else
                       {'--name': 'displayName', '--role': 'role', '--default-space': 'defaultSpaceId'})
            for flag, field in mapping.items():
                if flag in args:
                    row[field] = opt(flag)
            if command[0] == 'spaces':
                row['sharedSpaceIds'] = [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == '--share-with']
        elif command == ['agents', 'enroll']:
            row = {'id': args[2], 'displayName': opt('--name'), 'role': opt('--role'),
                   'defaultSpaceId': opt('--default-space')}
            state['agents'][row['id']] = row
        elif command == ['context', 'read']:
            row = {'active_space': {'primary_space_id': opt('--space')},
                   'rule_stack': {key: [] for key in ('global', 'owner', 'space', 'agent')}, 'warnings': []}
        elif args == ['config', 'mcp', 'show', '--host', 'cursor']:
            row = {'config': {'mcpServers': {'nowledge-mem': {
                'type': 'http', 'url': 'https://mem.example.invalid/mcp', 'headers': {}}}}}
        else:
            print('UNHANDLED nmem ' + ' '.join(args), file=sys.stderr)
            return 2
        atomic_write(path, state)
        print(json.dumps(row))
        return 0


def boundary(name, args):
    code = _answer_boundary(name, args)
    log_call(Path(os.environ['MMW_FAKE_LOG']), args if code != 2 else [name, *args],
             code == 2, program=name)
    return code


def _answer_boundary(name, args):
    if name == 'nmem':
        return _nmem(args)
    if name == 'launchctl':
        return 0
    if name in ('paseo', 'herdr'):
        if args in (['--help'], ['-h']):
            print(f'Usage: {name} <command>')
            return 0
        if args and args[-1] in ('--help', '-h'):
            command = ' '.join(args[:-1])
            rows = json.loads(Path(os.environ['MMW_FAKE_HELP']).read_text())[name]
            if command in rows:
                print(f'Usage: {name} {command} ' + ' '.join(rows[command]))
                return 0
    print('UNHANDLED ' + name + ' ' + ' '.join(args), file=sys.stderr)
    return 2


if __name__ == '__main__':
    if sys.argv[1:2] == ['_boundary']:
        raise SystemExit(boundary(sys.argv[2], sys.argv[3:]))
    raise SystemExit('Import Rehearsal from the night rehearsal test; this module does not run a night.')
