"""Read the cloud board from GitHub issues, pull requests, and origin night branches.

The page is the v4 board. This module fills it from the records v5 cloud actually
writes: issue labels, Blocked by, sub-issues, the work report on a pull request,
and whether that pull request's merge is in the night branch. It does not read
issue comments and it does not treat the checkout's current branch as the night.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
import subprocess
import sys
import threading
import urllib.parse
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'tools' / 'dispatch' / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import models
from status import GitHub, command, labels, read_plan

NIGHT_REF = re.compile(r'^refs/heads/night/(spec|ticket)-(\d+)$')
GRADES = ('junior-worker', 'senior-worker')
# One GitHub read a minute, including the manual refresh. A failed read waits
# five minutes, so a broken token or a down API cannot be polled into the limit
# the cloud workflow also uses.
READ_INTERVAL = 60
FAILURE_INTERVAL = 300


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso(value):
    return value.astimezone(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _listing(api, address):
    rows = api.listing(address)
    if not isinstance(rows, list):
        raise ValueError(f'GitHub did not return a list: {address}')
    return [row for row in rows if 'pull_request' not in row]


def _issues(api, label):
    quoted = urllib.parse.quote(label, safe='')
    return _listing(api, f'issues?state=open&labels={quoted}')


def _missing(exc):
    text = str(exc).lower()
    return '404' in text or 'not found' in text


def read_issue(api, number):
    try:
        issue = api.issue(number)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as exc:
        if _missing(exc):
            return None
        raise
    if not isinstance(issue, dict) or 'pull_request' in issue:
        return None
    return issue


def night_index(run):
    """Remote night branches. ls-remote does not update this checkout's refs."""
    text = run('git', 'ls-remote', '--heads', 'origin', 'refs/heads/night/*') or ''
    found = {}
    for line in text.splitlines():
        ref = line.split()[-1] if line.split() else ''
        match = NIGHT_REF.fullmatch(ref)
        if match:
            found[(match.group(1), int(match.group(2)))] = f'night/{match.group(1)}-{match.group(2)}'
    return found


def wayfinder_kind(tags):
    for tag in tags:
        if tag.startswith('wayfinder:'):
            return tag.split(':', 1)[1]
    return None


def slim(pr):
    head = pr.get('head') or {}
    base = pr.get('base') or {}
    return {
        'number': pr.get('number'),
        'state': pr.get('state') or '',
        'draft': bool(pr.get('draft')),
        'merged_at': pr.get('merged_at'),
        'merge_commit_sha': pr.get('merge_commit_sha'),
        'html_url': pr.get('html_url') or '',
        'title': pr.get('title') or '',
        'body': pr.get('body') or '',
        'head': {'ref': head.get('ref') or '', 'sha': head.get('sha') or ''},
        'base': {'ref': base.get('ref') or ''},
    }


def choose(prs):
    """Merged, then an open non-draft, then an open draft. List order breaks ties."""
    def rank(pr):
        state = (pr.get('state') or '').lower()
        if pr.get('merged_at'):
            return 0
        if state == 'open' and not pr.get('draft'):
            return 1
        if state == 'open' and pr.get('draft'):
            return 2
        return 3
    return sorted(prs, key=rank)[0] if prs else None


def delivery_line(prs):
    if not prs:
        return 'delivery PR 还没有'
    for pr in prs:
        if (pr.get('state') or '').lower() == 'open':
            return f"delivery PR #{pr['number']}"
    if any(pr.get('merged_at') for pr in prs):
        return "Night's branch merged"
    return 'delivery PR 还没有'


def list_delivery(api, into, project):
    """PRs whose head is this night branch. Not every PR into the project branch."""
    if not into or not project or '/' not in api.repo:
        return []
    owner = api.repo.split('/', 1)[0]
    head = urllib.parse.quote(f'{owner}:{into}', safe='')
    rows = api.listing(f'pulls?state=all&head={head}')
    if not isinstance(rows, list):
        raise ValueError(f'GitHub did not return delivery PRs for {into}')
    return [slim(pr) for pr in rows
            if (pr.get('head') or {}).get('ref') == into and (pr.get('base') or {}).get('ref') == project]


def project_of(fork, into):
    if not into:
        return None
    try:
        # project_fork resolves a commit. On this machine the night is origin/night/…,
        # not a local branch named night/….
        project, _sha = fork(f'origin/{into}')
    except ValueError:
        return None
    return project


def child_view(issue):
    return {
        'number': issue.get('number'),
        'title': issue.get('title') or '',
        'state': (issue.get('state') or '').lower(),
        'body': issue.get('body') or '',
        'labels': labels(issue),
        'html_url': issue.get('html_url') or '',
    }


def _fold(landed):
    return {
        'sessions': [], 'children': {}, 'unreadable': [], 'landed': landed,
        'held': False, 'claim_hold': False, 'returned': False, 'bounced': False,
        'worker': None, 'outcome': None,
    }


