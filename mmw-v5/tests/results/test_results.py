from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
VERIFY = TOOLS / "verify-ticket/scripts/verify-ticket.py"
spec = importlib.util.spec_from_file_location("result_test_events", VERIFY.with_name("events.py"))
events = importlib.util.module_from_spec(spec)
spec.loader.exec_module(events)

FAKE_GH = r'''#!/usr/bin/env python3
import fcntl,json,os,sys
from pathlib import Path
p=Path(os.environ['FAKE_TRACKER'])
lock=open(str(p)+'.lock','a');fcntl.flock(lock,fcntl.LOCK_EX)
s=json.loads(p.read_text());a=sys.argv[1:]
def save():p.write_text(json.dumps(s))
if a[:2]==['repo','view']:
 assert a[2]==os.environ.get('FAKE_ORIGIN_URL','https://github.test/owner/repo.git')
 assert 'GH_REPO' not in os.environ
 print('owner/repo');sys.exit()
if a[0]=='issue':assert os.environ.get('GH_REPO')=='owner/repo'
assert 'CLICOLOR_FORCE' not in os.environ
if a[:2]==['issue','view']:
 row=s['issues'][a[2]];fields=a[a.index('--json')+1].split(',')
 print(json.dumps({k:row.get(k) for k in fields}))
elif a[:3]==['api','--paginate','--slurp']:
 number=a[-1].split('/issues/')[1].split('/')[0]
 rows=s['issues'][number]['comments']
 print(json.dumps([rows[:1],rows[1:]]))
elif a[:2]==['api','-i']:
 assert a[2].startswith('repos/owner/repo/issues/')
 number=a[2].split('/issues/')[1].split('/')[0]
 print('HTTP/2 200 OK\nETag: "test"\n')
 print(json.dumps(s['issues'][number]['comments']))
elif a[:2]==['issue','comment']:
 row=s['issues'][a[2]]
 if s.get('fail_comment',0):
  s['fail_comment']-=1;save();print('comment refused',file=sys.stderr);sys.exit(1)
 text=Path(a[a.index('--body-file')+1]).read_text()
 row['comments'].append({'id':s['next_comment'],'body':text});s['next_comment']+=1
 s['mutations'].append('comment')
 if s.get('lost_receipt',0):
  s['lost_receipt']-=1;save();print('transport closed after write',file=sys.stderr);sys.exit(1)
 save();print('https://github.test/owner/repo/issues/'+a[2]+'#comment')
elif a[:2]==['issue','close']:
 if s.get('fail_close',0):
  s['fail_close']-=1;save();print('close refused',file=sys.stderr);sys.exit(1)
 row=s['issues'][a[2]];row['state']='CLOSED'
 if '--duplicate-of' in a:
  row['duplicateOf']=int(a[a.index('--duplicate-of')+1]);row['stateReason']='NOT_PLANNED'
 else:row['stateReason']='COMPLETED' if a[a.index('--reason')+1]=='completed' else 'NOT_PLANNED'
 s['mutations'].append('close');save()
elif a[:2]==['issue','edit']:
 if s.get('fail_edit',0):
  s['fail_edit']-=1;save();print('edit refused',file=sys.stderr);sys.exit(1)
 row=s['issues'][a[2]];names={x['name'] for x in row['labels']}
 for i,arg in enumerate(a):
  if arg=='--add-label':names.add(a[i+1])
  if arg=='--remove-label':names.discard(a[i+1])
 row['labels']=[{'name':n} for n in sorted(names)]
 if '--parent' in a:row['parent']={'number':int(a[a.index('--parent')+1])}
 if '--remove-parent' in a:row['parent']=None
 if '--remove-assignee' in a:row['assignees']=[]
 s['mutations'].append('edit');save()
elif a[:2]==['issue','create']:
 number=str(s['next_issue']);s['next_issue']+=1
 labels=[a[i+1] for i,arg in enumerate(a) if arg=='--label']
 s['issues'][number]={'number':int(number),'state':'OPEN','stateReason':None,
  'parent':{'number':int(a[a.index('--parent')+1])},'labels':[{'name':n} for n in labels],
  'comments':[],'assignees':[],'body':Path(a[a.index('--body-file')+1]).read_text()}
 s['mutations'].append('create');save();print('https://github.test/owner/repo/issues/'+number)
else:raise AssertionError(a)
'''


