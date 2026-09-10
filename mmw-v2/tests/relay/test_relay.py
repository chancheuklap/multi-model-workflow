"""Tests for relay.py and statedir.py: no tracker, no runner, no network.

The relay's two outsides are the board (a `Board` whose `gh` answers from a dict of
comments here) and the runner's `send` verb (a function here that records what it was
handed and answers with the exit code a test chooses). Between them runs the whole relay:
reading events, dedup, who each row is for, the queue, delivery, ack, the
unattended-stretch marker. What is asserted is what an outsider can see: the rows in the
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


def comment(cid: int, event: str | None, ticket: int | None = None,
            updated: datetime = T0, **payload) -> dict:
    """One GitHub issue comment; with an event it ends with the hidden mmw block."""
    body = "a first line for people, worded any way"
    if event:
        block = {"v": 1, "event": event, "ticket": ticket, **payload}
        body += "\n\n<!-- mmw " + json.dumps(block) + " -->"
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
            return [{"number": n} for n in self.spec_children.get(number, [])]
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


class RelayCase(unittest.TestCase):
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
        self.clock = Clock()
        self.relay = self.fresh()
        self.relay.register("paseo", "main-a")

    def restore_home(self):
        if self.old_home is None:
            os.environ.pop("MMW_HOME", None)
        else:
            os.environ["MMW_HOME"] = self.old_home

    def fresh(self):
        """A relay as a newly started process would be: same state directory, nothing in memory."""
        self.out, self.err = io.StringIO(), io.StringIO()
        return relay.Relay(self.state, relay.Board("o/r", self.gh), send=self.send,
                           clock=self.clock, out=self.out, err=self.err)

    def poll(self, tickets=(61, 62), grace=90):
        return self.relay.poll(lambda: list(tickets), 30, grace)

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
            comment(112, "ticket.passed", 61),
            comment(113, "ticket.landed", 61),
            comment(114, "worker.lost", 61),
        ]
        self.board[62] += [comment(115, "ticket.returned", 62), comment(116, "ticket.refused", 62)]
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

    def test_a_registration_made_while_the_board_is_read_addresses_the_new_rows(self):
        self.board[61].append(comment(101, "ticket.passed", 61))
        self.gh.during_read = lambda: self.relay.register("paseo", "main-b")
        self.poll()
        self.gh.during_read = None
        self.assertEqual(self.addressed(), [(1, "ticket.passed", "main", "main-b")])
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-b", "#61 ticket.passed")])

    def test_poll_with_no_registered_recipient_is_refused(self):
        (self.state / "recipient.json").unlink()
        with self.assertRaises(relay.Refusal) as caught:
            self.poll()
        self.assertIn("relay.py register", str(caught.exception))


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
        self.board[61].append(comment(101, "worker.started", 61, session="wk-a"))
        self.board[61].append(comment(102, "reviewer.reported", 61))
        self.poll()
        self.assertIn("comment 101 on #61 was not translated: its worker.started names no runner and session",
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
        self.relay.register("paseo", "s-1")
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

    def test_a_row_stays_when_the_send_answer_is_unknown(self):
        self.queue_two()
        for code in (4, 1):
            self.send.code = code
            self.relay.deliver()
            self.assertEqual([(r["seq"], r["delivered"]) for r in self.rows()], [(1, None), (2, None)])
        self.assertIn("neither delivered nor refused", self.err.getvalue())

    def test_a_row_is_dropped_when_the_runner_has_no_such_session(self):
        self.queue_two()
        self.send.code = 2
        self.relay.deliver()
        self.assertEqual(self.rows(), [])
        self.assertIn("dropped row 1", self.err.getvalue())
        self.assertIn("dropped row 2", self.err.getvalue())

    def test_a_row_for_a_retired_main_session_is_dropped_without_a_send(self):
        self.queue_two()
        self.relay.register("paseo", "main-b")
        self.board[61].append(comment(103, "ticket.refused", 61))
        self.poll()
        self.relay.deliver()
        self.assertEqual(self.send.sent, [("paseo", "main-b", "#61 ticket.refused")])
        self.assertEqual([(r["seq"], r["session"]) for r in self.rows()], [(3, "main-b")])
        self.assertIn("addressed to paseo session main-a, and the registered main agent is now paseo "
                      "session main-b", self.err.getvalue())


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
        self.gh.spec_children[50] = [61]
        self.board[62].append(comment(102, "ticket.passed", 62))
        board = relay.Board("o/r", self.gh)
        self.relay.poll(lambda: board.sub_issues(50), 30, 90)
        self.assertEqual(self.rows(), [])
        self.gh.spec_children[50] = [61, 62]
        self.relay.poll(lambda: board.sub_issues(50), 30, 90)
        self.assertEqual(self.summary(), [(1, 62, "ticket.passed")])


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
