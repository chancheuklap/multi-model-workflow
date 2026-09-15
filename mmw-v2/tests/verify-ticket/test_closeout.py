"""The closing gate: what a closing comment must say before the ticket may close."""

import io
import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import checked, event, load, started

vt = load()

ME = "chancheuklap"
VERIFIED = "3f9c2e1adeadbeefcafe0123456789abcdef0123"
HEAD = "9b1d40c7feedface0011223344556677889900aa"


STARTED = started(base="main", into="spec-337")

MET = """- [x] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: /\\d+ passed/
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=9"""

UNMET = """- [ ] AC2: the expiry page says the link is stale
  CHECK: pytest -q tests/test_expiry.py
  EXPECT: 2 passed
  EVIDENCE: pending"""

FINAL_RUN = checked("reverify", [MET], "ALL MET (1 met)", commit=HEAD, actor="worker")
STALE_FINAL_RUN = checked("reverify", [MET], "ALL MET (1 met)",
                          commit=VERIFIED, actor="worker")


def posted_as(body):
    """A posted closing comment as `(prose, event name)`: the draft, then its event."""
    what, payload = vt.events.parse(body)
    assert what == "event", (what, payload, body)
    return body[:body.index("\n\n<!-- mmw")] + "\n", payload["event"]


def ledger_of(text):
    """The criteria of a draft as a run states them: from its first criterion to its
    `Outside Owns:` line, with no `ABANDON:` lines.

    A run is generated from the ticket body, and a body carries no `ABANDON:` line, so
    a ledger that had one would not describe the same criteria as the body.
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if vt.GATE_LINE_RE.match(line)), None)
    if start is None:
        return []
    end = next((i for i, line in enumerate(lines[start:], start)
                if line.startswith("Outside Owns:")), len(lines))
    out = [line for line in lines[start:end] if not line.startswith("ABANDON:")]
    while out and not out[-1].strip():
        out.pop()
    return out


def acceptance_body(ledger):
    """A ticket body whose `## Acceptance criteria` are exactly these lines."""
    return "\n".join(["## Acceptance criteria", ""] + ledger) + "\n"


def reverify_of(ledger, summary="ALL MET (1 met)"):
    """The worker's final run of exactly these criteria, reporting `summary`."""
    return checked("reverify", ledger, summary, commit=HEAD, actor="worker")


def self_runs(block, rounds):
    """`rounds` runs of the worker's own, each leaving that criterion unmet."""
    ledger = block if block.startswith("- [ ]") else block.replace("- [x]", "- [ ]")
    return [checked("self", [ledger], "UNMET: 1")] * rounds


def is_reverify(comment):
    what, payload = vt.events.parse(comment)
    return (what == "event" and payload["event"] == "ticket.checked"
            and payload["run"] == "reverify")


def draft(first="ALL MET", criteria=(MET,), abandons=(), counts=None):
    """Assemble a closing comment in the shape #60 section 9 step 5 fixes."""
    body = [first, "", "Branch: issue-77  Commit: 9b1d40c7  PR: none", ""]
    for i, block in enumerate(criteria):
        body.append(block)
        for line in abandons:
            if line.split()[1] == vt.parse_criteria(block)[0]["id"]:
                body.append(line)
    body += ["", "Outside Owns: None"]
    if counts is not None:
        body += ["", counts]
    return "\n".join(body) + "\n"


def counts_line(met=1, unmet=0, abandoned=0, total=1):
    return f"Counts: {met} met, {unmet} unmet, {abandoned} abandoned of {total}"


# Every post and every state change the newest `check` made, in the order it made them.
CALLS = []


