"""Tests for status.py against fixed tickets: no tracker, no runner, no clock.

The one source status.py reads is the tracker, so the samples here are tickets in the
shape `gh issue view --json …` returns them, their comments carrying the events the
pipeline's scripts write. Everything status.py decides is a function of those, which is
why none of it needs a terminal.

    python3 -m unittest discover -s mmw-v4/tests/dispatch -p test_status.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

STATUS_PATH = Path(__file__).resolve().parents[2] / "skills" / "dispatch" / "scripts" / "status.py"
# The module under test finds events.py through `MMW_EVENTS_PY` when a caller set it, and
# `dispatch.sh` exports it to every command it runs — pointing at its own checkout's
# events.py, not this one's. Tested under it, this suite would read another version's
# vocabulary; the events.py beside the module is the one under test.
os.environ.pop("MMW_EVENTS_PY", None)
_spec = importlib.util.spec_from_file_location("status", STATUS_PATH)
status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(status)
events = status.events

AT = "2026-09-10T01:00:00Z"


def ev(name, line, ticket=61, **fields):
    """One comment as the pipeline's scripts post it."""
    return events.build(name, ticket=ticket, line=line, at=AT, **fields)


def started(ticket, session, runner="orca", kind="worker"):
    return ev(f"{kind}.started", f"{kind} started on {runner}: session {session}", ticket,
              session=session, runner=runner, machine="mac-1", into="main", host="codex", model="gpt-5.6-sol",
              effort="high",
              grade="junior-worker" if kind == "worker" else kind,
              worktree=f"/repo/.worktrees/issue-{ticket}", branch=f"issue-{ticket}",
              base="0" * 40)


def claimed(ticket):
    return ev("ticket.claimed", f"Claimed #{ticket}", ticket, login="mmw-bot")


def lost(ticket, session, runner="orca"):
    return ev("worker.lost", f"{session} is gone", ticket, session=session, runner=runner)


def passed(ticket):
    return ev("ticket.passed", "ALL MET", ticket)


def landed(ticket):
    return ev("ticket.landed", f"Landed issue-{ticket} into main", ticket)


def returned(ticket, line="HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 4 met of 5"):
    return ev("ticket.returned", line, ticket)


def bounced(ticket, reason="conflict"):
    fields = {"files": ["shared.txt"]} if reason == "conflict" else {
        "commands": [{"command": "false", "tail": "failed"}]}
    return ev("ticket.bounced", "bounced", ticket, reason=reason, commit="a" * 40,
              into="main", **fields)


def ticket(number, state="OPEN", labels=("ready-for-agent",), blockers=(),
           assignees=(), comments=(), title=None, body="", closed_blockers=()):
    """One `gh issue view --json …` answer, before status.py normalises it."""
    nodes = ([{"number": b, "state": "OPEN"} for b in blockers]
             + [{"number": b, "state": "CLOSED"} for b in closed_blockers])
    return status.normalise_ticket(number, {
        "state": state,
        "title": title if title is not None else f"ticket {number}",
        "body": body,
        "labels": [{"name": l} for l in labels],
        "assignees": [{"login": a} for a in assignees],
        "blockedBy": {"nodes": nodes},
        "comments": [{"body": c, "createdAt": "2000-01-01T00:00:00Z"} for c in comments],
    })


def rows_of(tickets, **kwargs):
    return status.build_rows(list(tickets), tickets,
                             lookup=lambda n: tickets.get(n), **kwargs)


def run_of(run, met, unmet=0, abandoned=0, result=None, ticket=61):
    """One run of the criteria as `verify-ticket.py` posts it: a `ticket.checked`."""
    total = met + unmet + abandoned
    result = result or ("met" if not unmet and not abandoned else "unmet")
    return ev("ticket.checked", f"{run} run: {met} of {total} met", ticket,
              run=run, commit="a" * 40, result=result,
              counts={"met": met, "unmet": unmet, "abandoned": abandoned, "total": total},
              failed=[f"AC{i}" for i in range(met + 1, total + 1)])


SELF_RUN_UNMET = run_of("self", met=3, unmet=2)
SELF_RUN_ALL_MET = run_of("self", met=5)
SELF_RUN_HANDOFF = run_of("self", met=3, unmet=1, abandoned=1, result="handoff")


class WhoHoldsATicket(unittest.TestCase):
    """A worker holds its ticket from its `worker.started` until an event closes it.

    Nothing here asks a runner: a worker started on Orca, on Herdr or on another
    machine holds its ticket exactly as one on Paseo does.
    """

    def row(self, *comments, **kwargs):
        return rows_of({61: ticket(61, comments=comments, **kwargs)})[0]

    def test_a_started_worker_holds_its_ticket_and_the_row_names_it(self):
        row = self.row(started(61, "term_7"))
        self.assertEqual(row["holder"]["session"], "term_7")
        self.assertEqual((row["runner"], row["session"], row["held"]),
                         ("orca", "term_7", "live"))
        self.assertEqual(status.held([row]), [row])

    def test_any_started_session_holds_the_ticket_a_reviewer_s_too(self):
        row = self.row(started(61, "rev_1", kind="reviewer"))
        self.assertEqual(row["holder"]["session"], "rev_1")

    def test_each_closing_event_ends_the_hold(self):
        closers = {
            "worker.retracted": ev("worker.retracted", "retracted", session="term_7",
                                   runner="orca"),
            "worker.lost": lost(61, "term_7"),
            "ticket.landed": landed(61),
            "ticket.released": ev("ticket.released", "released", reason="worker-lost"),
            "spec.suspended": ev("spec.suspended", "NIGHT SUSPENDED #76"),
            "ticket.returned": returned(61),
            "worker.replaced": ev("worker.replaced", "replaced", session="term_7",
                                  runner="orca"),
        }
        for name, closer in closers.items():
            with self.subTest(closer=name):
                row = self.row(started(61, "term_7"), closer)
                self.assertIsNone(row["holder"], name)

    def test_a_loss_of_another_session_leaves_this_one_holding(self):
        row = self.row(started(61, "term_7"), lost(61, "term_2"))
        self.assertEqual(row["holder"]["session"], "term_7")

    def test_a_claim_with_no_start_recorded_holds_the_ticket(self):
        row = self.row(claimed(61), assignees=("mmw-bot",))
        self.assertTrue(row["holder"]["claim"])
        self.assertEqual(status.frontier([row]), [])
        self.assertIn("ticket.claimed", status.why_not_on_frontier(row))

    def test_a_pass_on_a_ticket_still_open_does_not_end_the_hold(self):
        """The close after the pass failed: the worker is retrying on an open ticket."""
        row = self.row(started(61, "term_7"), claimed(61), passed(61))
        self.assertEqual(row["holder"]["session"], "term_7")

    def test_a_resumed_worker_holds_again(self):
        row = self.row(started(61, "term_7"), returned(61),
                       ev("worker.resumed", "resumed", session="term_7", runner="orca"))
        self.assertEqual(row["holder"]["session"], "term_7")

    def test_labels_never_hide_a_hold(self):
        for labels in (("ready-for-agent", "needs-triage"), ("needs-triage",), ()):
            with self.subTest(labels=labels):
                row = self.row(started(61, "term_7"), labels=labels)
                self.assertEqual(row["holder"]["session"], "term_7")

    def test_two_live_workers_are_named_on_the_note(self):
        row = self.row(started(61, "term_7"), started(61, "term_8"))
        self.assertIn("term_7", row["note"])
        self.assertIn("term_8", row["note"])


