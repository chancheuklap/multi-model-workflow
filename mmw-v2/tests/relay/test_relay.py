"""Tests for relay.py and statedir.py: no tracker, no runner, no network.

The relay's outsides are the board (a `Board` whose `gh` answers from a dict of comments
here), the runner's `send` verb (a function here that records what it was handed and
answers with the exit code a test chooses), the runner's `liveness` verb (a function
answering what a test chooses) and the clock. Between them runs the whole relay: the
watches and their main agents, reading events, dedup, who each row is for, the slot
wake, the queue, delivery, ack, the unattended-stretch marker, the watch of a main agent
that is gone. What is asserted is what an outsider can see: the watches, the rows in the
queue, their order and recipients, what was sent to whom, and what is left after an ack.

    python3 -m unittest discover -s mmw-v2/tests/relay -p test_relay.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "dispatch" / "scripts"
sys.path.insert(0, str(SCRIPTS))

_spec = importlib.util.spec_from_file_location("relay", SCRIPTS / "relay.py")
relay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(relay)
import statedir  # noqa: E402

T0 = datetime(2026, 9, 10, 1, 0, 0, tzinfo=timezone.utc)
MAIN_A = ("paseo", "main-a")


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def started(cid: int, ticket: int, session: str, runner: str = "paseo") -> dict:
    """The `worker.started` comment that names a ticket's worker."""
    return comment(cid, "worker.started", ticket, runner=runner, session=session)


# What each event must carry to be an event at all (`events.EVENTS`), for the fixtures
# below that do not care about those fields.
REQUIRED = {
    "verifier.passed": {"commit": "a" * 40},
    "verifier.failed": {"commit": "a" * 40},
    "ticket.refused": {"reason": "blocked"},
    "ticket.released": {"reason": "worker-lost"},
    "child.opened": {"child": 90, "kind": "review"},
    "worker.lost": {"session": "gone", "runner": "paseo"},
    "worker.started": {"machine": "mac-1", "host": "grok", "model": "grok-4.6", "effort": "high", "grade": "junior-worker", "worktree": "/repo/.worktrees/issue-61", "branch": "issue-61", "base": "0" * 40},
    "reviewer.started": {"session": "rv-1", "runner": "paseo", "machine": "mac-1"},
    "verifier.started": {"session": "vf-1", "runner": "paseo", "machine": "mac-1"},
}


def comment(cid: int, event: str | None, ticket: int | None = None,
            updated: datetime = T0, **payload) -> dict:
    """One GitHub issue comment; with an event it is written the way the scripts write one."""
    body = "a first line for people, worded any way"
    if event:
        body = relay.events.build(event, ticket=ticket, line=body, at=stamp(updated),
                                  **{**REQUIRED.get(event, {}), **payload})
    return {"id": cid, "body": body, "created_at": stamp(updated), "updated_at": stamp(updated)}


class FakeGh:
    """`gh_list` over a dict {ticket: [comments]}: pages already flattened, as `gh_list`
    hands them on. Honours `since` the way GitHub does (updated_at at or after it)."""

    def __init__(self, board: dict[int, list[dict]], spec_children: dict[int, list[int]] | None = None):
        self.board = board
        self.spec_children = spec_children or {}
        self.failing: set[int] = set()
        self.calls: list[list[str]] = []
        self.during_read = None  # called while a ticket's comments are read: time passing

    def __call__(self, args: list[str]) -> list:
        self.calls.append(args)
        url = args[-1]
        path, _, query = url.partition("?")
        parts = path.split("/")
        number = int(parts[4])
        if parts[5] == "sub_issues":
            if number in self.failing:
                raise relay.PollError("gh exited 1: HTTP 502: Bad Gateway")
            return [{"number": n, "state": "open"} for n in self.spec_children.get(number, [])]
        if number in self.failing:
            raise relay.PollError("gh exited 1: HTTP 502: Bad Gateway")
        if self.during_read:
            self.during_read()
        since = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("since")
        rows = [c for c in self.board.get(number, []) if not since or c["updated_at"] >= since]
        return rows

    def sinces(self, ticket: int) -> list[str | None]:
        out = []
        for args in self.calls:
            url = args[-1]
            if f"/issues/{ticket}/comments" in url:
                query = url.partition("?")[2]
                out.append(dict(p.split("=", 1) for p in query.split("&")).get("since"))
        return out


class FakeSend:
    """The runner's send verb: records (runner, session, text), answers `self.code`."""

    def __init__(self, code: int = 0):
        self.code = code
        self.sent: list[tuple[str, str, str]] = []

    def __call__(self, runner: str, session: str, text: str) -> int:
        self.sent.append((runner, session, text))
        return self.code


class Clock:
    def __init__(self, moment: datetime = T0):
        self.moment = moment

    def __call__(self) -> datetime:
        return self.moment


class FakeAsk:
    """The runner's liveness verb: records (runner, session), answers from `answers`."""

    def __init__(self, default: str = "alive"):
        self.default = default
        self.answers: dict[tuple[str, str], str] = {}
        self.calls: list[tuple[str, str]] = []

    def __call__(self, runner: str, session: str) -> str:
        self.calls.append((runner, session))
        return self.answers.get((runner, session), self.default)


class RelayCase(unittest.TestCase):
    """One repository's state directory with tickets #61 and #62 watched, main agent main-a."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old_home = os.environ.get("MMW_HOME")
        os.environ["MMW_HOME"] = self.tmp.name
        self.addCleanup(self.restore_home)
        self.state = statedir.state_dir("o/r")
        self.board: dict[int, list[dict]] = {61: [], 62: []}
        self.gh = FakeGh(self.board)
        self.send = FakeSend()
        self.ask = FakeAsk()
        self.clock = Clock()
        self.relay = self.fresh()
        self.relay.open_watch({"tickets": [61, 62]}, "paseo", "main-a")

    def restore_home(self):
        if self.old_home is None:
            os.environ.pop("MMW_HOME", None)
        else:
            os.environ["MMW_HOME"] = self.old_home

    def fresh(self):
        """A relay as a newly started process would be: same state directory, nothing in memory."""
        self.out, self.err = io.StringIO(), io.StringIO()
        return relay.Relay(self.state, relay.Board("o/r", self.gh), send=self.send,
                           clock=self.clock, ask=self.ask, out=self.out, err=self.err)

    def poll(self, grace=90):
        return self.relay.poll(30, grace)

    def watches(self):
        """Each open watch's key and its main agent."""
        return {k: (w["runner"], w["session"]) for k, w in self.relay.watches().items()}

    def rows(self):
        return self.relay.rows()

    def summary(self):
        return [(r["seq"], r["ticket"], r["event"]) for r in self.rows()]

    def addressed(self):
        return [(r["seq"], r["event"], r["to"], r["session"]) for r in self.rows()]


