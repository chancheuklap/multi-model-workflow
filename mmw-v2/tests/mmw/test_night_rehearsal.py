"""A complete night through the installed clone, with private external boundaries."""

import json
import re
import shlex
import sys
import time
import unittest
from pathlib import Path

import fake_orca
import rehearsal
import stand_in_agent

SOURCE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE / 'mmw-v2' / 'tests' / 'lib'))
from skill_text import anchors, normalize_title


class IsolatedInstall(unittest.TestCase):
    def test_isolated_install_check_is_complete(self):
        with rehearsal.Rehearsal(source=SOURCE, ref='HEAD') as fixture:
            result = fixture.run(['bash', fixture.installed / 'install.sh', '--check'],
                                 cwd=fixture.clone)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            complete = [line for line in result.stdout.splitlines() if line.startswith('齐了：')]
            self.assertEqual(len(complete), 1, result.stdout)
            print(complete[0], flush=True)


def resolve_pointer(root, line):
    match = re.search(r'\bmmw(?: ([\w-]+))?#(.+?)(?:\. Data: [^\r\n]+)?\.?$', line)
    if not match:
        raise ValueError(f'NO POINTER {line}')
    slug, title = match.groups()
    pointer = f'mmw {slug}#{title}' if slug else f'mmw#{title}'
    mode = root / 'mmw-v2' / 'skills' / 'mmw'
    file = mode / 'playbooks' / (slug + '.md') if slug else mode / 'SKILL.md'
    if not file.is_file():
        raise ValueError(f'{pointer}: no playbook at {file}')
    text = file.read_text()
    valid = {anchor.title for anchor in anchors(text) if
             not slug or re.match(r'\s*(?:#### |(?:(?:\d+[.)]|[-*+]) )?\*\*)',
                                  text.splitlines()[anchor.start - 1])}
    if normalize_title(title) not in valid:
        raise ValueError(f'{pointer}: no step or section at {file}')
    return slug, title


