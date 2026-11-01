from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _load import TOOLS, load_events, load_tool

tracker = load_tool("dispatch", "tracker.py")
statedir = load_tool("dispatch", "statedir.py")
events = load_events()


class RepositoryIdentity(unittest.TestCase):
    def test_origin_selects_repository_even_with_a_foreign_gh_default(self):
        tracker._repository.cache_clear()
        calls = []

        def run(args, **kwargs):
            calls.append((args, kwargs))
            if args[:3] == ["git", "remote", "get-url"]:
                return subprocess.CompletedProcess(args, 0, "https://github.test/owner/repo.git\n", "")
            self.assertNotIn("GH_REPO", kwargs["env"])
            return subprocess.CompletedProcess(args, 0, "owner/repo\n", "")

        with mock.patch.dict(os.environ, {"GH_REPO": "other/repo", "CLICOLOR_FORCE": "1"}):
            with mock.patch.object(tracker.subprocess, "run", side_effect=run):
                self.assertEqual(tracker.repository(), "owner/repo")
                self.assertEqual(tracker.environment()["GH_REPO"], "owner/repo")
        self.assertEqual(calls[1][0][3], "https://github.test/owner/repo.git")
        self.assertNotIn("CLICOLOR_FORCE", calls[1][1]["env"])

    def test_missing_origin_is_an_explicit_failure(self):
        with mock.patch.object(tracker.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "missing")):
            with self.assertRaisesRegex(tracker.RepositoryError, "origin"):
                tracker.repository()


class LocalState(unittest.TestCase):
    def test_default_state_is_separate_from_v4(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ):
                os.environ.pop("MMW_HOME", None)
                with mock.patch.object(Path, "home", return_value=Path(tmp)):
                    self.assertEqual(statedir.home(), Path(tmp) / ".mmw-v5")
                    self.assertEqual(statedir.state_dir("Owner/Repo"), Path(tmp) / ".mmw-v5/state/owner__repo")
                    self.assertFalse((Path(tmp) / ".mmw").exists())

    def test_explicit_state_home_and_atomic_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"MMW_HOME": tmp}):
            directory = statedir.state_dir("Owner/Repo")
            self.assertEqual(directory, statedir.state_dir("owner/repo"))
            record = directory / "sample.json"
            statedir.write_atomic(record, json.dumps({"session": "one"}))
            self.assertEqual(statedir.read_json(record, None), {"session": "one"})
            record.write_text("invalid json")
            with self.assertRaises(json.JSONDecodeError):
                statedir.read_json(record, {})
            self.assertEqual(list(directory.glob("*.tmp")), [])

    def test_lock_excludes_a_second_process_then_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "write.lock"
            program = """import sys
sys.path.insert(0, sys.argv[1])
import statedir
from pathlib import Path
try:
    with statedir.locked(Path(sys.argv[2]), wait=0, purpose='child'):
        print('acquired')
except statedir.LockHeld:
    print('held')
"""
            args = [sys.executable, "-c", program, str(TOOLS / "dispatch/scripts"), str(lock)]
            with statedir.locked(lock, wait=0, purpose="test"):
                self.assertEqual(statedir.holder(lock)["purpose"], "test")
                run = subprocess.run(args, capture_output=True, text=True, check=True)
                self.assertEqual(run.stdout.strip(), "held")
            run = subprocess.run(args, capture_output=True, text=True, check=True)
            self.assertEqual(run.stdout.strip(), "acquired")
            self.assertIsNone(statedir.holder(lock))


FAKE_GH = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
path = Path(os.environ['FAKE_GH_STATE'])
state = json.loads(path.read_text())
a = sys.argv[1:]
if a[:2] == ['repo', 'view']:
    assert a[2] == 'https://github.test/o/r.git', a
    assert 'GH_REPO' not in os.environ
    print('o/r')
    sys.exit(0)
assert os.environ.get('GH_REPO') == 'o/r', os.environ.get('GH_REPO')
if a[:2] == ['label', 'list']:
    print(json.dumps(state['labels']))
elif a[:2] == ['label', 'create']:
    name = a[2]
    assert not any(x['name'] == name for x in state['labels'])
    state['labels'].append({'name': name, 'color': a[a.index('--color')+1], 'description': a[a.index('--description')+1]})
    path.write_text(json.dumps(state))
elif a[:2] == ['label', 'edit']:
    for label in state['labels']:
        if label['name'] == a[2]:label['description'] = a[a.index('--description')+1]
    path.write_text(json.dumps(state))
