from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_dispatch_pipeline as fixtures


class PipelineIntegrity(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.TicketDispatch()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()

    def close_unused_tickets(self):
        fixture = self.fixture
        fixture.reload()
        for number in ("61", "62"):
            fixture.state["issues"][number].update(
                state="CLOSED", stateReason="NOT_PLANNED", labels=[])
        fixture.save()

    def write_check_with_red_full_suite(self):
        fixture = self.fixture
        (fixture.repo / "scripts/check").write_text(
            '#!/usr/bin/env bash\n'
            'for arg in "$@"; do\n'
            '  if [ "$arg" = --all ]; then echo FAIL full-suite; exit 1; fi\n'
            'done\n'
            'echo PASS unit\n')
        fixture.git("add", ".")
        fixture.git("commit", "-qm", "full suite fails while default passes")
        fixture.git("push", "-q", "origin", "batch")
        red = subprocess.run(["bash", "scripts/check", "--all"], cwd=fixture.repo,
                             capture_output=True, text=True)
        self.assertEqual(red.returncode, 1, red.stdout + red.stderr)

    def tool(self, *arguments, cwd=None, session=None):
        fixture = self.fixture
        env = dict(fixture.env)
        if session is not None:
            env.update(TEST_SESSION=session, MMW_TICKET="61")
        return subprocess.run(
            [sys.executable, str(fixture.tools / "verify-ticket/scripts/verify-ticket.py"),
             *map(str, arguments)], cwd=cwd or fixture.repo, env=env,
            capture_output=True, text=True, timeout=30)

    def test_land_keeps_dirty_orphan_merge_worktree(self):
        fixture = self.fixture
        fixture.started()
        fixture.output()
        fixture.ok(fixture.command("land", 61))
        orphan = fixture.repo / ".worktrees/merge-retired"
        fixture.git("worktree", "add", "--detach", orphan, fixture.base)
        (orphan / "code").write_text("unsaved repair\n")
        (orphan / "new-work").write_text("untracked evidence\n")

        fixture.command("land", 61)

        self.assertTrue(orphan.is_dir(), "land deleted unfinished unrelated merge work")
        self.assertEqual((orphan / "code").read_text(), "unsaved repair\n")
        self.assertEqual((orphan / "new-work").read_text(), "untracked evidence\n")

    def test_finish_refuses_batch_tip_that_changed_after_summary(self):
        fixture = self.fixture
        fixture.open()
        self.close_unused_tickets()
        fixture.ok(fixture.command("summary", 60))
        before = fixture.git("rev-parse", "origin/project")
        self.write_check_with_red_full_suite()

        result = fixture.command("finish", 60)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        fixture.git("fetch", "-q", "origin")
        self.assertEqual(fixture.git("rev-parse", "origin/project"), before)
        self.assertNotEqual(fixture.reload()["issues"]["60"]["state"], "CLOSED")

    def test_finish_requires_expected_ci_results(self):
        fixture = self.fixture
        fixture.started()
        workflow = fixture.repo / ".worktrees/issue-61/.github/workflows/ci.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "on: pull_request\njobs:\n  unit:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: echo checked\n")
        fixture.output()
        fixture.ok(fixture.command("land", 61))
        fixture.reload()
        fixture.state["issues"]["62"].update(
            state="CLOSED", stateReason="NOT_PLANNED", labels=[])
        fixture.save()
        fixture.ok(fixture.command("summary", 60))
        before = fixture.git("rev-parse", "origin/project")
        service = fixture.bin / "gh"
        backend = fixture.bin / "gh-fixture"
        service.rename(backend)
        service.write_text(
            "#!/usr/bin/env python3\nimport os, sys\n"
            "if sys.argv[1:3] == ['pr', 'checks']:\n"
            " print('no checks reported', file=sys.stderr)\n raise SystemExit(1)\n"
            f"os.execv({str(backend)!r}, [{str(backend)!r}, *sys.argv[1:]])\n")
        service.chmod(0o755)

        result = fixture.command("finish", 60)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        fixture.git("fetch", "-q", "origin")
        self.assertEqual(fixture.git("rev-parse", "origin/project"), before)
        self.assertNotEqual(fixture.reload()["issues"]["60"]["state"], "CLOSED")

    def test_summary_does_not_claim_all_from_default_check_proof(self):
        fixture = self.fixture
        fixture.open()
        self.close_unused_tickets()
        self.write_check_with_red_full_suite()
        checked = fixture.ok(self.tool("--repository-check", "--base", "HEAD"))
        proof = json.loads(checked.stdout)["proof"]
        self.assertEqual(proof["tier"], "default")
        fixture.add_event(60, "spec.checked", result="met", **proof)

        result = fixture.command("summary", 60)

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("CHECK PASS all", result.stdout)
        comments = fixture.reload()["issues"]["60"]["comments"]
        self.assertFalse(fixture.events.fold(comments)["spec_closed"])

    def test_actual_reports_push_output_and_notify_worker_then_orchestrator(self):
        fixture = self.fixture
        worker = fixture.started()
        tree = fixture.repo / ".worktrees/issue-61"
        (tree / "code").write_text("reviewable output\n")
        fixture.git("add", ".", cwd=tree)
        fixture.git("commit", "-qm", "actual output", cwd=tree)
        head = fixture.git("rev-parse", "HEAD", cwd=tree)
        reviewer = fixture.ok(fixture.command(
            "send", "reviewer", 61, "--task", fixture.review_task, cwd=tree,
            env=dict(fixture.env, TEST_SESSION=worker))).stdout.strip()
        report = fixture.root / "actual report.md"
        report.write_text("Checked the changed output.\nScope and limits are stated here.\n")

        fixture.ok(self.tool(61, "--review", report, "--base", fixture.base,
                             "--head", head, cwd=tree, session=reviewer))
        shown = fixture.ok(fixture.command("wait", 61, "reviewer"))
        self.assertIn(report.read_text().strip(), shown.stdout)
        fixture.ok(self.tool(61, "--closeout", report, "--result", "complete",
                             "--commit", head, "--into", "batch", cwd=tree, session=worker))
        self.assertEqual(fixture.git("rev-parse", "origin/issue-61"), head)
        self.assertEqual(fixture.reload()["issues"]["61"]["state"], "CLOSED")

        notifications = Path(__file__).resolve().parents[1] / "notifications"
        sys.path.insert(0, str(notifications))
        self.addCleanup(sys.path.remove, str(notifications))
        import test_relay as relay_fixtures

        relay = relay_fixtures.RelayCase()
        self.addCleanup(relay.doCleanups)
        relay.setUp()
        relay.board[61] = [
            {**comment, "created_at": relay_fixtures.stamp(relay_fixtures.T0),
             "updated_at": relay_fixtures.stamp(relay_fixtures.T0)}
            for comment in fixture.reload()["issues"]["61"]["comments"]]
        self.assertTrue(relay.poll(), relay.err.getvalue())
        relay.relay.deliver()
        self.assertEqual(relay.send.sent, [
            ("paseo", worker, "#61 reviewer.reported"),
            ("paseo", "main-a", "#61 ticket.passed")])
        self.assertEqual(relay.err.getvalue(), "")


class ReopenedBatch(unittest.TestCase):
    def test_finish_does_not_reuse_a_merge_record_from_an_earlier_open(self):
        fixture = fixtures.TicketDispatch()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        (fixture.repo / 'first-run').write_text('first output\n')
        fixture.git('add', '.')
        fixture.git('commit', '-qm', 'first run')
        fixture.git('push', '-q', 'origin', 'batch')
        fixture.open()
        fixture.reload()
        for number in ('61', '62'):
            fixture.state['issues'][number].update(state='CLOSED', stateReason='NOT_PLANNED', labels=[])
        fixture.save()
        fixture.ok(fixture.command('summary', 60))
        fixture.ok(fixture.command('finish', 60))
        fixture.reload()
        fixture.state['issues']['60'].update(state='OPEN', stateReason=None)
        fixture.save()
        (fixture.repo / 'second-run').write_text('new output\n')
        fixture.git('add', '.')
        fixture.git('commit', '-qm', 'second run')
        output = fixture.git('rev-parse', 'HEAD')
        fixture.git('push', '-q', 'origin', 'batch')
        fixture.open()
        fixture.ok(fixture.command('summary', 60))
        fixture.ok(fixture.command('finish', 60))
        fixture.git('fetch', '-q', 'origin')
        contained = subprocess.run(['git', 'merge-base', '--is-ancestor', output, 'origin/project'],
                                   cwd=fixture.repo, capture_output=True, text=True)
        self.assertEqual(contained.returncode, 0, 'finish closed the reopened spec without its new output')


if __name__ == "__main__":
    unittest.main()
