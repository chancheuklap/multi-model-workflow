"""Tests for briefs.py and the relay's brief watch: no tracker, no runner, no network.

A batch is what one `dispatch.sh send <role> <brief file>` starts. What is asserted is
what the parent session and the children can see: who may report, what a report keeps,
when the relay queues the batch's one wake, what it sends, what an ack removes, and that
closing the batch's watch leaves nothing of it behind.

    python3 -m unittest discover -s mmw-v4/tests/relay -p test_briefs.py
"""

from __future__ import annotations

import sys
import os
import subprocess
import unittest
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_relay import MAIN_A, RelayCase, comment, relay  # noqa: E402

import briefs  # noqa: E402

PARENT = ("orca", "term_parent")


class BriefCase(RelayCase):
    """The ticket watch of RelayCase, and a batch of two researchers briefed by PARENT."""

    def setUp(self):
        super().setUp()
        self.batch = briefs.create(self.state, "researcher", 2, *PARENT)
        for n, session in ((1, "agt_r1"), (2, "agt_r2")):
            briefs.mark_started(self.state, self.batch, n, {
                "runner": "paseo", "session": session, "host": "codex",
                "model": "gpt-5.6-sol", "effort": "high"})
        self.relay.open_watch({"briefs": self.batch}, *PARENT)
        self.result = Path(self.tmp.name) / "answer.md"
        self.result.write_text("the findings, cited\n")

    def report(self, n: int, session: str | None = None):
        return briefs.report(self.state, self.batch, n, self.result, "paseo",
                             session or f"agt_r{n}")

    def brief_rows(self):
        return [(r["event"], r.get("batch"), r["session"]) for r in self.rows()
                if r["event"] == relay.BRIEF_DONE]