class SummaryCloseoutGate(unittest.TestCase):
    """The summary gate names only conditions that make closeout unsafe."""

    def problems(self, tickets):
        return status.closeout_problems(rows_of(tickets), tickets)

    def test_refuses_a_live_session(self):
        tickets = {61: ticket(61, comments=(started(61, "term_7"),))}
        problems = self.problems(tickets)
        self.assertEqual([p.split()[0] for p in problems], ["#61"])
        self.assertIn("term_7", problems[0])

    def test_refuses_a_passed_ticket_that_has_not_landed(self):
        tickets = {61: ticket(61, state="CLOSED", labels=(), comments=(passed(61),))}
        self.assertEqual([p.split()[0] for p in self.problems(tickets)], ["#61"])

    def test_refuses_an_unreadable_ticket(self):
        broken = ticket(61)
        broken["unread_raw"] = True
        tickets = {61: broken}
        self.assertEqual([p.split()[0] for p in self.problems(tickets)], ["#61"])

    def test_refuses_a_dispatchable_frontier_ticket(self):
        tickets = {61: ticket(61)}
        self.assertEqual([p.split()[0] for p in self.problems(tickets)], ["#61"])

    def test_allows_human_acceptance_triage_and_blocked_tickets(self):
        tickets = {
            61: ticket(61, labels=("ready-for-human",)),
            62: ticket(62, labels=("needs-triage",)),
            63: ticket(63, blockers=(90,)),
        }
        self.assertEqual(self.problems(tickets), [])


class ReverifyGate(unittest.TestCase):
    """Every landed ticket's newest reverify has to be green on the commit summary checks."""

    TIP = "b" * 40

    def landed_with(self, number, *runs):
        return ticket(number, state="CLOSED", labels=(),
                      comments=(passed(number), landed(number), *runs))

    def reverify(self, number, commit, result="met"):
        return ev("ticket.checked", "Reverify", number, actor="main", stage="regress",
                  run="reverify", commit=commit, result=result,
                  failed=["AC2"] if result == "unmet" else [])

    def test_green_on_the_tip_counts_and_anything_else_is_named(self):
        tickets = {
            61: self.landed_with(61, self.reverify(61, self.TIP)),
            62: self.landed_with(62, self.reverify(62, "a" * 40)),
            63: self.landed_with(63, self.reverify(63, self.TIP, "unmet")),
            64: self.landed_with(64),
            65: ticket(65, labels=("ready-for-human",)),
        }
        green, problems = status.reverify_problems(tickets, self.TIP)
        self.assertEqual(green, 1)
        self.assertEqual([p.split(" ")[0] for p in problems], ["#62", "#63", "#64"])
        self.assertIn("AC2", problems[1])

    def test_a_ticket_reverify_handed_back_to_triage_does_not_hold_the_night(self):
        regressed = ev("ticket.regressed", "Reverify failed: AC2; reopened for triage", 62,
                       commit=self.TIP)
        tickets = {
            61: self.landed_with(61, self.reverify(61, self.TIP)),
            62: ticket(62, labels=("needs-triage",),
                       comments=(passed(62), landed(62),
                                 self.reverify(62, self.TIP, "unmet"), regressed)),
            63: ticket(63, labels=("needs-triage",),
                       comments=(passed(63), landed(63),
                                 self.reverify(63, "a" * 40, "unmet"),
                                 ev("ticket.regressed", "Reverify failed", 63,
                                    commit="a" * 40))),
        }
        green, problems = status.reverify_problems(tickets, self.TIP)
        self.assertEqual(green, 1)
        self.assertEqual([p.split(" ")[0] for p in problems], ["#63"])
        body = status.summary(rows_of(tickets), opened="2026-08-30T00:00:00Z",
                              now=datetime(2026, 8, 31, 2, 14)).splitlines()
        handed = [l for l in body if l.startswith("Handed back to needs-triage: ")]
        self.assertEqual(len(handed), 1)
        self.assertIn("#62 ", handed[0])


class NamingWhatHoldsIt(unittest.TestCase):
    """How a ticket's live sessions are named where a plan says why it cannot start.

    A non-worker session was once printed as a worker because the newest live session
    was given that name regardless of its kind. `retract` takes back a worker's start;
    run on that advice it stops a session reading a diff, and that round's work goes
    with it.
    """

    def row(self, *comments, **kwargs):
        return rows_of({61: ticket(61, comments=comments, **kwargs)})[0]

    def test_a_live_reviewer_is_named_a_reviewer_beside_its_worker(self):
        row = self.row(started(61, "term_7"), started(61, "rv_1", kind="reviewer"))
        why = status.why_not_on_frontier(row)
        self.assertIn("worker term_7", why)
        self.assertIn("reviewer rv_1", why)
        self.assertNotIn("worker rv_1", why)

    def test_the_retract_advice_names_the_one_live_worker(self):
        row = self.row(started(61, "term_7"))
        why = status.why_not_on_frontier(row)
        self.assertIn("worker term_7", why)
        self.assertIn("retract", why)

    def test_two_live_workers_are_both_named_and_neither_is_retracted(self):
        row = self.row(started(61, "term_7"), started(61, "term_8"))
        why = status.why_not_on_frontier(row)
        self.assertIn("worker term_7", why)
        self.assertIn("worker term_8", why)
        self.assertNotIn("retract", why)


