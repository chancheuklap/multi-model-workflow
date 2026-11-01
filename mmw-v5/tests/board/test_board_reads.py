from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

import test_board_data as fixtures


class GitHub:
    def __init__(self):
        self.tree = fixtures.container(10, "Plain v5 spec", [
            fixtures.leaf(11, "Produce output", state="CLOSED"),
            fixtures.leaf(12, "Use output", blocked=[
                {"number": 11, "state": "CLOSED", "stateReason": "COMPLETED"}]),
        ], ["mmw:spec"])
        self.tree["subIssues"]["nodes"][0]["stateReason"] = "COMPLETED"
        self.comments = {11: [], 12: []}
        self.calls = []
        self.fail = False

    def __call__(self, args):
        self.calls.append(list(args))
        if self.fail:
            return 1, "", "GitHub temporarily unavailable"
        if args[:2] == ["repo", "view"]:
            return 0, "owner/plain\n", ""
        if args[:2] == ["issue", "list"]:
            rows = [] if args[args.index("--label") + 1] == "mmw:map" else [
                {"number": 10, "labels": [{"name": "mmw:spec"}]}]
            return 0, json.dumps(rows), ""
        if args[:2] == ["api", "graphql"]:
            return 0, json.dumps({"data": {"repository": {"issue": self.tree}}}), ""
        if args[:2] == ["api", "-i"]:
            number = int(args[2].split("/issues/")[1].split("/")[0])
            body = json.dumps(self.comments[number])
            tag = '"' + hashlib.sha256(body.encode()).hexdigest() + '"'
            if f"If-None-Match: {tag}" in args:
                return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304"
            return 0, f"HTTP/2 200 OK\nETag: {tag}\n\n{body}", ""
        raise AssertionError(args)


def started(number=11):
    return fixtures.event(
        "worker.started", number, id=1, session="worker-1", runner="paseo",
        machine="test-machine", host="codex", model="test-model", effort="high",
        grade="junior-worker", worktree=f"/repo/.worktrees/issue-{number}",
        branch=f"issue-{number}", base="a" * 40, into="batch")


