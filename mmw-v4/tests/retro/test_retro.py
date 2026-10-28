import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'mmw-v4/skills/retro/scripts/retro.py'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


retro = load(SCRIPT, 'retro_test')
events = load(ROOT / 'mmw-v4/skills/verify-ticket/scripts/events.py', 'retro_test_events')
REAL_RUN = subprocess.run
REPO = 'o/r'
NOW = '2026-10-14T00:00:00Z'


def seen(ticket=61, source='noticed', at='2026-09-13T00:00:00Z', session='none', spec=76):
    return events.build('lesson.seen', ticket=ticket, spec=spec, lesson=90,
                        seen_in=REPO, source=source, session=session, at=at, line='Seen')


def issue(number=90, angle='环境', bodies=None, labels=('mmw:lesson',), state='open', parent=None):
    return dict(number=number, title=f'Problem {number}', body=f'## Problem\n\n问题代号：missing-information\n角度：{angle}\n发生了什么：信息拿不到\n证据：README.md:1\n代价：耽误工作\n该谁修：o/r\n',
                labels=[dict(name=n) for n in labels], state=state, state_reason=None,
                parent=parent, created_at='2026-09-01T00:00:00Z', updated_at=NOW,
                comments=[dict(id=i, body=b, html_url=f'https://github.com/o/r/issues/{number}#issuecomment-{i}')
                          for i, b in enumerate(bodies or [], 1)])


class Fake:
    def __init__(self, rows, repo=REPO):
        self.repo = repo
        self.rows = {r['number']: r for r in rows}
        self.calls = []

    def __call__(self, args, **kwargs):
        if args[0] != 'gh':
            return REAL_RUN(args, **kwargs)
        self.calls.append(args)
        a = args[1:]
        out = ''
        if a[:2] == ['repo', 'view']:
            out = json.dumps(dict(nameWithOwner=self.repo))
        elif a[0] == 'api':
            endpoint = a[1]
            if endpoint == 'graphql':
                out = json.dumps({'data':{'repository':{'issue':{'timelineItems':{'nodes':[]}}}}})
                rows = None
            elif '/comments?' in endpoint:
                n = int(endpoint.split('/issues/')[1].split('/')[0])
                rows = self.rows[n]['comments']
            elif '/sub_issues?' in endpoint:
                n = int(endpoint.split('/issues/')[1].split('/')[0])
                rows = [r for r in self.rows.values() if r.get('parent') == dict(number=n)]
            elif '/issues?' in endpoint:
                rows = [r for r in self.rows.values()
                        if r.get('repo', self.repo) == endpoint.split('/issues?')[0].removeprefix('repos/')]
                if 'labels=mmw%3Alesson' in endpoint or 'labels=mmw:lesson' in endpoint:
                    rows = [r for r in rows if {'name':'mmw:lesson'} in r['labels']]
            elif '/issues/comments/' in endpoint:
                n = int(endpoint.rsplit('/',1)[1])
                out = json.dumps(next(c for r in self.rows.values() for c in r['comments'] if c['id'] == n))
                rows = None
            elif '/issues/' in endpoint:
                n = int(endpoint.rsplit('/',1)[1])
                out = json.dumps(self.rows[n])
                rows = None
            else:
                raise AssertionError(args)
            if rows is not None:
                self.assert_pagination(a)
                out = json.dumps([rows[:1], rows[1:]])
        elif a[:2] == ['issue', 'view']:
            r = self.rows[int(a[2])]
            result = {k: r.get(k) for k in a[a.index('--json')+1].split(',')}
            if 'state' in result:
                result['state'] = result['state'].upper()
            out = json.dumps(result)
        elif a[:2] == ['label','create']:
            out = ''
        elif a[:2] == ['issue','create']:
            n = 101+len(self.rows)
            self.rows[n] = issue(n,bodies=[],labels=(a[a.index('--label')+1],))
            self.rows[n]['body'] = Path(a[a.index('--body-file')+1]).read_text()
            out = f'https://github.com/o/r/issues/{n}'
        elif a[:2] == ['issue', 'comment']:
            r = self.rows[int(a[2])]
            body = Path(a[a.index('--body-file')+1]).read_text()
            n = 100 + len(r['comments'])
            r['comments'].append(dict(id=n,body=body,html_url=f'https://github.com/o/r/issues/{r["number"]}#issuecomment-{n}'))
        elif a[:2] == ['issue', 'close']:
            r = self.rows[int(a[2])]
            r['state'] = 'closed'
            r['state_reason'] = a[a.index('--reason')+1]
            if '--duplicate-of' in a:
                r['duplicate_of'] = a[a.index('--duplicate-of')+1]
        elif a[:2] == ['issue', 'reopen']:
            self.rows[int(a[2])]['state'] = 'open'
            self.rows[int(a[2])]['state_reason'] = None
        elif a[:2] == ['issue','transfer']:
            r = self.rows.pop(int(a[2]))
            r['number'] = 99
            r['transferred_to'] = a[3]
            self.rows[99] = r
            out = f'https://github.com/{a[3]}/issues/99'
        elif a[:2] == ['issue', 'edit']:
            r = self.rows[int(a[2])]
            if '--add-label' in a:
                r['labels'].append(dict(name=a[a.index('--add-label')+1]))
            if '--body-file' in a:
                r['body'] = Path(a[a.index('--body-file')+1]).read_text()
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(args, 0, out, '')

    @staticmethod
    def assert_pagination(a):
        assert '--paginate' in a and '--slurp' in a, a


