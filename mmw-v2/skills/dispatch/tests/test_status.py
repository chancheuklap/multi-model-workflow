"""Tests for status.py against fixed samples: no tracker, no Paseo daemon, no clock.

The two sources status.py reads are a `paseo ls --json` array and a set of tickets, so
the samples here are one of each, in the shape the real calls return them. Inspect
fields (`LastUsage`, `PendingPermissions`, `ParentAgentId`) are merged onto each ls
row the way `live_agents` does. Everything status.py decides is a function of those
two, which is why none of it needs a terminal.

    python3 -m unittest discover -s mmw-v2/skills/dispatch/tests -p test_status.py
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

STATUS_PATH = Path(__file__).resolve().parent.parent / "scripts" / "status.py"
_spec = importlib.util.spec_from_file_location("status", STATUS_PATH)
status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(status)


def agent(ticket, status_="running", *, kind="worker", parent=None,
          created="2 minutes ago", agent_id=None, pending=None, name=None, cwd=None,
          last_usage=None):
    """One `paseo ls --json` row with the inspect fields already merged in."""
    aid = agent_id or f"{ticket:08d}-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    return {
        "id": aid,
        "shortId": aid[:7],
        "name": name or f"#{ticket} {kind}",
        "provider": "grok/grok-4.6",
        "thinking": "high",
        "status": status_,
        "cwd": cwd if cwd is not None else f"/repo/issue-{ticket}",
        "created": created,
        "LastUsage": last_usage,
        "PendingPermissions": pending or [],
        "ParentAgentId": parent,
    }


def ticket(number, state="OPEN", labels=("ready-for-agent",), blockers=(),
           assignees=(), comments=()):
    """One `gh issue view --json …` answer, before status.py normalises it."""
    return status.normalise_ticket(number, {
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

DECISIONS = "DECISIONS\n\nDecisions I made on my own\n- none\n\nOutside Owns\nNone"

REVIEW = "REVIEW abcdef0..1234567\n\nStandards: pass"


WORKER_61 = "11111111-1111-4111-8111-111111111111"
REVIEWER_61 = "22222222-2222-4222-8222-222222222222"


class Identity(unittest.TestCase):
    """Which ticket and kind a live agent belongs to."""

    def test_cwd_basename_names_the_ticket_and_a_root_agent_is_the_worker(self):
        found = status.sessions([agent(61, agent_id=WORKER_61)])[0]
        self.assertEqual((found["ticket"], found["kind"]), (61, "worker"))
        self.assertTrue(found["dispatched"])

    def test_a_tilde_cwd_still_reads_the_basename(self):
        found = status.sessions([agent(62, cwd="~/.paseo/worktrees/hash/issue-62")])[0]
        self.assertEqual(found["ticket"], 62)

    def test_a_child_agent_in_the_same_directory_is_the_reviewer(self):
        worker = agent(61, agent_id=WORKER_61)
        child = agent(61, kind="reviewer", parent=WORKER_61, agent_id=REVIEWER_61)
        found = {s["kind"]: s for s in status.sessions([worker, child])}
        self.assertEqual(found["worker"]["id"], WORKER_61)
        self.assertEqual(found["reviewer"]["id"], REVIEWER_61)

    def test_a_cwd_that_is_not_an_issue_directory_is_not_ours(self):
        self.assertEqual(status.sessions([agent(61, cwd="/repo/scratch")]), [])

    def test_an_agent_with_no_parent_in_the_list_is_held(self):
        rows = status.build_rows([61], {61: ticket(61)},
                                 status.sessions([agent(61, agent_id=WORKER_61)]))
        self.assertEqual([r["ticket"] for r in status.held(rows)], [61])

    def test_a_reviewer_alone_does_not_count_as_the_worker_being_held(self):
        """The worker is the parent; a child whose parent is still listed is not it.

        When the parent has already left the live list, the child has nothing to
        point at and would read as a worker — Paseo archives children with the
        parent, so that case does not arise on a live spec.
        """
        child = agent(61, kind="reviewer", parent=WORKER_61, agent_id=REVIEWER_61)
        worker = agent(61, agent_id=WORKER_61)
        rows = status.build_rows(
            [61], {61: ticket(61)}, status.sessions([worker, child]))
        self.assertEqual(rows[0]["worker"]["id"], WORKER_61)
        self.assertEqual(rows[0]["reviewer"]["id"], REVIEWER_61)


class Rows(unittest.TestCase):
    """The table's own contents, joined from the two sources."""

    def rows(self):
        agents = [
            agent(61, "running", created="2 minutes ago", agent_id=WORKER_61),
            agent(62, "idle", created="10 minutes ago"),
            agent(63, "idle", created="15 minutes ago"),
        ]
        tickets = {
            61: ticket(61, comments=[SELF_RUN_UNMET]),
            62: ticket(62, comments=[SELF_RUN_UNMET]),
            63: ticket(63, comments=[SELF_RUN_UNMET]),
            64: ticket(64, state="CLOSED", labels=(),
                       comments=[SELF_RUN_ALL_MET, "ALL MET\nBranch: issue-64"]),
            65: ticket(65, blockers=(62,)),
        }
        return status.build_rows(list(tickets), tickets, status.sessions(agents))

    def row(self, number):
        return next(r for r in self.rows() if r["ticket"] == number)

    def test_a_running_agent_shows_its_paseo_status_id_age_and_no_note(self):
        row = self.row(61)
        self.assertEqual(row["agent"], "#61 worker")
        self.assertEqual(row["status"], "running")
        self.assertEqual(row["agent_id"], WORKER_61[:7])
        self.assertEqual(row["age"], "2 minutes ago")
        self.assertEqual(row["phase"], "self-run")
        self.assertEqual(row["turn"], "-")
        self.assertEqual(row["note"], "")

    def test_ac_comes_off_the_newest_self_run(self):
        self.assertEqual(self.row(62)["ac"], "3/5")

    def test_a_closed_ticket_keeps_its_counts_and_names_the_closing_comment(self):
        row = self.row(64)
        self.assertEqual((row["agent"], row["phase"], row["ac"]), ("-", "ALL MET", "5/5"))
        self.assertEqual(row["note"], "ALL MET")

    def test_a_blocked_ticket_names_what_it_waits_on(self):
        self.assertEqual(self.row(65)["note"], "waiting on #62")

    def test_the_frontier_leaves_out_what_is_held_claimed_or_blocked(self):
        self.assertEqual([r["ticket"] for r in status.frontier(self.rows())], [])

    def test_only_the_worker_counts_as_held(self):
        worker = agent(61, agent_id=WORKER_61)
        child = agent(61, kind="reviewer", parent=WORKER_61, agent_id=REVIEWER_61)
        tickets = {61: ticket(61), 63: ticket(63)}
        rows = status.build_rows(list(tickets), tickets, status.sessions([worker, child]))
        self.assertEqual([r["ticket"] for r in status.held(rows)], [61])

    def test_the_frontier_takes_a_ready_ticket_with_no_session_and_no_blocker(self):
        tickets = {70: ticket(70), 71: ticket(71, assignees=("someone",)),
                   72: ticket(72, labels=("needs-triage",))}
        rows = status.build_rows(list(tickets), tickets, [])
        self.assertEqual([r["ticket"] for r in status.frontier(rows)], [70])

    def test_pending_permissions_show_on_the_note(self):
        agents = [agent(61, pending=[{"id": "perm-1"}])]
        rows = status.build_rows([61], {61: ticket(61)}, status.sessions(agents))
        self.assertEqual(rows[0]["note"], "needs permission")


