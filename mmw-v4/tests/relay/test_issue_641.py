from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from test_ghlist import ghlist, response
from test_relay import relay, FakeGh, FakeSend, comment


class ApiPauseContracts(unittest.TestCase):
    def test_pause_then_resume_without_lost_wakes(self):
        now = [1000.0]
        for headers, wait in [('Retry-After: 120', 120),
                              ('X-RateLimit-Remaining: 0\nX-RateLimit-Reset: 1180', 180),
                              ('', 60)]:
            with self.subTest(headers=headers):
                now[0] = 1000.0
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
                now[0] += wait - 0.001
                with self.assertRaises(ghlist.ListReadError):
                    reader.read('repos/o/r/issues/11/comments?per_page=100')
                self.assertEqual(len(calls), 1, 'pause lasts until the required deadline')
                now[0] += 0.001
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

        with tempfile.TemporaryDirectory() as name:
            now[0] = datetime(2026, 10, 31, tzinfo=timezone.utc).timestamp()
            clock = lambda: datetime.fromtimestamp(now[0], timezone.utc)
            data = {11: [comment(100, 'ticket.passed', 11, updated=clock())], 12: []}
            fake = FakeGh(data)
            sent = FakeSend()
            limited = [False]
            calls = []
            def external(args):
                calls.append(args)
                if limited[0]:
                    return 1, 'HTTP/2 429 Too Many Requests\nRetry-After: 120\n\n{}', ''
                return fake(args)
            reader = relay.ghlist.ConditionalListReader(external)
            reader.clock = lambda: now[0]
            board = relay.Board('o/r', comment_reader=reader)
            state = Path(name)
            run = relay.Relay(state, board, send=sent, clock=clock, out=io.StringIO(), err=io.StringIO())
            run.open_watch({'tickets': [11, 12]}, 'paseo', 'main-a')
            self.assertTrue(run.cycle(30, 90))
            self.assertEqual([s[2] for s in sent.sent], ['#11 ticket.passed'])
            run.ack(('paseo', 'main-a'), 1)
            old = json.loads((state / 'seen.json').read_text())['tickets']
            now[0] += 30
            data[11].append(comment(101, 'ticket.returned', 11, updated=clock()))
            data[12].append(comment(102, 'ticket.passed', 12, updated=clock()))
            limited[0] = True
            before = len(calls)
            self.assertFalse(run.cycle(30, 90))
            self.assertEqual(len(calls), before + 1, 'remaining tickets must not hit the limit')
            self.assertFalse(run.cycle(30, 90))
            self.assertEqual(len(calls), before + 1)
            self.assertEqual(json.loads((state / 'seen.json').read_text())['tickets'], old)
            now[0] += 120
            limited[0] = False
            self.assertTrue(run.cycle(30, 90))
            self.assertTrue(run.cycle(30, 90))
            self.assertEqual([s[2] for s in sent.sent],
                             ['#11 ticket.passed', '#11 ticket.returned', '#12 ticket.passed'])
            fresh_reader = relay.ghlist.ConditionalListReader(external)
            restarted = relay.Relay(state, relay.Board('o/r', comment_reader=fresh_reader),
                send=sent, clock=clock, out=io.StringIO(), err=io.StringIO())
            self.assertTrue(restarted.cycle(30, 90))
            self.assertEqual(len(sent.sent), 3, 'restart must not duplicate delivered wakes')

    def test_successful_requests_reset_their_failure_streak(self):
        now = [1000.0]
        limited = [True]
        def gh(args):
            if limited[0]:
                return 1, 'HTTP/2 429 Too Many Requests\nRetry-After: 60\n\n{}', ''
            return 0, 'HTTP/2 200 OK\n\n{"data":{"repository":{}}}', ''
        reader = ghlist.ConditionalListReader(gh)
        reader.clock = lambda: now[0]
        for _ in range(6):
            limited[0] = True
            with self.assertRaises(ghlist.ListReadError):
                reader.request(['api', 'graphql', '-f', 'query=roots'])
            now[0] += 60
            limited[0] = False
            self.assertEqual(reader.request(['api', 'graphql', '-f', 'query=roots'])[0], 0)

    def test_other_successful_lists_do_not_reset_secondary_backoff(self):
        now = [1000.0]
        calls = []
        def gh(args):
            calls.append(args)
            if 'comments' in args[2]:
                return 1, 'HTTP/2 403 Forbidden\n\n{"message":"secondary rate limit"}', ''
            return response(200, [])
        reader = ghlist.ConditionalListReader(gh)
        reader.clock = lambda: now[0]
        for delay in (60, 120, 240, 480, 960):
            reader.read('repos/o/r/issues/10/sub_issues?per_page=100')
            with self.assertRaises(ghlist.ListReadError):
                reader.read('repos/o/r/issues/11/comments?per_page=100')
            self.assertEqual(reader.retry_at - now[0], delay)
            now[0] += delay
        before = len(calls)
        with self.assertRaises(ghlist.ListReadError):
            reader.read('repos/o/r/issues/11/comments?per_page=100')
        self.assertEqual(len(calls), before)
