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
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

STATUS_PATH = Path(__file__).resolve().parent.parent / "scripts" / "status.py"
_spec = importlib.util.spec_from_file_location("status", STATUS_PATH)
status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(status)


def paseo_json_by_kind(by_kind, spec=76):
    """A `paseo_json` stand-in: `ls` returns the row for that kind under `mmw.spec`."""
    def fake(args):
        if args[:3] == ["ls", "-g", "--json"]:
            labels = [args[i + 1] for i, a in enumerate(args) if a == "--label"]
            if f"mmw.spec={spec}" not in labels:
                return []
            for kind, row in by_kind.items():
                if f"mmw.kind={kind}" in labels:
                    return [row]
            return []
        if args[:1] == ["inspect"]:
            return {}
        raise AssertionError(args)
    return fake


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
        "kind": kind,
        "LastUsage": last_usage,
        "PendingPermissions": pending or [],
        "ParentAgentId": parent,
    }


def workspace(ticket, archived=False, cwd=None):
    """One `paseo workspace ls --json` row, with only the fields status.py reads."""
    return {
        "workspaceId": f"wks_issue-{ticket}",
        "cwd": cwd if cwd is not None else f"/repo/issue-{ticket}",
        "archived": archived,
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
VERIFIER_61 = "33333333-3333-4333-8333-333333333333"
ADVISOR_61 = "44444444-4444-4444-8444-444444444444"


class Identity(unittest.TestCase):
    """Which ticket and kind a live agent belongs to."""

    def test_cwd_basename_names_the_ticket_and_a_root_agent_is_the_worker(self):
        found = status.sessions([agent(61, agent_id=WORKER_61)])[0]
        self.assertEqual((found["ticket"], found["kind"]), (61, "worker"))

    def test_a_tilde_cwd_still_reads_the_basename(self):
        found = status.sessions([agent(62, cwd="~/.paseo/worktrees/hash/issue-62")])[0]
        self.assertEqual(found["ticket"], 62)

    def test_kind_comes_from_the_mmw_kind_filter_not_from_parent(self):
        by_kind = {
            "worker": {
                "id": WORKER_61, "shortId": WORKER_61[:7], "name": "#61 worker",
                "status": "running", "cwd": "/repo/issue-61", "created": "2 minutes ago",
            },
            "reviewer": {
                "id": REVIEWER_61, "shortId": REVIEWER_61[:7], "name": "#61 reviewer",
                "status": "running", "cwd": "/repo/issue-61", "created": "2 minutes ago",
                "ParentAgentId": WORKER_61,
            },
        }
        saved = status.paseo_json
        try:
            status.paseo_json = paseo_json_by_kind(by_kind)
            found = {s["kind"]: s for s in status.sessions(status.live_agents(76))}
        finally:
            status.paseo_json = saved
        self.assertEqual(found["worker"]["id"], WORKER_61)
        self.assertEqual(found["reviewer"]["id"], REVIEWER_61)

    def test_a_cwd_that_is_not_an_issue_directory_is_not_ours(self):
        self.assertEqual(status.sessions([agent(61, cwd="/repo/scratch")]), [])

    def test_a_live_worker_is_held(self):
        rows = status.build_rows([61], {61: ticket(61)},
                                 status.sessions([agent(61, agent_id=WORKER_61)]))
        self.assertEqual([r["ticket"] for r in status.held(rows)], [61])

    def test_a_reviewer_alone_does_not_count_as_the_worker_being_held(self):
        child = agent(61, kind="reviewer", parent=WORKER_61, agent_id=REVIEWER_61)
        rows = status.build_rows(
            [61], {61: ticket(61)}, status.sessions([child]))
        self.assertIsNone(rows[0]["worker"])
        self.assertEqual(status.held(rows), [])

    def test_unknown_kind_is_not_a_worker(self):
        advisor = agent(61, kind="advisor", agent_id=ADVISOR_61)
        found = status.sessions([advisor])
        self.assertEqual(found, [])
        rows = status.build_rows([61], {61: ticket(61)}, found)
        self.assertEqual(rows[0]["agent"], "-")
        table = status.render_table(rows, 76, datetime(2000, 1, 1, 2, 14))
        self.assertNotIn("advisor", table)
        self.assertNotIn(ADVISOR_61[:7], table)


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
        self.assertNotIn("turn", row)
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
        child = agent(63, kind="reviewer", parent=WORKER_61, agent_id=REVIEWER_61)
        tickets = {61: ticket(61), 63: ticket(63)}
        rows = status.build_rows(list(tickets), tickets, status.sessions([worker, child]))
        self.assertEqual([r["ticket"] for r in status.held(rows)], [61])
        self.assertIsNone(next(r for r in rows if r["ticket"] == 63)["worker"])

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

    def test_the_columns_include_id_and_age_and_drop_turn(self):
        self.assertEqual(self.table().splitlines()[2].split(),
                         ["ticket", "agent", "id", "agent_status", "age",
                          "phase", "ac", "note"])

    def test_one_line_per_ticket_in_ticket_order_with_id_and_age(self):
        body = self.table().splitlines()[3:]
        self.assertEqual([l.split()[0] for l in body], ["#61", "#65"])
        self.assertIn("#61 worker", body[0])
        id_at = 1 + 8 + 18
        self.assertEqual(body[0][id_at:id_at + 8].strip(), "1111111")
        self.assertNotIn(WORKER_61, body[0])
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
    """The three kinds of line `--advance-plan` prints, and what it says when it prints none."""

    LOGIN = "mmw-bot"

    def setUp(self):
        self.saved = (status.sub_issues, status.read_ticket, status.live_agents,
                      status.own_login, status.live_workspaces)
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
        self.agents = []
        self.workspaces = []
        status.sub_issues = lambda spec: list(self.tickets)
        status.read_ticket = lambda n: self.tickets[n]
        status.live_agents = lambda spec: self.agents
        status.own_login = lambda: ""
        status.live_workspaces = lambda: self.workspaces

    def tearDown(self):
        (status.sub_issues, status.read_ticket, status.live_agents,
         status.own_login, status.live_workspaces) = self.saved

    def plan(self, spec=76):
        """The plan's stdout lines and its stderr lines, the two channels held apart."""
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(status.advance_plan(spec), 0)
        return out.getvalue().splitlines(), err.getvalue().splitlines()

    def test_merges_closed_all_met_in_closing_order_then_dispatches_the_frontier(self):
        self.assertEqual(self.plan()[0], [
            "MERGE 61",
            "MERGE 62",
            "DISPATCH 70",
        ])

    def test_a_live_worker_keeps_its_ticket_off_the_frontier(self):
        self.agents = [agent(70)]
        self.assertEqual(self.plan()[0], [
            "MERGE 61",
            "MERGE 62",
        ])

    def test_a_claim_with_no_session_behind_it_is_released_and_then_dispatched(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,))}
        self.assertEqual(self.plan()[0], ["RELEASE 61", "DISPATCH 61"])

    def test_a_claim_this_pipeline_did_not_make_is_left_alone(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=("alice",))}
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("#61 claimed by alice", err[1])

    def test_a_claim_with_a_live_worker_on_it_is_its_owners(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,))}
        self.agents = [agent(61)]
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("held by the live worker #61 worker", err[1])

    def test_a_claim_whose_workspace_still_stands_is_not_released(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,)),
                        62: ticket(62, assignees=(self.LOGIN,))}
        self.workspaces = [workspace(61), workspace(62)]
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertIn("#61 keeps its claim", err[0])
        self.assertIn("#62 keeps its claim", err[1])

    def test_a_claim_with_neither_a_worker_nor_a_workspace_is_still_released(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,))}
        self.workspaces = [workspace(99), workspace(61, archived=True)]
        self.assertEqual(self.plan()[0], ["RELEASE 61", "DISPATCH 61"])

    def test_with_no_login_to_compare_against_nothing_is_released(self):
        self.tickets = {61: ticket(61, assignees=(self.LOGIN,))}
        self.assertEqual(self.plan()[0], [])

    def test_the_merges_come_first_and_in_closing_order(self):
        status.own_login = lambda: self.LOGIN
        self.tickets = {
            61: ticket(61, state="CLOSED", labels=(),
                       comments=["ALL MET\nBranch: issue-61"]),
            62: ticket(62, state="CLOSED", labels=(),
                       comments=["ALL MET\nBranch: issue-62"]),
            63: ticket(63, assignees=(self.LOGIN,)),
        }
        self.tickets[61]["closed_at"] = "2026-08-31T02:00:00Z"
        self.tickets[62]["closed_at"] = "2026-08-31T01:00:00Z"
        self.assertEqual(self.plan()[0],
                         ["MERGE 62", "MERGE 61", "RELEASE 63", "DISPATCH 63"])

    def test_an_empty_frontier_names_every_queued_ticket_and_its_condition(self):
        self.tickets = {
            61: ticket(61, assignees=("alice",)),
            62: ticket(62, blockers=(61,)),
            63: ticket(63),
            64: ticket(64, labels=("needs-triage",)),
        }
        self.agents = [agent(63)]
        out, err = self.plan()
        self.assertEqual(out, [])
        self.assertEqual(err, [
            "dispatch: nothing on #76's frontier, and 3 open ticket(s) are still in "
            "the agent queue:",
            "  #61 claimed by alice",
            "  #62 blocked by #61",
            "  #63 held by the live worker #63 worker",
        ])

    def test_a_batch_with_nothing_left_in_the_queue_says_nothing(self):
        self.tickets = {61: ticket(61, state="CLOSED", labels=())}
        self.assertEqual(self.plan(), ([], []))

    def test_a_frontier_with_something_on_it_needs_no_explanation(self):
        self.tickets = {61: ticket(61), 62: ticket(62, blockers=(61,))}
        self.assertEqual(self.plan(), (["DISPATCH 61"], []))


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
        self.assertEqual(body[5], "Sub-issues opened tonight: None")

    def test_summary_walks_the_tickets_children(self):
        """The fourth line is each ticket's children in the window, not the spec's tickets."""
        tickets = {
            61: ticket(61, state="CLOSED", labels=(), comments=["ALL MET\nBranch: x"]),
            64: ticket(64, labels=("needs-triage",), comments=["fresh"]),
            90: ticket(90, labels=("needs-triage",),
                       comments=["SUB-ISSUE baseline from #61"]),
            91: ticket(91, labels=("needs-triage",),
                       comments=["SUB-ISSUE pipeline from #61"]),
        }
        tickets[61]["created"] = "2026-08-29T00:00:00Z"
        tickets[61]["closed_at"] = "2026-08-31T02:00:00Z"
        tickets[64]["created"] = "2026-08-31T00:00:00Z"
        tickets[90]["created"] = "2026-08-31T01:00:00Z"
        tickets[91]["created"] = "2026-08-29T00:00:00Z"
        children = {76: [61, 64], 61: [90, 91], 64: []}
        asked = []
        saved = (status.gh, status.sub_issues, status.read_ticket,
                 status.paseo_json, status.night_opened)
        try:
            status.gh = lambda args: []
            status.sub_issues = (lambda n: asked.append(n) or list(children.get(n, [])))
            status.read_ticket = lambda n: tickets[n]
            status.paseo_json = (
                lambda args: [] if args[:3] == ["ls", "-g", "--json"] else {})
            status.night_opened = lambda now=None: "2026-08-30T00:00:00Z"
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(status.main(["--summary", "76"]), 0)
            lines = out.getvalue().splitlines()
            self.assertEqual(
                lines[5], "Sub-issues opened tonight: #90 SUB-ISSUE baseline from #61")
            self.assertNotIn("#64", lines[5])
            self.assertNotIn("#91", lines[5])
            self.assertIn(61, asked)
            self.assertIn(64, asked)
        finally:
            (status.gh, status.sub_issues, status.read_ticket,
             status.paseo_json, status.night_opened) = saved

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
        gh_calls = []
        saved = (status.gh, status.sub_issues, status.read_ticket,
                 status.paseo_json, status.night_opened)
        try:
            status.gh = lambda args: gh_calls.append(list(args)) or ""
            status.sub_issues = lambda spec: [61]
            status.read_ticket = lambda n: tickets[n]
            status.paseo_json = (
                lambda args: [] if args[:3] == ["ls", "-g", "--json"] else {})
            status.night_opened = lambda now=None: "2026-08-30T00:00:00Z"
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(status.main(["--summary", "76"]), 0)
            lines = out.getvalue().splitlines()
            self.assertTrue(lines[0].startswith("NIGHT SUMMARY "))
            self.assertEqual(lines[2], "Closed: #61 ALL MET")
            self.assertEqual(lines[3], "Handed back to needs-triage: None")
            self.assertEqual(lines[4], "Not dispatched, a blocker stayed open: None")
            self.assertEqual(lines[5], "Sub-issues opened tonight: None")
            self.assertEqual(
                [c for c in gh_calls if c[:2] == ["issue", "comment"]], [])
        finally:
            (status.gh, status.sub_issues, status.read_ticket,
             status.paseo_json, status.night_opened) = saved


