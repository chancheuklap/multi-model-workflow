"""The event vocabulary and the fold: comments in, a ticket's state out.

The fold is a pure function over a list of comments, so every state it can reach is
reached here by writing the comments down. No tracker, no runner, no clock.

    python3 -m unittest discover -s mmw-v2/tests/verify-ticket -p test_events.py
"""

import json
import subprocess
import sys
import unittest

from _load import EVENTS, load_events

events = load_events()

SAME_SECOND = "2026-09-10T02:00:00Z"


def ev(name, line, ticket=61, at=SAME_SECOND, **fields):
    return events.build(name, ticket=ticket, line=line, at=at, **fields)


def comment(ident, body):
    """A comment the way `gh issue view --json comments` returns it."""
    return {"body": body, "createdAt": SAME_SECOND,
            "url": f"https://github.com/o/r/issues/61#issuecomment-{ident}"}


def started(session="term_7", runner="orca", kind="worker"):
    return ev(f"{kind}.started", f"{kind} started on {runner}: session {session}",
              session=session, runner=runner, host="grok", model="grok-4.6",
              effort="high", grade="junior-worker", worktree="/repo/.worktrees/issue-61",
              branch="issue-61", base="0" * 40)


class TheVocabulary(unittest.TestCase):
    """23 events, one shape, a closed set of subjects."""

    def test_there_are_twenty_three_events(self):
        self.assertEqual(len(events.EVENTS), 23)

    def test_every_name_is_subject_dot_past_tense_verb_with_no_value_in_it(self):
        for name in events.EVENTS:
            with self.subTest(name=name):
                self.assertRegex(name, r"^[a-z]+\.[a-z]+$")
                subject, verb = name.split(".")
                self.assertIn(subject, events.SUBJECTS)
                self.assertTrue(verb.endswith("ed") or verb == "lost", verb)

    def test_the_six_refusals_and_the_three_release_reasons(self):
        self.assertEqual(len(events.REFUSALS), 6)
        self.assertEqual(events.RELEASE_REASONS, ("landed", "suspended", "worker-lost"))

    def test_an_unknown_event_is_refused_when_written(self):
        with self.assertRaises(events.EventError):
            events.build("worker.failover", ticket=61, line="x")

    def test_a_missing_required_field_is_refused_when_written(self):
        with self.assertRaises(events.EventError):
            events.build("worker.started", ticket=61, line="started", runner="orca")

    def test_a_value_outside_a_closed_set_is_refused_when_written(self):
        with self.assertRaises(events.EventError):
            events.build("ticket.released", ticket=61, line="x", reason="bored")

    def test_a_worker_start_missing_any_of_its_facts_is_refused_when_written(self):
        full = dict(session="t", runner="orca", host="grok", model="m", effort="high",
                    grade="junior-worker", worktree="/repo/.worktrees/issue-61",
                    branch="issue-61", base="0" * 40)
        events.build("worker.started", ticket=61, line="started", **full)
        for key in full:
            with self.subTest(missing=key):
                with self.assertRaises(events.EventError):
                    events.build("worker.started", ticket=61, line="started",
                                 **{k: v for k, v in full.items() if k != key})

    def test_a_worker_start_on_a_relative_worktree_is_refused(self):
        with self.assertRaises(events.EventError):
            events.build("worker.started", ticket=61, line="started", session="t",
                         runner="orca", host="grok", model="m", effort="high",
                         grade="junior-worker", worktree=".worktrees/issue-61",
                         branch="issue-61", base="0" * 40)

    def test_no_effort_is_written_as_an_explicit_dash(self):
        body = events.build("worker.started", ticket=61, line="started", session="t",
                            runner="herdr", host="grok", model="m", effort="—",
                            grade="junior-worker", worktree="/w", branch="issue-61",
                            base="0" * 40)
        self.assertEqual(events.parse(body)[1]["effort"], "—")

    def test_a_session_is_named_by_its_runner_and_its_id_together(self):
        with self.assertRaises(events.EventError):
            events.build("worker.retracted", ticket=61, line="x", session="term_7")
        with self.assertRaises(events.EventError):
            events.build("worker.lost", ticket=61, line="x", session="term_7")

    def test_a_short_commit_on_a_verdict_is_refused_when_written(self):
        with self.assertRaises(events.EventError):
            events.build("verifier.passed", ticket=61, line="x", commit="3f9c2e1a")