def check(text, comments=(),
          head=HEAD, dirty=(), main_merged=True, diff="src/app.py",
          state="OPEN", assignees=(ME,), check_only=True, repo=None, body=None,
          reverify=True, tracker_fails=False, post_fails=False, labels=(), reason=None,
          started_event=STARTED, pushed=None):
    """Run --closeout against a made-up ticket; return (exit code, stderr, side effects).
    With `tracker_fails` the tracker refuses to close the ticket or hand it back; with
    `post_fails` it refuses the comment. `reason` is the ticket's `stateReason`."""
    seen = {"posted": [], "closed": [], "handed": []}
    CALLS.clear()

    def change(kind):
        def run(number):
            CALLS.append(kind)
            if tracker_fails:
                raise subprocess.CalledProcessError(1, ["gh", "issue", "edit", str(number)])
            seen[kind].append(number)
        return run

    def post(number, body):
        CALLS.append("posted")
        if post_fails:
            raise subprocess.CalledProcessError(1, ["gh", "issue", "comment", str(number)])
        seen["posted"].append((number, body))
    ledger = ledger_of(text)
    comments = (started_event, *comments)
    if body is None:
        body = acceptance_body(ledger)
    if reverify and not any(is_reverify(c) for c in comments):
        comments = tuple(comments) + (reverify_of(ledger),)

    def fake_git(*args, cwd=None):
        if args[:2] == ("rev-parse", "HEAD"):
            return head
        if args[0] == "merge-base" and "--is-ancestor" not in args:
            return "0d19a4f3"
        if args[0] == "status":
            return "\n".join(dirty)
        if args[0] == "diff":
            return diff
        return ""

    def fake_is_ancestor(commit, descendant, root=None):
        return main_merged

    ticket = {"state": state, "labels": [{"name": n} for n in labels],
              "assignees": [{"login": a} for a in assignees], "blockedBy": {"nodes": []}}
    if reason:
        ticket["stateReason"] = reason
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "closeout.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
             mock.patch.object(vt, "fetch_ticket", return_value=ticket), \
             mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "gh_login", return_value=ME), \
             mock.patch.object(vt, "repo_root", return_value=repo), \
             mock.patch.object(vt, "git", side_effect=fake_git), \
             mock.patch.object(vt, "is_ancestor", side_effect=fake_is_ancestor), \
             mock.patch.object(vt, "dirty_tracked", side_effect=lambda root=None: list(dirty)), \
             mock.patch.object(vt, "push_ticket_branch",
                               side_effect=lambda *args: pushed.append(args)
                               if pushed is not None else None), \
             mock.patch.object(vt, "post_comment", side_effect=post), \
             mock.patch.object(vt, "close_ticket", side_effect=change("closed")), \
             mock.patch.object(vt, "hand_back_for_triage", side_effect=change("handed")):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_closeout(77, path, check_only)
    return code, err.getvalue(), seen


class TestFirstLine(unittest.TestCase):
    def test_a_first_line_in_neither_shape_is_refused(self):
        code, err, _ = check(draft(first="done!", counts=counts_line()))
        self.assertEqual(code, 1)
        self.assertIn("first line is neither", err)

    def test_all_met_over_a_failed_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck the endpoint it checks does not exist yet",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("only `decision` may be abandoned", err)

    def test_all_met_over_a_stuck_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium is not installed; tried …",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        self.assertEqual(check(text)[0], 1)

    def test_all_met_over_a_decision_abandon_passes(self):
        """The self-run is generated from the ticket body, which carries no `ABANDON:`
        line, so the run still reports the decision criterion as unmet."""
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 decision both wordings are legal; opened #58",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        newest_run = checked("reverify", [MET, UNMET], "UNMET: 1 (met: 1)",
                             commit=HEAD, actor="worker")
        code, err, _ = check(text, comments=(FINAL_RUN, newest_run))
        self.assertEqual(code, 0, err)

    def test_all_met_with_a_real_unmet_beside_the_decision_is_refused(self):
        """The draft ticks AC3 as met; the newest run says it is not. Only the run's
        own summary refuses this — the draft is well formed on its face."""
        unmet3 = UNMET.replace("AC2: the expiry page says the link is stale",
                               "AC3: the expiry page links back home")
        met3 = MET.replace("AC1: the importer writes six rows",
                           "AC3: the expiry page links back home")
        text = draft(criteria=(MET, UNMET, met3),
                     abandons=("ABANDON: AC2 decision both wordings are legal; opened #58",),
                     counts=counts_line(met=2, abandoned=1, total=3))
        newest_run = checked("reverify", [MET, UNMET, unmet3], "UNMET: 2 (met: 1)")
        code, err, _ = check(text, comments=(FINAL_RUN, newest_run))
        self.assertEqual(code, 1)
        self.assertIn("still reports unmet", err)
        self.assertNotIn("first line is `ALL MET` but", err)

    def test_a_well_formed_handoff_first_line_passes(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text, comments=(FINAL_RUN, *self_runs(UNMET, 1)))
        self.assertEqual(code, 0, err)