class Rows(unittest.TestCase):
    """The table's own contents, off the tickets and their events."""

    def rows(self):
        tickets = {
            61: ticket(61, comments=[started(61, "term_1"), SELF_RUN_UNMET]),
            62: ticket(62, comments=[SELF_RUN_UNMET]),
            64: ticket(64, state="CLOSED", labels=(),
                       comments=[SELF_RUN_ALL_MET, passed(64)]),
            65: ticket(65, blockers=(62,)),
        }
        return rows_of(tickets)

    def row(self, number):
        return next(r for r in self.rows() if r["ticket"] == number)

    def test_a_live_worker_shows_its_runner_session_and_no_note(self):
        row = self.row(61)
        self.assertEqual((row["runner"], row["session"], row["held"], row["since"]),
                         ("orca", "term_1", "live", AT))
        self.assertEqual(row["phase"], "ticket.checked")
        self.assertEqual(row["note"], "")

    def test_a_closed_ticket_names_its_result(self):
        row = self.row(64)
        self.assertEqual((row["runner"], row["phase"], row["ac"]), ("-", "ticket.passed", "5/5"))
        self.assertEqual(row["note"], "ALL MET")

    def test_a_blocked_ticket_names_what_it_waits_on(self):
        self.assertIn("#62", self.row(65)["note"])

    def test_the_frontier_leaves_out_what_is_held_or_blocked(self):
        self.assertEqual([r["ticket"] for r in status.frontier(self.rows())], [62])

    def test_the_frontier_takes_a_ready_ticket_with_no_worker_and_no_blocker(self):
        tickets = {70: ticket(70), 71: ticket(71, assignees=("someone",)),
                   72: ticket(72, labels=("needs-triage",))}
        self.assertEqual([r["ticket"] for r in status.frontier(rows_of(tickets))], [70])


class BlockersLetGoWhenTheyLand(unittest.TestCase):
    """A ticket is cut from the base branch, so a blocker that closed with its branch not
    yet merged has left nothing there to build on. The unlock is `ticket.landed`."""

    def frontier(self, blocker, **kwargs):
        tickets = {60: blocker, 61: ticket(61, closed_blockers=(60,))}
        return [r["ticket"] for r in status.frontier(rows_of(tickets, **kwargs))]

    def test_a_blocker_that_passed_and_has_not_landed_still_blocks(self):
        blocker = ticket(60, state="CLOSED", labels=(), comments=[passed(60)])
        self.assertEqual(self.frontier(blocker), [])
        row = rows_of({60: blocker, 61: ticket(61, closed_blockers=(60,))})[1]
        self.assertIn("#60", row["note"])

    def test_a_landed_blocker_lets_go(self):
        blocker = ticket(60, state="CLOSED", labels=(), comments=[passed(60), landed(60)])
        self.assertEqual(self.frontier(blocker), [61])


    def test_a_blocker_closed_without_a_pass_lets_go_on_closing(self):
        blocker = ticket(60, state="CLOSED", labels=(), comments=["voided by a person"])
        self.assertEqual(self.frontier(blocker), [61])

    def test_a_regressed_blocker_blocks_again_once_it_passes_until_it_lands_again(self):
        blocker = ticket(60, state="CLOSED", labels=(), comments=[
            passed(60), landed(60),
            ev("ticket.regressed", "Reverify failed", 60, commit="a" * 40),
            passed(60)])
        self.assertEqual(self.frontier(blocker), [])

    def test_a_blocker_outside_the_batch_is_read_from_the_tracker(self):
        outside = ticket(90, state="CLOSED", labels=(), comments=[passed(90)])
        tickets = {61: ticket(61, closed_blockers=(90,))}
        rows = status.build_rows([61], tickets, lookup=lambda n: {90: outside}[n])
        self.assertEqual(rows[0]["blockers"], [90])


class UnreadableEvents(unittest.TestCase):
    """A comment whose event block cannot be read is a question left unanswered."""

    BROKEN = "worker started\n\n<!-- mmw {\"v\":1,\"event\":\"worker.started\" -->"

    def test_a_ticket_with_an_unreadable_event_is_off_the_frontier_and_says_why(self):
        rows = rows_of({61: ticket(61, comments=[self.BROKEN])})
        self.assertEqual(status.frontier(rows), [])

    def test_a_blocker_whose_events_cannot_be_read_blocks(self):
        tickets = {60: ticket(60, state="CLOSED", labels=(), comments=[self.BROKEN]),
                   61: ticket(61, closed_blockers=(60,))}
        self.assertEqual(status.frontier(rows_of(tickets)), [])


class TicketReading(unittest.TestCase):
    """The criteria counts read off the newest `ticket.checked` of a criteria run."""

    def test_the_counts_come_off_the_newest_run(self):
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_UNMET])), "3/5")
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_ALL_MET])), "5/5")

    def test_a_handoff_run_counts_the_abandoned_criteria_too(self):
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_HANDOFF])), "3/5")

    def test_a_ticket_with_no_run_has_no_counts(self):
        self.assertEqual(status.counted_ac(ticket(62)), "-")

    def test_the_newest_run_wins_whichever_run_it_is(self):
        comments = [SELF_RUN_UNMET, passed(62), SELF_RUN_ALL_MET]
        self.assertEqual(status.counted_ac(ticket(62, comments=comments)), "5/5")
        comments = [SELF_RUN_ALL_MET, run_of("reverify", met=4, unmet=1)]
        self.assertEqual(status.counted_ac(ticket(62, comments=comments)), "4/5")

    def test_an_old_baseline_event_is_not_the_criteria_count(self):
        baseline = ev("ticket.checked", "Baseline: 0/3 met", 62, run="baseline",
                      commit="a" * 40, result="unmet",
                      counts={"met": 0, "unmet": 3, "abandoned": 0, "total": 3})
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_ALL_MET, baseline])),
                         "5/5")

    def test_a_typed_run_comment_gives_no_counts(self):
        """The old run comment carried gate-check's summary on its second line. A first
        line is read by nothing now, so the same words typed by hand count nothing."""
        typed = "self-run\nALL MET (5 met)\n\n- [x] AC1: one\n  EVIDENCE: exit=0"
        self.assertEqual(status.counted_ac(ticket(62, comments=[typed])), "-")


class PhaseFromEvents(unittest.TestCase):
    """`phase` is the newest event's name, and a first line decides nothing."""

    def test_the_newest_event_is_the_phase(self):
        t = ticket(61, comments=[started(61, "term_1"), SELF_RUN_UNMET,
                                 ev("worker.decided", "DECISIONS")])
        self.assertEqual(status.phase_of(t), "worker.decided")

    def test_a_comment_that_only_looks_like_a_result_is_prose(self):
        t = ticket(61, comments=["ALL MET\nBranch: x", "VERDICT " + "a" * 40 + " by x — ok"])
        self.assertEqual(status.phase_of(t), "-")
        self.assertFalse(t["fold"]["passed"])

    def test_a_closed_ticket_with_no_event_still_says_closed(self):
        self.assertEqual(status.phase_of(ticket(61, state="CLOSED", labels=())), "closed")


