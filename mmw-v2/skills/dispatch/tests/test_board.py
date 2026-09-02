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
        "comments": [{"body": c, "createdAt": "2000-01-01T00:00:00Z"} for c in comments],
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

    def test_the_turn_token_is_read_beside_the_phase(self):
        found = board.session_of(agent("issue-61", "w1:p1", "idle", ticket=61,
                                       kind="worker", turn="failed:server_error",
                                       turn_id="p-4"))
        self.assertEqual((found["turn"], found["turn_id"]), ("failed:server_error", "p-4"))


class Rows(unittest.TestCase):
    """The table's own contents, joined from the two sources."""

    def rows(self):
        agents = [
            agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                  phase="implement", turn="working"),
            agent("issue-62", "w1:p2", "idle", ticket=62, kind="worker",
                  phase="selfcheck", ac="3/5", turn="failed:rate_limit"),
            agent("issue-63", "w1:p3", "idle", ticket=63, kind="worker",
                  phase="verify", ac="5/5", turn="ended"),
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
        self.assertEqual((row["agent"], row["status"], row["phase"], row["turn"], row["note"]),
                         ("issue-61", "working", "implement", "working", ""))

    def test_a_failed_turn_says_it_will_be_continued(self):
        row = self.row(62)
        self.assertEqual(row["ac"], "3/5")
        self.assertEqual(row["turn"], "failed:rate_limit")
        self.assertEqual(row["note"], "turn failed; continue")

    def test_a_turn_the_session_ended_says_mmw_main_is_told(self):
        self.assertEqual(self.row(63)["note"], "stopped; mmw-main told")

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


class TurnKinds(unittest.TestCase):
    """The one reading board.py makes of the `turn` token."""

    def test_the_four_kinds(self):
        self.assertEqual(board.turn_kind("failed:server_error"), "failed")
        self.assertEqual(board.turn_kind("ended"), "stopped")
        self.assertEqual(board.turn_kind("cancelled:no_progress"), "stopped")
        self.assertEqual(board.turn_kind("working"), "running")
        self.assertEqual(board.turn_kind("ready"), "running")
        self.assertEqual(board.turn_kind(""), "")


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
                        phase="implement", turn="working")]
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
                          "turn", "note"])

    def test_one_line_per_ticket_in_ticket_order(self):
        body = self.table().splitlines()[3:]
        self.assertEqual([l.split()[0] for l in body], ["#61", "#65"])
        self.assertIn("issue-61", body[0])
        self.assertIn("waiting on #61", body[1])


class Clock:
    """A monotonic clock the test moves by hand, so waits cost no wall time."""

    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def tick(self, seconds):
        self.now += seconds