def annotate_blockers(api, blockers):
    out = []
    for row in blockers:
        source = api.issue(row['number'])
        out.append({
            'number': row['number'],
            'title': row.get('title') or source.get('title') or '',
            'state': (source.get('state') or '').lower(),
            'ticket': 'mmw:ticket' in labels(source),
            'resolved': bool(row.get('resolved')),
        })
    return out


def ticket_prs(row, into):
    if not into:
        return []
    wanted = f"ticket/issue-{row['number']}"
    kept = []
    for pr in row.get('prs') or []:
        head = (pr.get('head') or {}).get('ref')
        base = (pr.get('base') or {}).get('ref')
        if head == wanted and base == into:
            kept.append(slim(pr))
    return kept


def present_ticket(row, into, api):
    prs = ticket_prs(row, into)
    landed = bool(row.get('landed'))
    tags = list(row.get('labels') or [])
    return {
        'n': row['number'],
        'title': row.get('title') or '',
        'state': (row.get('state') or '').lower(),
        'labels': tags,
        'grade': row.get('grade'),
        'blocked': [item['number'] for item in row.get('blockers') or []],
        'blockers': annotate_blockers(api, row.get('blockers') or []),
        'blocker_hold': '' if landed else 'open',
        'children': [child_view(child) for child in row.get('children') or []],
        'closeout': None,
        'prs': prs,
        'pr': choose(prs),
        'landed': landed,
        'into': into,
        'fold': _fold(landed),
        'events': [],
    }


def tickets_without_night(api, root):
    """An open spec whose night/spec-N is not on origin. Nothing has landed."""
    visited = set()
    found = []

    def tree(issue):
        number = issue['number']
        if number in visited:
            return {**issue, 'children': []}
        visited.add(number)
        children = [tree(item) for item in _listing(api, f'issues/{number}/sub_issues')]
        item = {**issue, 'children': children}
        if 'mmw:ticket' in labels(issue):
            found.append(item)
        return item

    tree(root)
    rows = []
    for issue in found:
        tags = labels(issue)
        blockers = []
        for ref in _listing(api, f"issues/{issue['number']}/dependencies/blocked_by"):
            source = api.issue(ref['number'])
            ticket = 'mmw:ticket' in labels(source)
            blockers.append({
                'number': source['number'],
                'title': source.get('title') or '',
                'resolved': False if ticket else source.get('state') == 'closed',
            })
        grades = [tag for tag in tags if tag in GRADES]
        rows.append({
            'number': issue['number'],
            'title': issue.get('title') or '',
            'state': issue.get('state') or '',
            'labels': tags,
            'grade': grades[0] if len(grades) == 1 else None,
            'children': issue.get('children') or [],
            'blockers': blockers,
            'prs': [],
            'landed': False,
        })
    return rows


def reconcile(tasks):
    """A ticket blocker is resolved only when that ticket has landed on its own night."""
    tickets = [ticket for task in tasks for spec in task['specs'] for ticket in spec['tickets']]
    landed = {ticket['n']: ticket['landed'] for ticket in tickets}
    for ticket in tickets:
        for blocker in ticket['blockers']:
            number = blocker['number']
            if number in landed:
                blocker['resolved'] = bool(landed[number])
            elif blocker.get('ticket'):
                blocker['resolved'] = False
            blocker['blocker_hold'] = '' if blocker['resolved'] else 'open'


def map_parts(api, number, seen):
    if number in seen:
        return [], []
    seen.add(number)
    specs, decisions = [], []
    for child in _listing(api, f'issues/{number}/sub_issues'):
        tags = labels(child)
        if 'mmw:spec' in tags:
            specs.append(child)
        elif wayfinder_kind(tags):
            decisions.append(child)
            nested_specs, nested_decisions = map_parts(api, child['number'], seen)
            specs.extend(nested_specs)
            decisions.extend(nested_decisions)
        elif 'mmw:ticket' not in tags and 'mmw:map' not in tags:
            nested_specs, nested_decisions = map_parts(api, child['number'], seen)
            specs.extend(nested_specs)
            decisions.extend(nested_decisions)
    return specs, decisions


def decision_view(api, issue):
    tags = labels(issue)
    refs = _listing(api, f"issues/{issue['number']}/dependencies/blocked_by")
    return {
        'n': issue['number'],
        'kind': wayfinder_kind(tags),
        'title': issue.get('title') or '',
        'state': (issue.get('state') or '').lower(),
        'blocked': [ref['number'] for ref in refs],
    }


def build_spec(api, issue, into, plan, fork):
    if into:
        snapshot = plan(issue['number'], into, single=False, api=api)
        rows = snapshot['tickets']
        project = project_of(fork, into)
    else:
        rows = tickets_without_night(api, issue)
        project = None
    return {
        'n': issue['number'],
        'title': issue.get('title') or '',
        'tickets': [present_ticket(row, into, api) for row in rows],
        'into': into,
        'project': project,
        'delivery': list_delivery(api, into, project),
    }


def spec_task(issue, spec):
    return {
        'n': issue['number'],
        'kind': 'spec',
        'title': issue.get('title') or '',
        'state': (issue.get('state') or '').lower(),
        'decisions': [],
        'specs': [spec],
        'deliveryLine': delivery_line(spec['delivery']),
    }


