from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest

V5 = Path(__file__).resolve().parents[2]

GH = r'''#!/usr/bin/env python3
import fcntl,json,os,sys
from pathlib import Path
p=Path(os.environ['TRACKER_STATE']); lock=open(str(p)+'.lock','a');fcntl.flock(lock,fcntl.LOCK_EX)
s=json.loads(p.read_text());a=sys.argv[1:]
def save():p.write_text(json.dumps(s))
def out(v):print(json.dumps(v))
def children(n):return [r for r in s['issues'].values() if (r.get('parent') or {}).get('number')==int(n)]
def node(r):
 kids=children(r['number']);return {**r,'labels':{'nodes':r.get('labels',[])},'subIssuesSummary':{'total':len(kids),'completed':sum(k['state']=='CLOSED' for k in kids)},'subIssues':{'nodes':[node(k) for k in kids]}}
if a[:2]==['repo','view']:
 if '--json' in a and a[a.index('--json')+1]=='url':print('https://github.test/owner/repo')
 else:
  assert a[2]==os.environ['EXPECTED_ORIGIN'];assert 'GH_REPO' not in os.environ;print('owner/repo')
 sys.exit()
assert os.environ.get('GH_REPO')=='owner/repo'
if a[:2]==['issue','view']:
 r=s['issues'][a[2]]
 for b in r.get('blockedBy',{}).get('nodes',[]):b.update(state=s['issues'][str(b['number'])]['state'],stateReason=s['issues'][str(b['number'])].get('stateReason'))
 if '-q' in a or '--jq' in a:
  q=a[a.index('-q')+1] if '-q' in a else a[a.index('--jq')+1]
  if q.startswith('.parent.number'):print((r.get('parent') or {}).get('number') or '')
  else:print(r.get(q.removeprefix('.'),'') or '')
 else:out({k:r.get(k) for k in a[a.index('--json')+1].split(',')})
elif a[:2]==['issue','comment']:
 if s.get('fail_event') and ('"event":"'+s['fail_event']+'"') in (a[a.index('--body')+1] if '--body' in a else Path(a[a.index('--body-file')+1]).read_text()):
  s.pop('fail_event');save();sys.exit(1)
 body=a[a.index('--body')+1] if '--body' in a else Path(a[a.index('--body-file')+1]).read_text()
 s['issues'][a[2]]['comments'].append({'id':s['next_comment'],'body':body});s['next_comment']+=1;save()
elif a[:2]==['issue','edit']:
 r=s['issues'][a[2]];labels={l['name'] for l in r['labels']}
 if '--add-label' in a:labels.add(a[a.index('--add-label')+1])
 if '--remove-label' in a:labels.discard(a[a.index('--remove-label')+1])
 if '--remove-assignee' in a:r['assignees']=[]
 r['labels']=[{'name':l} for l in sorted(labels)];save()
elif a[:2]==['issue','reopen']:s['issues'][a[2]]['state']='OPEN';save()
elif a[:2]==['issue','close']:
 s['issues'][a[2]].update(state='CLOSED',stateReason='COMPLETED',closedAt='2099-01-01T00:00:00Z');save()
elif a[:2]==['pr','list']:print('5')
elif a[:2]==['pr','checks']:
 if s.get('red_pr'):out([{'name':'unit','bucket':'fail'}]);sys.exit(1)
 out([])
elif a[:2]==['api','graphql']:
 if any('reviewThreads' in x for x in a):
  more=s.get('paged_review') and 'cursor=next' not in a
  nodes=[{'isResolved':False,'path':'code','line':2}] if s.get('paged_review') and not more else []
  out({'data':{'repository':{'pullRequest':{'reviewThreads':{'nodes':nodes,'pageInfo':{'hasNextPage':bool(more),'endCursor':'next' if more else None}}}}}})
 else:
  n=next(x.split('=',1)[1] for x in a if x.startswith('root='));out({'data':{'repository':{'issue':node(s['issues'][n])}}})
elif a[0]=='api' and 'user' in a:print('worker')
elif a[0]=='api' and any('/comments' in x for x in a):
 n=next(x.split('/issues/')[1].split('/')[0] for x in a if '/issues/' in x);out([s['issues'][n]['comments']])
elif a[0]=='api' and any('/sub_issues' in x for x in a):
 n=next(x.split('/issues/')[1].split('/')[0] for x in a if '/issues/' in x);print('\n'.join(str(r['number']) for r in children(n)))
elif a[0]=='api' and any('labels=mmw' in x for x in a):print('60')
else:raise AssertionError(a)
'''