class QueueTest(RelayCase):
    def test_events_queue_in_the_order_they_landed_with_rising_seq(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.board[62].append(comment(100, "ticket.returned", 62))
        self.assertTrue(self.poll())
        self.assertEqual(self.summary(), [(1, 62, "ticket.returned"), (2, 61, "ticket.passed")])
        row = self.rows()[0]
        self.assertEqual((row["runner"], row["session"], row["at"]), ("paseo", "main-a", stamp(T0)))

    def test_seq_is_never_reused_after_an_ack_empties_the_queue(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.board[62].append(comment(102, "ticket.passed", 62))
        self.poll()
        self.assertEqual(self.relay.ack(MAIN_A, 2), (2, 0))
        self.board[61].append(comment(103, "ticket.refused", 61))
        self.poll()
        self.assertEqual(self.summary(), [(3, 61, "ticket.refused")])

    def test_ack_through_removes_rows_up_to_that_seq_and_no_further(self):
        for cid in (101, 102, 103):
            self.board[61].append(comment(cid, "ticket.passed", 61))
        self.poll()
        self.assertEqual(self.relay.ack(MAIN_A, 2), (2, 1))
        self.assertEqual([r["seq"] for r in self.rows()], [3])

    def test_ack_past_the_last_seq_issued_is_refused_and_removes_nothing(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.poll()
        with self.assertRaises(relay.Refusal) as caught:
            self.relay.ack(MAIN_A, 5)
        self.assertIn("the last one is 1", str(caught.exception))
        self.assertEqual(len(self.rows()), 1)

    def test_one_event_is_queued_once_across_polls_restarts_and_acks(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.poll()
        self.poll()
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.summary(), [(1, 61, "ticket.passed")])
        self.relay.ack(MAIN_A, 1)
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.rows(), [])

    def test_a_lost_reviewer_or_verifier_wakes_the_worker_that_started_it(self):
        self.board[61] += [
            started(101, 61, "wk-61"),
            comment(102, "reviewer.started", 61),
            comment(103, "reviewer.lost", 61, session="rv-1", runner="paseo"),
            comment(104, "verifier.started", 61),
            comment(105, "verifier.lost", 61, session="vf-1", runner="paseo"),
        ]
        self.poll()
        self.assertEqual(self.addressed(), [
            (1, "reviewer.lost", "worker", "wk-61"),
            (2, "verifier.lost", "worker", "wk-61"),
        ])

    def test_only_the_events_in_wakes_are_queued_each_for_its_role(self):
        self.board[61] += [
            comment(100, None),
            started(101, 61, "wk-61"),
            comment(102, "ticket.claimed", 61),
            comment(103, "reviewer.started", 61),
            comment(104, "reviewer.reported", 61),
            comment(105, "verifier.started", 61),
            comment(106, "verifier.failed", 61),
            comment(107, "verifier.passed", 61),
            comment(108, "child.opened", 61, kind="finding"),
            comment(109, "child.opened", 61, kind="deferred"),
            comment(110, "child.opened", 61, kind="fault"),
            comment(111, "child.opened", 61, kind="decision"),
            comment(112, "child.opened", 61, kind="contract"),
            comment(113, "ticket.passed", 61),
            comment(114, "ticket.landed", 61),
            comment(115, "worker.lost", 61),
        ]
        self.board[62] += [comment(116, "ticket.returned", 62), comment(117, "ticket.refused", 62)]
        self.poll()
        self.assertEqual(self.addressed(), [
            (1, "reviewer.reported", "worker", "wk-61"),
            (2, "verifier.failed", "worker", "wk-61"),
            (3, "verifier.passed", "worker", "wk-61"),
            (4, "child.opened", "main", "main-a"),
            (5, "child.opened", "main", "main-a"),
            (6, "ticket.passed", "main", "main-a"),
            (7, "worker.lost", "main", "main-a"),
            (8, "ticket.returned", "main", "main-a"),
            (9, "ticket.refused", "main", "main-a"),
        ])
        # The two children that wake the main agent are the fault and the decision.
        woken = [r for r in self.rows() if r["event"] == "child.opened"]
        self.assertEqual(len(woken), 2)

    def test_a_fault_wakes_the_main_agent_and_the_other_kinds_do_not(self):
        for kind, wakes in (("fault", True), ("decision", True), ("finding", False),
                            ("contract", False), ("deferred", False)):
            with self.subTest(kind=kind):
                self.assertEqual(relay.woken_by({"event": "child.opened", "kind": kind}),
                                 relay.MAIN if wakes else None)

    def test_the_ticket_is_the_one_the_event_names_or_else_the_issue_it_sits_on(self):
        self.board[61].append(comment(101, "ticket.passed", 70))
        self.board[62].append(comment(102, "ticket.passed", None))
        self.poll()
        self.assertEqual([r["ticket"] for r in self.rows()], [70, 62])

    def test_an_unreadable_block_is_reported_once_and_queues_nothing(self):
        body = "prose\n\n<!-- mmw " + json.dumps({"v": 2, "event": "ticket.passed"}) + " -->"
        self.board[61].append({"id": 101, "body": body, "created_at": stamp(T0), "updated_at": stamp(T0)})
        self.poll()
        self.assertIn("comment 101 on #61", self.err.getvalue())
        self.assertIn("version 2", self.err.getvalue())
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.err.getvalue(), "")
        self.assertEqual(self.rows(), [])

    def test_a_main_agent_replaced_while_the_board_is_read_addresses_the_new_rows(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.gh.during_read = lambda: self.relay.open_watch({"tickets": [61, 62]}, "paseo", "main-b")
        self.poll()
        self.gh.during_read = None
        self.assertEqual(self.addressed(), [(1, "ticket.passed", "main", "main-b")])
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-b", "#61 ticket.passed")])

    def test_a_poll_with_nothing_watched_reads_nothing(self):
        self.relay.close_watch(None)
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.assertTrue(self.poll())
        self.assertEqual((self.gh.calls, self.rows()), ([], []))


class WorkerRecipientTest(RelayCase):
    def test_a_worker_wake_goes_to_the_worker_on_the_ticket_when_the_event_landed(self):
        self.board[61] += [started(101, 61, "wk-a", runner="orca"), comment(102, "reviewer.reported", 61),
                           started(103, 61, "wk-b", runner="herdr"), comment(104, "verifier.passed", 61)]
        self.poll()
        self.assertEqual([(r["event"], r["runner"], r["session"]) for r in self.rows()],
                         [("reviewer.reported", "orca", "wk-a"), ("verifier.passed", "herdr", "wk-b")])

    def test_the_worker_named_in_an_earlier_read_addresses_a_later_event(self):
        self.board[61] += [
            comment(101, "worker.started", 61, updated=T0 - timedelta(hours=1), runner="orca", session="wk-a"),
            comment(102, "ticket.claimed", 61, updated=T0),
        ]
        self.poll()
        self.board[61].append(comment(103, "reviewer.reported", 61, updated=T0 + timedelta(seconds=30)))
        self.clock.moment = T0 + timedelta(seconds=30)
        self.poll()
        # The since read returns only the report: the worker comes from what the first read saw.
        self.assertEqual(self.gh.sinces(61)[-1], stamp(T0 - timedelta(seconds=120)))
        self.assertEqual(self.addressed(), [(1, "reviewer.reported", "worker", "wk-a")])

    def test_a_worker_wake_on_a_ticket_with_no_worker_is_reported_once_and_not_queued(self):
        self.board[61].append(comment(102, "reviewer.reported", 61))
        self.poll()
        self.assertEqual(self.rows(), [])
        self.assertIn("comment 102 on #61 was not translated", self.err.getvalue())
        self.assertIn("no worker.started on #61 comes before it", self.err.getvalue())
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.err.getvalue(), "")

    def test_a_worker_started_without_runner_and_session_is_reported(self):
        # Written by hand, not by a script: the event table refuses to build this one.
        bare = '{"v":1,"event":"worker.started","ticket":61,"session":"wk-a"}'
        self.board[61].append({"id": 101, "body": f"started\n\n<!-- mmw {bare} -->",
                               "created_at": stamp(T0), "updated_at": stamp(T0)})
        self.board[61].append(comment(102, "reviewer.reported", 61))
        self.poll()
        self.assertIn("comment 101 on #61 was not translated: `worker.started` carries no `runner`",
                      self.err.getvalue())
        self.assertEqual(self.rows(), [])

    def test_a_row_for_a_replaced_worker_is_dropped_without_a_send(self):
        self.board[61] += [started(101, 61, "wk-a"), comment(102, "reviewer.reported", 61)]
        self.poll()
        self.board[61].append(started(103, 61, "wk-b"))
        self.poll()
        self.relay.deliver()
        self.assertEqual(self.send.sent, [])
        self.assertEqual(self.rows(), [])
        self.assertIn("#61's worker is now paseo session wk-b", self.err.getvalue())

    def test_a_busy_main_agent_does_not_hold_up_a_worker(self):
        self.board[61] += [started(101, 61, "wk-61"), comment(102, "ticket.refused", 61),
                           comment(103, "ticket.passed", 61), comment(104, "reviewer.reported", 61)]
        self.poll()
        codes = {"main-a": 3, "wk-61": 0}
        self.relay.send = lambda runner, session, text: (self.send.sent.append((runner, session, text))
                                                         or codes[session])
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-a", "#61 ticket.refused"),
                                          ("paseo", "wk-61", "#61 reviewer.reported")])
        self.assertEqual([(r["seq"], bool(r["delivered"])) for r in self.rows()],
                         [(1, False), (2, False), (3, True)])

    def test_a_recipient_is_its_runner_and_session_together(self):
        self.relay.open_watch({"tickets": [61, 62]}, "paseo", "s-1")
        self.board[61] += [started(101, 61, "s-1", runner="orca"), comment(102, "ticket.passed", 61),
                           comment(103, "reviewer.reported", 61)]
        self.poll()
        self.assertEqual([(r["runner"], r["session"]) for r in self.rows()], [("paseo", "s-1"), ("orca", "s-1")])
        self.assertEqual([r["seq"] for r in self.relay.rows(("orca", "s-1"))], [2])
        self.assertEqual(self.relay.ack(("orca", "s-1"), 2), (1, 0))
        self.assertEqual([(r["seq"], r["runner"]) for r in self.rows()], [(1, "paseo")])

    def test_ack_removes_only_that_recipients_rows(self):
        self.board[61] += [started(101, 61, "wk-61"), comment(102, "ticket.refused", 61),
                           comment(103, "reviewer.reported", 61), comment(104, "ticket.passed", 61)]
        self.poll()
        self.assertEqual(self.relay.ack(("paseo", "wk-61"), 3), (1, 0))
        self.assertEqual([(r["seq"], r["session"]) for r in self.rows()], [(1, "main-a"), (3, "main-a")])
        self.assertEqual([r["seq"] for r in self.relay.rows(MAIN_A)], [1, 3])
        self.assertEqual(self.relay.ack(MAIN_A, 1), (1, 1))
        self.assertEqual([r["seq"] for r in self.rows()], [3])