class TicketReading(unittest.TestCase):
    """The few fields read out of a ticket's comments."""

    def test_the_counts_come_off_the_newest_self_run(self):
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_UNMET])), "3/5")
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_ALL_MET])), "5/5")

    def test_a_handoff_summary_line_counts_the_abandoned_criteria_too(self):
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_HANDOFF])), "3/5")

    def test_a_summary_line_carrying_a_reverify_count_or_a_scope_still_counts(self):
        for line, counted in (
                ("ALL MET (5 met, reran: 5, previously met reverified: 5) [scope api]",
                 "5/5"),
                ("UNMET: 2 (met: 3, abandoned: 0, reran: 5) [scope api]", "3/5"),
                ("HANDOFF REQUIRED: 2 abandoned (met: 3, unmet: 1, reran: 6)", "3/6")):
            with self.subTest(line=line):
                self.assertEqual(
                    status.counted_ac(ticket(62, comments=["self-run\n" + line])), counted)

    def test_a_ticket_with_no_run_has_no_counts(self):
        self.assertEqual(status.counted_ac(ticket(62)), "-")

    def test_the_newest_comment_of_a_kind_wins(self):
        found = status.newest_with_first_line(
            ticket(62, comments=[SELF_RUN_UNMET, VERDICT, SELF_RUN_ALL_MET]),
            "self-run", "reverify")
        self.assertEqual(status.first_line(found), "self-run")
        self.assertEqual(status.counted_ac(ticket(62, comments=[SELF_RUN_UNMET, VERDICT,
                                                               SELF_RUN_ALL_MET])), "5/5")