class ReadingPaseo(unittest.TestCase):
    """What status.py makes of Paseo's answers about a session."""

    def setUp(self):
        self.saved = status.paseo_json
        self.ls = []
        self.inspect = {}

        def fake(args):
            if args[:3] == ["ls", "-g", "--json"]:
                labels = [args[i + 1] for i, a in enumerate(args) if a == "--label"]
                if any(l.startswith("mmw.kind=") and l != "mmw.kind=worker" for l in labels):
                    return []
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
        self.assertEqual(found[0]["kind"], "worker")
        self.assertNotIn("ParentAgentId", found[0])

    def test_live_agents_returns_one_row_per_kind_for_the_spec(self):
        by_kind = {
            "worker": {
                "id": WORKER_61, "shortId": WORKER_61[:7], "name": "#61 worker",
                "status": "running", "cwd": "/repo/issue-61", "created": "2 minutes ago",
            },
            "reviewer": {
                "id": REVIEWER_61, "shortId": REVIEWER_61[:7], "name": "#61 reviewer",
                "status": "running", "cwd": "/repo/issue-61", "created": "2 minutes ago",
            },
            "verifier": {
                "id": VERIFIER_61, "shortId": VERIFIER_61[:7], "name": "#61 verifier",
                "status": "running", "cwd": "/repo/issue-61", "created": "2 minutes ago",
            },
        }
        status.paseo_json = paseo_json_by_kind(by_kind)
        found = {a["kind"]: a["id"] for a in status.live_agents(76)}
        self.assertEqual(found, {
            "worker": WORKER_61,
            "reviewer": REVIEWER_61,
            "verifier": VERIFIER_61,
        })


if __name__ == "__main__":
    unittest.main()