class AckByWakeTest(RelayCase):
    """A woken session knows the wake it read — ticket and event — not a sequence number."""

    def board_with_two_recipients(self):
        self.board[61] += [started(100, 61, "wk-61"), comment(101, "ticket.passed", 61),
                           comment(102, "reviewer.reported", 61)]
        self.board[62] += [comment(103, "ticket.returned", 62)]
        self.poll()

    def test_the_wake_is_acked_by_ticket_and_event_and_nobody_elses_row_goes(self):
        self.board_with_two_recipients()
        self.relay.deliver()
        self.assertEqual(self.relay.ack_wake(MAIN_A, 61, "ticket.passed"), (1, 1, 1))
        self.assertEqual(self.summary(), [(2, 61, "reviewer.reported"), (3, 62, "ticket.returned")])
        self.assertEqual(self.relay.ack_wake(("paseo", "wk-61"), 61, "reviewer.reported"), (2, 1, 0))
        self.assertEqual(self.summary(), [(3, 62, "ticket.returned")])

    def test_a_wake_for_another_recipient_is_not_acked_by_this_one(self):
        self.board_with_two_recipients()
        self.assertIsNone(self.relay.ack_wake(MAIN_A, 61, "reviewer.reported"))
        self.assertEqual(len(self.rows()), 3)

    def test_it_acks_through_the_delivered_row_that_woke_it_not_a_later_one(self):
        """The same event name twice on one ticket (a pass, a regression, a pass): the
        wake that was delivered is the one read, and a later row stays for its own wake."""
        self.board[61] += [comment(101, "ticket.passed", 61)]
        self.poll()
        self.relay.deliver()
        self.board[61] += [comment(102, "ticket.passed", 61, updated=T0 + timedelta(seconds=5))]
        self.clock.moment = T0 + timedelta(seconds=30)
        self.poll()
        self.assertEqual(self.relay.ack_wake(MAIN_A, 61, "ticket.passed"), (1, 1, 1))
        self.assertEqual(self.summary(), [(2, 61, "ticket.passed")])

    def test_a_wake_acked_already_matches_nothing_the_second_time(self):
        self.board_with_two_recipients()
        self.relay.ack_wake(MAIN_A, 61, "ticket.passed")
        self.assertIsNone(self.relay.ack_wake(MAIN_A, 61, "ticket.passed"))
        self.assertEqual(len(self.rows()), 2)

    def test_the_recovered_announcement_is_acked_by_its_name(self):
        self.poll()
        self.clock.moment = T0 + timedelta(hours=1)
        self.poll()
        self.assertEqual([r["event"] for r in self.rows()], ["relay.recovered"])
        self.assertEqual(self.relay.ack_wake(MAIN_A, None, "relay.recovered"), (1, 1, 0))