class PhaseFromComments(unittest.TestCase):
    """`phase` is the newest protocol-slot comment, not a token on the agent."""

    def test_each_protocol_slot_is_a_phase(self):
        cases = (
            (SELF_RUN_UNMET, "self-run"),
            ("reverify\nALL MET (5 met)", "reverify"),
            (VERDICT, "VERDICT"),
            (DECISIONS, "DECISIONS"),
            (REVIEW, "REVIEW"),
            ("ALL MET\nBranch: x", "ALL MET"),
            ("HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 4 met of 5",
             "HANDOFF REQUIRED"),
        )
        for body, phase in cases:
            with self.subTest(phase=phase):
                self.assertEqual(status.phase_of(ticket(61, comments=[body])), phase)

    def test_the_newest_protocol_slot_wins(self):
        t = ticket(61, comments=[SELF_RUN_UNMET, VERDICT, DECISIONS])
        self.assertEqual(status.phase_of(t), "DECISIONS")

    def test_a_ticket_with_no_protocol_slot_has_no_phase(self):
        self.assertEqual(status.phase_of(ticket(61)), "-")

    def test_a_closed_ticket_with_no_closing_comment_still_says_closed(self):
        self.assertEqual(status.phase_of(ticket(61, state="CLOSED", labels=())), "closed")


class Table(unittest.TestCase):
    """The one screen `--table` prints."""

    def table(self, spec=60):
        agents = [agent(61, "running", created="2 minutes ago", agent_id=WORKER_61,
                        name="#61 worker")]
        tickets = {61: ticket(61, comments=[SELF_RUN_UNMET]),
                   65: ticket(65, blockers=(61,))}
        rows = status.build_rows(list(tickets), tickets, status.sessions(agents))
        return status.render_table(rows, spec, datetime(2026, 8, 31, 2, 14))

    def test_the_first_line_names_the_time_the_spec_the_count_and_the_live_sessions(self):
        self.assertEqual(self.table().splitlines()[0],
                         "mmw status · 02:14 · spec #60 · 2 tickets · 1 live")

    def test_without_a_spec_the_first_line_leaves_that_field_out(self):
        self.assertEqual(self.table(spec=None).splitlines()[0],
                         "mmw status · 02:14 · 2 tickets · 1 live")

    def test_the_columns_include_id_and_age_beside_the_original_seven(self):
        self.assertEqual(self.table().splitlines()[2].split(),
                         ["ticket", "agent", "id", "agent_status", "age",
                          "phase", "ac", "turn", "note"])

    def test_one_line_per_ticket_in_ticket_order_with_id_and_age(self):
        body = self.table().splitlines()[3:]
        self.assertEqual([l.split()[0] for l in body], ["#61", "#65"])
        self.assertIn("#61 worker", body[0])
        self.assertIn(WORKER_61[:7], body[0])
        self.assertIn("2 minutes ago", body[0])
        self.assertIn("self-run", body[0])
        self.assertIn("waiting on #61", body[1])


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
            "GRADE 61 junior-worker",
            "GRADE 62 junior-worker senior-worker",
            "GRADE 63",
        ])


class AdvancePlan(unittest.TestCase):
    """`--advance-plan` prints MERGE then DISPATCH, and nothing else."""

    def setUp(self):
        self.saved = status.sub_issues, status.read_ticket, status.live_agents
        self.tickets = {
            61: ticket(61, state="CLOSED", labels=(),
                       comments=["ALL MET\nBranch: issue-61"]),
            62: ticket(62, state="CLOSED", labels=(),
                       comments=["ALL MET\nBranch: issue-62"]),
            63: ticket(63, state="CLOSED", labels=(),
                       comments=["HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 4 met of 5"]),
            70: ticket(70),
            71: ticket(71, blockers=(70,)),
        }
        self.tickets[61]["closed_at"] = "2026-08-31T01:00:00Z"
        self.tickets[62]["closed_at"] = "2026-08-31T02:00:00Z"
        self.tickets[63]["closed_at"] = "2026-08-31T03:00:00Z"
        status.sub_issues = lambda spec: list(self.tickets)
        status.read_ticket = lambda n: self.tickets[n]
        status.live_agents = lambda spec: []

    def tearDown(self):
        status.sub_issues, status.read_ticket, status.live_agents = self.saved

    def test_merges_closed_all_met_in_closing_order_then_dispatches_the_frontier(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(status.advance_plan(76), 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "MERGE 61",
            "MERGE 62",
            "DISPATCH 70",
        ])

    def test_a_live_worker_keeps_its_ticket_off_the_frontier(self):
        status.live_agents = lambda spec: [agent(70)]
        with redirect_stdout(io.StringIO()) as out:
            status.advance_plan(76)
        self.assertEqual(out.getvalue().splitlines(), [
            "MERGE 61",
            "MERGE 62",
        ])