class TestBody(unittest.TestCase):
    def test_an_unknown_abandon_kind_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 giveup nothing worked",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("must be one of decision, failed, stuck", err)

    def test_an_abandon_pointing_at_no_criterion_is_refused(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 1",
                     criteria=(MET,), counts=counts_line())
        text += "ABANDON: AC9 stuck there is no AC9 on this ticket\n"
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("points at a criterion the draft does not list", err)

    def test_a_tick_with_pending_evidence_is_refused(self):
        ticked_but_empty = MET.replace(
            "EVIDENCE: exit=0; EXPECT=matched; output-bytes=9", "EVIDENCE: pending")
        code, err, _ = check(draft(criteria=(ticked_but_empty,), counts=counts_line(met=0, unmet=1)))
        self.assertEqual(code, 1)
        self.assertIn("is ticked but its EVIDENCE is pending", err)

    def test_counts_that_disagree_with_the_body_are_refused(self):
        code, err, _ = check(draft(criteria=(MET,), counts=counts_line(met=4, total=4)))
        self.assertEqual(code, 1)
        self.assertIn("the draft reads 1 met", err)

    def test_a_missing_counts_line_is_refused(self):
        code, err, _ = check(draft(criteria=(MET,), counts=None))
        self.assertEqual(code, 1)
        self.assertIn("no `Counts:", err)

    def test_a_first_line_that_disagrees_with_counts_is_refused(self):
        text = draft(first="HANDOFF REQUIRED: 2 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck the device this needs is not on this machine",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("first line says 2, `Counts:` says 1", err)


HANDOFF = "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1"
ABANDONED = "ABANDON: AC2 stuck chromium will not start here; tried the bundled build too"
NO_FINAL_RUN = (checked("self", [UNMET], "UNMET: 1 (met: 0)"),)


class TestTheFinalRunSettlesAllMet(unittest.TestCase):
    """`ALL MET` requires the worker's final full run on the current HEAD."""

    UNMET_RUN = checked("reverify", [UNMET], "UNMET: 1 (met: 0)")
    HANDOFF_RUN = checked("reverify", [UNMET], "HANDOFF REQUIRED: 1 abandoned (met: 0)")
    MET_SELF_RUN = checked("self", [MET], "ALL MET (1 met)")

    def test_a_reverify_reporting_unmet_refuses_all_met(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(FINAL_RUN, self.UNMET_RUN))
        self.assertEqual(code, 1)
        self.assertIn("still reports unmet", err)

    def test_a_reverify_summarising_as_handoff_refuses_all_met(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(FINAL_RUN, self.HANDOFF_RUN))
        self.assertEqual(code, 1)
        self.assertIn("still reports unmet", err)

    def test_a_later_self_run_cannot_override_the_final_run(self):
        """Only the newest worker reverify is closing proof, even if a self run follows."""
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(FINAL_RUN, self.UNMET_RUN, self.MET_SELF_RUN))
        self.assertEqual(code, 1)
        self.assertIn("final reverify still reports unmet", err)

    def test_a_ticket_with_no_reverify_cannot_close_as_all_met(self):
        code, err, _ = check(draft(counts=counts_line()), comments=NO_FINAL_RUN,
                             reverify=False)
        self.assertEqual(code, 1)
        self.assertIn("carries no worker reverify `ticket.checked` event", err)

    def test_a_reverify_typed_as_a_comment_is_not_a_reverify(self):
        """A hand-typed comment is prose, not the final run event."""
        typed = "reverify\nALL MET (1 met)\n\n" + MET
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(*NO_FINAL_RUN, typed), reverify=False)
        self.assertEqual(code, 1)
        self.assertIn("carries no worker reverify `ticket.checked` event", err)

    def test_a_failed_final_run_names_the_handoff(self):
        _, err, _ = check(draft(counts=counts_line()),
                          comments=(FINAL_RUN, self.UNMET_RUN))
        self.assertIn("HANDOFF REQUIRED", err)

    def test_handing_over_is_not_held_to_the_final_run(self):
        text = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                     counts=counts_line(met=0, abandoned=1, total=1))
        code, err, _ = check(text, comments=(FINAL_RUN, self.UNMET_RUN))
        self.assertEqual(code, 0, err)

    def test_handing_over_needs_no_reverify_at_all(self):
        text = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                     counts=counts_line(met=0, abandoned=1, total=1))
        code, err, _ = check(text, comments=NO_FINAL_RUN, reverify=False)
        self.assertEqual(code, 0, err)

    def test_a_final_run_on_an_older_commit_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), comments=(STALE_FINAL_RUN,))
        self.assertEqual(code, 1)
        self.assertIn("HEAD has moved on", err)

    def test_a_main_reverify_is_not_the_workers_final_run(self):
        main_run = checked("reverify", [MET], "ALL MET (1 met)", commit=HEAD,
                           actor="main")
        code, err, _ = check(draft(counts=counts_line()), comments=(main_run,),
                             reverify=False)
        self.assertEqual(code, 1)
        self.assertIn("carries no worker reverify", err)

    def test_a_later_main_reverify_does_not_hide_the_workers_final_run(self):
        main_run = checked("reverify", [UNMET], "UNMET: 1 (met: 0)", commit=HEAD,
                           actor="main")
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(FINAL_RUN, main_run), reverify=False)
        self.assertEqual(code, 0, err)


FENCED = """- [x] AC4: install.sh 装完五处配置
  CHECK:
  ```sh
  T=$(mktemp -d) && MMW_V2_HOME="$T" bash mmw-v2/install.sh >/dev/null
  python3 - <<'EOF'
  print("HOOKS-INSTALLED")
  EOF
  ```
  EXPECT: HOOKS-INSTALLED
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=16"""

UNFENCED = """- [x] AC4: install.sh 装完五处配置
  CHECK: python3 - <<'EOF'
print("HOOKS-INSTALLED")
EOF
  EXPECT: HOOKS-INSTALLED
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=16"""


