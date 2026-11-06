"""The cloud board reads origin night branches, issues, and pull requests.

A fake GitHub and a fake git stand in for the network. The test does not
claim a night from the checkout's current branch.
"""
from __future__ import annotations

import datetime as dt
import json
import unittest
import urllib.parse
from pathlib import Path
import sys

BOARD = Path(__file__).resolve().parents[2] / 'board'
sys.path.insert(0, str(BOARD))

import board_data


def pr(number, head, base, **extra):
    return {
        'number': number,
        'state': extra.get('state', 'open'),
        'draft': extra.get('draft', False),
        'merged_at': extra.get('merged_at'),
        'merge_commit_sha': extra.get('merge_commit_sha'),
        'html_url': f'https://github.com/acme/widgets/pull/{number}',
        'title': extra.get('title', f'PR {number}'),
        'body': extra.get('body', ''),
        'head': {'ref': head, 'sha': 'abcdef1'},
        'base': {'ref': base},
    }


def issue(number, title, state, *tags, body=''):
    return {
        'number': number,
        'title': title,
        'state': state,
        'body': body,
        'html_url': f'https://github.com/acme/widgets/issues/{number}',
        'labels': [{'name': tag} for tag in tags],
    }


class Api:
    def __init__(self):
        self.repo = 'acme/widgets'
        self.calls = []
        self.listings = {}
        self.issues = {}

    def listing(self, address):
        self.calls.append(address)
        if address not in self.listings:
            raise RuntimeError(f'missing list {address}')
        return self.listings[address]

    def issue(self, number):
        self.calls.append(f'issues/{number}')
        if number not in self.issues:
            raise RuntimeError('404 Not Found')
        return self.issues[number]


class Git:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        if args == ('git', 'ls-remote', '--heads', 'origin', 'refs/heads/night/*'):
            return self.text
        raise AssertionError(args)


class Clock:
    def __init__(self):
        self.now = dt.datetime(2026, 11, 4, 4, 0, tzinfo=dt.timezone.utc)

    def __call__(self):
        return self.now


def asked(calls, path, **query):
    for call in calls:
        base, _, qs = call.partition('?')
        if base != path:
            continue
        got = urllib.parse.parse_qs(qs)
        if all(got.get(key) == [value] for key, value in query.items()):
            return True
    return False


