"""Cloud board data: native Issue/PR facts and ordinary comments, not session events."""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/dispatch/scripts'))
from status import GitHub, labels, read_plan


def ticket_view(row, comments):
    children = row['children']
    # Compatibility with shared presentation components; these are not folded events.
    empty = {'sessions': [], 'children': {}, 'unreadable': [], 'landed': row['landed'],
             'worker': None, 'outcome': None, 'returned': False, 'bounced': False, 'held': False}
    return {**row, 'n': row['number'], 'blocked': [x['number'] for x in row['blockers']],
            'blocker_hold': '' if row['landed'] else 'not merged',
            'blockers': [{'number': x['number'], 'title': x['title'], 'readable': True,
                          'resolved': x['resolved'],
                          'blocker_hold': '' if x['resolved'] else 'unresolved'} for x in row['blockers']],
            'fold': empty, 'events': [], 'comments': comments, 'children': children, 'closeout': None}


class BoardStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_at = 0
        self.snapshot = {'tasks': [], 'repo': None, 'read_at': None}

    def answer(self, refresh=False):
        with self.lock:
            if not refresh and time.monotonic() - self.last_at < 20:
                return self.snapshot
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                api = GitHub()
                branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, check=True).stdout.strip()
                if not branch:
                    raise ValueError('open the cloud board from the Coordinator night-branch checkout')
                specs = api.listing('issues?state=open&labels=mmw:spec')
                tasks = []
                by_spec = {}
                for raw in specs:
                    plan = read_plan(raw['number'], branch, api=api)
                    tickets = [ticket_view(row, api.listing(f'issues/{row["number"]}/comments')) for row in plan['tickets']]
                    spec = {'n': raw['number'], 'title': raw['title'], 'tickets': tickets}
                    by_spec[raw['number']] = spec
                attached = set()
                for raw in api.listing('issues?state=open&labels=mmw:map'):
                    children = api.listing(f'issues/{raw["number"]}/sub_issues')
                    mapped = [by_spec[x['number']] for x in children if x['number'] in by_spec]
                    attached.update(x['n'] for x in mapped)
                    decisions = []
                    for item in children:
                        kind = next((x.split(':', 1)[1] for x in labels(item) if x.startswith('wayfinder:')), None)
                        if kind:
                            blocked = api.listing(f'issues/{item["number"]}/dependencies/blocked_by')
                            decisions.append({'n': item['number'], 'title': item['title'], 'state': item['state'],
                                              'kind': kind, 'blocked': [x['number'] for x in blocked]})
                    tasks.append({'n': raw['number'], 'kind': 'map', 'title': raw['title'],
                                  'state': raw['state'], 'decisions': decisions, 'specs': mapped})
                tasks += [{'n': spec['n'], 'kind': 'spec', 'title': spec['title'], 'state': 'open',
                           'decisions': [], 'specs': [spec]} for n, spec in by_spec.items() if n not in attached]
                self.snapshot = {'tasks': tasks, 'repo': api.repo, 'read_at': now, 'into': branch}
                self.last_at = time.monotonic()
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
                return {**self.snapshot, 'read_failed': {'at': now, 'message': str(exc)}}
            return self.snapshot

STORE = BoardStore()


def handle(request):
    value = STORE.answer(refresh=request.command == 'POST')
    return 200, {'Content-Type': 'application/json; charset=utf-8'}, (json.dumps(value, ensure_ascii=False) + '\n').encode()