class TestACheckThatNeededAFence(unittest.TestCase):
    """A draft carries its criteria verbatim, so it carries their fences too.

    Both readers of a ledger have to agree on where a command ends. `gates.mjs`
    refuses a bare line under a `CHECK:`; if the closing gate read the same ledger as
    fine, a ticket could close on criteria the engine would not even parse.
    """

    def test_a_fenced_command_does_not_hide_its_evidence(self):
        criteria = vt.parse_criteria(FENCED)
        self.assertEqual(len(criteria), 1)
        self.assertIn("EXPECT=matched", criteria[0]["evidence"])
        self.assertFalse(criteria[0]["stray"])

    def test_a_draft_whose_criterion_is_fenced_can_close(self):
        code, err, _ = check(draft(criteria=(FENCED,), counts=counts_line()))
        self.assertEqual(code, 0, err)

    def test_a_bare_line_under_a_check_is_refused_here_too(self):
        code, err, _ = check(draft(criteria=(UNFENCED,), counts=counts_line()))
        self.assertEqual(code, 1)
        self.assertIn("fenced block", err)

    def test_one_criterion_does_not_swallow_the_next(self):
        criteria = vt.parse_criteria(FENCED + "\n" + UNMET)
        self.assertEqual([c["id"] for c in criteria], ["AC4", "AC2"])
        self.assertEqual(criteria[1]["evidence"], "pending")


class TestEveryRefusalHasAWayOut(unittest.TestCase):
    """A refusal that names a next step has to accept that step when the worker takes it.

    `--closeout` is the one command a worker must get through to finish a ticket, and
    the loop it sits in has no cap: refused, edit the draft, run it again. A refusal
    whose advice the same gate then refuses is that loop with no exit at all.
    """

    def test_the_advice_in_a_refusal_is_a_draft_the_gate_accepts(self):
        code, err, _ = check(draft(counts=counts_line()), comments=NO_FINAL_RUN,
                             reverify=False)
        self.assertEqual(code, 1)
        self.assertIn("HANDOFF REQUIRED", err)

        # Now do exactly what it said, against the same ticket.
        advised = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                        counts=counts_line(met=0, abandoned=1, total=1))
        code, err, _ = check(advised, comments=NO_FINAL_RUN)
        self.assertEqual(code, 0, err)

    def test_no_refusal_asks_for_something_only_someone_else_can_write(self):
        """A hand-back remains possible regardless of the worker's final-run state."""
        for label, kwargs in (("no final run", {"comments": NO_FINAL_RUN}),
                              ("stale final run", {"comments": (STALE_FINAL_RUN,)}),
                              ("current final run", {"comments": (FINAL_RUN,)})):
            with self.subTest(ticket=label):
                code, err, _ = check(
                    draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                          counts=counts_line(met=0, abandoned=1, total=1)),
                    **kwargs)
                self.assertEqual(code, 0, err)


class TestGit(unittest.TestCase):
    def test_uncommitted_changes_to_tracked_files_are_refused(self):
        code, err, _ = check(draft(counts=counts_line()), dirty=[" M src/app.py"])
        self.assertEqual(code, 1)
        self.assertIn("uncommitted changes", err)

    def test_a_branch_that_does_not_contain_main_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), main_merged=False)
        self.assertEqual(code, 1)
        self.assertIn("does not contain its base main", err)

    def test_a_branch_that_changed_no_files_only_warns(self):
        code, err, _ = check(draft(counts=counts_line()), diff="")
        self.assertEqual(code, 0)
        self.assertIn("warning: this branch changes no files", err)

    def test_untracked_files_alone_do_not_refuse(self):
        code, err, _ = check(draft(counts=counts_line()), dirty=[])
        self.assertEqual(code, 0, err)


class TestFailedNeedsNoRoundCount(unittest.TestCase):
    """`failed` and `stuck` are told apart for whoever reads the ticket in the morning —
    it ran and did not pass, or it would not run — and the closeout holds neither to a
    number of self-runs: how many rounds a criterion gets is the worker's judgement,
    said on the `ABANDON:` line."""

    HANDOFF = "HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 1 met of 2"

    def failed_draft(self, kind="failed"):
        return draft(first=self.HANDOFF.replace("failed", kind),
                     criteria=(MET, UNMET),
                     abandons=(f"ABANDON: AC2 {kind} chromium kept crashing; tried …",),
                     counts=counts_line(met=1, abandoned=1, total=2))

    def test_failed_with_no_self_run_at_all_passes(self):
        code, err, _ = check(self.failed_draft(), comments=(FINAL_RUN,))
        self.assertEqual(code, 0, err)

    def test_failed_after_one_self_run_passes(self):
        code, err, _ = check(self.failed_draft(),
                             comments=(FINAL_RUN, *self_runs(UNMET, 1)))
        self.assertEqual(code, 0, err)

    def test_stuck_passes_the_same_way(self):
        code, err, _ = check(self.failed_draft(kind="stuck"), comments=(FINAL_RUN,))
        self.assertEqual(code, 0, err)


