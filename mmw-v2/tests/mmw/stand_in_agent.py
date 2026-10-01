#!/usr/bin/env python3
"""Deterministic rehearsal agent: resolve pointers, ack wakes, run real mode commands.

ACTIONS is the only step/action table. Informational entries are explicit empty
sequences; an unknown role, step or operation fails. MMW_FAKE_AGENT_PAUSED=1 lets
rehearsal.release_agent() control the first turn after dispatch records its start.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ACTIONS = {
    'work-a-ticket': {
        'Adopted ticket': (('dispatch', 'adopt', '{n}'),),
        'Claim': (('ticket', '--claim'),),
        'Read yourself in': (('gh', 'issue', 'view', '{n}', '--json', 'title,body,parent'),),
        'Write the code': (('@write_code',),),
        'Integrate and run every criterion': (('dispatch', 'integrate', '{n}'),
                                              ('ticket', '--run-and-record-criteria')),
        'Post the decisions': (('@decisions',),),
        'Get reviewed': (('@review_round',),),
        'Run every criterion one final time': (('ticket', '--reverify', '--actor', 'worker'),),
        'Audit against the ticket': (('gh', 'issue', 'view', '{n}', '--json', 'body'),
                                     ('git', 'diff', '--exit-code', 'HEAD')),
        'Tell the touched tickets': (('ticket', '--touched'),),
        'Draft the closing comment': (('@draft',),),
        'Close out': (('ticket', '--closeout', '{draft}'),),
        'When the orchestrator resumes you': (('@where',),),
        'After the closeout of an adopted ticket': (),
        'When something else wakes you': (('@where',),),
        'While the product runs': (),
    },
    'review-a-ticket': {
        'Pin the diff': (('@report',),),
        'Active Rules': (),
    },
    'run-a-night': {
        'Check and open': (('dispatch', 'check', '{n}'), ('dispatch', 'open-night', '{n}')),
        'Lint the batch': (('verify', '{n}', '--lint'),),
        'Advance, then end your turn': (('dispatch', 'advance', '{n}'),),
        'Handle each wake': (('dispatch', 'status', '{n}'), ('dispatch', 'advance', '{n}')),
        'Closing pass': (('dispatch', 'findings', '{n}'), ('@resolve_findings',)),
        'Close the Memory records': (('@memory_decisions',),),
        'Reverify and summarize': (('dispatch', 'reverify', '{n}'),
                                   ('dispatch', 'close-night', '{n}', '--memory-decisions', '{memory}')),
        'Retro': (('@retro',),),
    },
    'land-one-ticket': {
        'Start the worker, then end your turn': (('dispatch', 'start', '{n}', 'worker'),),
        'Handle each wake': (('@one_ticket_wake',),),
        'Land': (('dispatch', 'land', '{n}'),),
    },
}
ROLE_PLAYBOOK = {'worker': 'work-a-ticket', 'adopting-worker': 'work-a-ticket',
                 'reviewer': 'review-a-ticket', 'night-orchestrator': 'run-a-night',
                 'one-ticket-orchestrator': 'land-one-ticket'}
WORKER_STEPS = ('Claim', 'Read yourself in', 'Write the code',
                'Integrate and run every criterion', 'Post the decisions', 'Get reviewed',
                'Run every criterion one final time', 'Audit against the ticket',
                'Tell the touched tickets', 'Draft the closing comment', 'Close out')
POINTER = re.compile(r'(?: · |: )?mmw ([\w-]+)#(.+?)(?:\. Data: [^\r\n]+)?\.?$')


class NoAction(RuntimeError):
    pass


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def installed_root():
    marker = Path(os.environ['MMW_HOME']) / 'installed-root'
    root = Path(marker.read_text().strip()).resolve()
    if not root.is_dir():
        raise RuntimeError(f'no installed checkout at {root}')
    return root


class Agent:
    def __init__(self, role, number, inbox=None):
        self.role = role
        self.number = number
        self.inbox = inbox
        self.root = None
        self.memory = ''
        self.draft_path = ''
        self.wake = ''
        self.resumed = False
        self.files = inbox.parent if inbox else Path(os.environ.get('MMW_FAKE_ORCA_STATE', '.'))
        self.files.mkdir(parents=True, exist_ok=True)

    def paths(self):
        if self.root is None:
            self.root = installed_root()
            self.locations = load('agent_locations', self.root / 'skills' / 'mmw' / 'scripts' / 'locations.py')
            skills = self.root / 'skills'
            self.dispatch = skills / self.locations.MODE_SCRIPTS / 'dispatch.sh'
            self.ticket = skills / self.locations.TICKET_STATE_PY
            self.verify = skills / self.locations.VERIFY_TICKET_PY
            self.events = load('agent_events', skills / self.locations.EVENTS_PY)

    def command(self, kind, *args, acceptable=(0,)):
        self.paths()
        if kind == 'dispatch':
            command = ['bash', str(self.dispatch), *args]
        elif kind == 'ticket':
            command = [sys.executable, str(self.ticket), str(self.number), *args]
        elif kind == 'verify':
            command = [sys.executable, str(self.verify), *args]
        elif kind == 'retro':
            # Installed skill links are created by the disposable install, not the host's.
            path = Path(os.environ['HOME']) / '.agents' / 'skills' / 'retro' / 'scripts' / 'retro.py'
            command = [sys.executable, str(path), *args]
        elif kind in ('git', 'gh'):
            command = [kind, *args]
        else:
            raise NoAction(f'NO ACTION {self.role} operation {kind}')
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        print(result.stdout, end='', flush=True)
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr, flush=True)
        if result.returncode not in acceptable:
            raise RuntimeError(f'COMMAND FAILED {result.returncode}: {command}')
        return result

    def step(self, title, *, follow=False):
        playbook = ROLE_PLAYBOOK.get(self.role)
        if playbook not in ACTIONS or title not in ACTIONS[playbook]:
            raise NoAction(f'NO ACTION {self.role} {title}')
        print(f'ACTION {self.role} {title}', flush=True)
        for action in ACTIONS[playbook][title]:
            op, *args = action
            if op.startswith('@'):
                method = getattr(self, op[1:], None)
                if method is None:
                    raise NoAction(f'NO ACTION {self.role} {title} operation {op}')
                if method() == 'wait':
                    return
            else:
                values = {'n': str(self.number), 'draft': self.draft_path, 'memory': self.memory}
                result = self.command(op, *(value.format(**values) for value in args),
                                      acceptable=(0, 3) if '--run-and-record-criteria' in args else (0,))
                if result.returncode == 3:
                    return
        if follow and title in WORKER_STEPS:
            index = WORKER_STEPS.index(title) + 1
            if index < len(WORKER_STEPS):
                self.step(WORKER_STEPS[index], follow=True)

    def write_code(self):
        path = Path(f'ticket-{self.number}.txt')
        path.write_text(f'ticket {self.number} implemented\n')
        self.command('git', 'add', str(path))
        self.command('git', 'commit', '-m', f'Implement rehearsal ticket #{self.number}')

    def decisions(self):
        path = self.files / f'decisions-{self.number}.md'
        path.write_text('## Decisions I made on my own\nNone\n\n## Outside Owns\nOutside Owns: None\n')
        self.command('ticket', '--decisions', str(path))

    def comments(self):
        return json.loads(self.command('gh', 'issue', 'view', str(self.number),
                                        '--json', 'comments').stdout)['comments']

    def review_round(self):
        comments = self.comments()
        newest = self.events.newest(comments, 'reviewer.started', 'reviewer.reported', 'reviewer.lost')
        if newest and newest['event'] == 'reviewer.started':
            return 'wait'
        if not newest or newest['event'] == 'reviewer.lost':
            self.command('dispatch', 'start', str(self.number), 'reviewer')
            return 'wait'
        self.command('dispatch', 'result', str(self.number), 'reviewer')
        report = self.events.newest(self.comments(), 'reviewer.reported')
        if not report:
            raise RuntimeError('review wake without reviewer.reported')
        # C's deliberately injected out-of-ticket finding exercises the real child command.
        if str(self.number) == os.environ.get('MMW_FAKE_FINDING_TICKET'):
            finding = self.files / f'finding-{self.number}.md'
            finding.write_text('Rehearsal out-of-ticket finding\n\n'
                               '## What to build\nRecord the deliberately injected finding.\n')
            self.command('ticket', '--open-child', 'finding', str(finding))

    def report(self):
        comments = self.comments()
        started = self.events.newest(comments, 'reviewer.started')
        if not started:
            raise RuntimeError('reviewer has no started event to pin its diff')
        base = started['payload']['base']
        head = self.command('git', 'rev-parse', 'HEAD').stdout.strip()
        self.command('git', 'diff', '--stat', base, head)
        outside = 'None'
        if str(self.number) == os.environ.get('MMW_FAKE_FINDING_TICKET'):
            outside = '- Tests [correctness] README.md:1 — deliberate rehearsal finding — source: rehearsal spec'
        report = self.files / f'review-{self.number}.md'
        report.write_text(f'REVIEW {base}..{head}\n\n## In-ticket\nNone\n\n'
                          f'## Out-of-ticket\n{outside}\n\n## Active Rules\nNone\n')
        self.command('ticket', '--review', str(report))

    def draft(self):
        result = self.command('ticket', '--closing-draft')
        match = re.search(r'^DRAFT: wrote (.+)$', result.stdout, re.M)
        if not match:
            raise RuntimeError('closing-draft returned no path')
        self.draft_path = match.group(1)
        path = Path(self.draft_path)
        text = path.read_text()
        # Any findings or green-before-work rows require judgement, not a blanket fill.
        if re.search(r'(?:In-ticket|Green before work):?\s*\n(?:-.*)?<fill>', text):
            raise RuntimeError('rehearsal draft needs an explicit finding or baseline answer')
        text = text.replace('skipped: <fill>', 'skipped: None')
        text = text.replace('\n<fill>\n', '\nNone\n')
        if '<fill>' in text:
            raise RuntimeError('unanswered rehearsal draft field')
        self.paths()
        text += '\n' + self.locations.AUDITED_LINE + ' yes\n'
        path.write_text(text)

    def where(self):
        if self.resumed:
            raise RuntimeError('where returned a recursive resume pointer')
        result = self.command('dispatch', 'where', str(self.number))
        if not re.match(r'^(AT|BETWEEN|FRESH)\b', result.stdout):
            raise RuntimeError(f'unresolved where: {result.stdout.strip()}')
        if ' · waiting: end your turn' in result.stdout:
            return 'wait'
        self.resumed = True
        try:
            # where's BETWEEN interval and AT note follow the first registered pointer.
            line = result.stdout.strip().split(' .. #', 1)[0]
            line = line.split(' · ', 2)[:2]
            self.receive(' · '.join(line), wake=False)
        finally:
            self.resumed = False
        return 'wait'

    def resolve_findings(self):
        # Only children marked finding are settled; contract/fault/decision stay visible.
        result = self.command('gh', 'api', '--paginate',
                              f'repos/{{owner}}/{{repo}}/issues/{self.number}/sub_issues?per_page=100')
        for ticket in json.loads(result.stdout):
            kids = json.loads(self.command('gh', 'api', '--paginate',
                             f'repos/{{owner}}/{{repo}}/issues/{ticket["number"]}/sub_issues?per_page=100').stdout)
            for child in kids:
                if child['state'] == 'open' and any(label['name'] == 'mmw:finding' for label in child['labels']):
                    self.command('dispatch', 'resolve-child', str(ticket['number']),
                                 str(child['number']), 'stale', 'invalid')

    def memory_decisions(self):
        result = self.command('dispatch', 'prepare-memory-decisions', str(self.number))
        value = json.loads(result.stdout)
        if value.get('decisions'):
            raise RuntimeError('rehearsal Memory records require explicit closing decisions')
        self.memory = str(self.files / f'memory-decisions-{self.number}.json')
        Path(self.memory).write_text(json.dumps(value))

    def retro(self):
        gathered = json.loads(self.command('retro', 'gather', str(self.number)).stdout)
        gather_path = self.files / 'gather.json'
        gather_path.write_text(json.dumps(gathered))
        analysis = {'previous_proposals': [], 'categories': {name: 'none' for name in
                    ('Navigation', 'Automated checks', 'Coding standards', 'Global AGENTS.md',
                     'Tool economy', 'No-ops', 'Information access')}, 'problems': [],
                    'intent_reconciliation': {'expected': 'Rehearse a complete isolated night',
                                              'observed': 'Tracker events and landed commits', 'gap': 'aligned'},
                    'review_learning': 'none'}
        analysis_path = self.files / 'analysis.json'
        analysis_path.write_text(json.dumps(analysis))
        self.command('retro', 'finalize', str(self.number), str(analysis_path), str(gather_path))

    def one_ticket_wake(self):
        if any(event in self.wake for event in ('ticket.passed', 'ticket.returned')):
            self.step('Land')

    def receive(self, line, *, wake=True):
        if '\n' in line or '\r' in line:
            raise RuntimeError('MULTILINE INPUT')
        match = POINTER.search(line)
        if not match:
            raise RuntimeError(f'NO POINTER {line}')
        playbook, title = match.groups()
        if ROLE_PLAYBOOK.get(self.role) != playbook:
            raise NoAction(f'NO ACTION {self.role} {title}')
        self.wake = line
        if wake:
            event = re.match(r'#(\d+) ([\w.]+)', line)
            if event:
                self.command('dispatch', 'ack', event[1], event[2])
            elif line.startswith('relay.recovered'):
                self.command('dispatch', 'ack', 'relay.recovered')
        self.step(title, follow=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--handle')
    parser.add_argument('--inbox', type=Path)
    parser.add_argument('--role')
    parser.add_argument('--step')
    parser.add_argument('--ticket', type=int, default=0)
    args = parser.parse_args()
    try:
        if args.step:
            Agent(args.role, args.ticket).step(args.step)
            return 0
        if not args.inbox or not args.handle:
            parser.error('--inbox and --handle are required for a terminal')
        first = args.inbox.read_text().splitlines()[0]
        role = re.search(r'Role ([\w-]+)', first)
        number = re.search(r'(?:ticket|spec) #(\d+)', first)
        if not role or not number:
            raise RuntimeError(f'NO IDENTITY {first}')
        agent = Agent(role[1], int(number[1]), args.inbox)
        consumed = 0
        while True:
            with args.inbox.open() as stream:
                data = stream.read()
            # A concurrent append not ending in a newline is not a complete delivery.
            lines = data.splitlines() if data.endswith('\n') else data.splitlines()[:-1]
            for line in lines[consumed:]:
                while os.environ.get('MMW_FAKE_AGENT_PAUSED') == '1' and not args.inbox.with_suffix('.go').exists():
                    time.sleep(0.02)
                with args.inbox.with_suffix('.received').open('a') as stream:
                    stream.write(line + '\n')
                agent.receive(line, wake=consumed > 0)
                consumed += 1
                if agent.root is not None:
                    launcher = Path(os.environ['MMW_HOME']) / 'bin' / 'hook-launcher'
                    result = subprocess.run([sys.executable, str(launcher), 'turn-guard', 'stop', 'claude'],
                                            input=json.dumps({'hook_event_name': 'Stop', 'cwd': os.getcwd(),
                                                              'stop_hook_active': False}),
                                            capture_output=True, text=True, timeout=30)
                    print(result.stdout, end='', flush=True)
                    print(result.stderr, end='', file=sys.stderr, flush=True)
                    if result.returncode not in (0, 2):
                        raise RuntimeError(f'STOP HOOK FAILED {result.returncode}')
            time.sleep(0.05)
    except (NoAction, RuntimeError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