elif a[:2] == ['api', 'graphql']:
    children = []
    for ticket in state['tickets'].values():
        if (ticket.get('parent') or {}).get('number') != 100:continue
        children.append({'number': ticket['number'], 'title': ticket['title'], 'state': ticket['state'], 'labels': {'nodes': ticket['labels']}, 'blockedBy': ticket['blockedBy'], 'subIssuesSummary': {'total': 0, 'completed': 0}, 'subIssues': {'nodes': []}})
    print(json.dumps({'data': {'repository': {'issue': {'number': 100, 'title': 'Spec', 'state': 'OPEN', 'subIssuesSummary': {'total': len(children), 'completed': 0}, 'subIssues': {'nodes': children}}}}}))
elif a[:2] == ['issue', 'view']:
    ticket = state['tickets'][a[2]]
    fields = a[a.index('--json')+1].split(',')
    print(json.dumps({key: ticket.get(key) for key in fields}))
elif a[:2] == ['issue', 'edit']:
    ticket = state['tickets'][a[2]]
    names = {x['name'] for x in ticket['labels']}
    if '--add-label' in a:names.add(a[a.index('--add-label')+1])
    if '--remove-label' in a:names.discard(a[a.index('--remove-label')+1])
    ticket['labels'] = [{'name': name} for name in sorted(names)]
    path.write_text(json.dumps(state))
elif a[:2] == ['api', '--paginate']:
    address = a[-1]
    if '/comments?' in address:rows = state['tickets'][address.split('/issues/')[1].split('/')[0]]['comments']
    else:rows = [x for x in state['tickets'].values() if x['state'] == 'OPEN']
    print(json.dumps([rows]))
else:
    raise AssertionError(a)