class ReadEventTest(unittest.TestCase):
    def test_prose_alone_is_no_event(self):
        self.assertIsNone(relay.read_event("ALL MET\n\nall green"))

    def test_the_block_at_the_end_is_the_event(self):
        body = 'first line\n<!-- mmw {"v":1,"event":"ticket.passed","ticket":61,"x":{"y":1}} -->'
        self.assertEqual(relay.read_event(body)["event"], "ticket.passed")

    def test_a_block_that_is_not_json_is_unreadable_not_absent(self):
        with self.assertRaises(relay.UnreadableEvent):
            relay.read_event("x\n<!-- mmw {not json} -->")

    def test_a_name_outside_subject_verb_is_unreadable(self):
        with self.assertRaises(relay.UnreadableEvent):
            relay.read_event('<!-- mmw {"v":1,"event":"ALL MET"} -->')

    def test_an_event_missing_a_field_it_requires_is_unreadable(self):
        with self.assertRaises(relay.UnreadableEvent):
            relay.read_event('<!-- mmw {"v":1,"event":"worker.started","ticket":61} -->')

    def test_what_the_scripts_write_is_what_the_relay_reads(self):
        body = relay.events.build("worker.started", ticket=61, line="worker started",
                                  session="term_7", runner="orca", **REQUIRED["worker.started"])
        self.assertEqual(relay.read_event(body)["session"], "term_7")


class DeliveryTest(RelayCase):
    def queue_two(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.board[62].append(comment(102, "ticket.returned", 62))
        self.poll()

    def test_send_carries_the_ticket_and_the_event_name_only(self):
        self.queue_two()
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-a", "#61 ticket.passed"),
                                          ("paseo", "main-a", "#62 ticket.returned")])

    def test_a_delivered_row_stays_until_acked_and_is_sent_again_only_after_a_restart(self):
        self.queue_two()
        self.relay.deliver()
        self.relay.deliver()
        self.assertEqual(len(self.send.sent), 2)
        self.assertEqual([r["seq"] for r in self.rows()], [1, 2])
        self.assertTrue(all(r["delivered"] for r in self.rows()))
        self.relay = self.fresh()
        self.relay.forget_deliveries()
        self.relay.deliver()
        self.assertEqual([t for _, _, t in self.send.sent[2:]], ["#61 ticket.passed", "#62 ticket.returned"])
        self.relay.ack(MAIN_A, 2)
        self.assertEqual(self.rows(), [])

    def test_a_row_stays_when_the_recipient_is_in_a_turn(self):
        self.queue_two()
        self.send.code = 3
        self.relay.deliver()
        self.assertEqual(len(self.send.sent), 1, "a pass stops at the first row that stays")
        self.assertEqual([(r["seq"], r["delivered"]) for r in self.rows()], [(1, None), (2, None)])
        self.send.code = 0
        self.relay.deliver()
        self.assertEqual([t for _, _, t in self.send.sent[1:]], ["#61 ticket.passed", "#62 ticket.returned"])

    def test_a_row_stays_when_the_send_was_not_made(self):
        self.queue_two()
        for code in (relay.NOT_SENT, 1):
            self.send.code = code
            self.relay.deliver()
            self.assertEqual([(r["seq"], r["delivered"]) for r in self.rows()], [(1, None), (2, None)])
        self.assertIn("which says it was not sent", self.err.getvalue())

    def test_a_wake_handed_over_unconfirmed_is_delivered_and_not_typed_again(self):
        """Answer 4: the text reached the session and no turn start was seen. Sending it
        again every cycle would type the same wake into the session again and again."""
        self.queue_two()
        self.send.code = 4
        self.relay.deliver()
        rows = self.rows()
        self.assertTrue(rows[0]["delivered"])
        self.assertTrue(rows[0].get("unconfirmed"))
        self.assertEqual(len(self.send.sent), 1, "one recipient: nothing more to it this pass")
        self.relay.deliver()
        self.relay.deliver()
        self.assertEqual([s[2] for s in self.send.sent].count(relay.wake_text(rows[0])), 1)
        self.assertEqual(len(self.rows()), 2, "delivered is not acked: the rows stay")
        self.relay.forget_deliveries()
        self.send.code = 0
        self.relay.deliver()
        self.assertEqual([s[2] for s in self.send.sent].count(relay.wake_text(rows[0])), 2,
                         "a restart sends an unconfirmed row once more, like every unacked row")

    def test_a_row_is_dropped_when_the_runner_has_no_such_session(self):
        self.queue_two()
        self.send.code = 2
        self.relay.deliver()
        self.assertEqual(self.rows(), [])
        self.assertIn("dropped row 1", self.err.getvalue())
        self.assertIn("dropped row 2", self.err.getvalue())

    def test_a_row_for_a_retired_main_session_is_dropped_without_a_send(self):
        self.queue_two()
        self.relay.open_watch({"tickets": [61, 62]}, "paseo", "main-b")
        self.board[61].append(comment(103, "ticket.refused", 61))
        self.poll()
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-b", "#61 ticket.refused")])
        self.assertEqual([(r["seq"], r["session"]) for r in self.rows()], [(3, "main-b")])
        self.assertIn("addressed to paseo session main-a, and the main agent of tickets #61, #62 is "
                      "now paseo session main-b", self.err.getvalue())

    def test_a_row_of_a_closed_watch_is_dropped_without_a_send(self):
        self.relay.open_watch({"tickets": [70]}, "paseo", "main-b")
        self.board[70] = [comment(103, "ticket.passed", 70)]
        self.queue_two()
        self.relay.close_watch("tickets:61,62")
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-b", "#70 ticket.passed")])
        self.assertIn("it belongs to the watch on tickets #61, #62, which was closed", self.err.getvalue())