class Table(unittest.TestCase):
    """The one screen `--table` prints."""

    def table(self, spec=60):
        tickets = {61: ticket(61, comments=[started(61, "term_1"), SELF_RUN_UNMET]),
                   65: ticket(65, blockers=(61,))}
        return status.render_table(rows_of(tickets), spec, datetime(2026, 8, 31, 2, 14))

    def test_the_first_line_names_the_time_the_spec_the_count_and_the_live_workers(self):
        self.assertEqual(self.table().splitlines()[0],
                         "mmw status · 02:14 · spec #60 · 2 tickets · 1 live")

    def test_without_a_spec_the_first_line_leaves_that_field_out(self):
        self.assertEqual(self.table(spec=None).splitlines()[0],
                         "mmw status · 02:14 · 2 tickets · 1 live")

    def test_the_columns(self):
        self.assertEqual(self.table().splitlines()[2].split(),
                         ["ticket", "runner", "session", "worker", "since",
                          "phase", "ac", "note"])

    def test_one_line_per_ticket_in_ticket_order(self):
        body = self.table().splitlines()[3:]
        self.assertEqual([l.split()[0] for l in body], ["#61", "#65"])
        self.assertEqual(body[0].split()[1:5], ["orca", "term_1", "live", AT])
        self.assertIn("ticket.checked", body[0])
        self.assertIn("#61", body[1])


class WorkerGrades(unittest.TestCase):
    """The lines `--worker-grades` prints for `dispatch.sh check` to read."""

    def setUp(self):
        self.saved = status.sub_issues, status.read_ticket
        self.tickets = {
            61: ticket(61, labels=("ready-for-agent", "junior-worker")),
            62: ticket(62, labels=("ready-for-agent", "senior-worker", "junior-worker"),
                       blockers=(61,)),
            63: ticket(63, labels=("ready-for-agent",)),
            64: ticket(64, labels=("needs-triage", "principal-worker")),
            65: ticket(65, state="CLOSED", labels=("principal-worker",)),
        }
        status.sub_issues = lambda spec: list(self.tickets)
        status.read_ticket = lambda n: self.tickets[n]

    def tearDown(self):
        status.sub_issues, status.read_ticket = self.saved

    def test_one_line_per_open_ticket_in_the_agent_queue_blocked_or_not(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(status.worker_grades(76), 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "BATCH 61",
            "GRADE 61 junior-worker",
            "BATCH 62",
            "GRADE 62 junior-worker senior-worker",
            "BATCH 63",
            "GRADE 63",
            "BATCH 64",
            "BATCH 65",
        ])


class Plans(unittest.TestCase):
    """The plan forms read the batch through `sub_issues` and `read_ticket`."""

    LOGIN = "mmw-bot"

    def setUp(self):
        self.saved = (status.sub_issues, status.read_ticket, status.own_login)
        self.home = tempfile.TemporaryDirectory()
        self.saved_home = os.environ.get("MMW_HOME")
        os.environ["MMW_HOME"] = self.home.name
        self.models_path = Path(self.home.name) / "models.json"
        self.models_path.write_text(json.dumps({
            "version": 1, "runner": "orca", "rows": {
                role: {"host": "claude", "model": "opus 5", "effort": "high"}
                for role in [row["name"] for row in json.loads(
                    (STATUS_PATH.parent.parent / "roles.json").read_text())["roles"]]
            },
        }))
        self.tickets = {}
        status.sub_issues = lambda spec: list(self.tickets)
        status.read_ticket = lambda n: self.tickets[n]
        status.own_login = lambda: ""

    def tearDown(self):
        (status.sub_issues, status.read_ticket, status.own_login) = self.saved
        if self.saved_home is None:
            os.environ.pop("MMW_HOME", None)
        else:
            os.environ["MMW_HOME"] = self.saved_home
        self.home.cleanup()

    def closed(self, number, at, *comments):
        t = ticket(number, state="CLOSED", labels=(), comments=comments)
        t["closed_at"] = at
        return t

    def run_form(self, form, *args, exit_code=0):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(form(*args), exit_code)
        return out.getvalue().splitlines(), err.getvalue().splitlines()