class TestTheFirstLineCarriesTheWholeRefusal(unittest.TestCase):
    """The first line says how many problems there are and how to read the rest, so a
    worker takes in the whole set at once. Naming only the first would have it fix one
    per run, and nothing caps that loop."""

    def three_problems(self):
        return draft(criteria=(MET, UNMET), counts=counts_line(met=9, total=9))

    def test_the_first_line_counts_the_problems(self):
        code, err, _ = check(self.three_problems())
        first = err.strip().splitlines()[0]
        self.assertTrue(first.startswith("closeout rejected, "), first)
        self.assertRegex(first, r"closeout rejected, \d+ problems?: ")

    def test_the_first_line_says_how_to_read_the_rest(self):
        code, err, _ = check(self.three_problems())
        self.assertIn("--check-only", err.strip().splitlines()[0])

    def test_a_single_problem_does_not_point_at_a_second(self):
        code, err, _ = check(draft(criteria=(MET,), counts=counts_line(met=4, total=4)))
        first = err.strip().splitlines()[0]
        self.assertIn("1 problem:", first)
        self.assertNotIn("--check-only", first)

    def test_the_later_problems_are_still_printed(self):
        code, err, _ = check(self.three_problems())
        lines = err.strip().splitlines()
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(l.startswith("also: ") for l in lines[1:]), lines)


class TestTheCriteriaTheFinalRunUsedAreTheCriteriaTheTicketStates(unittest.TestCase):
    """Closing proof must cover the criteria currently stated on the ticket."""

    REWRITTEN = MET.replace("CHECK: pytest -q tests/test_import.py",
                            "CHECK: pytest -q tests/test_import.py --deselect the-slow-one")

    def test_a_rewritten_check_after_the_final_run_is_refused(self):
        code, err, _ = check(
            draft(criteria=(self.REWRITTEN,), counts=counts_line()),
            comments=(FINAL_RUN, reverify_of([MET])))
        self.assertEqual(code, 1)
        self.assertIn("acceptance criteria have changed since the worker's final run", err)

    def test_a_criterion_added_after_the_final_run_is_refused(self):
        code, err, _ = check(
            draft(criteria=(MET, UNMET), counts=counts_line(met=1, unmet=1, total=2)),
            comments=(FINAL_RUN, reverify_of([MET])))
        self.assertEqual(code, 1)
        self.assertIn("acceptance criteria have changed since the worker's final run", err)

    def test_the_same_criteria_pass(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(FINAL_RUN, reverify_of([MET])))
        self.assertEqual(code, 0, err)

    def test_a_tick_or_a_piece_of_evidence_is_not_a_change(self):
        """Every run writes its own ticks and evidence; only the criterion and its
        command are the thing being compared."""
        ran = MET.replace("- [x]", "- [ ]").replace(
            "EVIDENCE: exit=0; EXPECT=matched; output-bytes=9", "EVIDENCE: pending")
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(FINAL_RUN, reverify_of([ran])))
        self.assertEqual(code, 0, err)

    def test_handing_over_is_not_held_to_this(self):
        text = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                     counts=counts_line(met=0, abandoned=1, total=1))
        code, err, _ = check(text, comments=(FINAL_RUN, reverify_of([MET])))
        self.assertEqual(code, 0, err)


class TestClosingReleasesTheTicket(unittest.TestCase):
    """A claim outlives the session that made it, and `advance`'s give-a-claim-back
    reads open tickets alone — so a claim left on a closed ticket is one nothing else
    ever takes off. Both ways out of a ticket drop it."""

    def test_closing_drops_the_assignee_with_the_label(self):
        """The close comes first: it is the change `ticket.passed` announces, and a close
        that fails leaves nothing changed to run the closeout again over."""
        with mock.patch.object(vt.subprocess, "run") as run:
            run.return_value.returncode = 0
            vt.close_ticket(77)
        closed = run.call_args_list[0].args[0]
        self.assertEqual(closed[:4], ["gh", "issue", "close", "77"])
        edit = run.call_args_list[1].args[0]
        self.assertEqual(edit[:4], ["gh", "issue", "edit", "77"])
        self.assertEqual(edit[edit.index("--remove-assignee") + 1], "@me")
        self.assertEqual(edit[edit.index("--remove-label") + 1], "ready-for-agent")


class TestHandingBackReleasesTheTicket(unittest.TestCase):
    """`status.py`'s frontier takes only unassigned tickets, so a ticket handed back still held
    by the worker that gave up is one nothing picks up again."""

    def test_the_label_swap_also_drops_the_assignee(self):
        with mock.patch.object(vt.subprocess, "run") as run:
            vt.hand_back_for_triage(77)
        args = run.call_args.args[0]
        self.assertEqual(args[:4], ["gh", "issue", "edit", "77"])
        self.assertEqual(args[args.index("--remove-assignee") + 1], "@me")
        self.assertEqual(args[args.index("--add-label") + 1], "needs-triage")
        self.assertEqual(args[args.index("--remove-label") + 1], "ready-for-agent")


