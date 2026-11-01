from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import socket
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
 assert a[2]=='https://github.test/owner/repo.git'
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
 row['stateReason']='COMPLETED' if a[a.index('--reason')+1]=='completed' else 'NOT_PLANNED'
 s['mutations'].append('close');save()
elif a[:2]==['issue','edit']:
 if s.get('fail_edit',0):
  s['fail_edit']-=1;save();print('edit refused',file=sys.stderr);sys.exit(1)
 row=s['issues'][a[2]];names={x['name'] for x in row['labels']}
 if '--add-label' in a:names.add(a[a.index('--add-label')+1])
 if '--remove-label' in a:names.discard(a[a.index('--remove-label')+1])
 row['labels']=[{'name':n} for n in sorted(names)]
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
        self.git("remote", "add", "origin", "https://github.test/owner/repo.git")
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
                        PASEO_AGENT_ID="worker-1", FAKE_TRACKER=str(self.store))
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
