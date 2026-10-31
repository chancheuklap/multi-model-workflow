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