class TicketResults(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "issue-61")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.git("config", "core.hooksPath", "/dev/null")
        self.remote = self.root / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        self.git("remote", "add", "origin", "https://github.test/owner/repo.git")
        self.git("config", f"url.{self.remote.as_uri()}.insteadOf", "https://github.test/owner/repo.git")
        (self.repo / ".gitignore").write_text(".scratch/\n")
        (self.repo / "code.txt").write_text("baseline\n")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "baseline")
        self.base = self.git("rev-parse", "HEAD")
        (self.repo / "code.txt").write_text("output\n")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "output")
        self.head = self.git("rev-parse", "HEAD")
        self.home = self.root / "v5-home"
        binary = self.root / "bin"
        binary.mkdir()
        (binary / "gh").write_text(FAKE_GH)
        (binary / "gh").chmod(0o755)
        self.store = self.root / "tracker.json"
        self.env = dict(os.environ, PATH=str(binary)+os.pathsep+os.environ["PATH"],
                        MMW_HOME=str(self.home), GH_REPO="wrong/repository", CLICOLOR_FORCE="1",
                        PASEO_AGENT_ID="worker-1", FAKE_TRACKER=str(self.store), FAKE_ORIGIN_URL=self.remote.as_uri())
        self.env.pop("MMW_TICKET", None)
        self.original_body = "## Parent\n#60\n## What to build\nDeliver output\n## Acceptance criteria\n- [ ] The caller gets the result\n## Blocked by\nNone\n"
        self.state = {"issues": {"61": {"number": 61, "state": "OPEN", "stateReason": None,
            "labels": [{"name": "ready-for-agent"}], "parent": {"number": 60},
            "body": self.original_body, "assignees": [{"login": "test-worker"}], "comments": []}},
            "next_comment": 1, "next_issue": 80, "mutations": []}
        self.add_event("worker.started", session="worker-1", runner="paseo", machine=socket.gethostname(),
                       host="codex", model="test-model", effort="high", grade="junior-worker",
                       worktree=str(self.repo), branch="issue-61", base=self.base, into="integration")
        self.report = self.root / "report.md"
        self.report.write_text("Delivered the requested behavior.\nTests: actual result described here.\nReview: findings addressed.\n")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True, stderr=subprocess.PIPE).strip()

    def save(self):
        self.store.write_text(json.dumps(self.state))

    def reload(self):
        self.state = json.loads(self.store.read_text())
        return self.state["issues"]["61"]

    def add_event(self, name, **fields):
        self.state["issues"]["61"]["comments"].append({"id": self.state["next_comment"],
            "body": events.build(name, ticket=61, spec=60, line=name, **fields)})
        self.state["next_comment"] += 1
        self.save()

    def run_tool(self, *args, env=None):
        return subprocess.run([sys.executable, str(VERIFY), "61", *map(str, args)], cwd=self.repo,
                              env=env or self.env, capture_output=True, text=True)

    def complete(self, *args):
        return self.run_tool("--closeout", self.report, "--result", "complete", "--commit", self.head, *args)

    def assert_ok(self, run):
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_plain_ticket_completes_without_old_acceptance_or_report_fields(self):
        self.assert_ok(self.complete())
        ticket = self.reload()
        folded = events.fold(ticket["comments"], issue=61)
        self.assertEqual(ticket["body"], self.original_body)
        self.assertEqual(ticket["state"], "CLOSED")
        self.assertEqual(ticket["labels"], [])
        self.assertTrue(folded["passed"])
        payload = folded["outcome"]["payload"]
        self.assertEqual((payload["commit"], payload["into"], payload["session"]), (self.head, "integration", "worker-1"))
        self.assertTrue({"counts", "abandoned", "outside_owns", "shape"}.isdisjoint(payload))
        self.assertIn(self.report.read_text().strip(), folded["outcome"]["body"])
        self.assertTrue(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61").startswith(self.head + "\t"))

    def test_rejected_push_keeps_the_ticket_open_and_unpushed_work_intact(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho 'remote rejects this push' >&2\nexit 1\n")
        hook.chmod(0o755)
        result = self.complete()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("origin rejected", result.stderr)
        ticket = self.reload()
        self.assertEqual((ticket["state"], self.state["mutations"]), ("OPEN", []))
        self.assertFalse(events.fold(ticket["comments"])["passed"])
        self.assertEqual(self.git("rev-parse", "HEAD"), self.head)
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61"), "")
        self.assertEqual((self.repo / "code.txt").read_text(), "output\n")

    def test_completion_never_force_pushes_over_a_divergent_remote_branch(self):
        remote_head = self.git("commit-tree", "HEAD^{tree}", "-p", self.base, "-m", "other output")
        self.git("push", "origin", f"{remote_head}:refs/heads/issue-61")
        result = self.complete()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61").split()[0], remote_head)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.head)
        ticket = self.reload()
        self.assertEqual((ticket["state"], self.state["mutations"]), ("OPEN", []))

    def test_check_only_does_not_push_the_output_branch(self):
        self.assert_ok(self.complete("--check-only"))
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61"), "")
        self.reload()
        self.assertEqual(self.state["mutations"], [])

    def test_unconfirmed_remote_commit_does_not_close_or_pass_the_ticket(self):
        actual_git = shutil.which("git")
        wrapper = self.root / "bin/git"
        wrapper.write_text(f"#!{sys.executable}\n" +
                           "import os,sys\n" +
                           "if sys.argv[1:3]==['ls-remote','--heads']:\n" +
                           " print('" + "0" * 40 + "\\trefs/heads/issue-61');sys.exit(0)\n" +
                           f"os.execv({actual_git!r},[{actual_git!r},*sys.argv[1:]])\n")
        wrapper.chmod(0o755)
        result = self.complete()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("could not be confirmed", result.stderr)
        ticket = self.reload()
        self.assertEqual((ticket["state"], self.state["mutations"]), ("OPEN", []))
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61").split()[0], self.head)

    def test_standalone_completion_cannot_publish_from_another_output_branch(self):
        self.state["issues"]["61"]["comments"] = []
        self.save()
        self.git("checkout", "-qb", "another-output")
        result = self.complete("--into", "integration")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.reload()
        self.assertEqual(self.state["mutations"], [])
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61"), "")

    def test_dispatched_startup_must_be_recorded_before_the_worker_reports(self):
        self.state["issues"]["61"]["comments"] = []
        self.save()
        env = dict(self.env, MMW_TICKET="61")
        result = self.run_tool("--closeout", self.report, "--result", "complete", "--commit", self.head,
                               "--into", "integration", env=env)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("retry", result.stderr)
        self.assertIn("worker.started", result.stderr)
        self.reload()
        self.assertEqual(self.state["mutations"], [])
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/issue-61"), "")
        self.add_event("worker.started", session="worker-1", runner="paseo", machine=socket.gethostname(),
                       host="codex", model="test-model", effort="high", grade="junior-worker",
                       worktree=str(self.repo), branch="issue-61", base=self.base, into="integration")
        self.assert_ok(self.run_tool("--closeout", self.report, "--result", "complete", "--commit", self.head, env=env))

    def test_dispatch_marker_for_another_ticket_cannot_report_this_ticket(self):
        result = self.run_tool("--closeout", self.report, "--result", "complete", "--commit", self.head,
                               env=dict(self.env, MMW_TICKET="99"))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.reload()
        self.assertEqual(self.state["mutations"], [])

    def test_reviewer_cannot_report_before_its_dispatched_startup_is_recorded(self):
        env = dict(self.env, MMW_TICKET="61", PASEO_AGENT_ID="reviewer-1")
        result = self.run_tool("--review", self.report, "--base", self.base, "--head", self.head, env=env)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("reviewer.started", result.stderr)
        self.reload()
        self.assertEqual(self.state["mutations"], [])

    def test_incomplete_output_stays_open_and_does_not_claim_a_pass(self):
        (self.repo / "code.txt").write_text("unfinished\n")
        self.assert_ok(self.run_tool("--closeout", self.report, "--result", "incomplete", "--commit", self.head))
        ticket = self.reload();folded = events.fold(ticket["comments"], issue=61)
        self.assertEqual(ticket["state"], "OPEN")
        self.assertIn({"name": "needs-triage"}, ticket["labels"])
        self.assertNotIn({"name": "ready-for-agent"}, ticket["labels"])
        self.assertTrue(folded["returned"])
        self.assertFalse(folded["passed"])

    def test_stale_commit_and_dirty_complete_report_are_refused_without_mutations(self):
        stale = self.run_tool("--closeout", self.report, "--result", "complete", "--commit", self.base)
        self.assertEqual(stale.returncode, 2)
        (self.repo / "code.txt").write_text("uncommitted\n")
        self.assertEqual(self.complete().returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_wrong_worker_or_target_cannot_publish_completion(self):
        wrong = self.run_tool("--closeout", self.report, "--result", "complete", "--commit", self.head,
                              env=dict(self.env, PASEO_AGENT_ID="other-worker"))
        self.assertEqual(wrong.returncode, 2)
        self.assertEqual(self.complete("--into", "other-branch").returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_ended_worker_cannot_publish_a_new_result(self):
        self.add_event("worker.retracted", runner="paseo", session="worker-1")
        self.assertEqual(self.complete().returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_previous_worker_remains_authoritative_after_the_newer_session_is_retracted(self):
        self.add_event("worker.started", session="worker-2", runner="paseo", machine=socket.gethostname(),
                       host="codex", model="test-model", effort="high", grade="junior-worker",
                       worktree=str(self.repo), branch="issue-61", base=self.base, into="integration")
        self.add_event("worker.retracted", runner="paseo", session="worker-2")
        self.assert_ok(self.complete())
        self.assertEqual(events.fold(self.reload()["comments"])["outcome"]["payload"]["session"], "worker-1")

    def test_incomplete_retry_after_hold_ends_is_idempotent_but_a_changed_report_is_refused(self):
        args = ("--closeout", self.report, "--result", "incomplete", "--commit", self.head)
        self.assert_ok(self.run_tool(*args))
        count = len(self.reload()["comments"])
        self.assert_ok(self.run_tool(*args))
        self.assertEqual(len(self.reload()["comments"]), count)
        self.report.write_text("A different result after this worker has ended\n")
        self.assertEqual(self.run_tool(*args).returncode, 2)
        self.assertEqual(len(self.reload()["comments"]), count)

    def test_standalone_ticket_requires_target_without_imposing_a_dispatch_record(self):
        self.state["issues"]["61"]["comments"] = [];self.save()
        self.assertEqual(self.complete().returncode, 2)
        self.assert_ok(self.complete("--into", "integration"))
        self.assertTrue(events.fold(self.reload()["comments"])["passed"])

    def test_empty_report_check_only_and_unreadable_events_make_no_tracker_writes(self):
        self.assert_ok(self.complete("--check-only"))
        self.report.write_text("")
        self.assertEqual(self.complete().returncode, 2)
        self.report.write_text("Actual report\n")
        self.state["issues"]["61"]["comments"].append({"id": 50, "body": '<!-- mmw {"v":9,"event":"ticket.passed"} -->'})
        self.save()
        self.assertEqual(self.complete().returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_closed_issue_with_failed_comment_is_recoverable_and_retry_is_idempotent(self):
        self.state["fail_comment"] = 1;self.save()
        self.assertEqual(self.complete().returncode, 1)
        ticket = self.reload()
        self.assertEqual(ticket["state"], "CLOSED")
        self.assertFalse(events.fold(ticket["comments"])["passed"])
        self.assert_ok(self.complete())
        ticket = self.reload();count = len(ticket["comments"]);mutations = list(self.state["mutations"])
        self.assert_ok(self.complete())
        self.assertEqual(len(self.reload()["comments"]), count)
        self.assertEqual(self.state["mutations"], mutations)

    def test_lost_comment_receipt_does_not_duplicate_the_result(self):
        self.state["lost_receipt"] = 1;self.save()
        self.assertEqual(self.complete().returncode, 1)
        count = len(self.reload()["comments"])
        self.assert_ok(self.complete())
        self.assertEqual(len(self.reload()["comments"]), count)

    def test_failed_close_or_queue_edit_never_posts_a_pass(self):
        for failure in ("fail_close", "fail_edit"):
            with self.subTest(failure=failure):
                self.state["issues"]["61"].update(state="OPEN", stateReason=None)
                self.state[failure] = 1;self.save()
                self.assertEqual(self.complete().returncode, 1)
                self.assertFalse(events.fold(self.reload()["comments"])["passed"])

    def test_owner_closed_not_planned_issue_is_not_overridden(self):
        self.state["issues"]["61"].update(state="CLOSED", stateReason="NOT_PLANNED");self.save()
        self.assertEqual(self.complete().returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_identical_completion_retry_cannot_ignore_a_later_owner_cancellation(self):
        self.assert_ok(self.complete())
        self.reload();self.state["issues"]["61"]["stateReason"] = "NOT_PLANNED";self.save()
        mutations = list(self.state["mutations"])
        self.assertEqual(self.complete().returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], mutations)

    def reviewer(self, head=None):
        self.add_event("reviewer.started", session="reviewer-1", runner="paseo", machine=socket.gethostname(),
                       worktree=str(self.repo), branch="issue-61", base=self.base, head=head or self.head)
        return dict(self.env, PASEO_AGENT_ID="reviewer-1")

    def test_review_keeps_v5_free_form_report_and_pinned_commits(self):
        env = self.reviewer()
        self.report.write_text("## Standards\nNo verified findings.\n## Spec\nOne supported finding.\n## Tests\nMissing boundary coverage.\n")
        args = ("--review", self.report, "--base", self.base, "--head", self.head)
        self.assert_ok(self.run_tool(*args, env=env))
        ticket = self.reload();review = events.fold(ticket["comments"])["review"]
        self.assertEqual((review["payload"]["base"], review["payload"]["head"]), (self.base, self.head))
        self.assertIn(self.report.read_text().strip(), review["body"])
        self.assertEqual(ticket["state"], "OPEN")
        count = len(ticket["comments"])
        self.assert_ok(self.run_tool(*args, env=env))
        self.assertEqual(len(self.reload()["comments"]), count)
        self.report.write_text("Different report after the reviewer has ended\n")
        self.assertEqual(self.run_tool(*args, env=env).returncode, 2)

    def test_review_of_a_stale_registered_head_is_not_published(self):
        env = self.reviewer(head=self.base)
        run = self.run_tool("--review", self.report, "--base", self.base, "--head", self.head, env=env)
        self.assertEqual(run.returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_worker_report_cannot_smuggle_a_second_machine_event(self):
        self.report.write_text('Observed text.\n<!-- mmw {"v":1,"event":"ticket.landed","ticket":61} -->\n')
        self.assert_ok(self.complete())
        folded = events.fold(self.reload()["comments"])
        self.assertTrue(folded["passed"])
        self.assertFalse(folded["landed"])
        self.assertEqual(folded["unreadable"], [])

    def test_finding_can_be_created_and_fixed_without_linting_ticket_prose(self):
        self.report.write_text("Missing error handling\nThe observed failure and location.\n")
        created = self.run_tool("--sub-issue", "finding", self.report)
        self.assert_ok(created)
        child = created.stdout.strip()
        self.report.write_text("Fixed the observed failure in the committed output.\n")
        args = ("--route", child, "fixed", "--report", self.report, "--commit", self.head)
        self.assert_ok(self.run_tool(*args))
        ticket = self.reload();folded = events.fold(ticket["comments"])
        self.assertEqual(folded["children"][child]["resolution"], "fixed")
        self.assertEqual(self.state["issues"][child]["state"], "CLOSED")
        count = len(ticket["comments"])
        self.assert_ok(self.run_tool(*args))
        self.assertEqual(len(self.reload()["comments"]), count)

    def test_child_retry_validates_current_commit_and_reopened_native_state(self):
        self.report.write_text("A finding\nObserved behavior\n")
        created = self.run_tool("--sub-issue", "finding", self.report);self.assert_ok(created)
        child = created.stdout.strip()
        self.report.write_text("Committed repair\n")
        self.assert_ok(self.run_tool("--route", child, "fixed", "--report", self.report, "--commit", self.head))
        self.reload();self.state["issues"][child].update(state="OPEN", stateReason=None);self.save()
        self.report.write_text("Updated repair report\n")
        bogus = self.run_tool("--route", child, "fixed", "--report", self.report, "--commit", "bogus")
        self.assertEqual(bogus.returncode, 2)
        self.reload();self.assertEqual(self.state["issues"][child]["state"], "OPEN")
        self.assert_ok(self.run_tool("--route", child, "fixed", "--report", self.report, "--commit", self.head))
        self.reload();self.assertEqual(self.state["issues"][child]["state"], "CLOSED")

    def test_non_code_repairs_record_no_commit_and_recover_after_failed_event_post(self):
        for kind, repair in (("fault", "Restarted the unavailable service; its health check now passes.\n"),
                             ("contract", "Corrected the tracker-owned requirement to match the accepted spec.\n")):
            with self.subTest(kind=kind):
                self.reload()
                self.state["fail_comment"] = 0
                self.save()
                self.report.write_text("Repair needed\nThe environment or tracker authority needs correction.\n")
                created = self.run_tool("--sub-issue", kind, self.report)
                self.assert_ok(created)
                child = created.stdout.strip()
                self.report.write_text(repair)
                (self.repo / "code.txt").write_text("Unrelated unfinished product work\n")
                self.reload()
                closed_before = self.state["mutations"].count("close")
                self.state["fail_comment"] = 1
                self.save()
                args = ("--route", child, "fixed", "--report", self.report)
                failed = self.run_tool(*args)
                self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
                ticket = self.reload()
                self.assertEqual((self.state["issues"][child]["state"], self.state["issues"][child]["stateReason"]),
                                 ("CLOSED", "COMPLETED"))
                self.assertIsNone(events.fold(ticket["comments"])["children"][child].get("resolution"))
                self.assert_ok(self.run_tool(*args))
                ticket = self.reload()
                recorded = events.newest(ticket["comments"], "child.closed")
                self.assertEqual((recorded["payload"]["child"], recorded["payload"]["resolution"]), (int(child), "fixed"))
                self.assertNotIn("commit", recorded["payload"])
                self.assertIn(repair.strip(), recorded["body"])
                self.assertEqual(self.state["mutations"].count("close"), closed_before + 1)
                mutations = list(self.state["mutations"])
                self.assert_ok(self.run_tool(*args))
                self.reload()
                self.assertEqual(self.state["mutations"], mutations)
                self.report.write_text("A different claimed repair\n")
                self.assertEqual(self.run_tool(*args).returncode, 2)
                self.reload()
                self.assertEqual(self.state["mutations"], mutations)

    def test_fixed_route_keeps_supplied_commit_validation_and_recorded_metadata(self):
        self.report.write_text("A finding\nObserved behavior\n")
        created = self.run_tool("--sub-issue", "finding", self.report)
        self.assert_ok(created)
        child = created.stdout.strip()
        self.report.write_text("Repaired the product in the supplied commit.\n")
        args = ("--route", child, "fixed", "--report", self.report)
        mutations = list(self.reload()["comments"])
        for commit in (self.base, "0" * 40, self.head[:12], "bogus"):
            with self.subTest(commit=commit):
                self.assertEqual(self.run_tool(*args, "--commit", commit).returncode, 2)
                self.assertEqual(self.reload()["comments"], mutations)
                self.assertEqual(self.state["issues"][child]["state"], "OPEN")
        (self.repo / "code.txt").write_text("Uncommitted repair\n")
        dirty = self.run_tool(*args, "--commit", self.head)
        self.assertEqual(dirty.returncode, 2, dirty.stdout + dirty.stderr)
        self.assertIn("uncommitted", dirty.stderr)
        self.git("checkout", "--", "code.txt")
        self.assert_ok(self.run_tool(*args, "--commit", self.head))
        ticket = self.reload()
        self.assertEqual(events.newest(ticket["comments"], "child.closed")["payload"]["commit"], self.head)
        mutations = list(self.state["mutations"])
        self.assertEqual(self.run_tool(*args).returncode, 2)
        self.reload()
        self.assertEqual(self.state["mutations"], mutations)
        self.assert_ok(self.run_tool(*args, "--commit", self.head))
        self.reload()
        self.assertEqual(self.state["mutations"], mutations)

    def test_created_child_with_failed_registration_can_be_recovered_without_recreation(self):
        self.report.write_text("A finding\nObserved behavior\n")
        self.state["fail_comment"] = 1;self.save()
        failed = self.run_tool("--sub-issue", "finding", self.report)
        self.assertEqual(failed.returncode, 1)
        self.assertIn("--existing 80", failed.stderr)
        self.reload();self.assertEqual(self.state["mutations"].count("create"), 1)
        args = ("--sub-issue", "finding", self.report, "--existing", "80")
        self.assert_ok(self.run_tool(*args))
        count = len(self.reload()["comments"])
        self.assertTrue(events.fold(self.state["issues"]["61"]["comments"])["children"]["80"]["opened"])
        self.assert_ok(self.run_tool(*args))
        self.assertEqual(len(self.reload()["comments"]), count)
        self.assertEqual(self.state["mutations"].count("create"), 1)

    def test_check_only_on_an_unsupported_action_cannot_write_a_child(self):
        run = self.run_tool("--sub-issue", "finding", self.report, "--check-only")
        self.assertEqual(run.returncode, 2)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_repository_check_cli_runs_the_actual_script_and_preserves_exit_meaning(self):
        scripts = self.repo / "scripts";scripts.mkdir()
        check = scripts / "check"
        check.write_text('#!/usr/bin/env bash\nprintf "PASS source-check\\n"\nexit "${CHECK_EXIT:-0}"\n')
        check.chmod(0o755)
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "add repository checks")
        for status, expected, code in (("0", "pass", 0), ("1", "red", 1), ("2", "cannot-run", 2)):
            with self.subTest(exit=status):
                run = self.run_tool("--repository-check", "--base", self.base, env=dict(self.env, CHECK_EXIT=status))
                self.assertEqual(run.returncode, code, run.stderr)
                self.assertEqual(json.loads(run.stdout)["status"], expected)
        self.reload();self.assertEqual(self.state["mutations"], [])

    def test_real_report_producers_reach_the_existing_relay_without_old_report_formats(self):
        vendor = self.root / "bin/paseo"
        log = self.root / "notifications.jsonl"
        vendor.write_text('''#!/usr/bin/env python3
import json,sys
from pathlib import Path
a=sys.argv[1:]
if a[:1]==['ls']:
 print(json.dumps([{'id':n,'status':'idle'} for n in ('worker-1','reviewer-1','orchestrator')]))
elif a[:2]==['send','--no-wait']:
 with Path(''' + repr(str(log)) + ''').open('a') as f:f.write(json.dumps(a[2:])+'\\n')
else:raise AssertionError(a)
''')
        vendor.chmod(0o755)
        relay = TOOLS / "dispatch/scripts/relay.py"
        def command(*args):
            run = subprocess.run([sys.executable, str(relay), *args, "--repo", "owner/repo"],
                                 cwd=self.repo, env=self.env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        command("add", "--tickets", "61", "--runner", "paseo", "--session", "orchestrator")
        env = self.reviewer()
        self.report.write_text("## Standards\nNo verified findings.\n## Spec\nNo verified findings.\n## Tests\nNo verified findings.\n")
        self.assert_ok(self.run_tool("--review", self.report, "--base", self.base, "--head", self.head, env=env))
        command("run", "--once")
        self.assert_ok(self.complete())
        command("run", "--once")
        sent = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual(sent, [["worker-1", "#61 reviewer.reported"], ["orchestrator", "#61 ticket.passed"]])
        command("stop", "--tickets", "61")


if __name__ == "__main__":
    unittest.main()