class TheCommentFormat(unittest.TestCase):
    """First line for a person, the block for a program."""

    def test_the_first_line_is_the_prose_and_the_block_carries_the_common_fields(self):
        body = ev("ticket.claimed", "Claimed #61 on issue-61", spec=76, login="bot")
        self.assertEqual(body.splitlines()[0], "Claimed #61 on issue-61")
        what, payload = events.parse(body)
        self.assertEqual(what, "event")
        self.assertEqual({k: payload[k] for k in events.COMMON}, {
            "v": 1, "event": "ticket.claimed", "stage": "intake", "actor": "worker",
            "spec": 76, "ticket": 61, "at": SAME_SECOND})
        self.assertEqual(payload["login"], "bot")

    def test_the_block_is_one_line_at_the_end(self):
        body = ev("worker.decided", "DECISIONS", text="a\nb")
        self.assertTrue(body.rstrip("\n").splitlines()[-1].startswith("<!-- mmw {"))
        self.assertTrue(body.rstrip("\n").endswith("-->"))

    def test_a_value_holding_the_comment_closer_cannot_end_the_block_early(self):
        body = ev("ticket.refused", "NOT_READY", reason="blocked", note="a --> b")
        what, payload = events.parse(body)
        self.assertEqual((what, payload["note"]), ("event", "a --> b"))

    def test_prose_quoting_an_event_carries_no_second_block(self):
        """A review of this very code quotes blocks; its ticket must still read one event."""
        quoted = started("term_9")
        body = events.build("reviewer.reported", ticket=61, line="REVIEW a..b",
                            text="the fixture was:\n" + quoted, base="a", head="b")
        self.assertEqual(events.parse(body)[0], "event")
        self.assertEqual(events.parse(body)[1]["event"], "reviewer.reported")
        self.assertIn("&lt;!-- mmw", body)
        state = events.fold([body])
        self.assertEqual((state["unreadable"], state["sessions"]), ([], []))

    def test_a_first_line_quoting_a_block_is_neutralised_too(self):
        body = events.build("ticket.claimed", ticket=61, line="see <!-- mmw {} -->")
        self.assertEqual(events.parse(body)[0], "event")

    def test_a_comment_with_no_block_is_prose_whatever_its_first_line_says(self):
        for body in ("ALL MET\nBranch: issue-61", "VERDICT " + "a" * 40 + " by x — all passed",
                     "RUNNER orca term_7 worker", "NOT_READY: branch is main"):
            with self.subTest(body=body):
                self.assertEqual(events.parse(body), ("none", None))
        state = events.fold(["ALL MET", "RUNNER orca term_7 worker"])
        self.assertEqual((state["events"], state["passed"], state["sessions"]), ([], False, []))


class Ordering(unittest.TestCase):
    """Replay is in comment-id order: two comments of one second carry one timestamp."""

    def test_comments_given_out_of_order_are_replayed_by_id(self):
        # The worker claimed within the second the start was written; the tracker's
        # listing here happens to put the claim first.
        claim = ev("ticket.claimed", "Claimed #61", login="bot")
        state = events.fold([comment(102, claim), comment(101, started())])
        self.assertEqual([e["event"] for e in state["events"]],
                         ["worker.started", "ticket.claimed"])
        self.assertEqual([e["comment"] for e in state["events"]], [101, 102])

    def test_the_order_decides_what_the_fold_reads_last(self):
        start, landing = started(), ev("ticket.landed", "Landed issue-61")
        after = events.fold([comment(5, start), comment(6, landing)])
        before = events.fold([comment(6, start), comment(5, landing)])
        self.assertFalse(after["held"])
        self.assertTrue(before["held"])

    def test_comments_with_no_ids_are_replayed_in_the_order_given(self):
        state = events.fold([started(), ev("ticket.landed", "Landed")])
        self.assertFalse(state["held"])

    def test_an_edited_comment_is_read_as_its_newest_version(self):
        """One id handed in twice — an incremental read after an edit — is one comment."""
        claim = ev("ticket.claimed", "Claimed")
        release = ev("ticket.released", "Released", reason="worker-lost")
        edited = [
            {"id": 5, "body": claim, "updated_at": "2026-09-10T02:00:00Z"},
            {"id": 6, "body": "a note", "updated_at": "2026-09-10T02:01:00Z"},
            {"id": 5, "body": release, "updated_at": "2026-09-10T02:05:00Z"},
        ]
        state = events.fold(edited)
        self.assertEqual([e["event"] for e in state["events"]], ["ticket.released"])
        self.assertEqual(events.fold(list(reversed(edited)))["events"], state["events"])