class Summary(unittest.TestCase):
    """`--summary` prints the four lines; it does not post them."""

    def test_the_summary_is_four_lines_of_numbers_and_first_lines(self):
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
        rows = status.build_rows(list(tickets), tickets, [])
        body = status.summary(rows, opened="2026-08-30T00:00:00Z",
                              now=datetime(2026, 8, 31, 2, 14)).splitlines()
        self.assertEqual(body[0], "NIGHT SUMMARY 2026-08-31")
        self.assertEqual(body[2], "Closed: #61 ALL MET")
        self.assertEqual(body[3], "Handed back to needs-triage: "
                                  "#62 HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, "
                                  "4 met of 5, #64 fresh")
        self.assertEqual(body[4], "Not dispatched, a blocker stayed open: "
                                  "#63 blocked by #62")
        self.assertEqual(body[5], "Sub-issues opened tonight: #64 fresh")

    def test_the_cli_window_is_sixteen_hours_back(self):
        self.assertEqual(
            status.night_opened(datetime(2026, 8, 31, 8, 0, tzinfo=timezone.utc)),
            "2026-08-30T16:00:00Z")

    def test_the_summary_form_prints_and_does_not_post(self):
        tickets = {
            61: ticket(61, state="CLOSED", labels=(), comments=["ALL MET\nBranch: x"]),
        }
        tickets[61]["closed_at"] = "2026-08-31T02:00:00Z"
        tickets[61]["created"] = "2026-08-29T00:00:00Z"
        calls = []
        saved = status.collect, status.gh, status.night_opened
        try:
            status.collect = lambda spec: (
                status.build_rows(list(tickets), tickets, []), [])
            status.gh = lambda args: calls.append(list(args)) or ""
            status.night_opened = lambda now=None: "2026-08-30T00:00:00Z"
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(status.main(["--summary", "76"]), 0)
            self.assertTrue(out.getvalue().startswith("NIGHT SUMMARY "))
            self.assertEqual(calls, [])
        finally:
            status.collect, status.gh, status.night_opened = saved


class ReadingPaseo(unittest.TestCase):
    """What status.py makes of Paseo's answers about a session."""

    def setUp(self):
        self.saved = status.paseo_json
        self.ls = []
        self.inspect = {}

        def fake(args):
            if args[:3] == ["ls", "-g", "--json"]:
                return list(self.ls)
            if args[:1] == ["inspect"]:
                return dict(self.inspect.get(args[1], {}))
            raise AssertionError(args)

        status.paseo_json = fake

    def tearDown(self):
        status.paseo_json = self.saved

    def test_an_unanswered_ls_is_not_a_spec_with_no_agents(self):
        def boom(args):
            raise RuntimeError("exit 1")
        status.paseo_json = boom
        with self.assertRaises(RuntimeError):
            status.live_agents(76)

    def test_a_non_list_ls_is_refused_the_same_way(self):
        status.paseo_json = lambda args: {"agents": []}
        with self.assertRaises(RuntimeError):
            status.live_agents(76)

    def test_an_empty_list_is_read_as_no_agents(self):
        self.ls = []
        self.assertEqual(status.live_agents(76), [])

    def test_each_ls_row_is_inspected_once_and_the_three_keys_are_merged(self):
        self.ls = [{
            "id": WORKER_61,
            "shortId": WORKER_61[:7],
            "name": "#61 worker",
            "provider": "grok/grok-4.6",
            "thinking": "high",
            "status": "running",
            "cwd": "/repo/issue-61",
            "created": "2 minutes ago",
        }]
        self.inspect[WORKER_61] = {
            "LastUsage": {"InputTokens": 1, "OutputTokens": 2,
                          "CachedTokens": 0, "CostUsd": 0.01},
            "PendingPermissions": [],
            "ParentAgentId": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        }
        found = status.live_agents(76)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["id"], WORKER_61)
        self.assertEqual(found[0]["status"], "running")
        self.assertEqual(found[0]["cwd"], "/repo/issue-61")
        self.assertEqual(found[0]["created"], "2 minutes ago")
        self.assertEqual(found[0]["LastUsage"]["InputTokens"], 1)
        self.assertEqual(found[0]["PendingPermissions"], [])
        self.assertEqual(found[0]["ParentAgentId"],
                         "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

    def test_ls_is_asked_with_the_spec_label_and_not_for_labels_in_the_body(self):
        seen = []

        def fake(args):
            seen.append(list(args))
            if args[:3] == ["ls", "-g", "--json"]:
                return []
            raise AssertionError(args)

        status.paseo_json = fake
        status.live_agents(76)
        self.assertEqual(seen, [["ls", "-g", "--json", "--label", "mmw.spec=76"]])


if __name__ == "__main__":
    unittest.main()