class BoardReadTest(unittest.TestCase):
    def setUp(self):
        self.api = Api()
        self.git = Git('\n'.join([
            '1111111\trefs/heads/night/spec-4',
            '2222222\trefs/heads/night/spec-7',
            '3333333\trefs/heads/night/spec-11',
            '4444444\trefs/heads/night/spec-99',
            '5555555\trefs/heads/night/ticket-9',
            '6666666\trefs/heads/night/scratch',
        ]))
        self.plan_calls = []
        self.api.issues = {
            7: issue(7, 'Closed spec', 'closed', 'mmw:spec'),
            9: issue(9, 'Solo ticket', 'open', 'mmw:ticket', 'senior-worker'),
            13: issue(13, 'Closed unpassed', 'closed', 'mmw:ticket'),
            20: issue(20, 'Landed elsewhere', 'open', 'mmw:ticket', 'senior-worker'),
            40: issue(40, 'A closed note', 'closed', 'mmw:child'),
            41: issue(41, 'Another ticket', 'open', 'mmw:ticket'),
        }
        pulls = [
            pr(81, 'night/spec-4', 'project/app', body='ship four', state='open'),
            pr(70, 'night/spec-4', 'project/app', state='closed', merged_at='2026-11-01T00:00:00Z'),
            pr(82, 'night/spec-7', 'project/app', state='closed', merged_at='2026-11-02T00:00:00Z', body='ship seven'),
            pr(80, 'night/ticket-9', 'project/app', state='open', body='ship nine'),
            pr(1, 'night/other', 'project/app', state='open'),
        ]
        child = issue(31, 'Runner failed', 'open', 'mmw:child', body='runner failed')
        spec2 = issue(2, 'Nested spec', 'open', 'mmw:spec')
        spec4 = issue(4, 'Open spec', 'open', 'mmw:spec')
        spec6 = issue(6, 'No night', 'open', 'mmw:spec')
        spec11 = issue(11, 'No project', 'open', 'mmw:spec')
        decision = issue(3, 'A decision', 'open', 'wayfinder:contract')
        self.api.listings = {
            'issues?state=open&labels=mmw%3Amap': [
                issue(1, 'The map', 'open', 'mmw:map', 'wayfinder:migration'),
            ],
            'issues?state=open&labels=mmw%3Aspec': [spec2, spec4, spec6, spec11],
            'issues/1/sub_issues': [spec2, decision],
            'issues/3/sub_issues': [],
            'issues/3/dependencies/blocked_by': [],
            'issues/2/sub_issues': [],
            'issues/6/sub_issues': [
                issue(30, 'Unsent ticket', 'open', 'mmw:ticket', 'junior-worker'),
            ],
            'issues/30/sub_issues': [child],
            'issues/31/sub_issues': [],
            'issues/30/dependencies/blocked_by': [
                {'number': 40},
                {'number': 41},
            ],
            'pulls?state=all&head=acme%3Anight%2Fspec-4': pulls,
            'pulls?state=all&head=acme%3Anight%2Fspec-7': pulls,
            'pulls?state=all&head=acme%3Anight%2Fticket-9': pulls,
        }
        night4 = 'night/spec-4'
        self.plans = {
            (4, False): {'tickets': [
                {
                    'number': 5, 'title': 'Draft work', 'state': 'open',
                    'labels': ['mmw:ticket', 'junior-worker', 'ready-for-agent'],
                    'grade': 'junior-worker', 'landed': False, 'children': [],
                    'blockers': [{'number': 20, 'title': 'Landed elsewhere', 'resolved': False}],
                    'prs': [
                        pr(51, 'ticket/issue-5', night4, draft=True, body='draft notes'),
                        pr(52, 'ticket/issue-5', 'dev', draft=False, body='wrong base'),
                    ],
                },
                {
                    'number': 8, 'title': 'Needs triage', 'state': 'open',
                    'labels': ['mmw:ticket', 'junior-worker', 'needs-triage'],
                    'grade': 'junior-worker', 'landed': False, 'children': [],
                    'blockers': [],
                    'prs': [pr(53, 'ticket/issue-8', night4, draft=False, body='fix the door')],
                },
                {
                    'number': 12, 'title': 'Human ticket', 'state': 'open',
                    'labels': ['mmw:ticket', 'ready-for-human'],
                    'grade': None, 'landed': False, 'children': [],
                    'blockers': [{'number': 13, 'title': 'Closed unpassed', 'resolved': True}],
                    'prs': [],
                },
                {
                    'number': 13, 'title': 'Closed unpassed', 'state': 'closed',
                    'labels': ['mmw:ticket', 'junior-worker'],
                    'grade': 'junior-worker', 'landed': False, 'children': [],
                    'blockers': [], 'prs': [],
                },
            ]},
            (7, False): {'tickets': [
                {
                    'number': 20, 'title': 'Landed elsewhere', 'state': 'open',
                    'labels': ['mmw:ticket', 'senior-worker'],
                    'grade': 'senior-worker', 'landed': True, 'children': [],
                    'blockers': [],
                    'prs': [pr(54, 'ticket/issue-20', 'night/spec-7', state='closed',
                               merged_at='2026-11-03T00:00:00Z', merge_commit_sha='abc1234',
                               body='landed report')],
                },
            ]},
            (11, False): {'tickets': []},
            (9, True): {'tickets': [
                {
                    'number': 9, 'title': 'Solo ticket', 'state': 'open',
                    'labels': ['mmw:ticket', 'senior-worker'],
                    'grade': 'senior-worker', 'landed': False,
                    'children': [], 'blockers': [],
                    'prs': [
                        pr(91, 'ticket/issue-9', 'night/ticket-9', draft=True, body='still drafting'),
                        pr(92, 'ticket/issue-9', 'night/ticket-9', draft=False, body='ready report'),
                    ],
                },
            ]},
        }

    def plan(self, number, into, single=False, api=None):
        self.plan_calls.append((number, into, single))
        return self.plans[(number, single)]

    def fork(self, night):
        if night == 'origin/night/spec-11':
            raise ValueError(f'no project branch is a base of {night}')
        if night in ('origin/night/spec-4', 'origin/night/spec-7', 'origin/night/ticket-9'):
            return ('project/app', 'forksha')
        raise AssertionError(night)

    def load(self):
        return board_data.load(self.api, self.git, self.plan, self.fork)

    def test_board_reads_nights_issues_and_pull_requests(self):
        loaded = self.load()
        self.assertEqual(loaded['repo'], 'acme/widgets')
        self.assertEqual(self.git.calls, [
            ('git', 'ls-remote', '--heads', 'origin', 'refs/heads/night/*'),
        ])
        self.assertFalse(any(call[:2] == ('git', 'fetch') for call in self.git.calls))
        self.assertTrue(asked(self.api.calls, 'issues', state='open', labels='mmw:map'))
        self.assertTrue(asked(self.api.calls, 'issues', state='open', labels='mmw:spec'))
        self.assertIn('issues/1/sub_issues', self.api.calls)
        self.assertIn('issues/6/sub_issues', self.api.calls)
        self.assertIn('issues/30/dependencies/blocked_by', self.api.calls)
        self.assertTrue(asked(self.api.calls, 'pulls', state='all', head='acme:night/spec-4'))
        self.assertTrue(asked(self.api.calls, 'pulls', state='all', head='acme:night/spec-7'))
        self.assertTrue(asked(self.api.calls, 'pulls', state='all', head='acme:night/ticket-9'))
        self.assertFalse(any('base=project' in call for call in self.api.calls))
        self.assertFalse(any('comments' in call for call in self.api.calls))
        self.assertIn('issues/99', self.api.calls)

        tasks = {task['n']: task for task in loaded['tasks']}
        self.assertEqual([task['n'] for task in loaded['tasks']], [1, 4, 6, 11, 7, 9])
        self.assertEqual(tasks[1]['kind'], 'migration')
        self.assertNotIn('deliveryLine', tasks[1])
        self.assertEqual(tasks[1]['decisions'][0]['kind'], 'contract')
        self.assertEqual(tasks[1]['specs'][0]['n'], 2)
        self.assertIsNone(tasks[1]['specs'][0]['into'])
        self.assertNotIn(2, tasks)
        self.assertNotIn(99, tasks)

        self.assertEqual(tasks[4]['kind'], 'spec')
        self.assertEqual(tasks[4]['deliveryLine'], 'delivery PR #81')
        spec4 = tasks[4]['specs'][0]
        self.assertEqual(spec4['into'], 'night/spec-4')
        self.assertEqual(spec4['project'], 'project/app')
        self.assertEqual([item['number'] for item in spec4['delivery']], [81, 70])
        self.assertEqual(spec4['delivery'][0]['body'], 'ship four')

        by_n = {ticket['n']: ticket for task in loaded['tasks'] for spec in task['specs'] for ticket in spec['tickets']}
        draft = by_n[5]
        self.assertEqual(draft['pr']['number'], 51)
        self.assertEqual(draft['pr']['head']['ref'], 'ticket/issue-5')
        self.assertEqual(draft['pr']['base']['ref'], 'night/spec-4')
        self.assertTrue(draft['pr']['draft'])
        self.assertEqual(draft['grade'], 'junior-worker')
        self.assertFalse(draft['landed'])
        self.assertEqual(draft['events'], [])
        self.assertEqual(draft['fold']['sessions'], [])
        self.assertFalse(draft['fold']['landed'])
        self.assertEqual(draft['blocker_hold'], 'open')
        self.assertEqual(draft['blockers'][0]['number'], 20)
        self.assertTrue(draft['blockers'][0]['resolved'])
        self.assertEqual(draft['blockers'][0]['blocker_hold'], '')

        triage = by_n[8]
        self.assertEqual(triage['pr']['body'], 'fix the door')
        self.assertFalse(triage['pr']['draft'])
        self.assertIn('needs-triage', triage['labels'])

        human = by_n[12]
        self.assertIsNone(human['pr'])
        self.assertIsNone(human['grade'])
        self.assertFalse(human['blockers'][0]['resolved'])
        self.assertEqual(human['blockers'][0]['blocker_hold'], 'open')

        closed = by_n[13]
        self.assertEqual(closed['state'], 'closed')
        self.assertIsNone(closed['pr'])
        self.assertFalse(closed['landed'])

        landed = by_n[20]
        self.assertTrue(landed['landed'])
        self.assertEqual(landed['pr']['body'], 'landed report')
        self.assertEqual(landed['into'], 'night/spec-7')
        self.assertEqual(landed['blocker_hold'], '')

        unsent = by_n[30]
        self.assertIsNone(unsent['into'])
        self.assertIsNone(unsent['pr'])
        self.assertEqual(unsent['prs'], [])
        self.assertEqual(unsent['children'][0]['body'], 'runner failed')
        self.assertEqual(unsent['children'][0]['labels'], ['mmw:child'])
        blockers = {item['number']: item for item in unsent['blockers']}
        self.assertTrue(blockers[40]['resolved'])
        self.assertFalse(blockers[40]['ticket'])
        self.assertFalse(blockers[41]['resolved'])
        self.assertTrue(blockers[41]['ticket'])

        self.assertEqual(tasks[6]['deliveryLine'], 'delivery PR 还没有')
        self.assertIsNone(tasks[6]['specs'][0]['into'])
        self.assertIsNone(tasks[11]['specs'][0]['project'])
        self.assertEqual(tasks[11]['specs'][0]['into'], 'night/spec-11')
        self.assertEqual(tasks[11]['deliveryLine'], 'delivery PR 还没有')
        self.assertEqual(tasks[7]['state'], 'closed')
        self.assertEqual(tasks[7]['deliveryLine'], "Night's branch merged")
        self.assertEqual(tasks[7]['specs'][0]['delivery'][0]['body'], 'ship seven')

        solo = tasks[9]
        self.assertEqual(solo['kind'], 'ticket')
        self.assertEqual(solo['deliveryLine'], 'delivery PR #80')
        self.assertEqual(solo['specs'][0]['into'], 'night/ticket-9')
        self.assertEqual(solo['specs'][0]['project'], 'project/app')
        self.assertEqual(solo['specs'][0]['tickets'][0]['pr']['number'], 92)
        self.assertFalse(solo['specs'][0]['tickets'][0]['pr']['draft'])

    def test_failed_read_keeps_the_previous_board(self):
        clock = Clock()
        store = board_data.BoardStore(self.api, self.git, self.plan, self.fork, clock)
        first = store.answer()
        self.assertEqual(len(self.plan_calls), 4)
        second = store.answer()
        self.assertEqual(len(self.plan_calls), 4)
        self.assertEqual(second['tasks'], first['tasks'])

        clock.now += dt.timedelta(seconds=61)
        attempts = []

        def down(*_args, **_kwargs):
            attempts.append('down')
            raise RuntimeError('github down')

        store.plan = down
        failed = store.answer()
        self.assertEqual(attempts, ['down'])
        self.assertEqual(failed['tasks'], first['tasks'])
        self.assertEqual(failed['read_at'], first['read_at'])
        self.assertEqual(failed['read_failed']['message'], 'github down')
        self.assertEqual(store.answer()['read_failed']['message'], 'github down')
        self.assertEqual(store.answer(force=True)['read_failed']['message'], 'github down')
        self.assertEqual(attempts, ['down'])

        clock.now += dt.timedelta(seconds=61)
        self.assertEqual(store.answer()['read_failed']['message'], 'github down')
        self.assertEqual(attempts, ['down'])
        forced = store.answer(force=True)
        self.assertEqual(attempts, ['down', 'down'])
        self.assertEqual(forced['tasks'][0]['n'], 1)

        request = type('Request', (), {'command': 'POST', 'path': '/api/board/refresh'})()
        previous = board_data.STORE
        board_data.STORE = store
        try:
            status, _headers, body = board_data.handle(request)
        finally:
            board_data.STORE = previous
        self.assertEqual(status, 200)
        self.assertEqual(attempts, ['down', 'down'])
        refreshed = json.loads(body)
        self.assertEqual(refreshed['read_failed']['message'], 'github down')
        self.assertEqual(refreshed['tasks'][0]['n'], 1)


if __name__ == '__main__':
    unittest.main()
