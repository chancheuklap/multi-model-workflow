"""Tests for board.py against fixed samples: no tracker, no Herdr, no clock.

The two sources board.py reads are a Herdr snapshot and a set of tickets, so the
samples here are one of each, in the shape the real calls return them. Everything the
board decides is a function of those two, which is why none of it needs a terminal.

    python3 -m unittest discover -s mmw-v2/skills/dispatch/tests
"""

from __future__ import annotations

import importlib.util
import io
import os
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

BOARD_PATH = Path(__file__).resolve().parent.parent / "scripts" / "board.py"
_spec = importlib.util.spec_from_file_location("board", BOARD_PATH)
board = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(board)


def agent(name, pane, status, host="claude", **tokens):
    """One entry of `herdr api snapshot`'s `agents`, with only the fields read."""
    return {
        "name": name,
        "agent": host,
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
    "ALL MET (5 met)",
    "",
    "- [x] AC1: one",
    "  EVIDENCE: exit=0; EXPECT=matched",
    "",
    "Outside Owns: None",
])

SELF_RUN_HANDOFF = "\n".join([
    "self-run",
    "HANDOFF REQUIRED: 1 abandoned (met: 3, unmet: 1)",
    "  AC4: no credential for the staging account on this machine",
    "",
    "- [x] AC1: one",
    "  EVIDENCE: exit=0; EXPECT=matched",
    "",
    "Outside Owns: None",
])

VERDICT = ("VERDICT 1111111111111111111111111111111111111111 by Sonnet 5 — "
           "commands only; all passed; nothing repaired.")


class Identity(unittest.TestCase):
    """Which ticket and kind a live pane belongs to."""

    def test_tokens_name_the_ticket_and_the_kind(self):
        found = board.session_of(agent("issue-61", "w1:p1", "working",
                                       ticket=61, kind="worker", phase="implement"))
        self.assertEqual((found["ticket"], found["kind"]), (61, "worker"))

    def test_a_pane_with_no_token_yet_is_still_read_off_its_name(self):
        found = board.session_of(agent("issue-62", "w1:p2", "idle"))
        self.assertEqual((found["ticket"], found["kind"], found["phase"]), (62, "worker", ""))

    def test_the_reviewer_is_told_apart_from_the_worker(self):
        found = board.session_of(agent("issue-61-review", "w1:p3", "working"))
        self.assertEqual(found["kind"], "reviewer")

    def test_a_pane_of_someone_elses_is_not_ours(self):
        self.assertIsNone(board.session_of(agent("scratch", "w1:p9", "idle")))

    def test_a_stale_token_on_an_unnamed_pane_is_shown_but_not_held(self):
        found = board.session_of(agent(None, "w1:p9", "idle", ticket=102, kind="worker",
                                       phase="handoff"))
        self.assertEqual(found["ticket"], 102)
        self.assertFalse(found["dispatched"])

    def test_the_dispatchers_own_name_is_what_makes_a_session_held(self):
        found = board.session_of(agent("issue-61", "w1:p1", "working",
                                       ticket=61, kind="worker"))
        self.assertTrue(found["dispatched"])