class TestReviewFindingCompleteness(unittest.TestCase):
    def test_missing_finding_is_refused_by_check_only(self):
        rows = (
            "- Standards [documented-standard] docs/review.md:82 — Missing docs contract. — source: docs/AGENTS.md:17",
            "- Standards [Mysterious Name] tests/board.py:25 — The name obscures the subject. — source: docs/standards.md:37",
            "- Tests [Tautological] tests/events.py:256 — The test provides its expected value. — source: #430 AC2 CHECK",
            "- Tests [Only the happy path] tests/events.py:481 — It starts from empty state. — source: #430 AC2 CHECK",
        )
        review = event("reviewer.reported", "REVIEW abcdef0..1234567\n\n## In-ticket\n\n"
                       + "\n".join(rows) + "\n", base="abcdef0", head="1234567")
        for missing in rows:
            with self.subTest(missing=missing):
                remaining = [row + " — fixed " + HEAD for row in rows if row != missing]
                text = draft(counts=counts_line()) + "\nReview findings:\n" \
                       + "\n".join(remaining) + "\n"
                code, err, seen = check(text, comments=(review,))
                self.assertEqual(code, 1)
                self.assertIn(missing, err)
                self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_old_review_rows_accept_fixed_and_refuted_responses(self):
        row = "- Spec src/app.py:12 — the importer skips a row"
        review = event("reviewer.reported", "REVIEW abcdef0..1234567\n\n## In-ticket\n\n"
                       + row + "\n", base="abcdef0", head="1234567")
        for response in ("fixed " + HEAD, "refuted: the fixture contains the row"):
            with self.subTest(response=response):
                text = draft(counts=counts_line()) + "\nReview findings:\n" \
                       + row + " — " + response + "\n"
                code, err, seen = check(text, comments=(review,))
                self.assertEqual(code, 0, err)
                self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_changed_source_does_not_satisfy_the_latest_review(self):
        row = "- Tests [Tautological] tests/events.py:256 — The test provides its expected value. — source: #430 AC2 CHECK"
        review = event("reviewer.reported", "REVIEW abcdef0..1234567\n\n## In-ticket\n\n"
                       + row + "\n", base="abcdef0", head="1234567")
        changed = row.replace("#430 AC2 CHECK", "#430 AC1 CHECK")
        text = draft(counts=counts_line()) + "\nReview findings:\n" \
               + changed + " — fixed " + HEAD + "\n"
        code, err, _ = check(text, comments=(review,))
        self.assertEqual(code, 1)
        self.assertIn(row, err)


class TestNoSideEffectOnFail(unittest.TestCase):
    """A refused draft leaves the ticket exactly as it was."""

    def test_a_refused_draft_posts_nothing_and_closes_nothing(self):
        text = draft(criteria=(MET,), counts=counts_line(met=9, total=9))
        code, _, seen = check(text, check_only=False)
        self.assertEqual(code, 1)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_check_only_passes_without_touching_the_ticket(self):
        code, err, seen = check(draft(counts=counts_line()), check_only=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})

    def test_all_met_posts_closes_and_passed_carries_into(self):
        text = draft(counts=counts_line())
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual([(n, posted_as(b)) for n, b in seen["posted"]],
                         [(77, (text, "ticket.passed"))])
        self.assertEqual(seen["closed"], [77])
        self.assertEqual(seen["handed"], [])
        payload = vt.events.parse(seen["posted"][0][1])[1]
        self.assertEqual(payload["into"], "spec-337")

    def test_handoff_posts_the_draft_and_swaps_the_label(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual([(n, posted_as(b)) for n, b in seen["posted"]],
                         [(77, (text, "ticket.returned"))])
        payload = vt.events.parse(seen["posted"][0][1])[1]
        self.assertEqual(payload["abandoned"], [
            {"ac": "AC2", "kind": "stuck",
             "reason": "chromium will not start here; tried the bundled build too"}])
        self.assertEqual(payload["counts"],
                         {"met": 1, "unmet": 0, "abandoned": 1, "total": 2})
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [77])

    def test_handoff_needs_no_into_and_returned_carries_none(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium will not start",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, seen = check(text, check_only=False, started_event=started(base="main"))
        self.assertEqual(code, 0, err)
        payload = vt.events.parse(seen["posted"][0][1])[1]
        self.assertEqual(payload["event"], "ticket.returned")
        self.assertNotIn("into", payload)

    def test_resume_posts_the_missing_pass_without_pushing_again(self):
        claimed = event("ticket.claimed", "Claimed", login=ME)
        text = draft(counts=counts_line())
        pushed = []
        code, err, seen = check(text, comments=(claimed, FINAL_RUN), state="CLOSED",
                                assignees=(), labels=(), reason="COMPLETED", check_only=False,
                                pushed=pushed)
        self.assertEqual(code, 0, err)
        self.assertEqual(pushed, [])
        self.assertEqual(seen["closed"], [])
        self.assertEqual(posted_as(seen["posted"][0][1]), (text, "ticket.passed"))

    def test_a_hand_back_gives_the_slot_back_and_a_close_leaves_it_to_the_landing(self):
        """A handed-back ticket's work is over for the night; kept, its slot would hold
        the product from every other ticket until somebody landed it."""
        handoff = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                        criteria=(MET, UNMET),
                        abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                        counts=counts_line(met=1, abandoned=1, total=2))
        for text, expected in ((handoff, 1), (draft(counts=counts_line()), 0)):
            gave = []
            with mock.patch.object(vt, "give_slot_back",
                                   side_effect=lambda root: gave.append(root)):
                code, err, _ = check(text, check_only=False)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(gave), expected, text.splitlines()[0])

    def test_a_ticket_someone_else_holds_is_refused(self):
        code, err, seen = check(draft(counts=counts_line()), assignees=("someone-else",),
                                check_only=False)
        self.assertEqual(code, 1)
        self.assertIn("not assigned to you", err)
        self.assertEqual(seen["posted"], [])

    def test_an_already_closed_ticket_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), state="CLOSED", check_only=False)
        self.assertEqual(code, 1)
        self.assertIn("already CLOSED", err)