class PollingTest(RelayCase):
    def test_start_reads_in_full_then_since_the_mark_less_the_overlap(self):
        self.board[61].append(comment(101, "ticket.passed", 61, updated=T0))
        self.poll()
        self.poll()
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.gh.sinces(61), [None, stamp(T0 - timedelta(seconds=120)), None])

    def test_a_restart_recovers_an_event_the_since_read_could_not_see(self):
        self.board[61].append(comment(101, "ticket.passed", 61, updated=T0))
        self.poll()
        # A comment that became visible late, stamped before the relay's mark and overlap.
        self.board[61].append(comment(90, "ticket.returned", 61, updated=T0 - timedelta(hours=1)))
        self.poll()
        self.assertEqual(self.summary(), [(1, 61, "ticket.passed")])
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.summary(), [(1, 61, "ticket.passed"), (2, 61, "ticket.returned")])

    def test_a_failed_read_is_reported_and_is_not_a_good_poll(self):
        self.poll()
        self.gh.failing.add(62)
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.clock.moment = T0 + timedelta(seconds=30)
        self.assertFalse(self.poll())
        self.assertIn("could not read #62", self.err.getvalue())
        self.assertEqual(self.summary(), [(1, 61, "ticket.passed")], "the readable ticket still queues")
        beat = json.loads((self.state / "beat.json").read_text())
        self.assertEqual(beat["at"], stamp(T0))
        self.assertIn("#62", beat["failure"])
        self.gh.failing.clear()
        self.assertTrue(self.poll())
        beat = json.loads((self.state / "beat.json").read_text())
        self.assertEqual((beat["at"], beat["failure"]), (stamp(T0 + timedelta(seconds=30)), None))

    def test_a_ticket_whose_read_on_start_failed_is_read_in_full_when_it_works(self):
        self.board[62].append(comment(102, "ticket.claimed", 62))
        self.poll()
        self.relay = self.fresh()
        self.gh.failing.add(62)
        self.poll()
        self.gh.failing.clear()
        self.poll()
        self.poll()
        # Start, the failed read after the restart, the read that worked, then since the mark.
        self.assertEqual(self.gh.sinces(62), [None, None, None, stamp(T0 - timedelta(seconds=120))])

    def test_spec_mode_watches_the_sub_issues_read_each_cycle(self):
        self.relay.close_watch(None)
        self.relay.open_watch({"spec": 50}, "paseo", "main-a")
        self.gh.spec_children[50] = [61]
        self.board[62].append(comment(102, "ticket.passed", 62))
        self.poll()
        self.assertEqual(self.rows(), [])
        self.gh.spec_children[50] = [61, 62]
        self.poll()
        self.assertEqual(self.summary(), [(1, 62, "ticket.passed")])

    def test_a_spec_whose_tickets_cannot_be_listed_is_no_good_poll_and_others_are_read(self):
        self.relay.open_watch({"spec": 50}, "paseo", "main-b")
        self.gh.spec_children[50] = [63]
        self.gh.failing.add(50)
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.assertFalse(self.poll())
        self.assertIn("could not read the tickets of spec #50", self.err.getvalue())
        self.assertEqual(self.summary(), [(1, 61, "ticket.passed")])


class RecoveryTest(RelayCase):
    def recovered_rows(self):
        return [r for r in self.rows() if r["event"] == relay.RECOVERED]

    def test_an_unattended_stretch_is_announced_once_ahead_of_the_events_it_recovered(self):
        self.poll()
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.board[62].append(comment(102, "ticket.passed", 62))
        self.clock.moment = T0 + timedelta(hours=1)
        self.relay = self.fresh()
        self.poll()
        self.assertEqual([r["event"] for r in self.rows()],
                         [relay.RECOVERED, "ticket.passed", "ticket.passed"])
        self.assertEqual(self.recovered_rows()[0]["since"], stamp(T0))
        gap = json.loads((self.state / "gap.json").read_text())
        self.assertEqual((gap["generation"], gap["since"], gap["seq"]), (1, stamp(T0), 1))
        self.relay.deliver()
        self.assertEqual(self.send.sent[0][2], f"relay.recovered since {stamp(T0)}")

    def test_a_stretch_already_announced_is_not_announced_again(self):
        self.poll()
        self.clock.moment = T0 + timedelta(hours=1)
        self.poll()
        self.relay.ack(MAIN_A, 1)
        # The good poll's beat is lost (a crash before it was written): same stretch again.
        (self.state / "beat.json").write_text(json.dumps({"at": stamp(T0), "grace": 90, "interval": 30}))
        self.clock.moment = T0 + timedelta(hours=2)
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(self.recovered_rows(), [])

    def test_a_preset_marker_for_the_stretch_means_no_announcement(self):
        (self.state / "beat.json").write_text(json.dumps({"at": stamp(T0)}))
        (self.state / "gap.json").write_text(json.dumps({"generation": 4, "since": stamp(T0), "seq": 9}))
        self.clock.moment = T0 + timedelta(hours=1)
        self.poll()
        self.assertEqual(self.recovered_rows(), [])

    def test_a_new_stretch_after_a_good_poll_is_a_new_generation(self):
        self.poll()
        self.clock.moment = T0 + timedelta(hours=1)
        self.poll()
        self.clock.moment = T0 + timedelta(hours=1, seconds=30)
        self.poll()
        self.clock.moment = T0 + timedelta(hours=3)
        self.poll()
        self.assertEqual([r["since"] for r in self.recovered_rows()],
                         [stamp(T0), stamp(T0 + timedelta(hours=1, seconds=30))])
        self.assertEqual(json.loads((self.state / "gap.json").read_text())["generation"], 2)

    def test_polls_within_grace_announce_nothing(self):
        for step in range(4):
            self.clock.moment = T0 + timedelta(seconds=30 * step)
            self.poll()
        self.assertEqual(self.recovered_rows(), [])

    def test_time_spent_delivering_is_not_an_unattended_stretch(self):
        def slow(runner, session, text):
            self.send.sent.append((runner, session, text))
            self.clock.moment += timedelta(seconds=200)
            return 0

        self.relay.send = slow
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.poll()
        self.relay.deliver()
        self.clock.moment += timedelta(seconds=30)
        with statedir.locked(self.state / "relay.lock", wait=0, purpose="test"):
            self.assertIsNone(self.relay.health(), "230s since the good poll, 200 of them delivering")
        self.poll()
        self.assertEqual(self.recovered_rows(), [])

    def test_a_delivery_pass_under_way_is_not_past_grace(self):
        self.poll()
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.poll()
        seen = []

        def slow(runner, session, text):
            self.clock.moment += timedelta(seconds=200)
            seen.append(self.relay.health())
            return 0

        self.relay.send = slow
        with statedir.locked(self.state / "relay.lock", wait=0, purpose="test"):
            self.relay.deliver()
        self.assertEqual(seen, [None])

    def test_a_failing_poll_does_not_end_the_stretch(self):
        self.poll()
        self.gh.failing.add(62)
        self.clock.moment = T0 + timedelta(hours=1)
        self.poll()
        self.assertEqual(self.recovered_rows(), [])
        self.gh.failing.clear()
        self.clock.moment = T0 + timedelta(hours=2)
        self.poll()
        self.assertEqual([r["since"] for r in self.recovered_rows()], [stamp(T0)])