class Replays(unittest.TestCase):
    """State goes backwards, and a full replay needs no inverse for any of it."""

    def test_a_start_is_live_until_something_closes_it(self):
        state = events.fold([started()])
        self.assertTrue(state["held"])
        self.assertEqual(state["worker"]["session"], "term_7")
        self.assertEqual(state["worker"]["runner"], "orca")
        self.assertEqual(state["worker"]["worktree"], "/repo/.worktrees/issue-61")

    def test_a_retracted_start_is_closed_and_a_new_start_is_live(self):
        state = events.fold([
            started("term_7"),
            ev("worker.retracted", "Retracted", session="term_7", runner="orca"),
            started("term_9")])
        self.assertEqual([r["session"] for r in state["live_workers"]], ["term_9"])
        self.assertEqual(state["sessions"][0]["ended_by"], "worker.retracted")

    def test_a_release_closes_the_worker_and_the_claim(self):
        state = events.fold([
            started(), ev("ticket.claimed", "Claimed", login="bot"),
            ev("ticket.released", "Released", reason="suspended")])
        self.assertFalse(state["held"])
        self.assertFalse(state["claimed"])
        self.assertEqual(state["released"], "suspended")

    def test_a_suspended_night_closes_the_worker_and_the_next_start_reopens(self):
        state = events.fold([started("term_7"), ev("spec.suspended", "NIGHT SUSPENDED #76"),
                             started("term_8")])
        self.assertEqual([r["session"] for r in state["live_workers"]], ["term_8"])
        self.assertFalse(state["suspended"])

    def test_a_regression_takes_back_the_pass_and_the_landing(self):
        state = events.fold([
            started(), ev("ticket.passed", "ALL MET"), ev("ticket.landed", "Landed"),
            ev("ticket.regressed", "Reverify failed", commit="a" * 40, failed=["AC3"])])
        self.assertEqual((state["passed"], state["landed"], state["regressed"]),
                         (False, False, True))
        self.assertIsNone(state["outcome"])

    def test_passing_again_after_a_regression_is_a_pass_that_has_not_landed(self):
        state = events.fold([
            ev("ticket.passed", "ALL MET"), ev("ticket.landed", "Landed"),
            ev("ticket.regressed", "failed", commit="a" * 40), ev("ticket.passed", "ALL MET")])
        self.assertEqual((state["passed"], state["landed"]), (True, False))

    def test_a_lost_worker_closes_only_the_session_it_names(self):
        state = events.fold([started("term_7"), started("term_8"),
                             ev("worker.lost", "lost", session="term_7", runner="orca")])
        self.assertEqual([r["session"] for r in state["live_workers"]], ["term_8"])

    def test_a_session_is_closed_by_its_pair_never_by_its_id_alone(self):
        """Two runners hand out ids of their own; `term_7` on herdr is not `term_7` on orca."""
        state = events.fold([started("term_7", runner="orca"),
                             ev("worker.lost", "lost", session="term_7", runner="herdr")])
        self.assertTrue(state["held"])
        self.assertEqual([r["runner"] for r in state["live_workers"]], ["orca"])

    def test_a_replacement_closes_the_old_pair_and_the_new_session_is_its_own_start(self):
        replaced = ev("worker.replaced", "replaced", session="term_7", runner="orca")
        state = events.fold([started("term_7"), replaced])
        self.assertEqual(state["sessions"][0]["ended_by"], "worker.replaced")
        self.assertFalse(state["held"])
        state = events.fold([started("term_7"), replaced, started("term_8")])
        self.assertEqual([r["session"] for r in state["live_workers"]], ["term_8"])
        self.assertEqual(state["live_workers"][0]["comment"], 3)

    def test_a_pass_after_a_landing_is_new_work_not_yet_landed(self):
        state = events.fold([ev("ticket.passed", "ALL MET"), ev("ticket.landed", "Landed"),
                             ev("ticket.passed", "ALL MET again")])
        self.assertEqual((state["passed"], state["landed"]), (True, False))

    def test_a_claim_alone_holds_the_ticket(self):
        """A worker that claimed before its start was recorded, or with none recorded."""
        state = events.fold([ev("ticket.claimed", "Claimed", login="bot")])
        self.assertTrue(state["held"])
        self.assertFalse(state["hold_ended"])

    def test_a_claim_before_its_start_is_that_session_s_and_a_retraction_ends_both(self):
        state = events.fold([ev("ticket.claimed", "Claimed"), started("term_7"),
                             ev("worker.retracted", "retracted", session="term_7",
                                runner="orca")])
        self.assertFalse(state["held"])
        self.assertTrue(state["hold_ended"])

    def test_a_pass_does_not_end_the_hold(self):
        """The close after a pass can fail; the ticket stays open and its worker retries."""
        state = events.fold([started(), ev("ticket.claimed", "Claimed"),
                             ev("ticket.passed", "ALL MET")])
        self.assertTrue(state["held"])
        self.assertFalse(state["hold_ended"])

    def test_a_ticket_never_held_has_no_ended_hold(self):
        self.assertFalse(events.fold([ev("worker.decided", "DECISIONS")])["hold_ended"])

    def test_the_workers_own_result_ends_its_hold_and_a_resume_brings_it_back(self):
        state = events.fold([started(), ev("ticket.returned", "HANDOFF REQUIRED: 1 abandoned")])
        self.assertFalse(state["held"])
        state = events.fold([started(), ev("ticket.returned", "HANDOFF REQUIRED: 1 abandoned"),
                             ev("worker.resumed", "Resumed", session="term_7", runner="orca")])
        self.assertTrue(state["held"])

    def test_a_landing_ends_every_session_of_every_kind(self):
        state = events.fold([started(), started("rev_1", kind="reviewer"),
                             started("ver_1", kind="verifier"),
                             ev("ticket.landed", "Landed")])
        self.assertEqual([r["live"] for r in state["sessions"]], [False, False, False])

    def test_each_kind_has_its_newest_result(self):
        state = events.fold([
            started(), ev("reviewer.reported", "REVIEW a..b", base="a", head="b"),
            ev("verifier.failed", "VERDICT", commit="b" * 40),
            ev("verifier.passed", "VERDICT again", commit="c" * 40)])
        self.assertEqual(state["results"]["reviewer"]["line"], "REVIEW a..b")
        self.assertEqual(state["results"]["verifier"]["event"], "verifier.passed")
        self.assertIsNone(state["results"]["worker"])
        self.assertEqual(state["verdict"]["payload"]["commit"], "c" * 40)

    def test_children_carry_their_kind_and_their_resolution(self):
        state = events.fold([
            ev("child.opened", "Opened #90 (review)", child=90, kind="review"),
            ev("child.closed", "#90 became #80", child=90, resolution="became-ticket",
               became=80)])
        self.assertEqual(state["children"]["90"]["kind"], "review")
        self.assertEqual(state["children"]["90"]["resolution"], "became-ticket")

    def test_a_late_comment_is_replayed_in_its_place_not_applied_last(self):
        """Released, claimed again, then passed, landed and regressed — with the second
        claim arriving on a later page. Applied as it arrived, that claim would hold a
        ticket the landing had already let go of; replayed by id from empty, it does not."""
        pages = [
            comment(1, ev("ticket.claimed", "Claimed")),
            comment(2, ev("ticket.released", "Released", reason="worker-lost")),
            comment(4, ev("ticket.passed", "ALL MET")),
            comment(5, ev("ticket.landed", "Landed")),
            comment(6, ev("ticket.regressed", "Reverify failed", commit="a" * 40)),
            comment(3, ev("ticket.claimed", "Claimed again")),
        ]
        state = events.fold(pages)
        self.assertEqual((state["held"], state["passed"], state["landed"], state["regressed"]),
                         (False, False, False, True))
        self.assertEqual([e["comment"] for e in state["events"]], [1, 2, 3, 4, 5, 6])