class Actions(unittest.TestCase):
    """The lookup table: what board.py does about each thing it can see.

    Nothing here reaches Herdr or the tracker. Every call board.py would make to
    either is replaced by a recorder, so the test reads the decisions themselves.
    """

    def setUp(self):
        self.calls = {"herdr": [], "gh": [], "prompt": [], "main": []}
        self.clock = Clock()
        self.saved = {name: getattr(board, name) for name in
                      ("herdr", "gh", "herdr_run", "read_ticket", "collect",
                       "live_agents", "time")}
        self.main = [agent(board.main_name(), "w1:pMain", "idle")]
        self.tickets = {}
        self.rows = []

        def fake_herdr(args):
            self.calls["herdr"].append(list(args))
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

        board.herdr = fake_herdr
        board.gh = fake_gh
        board.herdr_run = fake_prompt
        board.live_agents = lambda: list(self.main)
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

    def worker_world(self, turn, phase="selfcheck", status="idle", turn_id="p-1", **extra):
        self.world([agent("issue-61", "w1:p1", status, ticket=61, kind="worker",
                          phase=phase, ac="1/2", turn=turn, turn_id=turn_id, **extra)],
                   {61: ticket(61, assignees=("me",), comments=[SELF_RUN_UNMET])})

    def comments(self):
        return [c for c in self.calls["gh"] if c[0:2] == ["issue", "comment"]]

    def labels(self):
        return [c for c in self.calls["gh"] if c[0:2] == ["issue", "edit"]]

    # ------------------------------------------------------------- working

    def test_a_working_session_is_left_alone(self):
        self.worker_world("working", status="working", phase="implement")
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(self.calls["gh"], [])
        self.assertEqual(self.calls["main"], [])
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    def test_a_session_that_just_came_up_is_left_alone(self):
        self.worker_world("ready", status="idle", phase="")
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(self.calls["main"], [])

    # ------------------------------------------------------------- at the end

    def test_a_session_whose_phase_is_closed_or_handoff_has_its_pane_closed(self):
        for phase in ("closed", "handoff"):
            with self.subTest(phase=phase):
                self.calls["herdr"].clear()
                self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                                  phase=phase, turn="ended")],
                           {61: ticket(61, state="CLOSED", labels=())})
                printed = self.round(self.watch())
                self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])
                self.assertIn("#61", printed)
                self.assertEqual(self.calls["prompt"], [])
                self.assertEqual([m for m in self.calls["main"] if "STOPPED" in m[1]], [])

    # ------------------------------------------------------------- a turn that failed

    def test_a_failed_turn_is_sent_continue_at_once(self):
        self.worker_world("failed:server_error")
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [("w1:p1", "continue")])
        self.assertEqual(self.calls["gh"], [])
        self.assertEqual(self.calls["main"], [])

    def test_the_same_failed_turn_is_not_continued_twice(self):
        self.worker_world("failed:server_error")
        watch = self.watch()
        self.round(watch)
        self.round(watch)
        self.clock.tick(3600)
        self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), 1)

    def test_a_new_turn_that_fails_again_is_continued_again(self):
        self.worker_world("failed:server_error", turn_id="p-1")
        watch = self.watch()
        self.round(watch)
        self.worker_world("failed:rate_limit", turn_id="p-2")
        self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), 2)

    def test_the_fourth_failure_at_one_phase_goes_to_mmw_main_instead(self):
        watch = self.watch()
        for n in range(1, board.FAILED_LIMIT + 2):
            self.worker_world("failed:server_error", turn_id=f"p-{n}")
            self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), board.FAILED_LIMIT)
        stopped = [m for m in self.calls["main"] if "STOPPED #61" in m[1]]
        self.assertEqual(len(stopped), 1)

    def test_a_new_phase_starts_the_failure_count_again(self):
        watch = self.watch()
        for n in range(1, board.FAILED_LIMIT + 1):
            self.worker_world("failed:server_error", turn_id=f"p-{n}", phase="selfcheck")
            self.round(watch)
        self.worker_world("failed:server_error", turn_id="p-9", phase="verify")
        self.round(watch)
        self.assertEqual(len(self.calls["prompt"]), board.FAILED_LIMIT + 1)
        self.assertEqual([m for m in self.calls["main"] if "STOPPED" in m[1]], [])

    def test_a_focused_pane_is_never_prompted(self):
        self.worker_world("failed:server_error")
        self.agents[0]["focused"] = True
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])

    def test_a_pane_that_went_back_to_work_is_not_prompted(self):
        self.worker_world("failed:server_error")
        self.agents[0]["agent_status"] = "working"
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])

    def test_a_pane_holding_a_different_session_now_is_not_prompted(self):
        self.worker_world("failed:server_error")
        self.agents[0]["agent_session"] = {"value": "somebody-else"}
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])

    # ------------------------------------------------------------- a turn the session ended

    STOPPED = ("mmw board: STOPPED #61 at phase=selfcheck — read issue-61 with herdr, "
               "then move it on with the dispatch skill")

    def test_a_turn_the_session_ended_short_of_closed_reaches_mmw_main(self):
        self.worker_world("ended")
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(self.calls["gh"], [])
        self.assertEqual(self.calls["main"], [(board.main_name(), self.STOPPED)])

    def test_a_cancelled_turn_reaches_mmw_main_the_same_way(self):
        self.worker_world("cancelled:no_progress")
        self.round(self.watch())
        self.assertEqual(self.calls["main"], [(board.main_name(), self.STOPPED)])

    def test_one_stop_is_reported_once(self):
        self.worker_world("ended")
        watch = self.watch()
        self.round(watch)
        self.round(watch)
        self.clock.tick(3600)
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 1)

    def test_a_later_stop_is_reported_again(self):
        self.worker_world("ended", turn_id="p-1")
        watch = self.watch()
        self.round(watch)
        self.worker_world("working", status="working", turn_id="p-2")
        self.round(watch)
        self.worker_world("ended", turn_id="p-2")
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 2)

    def test_the_ticket_keeps_its_label_and_its_pane(self):
        self.worker_world("ended")
        self.round(self.watch())
        self.assertEqual(self.labels(), [])
        self.assertEqual(self.comments(), [])
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    def test_a_reviewer_that_stops_is_left_to_its_workers_own_wait(self):
        self.world([agent("issue-61", "w1:p1", "working", ticket=61, kind="worker",
                          phase="review", turn="working"),
                    agent("issue-61-review", "w1:p2", "idle", ticket=61,
                          kind="reviewer", turn="ended")],
                   {61: ticket(61, assignees=("me",))})
        self.round(self.watch())
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(self.calls["main"], [])
        self.assertNotIn(["pane", "close", "w1:p2"], self.calls["herdr"])

    # ------------------------------------------------------------- no turn report at all

    def test_a_session_with_no_turn_token_is_left_alone_at_first(self):
        self.worker_world("", turn_id="")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.FALLBACK_SECONDS - 1)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(self.calls["main"], [])

    def test_idle_that_long_with_nothing_new_reaches_mmw_main_not_the_session(self):
        self.worker_world("", turn_id="")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.FALLBACK_SECONDS)
        self.round(watch)
        self.assertEqual(self.calls["prompt"], [])
        self.assertEqual(len(self.calls["main"]), 1)
        self.assertIn("STOPPED #61", self.calls["main"][0][1])

    def test_a_new_comment_on_the_ticket_starts_the_wait_again(self):
        self.worker_world("", turn_id="")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.FALLBACK_SECONDS - 1)
        self.world(self.agents, {61: ticket(61, assignees=("me",),
                                            comments=[SELF_RUN_UNMET, VERDICT])})
        self.round(watch)
        self.clock.tick(1)
        self.round(watch)
        self.assertEqual(self.calls["main"], [])

    def test_a_session_herdr_reads_as_working_is_never_counted(self):
        self.worker_world("", turn_id="", status="working")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.FALLBACK_SECONDS * 3)
        self.round(watch)
        self.assertEqual(self.calls["main"], [])

    def test_herdrs_unknown_is_not_idle(self):
        self.worker_world("", turn_id="", status="unknown")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(board.FALLBACK_SECONDS * 3)
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.assertEqual(self.calls["prompt"], [])

    # ------------------------------------------------------------- the time limit

    TIME_LIMIT = ("mmw board: TIME LIMIT #61 — 4 h at phase=verify; read issue-61 with "
                  "herdr and decide with the dispatch skill")

    def test_a_ticket_held_too_long_is_reported_once_and_keeps_everything(self):
        self.worker_world("working", status="working", phase="verify")
        watch = self.watch()
        self.round(watch)
        self.clock.tick(4 * 3600 + 1)
        self.round(watch)
        self.round(watch)
        self.assertEqual(self.calls["main"], [(board.main_name(), self.TIME_LIMIT)])
        self.assertEqual(self.labels(), [])
        self.assertEqual(self.comments(), [])
        self.assertNotIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    def test_a_session_whose_phase_is_closed_is_past_the_time_limit(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed", turn="ended")],
                   {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        self.clock.tick(4 * 3600 + 1)
        self.round(watch)
        self.assertEqual([m for m in self.calls["main"] if "TIME LIMIT" in m[1]], [])

    # ------------------------------------------------------------- never

    def test_the_board_never_changes_a_label_or_starts_a_session(self):
        watch = self.watch()
        for turn in ("failed:server_error", "ended", "cancelled:max_turns", ""):
            self.worker_world(turn, turn_id="")
            self.round(watch)
            self.clock.tick(5 * 3600)
            self.round(watch)
        self.assertEqual(self.labels(), [])
        self.assertEqual(self.comments(), [])
        self.assertEqual([c for c in self.calls["herdr"] if c[:2] == ["agent", "start"]], [])
        self.assertEqual([c for c in self.calls["herdr"] if c[:2] == ["agent", "send-keys"]], [])

    def test_a_claimed_ticket_with_no_session_is_neither_started_nor_handed_back(self):
        self.world([], {61: ticket(61, assignees=("me",))})
        watch = self.watch()
        self.round(watch)
        self.clock.tick(5 * 3600)
        self.round(watch)
        self.assertEqual(self.calls["gh"], [])
        self.assertEqual(self.calls["main"], [])

    # ------------------------------------------------------------- moving on

    ADVANCE = "mmw board: ADVANCE #76 — advance spec #76 with the dispatch skill"

    def test_a_frontier_with_tickets_on_it_reaches_the_main_agent(self):
        """The board says there is a step to take. Taking it is the main agent's."""
        self.world([], {70: ticket(70), 71: ticket(71), 72: ticket(72)})
        self.round(self.watch())
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
        self.worker_world("working", status="working", phase="implement")
        self.round(self.watch())
        self.assertEqual(self.calls["main"], [])

    def test_a_ticket_reaching_closed_has_its_pane_closed_in_the_same_round(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed", turn="ended")],
                   {61: ticket(61, state="CLOSED", labels=()), 70: ticket(70)})
        self.round(self.watch())
        self.assertIn(["pane", "close", "w1:p1"], self.calls["herdr"])

    def test_the_last_session_reaching_closed_ends_the_night_in_the_same_round(self):
        self.world([agent("issue-61", "w1:p1", "idle", ticket=61, kind="worker",
                          phase="closed", turn="ended")],
                   {61: ticket(61, state="CLOSED", labels=())})
        watch = self.watch()
        self.round(watch)
        self.assertTrue(watch.summary_written)

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
                       comments=["HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 4 met of 5"]),
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
                                  "#62 HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, "
                                  "4 met of 5, #64 fresh")
        self.assertEqual(body[4], "Not dispatched, a blocker stayed open: "
                                  "#63 blocked by #62")
        self.assertEqual(body[5], "Sub-issues opened tonight: #64 fresh")

    # ------------------------------------------------------------- the main agent

    def test_a_working_main_agent_is_left_for_the_next_round(self):
        self.main[0]["agent_status"] = "working"
        self.worker_world("ended")
        watch = self.watch()
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.main[0]["agent_status"] = "idle"
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 1)

    def test_a_focused_main_agent_is_left_alone(self):
        self.main[0]["focused"] = True
        self.worker_world("ended")
        self.round(self.watch())
        self.assertEqual(self.calls["main"], [])

    def test_with_nobody_named_mmw_main_the_line_waits(self):
        self.main = []
        self.worker_world("ended")
        watch = self.watch()
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.assertEqual(len(watch.for_main), 1)

    def test_a_waiting_line_is_delivered_once_mmw_main_is_there_again(self):
        """The pane can come back, and the night goes on from the line it left behind."""
        self.main = []
        self.worker_world("ended")
        watch = self.watch()
        self.round(watch)
        self.assertEqual(self.calls["main"], [])
        self.main = [agent(board.main_name(), "w1:pMain", "idle")]
        self.round(watch)
        self.assertEqual(len(self.calls["main"]), 1)
        self.assertEqual(watch.for_main, [])

    def test_an_absent_mmw_main_is_reported_once_and_not_every_round(self):
        self.main = []
        self.worker_world("ended")
        watch = self.watch()
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