class Rows(unittest.TestCase):
    """The table's own contents, joined from the two sources."""

    def rows(self):
        agents = [
            agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                  phase="implement"),
            agent("issue-62", "w1:p2", "idle", ticket=62, kind="worker",
                  phase="selfcheck", ac="3/5", wake=1),
            agent("issue-63", "w1:p3", "blocked", ticket=63, kind="worker",
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

    def test_an_idle_session_short_of_closed_or_handoff_counts_its_re_prompts(self):
        row = self.row(62)
        self.assertEqual(row["ac"], "3/5")
        self.assertEqual(row["wake"], "1")
        self.assertEqual(row["note"], "re-prompted 1 of 3")

    def test_a_blocked_session_says_the_form_is_on_the_ticket(self):
        self.assertEqual(self.row(63)["note"], "BLOCKED: commented, form dismissed")

    def test_a_closed_ticket_keeps_its_counts_and_says_its_pane_is_gone(self):
        row = self.row(64)
        self.assertEqual((row["agent"], row["phase"], row["ac"]), ("-", "closed", "5/5"))
        self.assertEqual(row["note"], "ALL MET, pane closed")

    def test_a_blocked_ticket_names_what_it_waits_on(self):
        self.assertEqual(self.row(65)["note"], "waiting on #62")

    def test_the_frontier_leaves_out_what_is_held_claimed_or_blocked(self):
        self.assertEqual([r["ticket"] for r in board.frontier(self.rows())], [])

    def test_only_the_dispatchers_own_sessions_count_against_the_parallel_cap(self):
        agents = [agent("issue-61", "w1:p1", "working", ticket=61, kind="worker"),
                  agent(None, "w1:p9", "idle", ticket=63, kind="worker", phase="handoff")]
        tickets = {61: ticket(61), 63: ticket(63)}
        rows = board.build_rows(list(tickets), tickets, board.sessions(agents))
        self.assertEqual([r["ticket"] for r in board.held(rows)], [61])

    def test_the_frontier_takes_a_ready_ticket_with_no_session_and_no_blocker(self):
        tickets = {70: ticket(70), 71: ticket(71, assignees=("someone",)),
                   72: ticket(72, labels=("needs-triage",))}
        rows = board.build_rows(list(tickets), tickets, [])
        self.assertEqual([r["ticket"] for r in board.frontier(rows)], [70])


class IdleAndNotClosedOrHandoff(unittest.TestCase):
    """The one judgement board.py makes about a session, from two machine-read facts."""

    def test_idle_or_done_with_any_other_phase(self):
        for status in ("idle", "done"):
            for phase in ("", "implement", "selfcheck", "verify", "closeout-rejected"):
                self.assertTrue(board.idle_and_not_closed_or_handoff(board.session_of(
                    agent("issue-62", "w1:p2", status, ticket=62, kind="worker",
                          phase=phase))))

    def test_closed_or_handoff_is_not(self):
        for phase in ("closed", "handoff"):
            self.assertFalse(board.idle_and_not_closed_or_handoff(board.session_of(
                agent("issue-62", "w1:p2", "idle", ticket=62, kind="worker",
                      phase=phase))))

    def test_working_is_not(self):
        self.assertFalse(board.idle_and_not_closed_or_handoff(board.session_of(
            agent("issue-62", "w1:p2", "working", ticket=62, kind="worker",
                  phase="selfcheck"))))


class TicketReading(unittest.TestCase):
    """The few fields read out of a ticket's comments."""

    def test_the_counts_come_off_the_newest_self_run(self):
        self.assertEqual(board.counted_ac(ticket(62, comments=[SELF_RUN_UNMET])), "3/5")
        self.assertEqual(board.counted_ac(ticket(62, comments=[SELF_RUN_ALL_MET])), "5/5")

    def test_a_handoff_summary_line_counts_the_abandoned_criteria_too(self):
        self.assertEqual(board.counted_ac(ticket(62, comments=[SELF_RUN_HANDOFF])), "3/5")

    def test_a_summary_line_carrying_a_reverify_count_or_a_scope_still_counts(self):
        for line, counted in (
                ("ALL MET (5 met, reran: 5, previously met reverified: 5) [scope api]",
                 "5/5"),
                ("UNMET: 2 (met: 3, abandoned: 0, reran: 5) [scope api]", "3/5"),
                ("HANDOFF REQUIRED: 2 abandoned (met: 3, unmet: 1, reran: 6)", "3/6")):
            with self.subTest(line=line):
                self.assertEqual(
                    board.counted_ac(ticket(62, comments=["self-run\n" + line])), counted)

    def test_a_ticket_with_no_run_has_no_counts(self):
        self.assertEqual(board.counted_ac(ticket(62)), "-")

    def test_the_newest_comment_of_a_kind_wins(self):
        found = board.newest_with_first_line(
            ticket(62, comments=[SELF_RUN_UNMET, VERDICT, SELF_RUN_ALL_MET]),
            "self-run", "reverify")
        self.assertEqual(board.first_line(found), "self-run")
        self.assertEqual(board.counted_ac(ticket(62, comments=[SELF_RUN_UNMET, VERDICT,
                                                              SELF_RUN_ALL_MET])), "5/5")


class ThePrompt(unittest.TestCase):
    """The only thing board.py ever says to a worker."""

    def test_it_is_the_dispatch_line_and_nothing_else(self):
        self.assertEqual(board.DISPATCH_LINE.format(n=62), "implement #62")


class Table(unittest.TestCase):
    """The one screen `--once` prints."""

    def table(self, spec=60):
        agents = [agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                        phase="implement")]
        tickets = {61: ticket(61), 65: ticket(65, blockers=(61,))}
        rows = board.build_rows(list(tickets), tickets, board.sessions(agents))
        return board.render_table(rows, spec, datetime(2026, 8, 31, 2, 14))

    def test_the_first_line_names_the_time_the_spec_the_count_and_the_parallel_cap(self):
        self.assertEqual(self.table().splitlines()[0],
                         "mmw board · 02:14 · spec #60 · 2 tickets · PARALLEL 1/2")

    def test_without_a_spec_the_first_line_leaves_that_field_out(self):
        self.assertEqual(self.table(spec=None).splitlines()[0],
                         "mmw board · 02:14 · 2 tickets · PARALLEL 1/2")

    def test_the_columns_are_the_fixed_seven(self):
        self.assertEqual(self.table().splitlines()[2].split(),
                         ["ticket", "agent", "agent_status", "phase", "ac",
                          "wake", "note"])

    def test_one_line_per_ticket_in_ticket_order(self):
        body = self.table().splitlines()[3:]
        self.assertEqual([l.split()[0] for l in body], ["#61", "#65"])
        self.assertIn("issue-61", body[0])
        self.assertIn("waiting on #61", body[1])