class CopyTest(BriefCase):
    """`briefs.py brief`: the file a child is pointed at is the brief, then how to report."""

    def test_briefs_checks_references_to_closed_batches(self):
        source = Path(self.tmp.name) / "follow-up.md"
        for batch, code in ((self.batch, 0), ("19990101-000000-abcd", 2)):
            for pointer in (f"briefs/{batch}/1/result.md",
                            str(briefs.batch_dir(self.state, batch) / "1/result.md")):
                source.write_text(f"Read [the answer]({pointer}).\n")
                run = subprocess.run(
                    [sys.executable, briefs.__file__, "check-references", "--repo", "o/r",
                     str(source)], capture_output=True, text=True)
                self.assertEqual(run.returncode, code, run.stderr)
                if code:
                    self.assertIn(str(source), run.stderr)
                    self.assertIn(batch, run.stderr)
                    self.assertIn("## Known", run.stderr)
                    self.assertTrue(run.stderr.isascii(), run.stderr)
        briefs.remove(self.state, self.batch)
        source.write_text(f"Read briefs/{self.batch}/1/result.md.\n")
        run = subprocess.run(
            [sys.executable, briefs.__file__, "check-references", "--repo", "o/r",
             str(source)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn(self.batch, run.stderr)

    def test_the_copy_is_the_brief_then_the_footer(self):
        source = Path(self.tmp.name) / "brief.txt"
        source.write_text("what to find out\n\n")
        copy = briefs.write_brief(self.state, self.batch, 1, source, "---\nreport it\n")
        self.assertEqual(copy, briefs.batch_dir(self.state, self.batch) / "1" / "brief.md")
        self.assertEqual(copy.read_text(), "what to find out\n\n---\nreport it\n")

    def test_nothing_is_copied_into_a_batch_that_is_gone(self):
        briefs.remove(self.state, self.batch)
        with self.assertRaises(briefs.Refusal):
            briefs.write_brief(self.state, self.batch, 1, self.result, "---")

    def test_a_new_batch_records_the_senders_worktree(self):
        worktree = Path(self.tmp.name) / "sender"
        worktree.mkdir()
        subprocess.run(["git", "init", "-q", str(worktree)], check=True)
        subdir = worktree / "notes"
        subdir.mkdir()
        run = subprocess.run(
            [sys.executable, briefs.__file__, "new", "--repo", "o/r", "--role",
             "researcher", "--count", "1", "--runner", "orca", "--session", "sender"],
            cwd=subdir, env=os.environ.copy(),
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        state = briefs.statedir.state_dir("o/r")
        record = briefs.batch_record(state, run.stdout.strip())
        self.assertEqual(record.get("worktree"), str(worktree.resolve()))


class ReportTest(BriefCase):
    def test_the_childs_report_is_kept_in_the_batch(self):
        kept = self.report(1)
        self.assertEqual(kept.read_text(), "the findings, cited\n")
        states = [b["state"] for b in briefs.briefs_of(self.state, self.batch)]
        self.assertEqual(states, ["reported", "open"])

    def test_only_the_session_started_for_the_brief_may_report_it(self):
        with self.assertRaises(briefs.Refusal) as caught:
            self.report(1, session="agt_r2")
        self.assertIn("agt_r1", str(caught.exception))
        self.assertEqual(briefs.briefs_of(self.state, self.batch)[0]["state"], "open")

    def test_an_empty_answer_is_refused(self):
        self.result.write_text("  \n")
        with self.assertRaises(briefs.Refusal):
            self.report(1)
        self.assertEqual(briefs.briefs_of(self.state, self.batch)[0]["state"], "open")

    def test_the_first_report_stands(self):
        self.report(1)
        self.result.write_text("a second answer\n")
        with self.assertRaises(briefs.Refusal):
            self.report(1)
        self.assertEqual(briefs.briefs_of(self.state, self.batch)[0]["result"],
                         str(self.state / "briefs" / self.batch / "1" / "result.md"))
        self.assertEqual((self.state / "briefs" / self.batch / "1" / "result.md").read_text(),
                         "the findings, cited\n")

    def test_a_brief_marked_lost_takes_no_late_report(self):
        self.assertTrue(briefs.mark_lost(self.state, self.batch, 1, "paseo says stopped"))
        with self.assertRaises(briefs.Refusal) as caught:
            self.report(1)
        self.assertIn("lost", str(caught.exception))

    def test_a_report_to_a_closed_batch_is_refused(self):
        self.relay.close_watch(f"briefs:{self.batch}")
        with self.assertRaises(briefs.Refusal):
            self.report(1)


class BatchWakeTest(BriefCase):
    def test_nothing_is_queued_while_one_brief_is_open(self):
        self.report(1)
        self.relay.poll_briefs()
        self.assertEqual(self.brief_rows(), [])

    def test_one_wake_for_the_whole_batch_once_every_brief_has_reported(self):
        self.report(1)
        self.report(2)
        self.relay.poll_briefs()
        self.relay.poll_briefs()
        self.assertEqual(self.brief_rows(), [(relay.BRIEF_DONE, self.batch, "term_parent")])
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("orca", "term_parent", f"brief {self.batch} done")])

    def test_a_lost_brief_counts_as_done(self):
        self.report(1)
        briefs.mark_lost(self.state, self.batch, 2, "paseo says stopped")
        self.relay.poll_briefs()
        self.assertEqual(len(self.brief_rows()), 1)

    def test_the_ack_names_the_batch_and_the_wake_is_not_queued_again(self):
        self.report(1)
        self.report(2)
        self.relay.poll_briefs()
        self.relay.deliver()
        self.assertIsNotNone(self.relay.ack_wake(PARENT, None, relay.BRIEF_DONE, self.batch))
        self.relay.poll_briefs()
        self.assertEqual(self.brief_rows(), [])

    def test_an_ack_of_another_batch_removes_nothing(self):
        self.report(1)
        self.report(2)
        self.relay.poll_briefs()
        self.assertIsNone(self.relay.ack_wake(PARENT, None, relay.BRIEF_DONE,
                                              "20260101-000000-abcd"))
        self.assertEqual(len(self.brief_rows()), 1)

    def test_the_batch_wake_and_a_ticket_wake_each_reach_their_own_orchestrator(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.report(1)
        self.report(2)
        self.relay.cycle(30, 90)
        self.assertEqual(sorted(self.send.sent), sorted([
            ("orca", "term_parent", f"brief {self.batch} done"),
            ("paseo", "main-a", "#61 ticket.passed")]))



class BatchWatchTest(BriefCase):
    def test_open_batches_are_found_by_their_parent(self):
        other_runner = briefs.create(self.state, "candidate", 1, "paseo", PARENT[1])
        other_session = briefs.create(self.state, "candidate", 1, PARENT[0], "another")
        nested = briefs.create(self.state, "candidate", 1, *PARENT)
        self.assertEqual({b["batch"] for b in briefs.open_batches(self.state, PARENT)},
                         {self.batch, nested})
        self.report(1)
        self.report(2)
        self.assertEqual({b["batch"] for b in briefs.open_batches(self.state, PARENT)},
                         {self.batch, nested})
        briefs.remove(self.state, self.batch)
        briefs.remove(self.state, nested)
        self.assertEqual(briefs.open_batches(self.state, PARENT), [])
        self.assertEqual({b["batch"] for b in briefs.open_batches(self.state)},
                         {other_runner, other_session})

    def test_a_batch_shares_no_ticket_with_any_watch(self):
        self.assertEqual(set(self.watches()), {"tickets:61,62", f"briefs:{self.batch}"})
        self.poll()  # a batch's watch lists no ticket to read
        self.assertNotIn("brief", " ".join(str(c) for c in self.gh.calls))

    def test_closing_the_watch_removes_the_batch(self):
        closed, _ = self.relay.close_watch(f"briefs:{self.batch}")
        self.assertEqual(list(closed), [f"briefs:{self.batch}"])
        self.assertFalse((self.state / "briefs" / self.batch).exists())


    def test_a_parent_gone_for_an_hour_has_its_batch_removed(self):
        self.ask.answers[PARENT] = "stopped"
        self.relay.check_mains()
        self.clock.moment += timedelta(seconds=relay.MAIN_GONE_AFTER)
        self.relay.check_mains()
        self.assertNotIn(f"briefs:{self.batch}", self.watches())
        self.assertFalse((self.state / "briefs" / self.batch).exists())

    def test_the_wake_of_a_closed_batch_is_dropped_unsent(self):
        self.report(1)
        self.report(2)
        self.relay.poll_briefs()
        self.relay.close_watch(f"briefs:{self.batch}")
        self.relay.deliver()
        self.assertEqual(self.send.sent, [])
        self.assertEqual(self.brief_rows(), [])


if __name__ == "__main__":
    unittest.main()