def write_checks(root: Path, commands):
    """A consuming repository's `.mmw/target.json` with only the `checks` key."""
    (root / ".mmw").mkdir(parents=True, exist_ok=True)
    (root / ".mmw" / "target.json").write_text(
        json.dumps({"checks": commands}), encoding="utf-8")


def repo_checks(posted):
    """The payload of the one `ticket.checked` (run `repo-checks`) among posted bodies."""
    found = [vt.events.parse(b)[1] for _, b in posted]
    found = [p for p in found if p["event"] == "ticket.checked" and p["run"] == "repo-checks"]
    assert len(found) == 1, found
    return found[0]


class TestTargetJsonChecks(unittest.TestCase):
    """After the draft is accepted and before the ticket closes, `checks` in
    `.mmw/target.json` run at the repository root. They are the consuming repository's
    own 'run the tests' rule, made a gate; `--reverify` and `--lint` never run them.
    Their run is a `ticket.checked` event of its own, run `repo-checks`."""

    def test_failing_checks_do_not_close_and_the_event_carries_each_failure(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [
                "python3 -c \"import sys; [print(i) for i in range(1, 26)]; sys.exit(1)\"",
                "python3 -c \"raise SystemExit(2)\"",
            ])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [])
        self.assertEqual(len(seen["posted"]), 1)
        payload = repo_checks(seen["posted"])
        self.assertEqual((payload["result"], payload["commit"]), ("unmet", HEAD))
        self.assertEqual(payload["counts"], {"passed": 0, "total": 2})
        commands = payload["commands"]
        self.assertEqual(len(commands), 2)
        self.assertIn("raise SystemExit(2)", commands[1]["command"])
        tail = commands[0]["tail"].splitlines()
        self.assertEqual((tail[0], tail[-1], len(tail)), ("6", "25", 20))
        self.assertNotIn(text.strip(), seen["posted"][0][1])

    def test_passing_checks_are_an_event_before_the_closing_comment(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, ["true", "true"])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["closed"], [77])
        payload = repo_checks(seen["posted"])
        self.assertEqual((payload["result"], payload["counts"]),
                         ("met", {"passed": 2, "total": 2}))
        self.assertEqual(posted_as(seen["posted"][1][1]), (text, "ticket.passed"))

    def test_repo_checks_see_mmw_base_ref(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [
                "python3 -c \"import os,sys; sys.exit(os.environ.get('MMW_BASE_REF') "
                "!= 'origin/spec-337')\"",
            ])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual(repo_checks(seen["posted"])["result"], "met")

    def test_an_entry_with_its_own_timeout_is_held_to_it(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [
                {"run": "python3 -c \"import time; time.sleep(5)\"", "timeout": 1},
                "true",
            ])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        payload = repo_checks(seen["posted"])
        self.assertIn("timed out after 1s", payload["commands"][0]["tail"])

    def test_an_entry_that_is_neither_string_nor_run_object_does_not_close(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [{"cmd": "true"}])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        payload = repo_checks(seen["posted"])
        self.assertEqual(payload["result"], "unmet")
        self.assertIn("neither a string", payload["problem"])

    def test_no_checks_key_leaves_closeout_unchanged(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(
                json.dumps({"reach": "echo"}), encoding="utf-8")
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual([(n, posted_as(b)) for n, b in seen["posted"]],
                         [(77, (text, "ticket.passed"))])
        self.assertEqual(seen["closed"], [77])

    def test_reverify_and_lint_do_not_run_the_target_json_checks(self):
        body = ("## Worker\n\njunior-worker\n\n## Acceptance criteria\n\n"
                "- [ ] AC1: something a stranger could judge\n"
                "  CHECK: python3 -c \"print('ok')\"\n"
                "  EXPECT: ok\n  EVIDENCE: pending\n")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c",
                            "user.name=t", "commit", "-q", "--allow-empty", "-m", "base"],
                           check=True)
            marker = root / "ran.marker"
            write_checks(root, [f"touch '{marker}'"])
            posted = []
            with mock.patch.object(vt, "repo_root", return_value=root), \
                 mock.patch.object(vt, "fetch_body", return_value=body), \
                 mock.patch.object(vt, "fetch_ticket",
                                   return_value={"labels": [{"name": "ready-for-agent"},
                                                            {"name": "junior-worker"}],
                                                 "state": "OPEN"}), \
                 mock.patch.object(vt, "fetch_comments", return_value=[]), \
                 mock.patch.object(vt, "fetch_parent", return_value=None), \
                 mock.patch.object(vt, "post_comment",
                                   side_effect=lambda n, b: posted.append(b)):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    vt.run_lint(77)
                    code = vt.run_checks(77, True, None)
            self.assertEqual(code, 0)
            self.assertEqual([vt.events.parse(b)[1]["run"] for b in posted], ["reverify"])
            self.assertFalse(marker.exists())

    def test_malformed_checks_do_not_close(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(
                json.dumps({"checks": "pytest -q"}), encoding="utf-8")
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        self.assertIn("not a list", repo_checks(seen["posted"])["problem"])

    def test_handoff_does_not_run_checks(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, ["false"])
            text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                         criteria=(MET, UNMET),
                         abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                         counts=counts_line(met=1, abandoned=1, total=2))
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [77])
        self.assertEqual([posted_as(b) for _, b in seen["posted"]],
                         [(text, "ticket.returned")])


