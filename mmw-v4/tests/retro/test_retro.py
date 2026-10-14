"""Retrospective commands against paginated tracker fixtures and real temporary git."""
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
    def __init__(self, rows):
        self.rows = {r['number']: r for r in rows}
        self.calls = []

    def __call__(self, args, **kwargs):
        if args[0] != 'gh':
            return REAL_RUN(args, **kwargs)
        self.calls.append(args)
        a = args[1:]
        out = ''
        if a[:2] == ['repo', 'view']:
            out = json.dumps(dict(nameWithOwner=REPO))
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
                rows = list(self.rows.values())
                if 'labels=mmw%3Alesson' in endpoint or 'labels=mmw:lesson' in endpoint:
                    rows = [r for r in rows if {'name':'mmw:lesson'} in r['labels']]
            elif '/issues/comments/' in endpoint:
                n = int(endpoint.rsplit('/',1)[1])
                out = json.dumps(next(c for r in self.rows.values() for c in r['comments'] if c['id'] == n))
                rows = None
            else:
                raise AssertionError(args)
            if rows is not None:
                self.assert_pagination(a)
                out = json.dumps([rows[:1], rows[1:]])
        elif a[:2] == ['issue', 'view']:
            r = self.rows[int(a[2])]
            out = json.dumps({k: r.get(k) for k in a[a.index('--json')+1].split(',')})
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

    def test_a_lesson_unseen_for_thirty_days_expires(self):
        rc, out, err = self.run_command('expire', REPO)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.fake.rows[90]['state'], 'closed')
        self.assertEqual(self.fake.rows[90]['state_reason'], 'not planned')
        self.assertIn('30 天没再出现', self.fake.rows[90]['comments'][-1]['body'])
        self.assertIn('#90', out)

    def test_a_recently_seen_lesson_stays_open(self):
        self.fake.rows[91] = issue(91, bodies=[seen(at='2026-09-15T00:00:00Z')])
        rc, out, err = self.run_command('expire', REPO)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.fake.rows[91]['state'], 'open')
        self.assertEqual(self.fake.rows[90]['state'], 'closed')
        self.assertEqual(out.count('CLOSED:'), 1)

    def test_expire_leaves_what_awaits_the_owner_and_problems(self):
        self.fake.rows[91] = issue(91, bodies=[seen()], labels=('mmw:lesson','needs-triage'))
        self.fake.rows[92] = issue(92, bodies=[seen()], labels=('mmw:problem',))
        self.fake.rows[93] = issue(93, bodies=[seen()], labels=('mmw:child',))
        rc, out, err = self.run_command('expire', REPO)
        self.assertEqual(rc, 0, err)
        self.assertEqual([self.fake.rows[n]['state'] for n in (90,91,92,93)], ['closed','open','open','open'])

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
        self.fake.rows[61] = issue(61, labels=('mmw:ticket',),state='closed')
        self.fake.rows[91] = issue(91,labels=('mmw:child',),parent=dict(number=61))
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        files = '\n'.join(p.read_text() for p in (self.root/'materials').glob('*.md'))
        self.assertIn('orphaned-child',files)
        self.assertIn('https://github.com/o/r/issues/91',files)

    def test_gather_lists_a_reverted_commit(self):
        self.start_run()
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

    def answer(self, conclusion='candidate', evidence='README.md:1', plan='', code='missing-information'):
        path = self.root/'answer.md'
        path.write_text(f'| 代号 | 结论 | 理由 | 证据 | 方案 |\n| --- | --- | --- | --- | --- |\n| {code} | {conclusion} | 检查仍不可靠 | {evidence} | {plan} |\n\n## Problems\nNone\n')
        context = dict(repo=REPO,spec=76,ticket=None,since='2026-09-01T00:00:00Z',registered=0,landed_since_last=0,
                       recurred_after_wontfix=[],evidence='complete',unreadable_sources=[],issues={'missing-information':dict(repo=REPO,number=90)})
        (self.root/'context.json').write_text(json.dumps(context))
        return str(path)

    def test_apply_refuses_a_row_without_evidence(self):
        self.start_run()
        path = self.answer('reject',evidence='')
        rc,out,err = self.run_command('apply',path)
        self.assertEqual(rc,2)
        self.assertIn('answer.md:3',err)
        self.assertIn('evidence',err)
        self.assertEqual(self.fake.rows[90]['state'],'open')

    def test_a_single_occurrence_is_kept_as_a_candidate(self):
        self.start_run()
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertNotIn({'name':'needs-triage'},self.fake.rows[90]['labels'])
        self.assertIn('candidate',out)
        self.assertIn('independent',out)

    def test_a_twice_seen_lesson_is_proposed_with_its_playbook(self):
        self.start_run()
        self.fake.rows[90] = issue(bodies=[seen(),seen(ticket=62)])
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertIn({'name':'needs-triage'},self.fake.rows[90]['labels'])
        self.assertEqual(self.fake.rows[90]['body'].splitlines()[:2],['## Problem','Playbook: Stop a repeated mistake'])

    def test_an_owner_correction_is_proposed_at_once(self):
        self.start_run()
        self.fake.rows[90] = issue(bodies=[seen(source='owner-correction')])
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：o/r；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertIn({'name':'needs-triage'},self.fake.rows[90]['labels'])

    def test_a_merged_lesson_moves_its_occurrences(self):
        self.start_run()
        self.fake.rows[90] = issue(bodies=[seen(),seen(ticket=62)])
        self.fake.rows[91] = issue(91,bodies=[])
        rc,out,err = self.run_command('apply',self.answer('merge:91'))
        self.assertEqual(rc,0,err)
        self.assertEqual(self.fake.rows[90]['state'],'closed')
        self.assertEqual(self.fake.rows[90]['state_reason'],'duplicate')
        self.assertEqual(self.fake.rows[90]['duplicate_of'],'https://github.com/o/r/issues/91')
        moved = [events.parse(c['body'])[1] for c in self.fake.rows[91]['comments']]
        self.assertEqual([r['ticket'] for r in moved],[61,62])
        self.assertEqual([r['lesson'] for r in moved],[91,91])

    def test_a_rejected_lesson_is_closed_with_its_reason(self):
        self.start_run()
        rc,out,err = self.run_command('apply',self.answer('reject'))
        self.assertEqual(rc,0,err)
        self.assertEqual(self.fake.rows[90]['state'],'closed')
        self.assertEqual(self.fake.rows[90]['state_reason'],'not planned')
        self.assertIn('检查仍不可靠',self.fake.rows[90]['comments'][-1]['body'])

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

    def test_a_failed_write_reports_partial_not_untouched(self):
        self.start_run()
        original = self.fake
        def fail_close(args,**kwargs):
            if args[:3]==['gh','issue','close']:
                return subprocess.CompletedProcess(args,1,'','close denied')
            return original(args,**kwargs)
        self.fake = fail_close
        rc,out,err = self.run_command('apply',self.answer('reject'))
        self.assertEqual(rc,1)
        self.assertIn('close denied',err)
        self.assertIn('检查仍不可靠',original.rows[90]['comments'][-1]['body'])

    def test_gather_reports_approved_closed_lessons_without_a_commit(self):
        self.start_run()
        self.fake.rows[91] = issue(91,labels=('mmw:ticket',),state='closed',bodies=[seen(ticket=40,spec=70)])
        self.fake.rows[91]['state_reason'] = 'completed'
        rc,out,err = self.run_command('gather','--spec','76',REPO,'--out',str(self.root/'materials'))
        self.assertEqual(rc,0,err)
        material = '\n'.join(p.read_text() for p in (self.root/'materials').glob('*.md'))
        self.assertIn('approved-without-commit',material)
        self.assertIn('https://github.com/o/r/issues/91',material)

    def test_proposals_wrongly_registered_in_the_product_are_transferred(self):
        self.start_run()
        REAL_RUN(['git','remote','add','origin','https://github.com/mmw/toolbox.git'],check=True)
        marker = self.root/'home/installed-root'
        marker.parent.mkdir(parents=True)
        marker.write_text(str(self.root))
        self.fake.rows[90] = issue(bodies=[seen(source='stall')])
        rc,out,err = self.run_command('apply',self.answer('propose',plan='仓库：mmw/toolbox；加：检查；文件：check.py；Playbook: Stop a repeated mistake'))
        self.assertEqual(rc,0,err)
        self.assertEqual(self.fake.rows[99].get('transferred_to'),'mmw/toolbox')

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

    def test_expire_runs_as_a_process_against_a_fake_tracker(self):
        data = self.root/'tracker.json'
        data.write_text(json.dumps(list(self.fake.rows.values())))
        binary = self.root/'bin'
        binary.mkdir()
        gh = binary/'gh'
        gh.write_text('#!'+os.sys.executable+'\n'+f'''import sys,json
from pathlib import Path
sys.path.insert(0,{str(Path(__file__).parent)!r})
from test_retro import Fake
path=Path({str(data)!r})
fake=Fake(json.loads(path.read_text()))
result=fake(['gh',*sys.argv[1:]])
path.write_text(json.dumps(list(fake.rows.values())))
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
''')
        gh.chmod(0o755)
        env = dict(os.environ,PATH=str(binary)+os.pathsep+os.environ['PATH'])
        result = REAL_RUN([os.sys.executable,str(SCRIPT),'expire',REPO],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        rows = json.loads(data.read_text())
        self.assertEqual(rows[0]['state_reason'],'not planned')
        self.assertIn('#90',result.stdout)

    def test_recurrence_after_refusal_is_a_reminder_not_a_reproposal(self):
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
        self.assertIn('owner refusal',out)

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