class WatchesTest(RelayCase):
    """Several watches in one repository, each with its own main agent: a night on spec
    #76 (tickets #61 and #62) opened by main-a, and whatever a test opens beside it."""

    def setUp(self):
        super().setUp()
        self.relay.close_watch(None)
        self.gh.spec_children[76] = [61, 62]
        self.relay.open_watch({"spec": 76}, "paseo", "main-a")
        self.board[5] = []

    def written(self) -> bytes:
        return (self.state / "watches.json").read_bytes()

    def test_a_ticket_outside_the_night_gets_its_own_watch_and_the_nights_main_is_untouched(self):
        # Opening a watch from a second session used to re-point the running night's
        # wake-ups, findings and turn guard to that session.
        previous, _ = self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        self.assertIsNone(previous)
        self.assertEqual(self.watches(), {"spec:76": MAIN_A, "tickets:5": ("paseo", "main-b")})
        self.board[5].append(comment(101, "ticket.passed", 5))
        self.board[61].append(comment(102, "ticket.passed", 61))
        self.poll()
        self.assertEqual(self.addressed(), [(1, "ticket.passed", "main", "main-b"),
                                            (2, "ticket.passed", "main", "main-a")])
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-b", "#5 ticket.passed"),
                                          ("paseo", "main-a", "#61 ticket.passed")])

    def test_a_ticket_of_a_watched_spec_is_refused_and_nothing_is_written(self):
        before = self.written()
        with self.assertRaises(relay.Refusal) as caught:
            self.relay.open_watch({"tickets": [61]}, "paseo", "main-b")
        self.assertIn("ticket #61 was not opened: #61 is a sub-issue of spec #76, which is watched "
                      "with paseo session main-a as its main agent", str(caught.exception))
        self.assertEqual(self.written(), before)

    def test_a_spec_one_of_whose_tickets_is_watched_alone_is_refused(self):
        self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        before = self.written()
        self.gh.spec_children[80] = [4, 5]
        with self.assertRaises(relay.Refusal) as caught:
            self.relay.open_watch({"spec": 80}, "paseo", "main-c")
        self.assertIn("spec #80 was not opened: its sub-issue #5 is already watched as ticket #5, "
                      "whose main agent is paseo session main-b", str(caught.exception))
        self.assertEqual(self.written(), before)

    def test_a_ticket_is_in_one_watch_only(self):
        self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        with self.assertRaises(relay.Refusal) as caught:
            self.relay.open_watch({"tickets": [5, 6]}, "paseo", "main-c")
        self.assertIn("#5 is already watched as ticket #5", str(caught.exception))

    def test_an_overlap_that_cannot_be_checked_is_refused(self):
        self.gh.failing.add(76)
        with self.assertRaises(relay.Refusal) as caught:
            self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        self.assertIn("could not read the sub-issues of spec #76", str(caught.exception))
        self.assertEqual(self.watches(), {"spec:76": MAIN_A})

    def test_opening_a_watch_again_replaces_its_main_agent_and_no_other(self):
        self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        previous, _ = self.relay.open_watch({"spec": 76}, "orca", "term-a2")
        self.assertEqual(relay.main_of(previous), MAIN_A)
        self.assertEqual(self.watches(), {"spec:76": ("orca", "term-a2"),
                                          "tickets:5": ("paseo", "main-b")})

    def test_closing_one_watch_leaves_the_others_and_the_last_good_poll(self):
        self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        self.poll()
        (self.state / "relay.json").write_text(json.dumps({"pid": 1, "identity": "x"}))
        closed, left = self.relay.close_watch("spec:76")
        self.assertEqual((list(closed), list(left)), (["spec:76"], ["tickets:5"]))
        self.assertEqual(json.loads((self.state / "beat.json").read_text())["at"], stamp(T0))
        self.assertNotIn("ending", json.loads((self.state / "relay.json").read_text()))
        self.assertFalse(self.relay.leave_if_unwatched())
        closed, left = self.relay.close_watch("tickets:5")
        self.assertEqual((list(closed), left), (["tickets:5"], {}))
        self.assertIsNone(json.loads((self.state / "beat.json").read_text())["at"],
                          "the last watch closed forgets the last good poll")
        self.assertTrue(json.loads((self.state / "relay.json").read_text())["ending"])

    def test_the_recovered_stretch_goes_once_to_each_main_agent(self):
        self.relay.open_watch({"tickets": [5]}, "paseo", "main-b")
        self.relay.open_watch({"tickets": [7]}, "paseo", "main-b")
        self.poll()
        self.clock.moment = T0 + timedelta(hours=1)
        self.poll()
        self.assertEqual(sorted(r["session"] for r in self.rows() if r["event"] == relay.RECOVERED),
                         ["main-a", "main-b"])
        self.clock.moment = T0 + timedelta(hours=1, seconds=30)
        self.poll()
        self.assertEqual(len([r for r in self.rows() if r["event"] == relay.RECOVERED]), 2)