class TestCloseoutPush(unittest.TestCase):
    @staticmethod
    def git(*args):
        return subprocess.run(["git", *args], check=True, capture_output=True,
                              text=True).stdout.strip()

    def sh(self, repo: Path, *args):
        return self.git("-C", str(repo), *args)

    def make_repo(self, root: Path):
        remote = root / "origin.git"
        work = root / "work"
        self.git("init", "-q", "--bare", str(remote))
        self.git("init", "-q", "-b", "issue-77", str(work))
        self.sh(work, "config", "user.email", "t@t")
        self.sh(work, "config", "user.name", "t")
        (work / "base.txt").write_text("base\n")
        self.sh(work, "add", "-A")
        self.sh(work, "commit", "-qm", "base")
        base = self.sh(work, "rev-parse", "HEAD")
        self.sh(work, "remote", "add", "origin", str(remote))
        return work, remote, base

    def add_ticket_commit(self, work: Path):
        (work / "work.txt").write_text("done\n")
        self.sh(work, "add", "-A")
        self.sh(work, "commit", "-qm", "ticket work")
        return self.sh(work, "rev-parse", "HEAD")

    def run_closeout(self, work: Path, base: str, head: str):
        text = draft(counts=counts_line())
        ledger = ledger_of(text)
        comments = [started(base=base, into="spec-337"),
                    reverify_of(ledger).replace(HEAD, head)]
        posted, closed = [], []
        real_git = vt.git

        def git_in_worktree(*args, cwd=None):
            return real_git(*args, cwd=cwd or work)

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "closeout.md"
            path.write_text(text, encoding="utf-8")
            with mock.patch.object(vt, "repo_root", return_value=work), \
                 mock.patch.object(vt, "fetch_comments", return_value=comments), \
                 mock.patch.object(vt, "fetch_body", return_value=acceptance_body(ledger)), \
                 mock.patch.object(vt, "fetch_ticket", return_value={
                     "state": "OPEN", "labels": [{"name": "ready-for-agent"}],
                     "assignees": [{"login": ME}], "blockedBy": {"nodes": []}}), \
                 mock.patch.object(vt, "gh_login", return_value=ME), \
                 mock.patch.object(vt, "git", side_effect=git_in_worktree), \
                 mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)), \
                 mock.patch.object(vt, "close_ticket", side_effect=lambda n: closed.append(n)):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                    code = vt.run_closeout(77, path, False)
        return code, err.getvalue(), posted, closed

    def test_closeout_pushes_the_final_run_commit(self):
        with TemporaryDirectory() as tmp:
            work, remote, base = self.make_repo(Path(tmp))
            head = self.add_ticket_commit(work)
            code, err, posted, closed = self.run_closeout(work, base, head)
            remote_head = self.sh(remote, "rev-parse", "refs/heads/issue-77")
        self.assertEqual(code, 0, err)
        self.assertEqual(remote_head, head)
        self.assertEqual(closed, [77])
        self.assertEqual(vt.events.parse(posted[-1])[1]["into"], "spec-337")

    def test_closeout_refuses_when_the_push_is_rejected(self):
        with TemporaryDirectory() as tmp:
            work, remote, base = self.make_repo(Path(tmp))
            self.sh(work, "push", "-q", "origin", "HEAD:refs/heads/issue-77")
            before = self.sh(remote, "rev-parse", "refs/heads/issue-77")
            head = self.add_ticket_commit(work)
            hook = remote / "hooks" / "pre-receive"
            hook.write_text("#!/bin/sh\necho protected branch >&2\nexit 1\n")
            hook.chmod(0o755)
            code, err, posted, closed = self.run_closeout(work, base, head)
            after = self.sh(remote, "rev-parse", "refs/heads/issue-77")
        self.assertNotEqual(code, 0)
        self.assertIn("protected branch", err)
        self.assertEqual((before, after), (base, base))
        self.assertEqual(closed, [])
        self.assertEqual(posted, [])


if __name__ == "__main__":
    unittest.main()
