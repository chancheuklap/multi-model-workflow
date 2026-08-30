"""Tests for board.py against fixed samples: no tracker, no Herdr, no clock.

The two sources board.py reads are a Herdr snapshot and a set of tickets, so the
samples here are one of each, in the shape the real calls return them. Everything the
board decides is a function of those two, which is why none of it needs a terminal.

    python3 -m unittest discover -s mmw-v2/skills/dispatch/tests
"""

from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime
from pathlib import Path

BOARD_PATH = Path(__file__).resolve().parent.parent / "scripts" / "board.py"
_spec = importlib.util.spec_from_file_location("board", BOARD_PATH)
board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(board)


def agent(name, pane, status, **tokens):
    """One entry of `herdr api snapshot`'s `agents`, with only the fields read."""
    return {
        "name": name,
        "pane_id": pane,
        "agent_status": status,
        "focused": False,
        "cwd": "/repo",
        "agent_session": {"value": "session-" + pane},
        "tokens": {k: str(v) for k, v in tokens.items()},
    }


def ticket(number, state="OPEN", labels=("ready-for-agent",), blockers=(),
           assignees=(), comments=()):
    """One `gh issue view --json …` answer, before board.py normalises it."""
    return board.normalise_ticket(number, {
        "state": state,
        "title": f"ticket {number}",
        "labels": [{"name": l} for l in labels],
        "assignees": [{"login": a} for a in assignees],
        "blockedBy": {"nodes": [{"number": b, "state": "OPEN"} for b in blockers]},
        "comments": [{"body": c} for c in comments],
    })


SELF_RUN_UNMET = "\n".join([
    "self-run",
    "UNMET: 2 (met: 3)",
    "",
    "- [x] AC1: one",
    "  EVIDENCE: exit=0; EXPECT=matched",
    "- [ ] AC3: three",
    "  EVIDENCE: pending",
    "- [ ] AC5: five",
    "  EVIDENCE: pending",
    "",
    "Outside Owns: None",
])

SELF_RUN_ALL_MET = "\n".join([
    "self-run",
    "UNMET: 0 (met: 5)",
    "",
    "- [x] AC1: one",
    "  EVIDENCE: exit=0; EXPECT=matched",
    "",
    "Outside Owns: None",
])

VERDICT = ("VERDICT 1111111111111111111111111111111111111111 unit-test-verified "
           "by Sonnet 5 — every criterion passed.")


class Identity(unittest.TestCase):
    """Which ticket and role a live pane belongs to."""

    def test_tokens_name_the_ticket_and_the_role(self):
        found = board.session_of(agent("issue-61", "w1:p1", "working",
                                       ticket=61, role="worker", phase="implement"))
        self.assertEqual((found["ticket"], found["role"]), (61, "worker"))

    def test_a_pane_that_stopped_before_its_first_run_is_still_read_off_its_name(self):
        found = board.session_of(agent("issue-62", "w1:p2", "idle"))
        self.assertEqual((found["ticket"], found["role"], found["phase"]), (62, "worker", ""))

    def test_the_reviewer_is_told_apart_from_the_worker(self):
        found = board.session_of(agent("issue-61-review", "w1:p3", "working"))
        self.assertEqual(found["role"], "reviewer")

    def test_a_pane_of_someone_elses_is_not_ours(self):
        self.assertIsNone(board.session_of(agent("scratch", "w1:p9", "idle")))

    def test_a_stale_token_on_an_unnamed_pane_is_shown_but_not_held(self):
        found = board.session_of(agent(None, "w1:p9", "idle", ticket=102, role="worker",
                                       phase="handoff"))
        self.assertEqual(found["ticket"], 102)
        self.assertFalse(found["dispatched"])

    def test_the_dispatchers_own_name_is_what_makes_a_session_held(self):
        found = board.session_of(agent("issue-61", "w1:p1", "working",
                                       ticket=61, role="worker"))
        self.assertTrue(found["dispatched"])


class Rows(unittest.TestCase):
    """The table's own contents, joined from the two sources."""

    def rows(self):
        agents = [
            agent("issue-61", "w1:p1", "working", ticket=61, role="worker",
                  phase="implement"),
            agent("issue-62", "w1:p2", "idle", ticket=62, role="worker",
                  phase="selfcheck", ac="3/5", wake=1),
            agent("issue-63", "w1:p3", "blocked", ticket=63, role="worker",
                  phase="verify", ac="5/5"),
        ]
        tickets = {
            61: ticket(61),
            62: ticket(62, comments=[SELF_RUN_UNMET]),
            63: ticket(63, comments=[SELF_RUN_UNMET]),
            64: ticket(64, state="CLOSED", labels=(),
                       comments=[SELF_RUN_ALL_MET, "ALL MET\nBranch: issue-64"]),
            65: ticket(65, blockers=(62,)),
        }
        return board.build_rows(list(tickets), tickets, board.sessions(agents))

    def row(self, number):
        return next(r for r in self.rows() if r["ticket"] == number)

    def test_a_working_session_shows_its_phase_and_no_note(self):
        row = self.row(61)
        self.assertEqual((row["agent"], row["status"], row["phase"], row["note"]),
                         ("issue-61", "working", "implement", ""))

    def test_a_settled_session_short_of_the_end_is_stalled_and_counts_its_prompts(self):
        row = self.row(62)
        self.assertEqual(row["ac"], "3/5")
        self.assertEqual(row["wake"], "1")
        self.assertEqual(row["note"], "stalled, prompted 1 of 3")

    def test_a_blocked_session_says_the_question_is_on_the_ticket(self):
        self.assertEqual(self.row(63)["note"], "QUESTION commented")

    def test_a_closed_ticket_keeps_its_counts_and_says_its_pane_is_gone(self):
        row = self.row(64)
        self.assertEqual((row["agent"], row["phase"], row["ac"]), ("-", "closed", "5/5"))
        self.assertEqual(row["note"], "ALL MET, pane closed")

    def test_a_blocked_ticket_names_what_it_waits_on(self):
        self.assertEqual(self.row(65)["note"], "waiting on #62")

    def test_the_frontier_leaves_out_what_is_held_claimed_blocked_or_done(self):
        self.assertEqual([r["ticket"] for r in board.frontier(self.rows())], [])

    def test_only_the_dispatchers_own_sessions_count_against_the_parallel_cap(self):
        agents = [agent("issue-61", "w1:p1", "working", ticket=61, role="worker"),
                  agent(None, "w1:p9", "idle", ticket=63, role="worker", phase="handoff")]
        tickets = {61: ticket(61), 63: ticket(63)}
        rows = board.build_rows(list(tickets), tickets, board.sessions(agents))
        self.assertEqual([r["ticket"] for r in board.held(rows)], [61])

    def test_the_frontier_takes_a_ready_ticket_with_no_session_and_no_blocker(self):
        tickets = {70: ticket(70), 71: ticket(71, assignees=("someone",)),
                   72: ticket(72, labels=("needs-triage",))}
        rows = board.build_rows(list(tickets), tickets, [])
        self.assertEqual([r["ticket"] for r in board.frontier(rows)], [70])