class AdvancePlan(Plans):
    """The three kinds of line `--advance-plan` prints, and what it says when it prints none."""

    def plan(self, spec=76, *, exit_code=0):
        return self.run_form(status.advance_plan, spec, exit_code=exit_code)

    def test_without_max_workers_three_tickets_are_dispatched(self):
        self.tickets = {n: ticket(n) for n in (65, 63, 61, 64, 62)}
        self.assertEqual(self.plan()[0], ["DISPATCH 61", "DISPATCH 62", "DISPATCH 63"])

    def test_a_full_night_dispatches_nothing_and_names_each_waiting_ticket(self):
        self.tickets = {
            60: ticket(60, comments=(started(60, "w60"),)),
            61: ticket(61, comments=(started(61, "w61"),)),
            62: ticket(62, comments=(started(62, "w62"),)),
            63: ticket(63), 64: ticket(64),
        }
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertEqual(len(err), 2)
        for number, line in zip((63, 64), err):
            with self.subTest(ticket=number):
                self.assertIn(f"#{number}", line)
                self.assertIn("max_workers", line)
                self.assertRegex(line, r"\b3\b")
                for held_number in (60, 61, 62):
                    self.assertIn(f"#{held_number}", line)

    def test_a_passed_unlanded_ticket_holds_a_place(self):
        self.tickets = {
            60: self.closed(60, AT, started(60, "w60"), passed(60)),
            61: ticket(61), 62: ticket(62), 63: ticket(63),
        }
        self.assertEqual(self.plan()[0], ["MERGE 60", "DISPATCH 61", "DISPATCH 62"])

    def test_a_claim_no_session_has_taken_over_holds_a_place(self):
        self.tickets = {
            60: ticket(60, comments=(claimed(60),)),
            61: ticket(61), 62: ticket(62), 63: ticket(63),
        }
        self.assertEqual(self.plan()[0], ["DISPATCH 61", "DISPATCH 62"])

    def test_a_ticket_under_review_holds_one_place(self):
        self.tickets = {
            60: ticket(60, comments=(started(60, "w60"),
                                     started(60, "r60", kind="reviewer"))),
            61: ticket(61), 62: ticket(62), 63: ticket(63),
        }
        self.assertEqual(self.plan()[0], ["DISPATCH 61", "DISPATCH 62"])

    def test_merge_and_release_are_not_capped(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {
            60: self.closed(60, AT, started(60, "w60"), passed(60)),
            61: ticket(61, comments=(started(61, "w61"),)),
            62: ticket(62, comments=(started(62, "w62"),)),
            63: ticket(63, assignees=(self.LOGIN,),
                       comments=(started(63, "w63"), lost(63, "w63"))),
        }
        self.assertEqual(self.plan()[0], ["MERGE 60", "RELEASE 63"])

    def test_an_invalid_max_workers_dispatches_nothing_and_still_merges(self):
        self.tickets = {60: self.closed(60, AT, passed(60)), 61: ticket(61)}
        config = json.loads(self.models_path.read_text())
        for value in (0, -1, True, "3", 2.5, None):
            with self.subTest(max_workers=value):
                self.models_path.write_text(json.dumps({**config, "max_workers": value}))
                out, err = self.plan(exit_code=3)
                self.assertEqual(out, ["MERGE 60"])
                self.assertEqual(len(err), 1)
                self.assertIn(str(self.models_path), err[0])
                self.assertIn("max_workers", err[0])
                self.assertIn("models.py config set max_workers <n>", err[0])

    def test_an_unreadable_models_json_dispatches_nothing_and_still_merges(self):
        self.tickets = {60: self.closed(60, AT, passed(60)), 61: ticket(61)}
        for contents in (None, "{broken", "[]"):
            with self.subTest(contents=contents):
                if contents is None:
                    self.models_path.unlink()
                else:
                    self.models_path.write_text(contents)
                out, err = self.plan(exit_code=3)
                self.assertEqual(out, ["MERGE 60"])
                self.assertEqual(len(err), 1)
                self.assertIn(str(self.models_path), err[0])

    def test_unreadable_occupancy_withholds_dispatch_but_still_merges_and_releases(self):
        status.own_login = lambda: self.LOGIN
        config = json.loads(self.models_path.read_text())
        self.models_path.write_text(json.dumps({**config, "max_workers": 2}))
        self.tickets = {
            60: self.closed(60, AT, passed(60)),
            62: ticket(62), 63: ticket(63),
            64: ticket(64, assignees=(self.LOGIN,),
                       comments=(started(64, "w64"), lost(64, "w64"))),
        }
        for unread in (status.normalise_ticket(61, {}),
                       ticket(61, comments=(UnreadableEvents.BROKEN,))):
            with self.subTest(reason=status.unreadable_reason(unread)):
                self.tickets[61] = unread
                out, err = self.plan()
                self.assertEqual(out, ["MERGE 60", "RELEASE 64"])
                for number in (62, 63):
                    line = next(line for line in err if f"#{number}" in line)
                    self.assertIn("#61", line)
                    self.assertIn("max_workers", line)
                    self.assertRegex(line, r"\b2\b")
        self.tickets[61] = ticket(61, comments=(started(61, "w61"),))
        self.assertEqual(self.plan()[0], ["MERGE 60", "RELEASE 64", "DISPATCH 62"])

    def test_broken_roles_only_prevents_dispatch_not_other_plan_forms(self):
        scripts = Path(self.home.name) / "skills" / "dispatch" / "scripts"
        shutil.copytree(STATUS_PATH.parent, scripts)
        shutil.copytree(STATUS_PATH.parents[2] / "verify-ticket" / "scripts",
                        scripts.parents[1] / "verify-ticket" / "scripts")
        roles_path = scripts.parent / "roles.json"
        program = '''
import importlib.util, sys
spec = importlib.util.spec_from_file_location("isolated_status", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.sub_issues = lambda spec: [60, 61]
module.own_login = lambda: ""
module.read_ticket = lambda n: module.normalise_ticket(n, {
    "state": "CLOSED" if n == 60 else "OPEN",
    "labels": [{"name": "ready-for-agent"}],
    "comments": [{"body": module.events.build("ticket.passed", ticket=60,
                  line="ALL MET")}] if n == 60 else []})
sys.exit(module.main([sys.argv[2], "76" if sys.argv[2] == "--advance-plan" else "61"]))
'''
        for contents in (None, "{broken"):
            with self.subTest(roles=contents):
                if contents is None:
                    roles_path.unlink(missing_ok=True)
                else:
                    roles_path.write_text(contents)
                for form, expected in (("--land-plan", "HOLD 61 it is open with no outcome on it\n"),
                                       ("--advance-plan", "MERGE 60\n")):
                    run = subprocess.run(
                        [sys.executable, "-c", program, str(scripts / "status.py"), form],
                        capture_output=True, text=True)
                    self.assertEqual(run.returncode, 3 if form == "--advance-plan" else 0, run.stderr)
                    self.assertEqual(run.stdout, expected)
                    if form == "--advance-plan":
                        self.assertIn(str((scripts / "models.py").resolve()), run.stderr)

    def test_merges_passed_tickets_in_closing_order_then_dispatches_the_frontier(self):
        self.tickets = {
            61: self.closed(61, "2026-08-31T02:00:00Z", passed(61)),
            62: self.closed(62, "2026-08-31T01:00:00Z", passed(62)),
            63: self.closed(63, "2026-08-31T03:00:00Z", returned(63)),
            70: ticket(70),
        }
        self.assertEqual(self.plan()[0], ["MERGE 62", "MERGE 61", "DISPATCH 70"])

    def test_a_landed_ticket_is_not_merged_again(self):
        self.tickets = {61: self.closed(61, "2026-08-31T01:00:00Z", passed(61), landed(61))}
        self.assertEqual(self.plan(), ([], []))

    def test_a_ticket_blocked_by_one_this_plan_merges_waits_for_its_landing(self):
        """The plan reads the tracker as it stands: the merge unblocks nothing until its
        ticket.landed is written, which `dispatch.sh` reads in its second plan."""
        self.tickets = {60: self.closed(60, "2026-08-31T01:00:00Z", passed(60)),
                        61: ticket(61, closed_blockers=(60,))}
        self.assertEqual(self.plan()[0], ["MERGE 60"])
        self.tickets[60] = self.closed(60, "2026-08-31T01:00:00Z", passed(60), landed(60))
        self.assertEqual(self.plan()[0], ["DISPATCH 61"])

    def test_a_ticket_whose_events_cannot_be_read_is_never_merged(self):
        self.tickets = {61: self.closed(61, "2026-08-31T01:00:00Z", passed(61),
                                        UnreadableEvents.BROKEN)}
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("#61", "\n".join(err))

    def test_a_claim_with_a_live_worker_on_its_events_is_kept_on_any_runner(self):
        """2026-09-10: a worker on Orca, invisible to Paseo, lost its claim and got a
        second worker beside it. The ticket's own events are what say it is held."""
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,),
                                   comments=[started(61, "term_7", runner="orca")])}
        out, err = self.plan()
        self.assertEqual(out, [])
        joined = "\n".join(err)
        self.assertIn("term_7", joined)
        self.assertIn("orca", joined)

    def test_a_claim_a_live_reviewer_keeps_says_it_is_the_reviewer(self):
        """The claim is kept because a session still holds the ticket; which kind of
        session that is decides whether `retract` is the answer, so the line says it."""
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,), comments=[
            started(61, "term_7"), claimed(61), started(61, "rv_1", kind="reviewer"),
            ev("worker.retracted", "retracted", session="term_7", runner="orca")])}
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("rv_1", "\n".join(err))

    def test_a_claim_no_event_ever_showed_held_is_kept(self):
        """Only an event that ended a hold says a claim's worker is gone."""
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,))}
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("#61", "\n".join(err))

    def test_a_finished_reviewer_does_not_keep_a_lost_or_retracted_workers_ticket(self):
        # The reviewer's report ended its own hold, so when the worker goes — lost, or
        # retracted — nothing holds the ticket any more, and advance starts it again.
        for ending in (lost(61, "term_7"),
                       ev("worker.retracted", "retracted", session="term_7", runner="orca")):
            with self.subTest(ending=ending.split("\n")[0]):
                status.own_login = lambda: self.LOGIN
                self.tickets = {61: ticket(61, assignees=(self.LOGIN,), comments=[
                    started(61, "term_7"), claimed(61),
                    started(61, "rv_1", kind="reviewer"),
                    ev("reviewer.reported", "REVIEW", base="0" * 40, head="1" * 40),
                    ending])}
                self.assertEqual(self.plan()[0], ["RELEASE 61", "DISPATCH 61"])

    def test_a_claim_made_before_its_start_was_recorded_is_kept(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,), comments=[claimed(61)])}
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("ticket.claimed", "\n".join(err))

    def test_a_claim_on_a_ticket_whose_events_cannot_be_read_is_kept(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,),
                                   comments=[UnreadableEvents.BROKEN])}
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("#61", "\n".join(err))

    def test_with_no_login_to_compare_against_nothing_is_released(self):
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,))}
        self.assertEqual(self.plan()[0], [])

    def test_an_empty_frontier_names_every_queued_ticket_and_its_condition(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {
            61: ticket(61, assignees=("alice",)),
            62: ticket(62, blockers=(61,)),
            63: ticket(63, comments=[started(63, "term_3")]),
            64: ticket(64, labels=("needs-triage",)),
        }
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertEqual(len(err), 4, err)
        self.assertIn("#76", err[0])
        self.assertEqual(err[1].split()[0], "#61")
        self.assertIn("alice", err[1])
        self.assertEqual(err[2].split()[0], "#62")
        self.assertEqual(err[3].split()[0], "#63")
        self.assertIn("term_3", err[3])

    def test_a_batch_with_nothing_left_in_the_queue_says_nothing(self):
        self.tickets = {61: ticket(61, state="CLOSED", labels=())}
        self.assertEqual(self.plan(), ([], []))


class ReverifyPlan(Plans):
    """`--reverify-plan`: the landed tickets, which are the ones on the base branch."""

    def test_only_landed_passes_are_run_again_and_the_rest_are_named(self):
        self.tickets = {
            61: self.closed(61, "2026-08-31T01:00:00Z", passed(61), landed(61)),
            62: self.closed(62, "2026-08-31T02:00:00Z", passed(62)),
            63: self.closed(63, "2026-08-31T03:00:00Z", returned(63)),
        }
        out, err = self.run_form(status.reverify_plan, 76)
        self.assertEqual(out, ["REVERIFY 61"])
        self.assertIn("#62", "\n".join(err))

    def test_a_ticket_an_earlier_reverify_reopened_is_run_again_to_recover_it(self):
        regressed = ev("ticket.regressed", "Reverify failed", 62, commit="a" * 40)
        self.tickets = {
            61: self.closed(61, "2026-08-31T01:00:00Z", passed(61), landed(61)),
            62: ticket(62, labels=("needs-triage",),
                       comments=[passed(62), landed(62), regressed]),
        }
        out, _ = self.run_form(status.reverify_plan, 76)
        self.assertEqual(sorted(out), ["RECOVER 62", "REVERIFY 61"])

    def test_a_reopened_ticket_triage_has_handed_on_is_not_run_again(self):
        regressed = ev("ticket.regressed", "Reverify failed", 62, commit="a" * 40)
        self.tickets = {62: ticket(62, labels=("ready-for-agent",),
                                   comments=[passed(62), landed(62), regressed])}
        out, _ = self.run_form(status.reverify_plan, 76)
        self.assertEqual(out, [])

    def test_a_ticket_open_for_its_first_run_is_not_a_recovery(self):
        self.tickets = {62: ticket(62, labels=("needs-triage",), comments=[])}
        out, _ = self.run_form(status.reverify_plan, 76)
        self.assertEqual(out, [])


class LandPlan(Plans):
    """`--land-plan`: a handed-back ticket keeps its branch to itself until it passes."""

    def test_a_handed_back_ticket_is_not_merged(self):
        self.tickets = {1: ticket(1, labels=("needs-triage",), comments=[returned(1)])}
        rows, _ = self.run_form(status.land_plan, [1])
        self.assertEqual([l for l in rows if l.startswith("MERGE")], [])
        self.assertTrue([l for l in rows if l.startswith("NOTHING 1")], rows)

    def test_a_passed_ticket_merges_and_a_landed_one_does_not(self):
        self.tickets = {1: self.closed(1, "x", passed(1)),
                        2: self.closed(2, "x", passed(2), landed(2))}
        rows, _ = self.run_form(status.land_plan, [1, 2])
        self.assertEqual([l for l in rows if l.startswith("MERGE")], ["MERGE 1"])

    def test_a_ticket_whose_events_cannot_be_read_is_held(self):
        self.tickets = {1: self.closed(1, "x", UnreadableEvents.BROKEN)}
        rows, _ = self.run_form(status.land_plan, [1])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].startswith("HOLD 1"), rows)


