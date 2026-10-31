from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from test_ghlist import ghlist, response
from test_relay import relay


class ApiPauseContracts(unittest.TestCase):
    def test_pause_then_resume_without_lost_wakes(self):
        now = [1000.0]
        for headers, wait in [('Retry-After: 120', 120),
                              ('X-RateLimit-Remaining: 0\nX-RateLimit-Reset: 1180', 180),
                              ('', 60)]:
            with self.subTest(headers=headers):
                calls = []
                limited = [True]
                def gh(args):
                    calls.append(args)
                    if limited[0]:
                        return 1, f'HTTP/2 403 Forbidden\n{headers}\n\n'+json.dumps({'message': 'secondary rate limit'}), ''
                    return response(200, [])
                reader = ghlist.ConditionalListReader(gh)
                reader.clock = lambda: now[0]
                for _ in range(2):
                    with self.assertRaises(ghlist.ListReadError):
                        reader.read('repos/o/r/issues/11/comments?per_page=100')
                self.assertEqual(len(calls), 1, 'no requests during server pause')
                now[0] += wait
                limited[0] = False
                self.assertEqual(reader.read('repos/o/r/issues/11/comments?per_page=100'), [])
                self.assertEqual(len(calls), 2)
        calls = []
        def forbidden(args):
            calls.append(args)
            return 1, 'HTTP/2 403 Forbidden\n\n{"message":"Resource not accessible"}', ''
        reader = ghlist.ConditionalListReader(forbidden)
        for _ in range(2):
            with self.assertRaises(ghlist.ListReadError):
                reader.read('repos/o/r/issues/11/comments?per_page=100')
        self.assertEqual(len(calls), 2, 'permission errors do not trigger rate pause')