class Unreadable(unittest.TestCase):
    """A block that cannot be read is reported, never read as no event (ADR 0008)."""

    def assertUnreadable(self, body, reason_part):
        state = events.fold([comment(7, started()), comment(8, body)])
        self.assertEqual(len(state["unreadable"]), 1, state["unreadable"])
        item = state["unreadable"][0]
        self.assertEqual(item["comment"], 8)
        self.assertIn(reason_part, item["reason"])
        # The readable events around it still fold.
        self.assertTrue(state["held"])

    def test_a_block_that_is_not_json(self):
        self.assertUnreadable("x\n\n<!-- mmw {not json} -->", "not JSON")

    def test_a_block_that_is_never_closed(self):
        self.assertUnreadable("x\n\n<!-- mmw {\"v\":1", "never closed")

    def test_a_block_of_another_version(self):
        self.assertUnreadable('x\n\n<!-- mmw {"v":2,"event":"ticket.claimed"} -->', "version")

    def test_a_block_naming_no_event_of_this_pipeline(self):
        self.assertUnreadable('x\n\n<!-- mmw {"v":1,"event":"worker.failover"} -->',
                              "not an event")

    def test_a_block_missing_a_field_its_event_requires(self):
        self.assertUnreadable('x\n\n<!-- mmw {"v":1,"event":"worker.started"} -->', "session")

    def test_two_blocks_in_one_comment(self):
        body = started() + "\n" + ev("ticket.claimed", "again")
        self.assertUnreadable(body, "one comment is one event")