'''


def ticket(number, blockers=(), *, parent=True):
    return {"number": number, "title": f"Ticket {number}", "state": "OPEN",
            "body": "## Parent\n#100\n\n## What to build\nImplement the stated behavior.\n\n## Acceptance criteria\n- [ ] The caller gets the agreed result\n\n## Blocked by\nNone\n",
            "labels": [{"name": "mmw:ticket"}, {"name": "ready-for-agent"}],
            "assignees": [], "blockedBy": {"nodes": [{"number": n, "state": "OPEN"} for n in blockers]},
            "parent": {"number": 100} if parent else None, "comments": [],
            "createdAt": "2026-11-01T00:00:00Z", "closedAt": ""}


class ToolCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://github.test/o/r.git"], check=True)
        binary = self.root / "bin"
        binary.mkdir()
        (binary / "gh").write_text(FAKE_GH)
        (binary / "gh").chmod(0o755)
        self.state_path = self.root / "github.json"
        self.state = {"labels": [], "tickets": {"100": {"number": 100, "labels": [{"name": "mmw:spec"}], "state": "OPEN", "parent": None, "body": "Spec", "comments": []}, "101": ticket(101), "102": ticket(102, [101])}}
        self.save()
        self.env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"],
                        FAKE_GH_STATE=str(self.state_path), GH_REPO="wrong/repository",
                        MMW_HOME=str(self.root / "state"), MMW_EVENTS_PY="/missing/v4/events.py")

    def save(self):
        self.state_path.write_text(json.dumps(self.state))

    def run_tool(self, group, name, *args):
        return subprocess.run([sys.executable, str(TOOLS / group / "scripts" / name), *map(str, args)],
                              cwd=self.repo, env=self.env, text=True, capture_output=True)

    def assert_ok(self, run):
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_missing_origin_reports_the_repository_error_without_a_traceback(self):
        subprocess.run(["git", "remote", "remove", "origin"], cwd=self.repo, check=True)
        for group, name, args, code in (
            ("dispatch", "status.py", ("--frontier", 100), 2),
            ("verify-ticket", "events.py", ("fold", 101), 2),
            ("verify-ticket", "issue_tree.py", (100, "--root", "spec"), 2),
            ("setup-mmw", "labels.py", (), 1),
        ):
            with self.subTest(tool=name):
                run = self.run_tool(group, name, *args)
                self.assertEqual(run.returncode, code, run.stdout + run.stderr)
                self.assertIn("origin", run.stderr)
                self.assertNotIn("Traceback", run.stderr)

    def test_plain_v5_ticket_is_eligible_without_check_owns_or_worker_grade(self):
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "101\n")
        table = self.run_tool("dispatch", "status.py", "--table", 100)
        self.assert_ok(table)
        self.assertIn("#101", table.stdout)
        self.assertRegex(table.stdout, r"#102.*waiting on #101")
        self.assertNotIn("met of", table.stdout)

    def test_dependency_stays_blocked_until_passed_work_lands(self):
        first = self.state['tickets']['101']
        first.update(state="CLOSED", comments=[{"id": 1, "body": events.build("ticket.passed", ticket=101, line="Completed", commit="a"*40, into="night")}])
        self.state['tickets']['102']['blockedBy']['nodes'][0]['state'] = 'CLOSED'
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "")
        first['comments'].append({"id": 2, "body": events.build("ticket.landed", ticket=101, line="Landed")})
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "102\n")

    def close_blocker_with_worker_hold(self, reason):
        first = self.state["tickets"]["101"]
        first.update(state="CLOSED", stateReason=reason, comments=[{"id": 1, "body": events.build(
            "worker.started", ticket=101, line="Started", session="one", runner="fake", machine="test",
            host="codex", model="test-model", effort="high", grade="junior-worker",
            worktree=str(self.repo), branch="issue-101", base="a" * 40)}])
        self.state["tickets"]["102"]["blockedBy"]["nodes"][0]["state"] = "CLOSED"
        self.save()
        return first

    def test_close_success_without_result_post_does_not_release_the_dependent(self):
        first = self.close_blocker_with_worker_hold("COMPLETED")
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "")
        first["comments"].append({"id": 2, "body": events.build(
            "ticket.passed", ticket=101, line="Completed", commit="a" * 40, into="night")})
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "")
        first["comments"].append({"id": 3, "body": events.build(
            "ticket.landed", ticket=101, line="Landed")})
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "102\n")

    def test_manual_close_without_a_hold_releases_the_dependent(self):
        first = self.state["tickets"]["101"]
        first.update(state="CLOSED", stateReason="COMPLETED", comments=[])
        self.state["tickets"]["102"]["blockedBy"]["nodes"][0]["state"] = "CLOSED"
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "102\n")

    def test_explicit_not_planned_releases_the_dependent_despite_an_old_hold(self):
        first = self.close_blocker_with_worker_hold("NOT_PLANNED")
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "102\n")
        first["comments"].append({"id": 2, "body": "<!-- mmw {broken} -->"})
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assertEqual((run.returncode, run.stdout), (2, ""))
        self.assertIn("cannot determine eligible work", run.stderr)

    def test_not_planned_does_not_override_an_existing_pass_waiting_to_land(self):
        first = self.close_blocker_with_worker_hold("NOT_PLANNED")
        first["comments"].append({"id": 2, "body": events.build(
            "ticket.passed", ticket=101, line="Completed", commit="a" * 40, into="night")})
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "")

    def test_started_session_prevents_duplicate_work(self):
        self.state['tickets']['101']['comments'] = [{"id": 1, "body": events.build(
            "worker.started", ticket=101, line="Started", session="one", runner="codex-app", machine="test",
            host="codex", model="test-model", effort="high", grade="junior-worker", worktree=str(self.repo), branch="issue-101", base="a"*40)}]
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assert_ok(run)
        self.assertEqual(run.stdout, "")

    def test_unreadable_event_cannot_look_like_available_work(self):
        self.state['tickets']['101']['comments'] = [{"id": 1, "body": '<!-- mmw {"v":9,"event":"ticket.passed"} -->'}]
        self.save()
        run = self.run_tool("dispatch", "status.py", "--frontier", 100)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, "")
        self.assertIn("cannot determine eligible work", run.stderr)

    def test_label_creation_is_repeatable_and_preserves_existing_choices(self):
        self.state['labels'] = [{"name": "needs-triage", "color": "123456", "description": "project-owned"}]
        self.save()
        run = self.run_tool("setup-mmw", "labels.py")
        self.assert_ok(run)
        first = json.loads(self.state_path.read_text())['labels']
        self.assertIn({"name": "needs-triage", "color": "123456", "description": "project-owned"}, first)
        names = {label['name'] for label in first}
        self.assertTrue({"mmw:spec", "mmw:ticket", "ready-for-agent", "junior-worker", "wayfinder:map"}.issubset(names))
        run = self.run_tool("setup-mmw", "labels.py")
        self.assert_ok(run)
        self.assertEqual(json.loads(self.state_path.read_text())['labels'], first)
        self.assertNotIn("created ", run.stdout)

    def test_label_migration_preserves_executable_spec_tickets(self):
        self.state['tickets']['103'] = ticket(103, parent=False)
        self.state['tickets']['103'].update(labels=[{"name": "needs-triage"}], body="## Problem\nA pending proposal")
        self.save()
        run = self.run_tool("setup-mmw", "labels.py", "--migrate")
        self.assert_ok(run)
        got = json.loads(self.state_path.read_text())['tickets']
        self.assertIn({"name": "mmw:problem"}, got['103']['labels'])
        self.assertIn({"name": "mmw:ticket"}, got['101']['labels'])
        self.assertIn({"name": "mmw:ticket"}, got['102']['labels'])


if __name__ == "__main__":
    unittest.main()
