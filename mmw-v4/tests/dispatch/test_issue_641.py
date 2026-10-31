from __future__ import annotations

import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from test_status import status


class SummaryReadContracts(unittest.TestCase):
    def test_summary_reuses_complete_ticket_reads(self):
        calls = []
        def opened(ticket, child):
            body = status.events.build('child.opened', ticket=ticket, spec=10,
                at='2026-10-31T00:00:00Z', line='finding opened', child=child, kind='finding', title='fix')
            return {'body': body}
        raw = {n: {'state': 'OPEN', 'title': f'issue {n}', 'labels': [], 'comments': []}
               for n in (11, 12, 30)}
        raw[11]['comments'] = [opened(11, 30)]
        raw[12]['comments'] = [opened(12, 30)]
        raw[30]['createdAt'] = '2999-01-01T00:00:00Z'
        def external(command, **kwargs):
            args = command[1:]
            if args[:2] == ['issue', 'view']:
                number = int(args[2])
                calls.append(number)
                value = copy.deepcopy(raw[number])
            elif args[:2] == ['api', 'graphql']:
                value = {'data': {'repository': {'issue': {'number': 10, 'title': 'spec', 'state': 'OPEN',
                    'subIssuesSummary': {'total': 2, 'completed': 0},
                    'subIssues': {'nodes': [{'number': n, 'title': f'issue {n}', 'state': 'OPEN',
                        'subIssuesSummary': {'total': 0, 'completed': 0}, 'subIssues': {'nodes': []}}
                        for n in (11, 12)]}}}}}
            else:
                raise AssertionError(command)
            return SimpleNamespace(returncode=0, stdout=json.dumps(value), stderr='')
        with patch.object(status.subprocess, 'run', side_effect=external):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(status.print_summary(10), 0)
            self.assertIn('Sub-issues opened tonight: #30 issue 30', out.getvalue())
            self.assertIn('Findings routed: 1/0/0/0/0/1', out.getvalue())
            self.assertEqual(calls, [11, 12, 30], 'N+C complete ticket reads per command')
            calls.clear()
            children = status.batch_children(10)
            self.assertEqual([(c['number'], c['owner']) for c in children], [(30, 11)])
            raw[30]['title'] = 'changed outside the command'
            calls.clear()
            out = io.StringIO()
            with redirect_stdout(out):
                status.print_summary(10)
            self.assertIn('#30 changed outside the command', out.getvalue())
            self.assertEqual(calls, [11, 12, 30])