class CommandLine(unittest.TestCase):
    """`events.py` for the bash callers: emit a body, and read the fold back."""

    def run_cli(self, *args, stdin=""):
        out = subprocess.run([sys.executable, str(EVENTS), *args], input=stdin,
                             capture_output=True, text=True)
        return out.returncode, out.stdout, out.stderr

    def test_emit_prints_a_body_that_parses_to_the_event_asked_for(self):
        code, out, err = self.run_cli(
            "emit", "worker.started", "--ticket", "61", "--spec", "76",
            "--line", "worker started on orca: session term_7",
            "--field", "session=term_7", "--field", "runner=orca", "--field", "host=grok",
            "--field", "model=m", "--field", "effort=high", "--field", "grade=junior-worker",
            "--field", "worktree=/repo/.worktrees/issue-61", "--field", "branch=issue-61",
            "--field", "base=" + "0" * 40, "--field", "note=", "--json-field", "slot=2")
        self.assertEqual(code, 0, err)
        what, payload = events.parse(out)
        self.assertEqual(what, "event")
        self.assertEqual((payload["event"], payload["ticket"], payload["spec"],
                          payload["session"], payload["slot"]),
                         ("worker.started", 61, 76, "term_7", 2))
        self.assertNotIn("note", payload)

    def test_emit_refuses_an_event_the_table_refuses(self):
        code, out, err = self.run_cli("emit", "worker.started", "--ticket", "61",
                                      "--line", "x", "--field", "runner=orca")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("session", err)

    def test_the_readers_answer_from_a_comments_file(self):
        data = json.dumps({"comments": [
            comment(1, started("term_7")),
            comment(2, started("rev_1", kind="reviewer")),
            comment(3, ev("reviewer.reported", "REVIEW a..b", base="a", head="b")),
            comment(4, ev("verifier.failed", "VERDICT", commit="c" * 40, failed=["AC2"],
                          ran=True))]})
        code, out, err = self.run_cli("session", "61", "--kind", "worker",
                                      "--comments-file", "-", stdin=data)
        self.assertEqual((code, out, err), (0, "orca\tterm_7\n", ""))
        code, out, _ = self.run_cli("sessions", "61", "--comments-file", "-", stdin=data)
        self.assertEqual(out, "orca\tterm_7\norca\trev_1\n")
        code, out, _ = self.run_cli("result", "61", "--kind", "worker",
                                    "--comments-file", "-", stdin=data)
        self.assertEqual(out, "")

    def test_result_prints_the_event_and_its_key_fields_never_its_prose(self):
        data = json.dumps({"comments": [
            comment(1, ev("reviewer.reported", "REVIEW a..b", base="a", head="b")),
            comment(2, ev("verifier.failed", "VERDICT … all passed", commit="c" * 40,
                          failed=["AC2", "AC3"], ran=True)),
            comment(3, ev("ticket.passed", "ALL MET", commit="d" * 40))]})
        for kind, want in (("reviewer", "reviewer.reported base=a head=b"),
                           ("verifier", f"verifier.failed commit={'c' * 40} failed=AC2,AC3 ran=true"),
                           ("worker", f"ticket.passed commit={'d' * 40}")):
            with self.subTest(kind=kind):
                code, out, _ = self.run_cli("result", "61", "--kind", kind,
                                            "--comments-file", "-", stdin=data)
                self.assertEqual((code, out), (0, want + "\n"))

    def test_an_unreadable_block_is_no_answer_from_any_reader(self):
        """A caller about to archive, send or wait must not get half a ticket."""
        data = json.dumps({"comments": [
            comment(1, started("term_7")),
            comment(2, ev("reviewer.reported", "REVIEW a..b", base="a", head="b")),
            comment(4, "x\n\n<!-- mmw {bad} -->")]})
        for args in (("session", "--kind", "worker"), ("sessions",),
                     ("result", "--kind", "reviewer")):
            with self.subTest(args=args):
                code, out, err = self.run_cli(args[0], "61", *args[1:],
                                              "--comments-file", "-", stdin=data)
                self.assertEqual((code, out), (3, ""))
                self.assertIn("comment 4", err)
        code, out, _ = self.run_cli("fold", "61", "--comments-file", "-", stdin=data)
        self.assertEqual(len(json.loads(out)["unreadable"]), 1)

    def test_comments_that_cannot_be_read_are_exit_2_not_an_empty_ticket(self):
        code, out, err = self.run_cli("session", "61", "--comments-file", "-",
                                      stdin="not json")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("not JSON", err)


if __name__ == "__main__":
    unittest.main()