class SlotWakeTest(RelayCase):
    """A run that found no free product slot waits under a `worker.queued`, and a slot
    given back on any watched ticket wakes its worker."""

    def setUp(self):
        super().setUp()
        self.board[61].append(started(100, 61, "wk-61"))
        self.board[62].append(started(101, 62, "wk-62"))

    @staticmethod
    def queued(cid: int, ticket: int = 62, updated: datetime = T0) -> dict:
        return comment(cid, "worker.queued", ticket, updated=updated, reason="machine-full", run="self")

    def woken(self):
        return [(r["ticket"], r["session"]) for r in self.rows() if r["event"] == "worker.queued"]

    def test_a_slot_given_back_wakes_the_worker_waiting_for_one(self):
        self.board[62].append(self.queued(110))
        self.board[61].append(comment(120, "ticket.landed", 61))
        self.poll()
        self.assertEqual(self.addressed(), [(1, "worker.queued", "worker", "wk-62")])
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "wk-62", "#62 worker.queued")])
        # Read again, and read in full by a restarted relay: queued no second time.
        self.poll()
        self.relay = self.fresh()
        self.poll()
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.relay.ack_wake(("paseo", "wk-62"), 62, "worker.queued"), (1, 1, 0))

    def test_the_run_that_got_a_slot_ends_the_wait_and_the_next_release_wakes_nobody(self):
        self.board[62] += [self.queued(110),
                           comment(115, "ticket.checked", 62, run="self", commit="a" * 40, result="met")]
        self.board[61].append(comment(120, "ticket.landed", 61))
        self.poll()
        self.assertEqual(self.woken(), [])

    def test_a_release_older_than_the_wait_wakes_nobody(self):
        self.board[61].append(comment(105, "ticket.released", 61))
        self.board[62].append(self.queued(110))
        self.poll()
        self.assertEqual(self.woken(), [])

    def test_a_release_read_again_after_a_newer_wait_wakes_nobody(self):
        self.board[61].append(comment(105, "ticket.released", 61))
        self.board[62].append(self.queued(110))
        self.poll()
        # The next read takes the release again, in its two minutes of overlap, and the
        # wait recorded since is newer than it.
        self.clock.moment = T0 + timedelta(seconds=30)
        self.poll()
        self.assertEqual(self.woken(), [])

    def test_a_wait_and_a_later_release_meet_across_polls(self):
        self.board[62].append(self.queued(110))
        self.poll()
        self.assertEqual(self.woken(), [])
        later = T0 + timedelta(seconds=30)
        self.clock.moment = later
        self.board[61].append(comment(120, "worker.retracted", 61, updated=later))
        self.poll()
        self.assertEqual(self.woken(), [(62, "wk-62")])

    def test_an_ended_wait_read_again_in_the_overlap_stays_ended(self):
        self.board[62] += [self.queued(110),
                           comment(115, "ticket.checked", 62, run="self", commit="a" * 40, result="met")]
        self.poll()
        later = T0 + timedelta(seconds=30)
        self.clock.moment = later
        self.board[61].append(comment(120, "ticket.landed", 61, updated=later))
        self.poll()
        self.assertEqual(self.woken(), [])

    def test_a_lost_reviewer_does_not_end_the_wait(self):
        self.board[62] += [self.queued(110),
                           comment(112, "reviewer.lost", 62, session="rv-1", runner="paseo")]
        self.board[61].append(comment(120, "ticket.landed", 61))
        self.poll()
        self.assertEqual(self.addressed(), [(1, "reviewer.lost", "worker", "wk-62"),
                                            (2, "worker.queued", "worker", "wk-62")])

    def test_a_waiting_ticket_of_another_watch_is_woken(self):
        self.relay.open_watch({"tickets": [70]}, "paseo", "main-b")
        self.board[70] = [started(102, 70, "wk-70"), self.queued(110, 70)]
        self.board[61].append(comment(120, "ticket.landed", 61))
        self.poll()
        self.assertEqual(self.woken(), [(70, "wk-70")])
        self.assertEqual(self.rows()[0]["watch"], "tickets:70")

    def test_the_wait_is_kept_where_a_restart_reads_it(self):
        self.board[62].append(self.queued(110))
        self.poll()
        seen = json.loads((self.state / "seen.json").read_text())
        self.assertEqual((seen["tickets"]["62"]["waiting"], seen["tickets"]["61"]["waiting"]), (110, None))