class Clock:
    """A monotonic clock the test moves by hand, so cooldowns cost no wall time."""

    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def tick(self, seconds):
        self.now += seconds


class Table4(unittest.TestCase):
    """The lookup table: what board.py does about each thing it can see.

    Nothing here reaches Herdr or the tracker. Every call board.py would make to
    either is replaced by a recorder, so the test reads the decisions themselves.
    """

    def setUp(self):
        self.calls = {"herdr": [], "gh": [], "prompt": [], "dispatch": [],
                      "main": []}
        self.clock = Clock()
        self.saved = {name: getattr(board, name) for name in
                      ("herdr", "gh", "herdr_run", "herdr_text", "run_dispatch",
                       "read_ticket", "collect", "live_agents", "time")}
        self.screen = ("Which colour do you prefer?\n"
                       "1. red\n2. blue\nEnter to select · Esc to cancel")
        self.main = [agent(board.MAIN, "w1:pMain", "idle")]
        self.tickets = {}
        self.rows = []

        def fake_herdr(args):
            self.calls["herdr"].append(list(args))
            if args[:2] == ["agent", "send-keys"]:
                # Dismissing the form is what takes the session out of `blocked`.
                for a in self.agents:
                    if a["pane_id"] == args[2]:
                        a["agent_status"] = "idle"
            if args[:2] == ["agent", "get"]:
                pane = args[2]
                agent_ = next((a for a in self.agents if a["pane_id"] == pane), {})
                return {"result": {"agent": agent_}}
            return {"result": {}}

        def fake_gh(args):
            self.calls["gh"].append(list(args))
            return ""

        def fake_prompt(args):
            if args[:2] == ["agent", "prompt"]:
                where = "main" if args[2] == board.MAIN else "prompt"
                self.calls[where].append((args[2], args[3]))
            return (0, "")

        def fake_dispatch(number, role):
            self.calls["dispatch"].append((number, role))
            return (self.dispatch_code, f"issue-{number} is working on #{number}",
                    "the reason")

        def fake_text(args):
            self.calls["herdr"].append(list(args))
            return self.screen

        self.dispatch_code = 0

        board.herdr = fake_herdr
        board.gh = fake_gh
        board.herdr_run = fake_prompt
        board.herdr_text = fake_text
        board.live_agents = lambda: list(self.main)
        board.run_dispatch = fake_dispatch
        board.read_ticket = lambda n: self.tickets[n]
        board.collect = lambda spec: (self.rows, [])
        board.time = self.clock
        os.environ.setdefault("HERDR_PANE_ID", "w1:pBoard")

    def tearDown(self):
        for name, value in self.saved.items():
            setattr(board, name, value)

    def world(self, agents, tickets):
        """Set the two sources for the rounds that follow."""
        self.agents = agents
        self.tickets = tickets
        self.rows = board.build_rows(list(tickets), tickets, board.sessions(agents))

    def watch(self, parallel=2, max_hours=4):
        return board.Watch(76, "junior-worker", parallel, max_hours)

    def round(self, watch):
        with redirect_stdout(io.StringIO()) as out:
            watch.round()
        return out.getvalue()

    # ------------------------------------------------------------- working

    def test_a_working_session_is_left_alone(self):
        self.world([agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                          phase="implement")], {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(self.calls["gh"], [])
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    # ------------------------------------------------------------- at the end

    def test_a_session_whose_phase_is_closed_or_handoff_has_its_pane_closed(self):
        for phase in ("closed", "handoff"):
            with self.subTest(phase=phase):
                self.calls["herdr"].clear()
                self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                                  phase=phase)],
                           {61: ticket(61, state="CLOSED", labels=())})
                printed = self.round(self.watch())
                self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])
                self.assertIn("#61", printed)
                self.assertEqual(self.calls["prompt"], [])

    # ------------------------------ idle, phase not closed and not handoff

    def idle_world(self, wake=0, phase="selfcheck", status="idle", **extra):
        self.world([agent("issue-61", "w1:p1", status, ticket=61, kind="worker",
                          phase=phase, ac="1/2", wake=wake, **extra)],
                   {61: ticket(61, assignees=("me",), comments=[SELF_RUN_UNMET])})

    def test_the_first_idle_round_only_starts_the_cooldown(self):
        self.idle_world()
        watch = self.watch()
        printed = self.round(watch)
        self.assertEqual(self.calls["prompt"], [])
        self.assertIn("COOLDOWN 120s", printed)

    def test_after_the_cooldown_it_is_sent_its_own_dispatch_line(self):
        self.idle_world()
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [("w1:p1", "implement #61")])

    def test_the_wait_before_each_prompt_grows(self):
        for wake, wait in enumerate(board.WAKE_BACKOFF):
            with self.subTest(wake=wake):
                self.calls["prompt"].clear()
                self.idle_world(wake=wake)
                watch = self.watch()
                self.round(watch)
                self.clock.tick(wait - 1)
                self.round(watch)
                self.assertEqual(self.calls["prompt"], [])
                self.clock.tick(1)
                self.round(watch)
                self.assertEqual(len(self.calls["prompt"]), 1)

    def test_the_count_of_prompts_is_written_on_the_pane(self):
        self.idle_world(wake=1)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.WAKE_BACKOFF[1])
        self.round(watch)
        self.assertIn(["pane", "report-metadata", "w1:p1", "--source", "mmw",
                       "--token", "wake=2", "--ttl-ms", "86400000"],
                      self.calls["herdr"])

    def test_at_the_third_prompt_the_ticket_goes_back_to_be_judged(self):
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertTrue(comment[-1].startswith("WAKEUP LIMIT:"))
        self.assertIn(["issue", "edit", "61", "--remove-label", "ready-for-agent",
                       "--add-label", "needs-triage"], self.calls["gh"])

    def test_a_token_that_has_not_come_round_yet_does_not_earn_a_second_prompt(self):
        self.idle_world()
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), 1)
        # The pane still reports wake=0: the write has not reached the snapshot.
        self.clock.tick(board.WAKE_BACKOFF[0])
        self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), 1)
        self.clock.tick(board.WAKE_BACKOFF[1] - board.WAKE_BACKOFF[0])
        self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), 2)

    def test_a_focused_pane_is_never_prompted(self):
        self.idle_world()
        self.agents[0]["focused"] = True
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])

    def test_a_pane_that_went_back_to_work_is_not_prompted(self):
        self.idle_world()
        watch = self.watch()
        self.round(watch)
        self.agents[0]["agent_status"] = "working"
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])

    def test_a_pane_holding_a_different_session_now_is_not_prompted(self):
        self.idle_world()
        watch = self.watch()
        self.round(watch)
        self.agents[0]["agent_session"] = {"value": "somebody-else"}
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])

    def test_a_reviewer_that_stops_is_left_to_its_workers_own_wait(self):
        self.world([agent("issue-61-review", "w1:p2", "idle", ticket=61,
                          kind="reviewer")], {61: ticket(61, assignees=("me",))})
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])
        self.assertNotIn(["pane", "close", "w1:p2"], self.calls["herdr"])

    # ------------------------------------------------------------- the time limit

    def test_a_ticket_that_held_a_session_too_long_goes_back_and_keeps_its_session(self):
        self.idle_world(phase="verify")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(4 * 3600 + 1)
        self.round(watch)
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertTrue(comment[-1].startswith(
            "TIME LIMIT: 4 h under this board, still at phase=verify"))
        self.assertIn(["issue", "edit", "61", "--remove-label", "ready-for-agent",
                       "--add-label", "needs-triage"], self.calls["gh"])
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    def test_a_session_whose_phase_is_closed_is_past_the_time_limit(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed")], {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        self.calls["gh"].clear()
        self.clock.tick(4 * 3600 + 1)
        self.round(watch)
        self.assertEqual([c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"]], [])

    # ------------------------------------------------------------- dispatching

    def test_the_frontier_is_dispatched_up_to_the_parallel_cap(self):
        self.world([], {70: ticket(70), 71: ticket(71), 72: ticket(72)})
        self.round(self.watch(parallel=2))
        self.assertEqual(self.calls["dispatch"],
                         [(70, "junior-worker"), (71, "junior-worker")])

    def test_a_live_session_takes_up_one_of_those_places(self):
        self.world([agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                          phase="implement")],
                   {61: ticket(61, assignees=("me",)), 70: ticket(70), 71: ticket(71)})
        self.round(self.watch(parallel=2))
        self.assertEqual(self.calls["dispatch"], [(70, "junior-worker")])

    def test_a_ticket_already_handed_back_is_not_started_again(self):
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.world([], {61: ticket(61)})
        self.round(watch)
        self.assertEqual(self.calls["dispatch"], [])

    def test_a_ticket_reaching_closed_frees_its_place_in_the_same_round(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed")],
                   {61: ticket(61, state="CLOSED", labels=()), 70: ticket(70)})
        self.round(self.watch(parallel=1))
        self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])
        self.assertEqual(self.calls["dispatch"], [(70, "junior-worker")])

    def test_a_ticket_handed_back_with_its_pane_closed_frees_its_place_too(self):
        self.idle_world(wake=board.WAKE_LIMIT)
        self.tickets[70] = ticket(70)
        self.rows = board.build_rows(list(self.tickets), self.tickets,
                                     board.sessions(self.agents))
        watch = self.watch(parallel=1)
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])
        self.assertEqual(self.calls["dispatch"], [(70, "junior-worker")])

    def test_a_ticket_over_its_time_limit_keeps_its_place_because_it_keeps_its_session(self):
        self.idle_world(phase="verify")
        self.tickets[70] = ticket(70)
        self.rows = board.build_rows(list(self.tickets), self.tickets,
                                     board.sessions(self.agents))
        watch = self.watch(parallel=1)
        self.round(watch)
        self.clock.tick(4 * 3600 + 1)
        self.round(watch)
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])
        self.assertEqual(self.calls["dispatch"], [])

    def test_the_last_session_reaching_closed_ends_the_night_in_the_same_round(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed")], {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        self.assertTrue(watch.summary_written)

    # ------------------------------------------------------------- blocked

    def blocked_world(self, host="grok", wake=0, comments=()):
        self.world([agent("issue-61", "w1:p1", "blocked", host=host, ticket=61,
                          kind="worker", phase="verify", wake=wake)],
                   {61: ticket(61, assignees=("me",), comments=list(comments))})

    def test_the_form_goes_on_the_ticket_under_BLOCKED(self):
        self.blocked_world()
        self.round(self.watch())
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertEqual(comment[2], "61")
        self.assertEqual(comment[-1],
                         "BLOCKED: Which colour do you prefer? 1. red 2. blue "
                         "Enter to select · Esc to cancel")

    def test_only_the_first_500_characters_of_the_form_are_quoted(self):
        self.blocked_world()
        self.screen = "x" * 900
        self.round(self.watch())
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertEqual(len(comment[-1]), len("BLOCKED: ") + board.FORM_CHARS)

    def test_what_scrolled_above_the_form_is_not_quoted(self):
        self.blocked_world()
        self.screen = ("an earlier turn\n" * 40) + "Do you prefer red or blue?\n1. red"
        self.round(self.watch())
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertTrue(comment[-1].endswith("Do you prefer red or blue? 1. red"))
        self.assertEqual(comment[-1].count("an earlier turn"), board.FORM_LINES - 2)

    def test_each_host_gets_its_own_key(self):
        for host, key in (("grok", "shift+x"), ("cursor", "esc"), ("claude", "esc")):
            with self.subTest(host=host):
                self.calls["herdr"].clear()
                self.blocked_world(host=host)
                self.round(self.watch())
                self.assertIn(["agent", "send-keys", "w1:p1", key], self.calls["herdr"])

    def test_the_form_is_never_answered_only_dismissed(self):
        self.blocked_world()
        self.round(self.watch())
        for call in self.calls["herdr"]:
            self.assertNotIn(call[0:2], (["pane", "send-text"], ["agent", "send-text"]))

    def test_after_the_form_it_is_sent_its_dispatch_line_and_the_count_goes_up(self):
        self.blocked_world()
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [("w1:p1", "implement #61")])
        self.assertIn(["pane", "report-metadata", "w1:p1", "--source", "mmw",
                       "--token", "wake=1", "--ttl-ms", str(board.TOKEN_TTL_MS)],
                      self.calls["herdr"])

    def test_a_form_does_not_reach_the_main_agent(self):
        self.blocked_world()
        self.round(self.watch())
        self.assertEqual(self.calls["main"], [])

    def test_a_third_form_hands_the_ticket_back_saying_it_asked_again(self):
        self.blocked_world(wake=board.WAKE_LIMIT)
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertTrue(comment[-1].startswith(
            "WAKEUP LIMIT: dismissed 3 forms and it asked again at phase=verify"))
        self.assertNotIn("went idle again", comment[-1])

    # ------------------------------------------------------------- the session is gone

    def test_an_unknown_session_is_redispatched_once_and_says_so_on_the_ticket(self):
        self.world([agent("issue-61", "w1:p1", "unknown", ticket=61, kind="worker",
                          phase="selfcheck")], {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertEqual(
            comment[-1],
            "REDISPATCHED: session issue-61 ended at phase=selfcheck; started again "
            "as junior-worker")
        self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])
        self.assertEqual(self.calls["dispatch"], [(61, "junior-worker")])

    def test_a_claimed_ticket_whose_pane_is_gone_is_redispatched_too(self):
        self.world([], {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        self.assertEqual(self.calls["dispatch"], [(61, "junior-worker")])
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertIn("ended at phase=unknown", comment[-1])

    def test_a_ticket_nobody_claimed_is_dispatched_not_redispatched(self):
        self.world([], {61: ticket(61)})
        self.round(self.watch())
        self.assertEqual([c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"]], [])
        self.assertEqual(self.calls["dispatch"], [(61, "junior-worker")])

    def test_a_ticket_with_a_closing_comment_is_left_alone(self):
        for closing in ("ALL MET", "HANDOFF REQUIRED: 1 abandoned (failed)"):
            with self.subTest(closing=closing):
                self.calls["dispatch"].clear()
                self.world([], {61: ticket(61, assignees=("me",), comments=[closing])})
                self.round(self.watch())
                self.assertEqual(self.calls["dispatch"], [])

    def test_a_second_death_hands_the_ticket_back_instead(self):
        self.world([agent("issue-61", "w1:p1", "unknown", ticket=61, kind="worker",
                          phase="verify")],
                   {61: ticket(61, assignees=("me",),
                               comments=["REDISPATCHED: session issue-61 ended at "
                                         "phase=selfcheck; started again as "
                                         "junior-worker"])})
        self.round(self.watch())
        self.assertEqual(self.calls["dispatch"], [])
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertTrue(comment[-1].startswith("REDISPATCHED:"))
        self.assertIn("Handed back to needs-triage", comment[-1])
        self.assertIn(["issue", "edit", "61", "--remove-label", "ready-for-agent",
                       "--add-label", "needs-triage"], self.calls["gh"])

    # ------------------------------------------------------------- dispatch.sh's exits

    def test_exit_1_still_takes_up_a_place(self):
        self.dispatch_code = 1
        self.world([], {70: ticket(70), 71: ticket(71), 72: ticket(72)})
        self.round(self.watch(parallel=2))
        self.assertEqual(self.calls["dispatch"],
                         [(70, "junior-worker"), (71, "junior-worker")])

    def test_exit_2_takes_up_no_place_and_is_not_retried_this_round(self):
        self.dispatch_code = 2
        self.world([], {70: ticket(70), 71: ticket(71), 72: ticket(72)})
        self.round(self.watch(parallel=2))
        self.assertEqual(self.calls["dispatch"],
                         [(70, "junior-worker"), (71, "junior-worker"),
                          (72, "junior-worker")])

    def test_a_session_that_was_never_told_anything_gets_its_dispatch_line(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker")],
                   {61: ticket(61)})
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [("w1:p1", "implement #61")])

    # ------------------------------------------------------------- the night's end

    def test_nothing_open_and_nothing_alive_ends_the_night(self):
        self.world([], {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertEqual(comment[2], "76")
        self.assertTrue(comment[-1].startswith("NIGHT SUMMARY "))
        self.assertTrue(watch.summary_written)

    def test_an_open_agent_lane_keeps_the_night_going(self):
        self.world([], {61: ticket(61)})
        watch = self.watch()
        self.round(watch)
        self.assertFalse(watch.summary_written)

    def test_the_summary_is_four_lines_of_numbers_and_first_lines(self):
        watch = self.watch()
        watch.opened = "2026-08-30T00:00:00+08:00"
        tickets = {
            61: ticket(61, state="CLOSED", labels=(), comments=["ALL MET\nBranch: x"]),
            62: ticket(62, labels=("needs-triage",),
                       comments=["WAKEUP LIMIT: re-prompted 3 times"]),
            63: ticket(63, blockers=(62,)),
            64: ticket(64, labels=("needs-triage",), comments=["fresh"]),
        }
        for number, when in ((61, "2026-08-29"), (62, "2026-08-29"),
                             (63, "2026-08-29"), (64, "2026-08-31")):
            tickets[number]["created"] = when + "T00:00:00+08:00"
        tickets[61]["closed_at"] = "2026-08-31T02:00:00+08:00"
        rows = board.build_rows(list(tickets), tickets, [])
        body = watch.summary(rows).splitlines()
        self.assertTrue(body[0].startswith("NIGHT SUMMARY "))
        self.assertEqual(body[2], "Closed: #61 ALL MET")
        self.assertEqual(body[3], "Handed back to needs-triage: "
                                  "#62 WAKEUP LIMIT: re-prompted 3 times, #64 fresh")
        self.assertEqual(body[4], "Not dispatched, a blocker stayed open: "
                                  "#63 blocked by #62")
        self.assertEqual(body[5], "Sub-issues opened tonight: #64 fresh")

    # ------------------------------------------------------------- the main agent

    def test_the_main_agent_hears_about_a_limit_and_about_the_end(self):
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["main"],
                         [(board.MAIN,
                           "mmw board: WAKEUP LIMIT #61 — run "
                           "~/.agents/skills/dispatch/scripts/board.py --once 76")])

    def test_a_working_main_agent_is_left_for_the_next_round(self):
        self.main[0]["agent_status"] = "working"
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.main[0]["agent_status"] = "idle"
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 1)

    def test_a_focused_main_agent_is_left_alone(self):
        self.main[0]["focused"] = True
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["main"], [])

    def test_with_nobody_named_mmw_main_the_line_is_dropped(self):
        self.main = []
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.assertEqual(watch.for_main, [])

    def test_the_end_of_the_night_reaches_the_main_agent(self):
        self.world([], {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        self.assertEqual(self.calls["main"],
                         [(board.MAIN, "mmw board: night over #76 — run "
                                       "~/.agents/skills/dispatch/scripts/board.py "
                                       "--once 76")])


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