class NightRehearsal(unittest.TestCase):
    def test_pointer_resolver_refuses_an_unknown_step(self):
        for pointer in ('mmw work-a-ticket#No Such Step', 'mmw no-such-playbook#Claim'):
            with self.subTest(pointer=pointer):
                with self.assertRaisesRegex(ValueError, pointer):
                    resolve_pointer(SOURCE, pointer)

    def test_night_rehearsal_from_open_night_to_finish(self):
        started_at = time.monotonic()
        with rehearsal.Rehearsal(source=SOURCE, ref='HEAD') as fixture:
            self.fixture = fixture
            self.killed = set()
            self.held_c = True
            self.events_module = stand_in_agent.load('night_events', fixture.scripts / 'events.py')
            self.locations = stand_in_agent.load('night_locations', fixture.scripts / 'locations.py')
            a, _, c = fixture.tickets
            prompt = (f'Use the mmw skill. Role night-orchestrator, spec #{fixture.spec}, '
                      'unattended: mmw run-a-night#Check and open.')
            orchestrator = self.start_agent(prompt, fixture.consumer)
            fixture.env['ORCA_TERMINAL_HANDLE'] = orchestrator
            fixture.release_agent(orchestrator)
            self.wait_for('Check and open', lambda: self.completed(orchestrator, prompt))
            self.send_step(orchestrator, 'Lint the batch')
            self.send_step(orchestrator, 'Advance, then end your turn')

            def first_reviewer_and_silent_worker():
                reviews = self.event_rows(a, 'reviewer.started')
                workers = self.event_rows(c, 'worker.started')
                return reviews and workers and (reviews[0]['session'], workers[0]['session'])

            first_review, c_worker = self.wait_for('A reviewer started and C worker held',
                                                   first_reviewer_and_silent_worker)
            row = next(row for row in self.rows() if row['handle'] == first_review)
            fake_orca.stop(row)
            self.killed.add(first_review)
            # The silence thresholds are real elapsed time, not invented tracker events.
            time.sleep(3)
            result = fixture.watchdog_once()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.wait_for('reviewer.lost', lambda: self.event_rows(a, 'reviewer.lost'))
            self.wait_for('C silent alert', lambda: any(
                line.startswith(f'watchdog: #{c} silent since') for line in self.received(orchestrator)))
            result = fixture.run(['bash', fixture.dispatch, 'resume', c, 'Carry on from where you are.'])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.held_c = False
            self.wait_for('three tickets landed', lambda: all(
                self.event_rows(n, 'ticket.landed') for n in fixture.tickets), timeout=420)
            for title in ('Advance, then end your turn', 'Closing pass', 'Close the Memory records',
                          'Reverify and summarize', 'Retro'):
                self.send_step(orchestrator, title)
            findings = fixture.checked(['bash', fixture.dispatch, 'findings', fixture.spec])
            self.assertEqual(findings, '', 'Closing pass left an unresolved finding')
            result = fixture.run(['bash', fixture.dispatch, 'finish', fixture.spec])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            d = fixture.adopted_ticket
            tree = fixture.consumer / '.worktrees' / f'issue-{d}'
            fixture.checked(['git', 'worktree', 'add', '-b', f'issue-{d}', tree, 'origin/project'])
            fixture.env['MMW_FAKE_ADOPT_INTO'] = 'project'
            adopt = self.start_agent(f'Use the mmw skill. Role adopting-worker, ticket #{d}, '
                                    'unattended: mmw work-a-ticket#Adopted ticket.', tree,
                                    role='adopting-worker', number=d)
            fixture.release_agent(adopt)
            self.wait_for('D adopted', lambda: self.completed(adopt,
                          self.received(adopt)[0] if self.received(adopt) else ''))
            child = fixture.root / 'decision.md'
            child.write_text('Rehearsal decision\n\nA deliberately open decision for the adopted ticket.\n')
            ticket_script = fixture.installed / 'skills' / self.locations.TICKET_STATE_PY
            fixture.checked([sys.executable, ticket_script, d, '--open-child', 'decision', child], cwd=tree)
            wake = f'#{d} child.opened · mmw work-a-ticket#When something else wakes you'
            self.wait_for('D child wake and where', lambda: self.completed(adopt, wake))
            self.assertIn(wake, self.received(adopt))
            self.wait_for('C resume processed', lambda: any(
                'When the orchestrator resumes you' in line
                for line in self.completed_lines(c_worker)))
            wakes, pointers = self.assert_rehearsal(orchestrator, c_worker, adopt)
            root = fixture.root
            fixture.close()
            self.assertFalse(root.exists(), 'rehearsal left its disposable directory')
            self.assertEqual(fixture.remaining_processes(), [])
            for pid in fixture.pids:
                self.assertFalse(rehearsal.process_command(pid), f'cleanup left owned pid {pid}')
        print(f'REHEARSAL OK {wakes} wakes, {pointers} pointers resolved', flush=True)
        print(f'REHEARSAL elapsed {time.monotonic() - started_at:.1f}s', flush=True)

    def rows(self):
        path = self.fixture.orca_state / 'terminals.json'
        return json.loads(path.read_text()) if path.exists() else []

    def event_rows(self, number, name=None):
        state = json.loads(self.fixture.gh_state.read_text())
        result = []
        for comment in state['issues'][str(number)]['comments']:
            kind, event = self.events_module.parse(comment['body'])
            self.assertNotEqual(kind, 'unreadable', f'#{number}: {event}')
            if kind == 'event' and (name is None or event['event'] == name):
                result.append(event)
        return result

    def lines(self, handle, suffix):
        path = self.fixture.orca_state / f'{handle}.{suffix}'
        return path.read_text().splitlines() if path.exists() else []

    def received(self, handle):
        return self.lines(handle, 'received')

    def completed_lines(self, handle):
        return self.lines(handle, 'completed')

    def completed(self, handle, line):
        return bool(line) and line in self.completed_lines(handle)

    def release_ready(self):
        hold = set(self.killed)
        for row in self.rows():
            first = self.lines(row['handle'], 'inbox')[0]
            if (f'ticket #{self.fixture.tickets[2]},' in first and 'Role worker,' in first
                    and self.held_c):
                hold.add(row['handle'])
            if f'ticket #{self.fixture.tickets[0]},' in first and 'Role reviewer,' in first:
                reviews = self.event_rows(self.fixture.tickets[0], 'reviewer.started')
                if not reviews or row['handle'] == reviews[0]['session']:
                    hold.add(row['handle'])
        self.fixture.release_started_agents(hold=hold)

    def wait_for(self, step, predicate, timeout=150):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.release_ready()
            for row in self.rows():
                if row['handle'] in self.killed:
                    continue
                errors = '\n'.join(self.lines(row['handle'], 'stderr'))
                if re.search(r'NO ACTION|NO POINTER|NO IDENTITY|MULTILINE INPUT|COMMAND FAILED|'
                             r'STOP HOOK FAILED|Traceback', errors):
                    self.fail(f'{step}: {row["handle"]}: ' + ' | '.join(errors.splitlines()[-8:]))
                exit_file = self.fixture.orca_state / f'{row["handle"]}.exit'
                # Landing can archive this session between the row read and ps.
                if not fake_orca.alive(row):
                    row = next(current for current in self.rows() if current['handle'] == row['handle'])
                if row.get('closed'):
                    self.assertTrue(row.get('healthyBeforeClose'),
                                    f'{step}: {row["handle"]} failed before close')
                elif not fake_orca.alive(row) and (not exit_file.exists() or exit_file.read_text() != '0'):
                    self.fail(f'{step}: {row["handle"]} exited: ' + ' | '.join(errors.splitlines()[-8:]))
            value = predicate()
            if value:
                return value
            time.sleep(0.1)
        diagnostics = '; '.join(row['handle'] + ': ' + ' | '.join(self.lines(row['handle'], 'stderr')[-5:])
                                + ' stdout: ' + ' | '.join(self.lines(row['handle'], 'stdout')[-5:])
                                for row in self.rows())
        self.fail(f'{step}: timed out after {timeout}s; {diagnostics}')

    def start_agent(self, prompt, cwd, role='night-orchestrator', number=None):
        command = shlex.join(['exec', 'env', f'MMW_ROLE={role}',
                              f'MMW_SPEC={self.fixture.other_spec if role == "adopting-worker" else self.fixture.spec}',
                              *([f'MMW_TICKET={number}'] if number else []), 'claude', prompt])
        result = self.fixture.orca('terminal', 'create', '--worktree', f'path:{cwd}',
                                   '--command', command, '--title', role, '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)['result']['handle']

    def send_step(self, handle, title):
        # Completion counters distinguish repeated identical steps from an earlier turn.
        before = len(self.completed_lines(handle))
        line = f'mmw run-a-night#{title}'
        result = self.fixture.orca('terminal', 'send', '--terminal', handle, '--text', line,
                                   '--enter', '--wait-submit', '30', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.wait_for(title, lambda: line in self.completed_lines(handle)[before:]
                      and len(self.completed_lines(handle)) == len(self.lines(handle, 'inbox')))

    def assert_rehearsal(self, orchestrator, c_worker, adopt):
        fixture = self.fixture
        pointers = 0
        where_count = 0
        logs = [fixture.root / name for name in ('gh.log', 'orca.log', 'boundary.log')]
        state_dir = fixture.home / '.mmw' / 'state'
        logs += list(state_dir.glob('*/relay.log')) + list(state_dir.glob('*/watchdog.log'))
        for row in self.rows():
            handle = row['handle']
            errors = '\n'.join(self.lines(handle, 'stderr'))
            self.assertNotRegex(errors, r'NO ACTION|NO POINTER|NO IDENTITY|MULTILINE INPUT|'
                                r'COMMAND FAILED|STOP HOOK FAILED|Traceback', handle)
            if handle not in self.killed:
                if row.get('closed'):
                    self.assertTrue(row.get('healthyBeforeClose'), handle)
                elif not fake_orca.alive(row):
                    self.assertEqual(self.lines(handle, 'exit'), ['0'], handle)
            inputs = self.received(handle)
            # The injected dead reviewer never takes its first turn, but its start is checked too.
            if handle in self.killed:
                for line in self.lines(handle, 'inbox'):
                    resolve_pointer(fixture.clone, line)
            else:
                self.assertTrue(inputs, f'{handle} received no pointer')
            role = re.search(r'Role ([\w-]+)', self.lines(handle, 'inbox')[0])[1]
            for line in inputs:
                self.assertNotIn('\r', line)
                resolve_pointer(fixture.clone, line)
                pointers += 1
            output = self.lines(handle, 'stdout')
            where_lines = [line for line in output if re.match(r'^(AT|BETWEEN|FRESH)\b', line)]
            for line in where_lines:
                pointer = re.search(r'mmw ([\w-]+)#([^\n]+?)(?: \.\. #| · |$)', line)
                self.assertIsNotNone(pointer, line)
                self.assertIn(pointer[2], {entry['step'] for entry in self.locations.WHERE_ROWS[role].values()}, line)
                where_count += 1
            self.assertEqual(sum(line == f'ACTION {role} When the orchestrator resumes you' or
                                 line == f'ACTION {role} When something else wakes you' for line in output),
                             len(where_lines), f'{handle}: a resume/wake did not produce a where line')
            logs += [fixture.orca_state / f'{handle}.{suffix}' for suffix in ('stdout', 'stderr')]
        self.assertGreaterEqual(where_count, 2)
        self.assertFalse((fixture.installed / 'skills' / 'dispatch').exists())
        for path in logs:
            text = path.read_text() if path.exists() else ''
            self.assertNotIn('skills/dispatch/', text, str(path))
            if path.name in ('gh.log', 'orca.log', 'boundary.log'):
                self.assertNotIn('UNHANDLED', text, str(path))
        path_texts = [path.read_text() for path in state_dir.glob('*/prompts/*') if path.is_file()]
        path_texts += [row['command'] for row in self.rows()]
        mmw_paths = [match for text in path_texts for match in
                     re.findall(r'/[^\s`\'"<>]*?/mmw-v2/[^\s`\'"<>]*', text)]
        self.assertTrue(mmw_paths, 'no frozen MMW paths were checked')
        for path in mmw_paths:
            self.assertTrue(path.startswith(str(fixture.installed) + '/'), path)
            self.assertFalse(path.startswith(str(SOURCE) + '/'), path)
        state = json.loads(fixture.gh_state.read_text())
        for number in fixture.tickets:
            issue = state['issues'][str(number)]
            self.assertEqual(issue['state'], 'CLOSED')
            closing = [comment['body'] for comment in issue['comments']
                       if self.events_module.parse(comment['body'])[0] == 'event'
                       and self.events_module.parse(comment['body'])[1]['event'] == 'ticket.passed']
            self.assertTrue(closing, f'#{number} has no closing comment')
            self.assertIn('ALL MET', closing[-1].splitlines()[0])
            self.assertNotIn(self.locations.STEPS_WITHOUT_TRACE_HEADER, closing[-1])
        a, _, c = fixture.tickets
        names = [event['event'] for event in self.event_rows(a)]
        lost = names.index('reviewer.lost')
        restarted = names.index('reviewer.started', lost + 1)
        self.assertIn('reviewer.reported', names[restarted + 1:])
        self.assertTrue(any(line.startswith(f'watchdog: #{c} silent since')
                            for line in self.received(orchestrator)))
        self.assertTrue(self.event_rows(c, 'worker.resumed'))
        self.assertTrue(any(line.endswith('mmw work-a-ticket#When the orchestrator resumes you')
                            for line in self.received(c_worker)))
        findings = self.event_rows(c, 'child.opened')
        findings = {str(event['child']) for event in findings if event['kind'] == 'finding'}
        self.assertTrue(findings)
        self.assertTrue(findings <= {str(event['child']) for event in self.event_rows(c, 'child.closed')})
        events = self.event_rows(fixture.spec)
        expected = ('spec.opened', 'spec.closed', 'spec.retroed', 'spec.merged')
        actual = [event['event'] for event in events if event['event'] in expected]
        self.assertEqual(actual, list(expected))
        self.assertEqual(self.event_rows(fixture.spec, 'spec.retroed')[0]['result'], 'recorded')
        self.assertTrue(any(comment['body'].startswith('NIGHT SUMMARY')
                            for comment in state['issues'][str(fixture.spec)]['comments']))
        self.assertTrue(any(event['kind'] == 'decision'
                            for event in self.event_rows(fixture.adopted_ticket, 'child.opened')))
        self.assertTrue(any(line.startswith('FRESH adopting-worker') or line.startswith('AT adopting-worker')
                            for line in self.lines(adopt, 'stdout')))
        wakes = sum(line.startswith('orca :: terminal :: send ::')
                    for line in (fixture.root / 'orca.log').read_text().splitlines())
        self.assertGreater(wakes, 0)
        return wakes, pointers