class MainGoneTest(RelayCase):
    """A watch whose main agent's session is gone: tickets #61 and #62 opened by main-a,
    whose runner answers `stopped`, and ticket #70 opened by main-b, alive."""

    def setUp(self):
        super().setUp()
        self.relay.open_watch({"tickets": [70]}, "paseo", "main-b")
        self.ask.answers[MAIN_A] = "stopped"

    def test_the_main_agents_are_asked_every_ten_cycles(self):
        for _ in range(9):
            self.relay.cycle(30, 90)
        self.assertEqual(self.ask.calls, [])
        self.relay.cycle(30, 90)
        self.assertEqual(sorted(self.ask.calls), [MAIN_A, ("paseo", "main-b")])

    def test_a_main_agent_answered_stopped_for_an_hour_has_its_watch_closed(self):
        self.relay.check_mains()
        self.clock.moment = T0 + timedelta(seconds=3599)
        self.relay.check_mains()
        self.assertIn("tickets:61,62", self.watches())
        self.clock.moment = T0 + timedelta(seconds=3600)
        self.relay.check_mains()
        self.assertEqual(self.watches(), {"tickets:70": ("paseo", "main-b")})
        self.assertIn("closed the watch on tickets #61, #62: paseo has answered that its main "
                      "agent, session main-a, is stopped at every ask since 2026-09-10T01:00:00Z",
                      self.out.getvalue())

    def test_an_answer_other_than_stopped_starts_the_count_again(self):
        for answer in ("unknown", "alive"):
            with self.subTest(answer=answer):
                self.clock.moment = T0
                self.ask.answers[MAIN_A] = "stopped"
                self.relay.open_watch({"tickets": [61, 62]}, "paseo", "main-a")
                self.relay.check_mains()
                self.clock.moment = T0 + timedelta(seconds=1800)
                self.ask.answers[MAIN_A] = answer
                self.relay.check_mains()
                self.ask.answers[MAIN_A] = "stopped"
                self.clock.moment = T0 + timedelta(seconds=3600)
                self.relay.check_mains()
                self.clock.moment = T0 + timedelta(seconds=7199)
                self.relay.check_mains()
                self.assertIn("tickets:61,62", self.watches())
                self.clock.moment = T0 + timedelta(seconds=7200)
                self.relay.check_mains()
                self.assertNotIn("tickets:61,62", self.watches())

    def test_the_count_outlives_a_restart(self):
        self.relay.check_mains()
        self.relay = self.fresh()
        self.clock.moment = T0 + timedelta(seconds=3600)
        self.relay.check_mains()
        self.assertNotIn("tickets:61,62", self.watches())

    def test_the_last_watch_closed_ends_the_relay_and_forgets_the_last_good_poll(self):
        self.ask.answers[("paseo", "main-b")] = "stopped"
        self.poll()
        (self.state / "relay.json").write_text(json.dumps({"pid": 1, "identity": "x"}))
        self.relay.check_mains()
        self.clock.moment = T0 + timedelta(seconds=3600)
        self.relay.check_mains()
        self.assertEqual(self.watches(), {})
        self.assertIn("no watch is left, and the relay ends", self.out.getvalue())
        self.assertIsNone(json.loads((self.state / "beat.json").read_text())["at"])
        self.assertTrue(json.loads((self.state / "relay.json").read_text())["ending"])
        self.assertTrue(self.relay.leave_if_unwatched())


class HealthTest(RelayCase):
    def test_an_empty_queue_with_no_relay_running_says_so(self):
        self.assertIn("no relay is running", self.relay.health())

    def test_a_running_relay_that_polled_within_grace_is_healthy(self):
        self.poll()
        with statedir.locked(self.state / "relay.lock", wait=0, purpose="test"):
            self.assertIsNone(self.relay.health())
            self.clock.moment = T0 + timedelta(seconds=91)
            self.assertIn("past its grace of 90s", self.relay.health())


class StateDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lock = Path(self.tmp.name) / "x.lock"

    def test_one_directory_per_repository_under_mmw_home(self):
        old = os.environ.get("MMW_HOME")
        os.environ["MMW_HOME"] = self.tmp.name
        try:
            path = statedir.state_dir("Chancheuklap/Multi-Model-Workflow")
        finally:
            if old is None:
                os.environ.pop("MMW_HOME", None)
            else:
                os.environ["MMW_HOME"] = old
        self.assertEqual(path, Path(self.tmp.name) / "state" / "chancheuklap__multi-model-workflow")
        self.assertTrue(path.is_dir())
        with self.assertRaises(ValueError):
            statedir.slug("not a repo")

    def test_a_record_whose_pid_is_dead_names_nobody_and_the_lock_is_taken(self):
        child = subprocess.Popen(["sleep", "30"])
        identity = statedir.process_identity(child.pid)
        self.assertTrue(identity)
        child.kill()
        child.wait()
        self.lock.write_text(json.dumps({"pid": child.pid, "identity": identity}))
        self.assertIsNone(statedir.holder(self.lock))
        with statedir.locked(self.lock, wait=0, purpose="test"):
            self.assertEqual(statedir.holder(self.lock)["pid"], os.getpid())

    def test_a_record_whose_pid_now_belongs_to_another_process_names_nobody(self):
        self.lock.write_text(json.dumps({"pid": os.getpid(), "identity": "Mon Jan 1 00:00:00 2001"}))
        self.assertIsNone(statedir.holder(self.lock))
        with statedir.locked(self.lock, wait=0, purpose="test"):
            record = statedir.holder(self.lock)
        self.assertEqual(record["identity"], statedir.process_identity(os.getpid()))

    def test_a_holder_in_one_time_zone_is_live_to_a_reader_in_another(self):
        code = ("import sys, time; sys.path.insert(0, sys.argv[1]); import statedir\n"
                "with statedir.locked(sys.argv[2], wait=0, purpose='held under Tokyo time'):\n"
                "    print('held', flush=True); time.sleep(60)\n")
        child = subprocess.Popen([sys.executable, "-c", code, str(SCRIPTS), str(self.lock)],
                                 stdout=subprocess.PIPE, text=True,
                                 env=dict(os.environ, TZ="Asia/Tokyo"))
        self.addCleanup(lambda: (child.kill(), child.wait(), child.stdout.close()))
        self.assertEqual(child.stdout.readline().strip(), "held")
        old = os.environ.get("TZ")
        os.environ["TZ"] = "America/New_York"
        try:
            record = statedir.holder(self.lock)
        finally:
            if old is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = old
        self.assertIsNotNone(record)
        self.assertEqual(record["pid"], child.pid)

    def test_a_live_holder_is_named_excludes_others_and_frees_the_lock_when_killed(self):
        code = ("import sys, time; sys.path.insert(0, sys.argv[1]); import statedir\n"
                "with statedir.locked(sys.argv[2], wait=0, purpose='held by a test child'):\n"
                "    print('held', flush=True); time.sleep(60)\n")
        child = subprocess.Popen([sys.executable, "-c", code, str(SCRIPTS), str(self.lock)],
                                 stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: (child.kill(), child.wait(), child.stdout.close()))
        self.assertEqual(child.stdout.readline().strip(), "held")
        self.assertEqual(statedir.holder(self.lock)["pid"], child.pid)
        with self.assertRaises(statedir.LockHeld) as caught:
            with statedir.locked(self.lock, wait=0.2):
                pass
        self.assertEqual(caught.exception.record["pid"], child.pid)
        child.kill()
        child.wait()
        self.assertIsNone(statedir.holder(self.lock))
        with statedir.locked(self.lock, wait=2):
            self.assertEqual(statedir.holder(self.lock)["pid"], os.getpid())
        self.assertEqual(self.lock.read_text(), "", "a holder that lets go empties the record")


if __name__ == "__main__":
    unittest.main()