RUNNER = r'''#!/usr/bin/env python3
import fcntl,json,os,sys
from pathlib import Path
p=Path(os.environ['RUNNER_STATE']);lock=open(str(p)+'.lock','a');fcntl.flock(lock,fcntl.LOCK_EX)
s=json.loads(p.read_text());a=sys.argv[1:];s['calls'].append(a)
if a[0]=='describe':print(json.dumps({'catalog':'paseo','launch':'provider'}))
elif a[0]=='self':print(os.environ.get('TEST_SESSION','parent'))
elif a[0]=='start':
 assert Path(os.environ['ARMED']).is_file(), 'watchdog must be armed before startup'
 assert json.loads(Path(os.environ['WATCH_STATE']).read_text()), 'a watch must exist before startup'
 if s.get('fail_start'):p.write_text(json.dumps(s));sys.exit(2)
 n='child-'+str(len(s['sessions'])+1);s['sessions'][n]='alive';print(n)
elif a[0]=='liveness':print(s['sessions'].get(a[1],'stopped'))
elif a[0]=='stop':
 if s.get('fail_stop'):p.write_text(json.dumps(s));sys.exit(2)
 s['sessions'][a[1]]='stopped'
elif a[0]=='send':
 p.write_text(json.dumps(s));sys.exit(s.get('send_exit',0))
p.write_text(json.dumps(s))
'''

RELAY = r'''import json,os,sys
from pathlib import Path
p=Path(os.environ['WATCH_STATE']);s=json.loads(p.read_text());a=sys.argv[1:];op=a[0]
def val(k):return a[a.index(k)+1] if k in a else None
key='spec:'+val('--spec') if val('--spec') else 'tickets:'+str(val('--tickets'))
if op=='start':
 s[key]={'runner':val('--runner'),'session':val('--session')};print('opened '+key)
elif op=='stop':s.pop(key,None)
elif op=='watching':
 if key not in s and ('tickets:'+str(val('--ticket'))) not in s:sys.exit(1)
p.write_text(json.dumps(s))
'''


class TicketDispatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.tools = self.root / 'tools';shutil.copytree(V5 / 'tools', self.tools)
        self.dispatch = self.tools / 'dispatch/scripts/dispatch.sh'
        for name in ('paseo', 'herdr', 'orca', 'codex-app'):
            path=self.dispatch.parent / 'runners' / (name+'.sh')
            path.write_text('#!/usr/bin/env bash\n# MMW_RUNNER: {"catalog":"paseo","launch":"paseo"}\nexec python3 '+str(self.root/'runner.py')+' "$@"\n')
        (self.root/'runner.py').write_text(RUNNER)
        (self.dispatch.parent/'relay.py').write_text(RELAY)
        (self.dispatch.parent/'watchdog.py').write_text("import os\nfrom pathlib import Path\nPath(os.environ['ARMED']).write_text('armed')\n")
        self.bin=self.root/'bin';self.bin.mkdir();(self.bin/'gh').write_text(GH);(self.bin/'gh').chmod(0o755)
        self.repo=self.root/'repo';self.repo.mkdir();self.origin=self.root/'origin.git'
        subprocess.run(['git','init','--bare','-q',str(self.origin)],check=True)
        self.git('init','-q','-b','project');self.git('config','user.name','Test');self.git('config','user.email','test@example.invalid')
        self.git('config','core.hooksPath','/dev/null');self.git('config','commit.gpgsign','false')
        (self.repo/'.gitignore').write_text('.worktrees/\n.scratch/\n');(self.repo/'code').write_text('base\n')
        scripts=self.repo/'scripts';scripts.mkdir();check=scripts/'check';check.write_text('#!/usr/bin/env bash\necho PASS unit\n');check.chmod(0o755)
        self.git('add','.');self.git('commit','-qm','baseline');self.base=self.git('rev-parse','HEAD')
        self.git('remote','add','origin',str(self.origin));self.git('push','-q','origin','project');self.git('checkout','-qb','batch');self.git('push','-q','origin','batch')
        self.home=self.root/'home';self.home.mkdir();catalog=self.root/'catalog.json'
        catalog.write_text(json.dumps({'paseo':{'codex':[{'id':'test','name':'Test','thinkingOptionIds':['high']}]}}))
        self.store=self.root/'tracker.json';self.runner_store=self.root/'runner.json';self.watches=self.root/'watches.json'
        self.runner_store.write_text(json.dumps({'calls':[],'sessions':{}}));self.watches.write_text('{}')
        self.env={k:v for k,v in os.environ.items() if k not in ('MMW_SPEC','MMW_TICKET','PASEO_AGENT_ID','HERDR_PANE_ID','ORCA_TERMINAL_HANDLE','CODEX_THREAD_ID')}
        self.env.update(PATH=str(self.bin)+os.pathsep+os.environ['PATH'],MMW_HOME=str(self.home),MMW_RUNNER='paseo',MMW_HOST_CATALOG=str(catalog),GH_REPO='wrong/repo',TRACKER_STATE=str(self.store),RUNNER_STATE=str(self.runner_store),WATCH_STATE=str(self.watches),EXPECTED_ORIGIN=str(self.origin),ARMED=str(self.root/'armed'))
        init=subprocess.run([sys.executable,str(self.dispatch.parent/'models.py'),'init'],env=self.env,capture_output=True,text=True);self.assertEqual(init.returncode,0,init.stderr)
        config=json.loads((self.home/'models.json').read_text());config['runner']='paseo';config['max_workers']=1
        for role in config['rows']:config['rows'][role]={'host':'codex','model':'test','effort':'high'}
        (self.home/'models.json').write_text(json.dumps(config))
        self.task=self.root/'worker task.md';self.task.write_text('Perform this caller task.\n')
        self.review_task=self.root/'review task.md';self.review_task.write_text('Review this caller task.\n')
        self.state={'issues':{},'next_comment':1}
        self.issue(60,parent=None,labels=['mmw:spec']);self.issue(61);self.issue(62,blocked=[61]);self.save()
        spec=importlib.util.spec_from_file_location('pipeline_events',self.tools/'verify-ticket/scripts/events.py');self.events=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.events)

    def git(self,*args,cwd=None):
        return subprocess.check_output(['git',*map(str,args)],cwd=cwd or self.repo,text=True,stderr=subprocess.PIPE).strip()

    def issue(self,n,parent=60,labels=None,blocked=()):
        self.state['issues'][str(n)]={'number':n,'title':'Ticket '+str(n),'state':'OPEN','stateReason':None,'parent':{'number':parent} if parent else None,'labels':[{'name':x} for x in (labels if labels is not None else ['ready-for-agent'])],'blockedBy':{'nodes':[{'number':b,'state':self.state['issues'][str(b)]['state']} for b in blocked]},'comments':[],'assignees':[],'body':'## Acceptance criteria\n- [ ] Caller result\n','createdAt':'2026-01-01T00:00:00Z','closedAt':''}

    def save(self):self.store.write_text(json.dumps(self.state))
    def reload(self):self.state=json.loads(self.store.read_text());return self.state
    def command(self,*args,cwd=None,env=None):
        return subprocess.run(['bash',str(self.dispatch),*map(str,args)],cwd=cwd or self.repo,env=env or self.env,text=True,capture_output=True,timeout=30)
    def ok(self,r):self.assertEqual(r.returncode,0,r.stdout+r.stderr);return r
    def open(self):return self.ok(self.command('open',60,'--into','batch','--project','project','--worker-task',self.task,'--reviewer-task',self.review_task))
    def starts(self):return [x for x in json.loads(self.runner_store.read_text())['calls'] if x[0]=='start']

    def test_explicit_spec_tasks_reach_worker_in_origin_backed_workspace(self):
        self.open();self.ok(self.command('start',61,'worker','--task',self.task))
        start=self.starts()[0];cwd=Path(start[start.index('--cwd')+1]);self.assertEqual(cwd,self.repo/'.worktrees/issue-61')
        self.assertEqual(self.git('rev-parse','origin/issue-61'),self.base)
        attach=[a for a in json.loads(self.runner_store.read_text())['calls'] if a[0]=='attach'][-1]
        self.assertIn('--under-caller',attach)
        self.assertIn(str(self.task),shlex.split(start[start.index('--prompt')+1]));self.assertTrue((self.root/'armed').exists())
        fold=self.events.fold(self.reload()['issues']['61']['comments']);self.assertEqual(fold['worker']['base'],self.base)

    def test_missing_task_cannot_start_a_worker(self):
        self.open();r=self.command('start',61,'worker');self.assertEqual(r.returncode,2);self.assertEqual(self.starts(),[])

    def add_event(self,n,event,**fields):
        self.reload();self.state['issues'][str(n)]['comments'].append({'id':self.state['next_comment'],'body':self.events.build(event,ticket=n,spec=60,line=event,**fields)})
        self.state['next_comment']+=1;self.save()

    def started(self,n=61):
        self.open();return self.ok(self.command('start',n,'worker','--task',self.task)).stdout.strip()

    def output(self,n=61,filename='result',text='output\n',check=None):
        tree=self.repo/'.worktrees'/('issue-'+str(n))
        (tree/filename).write_text(text)
        if check is not None:(tree/'scripts/check').write_text('#!/usr/bin/env bash\n'+check+'\n')
        self.git('add','.',cwd=tree);self.git('commit','-qm','ticket output',cwd=tree)
        head=self.git('rev-parse','HEAD',cwd=tree);self.git('push','-q','origin','issue-'+str(n),cwd=tree)
        self.add_event(n,'ticket.passed',commit=head,into='batch',branch='issue-'+str(n),runner='paseo',session='child-1')
        self.reload();self.state['issues'][str(n)].update(state='CLOSED',stateReason='COMPLETED',labels=[],closedAt='2099-01-01T00:00:00Z');self.save()
        return head

    def test_reviewer_records_actual_comparison_and_caller_task(self):
        self.started();tree=self.repo/'.worktrees/issue-61';(tree/'reviewed').write_text('change')
        self.git('add','.',cwd=tree);self.git('commit','-qm','review target',cwd=tree);head=self.git('rev-parse','HEAD',cwd=tree)
        self.ok(self.command('send','reviewer',61,'--task',self.review_task,cwd=tree,env=dict(self.env,TEST_SESSION='child-1')))
        fold=self.events.fold(self.reload()['issues']['61']['comments']);reviewer=[r for r in fold['sessions'] if r['kind']=='reviewer'][-1]
        self.assertEqual(reviewer['base'],self.base)
        payload=self.events.newest(self.state['issues']['61']['comments'],'reviewer.started')['payload']
        self.assertEqual(payload['head'],head);self.assertEqual(payload['task'],str(self.review_task))
        prompt=self.starts()[-1][self.starts()[-1].index('--prompt')+1]
        self.assertIn('--head '+head,prompt);self.assertIn('python3',prompt)
        attach=[a for a in json.loads(self.runner_store.read_text())['calls'] if a[0]=='attach'][-1]
        self.assertNotIn('--under-caller',attach)

    def test_startup_failure_preserves_workspace_without_a_false_hold(self):
        self.open();self.runner_store.write_text(json.dumps({'calls':[],'sessions':{},'fail_start':True}))
        self.assertEqual(self.command('start',61,'worker','--task',self.task).returncode,2)
        self.assertTrue((self.repo/'.worktrees/issue-61').is_dir())
        self.assertEqual(self.git('rev-parse','origin/issue-61'),self.base)
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['held'])

    def test_failed_start_event_stops_only_created_session_and_keeps_workspace(self):
        self.open();self.reload();self.state['fail_event']='worker.started';self.save()
        self.assertEqual(self.command('start',61,'worker','--task',self.task).returncode,2)
        self.assertEqual(json.loads(self.runner_store.read_text())['sessions']['child-1'],'stopped')
        self.assertTrue((self.repo/'.worktrees/issue-61').is_dir())
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['held'])

    def test_replacement_stop_failure_starts_nothing_beside_the_worker(self):
        self.started();s=json.loads(self.runner_store.read_text());s['fail_stop']=True;self.runner_store.write_text(json.dumps(s))
        self.assertEqual(self.command('start',61,'worker','--task',self.task).returncode,2);self.assertEqual(len(self.starts()),1)
        self.assertTrue(self.events.fold(self.reload()['issues']['61']['comments'])['held'])

    def test_resume_preserves_adapter_receipts_and_ended_hold_refuses_send(self):
        self.started()
        for code in (3,4,2,0):
            state=json.loads(self.runner_store.read_text());state['send_exit']=code;self.runner_store.write_text(json.dumps(state))
            self.assertEqual(self.command('resume',61,'continue').returncode,code)
        self.add_event(61,'worker.lost',runner='paseo',session='child-1')
        before=len(json.loads(self.runner_store.read_text())['calls']);ended=self.command('resume',61,'again');self.assertEqual(ended.returncode,2);self.assertIn('--task FILE',ended.stderr)
        self.assertEqual(len(json.loads(self.runner_store.read_text())['calls']),before)

    def test_advance_obeys_capacity_and_does_not_repeat_workers(self):
        self.open();self.ok(self.command('advance',60));self.ok(self.command('advance',60));self.assertEqual(len(self.starts()),1)
        self.assertIn('#61 worker',self.starts()[0])
        self.assertFalse((self.repo/'.worktrees/issue-62').exists())

    def test_advance_lands_dependency_before_starting_dependent_worker(self):
        self.started();head=self.output();self.ok(self.command('advance',60))
        self.assertEqual(len(self.starts()),2)
        tree=self.repo/'.worktrees/issue-62';self.assertTrue((tree/'result').exists())
        self.assertEqual(self.git('rev-parse','HEAD',cwd=self.repo),self.base)
        self.git('merge-base','--is-ancestor',head,'origin/batch')
        self.ok(self.command('advance',60));self.assertEqual(len(self.starts()),2)

    def test_landing_merges_exact_reported_commit_and_keeps_later_branch_work(self):
        self.started();passed=self.output();tree=self.repo/'.worktrees/issue-61'
        (tree/'later').write_text('unreported');self.git('add','.',cwd=tree);self.git('commit','-qm','after pass',cwd=tree);extra=self.git('rev-parse','HEAD',cwd=tree)
        self.git('push','-q','origin','issue-61',cwd=tree)
        self.ok(self.command('land',61));self.git('fetch','-q','origin')
        self.git('merge-base','--is-ancestor',passed,'origin/batch')
        self.assertNotEqual(subprocess.run(['git','merge-base','--is-ancestor',extra,'origin/batch'],cwd=self.repo).returncode,0)
        self.assertEqual(self.git('rev-parse','issue-61'),extra);self.assertEqual(self.git('rev-parse','origin/issue-61'),extra)
        count=len(self.reload()['issues']['61']['comments']);self.assertNotEqual(self.command('land',61).returncode,0);self.assertEqual(len(self.reload()['issues']['61']['comments']),count)

    def test_failed_repository_check_bounces_without_pushing_or_removing_ticket_work(self):
        self.started();passed=self.output(check='echo FAIL unit; exit 1')
        before=self.git('rev-parse','origin/batch');self.ok(self.command('land',61));self.git('fetch','-q','origin')
        self.assertEqual(self.git('rev-parse','origin/batch'),before)
        fold=self.events.fold(self.reload()['issues']['61']['comments']);self.assertTrue(fold['bounced']);self.assertFalse(fold['landed'])
        self.assertTrue((self.repo/'.worktrees/issue-61').is_dir());self.assertEqual(self.git('rev-parse','issue-61'),passed)
        event=self.events.newest(self.state['issues']['61']['comments'],'ticket.bounced');self.assertIn('FAIL unit',event['body'])

    def test_cannot_run_checks_keeps_pass_and_origin_unchanged(self):
        self.started();self.output(check='echo ENV unavailable; exit 2');before=self.git('rev-parse','origin/batch')
        self.assertNotEqual(self.command('land',61).returncode,0);self.assertEqual(self.git('rev-parse','origin/batch'),before)
        fold=self.events.fold(self.reload()['issues']['61']['comments']);self.assertTrue(fold['passed']);self.assertFalse(fold['landed']);self.assertFalse(fold['bounced'])
        self.assertTrue((self.repo/'.worktrees/issue-61').is_dir())

    def test_dirty_work_after_pass_is_kept_when_landing_cleanup_refuses(self):
        self.started();self.output();tree=self.repo/'.worktrees/issue-61';(tree/'untracked-work').write_text('keep me')
        self.assertNotEqual(self.command('land',61).returncode,0)
        self.assertEqual((tree/'untracked-work').read_text(),'keep me')
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['landed'])

    def test_retract_saves_stopped_worker_edits_before_removing_workspace(self):
        self.started();tree=self.repo/'.worktrees/issue-61';(tree/'code').write_text('unfinished')
        runner=json.loads(self.runner_store.read_text());runner['sessions']['child-1']='stopped';self.runner_store.write_text(json.dumps(runner))
        self.ok(self.command('retract',61));self.assertFalse(tree.exists());self.assertEqual(self.git('show','origin/issue-61:code'),'unfinished')
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['held'])

    def test_suspend_preserves_edits_and_failed_stops_keep_the_hold(self):
        self.started();tree=self.repo/'.worktrees/issue-61';(tree/'code').write_text('interrupted')
        self.ok(self.command('suspend',60));self.assertTrue(tree.exists());self.assertEqual(self.git('show','origin/issue-61:code'),'interrupted')
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['held']);self.assertEqual(json.loads(self.watches.read_text()),{})

    def test_integrate_conflict_keeps_merge_and_ticket_worktree(self):
        self.started();tree=self.repo/'.worktrees/issue-61'
        (tree/'code').write_text('ticket');self.git('add','.',cwd=tree);self.git('commit','-qm','ticket edit',cwd=tree)
        (self.repo/'code').write_text('base edit');self.git('add','.');self.git('commit','-qm','base edit');self.git('push','-q','origin','batch')
        run=self.command('integrate',61,cwd=tree);self.assertEqual(run.returncode,3,run.stdout+run.stderr)
        self.git('rev-parse','--verify','MERGE_HEAD',cwd=tree);self.assertIn('<<<<<<<',(tree/'code').read_text())

    def test_wait_does_not_return_an_older_workers_result_after_a_new_start(self):
        self.started();self.output();self.reload();self.state['issues']['61'].update(state='OPEN',stateReason=None,labels=[{'name':'ready-for-agent'}]);self.save()
        self.ok(self.command('start',61,'worker','--task',self.task))
        r=self.command('wait',61,'worker');self.assertEqual(r.returncode,3,r.stdout+r.stderr);self.assertNotIn('ticket.passed',r.stdout);self.assertIn('wait-wake',r.stderr);self.assertNotIn('end your turn',r.stderr)

    def test_landed_ticket_cleanup_and_repeated_land_are_idempotent(self):
        self.started();self.output();self.ok(self.command('land',61));count=len(self.reload()['issues']['61']['comments'])
        self.ok(self.command('land',61));self.assertEqual(len(self.reload()['issues']['61']['comments']),count)
        self.assertFalse((self.repo/'.worktrees/issue-61').exists())
        self.assertNotEqual(subprocess.run(['git','show-ref','--verify','--quiet','refs/heads/issue-61'],cwd=self.repo).returncode,0)

    def test_standalone_open_records_explicit_target_and_send_requires_task(self):
        self.state['issues']['61']['parent']=None;self.save()
        self.ok(self.command('open-ticket',61,'--into','batch','--task',self.task))
        self.ok(self.command('start',61,'worker','--task',self.task))
        payload=self.events.newest(self.reload()['issues']['61']['comments'],'worker.started')['payload']
        self.assertEqual(payload['into'],'batch');self.assertIsNone(payload['spec'])

    def test_summary_checks_actual_tip_and_reuses_exact_proof_without_duplicate_close(self):
        self.started();self.output();self.ok(self.command('land',61))
        self.reload();self.state['issues']['62'].update(labels=[{'name':'needs-triage'}],blockedBy={'nodes':[]});self.save()
        self.ok(self.command('summary',60));self.reload();count=len(self.state['issues']['60']['comments'])
        self.ok(self.command('summary',60));self.assertEqual(len(self.reload()['issues']['60']['comments']),count)
        fold=self.events.fold(self.state['issues']['60']['comments']);self.assertTrue(fold['spec_closed'])
        record=self.events.newest(self.state['issues']['60']['comments'],'spec.checked')['payload']
        self.assertEqual(record['commit'],self.git('rev-parse','origin/batch'));self.assertEqual(record['tier'],'all')
        self.assertEqual(json.loads(self.watches.read_text()),{})

    def test_summary_red_check_keeps_watch_and_does_not_claim_closed(self):
        self.open();self.reload()
        for n in ('61','62'):self.state['issues'][n].update(labels=[{'name':'needs-triage'}],blockedBy={'nodes':[]})
        self.save();(self.repo/'scripts/check').write_text('#!/usr/bin/env bash\necho FAIL unit\nexit 1\n')
        self.git('add','.');self.git('commit','-qm','red check');self.git('push','-q','origin','batch')
        self.assertEqual(self.command('summary',60).returncode,2)
        self.assertFalse(self.events.fold(self.reload()['issues']['60']['comments'])['spec_closed'])
        self.assertIn('spec:60',json.loads(self.watches.read_text()))

    def test_finish_merges_checked_batch_and_preserves_callers_base_checkout(self):
        self.started();self.output();self.ok(self.command('land',61))
        self.reload();self.state['issues']['62'].update(state='CLOSED',stateReason='NOT_PLANNED',labels=[]);self.save()
        self.ok(self.command('summary',60));head=self.git('rev-parse','origin/batch')
        self.ok(self.command('finish',60));self.git('fetch','-q','origin');self.git('merge-base','--is-ancestor',head,'origin/project')
        self.assertTrue(self.repo.is_dir());self.assertEqual(self.git('branch','--show-current'),'batch')
        self.assertEqual(self.reload()['issues']['60']['state'],'CLOSED')
        self.assertNotEqual(subprocess.run(['git','show-ref','--verify','--quiet','refs/remotes/origin/batch'],cwd=self.repo).returncode,0)
        count=len(self.state['issues']['60']['comments']);self.ok(self.command('finish',60));self.assertEqual(len(self.reload()['issues']['60']['comments']),count)

    def test_push_rejection_keeps_pass_workspace_and_remote_base(self):
        self.started();self.output();before=self.git('rev-parse','origin/batch')
        hook=self.origin/'hooks/pre-receive';hook.write_text('#!/usr/bin/env bash\nexit 1\n');hook.chmod(0o755)
        r=self.command('land',61);self.assertNotEqual(r.returncode,0)
        self.assertEqual(self.git('rev-parse','origin/batch'),before);self.assertTrue((self.repo/'.worktrees/issue-61').exists())
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['landed'])
        self.assertIn('nothing was force-pushed',r.stderr)

    def test_landing_event_failure_retries_without_another_merge(self):
        self.started();self.output();self.reload();self.state['fail_event']='ticket.landed';self.save()
        self.assertNotEqual(self.command('land',61).returncode,0);tip=self.git('rev-parse','origin/batch')
        self.ok(self.command('land',61));self.assertEqual(self.git('rev-parse','origin/batch'),tip)
        fold=self.events.fold(self.reload()['issues']['61']['comments']);self.assertTrue(fold['landed'])
        events=[e for e in fold['events'] if e['event']=='ticket.landed'];self.assertEqual(len(events),1)

    def test_suspension_failed_stop_keeps_ticket_hold_and_edits(self):
        self.started();tree=self.repo/'.worktrees/issue-61';(tree/'code').write_text('keep unfinished')
        state=json.loads(self.runner_store.read_text());state['fail_stop']=True;self.runner_store.write_text(json.dumps(state))
        self.assertEqual(self.command('suspend',60).returncode,1)
        self.assertEqual((tree/'code').read_text(),'keep unfinished');self.assertTrue(self.events.fold(self.reload()['issues']['61']['comments'])['held'])

    def test_worker_grade_chooses_its_model_and_multiple_grades_refuse(self):
        catalog=Path(self.env['MMW_HOST_CATALOG']);catalog.write_text(json.dumps({'paseo':{'codex':[{'id':x,'name':x,'thinkingOptionIds':['high']} for x in ('test','senior-test')]}}))
        config=json.loads((self.home/'models.json').read_text());config['rows']['senior-worker']['model']='senior-test';(self.home/'models.json').write_text(json.dumps(config))
        self.state['issues']['61']['labels'].append({'name':'senior-worker'});self.save()
        self.started();request=self.starts()[0];self.assertEqual(request[request.index('--model')+1],'senior-test')
        self.reload();self.state['issues']['61']['labels'].append({'name':'junior-worker'});self.save()
        self.assertEqual(self.command('start',61,'worker','--task',self.task).returncode,2);self.assertEqual(len(self.starts()),1)

    def test_concurrent_advances_start_one_worker_for_the_ticket(self):
        self.open();commands=[subprocess.Popen(['bash',str(self.dispatch),'advance','60'],cwd=self.repo,env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        for child in commands:
            out,err=child.communicate(timeout=30);self.assertEqual(child.returncode,0,out+err)
        self.assertEqual(len(self.starts()),1)

    def test_checks_that_mutate_checkout_do_not_authorize_a_push(self):
        self.started();self.output(check='echo changed >> code; echo PASS unit');before=self.git('rev-parse','origin/batch')
        r=self.command('land',61);self.assertNotEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(self.git('rev-parse','origin/batch'),before);self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['landed'])

    def test_start_refuses_prior_worker_target_that_conflicts_with_open_spec(self):
        self.started();self.git('branch','other',self.base);self.git('push','-q','origin','other')
        self.add_event(61,'worker.started',session='child-1',runner='paseo',machine='test',host='codex',model='test',effort='high',grade='junior-worker',worktree=str(self.repo/'.worktrees/issue-61'),branch='issue-61',base=self.base,into='other')
        r=self.command('start',61,'worker','--task',self.task)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertEqual(len(self.starts()),1)

    def test_advance_refuses_pass_for_a_different_target_branch(self):
        self.started();self.git('branch','other',self.base);self.git('push','-q','origin','other');passed=self.output()
        self.add_event(61,'ticket.passed',commit=passed,into='other')
        r=self.command('advance',60);self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.git('fetch','-q','origin');self.assertEqual(self.git('rev-parse','origin/other'),self.base)
        self.assertFalse(self.events.fold(self.reload()['issues']['61']['comments'])['landed'])

    def test_finish_reads_review_threads_after_the_first_page(self):
        self.started();self.output();self.ok(self.command('land',61));self.reload();self.state['issues']['62'].update(state='CLOSED',stateReason='NOT_PLANNED',labels=[]);self.save()
        self.ok(self.command('summary',60));self.reload();self.state['paged_review']=True;self.save()
        before=self.git('rev-parse','origin/project');r=self.command('finish',60)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertIn('code:2',r.stderr);self.assertEqual(self.git('rev-parse','origin/project'),before)
        self.assertFalse(self.events.fold(self.reload()['issues']['60']['comments'])['spec_merged'])

    def test_retract_refuses_an_older_live_holder_when_latest_worker_has_ended(self):
        self.started()
        self.add_event(61,'worker.started',session='child-2',runner='paseo',machine='test',host='codex',model='test',effort='high',grade='junior-worker',worktree=str(self.repo/'.worktrees/issue-61'),branch='issue-61',base=self.base,into='batch')
        self.add_event(61,'worker.retracted',runner='paseo',session='child-2')
        runner=json.loads(self.runner_store.read_text());runner['sessions']['child-2']='stopped';self.runner_store.write_text(json.dumps(runner))
        r=self.command('retract',61);self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertEqual(json.loads(self.runner_store.read_text())['sessions']['child-1'],'alive');self.assertTrue((self.repo/'.worktrees/issue-61').exists())

    def test_landing_refuses_a_branch_name_instead_of_reported_commit(self):
        self.started();self.output();self.add_event(61,'ticket.passed',commit='origin/issue-61',into='batch')
        before=self.git('rev-parse','origin/batch');r=self.command('land',61)
        self.assertNotEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(self.git('rev-parse','origin/batch'),before)



if __name__=='__main__':unittest.main()