class Stalled(unittest.TestCase):
    """`idle`/`done` with a phase short of either exit is the one machine-made call."""

    def test_settled_short_of_the_end(self):
        for status in ("idle", "done"):
            self.assertTrue(board.stalled(board.session_of(
                agent("issue-62", "w1:p2", status, ticket=62, role="worker",
                      phase="selfcheck"))))

    def test_settled_at_the_end_is_not_stalled(self):
        for phase in ("closed", "handoff"):
            self.assertFalse(board.stalled(board.session_of(
                agent("issue-62", "w1:p2", "idle", ticket=62, role="worker",
                      phase=phase))))

    def test_working_is_never_stalled(self):
        self.assertFalse(board.stalled(board.session_of(
            agent("issue-62", "w1:p2", "working", ticket=62, role="worker",
                  phase="selfcheck"))))


class TicketReading(unittest.TestCase):
    """The few fields read out of a ticket's comments."""

    def test_the_counts_come_off_the_newest_self_run(self):
        self.assertEqual(board.counted_ac(ticket(62, comments=[SELF_RUN_UNMET])), "3/5")
        self.assertEqual(board.counted_ac(ticket(62, comments=[SELF_RUN_ALL_MET])), "5/5")

    def test_a_ticket_with_no_run_has_no_counts(self):
        self.assertEqual(board.counted_ac(ticket(62)), "-")

    def test_the_unmet_criteria_are_read_in_ticket_order(self):
        self.assertEqual(board.unmet_criteria(SELF_RUN_UNMET), ["AC3", "AC5"])
        self.assertEqual(board.unmet_criteria(SELF_RUN_ALL_MET), [])

    def test_the_newest_comment_of_a_kind_wins(self):
        found = board.newest_with_first_line(
            ticket(62, comments=[SELF_RUN_UNMET, VERDICT, SELF_RUN_ALL_MET]),
            "self-run", "reverify")
        self.assertEqual(board.first_line(found), "self-run")
        self.assertEqual(board.unmet_criteria(found), [])


class Table(unittest.TestCase):
    """The one screen `--once` prints."""

    def table(self, spec=60):
        agents = [agent("issue-61", "w1:p1", "working", ticket=61, role="worker",
                        phase="implement")]
        tickets = {61: ticket(61), 65: ticket(65, blockers=(61,))}
        rows = board.build_rows(list(tickets), tickets, board.sessions(agents))
        return board.render_table(rows, spec, datetime(2026, 8, 31, 2, 14))

    def test_the_first_line_names_the_time_the_spec_the_count_and_the_parallel_cap(self):
        self.assertEqual(self.table().splitlines()[0],
                         "mmw board · 02:14 · spec #60 · 2 tickets · parallel 1/2")

    def test_without_a_spec_the_first_line_leaves_that_field_out(self):
        self.assertEqual(self.table(spec=None).splitlines()[0],
                         "mmw board · 02:14 · 2 tickets · parallel 1/2")

    def test_the_columns_are_the_fixed_seven(self):
        self.assertEqual(self.table().splitlines()[2].split(),
                         ["ticket", "agent", "status", "phase", "ac", "wake", "note"])

    def test_one_line_per_ticket_in_ticket_order(self):
        body = self.table().splitlines()[3:]
        self.assertEqual([l.split()[0] for l in body], ["#61", "#65"])
        self.assertIn("issue-61", body[0])
        self.assertIn("waiting on #61", body[1])


class Constants(unittest.TestCase):
    """Every number the night runs on is here, and nowhere else."""

    def test_the_numbers_are_the_ones_the_plan_settled(self):
        self.assertEqual(
            (board.PARALLEL, board.COOLDOWN_SECONDS, board.WAKE_BACKOFF,
             board.WAKE_LIMIT, board.REDISPATCH_LIMIT, board.MAX_HOURS,
             board.SNAPSHOT_INTERVAL),
            (2, 120, (120, 240, 480), 3, 1, 4, 60))


if __name__ == "__main__":
    unittest.main()
