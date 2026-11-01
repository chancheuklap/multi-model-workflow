"""Ticket planning contracts migrated from v4, using fixed tracker evidence."""
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
from pathlib import Path

STATUS_PATH = Path(__file__).resolve().parents[2] / "tools/dispatch/scripts/status.py"
sys.path.insert(0, str(STATUS_PATH.parent))
_spec = importlib.util.spec_from_file_location("pipeline_status", STATUS_PATH)
status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(status)
events = status.events
AT = "2026-09-10T01:00:00Z"
BROKEN = 'worker started\n\n<!-- mmw {"v":1,"event":"worker.started" -->'

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
    return ev("ticket.passed", "Completed", ticket)

def landed(ticket):
    return ev("ticket.landed", f"Landed issue-{ticket} into main", ticket)

def returned(ticket, line="Incomplete: the requested behavior is still missing"):
    return ev("ticket.returned", line, ticket)

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
                       ticket(61, comments=(BROKEN,))):
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
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
spec = importlib.util.spec_from_file_location("isolated_status", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.sub_issues = lambda spec: [60, 61]
module.own_login = lambda: ""
module.read_ticket = lambda n: module.normalise_ticket(n, {
    "state": "CLOSED" if n == 60 else "OPEN",
    "labels": [{"name": "ready-for-agent"}],
    "comments": [{"body": module.events.build("ticket.passed", ticket=60,
                  line="Completed")}] if n == 60 else []})
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
                                        BROKEN)}
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
                                   comments=[BROKEN])}
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
        self.tickets = {1: self.closed(1, "x", BROKEN)}
        rows, _ = self.run_form(status.land_plan, [1])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].startswith("HOLD 1"), rows)


class CompleteTrackerEvidence(unittest.TestCase):
    def test_late_landing_event_is_read_from_all_comment_pages(self):
        from unittest import mock
        first = {"state": "CLOSED", "comments": [{"body": passed(61)}]}
        pages = [[{"id": 1, "body": passed(61)}], [{"id": 105, "body": landed(61)}]]
        with mock.patch.object(status, 'gh_json', side_effect=[first, pages]) as gh:
            with mock.patch.object(status.tracker, 'repository', return_value='o/r'):
                result = status.read_ticket(61)
        self.assertTrue(status.landed(result))
        self.assertEqual(gh.call_args_list[1].args[0], [
            'api', '--paginate', '--slurp', 'repos/o/r/issues/61/comments?per_page=100'])

    def test_unreadable_comment_page_cannot_authorize_a_landing(self):
        from unittest import mock
        for pages in (None, [{}], [[{"id": 105, "body": None}]]):
            with self.subTest(pages=pages):
                with mock.patch.object(status, 'gh_json', side_effect=[{'state': 'CLOSED'}, pages]):
                    with mock.patch.object(status.tracker, 'repository', return_value='o/r'):
                        result = status.read_ticket(61)
                self.assertTrue(result['unread_raw'])
                self.assertFalse(status.passed_unlanded(result))


class BatchCompletion(Plans):
    def test_summary_counts_landed_work_without_acceptance_run_records(self):
        self.tickets = {61: self.closed(61, AT, passed(61), landed(61)),
                        62: ticket(62, labels=('needs-triage',), comments=[returned(62)])}
        self.assertEqual(self.run_form(status.closeout_ready, 76), (['1'], []))

    def test_summary_refuses_unlanded_output_or_live_work(self):
        self.tickets = {61: self.closed(61, AT, passed(61)),
                        62: ticket(62, comments=[started(62, 'worker-62')])}
        out, err = self.run_form(status.closeout_ready, 76, exit_code=2)
        self.assertEqual(out, [])
        self.assertIn('#61 passed but has not landed', '\n'.join(err))
        self.assertIn('worker-62', '\n'.join(err))