def child(number, *, state="CLOSED", title=None, kind=None, resolution=None):
    c = ticket(number, state=state, labels=("needs-triage",),
               title=title if title is not None else f"child {number}")
    if kind:
        c["kind"] = kind
    if resolution:
        c["resolution"] = resolution
    c["created"] = "2026-08-31T01:00:00Z"
    return c


class Summary(unittest.TestCase):
    """`--summary` prints the night lines; it does not post them."""

    def test_the_summary_keeps_closed_handed_and_waiting_and_lists_sub_issues_by_title(self):
        tickets = {
            61: ticket(61, state="CLOSED", labels=(), comments=[passed(61), landed(61)]),
            62: ticket(62, labels=("needs-triage",), comments=[returned(62)]),
            63: ticket(63, blockers=(62,)),
            64: ticket(64, labels=("needs-triage",), comments=["fresh"]),
        }
        for number, when in ((61, "2026-08-29"), (62, "2026-08-29"),
                             (63, "2026-08-29"), (64, "2026-08-31")):
            tickets[number]["created"] = when + "T00:00:00Z"
        tickets[61]["closed_at"] = "2026-08-31T02:00:00Z"
        body = status.summary(rows_of(tickets), opened="2026-08-30T00:00:00Z",
                              now=datetime(2026, 8, 31, 2, 14)).splitlines()
        self.assertEqual(body[0], "NIGHT SUMMARY 2026-08-31")
        self.assertEqual(body[2], "Closed: #61 ALL MET")
        self.assertEqual(body[3], "Handed back to needs-triage: "
                                  "#62 HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, "
                                  "4 met of 5, #64")
        self.assertEqual(body[4], "Bounced: None")
        self.assertEqual(body[5], "Not dispatched, a blocker stayed open: "
                                  "#63 blocked by #62")
        self.assertEqual(body[6], "Sub-issues opened tonight: None")
        self.assertEqual(body[7], status.routed_line((0, 0, 0, 0, 0, 0)))

    def test_the_summary_lists_bounced_tickets_with_their_reason(self):
        tickets = {61: ticket(61, labels=("needs-triage",), comments=[bounced(61)])}
        body = status.summary(rows_of(tickets), opened="2026-08-30T00:00:00Z",
                              now=datetime(2026, 8, 31, 2, 14)).splitlines()
        self.assertEqual(body[3], "Handed back to needs-triage: None")
        self.assertEqual(body[4], "Bounced: #61 (conflict)")

    def test_the_summary_omits_a_bounce_returned_to_the_agent_queue(self):
        tickets = {61: ticket(61, labels=("ready-for-agent",), comments=[bounced(61)])}
        body = status.summary(rows_of(tickets), opened="2026-08-30T00:00:00Z",
                              now=datetime(2026, 8, 31, 2, 14)).splitlines()
        self.assertEqual(body[3], "Handed back to needs-triage: None")
        self.assertEqual(body[4], "Bounced: None")

    def test_a_later_pass_replaces_an_old_bounce_in_the_summary(self):
        tickets = {61: ticket(61, state="CLOSED", labels=(),
                              comments=[bounced(61), passed(61)])}
        body = status.summary(rows_of(tickets), opened="2026-08-30T00:00:00Z",
                              now=datetime(2026, 8, 31, 2, 14)).splitlines()
        self.assertEqual(body[4], "Bounced: None")

    def test_the_cli_window_is_sixteen_hours_back(self):
        self.assertEqual(
            status.night_opened(datetime(2026, 8, 31, 8, 0, tzinfo=timezone.utc)),
            "2026-08-30T16:00:00Z")

    def test_routed_counts_come_off_the_parents_child_events(self):
        """opened/fixed/became/skipped/unread/open, each slot a distinct number."""
        children = [
            child(89, kind="finding", resolution="fixed"),
            child(90, kind="finding", resolution="fixed"),
            child(91, kind="finding", resolution="became-ticket"),
            child(92, kind="finding", resolution="stale"),
            child(93, kind="finding"),
            child(94, kind="finding", state="OPEN"),
            status.normalise_ticket(99, {}),
            child(100, kind="contract", resolution="fixed"),
            child(101),
        ]
        self.assertEqual(status.routed_counts(children), (7, 2, 1, 1, 2, 1))
        self.assertTrue(status.routed_line((7, 2, 1, 1, 2, 1)).startswith(
            "Findings routed: 7/2/1/1/2/1 "))

    def test_summary_walks_the_tickets_children_and_reads_their_kind_off_the_parent(self):
        raws = {
            61: {"state": "CLOSED", "title": "ticket 61", "body": "",
                 "labels": [], "assignees": [], "blockedBy": {"nodes": []},
                 "comments": [{"body": passed(61)},
                              {"body": ev("child.opened", "Opened #90 (finding)", 61,
                                          child=90, kind="finding")},
                              {"body": ev("child.opened", "Opened #91 (fault)", 61,
                                          child=91, kind="fault")},
                              {"body": ev("child.closed", "#90 became #80", 61,
                                          child=90, resolution="became-ticket", became=80)}],
                 "createdAt": "2026-08-29T00:00:00Z",
                 "closedAt": "2026-08-31T02:00:00Z"},
            64: {"state": "OPEN", "title": "ticket 64", "body": "",
                 "labels": [{"name": "needs-triage"}], "assignees": [],
                 "blockedBy": {"nodes": []}, "comments": [{"body": "fresh"}],
                 "createdAt": "2026-08-31T00:00:00Z", "closedAt": ""},
            90: {"state": "CLOSED", "title": "REVIEW: RUNNER is now a Path",
                 "body": "A `finding` child of #61.\n", "labels": [], "assignees": [],
                 "blockedBy": {"nodes": []}, "comments": [],
                 "createdAt": "2026-08-31T01:00:00Z", "closedAt": ""},
            91: {"state": "OPEN", "title": "a fault child",
                 "body": "A `fault` child of #61.\n", "labels": [], "assignees": [],
                 "blockedBy": {"nodes": []}, "comments": [],
                 "createdAt": "2026-08-29T00:00:00Z", "closedAt": ""},
        }
        read_trees = []

        def fake_tree(spec):
            read_trees.append(spec)
            return {"number": 76, "children": [
                {"number": 61, "state": "CLOSED",
                 "children": [{"number": 90, "state": "CLOSED"},
                              {"number": 91, "state": "OPEN"}]},
                {"number": 64, "state": "OPEN", "children": []}]}

        saved = (status.gh_json, status.spec_tree, status.night_opened)

        def fake_gh_json(args, fallback=None):
            if args[:2] == ["issue", "view"]:
                return raws[int(args[2])]
            return [] if fallback is None else fallback

        try:
            status.gh_json = fake_gh_json
            status.spec_tree = fake_tree
            status.night_opened = lambda now=None: "2026-08-30T00:00:00Z"
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(status.main(["--summary", "76"]), 0)
            lines = out.getvalue().splitlines()
            self.assertEqual(
                lines[6], "Sub-issues opened tonight: #90 REVIEW: RUNNER is now a Path")
            self.assertEqual(lines[7], status.routed_line((1, 0, 1, 0, 0, 0)))
            # The tickets and every ticket's children come from one read of the tree.
            self.assertEqual(read_trees, [76])
        finally:
            (status.gh_json, status.spec_tree, status.night_opened) = saved

    def test_an_open_child_is_open_not_unread(self):
        c = child(98, kind="finding", resolution="fixed", state="OPEN")
        self.assertEqual(status.route_of(c), "open")

    def test_a_finding_promoted_in_place_counts_as_became_though_it_is_open(self):
        c = child(98, kind="finding", resolution="became-ticket", state="OPEN")
        self.assertEqual(status.route_of(c), "became")

    def test_a_finding_that_moved_under_the_spec_is_still_counted_from_its_ticket(self):
        """Promoted in place, #92 is a ticket under the spec now and under #61 no longer.
        The count comes from #61's events, not from where #92 sits."""
        raws = {
            61: {"state": "CLOSED", "title": "ticket 61", "body": "", "labels": [],
                 "assignees": [], "blockedBy": {"nodes": []},
                 "comments": [{"body": passed(61)},
                              {"body": ev("child.opened", "Opened #92 (finding)", 61,
                                          child=92, kind="finding")},
                              {"body": ev("child.closed", "#92 became ticket #92", 61,
                                          child=92, resolution="became-ticket", became=92)}],
                 "createdAt": "2026-08-29T00:00:00Z", "closedAt": "2026-08-31T02:00:00Z"},
            92: {"state": "OPEN", "title": "a finding, now a ticket", "body": "",
                 "labels": [{"name": "mmw:ticket"}], "assignees": [],
                 "blockedBy": {"nodes": []}, "comments": [],
                 "createdAt": "2026-08-31T01:00:00Z", "closedAt": ""},
        }
        saved = (status.gh_json, status.spec_tree, status.night_opened)
        try:
            status.gh_json = lambda args, fallback=None: raws[int(args[2])]
            status.spec_tree = lambda spec: {"number": 76, "children": [
                {"number": 61, "state": "CLOSED", "children": []},
                {"number": 92, "state": "OPEN", "children": []}]}
            status.night_opened = lambda now=None: "2026-08-30T00:00:00Z"
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(status.main(["--summary", "76"]), 0)
        finally:
            (status.gh_json, status.spec_tree, status.night_opened) = saved
        self.assertEqual(out.getvalue().splitlines()[7],
                         status.routed_line((1, 0, 1, 0, 0, 0)))

    def test_a_child_the_tracker_could_not_answer_is_unread_not_omitted(self):
        c = status.normalise_ticket(99, {})
        self.assertTrue(c["unread_raw"])
        self.assertEqual(status.routed_counts([c]), (1, 0, 0, 0, 1, 0))

    def test_read_ticket_asks_gh_for_the_body_and_the_comments(self):
        asked = []

        def fake_gh_json(args, fallback=None):
            asked.append(list(args))
            return fallback if fallback is not None else {}

        saved = status.gh_json
        try:
            status.gh_json = fake_gh_json
            status.read_ticket(90)
        finally:
            status.gh_json = saved
        fields = asked[0][asked[0].index("--json") + 1].split(",")
        self.assertIn("body", fields)
        self.assertIn("comments", fields)