class TheLog(unittest.TestCase):
    """Every line `say()` prints is also appended to the night's log file."""

    def test_a_line_lands_in_the_file_when_one_is_named(self):
        import tempfile
        saved = board.LOG_FILE
        try:
            with tempfile.TemporaryDirectory() as tmp:
                board.LOG_FILE = Path(tmp) / "logs" / "board-w1-76.log"
                with redirect_stdout(io.StringIO()) as out:
                    board.say("#61", "prompt", "continue", datetime(2026, 9, 2, 3, 4, 5))
                text = board.LOG_FILE.read_text(encoding="utf-8")
            self.assertIn("03:04:05  #61       prompt     continue", out.getvalue())
            self.assertEqual(text, "2026-09-02 03:04:05  #61       prompt     continue\n")
        finally:
            board.LOG_FILE = saved

    def test_without_a_file_it_only_prints(self):
        saved = board.LOG_FILE
        try:
            board.LOG_FILE = None
            with redirect_stdout(io.StringIO()) as out:
                board.say("board", "watch", "spec #76")
            self.assertIn("spec #76", out.getvalue())
        finally:
            board.LOG_FILE = saved


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


class ReadingHerdr(unittest.TestCase):
    """What the board makes of Herdr's answers about a session."""

    def setUp(self):
        self.saved = board.herdr, board.herdr_strict

    def tearDown(self):
        board.herdr, board.herdr_strict = self.saved

    def test_a_snapshot_herdr_would_not_answer_is_not_a_workspace_with_no_sessions(self):
        """Every ticket would read as one whose session vanished, so the round stops."""
        board.herdr_strict = lambda args: (_ for _ in ()).throw(RuntimeError("exit 1"))
        with self.assertRaises(RuntimeError):
            board.live_agents()

    def test_a_snapshot_without_the_snapshot_field_is_refused_the_same_way(self):
        board.herdr_strict = lambda args: {"result": {}}
        with self.assertRaises(RuntimeError):
            board.live_agents()

    def test_an_empty_workspace_is_read_as_no_sessions(self):
        board.herdr_strict = lambda args: {"result": {"snapshot": {"agents": []}}}
        self.assertEqual(board.live_agents(), [])


class Constants(unittest.TestCase):
    """Every number the night runs on is here, and nowhere else."""

    def test_the_numbers_are_the_ones_the_spec_settled(self):
        self.assertEqual(
            (board.MAX_HOURS, board.SNAPSHOT_INTERVAL, board.FAILED_LIMIT,
             board.FALLBACK_SECONDS),
            (4, 60, 3, 600))

    def test_nothing_that_takes_a_ticket_out_of_the_queue_exists(self):
        for name in ("WAKE_LIMIT", "WAKE_BACKOFF", "COOLDOWN_SECONDS", "REDISPATCH_LIMIT",
                     "ABSENT_GRACE", "CLOSE_KEYS", "FORM_LINES", "STOPPED_STATUSES",
                     "PARALLEL"):
            self.assertFalse(hasattr(board, name), name)
        for name in ("hand_back", "redispatch", "at_a_form", "gone", "re_prompt", "bump"):
            self.assertFalse(hasattr(board.Watch, name), name)


if __name__ == "__main__":
    unittest.main()
