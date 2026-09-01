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

_OWN_WORKSPACE = object()


def setUpModule():
    """Answer for no workspace unless a test says otherwise.

    These tests run inside Herdr as often as not, and a board reads the workspace it
    was started in out of the environment — to name its sessions and to tell them from
    another board's. Left alone, the tests would be answering for whichever workspace
    the run happened to start in.
    """
    global _OWN_WORKSPACE
    _OWN_WORKSPACE = os.environ.pop("HERDR_WORKSPACE_ID", _OWN_WORKSPACE)


def tearDownModule():
    if _OWN_WORKSPACE is not None and not isinstance(_OWN_WORKSPACE, object.__class__):
        os.environ["HERDR_WORKSPACE_ID"] = _OWN_WORKSPACE


def agent(name, pane, status, host="claude", workspace="", **tokens):
    """One entry of `herdr api snapshot`'s `agents`, with only the fields read."""
    return {
        "name": name,
        "agent": host,
        "workspace_id": workspace,
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

    def test_only_the_dispatchers_own_sessions_count_as_held(self):
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
    """The only thing board.py ever says to a worker.

    One word, carrying no ticket number and naming no skill: every session it reaches
    is alive and already holds both.
    """

    def test_it_is_one_word_and_nothing_else(self):
        self.assertEqual(board.CONTINUE_LINE, "continue")


class Table(unittest.TestCase):
    """The one screen `--once` prints."""

    def table(self, spec=60):
        agents = [agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                        phase="implement")]
        tickets = {61: ticket(61), 65: ticket(65, blockers=(61,))}
        rows = board.build_rows(list(tickets), tickets, board.sessions(agents))
        return board.render_table(rows, spec, datetime(2026, 8, 31, 2, 14))

    def test_the_first_line_names_the_time_the_spec_the_count_and_the_live_sessions(self):
        self.assertEqual(self.table().splitlines()[0],
                         "mmw board · 02:14 · spec #60 · 2 tickets · 1 live")

    def test_without_a_spec_the_first_line_leaves_that_field_out(self):
        self.assertEqual(self.table(spec=None).splitlines()[0],
                         "mmw board · 02:14 · 2 tickets · 1 live")

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
        self.main = [agent(board.main_name(), "w1:pMain", "idle")]
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
                where = "main" if args[2] == board.main_name() else "prompt"
                self.calls[where].append((args[2], args[3]))
            return (0, "")

        def fake_dispatch(number, kind):
            self.calls["dispatch"].append((number, kind))
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

    def watch(self, max_hours=4):
        return board.Watch(76, max_hours)

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
        self.assertEqual(self.calls["prompt"], [("w1:p1", "continue")])

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

    # ------------------------------------------------------------- moving on

    ADVANCE = "mmw board: ADVANCE #76 — advance spec #76 with the dispatch skill"

    def test_a_frontier_with_tickets_on_it_reaches_the_main_agent(self):
        """The board says there is a step to take. Taking it is the main agent's."""
        self.world([], {70: ticket(70), 71: ticket(71), 72: ticket(72)})
        self.round(self.watch())
        self.assertEqual(self.calls["dispatch"], [])
        self.assertEqual(self.calls["main"], [(board.main_name(), self.ADVANCE)])

    def test_the_same_frontier_is_not_announced_twice(self):
        self.world([], {70: ticket(70)})
        watch = self.watch()
        self.round(watch)
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 1)

    def test_a_frontier_that_grows_is_announced_again(self):
        self.world([], {70: ticket(70)})
        watch = self.watch()
        self.round(watch)
        self.world([], {70: ticket(70), 71: ticket(71)})
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 2)

    def test_an_empty_frontier_says_nothing(self):
        self.world([agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                          phase="implement")], {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        self.assertEqual(self.calls["main"], [])

    def test_a_ticket_already_handed_back_is_not_announced(self):
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        before = len(self.calls["main"])
        self.world([], {61: ticket(61)})
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), before)

    def test_a_ticket_reaching_closed_has_its_pane_closed_in_the_same_round(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed")],
                   {61: ticket(61, state="CLOSED", labels=()), 70: ticket(70)})
        self.round(self.watch())
        self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    def test_a_ticket_over_its_time_limit_keeps_its_session(self):
        self.idle_world(phase="verify")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(4 * 3600 + 1)
        self.round(watch)
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])

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

    def reviewing_world(self, reviewer_status="blocked", wake=0):
        """A worker waiting on its reviewer, with the reviewer at a form.

        The worker is `working` throughout: it is sitting inside `dispatch.sh wait`,
        which reads the ticket and presses nothing.
        """
        self.world([agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                          phase="review"),
                    agent("issue-61-review", "w1:p2", reviewer_status, ticket=61,
                          kind="reviewer", wake=wake)],
                   {61: ticket(61, assignees=("me",))})

    def test_a_reviewer_at_a_form_has_it_read_onto_the_ticket_and_dismissed(self):
        self.reviewing_world()
        self.round(self.watch())
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertEqual(comment[2], "61")
        self.assertTrue(comment[-1].startswith(
            "BLOCKED: the reviewer on this ticket asked:"))
        self.assertIn("Which colour do you prefer?", comment[-1])
        self.assertIn(["agent", "send-keys", "w1:p2", "esc"], self.calls["herdr"])
        self.assertEqual(self.calls["prompt"], [("w1:p2", "continue")])

    def test_the_worker_waiting_on_it_is_not_touched(self):
        self.reviewing_world()
        self.round(self.watch())
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])
        self.assertEqual([p for p in self.calls["prompt"] if p[0] == "w1:p1"], [])

    def test_a_reviewer_out_of_dismissals_keeps_the_ticket(self):
        """No hand-back over a reviewer: the worker's own wait already times out."""
        self.reviewing_world(wake=board.WAKE_LIMIT)
        printed = self.round(self.watch())
        self.assertEqual(self.calls["gh"], [])
        self.assertEqual(self.calls["prompt"], [])
        self.assertIn("left for the worker's wait to time out", printed)

    def test_a_reviewer_that_is_working_is_left_alone(self):
        self.reviewing_world(reviewer_status="working")
        self.round(self.watch())
        self.assertEqual(self.calls["gh"], [])
        self.assertEqual(self.calls["prompt"], [])

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

    def test_after_the_form_it_is_told_to_continue_and_the_count_goes_up(self):
        self.blocked_world()
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [("w1:p1", "continue")])
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
            "REDISPATCHED: session issue-61 ended at phase=selfcheck; started again")
        self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])
        self.assertEqual(self.calls["dispatch"], [(61, "worker")])

    def test_a_claimed_ticket_whose_pane_is_gone_is_redispatched_too(self):
        self.world([], {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        self.assertEqual(self.calls["dispatch"], [(61, "worker")])
        comment = next(c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"])
        self.assertIn("ended at phase=unknown", comment[-1])

    def test_a_ticket_nobody_claimed_is_not_a_session_that_died(self):
        """No assignee means it was never started, so it goes to the frontier."""
        self.world([], {61: ticket(61)})
        self.round(self.watch())
        self.assertEqual([c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"]], [])
        self.assertEqual(self.calls["dispatch"], [])
        self.assertEqual(self.calls["main"], [(board.main_name(), self.ADVANCE)])

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

    def test_a_redispatch_that_will_not_start_is_left_for_the_next_round(self):
        """Exit 2 says the ticket did not qualify; the next round asks the tracker again."""
        self.dispatch_code = 2
        self.world([agent("issue-61", "w1:p1", "unknown", ticket=61, kind="worker",
                          phase="selfcheck")], {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        self.assertEqual(self.calls["dispatch"], [(61, "worker")])

    def test_a_session_that_was_never_told_anything_gets_its_dispatch_line(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker")],
                   {61: ticket(61)})
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.COOLDOWN_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [("w1:p1", "continue")])

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
        # GitHub writes createdAt and closedAt in UTC with a `Z` suffix; the fixtures
        # carry that exact shape, because the summary compares them to `opened` as
        # strings.
        watch.opened = "2026-08-30T00:00:00Z"
        tickets = {
            61: ticket(61, state="CLOSED", labels=(), comments=["ALL MET\nBranch: x"]),
            62: ticket(62, labels=("needs-triage",),
                       comments=["WAKEUP LIMIT: re-prompted 3 times"]),
            63: ticket(63, blockers=(62,)),
            64: ticket(64, labels=("needs-triage",), comments=["fresh"]),
        }
        for number, when in ((61, "2026-08-29"), (62, "2026-08-29"),
                             (63, "2026-08-29"), (64, "2026-08-31")):
            tickets[number]["created"] = when + "T00:00:00Z"
        tickets[61]["closed_at"] = "2026-08-31T02:00:00Z"
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
                         [(board.main_name(),
                           "mmw board: WAKEUP LIMIT #61 — read spec #76 with "
                           "the dispatch skill")])

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

    def test_with_nobody_named_mmw_main_the_line_waits(self):
        self.main = []
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.assertEqual(len(watch.for_main), 1)

    def test_a_waiting_line_is_delivered_once_mmw_main_is_there_again(self):
        """The pane can come back, and the night goes on from the line it left behind.

        A dropped line would end the night in silence: the frontier it belongs to is
        already recorded as announced, so no later round would raise it a second time.
        """
        self.main = []
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.main = [agent(board.main_name(), "w1:pMain", "idle")]
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 1)
        self.assertEqual(watch.for_main, [])

    def test_an_absent_mmw_main_is_reported_once_and_not_every_round(self):
        self.main = []
        self.idle_world(wake=board.WAKE_LIMIT)
        watch = self.watch()
        self.round(watch)
        self.clock.tick(max(board.WAKE_BACKOFF))
        printed = self.round(watch) + self.round(watch) + self.round(watch)
        self.assertEqual(printed.count("absent"), 1)

    def test_the_end_of_the_night_reaches_the_main_agent(self):
        self.world([], {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        self.assertEqual(
            self.calls["main"],
            [(board.main_name(), "mmw board: night over #76 — advance spec #76 "
                                 "with the dispatch skill")])


class Workspace(unittest.TestCase):
    """One board answers for one Herdr workspace, and names its sessions for it.

    Several projects run at once on one server, each in its own workspace, and every
    board sees every pane. Two things follow. A board acts only on the sessions of its
    own workspace, or it would re-prompt and close another project's. And the names it
    hands out carry the workspace, because Herdr's names are unique among live agents
    across the whole server — two repositories each holding a ticket #100 would collide
    on `issue-100`, and the second `agent start` would simply fail.
    """

    def setUp(self):
        os.environ.pop("HERDR_WORKSPACE_ID", None)

    def tearDown(self):
        os.environ.pop("HERDR_WORKSPACE_ID", None)

    def test_with_no_workspace_the_names_are_the_bare_ones(self):
        self.assertEqual(board.name_prefix(), "")
        self.assertEqual(board.main_name(), "mmw-main")
        self.assertEqual(board.worker_name(61), "issue-61")

    def test_a_workspace_is_carried_by_every_name(self):
        os.environ["HERDR_WORKSPACE_ID"] = "w2Q"
        self.assertEqual(board.name_prefix(), "w2q-")
        self.assertEqual(board.main_name(), "w2q-mmw-main")
        self.assertEqual(board.worker_name(61), "w2q-issue-61")
        self.assertTrue(board.name_re().match("w2q-issue-61-review"))
        self.assertIsNone(board.name_re().match("issue-61"))

    def test_a_name_stays_within_what_herdr_accepts(self):
        os.environ["HERDR_WORKSPACE_ID"] = "w2Q"
        name = board.worker_name(555) + "-review"
        self.assertRegex(name, r"^[a-z][a-z0-9_-]{0,31}$")

    def test_another_workspaces_session_is_not_this_boards(self):
        os.environ["HERDR_WORKSPACE_ID"] = "w2Q"
        agents = [agent("w2q-issue-61", "w2Q:p1", "idle", workspace="w2Q",
                        ticket=61, kind="worker"),
                  agent("w2k-issue-61", "w2K:p1", "idle", workspace="w2K",
                        ticket=61, kind="worker")]
        found = board.sessions(agents)
        self.assertEqual([s["pane_id"] for s in found], ["w2Q:p1"])

    def test_without_a_workspace_every_session_is_read(self):
        agents = [agent("issue-61", "w1:p1", "idle", workspace="w1",
                        ticket=61, kind="worker"),
                  agent("issue-62", "w2:p1", "idle", workspace="w2",
                        ticket=62, kind="worker")]
        self.assertEqual(len(board.sessions(agents)), 2)


class Constants(unittest.TestCase):
    """Every number the night runs on is here, and nowhere else."""

    def test_the_numbers_are_the_ones_the_plan_settled(self):
        self.assertEqual(
            (board.COOLDOWN_SECONDS, board.WAKE_BACKOFF, board.WAKE_LIMIT,
             board.REDISPATCH_LIMIT, board.MAX_HOURS, board.SNAPSHOT_INTERVAL),
            (120, (120, 240, 480), 3, 1, 4, 60))

    def test_no_cap_on_how_many_tickets_run_at_once(self):
        """Dispatching is the main agent's, and it is given no limit to spend."""
        self.assertFalse(hasattr(board, "PARALLEL"))


if __name__ == "__main__":
    unittest.main()