class TheTreeIsOneQuery(unittest.TestCase):
    """The batch is read as the spec's tree, in one GraphQL query, and a tree the
    tracker could not answer for whole is a refusal — never an emptier batch."""

    def test_the_batch_is_one_graphql_query_rooted_at_the_spec(self):
        asked = []

        def fake_gh(args):
            asked.append(args)
            return 0, json.dumps({"data": {"repository": {"issue": {
                "number": 76, "title": "spec", "state": "OPEN",
                "subIssuesSummary": {"total": 2, "completed": 0},
                "subIssues": {"nodes": [
                    {"number": 61, "title": "a", "state": "OPEN",
                     "subIssuesSummary": {"total": 0, "completed": 0},
                     "subIssues": {"nodes": []}},
                    {"number": 62, "title": "b", "state": "OPEN",
                     "subIssuesSummary": {"total": 0, "completed": 0},
                     "subIssues": {"nodes": []}}]}}}}}), ""

        saved = status._gh_run
        try:
            status._gh_run = fake_gh
            self.assertEqual(status.sub_issues(76), [61, 62])
        finally:
            status._gh_run = saved
        self.assertEqual(len(asked), 1)
        self.assertEqual(asked[0][:2], ["api", "graphql"])
        self.assertIn("root=76", asked[0])
        self.assertIn("subIssues(first:100)", " ".join(asked[0]))

    def test_a_tree_cut_short_is_exit_2_not_an_empty_batch(self):
        def cut_short(args):
            return 0, json.dumps({"data": {"repository": {"issue": {
                "number": 76, "title": "spec", "state": "OPEN",
                "subIssuesSummary": {"total": 3, "completed": 0},
                "subIssues": {"nodes": []}}}}}), ""

        saved = status._gh_run
        try:
            status._gh_run = cut_short
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = status.main(["--advance-plan", "76"])
        finally:
            status._gh_run = saved
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("#76", err.getvalue())


class NoRunnerIsAsked(unittest.TestCase):
    """status.py's one source is the tracker: no runner command is ever run."""

    def test_the_table_runs_nothing_but_gh(self):
        ran = []
        saved = (status.ghlist.subprocess.run, status.sub_issues, status.read_ticket)

        def fake_run(cmd, **kwargs):
            ran.append(cmd[0])
            raise AssertionError(f"ran {cmd}")

        try:
            status.ghlist.subprocess.run = fake_run
            status.sub_issues = lambda spec: [61]
            status.read_ticket = lambda n: ticket(61, comments=[started(61, "term_1")])
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(status.main(["--table", "76"]), 0)
        finally:
            (status.ghlist.subprocess.run, status.sub_issues, status.read_ticket) = saved
        self.assertEqual(ran, [])
        self.assertIn("1 live", out.getvalue())


if __name__ == "__main__":
    unittest.main()