class BoardReads(unittest.TestCase):
    def setUp(self):
        self.service = GitHub()
        self.now = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
        self.store = fixtures.board_data.BoardStore(gh=self.service, clock=lambda: self.now)

    def test_closed_worker_keeps_dependency_waiting_until_pass_and_landing_are_recorded(self):
        self.service.comments[11] = [started()]
        initial = fixtures.tickets(self.store.answer())
        self.assertEqual(initial[11]["blocker_hold"], "still held, completion not recorded")
        self.assertEqual(initial[12]["blockers"][0]["blocker_hold"],
                         "still held, completion not recorded")

        self.service.comments[11].append(fixtures.event(
            "ticket.passed", 11, id=2, commit="b" * 40, into="batch"))
        passed = fixtures.tickets(self.store.answer())
        self.assertEqual(passed[12]["blockers"][0]["blocker_hold"], "passed, not landed")
        self.assertEqual(passed[11]["fold"]["outcome"]["payload"]["commit"], "b" * 40)

        self.service.comments[11].append(fixtures.event(
            "ticket.landed", 11, id=3, commit="b" * 40, into="batch"))
        landed = fixtures.tickets(self.store.answer())
        self.assertEqual(landed[12]["blockers"][0]["blocker_hold"], "")
        self.assertTrue(landed[11]["fold"]["landed"])
        self.assertEqual([row["event"] for row in landed[11]["events"]],
                         ["worker.started", "ticket.passed", "ticket.landed"])

    def test_manual_close_and_explicit_not_planned_release_without_fabricated_pass(self):
        for held, reason in ((False, "COMPLETED"), (True, "NOT_PLANNED")):
            with self.subTest(held=held, reason=reason):
                service = GitHub()
                service.tree["subIssues"]["nodes"][0]["stateReason"] = reason
                service.comments[11] = [started()] if held else []
                store = fixtures.board_data.BoardStore(gh=service)
                rows = fixtures.tickets(store.answer())
                self.assertEqual(rows[11]["state_reason"], reason)
                self.assertEqual(rows[11]["blocker_hold"], "")
                self.assertEqual(rows[12]["blockers"][0]["blocker_hold"], "")
                self.assertFalse(rows[11]["fold"]["passed"])
                self.assertFalse(rows[11]["fold"]["landed"])

    def test_failed_poll_preserves_snapshot_and_recovery_clears_failure(self):
        self.service.comments[11] = [started()]
        first = self.store.answer()
        self.service.comments[11].append(fixtures.event("ticket.returned", 11, id=2))
        self.service.fail = True
        self.now += dt.timedelta(seconds=1)
        failed = self.store.answer()
        self.assertEqual(failed["tasks"], first["tasks"])
        self.assertEqual(failed["read_at"], first["read_at"])
        self.assertIn("temporarily unavailable", failed["read_failed"]["message"])

        self.service.fail = False
        self.now += dt.timedelta(seconds=1)
        recovered = self.store.answer()
        self.assertNotIn("read_failed", recovered)
        self.assertNotEqual(recovered["read_at"], first["read_at"])
        self.assertTrue(fixtures.tickets(recovered)[11]["fold"]["returned"])

    def test_repaired_unreadable_event_after_landing_is_read_again(self):
        self.service.comments[11] = [started(),
            fixtures.event("ticket.passed", 11, id=2, commit="b" * 40),
            fixtures.event("ticket.landed", 11, id=3),
            {"id": 4, "body": '<!-- mmw {"v":1,"event":"unknown.event"} -->'}]
        unreadable = fixtures.tickets(self.store.answer())[11]
        self.assertEqual(unreadable["blocker_hold"], "its events cannot be read")
        self.assertFalse(fixtures.board_data.finished(unreadable))

        self.service.comments[11] = self.service.comments[11][:3]
        repaired = fixtures.tickets(self.store.answer())[11]
        self.assertEqual(repaired["blocker_hold"], "")
        self.assertFalse(repaired["fold"]["unreadable"])
        self.assertTrue(fixtures.board_data.finished(repaired))
        self.store.answer()
        reads = [args for args in self.service.calls
                 if args[:2] == ["api", "-i"] and "/issues/11/" in args[2]]
        self.assertEqual(len(reads), 2, "read the repair, then stop polling the finished ticket")

    def test_concurrent_polls_keep_one_committed_cache_and_use_its_etags(self):
        self.service.comments[11] = [started()]
        start = threading.Barrier(3)
        answers = []

        def read():
            start.wait(timeout=3)
            answers.append(self.store.answer())

        workers = [threading.Thread(target=read) for _ in range(2)]
        for worker in workers:
            worker.start()
        start.wait(timeout=3)
        for worker in workers:
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive())
        self.assertEqual(len(answers), 2)
        self.assertEqual(answers[0], answers[1])
        reads = [args for args in self.service.calls
                 if args[:2] == ["api", "-i"] and "/issues/11/" in args[2]]
        self.assertEqual(len(reads), 2)
        self.assertFalse(any(arg.startswith("If-None-Match:") for arg in reads[0]))
        self.assertTrue(any(arg.startswith("If-None-Match:") for arg in reads[1]))

    def test_actual_default_reads_bind_origin_despite_foreign_gh_repo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin",
                            "https://github.test/owner/plain.git"], check=True)
            binary = root / "bin"
            binary.mkdir()
            fixture = root / "tree.json"
            fixture.write_text(json.dumps(self.service.tree))
            log = root / "calls.jsonl"
            command = binary / "gh"
            command.write_text(f"#!{sys.executable}\n" + '''import json, os, sys
from pathlib import Path
a = sys.argv[1:]
with Path(os.environ['CALL_LOG']).open('a') as stream:
    stream.write(json.dumps(a) + '\\n')
if a[:2] == ['repo', 'view']:
    assert a[2] == 'https://github.test/owner/plain.git'
    assert 'GH_REPO' not in os.environ
    print('owner/plain')
elif a[:2] == ['issue', 'list']:
    assert a[a.index('--repo') + 1] == 'owner/plain'
    print('[]' if a[a.index('--label') + 1] == 'mmw:map' else '[{"number":10,"labels":[{"name":"mmw:spec"}]}]')
elif a[:2] == ['api', 'graphql']:
    assert 'o=owner' in a and 'n=plain' in a
    print(json.dumps({'data': {'repository': {'issue': json.loads(Path(os.environ['TREE_FIXTURE']).read_text())}}}))
elif a[:2] == ['api', '-i']:
    assert a[2].startswith('repos/owner/plain/issues/')
    print('HTTP/2 200 OK\\nETag: "plain"\\n\\n[]')
else:
    raise AssertionError(a)
''')
            command.chmod(0o755)
            env = dict(os.environ, HOME=str(root), MMW_HOME=str(root / "v5-home"),
                       GH_REPO="foreign/wrong", TREE_FIXTURE=str(fixture), CALL_LOG=str(log),
                       PATH=str(binary) + os.pathsep + os.environ["PATH"])
            code = ("import json,sys;sys.path.insert(0,sys.argv[1]);import board_data;"
                    "print(json.dumps(board_data.BoardStore().answer()))")
            result = subprocess.run([sys.executable, "-c", code,
                                     str(fixtures.SERVER.parent)], cwd=repo, env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            answer = json.loads(result.stdout)
            self.assertNotIn("read_failed", answer)
            self.assertEqual(answer["repo"], "owner/plain")
            self.assertEqual(sorted(fixtures.tickets(answer)), [11, 12])
            self.assertEqual(sum(json.loads(line)[:2] == ["repo", "view"]
                                 for line in log.read_text().splitlines()), 1)

            subprocess.run(["git", "-C", str(repo), "remote", "remove", "origin"], check=True)
            missing = subprocess.run([sys.executable, "-c", code,
                                      str(fixtures.SERVER.parent)], cwd=repo, env=env,
                                     capture_output=True, text=True, timeout=10)
            self.assertEqual(missing.returncode, 0, missing.stderr)
            refused = json.loads(missing.stdout)
            self.assertEqual(refused["tasks"], [])
            self.assertIsNone(refused["repo"])
            self.assertIn("origin", refused["read_failed"]["message"])
            self.assertEqual(sum(json.loads(line)[:2] == ["repo", "view"]
                                 for line in log.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