def load(api=None, run=None, plan=None, fork=None):
    api = api or GitHub()
    run = run or command
    plan = plan or read_plan
    fork = fork or models.project_fork
    nights = night_index(run)
    maps = _issues(api, 'mmw:map')
    open_specs = _issues(api, 'mmw:spec')
    tasks = []
    placed = set()

    for raw in maps:
        spec_issues, decision_issues = map_parts(api, raw['number'], set())
        specs = []
        for issue in spec_issues:
            placed.add(issue['number'])
            specs.append(build_spec(api, issue, nights.get(('spec', issue['number'])), plan, fork))
        tasks.append({
            'n': raw['number'],
            'kind': wayfinder_kind(labels(raw)) or 'map',
            'title': raw.get('title') or '',
            'state': (raw.get('state') or '').lower(),
            'decisions': [decision_view(api, issue) for issue in decision_issues],
            'specs': specs,
        })

    for issue in open_specs:
        if issue['number'] in placed:
            continue
        placed.add(issue['number'])
        into = nights.get(('spec', issue['number']))
        tasks.append(spec_task(issue, build_spec(api, issue, into, plan, fork)))

    for (kind, number) in sorted(key for key in nights if key[0] == 'spec'):
        if number in placed:
            continue
        issue = read_issue(api, number)
        if not issue or 'mmw:spec' not in labels(issue):
            continue
        placed.add(number)
        tasks.append(spec_task(issue, build_spec(api, issue, nights[('spec', number)], plan, fork)))

    placed_tickets = {ticket['n'] for task in tasks for spec in task['specs'] for ticket in spec['tickets']}
    for (kind, number) in sorted(key for key in nights if key[0] == 'ticket'):
        if number in placed_tickets:
            continue
        issue = read_issue(api, number)
        if not issue or 'mmw:ticket' not in labels(issue):
            continue
        into = nights[('ticket', number)]
        snapshot = plan(number, into, single=True, api=api)
        project = project_of(fork, into)
        delivery = list_delivery(api, into, project)
        rows = snapshot['tickets']
        spec = {
            'n': number,
            'title': issue.get('title') or '',
            'tickets': [present_ticket(row, into, api) for row in rows],
            'into': into,
            'project': project,
            'delivery': delivery,
        }
        tasks.append({
            'n': number,
            'kind': 'ticket',
            'title': issue.get('title') or '',
            'state': (issue.get('state') or '').lower(),
            'decisions': [],
            'specs': [spec],
            'deliveryLine': delivery_line(delivery),
        })

    reconcile(tasks)
    return {'tasks': tasks, 'repo': api.repo}


class BoardStore:
    def __init__(self, api=None, run=None, plan=None, fork=None, clock=utc_now):
        self.api = api
        self.run = run
        self.plan = plan
        self.fork = fork
        self.clock = clock
        self.last_tree_at = None
        self.last_attempt_at = None
        self.failed_at = None
        self.snapshot = {'tasks': [], 'repo': None, 'read_at': None}
        self.lock = threading.Condition()
        self.refreshing = False
        self.last_answer = self.snapshot

    def _cached(self, now, force):
        if self.last_attempt_at is not None and (now - self.last_attempt_at).total_seconds() < READ_INTERVAL:
            return True
        if force:
            return False
        if self.failed_at is not None and (now - self.failed_at).total_seconds() < FAILURE_INTERVAL:
            return True
        if self.last_tree_at is not None and (now - self.last_tree_at).total_seconds() < READ_INTERVAL:
            return True
        return False

    def answer(self, force=False):
        with self.lock:
            if self.refreshing:
                self.lock.wait_for(lambda: not self.refreshing)
                return copy.deepcopy(self.last_answer)
            now = self.clock()
            if self._cached(now, force):
                return copy.deepcopy(self.last_answer)
            self.refreshing = True
            self.last_attempt_at = now
        try:
            loaded = load(self.api, self.run, self.plan, self.fork)
            snapshot = {'tasks': loaded['tasks'], 'repo': loaded['repo'], 'read_at': iso(self.clock())}
            with self.lock:
                self.last_tree_at = self.clock()
                self.failed_at = None
                self.snapshot = snapshot
                self.last_answer = snapshot
        except Exception as exc:
            with self.lock:
                self.failed_at = self.clock()
                failed = copy.deepcopy(self.snapshot)
                failed['read_failed'] = {'at': iso(self.failed_at), 'message': str(exc)}
                self.last_answer = failed
        finally:
            with self.lock:
                self.refreshing = False
                self.lock.notify_all()
        return copy.deepcopy(self.last_answer)


STORE = BoardStore()


def handle(request):
    path = urllib.parse.urlsplit(request.path).path
    if request.command == 'GET' and path == '/api/board':
        answer = STORE.answer()
    elif request.command == 'POST' and path == '/api/board/refresh':
        answer = STORE.answer(force=True)
    else:
        return 404, {'Content-Type': 'application/json'}, b'{"error":"not found"}\n'
    body = (json.dumps(answer, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    return 200, {'Content-Type': 'application/json; charset=utf-8'}, body
