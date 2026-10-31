from __future__ import annotations

import copy
import datetime as dt
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from test_board_data import board_data, container, event, fixture_store, scenario, tickets


class BoardRefreshContracts(unittest.TestCase):
    def test_root_discovery_complete(self):
        calls = []
        def gh(args):
            calls.append(args)
            root = next((int(a.split('=')[1]) for a in args if a.startswith('root=')), None)
            if root is not None:
                node = container(root, 'root', [], ['mmw:spec' if root == 10 else 'mmw:map'])
                return 0, json.dumps({'data': {'repository': {'issue': node}}}), ''
            if args[:2] != ['api', 'graphql']:
                return 1, '', 'root discovery must use GraphQL'
            later = 'mapsAfter=next' in args
            maps = [dict(number=2 if later else 1, title='map', state='OPEN',
                         labels={'nodes': [{'name': 'mmw:map'}]})]
            specs = [dict(number=10, title='spec', state='OPEN',
                          labels={'nodes': [{'name': 'mmw:spec'}]})]
            return 0, json.dumps({'data': {'repository': {'nameWithOwner': 'owner/repo',
                'maps': {'nodes': maps, 'pageInfo': {'hasNextPage': not later,
                                                    'endCursor': 'next' if not later else None}},
                'specs': {'nodes': specs, 'pageInfo': {'hasNextPage': False, 'endCursor': None}}}}}), ''
        store = board_data.BoardStore(gh=gh)
        result = store.answer()
        self.assertNotIn('read_failed', result)
        self.assertEqual(result['repo'], 'owner/repo')
        self.assertEqual([t['n'] for t in result['tasks']], [1, 2, 10])
        self.assertEqual(sum(not any(a.startswith('root=') for a in c) for c in calls), 2)

    def test_refresh_freshness(self):
        data = scenario()
        now = [dt.datetime(2026, 10, 31, tzinfo=dt.timezone.utc)]
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            store = fixture_store(directory, data, lambda: now[0])
            first = store.answer()
            before = (directory / 'calls.jsonl').read_text()
            now[0] += dt.timedelta(seconds=59)
            self.assertEqual(store.answer(), first)
            self.assertEqual((directory / 'calls.jsonl').read_text(), before)
            data['comments']['11'].append({'etag': 'regressed', 'comments': [
                event('ticket.regressed', 11, id=1199)]})
            data['comment_active']['11'] = 1
            data['trees'][0]['subIssues']['nodes'][3]['subIssues']['nodes'][0]['state'] = 'OPEN'
            (directory / 'scenario.json').write_text(json.dumps(data))
            now[0] += dt.timedelta(seconds=1)
            changed = store.answer()
            self.assertTrue(tickets(changed)[11]['fold']['regressed'])
            self.assertEqual(tickets(changed)[11]['state'], 'open')
            self.assertNotEqual(changed['read_at'], first['read_at'])
            data['fail_comments'] = [13]
            data['comments']['12'][0]['comments'] = []
            (directory / 'scenario.json').write_text(json.dumps(data))
            now[0] += dt.timedelta(seconds=60)
            failed = store.answer()
            self.assertIn('read_failed', failed)
            self.assertEqual(failed['tasks'], changed['tasks'])
            self.assertEqual(failed['read_at'], changed['read_at'])
            self.assertEqual(store.snapshot, changed)

    def test_overlapping_refresh(self):
        data = scenario()
        now = [dt.datetime(2026, 10, 31, tzinfo=dt.timezone.utc)]
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            store = fixture_store(directory, data, lambda: now[0])
            store.answer()
            now[0] += dt.timedelta(seconds=60)
            before = len((directory / 'calls.jsonl').read_text().splitlines())
            gate, release = threading.Event(), threading.Event()
            gh = store.gh
            def blocked(args):
                if 'mapsMore=true' in args:
                    gate.set()
                    self.assertTrue(release.wait(5), 'refresh was not released')
                return gh(args)
            store.gh = blocked
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(store.answer)
                self.assertTrue(gate.wait(5), 'expired refresh did not query roots')
                second = pool.submit(store.answer)
                release.set()
                self.assertEqual(first.result(5), second.result(5))
            calls = [json.loads(line) for line in (directory / 'calls.jsonl').read_text().splitlines()[before:]]
            self.assertEqual(sum('mapsMore=true' in c for c in calls), 1)