class Commands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.fake = Fake([issue(bodies=[seen()])])
        self.env = patch.dict(os.environ, MMW_NOW=NOW, MMW_HOME=str(self.root/'home'))
        self.env.start()
        for key in ('ORCA_TERMINAL_HANDLE','PASEO_AGENT_ID','HERDR_PANE_ID','MMW_TICKET','MMW_SPEC'):
            os.environ.pop(key,None)
        self.addCleanup(self.env.stop)

    def run_command(self, *args):
        with patch.object(subprocess, 'run', side_effect=self.fake), redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            rc = retro.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def start_run(self):
        self.fake.rows[76] = issue(76, labels=('mmw:spec',), bodies=[events.build('spec.opened', ticket=None, spec=76, line='Opened', at='2026-09-01T00:00:00Z')])
        REAL_RUN(['git','init','-q',str(self.root)],check=True)
        REAL_RUN(['git','-C',str(self.root),'config','user.email','test@example.invalid'],check=True)
        REAL_RUN(['git','-C',str(self.root),'config','user.name','Test'],check=True)
        (self.root/'README.md').write_text('Evidence\n')
        REAL_RUN(['git','-C',str(self.root),'add','README.md'],check=True)
        REAL_RUN(['git','-C',str(self.root),'commit','-qm','initial'],check=True)
        self.previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous)

    def test_backlog_lists_open_lessons_with_assessments(self):
        assessment = events.build('lesson.assessed', ticket=61, line='Still present',
                                  conclusion='candidate', reason='Still present', evidence='README.md:1',
                                  plan='', run='o/r#61', qualifies=False, request='assessment-1')
        self.fake.rows[90]['comments'].append(dict(id=2, body=assessment))
        self.fake.rows[91] = issue(91, state='closed')
        self.fake.rows[92] = issue(92, labels=('mmw:ticket',))
        self.fake.rows[93] = issue(93, bodies=[seen(ticket=62)])
        self.fake.rows[93]['repo'] = 'other/product'
        self.fake.rows[90]['body'] += '\n## Other\nNot the problem.\n'
        rc, out, err = self.run_process('backlog', REPO, 'other/product', '--out', str(self.root/'backlog'))
        self.assertEqual(rc, 0, err)
        self.assertIn('BACKLOG 2 open, 1 assessed since last merge', out)
        rows = json.loads((self.root/'backlog/backlog.json').read_text())
        self.assertEqual([r['number'] for r in rows], [90, 93])
        self.assertEqual(rows[0]['repo'], REPO)
        self.assertIn('发生了什么：信息拿不到', rows[0]['problem'])
        self.assertNotIn('Not the problem', rows[0]['problem'])
        self.assertEqual(rows[0]['occurrences'], [dict(seen_in=REPO, spec=76, ticket=61,
                         session='none', source='noticed', at='2026-09-13T00:00:00Z')])
        self.assertEqual(rows[0]['assessments'], [events.parse(assessment)[1]])
        self.assertIsNone(rows[0]['merged'])
        self.assertEqual(rows[1]['assessments'], [])
        self.assertEqual(rows[1]['repo'], 'other/product')
        self.assertFalse(any(call[1:3] in (['issue','comment'], ['issue','close'])
                             for call in self.fake.calls))

    def test_backlog_counts_assessments_since_the_last_merge(self):
        def assessed(request):
            return events.build('lesson.assessed', ticket=61, at=NOW, line='Assessment',
                                conclusion='candidate', reason='Still present', evidence='README.md:1',
                                plan='', run='o/r#61', qualifies=False, request=request)
        merged = events.build('lessons.merged', ticket=None, at=NOW, line='Kept',
                              decision='kept', batch='latest')
        self.fake.rows[90] = issue(bodies=[assessed('old-1'), events.build(
            'lessons.merged', ticket=None, at=NOW, line='Kept earlier', decision='kept', batch='earlier'),
            assessed('old-2'), merged, assessed('new-1'), assessed('new-2')])
        self.fake.rows[90]['comments'].reverse()
        self.fake.rows[91] = issue(91, bodies=[assessed('never-merged')])
        self.fake.rows[92] = issue(92, state='closed', bodies=[assessed('closed')])
        rc, out, err = self.run_process('backlog', REPO, REPO, '--out', str(self.root/'backlog'))
        self.assertEqual(rc, 0, err)
        self.assertIn('BACKLOG 2 open, 3 assessed since last merge', out)
        rows = json.loads((self.root/'backlog/backlog.json').read_text())
        self.assertEqual(rows[0]['merged'], events.parse(merged)[1])
        self.assertEqual([a['request'] for a in rows[0]['assessments']],
                         ['old-1', 'old-2', 'new-1', 'new-2'])

    def test_merge_apply_carries_out_the_decisions_once(self):
        self.fake.rows[91] = issue(91, bodies=[seen(ticket=62), seen(ticket=63)])
        self.fake.rows[92] = issue(92, bodies=[seen(ticket=64)])
        self.fake.rows[93] = issue(93, bodies=[seen(ticket=65)])
        path = self.root/'decisions.json'
        path.write_text(json.dumps(dict(batch='owner-approved-1', decisions=[
            dict(lesson='o/r#90', decision='closed', reason='Already fixed'),
            dict(lesson='o/r#91', decision='merged:o/r#92', reason='Same root cause'),
            dict(lesson='o/r#93', decision='kept', reason='Wait for more evidence')])) )
        rc, out, err = self.run_process('merge-apply', str(path))
        self.assertEqual(rc, 0, err)
        self.assertEqual((self.fake.rows[90]['state'], self.fake.rows[90]['state_reason']),
                         ('closed', 'not planned'))
        self.assertEqual((self.fake.rows[91]['state'], self.fake.rows[91]['state_reason'],
                          self.fake.rows[91]['duplicate_of']),
                         ('closed', 'duplicate', 'https://github.com/o/r/issues/92'))
        self.assertEqual(self.fake.rows[93]['state'], 'open')
        self.assertEqual([o['ticket'] for o in events.fold(self.fake.rows[92]['comments'])['occurrences']],
                         [64, 62, 63])
        for number, decision, reason in ((90, 'closed', 'Already fixed'),
                                         (91, 'merged:o/r#92', 'Same root cause'),
                                         (93, 'kept', 'Wait for more evidence')):
            comment = self.fake.rows[number]['comments'][-1]['body']
            record = events.parse(comment)[1]
            self.assertEqual((record['event'], record['batch'], record['decision']),
                             ('lessons.merged', 'owner-approved-1', decision))
            self.assertIn(reason, comment)
        before = json.loads(json.dumps(list(self.fake.rows.values())))
        self.fake.calls.clear()
        rc, out, err = self.run_process('merge-apply', str(path))
        self.assertEqual(rc, 0, err)
        self.assertEqual(list(self.fake.rows.values()), before)
        self.assertFalse(any(c[1:3] in (['issue','comment'], ['issue','close']) for c in self.fake.calls))

    def test_merge_apply_resumes_after_each_lost_write_response(self):
        path = self.root/'decisions.json'
        path.write_text(json.dumps(dict(batch='retry-batch', decisions=[
            dict(lesson='o/r#90', decision='merged:o/r#91', reason='Same root cause'),
            dict(lesson='o/r#92', decision='closed', reason='Fixed'),
            dict(lesson='o/r#93', decision='kept', reason='Keep observing')])))
        for fail_at in range(1, 7):
            with self.subTest(write=fail_at):
                tracker = Fake([issue(bodies=[seen()]), issue(91), issue(92), issue(93)])
                writes = 0
                def lose_response(args, **kwargs):
                    nonlocal writes
                    result = tracker(args, **kwargs)
                    if args[1:3] in (['issue', 'comment'], ['issue', 'close']):
                        writes += 1
                        if writes == fail_at:
                            return subprocess.CompletedProcess(args, 1, '', 'response lost')
                    return result
                self.fake = lose_response
                rc, out, err = self.run_command('merge-apply', str(path))
                self.assertEqual(rc, 1, err)
                self.fake = tracker
                rc, out, err = self.run_process('merge-apply', str(path))
                self.assertEqual(rc, 0, err)
                self.assertEqual(len(events.fold(self.fake.rows[91]['comments'])['occurrences']), 1)
                for number in (90, 92, 93):
                    records = [events.parse(c['body'])[1] for c in self.fake.rows[number]['comments']]
                    self.assertEqual(len([r for r in records if r['event'] == 'lessons.merged']), 1)
                self.assertEqual(self.fake.rows[90]['state_reason'], 'duplicate')
                self.assertEqual(self.fake.rows[92]['state_reason'], 'not planned')
                self.assertEqual(self.fake.rows[93]['state'], 'open')

    def test_merge_apply_validates_the_whole_batch_before_writing(self):
        path = self.root/'decisions.json'
        self.fake.rows[91] = issue(91, labels=('mmw:ticket',))
        for second in (dict(lesson='o/r#91', decision='kept', reason='Not a lesson'),
                       dict(lesson='o/r#90', decision='kept', reason='Conflicting duplicate')):
            with self.subTest(second=second):
                path.write_text(json.dumps(dict(batch='bad-batch', decisions=[
                    dict(lesson='o/r#90', decision='closed', reason='Fixed'), second])))
                rc, out, err = self.run_process('merge-apply', str(path))
                self.assertEqual(rc, 2, err)
                self.assertEqual(self.fake.rows[90]['state'], 'open')
                self.assertEqual(len(self.fake.rows[90]['comments']), 1)

    def test_merge_apply_refuses_self_merge(self):
        path = self.root/'self-merge.json'
        path.write_text(json.dumps(dict(batch='self-merge', decisions=[
            dict(lesson='o/r#90', decision='merged:o/r#90', reason='Self merge')])))
        rc, out, err = self.run_process('merge-apply', str(path))
        self.assertEqual(rc, 2, err)
        self.assertEqual(self.fake.rows[90]['state'], 'open')
        self.assertEqual(len(self.fake.rows[90]['comments']), 1)

    def test_merge_apply_normalizes_registration_identity_before_conflict_checks(self):
        self.fake.rows[91] = issue(91)
        path = self.root/'case-conflicts.json'
        cases = [
            [dict(lesson='o/r#90', decision='closed', reason='Fixed'),
             dict(lesson='O/R#90', decision='kept', reason='Keep')],
            [dict(lesson='O/R#91', decision='closed', reason='Fixed'),
             dict(lesson='o/r#90', decision='merged:o/r#91', reason='Same cause')],
        ]
        for decisions in cases:
            with self.subTest(decisions=decisions):
                self.fake = Fake([issue(bodies=[seen()]), issue(91)])
                path.write_text(json.dumps(dict(batch='case-conflicts', decisions=decisions)))
                rc, out, err = self.run_process('merge-apply', str(path))
                self.assertEqual(rc, 2, err)
                self.assertFalse(any(c[1:3] in (['issue','comment'], ['issue','close'])
                                     for c in self.fake.calls))

    def test_merge_apply_refuses_a_closed_destination_before_writing(self):
        self.fake.rows[91] = issue(91, state='closed')
        path = self.root/'closed-target.json'
        path.write_text(json.dumps(dict(batch='closed-target', decisions=[
            dict(lesson='o/r#90', decision='merged:o/r#91', reason='Same cause')])))
        rc, out, err = self.run_process('merge-apply', str(path))
        self.assertEqual(rc, 2, err)
        self.assertIn('o/r#91', err)
        self.assertIn('open', err)
        self.assertEqual(self.fake.rows[90]['state'], 'open')
        self.assertEqual(self.fake.rows[91]['comments'], [])

    def test_merge_apply_names_the_file_and_malformed_field(self):
        path = self.root/'malformed-decisions.json'
        for data, field in (([], 'object'), ({'decisions': []}, 'batch'),
                            ({'batch': 'bad', 'decisions': [dict(lesson='o/r#90', decision='kept')]}, 'reason')):
            with self.subTest(data=data):
                path.write_text(json.dumps(data))
                rc, out, err = self.run_process('merge-apply', str(path))
                self.assertEqual(rc, 2, err)
                self.assertIn(str(path), err)
                self.assertIn(field, err)
                self.assertEqual(len(self.fake.rows[90]['comments']), 1)

    def test_gather_window_starts_at_the_first_claim(self):
        self.start_run()
        bodies = [events.build('ticket.claimed', ticket=61, line='Claimed',
                               at=f'2026-09-{day:02}T00:00:00Z') for day in (1, 3, 5, 7)]
        bodies.insert(1, events.build('child.opened', ticket=61, child=91, kind='fault',
                                    title='First round failure', line='Fault', at='2026-09-02T00:00:00Z'))
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',), bodies=bodies)
        rc, out, err = self.run_command('gather', '--ticket', '61', REPO, '--out', str(self.root/'materials'))
        self.assertEqual(rc, 0, err)
        context = json.loads((self.root/'materials/context.json').read_text())
        self.assertEqual(context['since'], '2026-09-01T00:00:00Z')
        material = json.loads((self.root/'materials/process.md').read_text().split('\n\n', 1)[1])
        self.assertEqual([r['event']['child'] for r in material if r['kind'] == 'signal'], [91])

    def test_gather_window_covers_the_half_before_a_suspend(self):
        self.start_run()
        self.fake.rows[76]['comments'].extend([
            dict(id=2, body=events.build('spec.suspended', spec=76, ticket=None, line='Suspended',
                                         at='2026-09-14T00:00:00Z')),
            dict(id=3, body=events.build('spec.opened', spec=76, ticket=None, line='Resumed',
                                         at='2026-09-15T00:00:00Z'))])
        self.fake.rows[90]['created_at'] = '2026-09-13T00:00:00Z'
        rc, out, err = self.run_command('gather', '--spec', '76', REPO, '--out', str(self.root/'materials'))
        self.assertEqual(rc, 0, err)
        context = json.loads((self.root/'materials/context.json').read_text())
        self.assertEqual(context['since'], '2026-09-01T00:00:00Z')
        self.assertEqual(context['registered'], 1)
        material = json.loads((self.root/'materials/environment.md').read_text().split('\n\n', 1)[1])
        self.assertEqual([r['kind'] for r in material], ['registration'])

    def test_gather_window_starts_after_the_last_retrospective(self):
        self.start_run()
        receipt = events.build('ticket.retroed', ticket=61, line='Earlier receipt',
                               at='2026-09-10T00:00:00Z', result='recorded', registered=0,
                               merged=0, rejected=0, candidates=0, proposals=0,
                               recurred_after_wontfix=[], landed_since_last=0,
                               evidence='complete', unreadable_sources=[])
        bodies = [events.build('ticket.claimed', ticket=61, line='Claimed', at='2026-09-01T00:00:00Z'),
                  receipt,
                  events.build('ticket.claimed', ticket=61, line='Restarted', at='2026-09-11T00:00:00Z'),
                  events.build('ticket.claimed', ticket=61, line='Retry', at='2026-09-14T00:00:00Z')]
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',), bodies=bodies)
        self.fake.rows[90]['comments'].append(dict(id=2, body=seen(at='2026-09-05T00:00:00Z')))
        rc, out, err = self.run_command('gather', '--ticket', '61', REPO, '--out', str(self.root/'materials'))
        self.assertEqual(rc, 0, err)
        context = json.loads((self.root/'materials/context.json').read_text())
        self.assertEqual(context['since'], '2026-09-11T00:00:00Z')
        self.assertIn('missing-information', context['issues'])

    def test_gather_refuses_when_nothing_started_since_the_receipt(self):
        self.start_run()
        self.fake.rows[76]['comments'].append(dict(id=812, body=events.build(
            'spec.retroed', spec=76, ticket=None, line='Already reviewed',
            at='2026-09-15T00:00:00Z', result='recorded', registered=0,
            merged=0, rejected=0, candidates=0, proposals=0, recurred_after_wontfix=[],
            landed_since_last=0, evidence='complete', unreadable_sources=[])))
        rc, out, err = self.run_command('gather', '--spec', '76', REPO, '--out', str(self.root/'materials'))
        self.assertEqual(rc, 2, err)
        self.assertIn('https://github.com/o/r/issues/76#issuecomment-812', err)
        self.assertFalse((self.root/'materials').exists())

    def test_gather_orphans_are_this_runs_only(self):
        self.start_run()
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',), state='closed', parent=dict(number=76))
        self.fake.rows[62] = issue(62, labels=('mmw:ticket',), state='closed')
        self.fake.rows[91] = issue(91, labels=('mmw:child',), parent=dict(number=61))
        self.fake.rows[92] = issue(92, labels=('mmw:child',), parent=dict(number=62))
        rc, out, err = self.run_command('gather', '--spec', '76', REPO, '--out', str(self.root/'materials'))
        self.assertEqual(rc, 0, err)
        material = json.loads((self.root/'materials/process.md').read_text().split('\n\n', 1)[1])
        self.assertEqual([r['source'] for r in material if r['kind'] == 'orphaned-child'],
                         ['https://github.com/o/r/issues/91'])

    def test_gather_lists_contract_children_with_their_settlement(self):
        self.start_run()
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',), parent=dict(number=76), bodies=[
            events.build('child.opened', ticket=61, child=91, kind='contract', line='Missing case',
                         at='2026-09-02T00:00:00Z'),
            events.build('child.closed', ticket=61, child='91', resolution='fixed',
                         line='The orchestrator added the missing case', at='2026-09-03T00:00:00Z'),
            events.build('child.opened', ticket=61, child=92, kind='contract', line='Another gap',
                         at='2026-09-04T00:00:00Z')])
        self.fake.rows[91] = issue(91, labels=('mmw:child',), parent=dict(number=61))
        self.fake.rows[92] = issue(92, labels=('mmw:child',), parent=dict(number=61))
        self.fake.rows[91]['body'] = 'Contract 91 needs the missing case.'
        self.fake.rows[92]['body'] = 'Contract 92 needs another field.'
        rc, out, err = self.run_command('gather', '--spec', '76', REPO, '--out', str(self.root/'materials'))
        self.assertEqual(rc, 0, err)
        self.assertTrue((self.root/'materials/process.md').exists(), 'contract signals produce process materials')
        material = json.loads((self.root/'materials/process.md').read_text().split('\n\n', 1)[1])
        signals = [r for r in material if r['kind'] == 'signal']
        self.assertEqual([r['event']['child'] for r in signals], [91, 92])
        self.assertEqual(signals[0]['child_body'], 'Contract 91 needs the missing case.')
        self.assertEqual(signals[0]['settlement'], self.fake.rows[61]['comments'][1]['body'])
        self.assertEqual(signals[1]['child_body'], 'Contract 92 needs another field.')
        self.assertIn('not yet settled', signals[1]['settlement'])

        fixture = json.loads((Path(__file__).parent/'fixtures'/'settled-contract-1358.json').read_text())
        self.fake.rows[1350] = issue(1350, labels=('mmw:ticket',), bodies=[events.build(
            'ticket.claimed', ticket=1350, line='Claimed', at='2026-10-27T11:21:51Z')])
        self.fake.rows[1350]['comments'].extend(fixture)
        self.fake.rows[1358] = issue(1358, labels=('mmw:child',), parent=dict(number=1350))
        self.fake.rows[1358]['body'] = 'The historical fault child does not exist.'
        rc, out, err = self.run_command('gather', '--ticket', '1350', REPO,
                                        '--out', str(self.root/'real-settlement'))
        self.assertEqual(rc, 0, err)
        material = json.loads((self.root/'real-settlement/process.md').read_text().split('\n\n', 1)[1])
        signals = [r for r in material if r['kind'] == 'signal']
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]['child_body'], 'The historical fault child does not exist.')
        self.assertEqual(signals[0]['settlement'], fixture[1]['body'])

    def test_gather_replays_the_three_real_misses(self):
        self.start_run()
        cases = [(1165, '2026-10-19T07:25:26Z', {1166}),
                 (1618, '2026-10-26T13:05:51Z', {1633, 1634}),
                 (1418, '2026-10-21T11:24:21Z', {1431, 1432, 1435, 1436, 1437, 1440})]
        for number, since, children in cases:
            with self.subTest(run=number):
                fixture = json.loads((Path(__file__).parent/'fixtures'/f'run-{number}.json').read_text())
                self.fake = Fake(fixture['rows'], repo=fixture['repo'])
                material_dir = self.root/f'materials-{number}'
                with patch.dict(os.environ, MMW_NOW=fixture['as_of']):
                    rc, out, err = self.run_process('gather', f'--{fixture["mode"]}', str(number),
                                                    fixture['repo'], '--out', str(material_dir))
                self.assertEqual(rc, 0, err)
                context = json.loads((material_dir/'context.json').read_text())
                self.assertEqual(context['since'], since)
                self.assertTrue((material_dir/'process.md').exists(), 'real missed contracts produce material')
                material = json.loads((material_dir/'process.md').read_text().split('\n\n', 1)[1])
                signals = [r for r in material if r['kind'] == 'signal']
                self.assertEqual({r['event']['child'] for r in signals}, children)
                for signal in signals:
                    child = self.fake.rows[signal['event']['child']]
                    self.assertEqual(signal['child_body'], child['body'])

    def test_gather_writes_only_the_angles_with_material(self):
        self.start_run()
        rc, out, err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        self.assertEqual(sorted(p.name for p in (self.root/'materials').glob('*.md')), ['environment.md'])
        material = (self.root/'materials/environment.md').read_text()
        self.assertIn('missing-information',material)
        self.assertIn('environment.md',out)

    def test_gather_lists_an_orphaned_child(self):
        self.start_run()
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',),state='closed',parent=dict(number=76))
        self.fake.rows[91] = issue(91,labels=('mmw:child',),parent=dict(number=61))
        self.fake.rows[92] = issue(92,labels=('mmw:child',),parent=dict(number=61))
        self.fake.rows[61]['comments'].append(dict(id=1,body=events.build('child.closed',ticket=61,child=92,resolution='fixed',line='Resolved child')))
        self.fake.rows[62] = issue(62,labels=('mmw:ticket',))
        self.fake.rows[93] = issue(93,labels=('mmw:child',),parent=dict(number=62))
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        files = '\n'.join(p.read_text() for p in (self.root/'materials').glob('*.md'))
        self.assertIn('orphaned-child',files)
        self.assertIn('https://github.com/o/r/issues/91',files)
        self.assertNotIn('https://github.com/o/r/issues/92',files)
        self.assertNotIn('https://github.com/o/r/issues/93',files)

    def test_gather_excludes_needs_triage_children_but_lists_orphans(self):
        self.start_run()
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',),state='closed',parent=dict(number=76))
        self.fake.rows[91] = issue(91,labels=('mmw:child','needs-triage'),parent=dict(number=61))
        self.fake.rows[92] = issue(92,labels=('mmw:child',),parent=dict(number=61))
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        material = (self.root/'materials/process.md').read_text()
        rows = json.loads(material.split('\n\n',1)[1])
        self.assertEqual(rows, [dict(kind='orphaned-child',
                                    source='https://github.com/o/r/issues/92',
                                    parent='https://github.com/o/r/issues/61')])

    def test_gather_lists_a_reverted_commit(self):
        self.start_run()
        (self.root/'before.txt').write_text('before merge\n')
        REAL_RUN(['git','add','before.txt'],check=True)
        REAL_RUN(['git','commit','-qm','before merge'],check=True)
        old = REAL_RUN(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        REAL_RUN(['git','revert','--no-edit',old],capture_output=True,check=True)
        base = REAL_RUN(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        (self.root/'change.txt').write_text('change\n')
        REAL_RUN(['git','add','change.txt'],check=True)
        REAL_RUN(['git','commit','-qm','change'],check=True)
        change = REAL_RUN(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        REAL_RUN(['git','revert','--no-edit',change],capture_output=True,check=True)
        self.fake.rows[75] = issue(75,labels=('mmw:spec',),state='closed',bodies=[events.build('spec.merged',ticket=None,spec=75,line='Merged',at='2026-08-01T00:00:00Z',into='night',project='main',merge=base,base=base)])
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        files = '\n'.join(p.read_text() for p in (self.root/'materials').glob('*.md'))
        self.assertIn('reverted-commit',files)
        self.assertIn(change,files)
        self.assertNotIn(old,files)

    def answer(self, conclusion='candidate', evidence='README.md:1', plan='', code='missing-information'):
        path = self.root/'answer.md'
        path.write_text(f'| 代号 | 结论 | 理由 | 证据 | 方案 |\n| --- | --- | --- | --- | --- |\n| {code} | {conclusion} | 检查仍不可靠 | {evidence} | {plan} |\n\n## Problems\nNone\n')
        context = dict(repo=REPO,spec=76,ticket=None,since='2026-09-01T00:00:00Z',registered=0,landed_since_last=0,
                       recurred_after_wontfix=[],evidence='complete',unreadable_sources=[],issues={'missing-information':dict(repo=REPO,number=90)})
        (self.root/'context.json').write_text(json.dumps(context))
        return str(path)

    def assessment_answer(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/mmw/toolbox.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        for number in (91, 92, 93, 94):
            self.fake.rows[number] = issue(number, bodies=[seen()])
        self.fake.rows[91]['comments'].append(dict(id=2,body=seen(ticket=62)))
        self.fake.rows[92]['labels'].append(dict(name='needs-triage'))
        self.fake.rows[94].update(state='closed',state_reason='completed',closed_at='2026-09-12T00:00:00Z')
        path = Path(self.answer('reject'))
        path.write_text(path.read_text().replace('## Problems',
            '| 91 | merge:94 | 同一根因 | README.md:1 | |\n'
            '| 92 | propose | 需要检查 | README.md:1 | 仓库：mmw/toolbox；加：检查；文件：check.py；Playbook: Bug fix |\n'
            '| 93 | candidate | 待积累 | README.md:1 | |\n'
            '| 93 | candidate | 另一角度 | README.md:1 | 继续观察 |\n\n## Problems'))
        return str(path)

    def test_apply_changes_no_registration_state(self):
        path = self.assessment_answer()
        self.fake.rows[92]['comments'] = [dict(id=1,body=seen(source='stall'))]
        self.fake.rows[92]['labels'] = [dict(name='mmw:lesson')]
        before = {n: {k: v for k,v in row.items() if k != 'comments'}
                  for n,row in self.fake.rows.items()}
        before = json.loads(json.dumps(before))
        rc,out,err = self.run_process('apply',path)
        self.assertEqual(rc,0,err)
        forbidden = [call for call in self.fake.calls
                     if call[1:3] in (['issue','close'], ['issue','reopen'], ['issue','transfer'],
                                      ['issue','edit'], ['label','create'])]
        self.assertEqual(forbidden, [])
        after = {str(n): {k: v for k,v in row.items() if k != 'comments'}
                 for n,row in self.fake.rows.items()}
        self.assertEqual(after, before)
        self.assertEqual(events.fold(self.fake.rows[94]['comments'])['occurrences'],
                         events.fold([seen()])['occurrences'])

    def test_apply_records_each_row_as_lesson_assessed(self):
        path = self.assessment_answer()
        rc,out,err = self.run_process('apply',path)
        self.assertEqual(rc,0,err)
        rows = {n: [events.parse(c['body'])[1] for c in self.fake.rows[n]['comments']
                    if events.parse(c['body'])[0] == 'event'
                    and events.parse(c['body'])[1]['event'] == 'lesson.assessed']
                for n in (90, 91, 92, 93)}
        self.assertEqual([len(rows[n]) for n in (90,91,92,93)], [1,1,1,2])
        expected = [('reject', '检查仍不可靠', '', False),
                    ('merge:94', '同一根因', '', True),
                    ('propose', '需要检查', '仓库：mmw/toolbox；加：检查；文件：check.py；Playbook: Bug fix', False),
                    ('candidate', '待积累', '', False),
                    ('candidate', '另一角度', '继续观察', False)]
        for record, (conclusion, reason, plan, qualified) in zip(
                [r for group in rows.values() for r in group], expected):
            self.assertEqual({k:record[k] for k in ('conclusion','reason','evidence','plan','run','qualifies')},
                             dict(conclusion=conclusion, reason=reason, evidence='README.md:1',
                                  plan=plan, run='o/r#76', qualifies=qualified))
            self.assertTrue(record['request'])
        for number in rows:
            for comment in self.fake.rows[number]['comments'][1:]:
                if events.parse(comment['body'])[1]['event'] == 'lesson.assessed':
                    record = events.parse(comment['body'])[1]
                    self.assertIn(record['conclusion'], comment['body'].splitlines()[0])
                    self.assertIn(record['reason'], comment['body'].splitlines()[0])
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual([receipt[k] for k in ('merged','rejected','candidates','proposals')], [1,1,2,1])
        self.assertEqual(receipt['problems'], [
            dict(repo='o/r',number=90,conclusion='reject'),
            dict(repo='o/r',number=91,conclusion='merge:94'),
            dict(repo='o/r',number=92,conclusion='propose'),
            dict(repo='o/r',number=93,conclusion='candidate'),
            dict(repo='o/r',number=93,conclusion='candidate')])

    def test_apply_records_loose_rows_verbatim(self):
        self.start_run()
        path = Path(self.answer())
        rows = [
            ('missing-information (signal, first round)', 'propose', '改：保留原始答复'),
            ('#91 (related lesson)', 'candidate', '继续观察'),
            ('other/product#92', 'propose', '仓库：another/product；文件：AGENTS.md；改：记录'),
            ('https://github.com/other/product/issues/93 (registration)', 'reject', ''),
            ('#94', 'merge:unknown target (signal, note)', '目标留给归并时判断'),
            ('#90', 'reject', '另一位分析员的不同判断'),
        ]
        for number in (91, 92, 93, 94):
            self.fake.rows[number] = issue(number)
        evidence = 'README.md:1；https://github.com/o/r/issues/90'
        path.write_text('| 代号 | 结论 | 理由 | 证据 | 方案 |\n' + ''.join(
            f'| {code} | {conclusion} | 核对过原始材料 | {evidence} | {plan} |\n'
            for code, conclusion, plan in rows) + '\n## Problems\nNone\n')
        rc, out, err = self.run_process('apply', str(path))
        self.assertEqual(rc, 0, err)
        for number, expected in ((90, [rows[0], rows[5]]), (91, [rows[1]]),
                                 (92, [rows[2]]), (93, [rows[3]]), (94, [rows[4]])):
            records = [events.parse(c['body'])[1] for c in self.fake.rows[number]['comments']
                       if events.parse(c['body'])[1]['event'] == 'lesson.assessed']
            self.assertEqual([(r['conclusion'], r['reason'], r['evidence'], r['plan']) for r in records],
                             [(r[1], '核对过原始材料', evidence, r[2]) for r in expected])
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['problems'], [
            dict(repo='o/r', number=90, conclusion='propose'),
            dict(repo='o/r', number=91, conclusion='candidate'),
            dict(repo='other/product', number=92, conclusion='propose'),
            dict(repo='other/product', number=93, conclusion='reject'),
            dict(repo='o/r', number=94, conclusion='merge:unknown target (signal, note)'),
            dict(repo='o/r', number=90, conclusion='reject')])
        self.assertFalse(any(c[1:3] in (['issue','edit'], ['issue','close'],
                                       ['issue','reopen'], ['issue','transfer']) for c in self.fake.calls))
        writes = [(c[c.index('--repo')+1], int(c[3])) for c in self.fake.calls
                  if c[1:3] == ['issue', 'comment']]
        self.assertEqual(writes, [('o/r', 90), ('o/r', 91), ('other/product', 92),
                                  ('other/product', 93), ('o/r', 94), ('o/r', 90), ('o/r', 76)])
        self.fake.calls.clear()
        rc, out, err = self.run_process('apply', str(path))
        self.assertEqual(rc, 0, err)
        self.assertFalse(any(c[1:3] == ['issue','comment'] for c in self.fake.calls))

    def test_apply_lists_a_row_naming_no_registration(self):
        self.start_run()
        self.fake.rows[91] = issue(91, labels=('mmw:ticket',))
        path = Path(self.answer())
        signal = 'https://github.com/o/r/issues/76#issuecomment-1 (signal, stalled)'
        path.write_text(path.read_text().replace('## Problems',
            f'| {signal} | propose | 信号不是登记 | README.md:1 | 改：记录停顿 |\n'
            '| #91 | reject | 这是产品票 | README.md:1 | |\n\n## Problems'))
        rc, out, err = self.run_process('apply', str(path))
        self.assertEqual(rc, 0, err)
        records = [events.parse(c['body'])[1] for c in self.fake.rows[90]['comments']]
        self.assertEqual([r['event'] for r in records], ['lesson.seen', 'lesson.assessed'])
        self.assertEqual(self.fake.rows[91]['comments'], [])
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['candidates'], 1)
        self.assertEqual(len(receipt['problems']), 3)
        for entry, code in zip(receipt['problems'][1:], (signal, '#91')):
            self.assertEqual(entry['code'], code)
            self.assertEqual(entry['conclusion'], 'unrecorded')
            self.assertTrue(entry['reason'])

    def test_apply_retries_a_failed_registration_lookup(self):
        self.start_run()
        self.fake.rows[91] = issue(91)
        path = Path(self.answer())
        path.write_text(path.read_text().replace('## Problems',
            '| #91 | candidate | 另一条登记 | README.md:1 | |\n\n## Problems'))
        tracker = self.fake
        def unavailable(args, **kwargs):
            if args[:4] == ['gh', 'issue', 'view', '90']:
                return subprocess.CompletedProcess(args, 1, '', 'GitHub unavailable')
            return tracker(args, **kwargs)
        self.fake = unavailable
        rc, out, err = self.run_command('apply', str(path))
        self.assertEqual(rc, 2, err)
        self.assertIn('GitHub unavailable', err)
        self.assertFalse(any(c[1:3] == ['issue', 'comment'] for c in tracker.calls))
        self.fake = tracker
        rc, out, err = self.run_process('apply', str(path))
        self.assertEqual(rc, 0, err)
        for number in (90, 91):
            self.assertEqual(len([c for c in self.fake.rows[number]['comments']
                                  if events.parse(c['body'])[1]['event'] == 'lesson.assessed']), 1)

    def test_apply_requires_an_explicit_problems_section(self):
        self.start_run()
        path = Path(self.answer())
        table = path.read_text().split('## Problems')[0]
        for section in ('', '## Problems\n'):
            with self.subTest(section=section):
                path.write_text(table + section)
                rc, out, err = self.run_command('apply', str(path))
                self.assertEqual(rc, 2, err)
                self.assertIn('## Problems', err)
                self.assertFalse(any(c[1:3] == ['issue', 'comment'] for c in self.fake.calls))

    def test_apply_refuses_an_answer_without_an_analysis_table(self):
        self.start_run()
        path = Path(self.answer())
        for content in ('No problems found.', '- No problems found.',
                        '｜ 代号 ｜ 结论 ｜ 理由 ｜ 证据 ｜ 方案 ｜', ''):
            with self.subTest(content=content):
                path.write_text(content + '\n\n## Problems\nNone\n')
                rc, out, err = self.run_command('apply', str(path))
                self.assertEqual(rc, 2, err)
                self.assertIn('answer.md', err)
                self.assertIn('table', err)
                self.assertFalse(any(c[1:3] == ['issue', 'comment'] for c in self.fake.calls))

    def test_apply_refuses_an_empty_table_with_only_malformed_problems(self):
        self.start_run()
        path = Path(self.answer())
        path.write_text('| 代号 | 结论 | 理由 | 证据 | 方案 |\n'
                        '| --- | --- | --- | --- | --- |\n\n'
                        '## Problems\n### bad\n问题代号：bad\n角度：流程\n')
        rc, out, err = self.run_command('apply', str(path))
        self.assertEqual(rc, 2, err)
        self.assertIn('answer.md', err)
        self.assertIn('## Problems bad', err)
        self.assertFalse(any(c[1:3] == ['issue', 'comment'] for c in self.fake.calls))

    def test_apply_reads_loose_problem_entries(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/o/r.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        path = Path(self.answer())
        path.write_text(path.read_text().replace('## Problems\nNone',
            '## Problems\n### unreadable\n- 问题代号：broken-entry\n'
            '- 角度：流程\n- 该谁修：o/r\n'
            '### loose-fault\n- 问题代号：loose-fault\n- 角度：流程\n'
            '- 发生了什么：工具拒绝了正常请求\n- 证据：`README.md:1`；https://github.com/o/r/issues/90\n'
            '- 代价：工作停下\n- 该谁修：o/r (由工具仓库处理)\n'
            '### bad-owner\n问题代号：bad-owner\n角度：流程\n发生了什么：没有目标仓库\n'
            '证据：README.md:1\n代价：工作停下\n该谁修：不知道\n'
            '### another-fault\n问题代号：another-fault\n角度：流程\n'
            '发生了什么：工具丢失了请求\n证据：README.md:1\n'
            '代价：工作停下\n该谁修：MMW 仓库（工具负责人）\n'))
        rc, out, err = self.run_process('apply', str(path))
        self.assertEqual(rc, 0, err)
        self.assertIn('broken-entry', err)
        self.assertIn('bad-owner', err)
        created = [r for n, r in self.fake.rows.items() if n > 100]
        self.assertEqual([retro.register.problem_fields(r['body'])['问题代号'] for r in created],
                         ['loose-fault', 'another-fault'])
        for row in created:
            self.assertEqual(events.parse(row['comments'][0]['body'])[1]['source'], 'retro-signal')
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['registered'], 2)
        self.assertEqual(receipt['candidates'], 1)

    def test_apply_marks_unreadable_new_problem_evidence(self):
        self.start_run()
        path = Path(self.answer())
        path.write_text(path.read_text().replace('## Problems\nNone',
            '## Problems\n### missing-source\n问题代号：missing-source\n角度：流程\n'
            '发生了什么：证据文件无法读取\n证据：README.md:1；absent.md:1\n'
            '代价：不能核实结论\n该谁修：o/r\n'))
        rc, out, err = self.run_process('apply', str(path))
        self.assertEqual(rc, 1, err)
        self.assertIn('absent.md:1', err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['candidates'], 1)
        self.assertEqual(receipt['registered'], 0)
        self.assertEqual(receipt['evidence'], 'partial')
        self.assertEqual(receipt['unreadable_sources'], ['absent.md:1'])
        self.assertFalse(any(c[1:3] == ['issue', 'create'] for c in self.fake.calls))

    def test_apply_rerun_records_nothing_twice(self):
        path = self.assessment_answer()
        original = self.fake
        def lose_assessment_response(args, **kwargs):
            result = original(args, **kwargs)
            if args[:4] == ['gh','issue','comment','91']:
                return subprocess.CompletedProcess(args,1,'','assessment response lost')
            return result
        self.fake = lose_assessment_response
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        self.fake = original
        for _ in range(2):
            rc,out,err = self.run_process('apply',path)
            self.assertEqual(rc,0,err)
        records = [events.parse(c['body'])[1] for row in self.fake.rows.values()
                   for c in row['comments'] if events.parse(c['body'])[0] == 'event']
        assessments = [r for r in records if r['event'] == 'lesson.assessed']
        self.assertEqual(len(assessments),5)
        self.assertEqual(len({r['request'] for r in assessments}),5)
        self.assertEqual(len([r for r in records if r['event'] == 'spec.retroed']),1)

    def test_apply_refuses_a_row_without_evidence(self):
        self.start_run()
        path = self.answer('reject',evidence='')
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,2)
        self.assertIn('answer.md:3',err)
        self.assertIn('evidence',err)
        self.assertEqual(self.fake.rows[90]['state'],'open')

    def test_gather_exposes_unregistered_stalls_and_related_closed_lessons(self):
        self.start_run()
        self.fake.rows[61] = issue(61,labels=('mmw:ticket',),parent=dict(number=76),bodies=[events.build('ticket.returned',ticket=61,spec=76,line='Missing tool',at='2026-09-14T00:00:00Z')])
        self.fake.rows[92] = issue(92,bodies=[seen(ticket=40,spec=70)],state='closed')
        self.fake.rows[90]['comments'] = [dict(id=1,body=seen(ticket=62))]
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        material = '\n'.join(p.read_text() for p in (self.root/'materials').glob('*.md'))
        self.assertIn('unregistered-signal',material)
        self.assertIn('ticket.returned',material)
        self.assertIn('https://github.com/o/r/issues/92',material)
        self.assertIn('closed',material)

    def test_apply_records_a_zero_row_receipt_for_an_empty_answer(self):
        self.start_run()
        path = Path(self.answer())
        path.write_text('| 代号 | 结论 | 理由 | 证据 | 方案 |\n'
                        '| --- | --- | --- | --- | --- |\n\n## Problems\nNone\n')
        rc, out, err = self.run_command('apply', str(path))
        self.assertEqual(rc, 0, err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['event'], 'spec.retroed')
        self.assertEqual(receipt['result'], 'recorded')
        self.assertEqual(receipt['problems'], [])
        self.assertEqual([receipt[k] for k in ('merged', 'rejected', 'candidates', 'proposals', 'registered')],
                         [0, 0, 0, 0, 0])

    def test_apply_records_a_receipt_when_every_row_is_unrecorded(self):
        self.start_run()
        self.fake.rows[90]['labels'] = [dict(name='mmw:ticket')]
        rc, out, err = self.run_command('apply', self.answer())
        self.assertEqual(rc, 0, err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['event'], 'spec.retroed')
        self.assertEqual(receipt['result'], 'recorded')
        self.assertEqual(receipt['problems'], [dict(
            code='missing-information', conclusion='unrecorded',
            reason='answer target is not a lesson; product problems and children stay in their workflows')])
        self.assertEqual([receipt[k] for k in ('merged', 'rejected', 'candidates', 'proposals', 'registered')],
                         [0, 0, 0, 0, 0])

    def test_apply_records_a_typed_retrospective_receipt(self):
        self.start_run()
        rc,out,err = self.run_command('apply',self.answer('candidate'))
        self.assertEqual(rc,0,err)
        records = [events.parse(c['body'])[1] for c in self.fake.rows[76]['comments']]
        receipt = records[-1]
        self.assertEqual(receipt['event'],'spec.retroed')
        self.assertEqual(receipt['candidates'],1)
        self.assertEqual(receipt['registered'],0)
        self.assertNotIn('retro_memory',receipt)

    def test_apply_receipt_lists_each_problem(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/o/r.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        for number in (91, 92, 93, 94):
            self.fake.rows[number] = issue(number, bodies=[seen(source='owner-correction')])
        path = self.answer('candidate')
        Path(path).write_text(Path(path).read_text().replace('## Problems\nNone',
            '| 91 | reject | 已不成立 | README.md:1 | |\n'
            '| 92 | merge:94 | 重复 | README.md:1 | |\n'
            '| 93 | propose | 主人纠正 | README.md:1 | 仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake |\n'
            '\n## Problems\n### new-fault\n问题代号：new-fault\n角度：流程\n'
            '发生了什么：工具拒绝了正常请求\n证据：README.md:1\n代价：工作停下\n该谁修：o/r'))
        expected = [dict(repo='o/r', number=90, conclusion='candidate'),
                    dict(repo='o/r', number=91, conclusion='reject'),
                    dict(repo='o/r', number=92, conclusion='merge:94'),
                    dict(repo='o/r', number=93, conclusion='propose'),
                    dict(repo='o/r', number=107, conclusion='registered')]
        original = self.fake
        def fail_receipt(args, **kwargs):
            if args[:4] == ['gh','issue','comment','76']:
                return subprocess.CompletedProcess(args,1,'','receipt denied')
            return original(args, **kwargs)
        self.fake = fail_receipt
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        self.fake = original
        for _ in range(2):
            rc,out,err = self.run_command('apply',path)
            self.assertEqual(rc,0,err)
            receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
            self.assertEqual(receipt.get('problems'),expected)
        self.assertEqual(len([c for c in self.fake.rows[76]['comments']
                              if events.parse(c['body'])[1].get('event')=='spec.retroed']),1)

    def test_apply_receipt_marks_an_appended_occurrence(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/o/r.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        self.fake.rows[91] = issue(91,bodies=[seen()])
        self.fake.rows[91]['body'] = self.fake.rows[91]['body'].replace('missing-information','old-fault')
        path = self.answer('candidate')
        Path(path).write_text(Path(path).read_text().replace('## Problems\nNone',
            '## Problems\n### old-fault\n问题代号：old-fault\n角度：流程\n'
            '发生了什么：工具拒绝了正常请求\n证据：README.md:1\n代价：工作停下\n该谁修：o/r\n'
            '### new-fault\n问题代号：new-fault\n角度：流程\n'
            '发生了什么：工具丢失了请求\n证据：README.md:1\n代价：工作停下\n该谁修：o/r\n'
            '### new-fault-again\n问题代号：new-fault\n角度：流程\n'
            '发生了什么：工具丢失了请求\n证据：README.md:1\n代价：工作停下\n该谁修：o/r'))
        original = self.fake
        def fail_receipt(args, **kwargs):
            if args[:4] == ['gh','issue','comment','76']:
                return subprocess.CompletedProcess(args,1,'','receipt denied')
            return original(args, **kwargs)
        self.fake = fail_receipt
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        self.fake = original
        for _ in range(2):
            rc,out,err = self.run_command('apply',path)
            self.assertEqual(rc,0,err)
            receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
            self.assertEqual(receipt['problems'],[
                dict(repo='o/r',number=90,conclusion='candidate'),
                dict(repo='o/r',number=91,conclusion='appended'),
                dict(repo='o/r',number=104,conclusion='registered'),
                dict(repo='o/r',number=104,conclusion='appended')])
            self.assertEqual(receipt['registered'],1)
        self.assertEqual(len(events.fold(self.fake.rows[91]['comments'])['occurrences']),2)
        self.assertEqual(len([c for c in self.fake.rows[76]['comments']
                              if events.parse(c['body'])[1].get('event')=='spec.retroed']),1)

    def test_apply_refuses_unreadable_evidence_and_keeps_other_rows(self):
        self.start_run()
        self.fake.rows[91] = issue(91)
        path = self.answer('reject',evidence='absent.md:1')
        Path(path).write_text(Path(path).read_text().replace('## Problems','| 91 | candidate | 已核实 | README.md:1 | |\n\n## Problems'))
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        self.assertEqual(self.fake.rows[90]['state'],'open')
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['candidates'],1)
        self.assertEqual(receipt['evidence'],'partial')
        self.assertIn('answer.md:3',err)

    def test_gather_reports_approved_closed_lessons_without_a_commit(self):
        self.start_run()
        self.fake.rows[91] = issue(91,labels=('mmw:ticket',),state='closed',bodies=[seen(ticket=40,spec=70)])
        self.fake.rows[91]['state_reason'] = 'completed'
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        material = '\n'.join(p.read_text() for p in (self.root/'materials').glob('*.md'))
        self.assertIn('approved-without-commit',material)
        self.assertIn('https://github.com/o/r/issues/91',material)

    def test_a_cross_repository_proposal_stays_on_its_registration(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/mmw/toolbox.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        self.fake.rows[90] = issue(bodies=[seen(source='stall')])
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：mmw/toolbox；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertNotIn(99,self.fake.rows)
        self.assertEqual(self.fake.rows[90]['state'],'open')
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['problems'], [dict(repo='o/r', number=90, conclusion='propose')])

    def test_new_problems_are_registered_from_the_answer(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/o/r.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        path = self.answer('candidate')
        text = Path(path).read_text().replace('## Problems\nNone', '## Problems\n### new-fault\n问题代号：new-fault\n角度：流程\n发生了什么：工具拒绝了正常请求\n证据：README.md:1\n代价：工作停下\n该谁修：o/r')
        Path(path).write_text(text)
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,0,err)
        created = [r for n,r in self.fake.rows.items() if n>100]
        self.assertEqual(len(created),1)
        self.assertIn('new-fault',created[0]['body'])
        occurrence = events.parse(created[0]['comments'][0]['body'])[1]
        self.assertEqual(occurrence['source'],'retro-signal')
        self.assertEqual(occurrence['spec'],76)

    def run_process(self, *args):
        data = self.root/'tracker.json'
        data.write_text(json.dumps(list(self.fake.rows.values())))
        binary = self.root/'bin'
        binary.mkdir(exist_ok=True)
        gh = binary/'gh'
        gh.write_text('#!'+os.sys.executable+'\n'+f'''import sys,json
from pathlib import Path
sys.path.insert(0,{str(Path(__file__).parent)!r})
from test_retro import Fake
path=Path({str(data)!r})
fake=Fake(json.loads(path.read_text()), repo={self.fake.repo!r})
result=fake(['gh',*sys.argv[1:]])
with Path({str(self.root/'calls.jsonl')!r}).open('a') as log:
    for call in fake.calls:
        log.write(json.dumps(call)+'\\n')
path.write_text(json.dumps(list(fake.rows.values())))
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
''')
        gh.chmod(0o755)
        env = dict(os.environ,PATH=str(binary)+os.pathsep+os.environ['PATH'])
        (self.root/'calls.jsonl').write_text('')
        result = REAL_RUN([os.sys.executable,str(SCRIPT),*args],env=env,capture_output=True,text=True)
        self.fake.calls.extend(json.loads(line) for line in (self.root/'calls.jsonl').read_text().splitlines())
        self.fake.rows = {r['number']:r for r in json.loads(data.read_text())}
        return result.returncode, result.stdout, result.stderr

    def test_recurrence_after_refusal_records_the_analyst_conclusion(self):
        self.start_run()
        self.fake.rows[90] = issue(bodies=[seen(source='owner-correction')],labels=('mmw:lesson','wontfix'),state='closed')
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        context = json.loads((self.root/'materials/context.json').read_text())
        self.assertEqual(context['recurred_after_wontfix'],[90])
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertEqual(self.fake.rows[90]['state'],'closed')
        self.assertNotIn({'name':'needs-triage'},self.fake.rows[90]['labels'])
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['candidates'],0)
        self.assertEqual(receipt['proposals'],1)

    def test_a_ticket_retrospective_is_recorded_on_that_ticket(self):
        self.start_run()
        self.fake.rows[61] = issue(61,labels=('mmw:ticket',),bodies=[events.build('ticket.claimed',ticket=61,line='Claimed',at='2026-09-01T00:00:00Z')])
        path = self.answer('candidate')
        context = json.loads((self.root/'context.json').read_text())
        context.update(spec=None,ticket=61)
        (self.root/'context.json').write_text(json.dumps(context))
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,0,err)
        receipt = events.parse(self.fake.rows[61]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['event'],'ticket.retroed')
        self.assertEqual(receipt['ticket'],61)
        self.assertEqual(receipt['problems'], [dict(repo=REPO, number=90, conclusion='candidate')])

    def test_a_bad_url_rejects_only_its_row_with_a_location(self):
        self.start_run()
        self.fake.rows[91] = issue(91)
        path = self.answer('reject',evidence='http://127.0.0.1:1/unavailable')
        Path(path).write_text(Path(path).read_text().replace('## Problems','| 91 | candidate | 已核实 | README.md:1 | |\n\n## Problems'))
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        self.assertIn('answer.md:3',err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['candidates'],1)
        self.assertEqual(self.fake.rows[90]['state'],'open')

    def test_proposal_preserves_the_registration_body(self):
        self.start_run()
        self.fake.rows[90] = issue(bodies=[seen(source='stall')])
        original = self.fake.rows[90]['body'].replace('\n','\r\n')
        self.fake.rows[90]['body'] = original
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertEqual(self.fake.rows[90]['body'], original)

    def test_non_lesson_targets_are_unrecorded(self):
        self.start_run()
        self.fake.rows[90]['labels'] = [dict(name='mmw:ticket')]
        rc,out,err = self.run_command('apply',self.answer('candidate'))
        self.assertEqual(rc,0,err)
        self.assertIn('not a lesson',err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['problems'], [dict(
            code='missing-information', conclusion='unrecorded',
            reason='answer target is not a lesson; product problems and children stay in their workflows')])

    def test_retry_after_receipt_failure_keeps_proposals_and_does_not_repeat_rejections(self):
        self.start_run()
        self.fake.rows[90] = issue(bodies=[seen(source='stall')])
        self.fake.rows[91] = issue(91)
        path = self.answer('propose',plan='仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake')
        Path(path).write_text(Path(path).read_text().replace('## Problems','| 91 | reject | 已不成立 | README.md:1 | |\n\n## Problems'))
        original = self.fake
        def fail_receipt(args,**kwargs):
            if args[:4]==['gh','issue','comment','76']:
                return subprocess.CompletedProcess(args,1,'','receipt denied')
            return original(args,**kwargs)
        self.fake = fail_receipt
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        self.fake = original
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,0,err)
        receipt = events.parse(original.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['proposals'],1)
        self.assertEqual(receipt['candidates'],0)
        self.assertEqual(len([c for c in original.rows[91]['comments'] if '已不成立' in c['body']]),1)
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,0,err)
        self.assertEqual(len([c for c in original.rows[76]['comments'] if events.parse(c['body'])[1].get('event')=='spec.retroed']),1)

    def test_a_refused_row_is_not_itself_an_unreadable_primary_source(self):
        self.start_run()
        self.fake.rows[91] = issue(91)
        path = self.answer('reject',evidence='')
        Path(path).write_text(Path(path).read_text().replace('## Problems','| 91 | candidate | 已核实 | README.md:1 | |\n\n## Problems'))
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,1,err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['evidence'],'complete')
        self.assertEqual(receipt['unreadable_sources'],[])

    def test_apply_uses_the_context_written_by_gather(self):
        self.start_run()
        material = self.root/'materials'
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(material))
        self.assertEqual(rc,0,err)
        path = self.answer('candidate')
        rc,out,err = self.run_command('apply',path,'--context',str(material/'context.json'))
        self.assertEqual(rc,0,err)
        receipt = events.parse(self.fake.rows[76]['comments'][-1]['body'])[1]
        self.assertEqual(receipt['registered'],1)
        self.assertEqual(receipt['candidates'],1)
        self.assertEqual(receipt['proposals'],0)
