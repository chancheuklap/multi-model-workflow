"""Shared criteria engine behaviour against fixed ticket bodies; never posts."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import SCRIPT, checked, event, load, started

vt = load()

UI_ACCEPTANCE = SCRIPT.parents[2] / "ui-acceptance" / "scripts"
HEAD_RE = r"^[0-9a-f]{40}$"


def current_evidence(check: str, expect: str) -> str:
    """A pass line as gate-check writes it for this CHECK and EXPECT with no CWD:
    `definition-sha256` is `gateDefinitionDigest` in `mmw-v2/upstream-unlazy/scripts/lib/gates.mjs`."""
    definition = json.dumps(["unlazy.gate-definition", 1, check, expect, None],
                            separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(definition.encode("utf-8")).hexdigest()
    return (f"automatic-evidence=v1; definition-sha256={digest}; exit=0; EXPECT=matched; "
            f"output-sha256={'a' * 64}; output-bytes=13; shell=/bin/sh; cwd=.")
STARTED = started(ticket=1, into="spec-337")


def ticket(*criteria: str, owns: str = "- src/**") -> str:
    return "## Owns\n\n" + owns + "\n\n## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"


def payload_of(comment: str) -> dict:
    what, payload = vt.events.parse(comment)
    assert what == "event", (what, payload, comment)
    return payload


class LedgerRun(unittest.TestCase):
    """Run the shared engine without writing tracker state."""

    def run_ticket(self, body, reverify=False, comments=None, outside=(), started_event=STARTED):
        history = ([] if started_event is None else [started_event]) + (comments or [])
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_comments", return_value=history), \
             mock.patch.object(vt, "outside_owns", return_value=list(outside)), \
             mock.patch.object(vt, "current_branch", return_value="issue-1"), \
             mock.patch.object(vt, "post_comment") as posted:
            result = vt.run_criteria(1, reverify)
        posted.assert_not_called()
        self.result = result
        return result.returncode, result.ledger, result.output



class TestACheckMaySpanLines(LedgerRun):
    """A CHECK is a shell command; a command longer than a line goes in a fenced block."""

    def test_the_lines_inside_the_fence_are_the_command(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK:",
            "  ```sh",
            "  python3 -c \"",
            "rows = 6",
            "print('wrote', rows, 'rows')\"",
            "  ```",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0, comment)
        self.assertIn("- [x] AC1:", comment)

    def test_the_evidence_lands_after_the_closing_fence(self):
        _, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK:",
            "  ```sh",
            "  python3 -c \"print('wrote 6 rows')\"",
            "  ```",
            "  EXPECT: wrote 6 rows",
        ))
        body = comment.splitlines()
        evidence = next(i for i, l in enumerate(body) if l.strip().startswith("EVIDENCE:"))
        command = next(i for i, l in enumerate(body) if "wrote 6 rows" in l and "print" in l)
        self.assertGreater(evidence, command)

    def test_a_bare_line_under_a_check_says_to_use_a_fence(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: python3 -c \"",
            "print('wrote 6 rows')\"",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 2)
        self.assertEqual(comment, "", "a ledger it could not read is not a result to post")
        self.assertIn("fenced block", printed)


class TestDoubleCondition(LedgerRun):
    def test_expected_text_does_not_pass_a_failed_process(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer reports the row count it wrote",
            "  CHECK: echo ok; exit 3",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] AC1:", comment)
        # The failure is recorded, not left `pending`, and it says which of the two
        # conditions failed: the output matched, the exit code did not.
        self.assertIn("exit=3", comment)
        self.assertIn("EXPECT=matched", comment)
        self.assertNotIn("EVIDENCE: pending", comment)
        self.assertEqual(self.result.criteria[0]["ticked"], False)

    def test_exit_zero_with_unmatched_output_does_not_pass(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 5 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] AC1:", comment)

    def test_exit_zero_and_matching_output_passes_with_evidence(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("- [x] AC1:", comment)
        self.assertRegex(comment, r"EVIDENCE: automatic-evidence=v1; definition-sha256=[0-9a-f]{64}; exit=0;")

    def test_a_criterion_with_no_check_is_never_run_and_never_ticked(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
            "- [ ] AC2: the empty-state copy matches the baseline word for word",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertNotIn("RUN  AC:AC2", printed)
        self.assertIn("- [ ] AC2:", comment)
        self.assertEqual([c["id"] for c in self.result.criteria if not c["ticked"]], ["AC2"])




class TestMmwTicketInCheckEnv(LedgerRun):
    """The CHECK shell sees the ticket number, not an empty leftover from the host."""

    def test_mmw_ticket_in_check_env(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the check shell sees the ticket number",
            "  CHECK: echo T=$MMW_TICKET",
            "  EXPECT: T=1",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0, comment)
        self.assertIn("- [x] AC1:", comment)


class TestMmwBaseRefInCheckEnv(LedgerRun):
    """Both criterion runs compare against the base branch recorded at start."""

    BODY = ticket(
        "- [ ] AC1: the check shell sees the fetched integration base",
        "  CHECK: echo B=$MMW_BASE_REF",
        "  EXPECT: B=origin/spec-337",
        "  EVIDENCE: pending",
    )

    def test_the_workers_own_run_sees_the_base_ref(self):
        code, comment, _ = self.run_ticket(self.BODY)
        self.assertEqual(code, 0, comment)

    def test_reverify_sees_the_same_base_ref(self):
        code, comment, _ = self.run_ticket(self.BODY, reverify=True)
        self.assertEqual(code, 0, comment)


class TestNoRoundCap(LedgerRun):
    """How many rounds a criterion gets is the worker's own judgement: no run names a
    limit, however many runs of its own the ticket already carries."""

    FAILING = ("- [ ] AC1: the importer writes six rows\n"
               "  CHECK: echo 'wrote 4 rows'; exit 1\n"
               "  EXPECT: wrote 6 rows\n"
               "  EVIDENCE: pending")

    def prior_runs(self, rounds: int) -> list[str]:
        return [checked("self", self.FAILING, "UNMET: 1", ticket=1)] * rounds

    def test_no_run_names_a_limit(self):
        for rounds in (0, 2, 5):
            with self.subTest(rounds=rounds):
                _, comment, _ = self.run_ticket(ticket(self.FAILING),
                                                comments=self.prior_runs(rounds))
                self.assertNotIn("ROUND LIMIT", comment)
                self.assertNotIn("ABANDON", comment)


class TestCheckTimeout(LedgerRun):
    """One number per ticket, read off the ticket body, never lowered."""

    def body(self, *timeouts: str) -> str:
        lines = []
        for i, t in enumerate(timeouts, 1):
            lines += [f"- [ ] AC{i}: thing {i}", f"  CHECK: echo ok{i}", f"  EXPECT: ok{i}",
                      "  EVIDENCE: pending"]
            if t:
                lines.append(f"  TIMEOUT: {t}")
        return ticket(*lines)

    def test_the_default_is_ten_minutes(self):
        self.assertEqual(vt.check_timeout(self.body("")), 600)

    def test_a_ticket_raises_it_with_the_largest_timeout_line(self):
        self.assertEqual(vt.check_timeout(self.body("900", "", "1500")), 1500)

    def test_a_ticket_cannot_lower_it(self):
        self.assertEqual(vt.check_timeout(self.body("30")), 600)

    def test_the_ledger_handed_to_gate_check_carries_no_timeout_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = vt.write_ledger(self.body("900"), Path(tmp))
            text = ledger.read_text(encoding="utf-8")
        self.assertNotIn("TIMEOUT", text)
        self.assertIn("CHECK: echo ok1", text)

    def test_gate_check_is_always_given_the_number(self):
        seen: list[list[str]] = []
        real = vt.subprocess.run

        def spy(cmd, *a, **kw):
            seen.append(list(cmd))
            return real(cmd, *a, **kw)

        with mock.patch.object(vt.subprocess, "run", side_effect=spy):
            code, comment, _ = self.run_ticket(self.body("1200"))
        gate = next(c for c in seen if any(str(x).endswith("gate-check.mjs") for x in c))
        self.assertIn("--timeout", gate)
        self.assertEqual(gate[gate.index("--timeout") + 1], "1200")
        self.assertEqual(code, 0)
        self.assertIn("[x] AC1", comment)

    def test_a_reverify_reads_the_same_number_off_the_body(self):
        seen: list[list[str]] = []
        real = vt.subprocess.run

        def spy(cmd, *a, **kw):
            seen.append(list(cmd))
            return real(cmd, *a, **kw)

        body = self.body("1200")
        previous = checked("self", ["- [x] AC1: thing 1", "  CHECK: echo ok1", "  EXPECT: ok1",
                                    "  TIMEOUT: 1200",
                                    "  EVIDENCE: exit=0; EXPECT=matched"], ticket=1)
        with mock.patch.object(vt.subprocess, "run", side_effect=spy):
            self.run_ticket(body, reverify=True, comments=[previous])
        gate = next(c for c in seen if any(str(x).endswith("gate-check.mjs") for x in c))
        self.assertEqual(gate[gate.index("--timeout") + 1], "1200")

    def test_lint_refuses_a_timeout_that_is_not_seconds(self):
        for bad in ("0", "-5", "ten", "1.5"):
            with self.subTest(value=bad):
                findings = vt.lint_timeouts(self.body(bad))
                self.assertEqual(len(findings), 1)
                self.assertIn("AC1", findings[0])
        self.assertEqual(vt.lint_timeouts(self.body("120")), [])




class TestLedgerWithResults(unittest.TestCase):
    """A run's ticks and evidence written back onto the criteria the body states."""

    LINES = ["- [ ] AC1: a", "  CHECK: true", "  EXPECT: a", "  EVIDENCE: pending",
             "- [ ] AC2: b", "  CHECK: false", "  EXPECT: b", "  EVIDENCE: pending"]

    def test_ticks_and_evidence_come_from_the_run(self):
        out = vt.ledger_with_results(self.LINES, [
            {"id": "AC1", "met": True, "evidence": "exit=0; EXPECT=matched"},
            {"id": "AC2", "met": False, "evidence": "exit=1"}])
        self.assertEqual(out, [
            "- [x] AC1: a", "  CHECK: true", "  EXPECT: a", "  EVIDENCE: exit=0; EXPECT=matched",
            "- [ ] AC2: b", "  CHECK: false", "  EXPECT: b", "  EVIDENCE: exit=1"])

    def test_a_criterion_the_run_does_not_name_is_left_as_the_body_has_it(self):
        out = vt.ledger_with_results(self.LINES, [{"id": "AC2", "met": True, "evidence": "e"}])
        self.assertEqual(out[:4], self.LINES[:4])
        self.assertEqual(out[4], "- [x] AC2: b")

    def test_evidence_is_written_after_the_last_attribute_when_the_body_has_none(self):
        out = vt.ledger_with_results(
            ["- [ ] AC1: a", "  CHECK: true", "  EXPECT: a", "", "- [ ] AC2: b",
             "  CHECK: true", "  EXPECT: b"],
            [{"id": "AC1", "met": True, "evidence": "e1"},
             {"id": "AC2", "met": True, "evidence": "e2"}])
        self.assertEqual(out, ["- [x] AC1: a", "  CHECK: true", "  EXPECT: a", "  EVIDENCE: e1",
                               "", "- [x] AC2: b", "  CHECK: true", "  EXPECT: b",
                               "  EVIDENCE: e2"])

    def test_a_criterion_shaped_line_inside_a_fenced_check_is_the_command(self):
        lines = ["- [ ] AC1: a", "  CHECK:", "  ```sh", "  cat <<'EOF'",
                 "- [ ] AC9: printed, not a criterion", "  EOF", "  ```", "  EXPECT: AC9"]
        out = vt.ledger_with_results(lines, [{"id": "AC1", "met": True, "evidence": "e"},
                                             {"id": "AC9", "met": True, "evidence": "x"}])
        self.assertEqual(out[0], "- [x] AC1: a")
        self.assertIn("- [ ] AC9: printed, not a criterion", out)
        self.assertEqual(out[-1], "  EVIDENCE: e")
        self.assertEqual([c["id"] for c in vt.parse_criteria("\n".join(out))], ["AC1"])


class TestCarriedLedger(unittest.TestCase):
    """`--reverify` carries the newest run's ticks and evidence, unless the ticket has
    rewritten its criteria since."""

    BODY = ("## Acceptance criteria\n\n"
            "- [ ] AC1: the importer writes six rows\n"
            "  CHECK: pytest test_importer_v5.py\n"
            "  EXPECT: /^\\d+ passed/m\n"
            "  EVIDENCE: pending\n\n"
            "## Blocked by\n")
    SAME = ["- [x] AC1: the importer writes six rows",
            "  CHECK: pytest test_importer_v5.py",
            "  EXPECT: /^\\d+ passed/m",
            "  EVIDENCE: exit=0; EXPECT=matched"]

    def test_a_run_of_the_same_criteria_is_carried(self):
        self.assertEqual(vt.carried_ledger(self.BODY, [checked("self", self.SAME)]), self.SAME)

    def test_a_run_whose_command_the_ticket_has_rewritten_is_dropped(self):
        """The old command names a file a later decision renamed: the body wins."""
        stale = [line.replace("v5", "v4") for line in self.SAME]
        self.assertEqual(vt.carried_ledger(self.BODY, [checked("self", stale)]), [])

    def test_the_newest_of_the_workers_run_and_a_reverify_is_carried(self):
        unmet = [self.SAME[0].replace("[x]", "[ ]")] + self.SAME[1:3] + ["  EVIDENCE: exit=1"]
        comments = [checked("self", unmet), checked("reverify", self.SAME)]
        self.assertEqual(vt.carried_ledger(self.BODY, comments), self.SAME)
        comments = [checked("reverify", self.SAME), checked("self", unmet)]
        self.assertEqual(vt.carried_ledger(self.BODY, comments)[0], unmet[0])

    def test_no_run_and_the_repository_checks_carry_nothing(self):
        self.assertEqual(vt.carried_ledger(self.BODY, []), [])
        repo = vt.events.build("ticket.checked", ticket=77, line="checks", run="repo-checks",
                               commit="0" * 40, result="met")
        self.assertEqual(vt.carried_ledger(self.BODY, [repo]), [])


class TestOwns(unittest.TestCase):
    def test_globs_drop_the_new_marker_and_the_none_line(self):
        body = "## Owns\n\n- src/import/**\n- src/import/ui/** (new)\n\n## Acceptance criteria\n"
        self.assertEqual(vt.owns_globs(body), ["src/import/**", "src/import/ui/**"])
        self.assertEqual(vt.owns_globs("## Owns\n\n- None\n\n## Blocked by\n"), [])

    def test_globs_drop_wrapping_backticks(self):
        body = ("## Owns\n\n- `src/import/**`\n- `src/import/ui/**` (new)\n\n"
                "## Acceptance criteria\n")
        self.assertEqual(vt.owns_globs(body), ["src/import/**", "src/import/ui/**"])


class TestLint(unittest.TestCase):
    def lint(self, body: str, labels=()):
        """`--lint` on a ticket whose text is `body` and whose labels are `labels`.

        The tracker is reached for three things and all three are answered here: the
        body, the parent link, and the labels the worker rule reads. Left unpatched,
        `fetch_ticket` runs `gh issue view` against the real repository, which makes
        a unit test wait on the network and fail when it is not there."""
        ticket_json = {"state": "OPEN", "labels": [{"name": name} for name in labels],
                       "assignees": [], "blockedBy": []}
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             mock.patch.object(vt, "fetch_ticket", return_value=ticket_json):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_lint(1)
        return code, out.getvalue()

    def test_the_worker_label_the_tracker_carries_is_what_the_rule_reads(self):
        """A ticket in the agent queue with two worker labels is the worker ERROR, one
        with none a WARN, and it is the labels that decide it, not anything in the body."""
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: /wrote 6 rows/",
            "  EVIDENCE: pending",
        )
        code, printed = self.lint(body, labels=["ready-for-agent", "junior-worker", "senior-worker"])
        self.assertEqual(code, 1)
        self.assertIn("worker-label", printed)
        code, printed = self.lint(body, labels=["ready-for-agent"])
        self.assertEqual(code, 0)
        self.assertIn("WARN", printed)
        self.assertIn("worker-label", printed)
        self.assertEqual(self.lint(body, labels=["needs-triage"])[0], 0)

    def test_a_weak_expectation_is_reported_without_failing_the_run(self):
        """A warning is for a person to weigh, so it must not decide the exit code."""
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("weak-expect", printed)

    def test_a_ticket_with_no_criteria_section_is_not_a_finding(self):
        """A `ready-for-human` ticket holds one thing to look at, and no criteria."""
        body = "## Parent\n\n#76\n\n## Blocked by\n\n- #96\n"
        with mock.patch.object(vt, "lint_ticket_graph", return_value=0):
            code, printed = self.lint(body)
        self.assertEqual(code, 0)
        self.assertIn("carries no `## Acceptance criteria`", printed)
        self.assertNotIn("zero live gates", printed)

    def test_a_criterion_with_no_command_fails_the_run(self):
        """Nobody but the ticket's own author decides it, which the section forbids."""
        code, printed = self.lint(ticket(
            "- [ ] AC1: the wording reads well",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("manual-gate", printed)
        self.assertIn("ERROR", printed)

    def test_lint_runs_no_check_and_posts_no_comment(self):
        posted: list[str] = []
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo LINT-MUST-NOT-RUN-THIS",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        )
        with mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            _, printed = self.lint(body)
        self.assertNotIn("LINT-MUST-NOT-RUN-THIS\n", printed.replace("CHECK: echo LINT-MUST-NOT-RUN-THIS", ""))
        self.assertEqual(posted, [])

    def test_a_sound_ledger_is_clean(self):
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: /wrote 6 rows/",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("LINT OK", printed)


def git_repo(root: Path):
    """A repository with one commit at `root`; returns a function running git there."""
    def sh(*args, cwd=root):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    sh("init", "-q", "-b", "main")
    sh("config", "user.email", "t@t")
    sh("config", "user.name", "t")
    return sh


class TestOutsideOwns(unittest.TestCase):
    """`outside_owns` counts this ticket's own commits, not what a merge rides in."""

    def repo(self, tmp):
        sh = git_repo(tmp)
        (tmp / "base.txt").write_text("base\n")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        return sh

    def test_a_merged_branch_does_not_count_as_this_tickets_work(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            # The earlier ticket's branch commits its own file.
            sh("checkout", "-qb", "issue-2")
            (tmp / "theirs.txt").write_text("theirs\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-2 work")
            # This ticket's branch commits one file inside Owns, one outside...
            sh("checkout", "-q", "main")
            sh("checkout", "-qb", "issue-4")
            (tmp / "mine.txt").write_text("mine\n")
            (tmp / "stray.txt").write_text("stray\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-4 work")
            # ...then merges the earlier ticket's branch to build on it.
            sh("merge", "-q", "--no-ff", "-m", "merge issue-2", "issue-2")
            self.assertEqual(vt.outside_owns(["mine.txt"], tmp, "main"), ["stray.txt"])

    def test_backticked_owns_that_cover_the_commit_report_none(self):
        """A `## Owns` bullet written `` `path` `` still excludes that path."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "issue-4")
            (tmp / "mine.txt").write_text("mine\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-4 work")
            globs = vt.owns_globs("## Owns\n\n- `mine.txt`\n")
            self.assertEqual(globs, ["mine.txt"])
            fields = vt.outside_owns_fields(4, globs, tmp, "main")
            self.assertEqual(fields, {"outside_owns": []})
            self.assertEqual(vt.outside_owns_text(fields), "Outside Owns: None")

    def test_the_list_is_answered_on_the_tickets_own_branch(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "issue-4")
            (tmp / "stray.txt").write_text("stray\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-4 work")
            fields = vt.outside_owns_fields(4, ["mine.txt"], tmp, "main")
            self.assertEqual(fields, {"outside_owns": ["stray.txt"]})
            self.assertEqual(vt.outside_owns_text(fields), "Outside Owns: stray.txt")

    def test_the_list_is_left_unanswered_on_the_branch_tickets_merge_into(self):
        """A re-run there is walking every ticket's commits, which answers nothing."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "spec-branch")
            (tmp / "stray.txt").write_text("stray\n")
            sh("add", "-A")
            sh("commit", "-qm", "somebody else's work")
            fields = vt.outside_owns_fields(4, ["mine.txt"], tmp, "main")
            self.assertEqual(fields, {"outside_owns_unchecked": "spec-branch"})
            self.assertEqual(
                vt.outside_owns_text(fields),
                "Outside Owns: not checked on spec-branch, which carries more than "
                "this ticket")

    def test_outside_owns_starts_at_worker_started_base(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "spec-x")
            (tmp / "spec-start.txt").write_text("base branch before ticket\n")
            sh("add", "-A")
            sh("commit", "-qm", "spec start")
            base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp, check=True,
                                  capture_output=True, text=True).stdout.strip()
            sh("checkout", "-qb", "issue-4")
            (tmp / "mine.txt").write_text("mine\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue work")
            sh("checkout", "-q", "spec-x")
            (tmp / "spec-later.txt").write_text("base branch after ticket\n")
            sh("add", "-A")
            sh("commit", "-qm", "base moved")
            sh("checkout", "-q", "issue-4")
            sh("merge", "-q", "--no-ff", "-m", "merge latest base", "spec-x")
            body = ticket("- [ ] AC1: the check runs",
                          "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending",
                          owns="- mine.txt")
            posted = []
            with mock.patch.object(vt, "repo_root", return_value=tmp), \
                 mock.patch.object(vt, "fetch_body", return_value=body), \
                 mock.patch.object(vt, "fetch_comments",
                                   return_value=[started(ticket=4, base=base, into="spec-x")]), \
                 mock.patch.object(vt, "post_comment",
                                   side_effect=lambda n, b: posted.append(b)):
                with redirect_stdout(io.StringIO()):
                    result = vt.run_criteria(4, False)
                    code = result.returncode
            self.assertEqual(code, 0, posted)
            self.assertEqual(result.outside_owns, {"outside_owns": []})
            self.assertEqual(posted, [])
            self.assertEqual(vt.outside_owns(["mine.txt"], tmp, "main"),
                             ["spec-start.txt"])


def lease_in(home: Path):
    """`lease.py` of the ui-acceptance skill, its registry under `home`, not ~/.mmw."""
    spec = importlib.util.spec_from_file_location(f"lease_for_tests_{id(home)}",
                                                  UI_ACCEPTANCE / "lease.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # `lease.py` asks `home()` for the root every time it needs a path, so the test's
    # own root is given by replacing that one reader, not by writing paths into it.
    module.home = lambda: home
    return module


PRODUCT = ticket("- [ ] AC1: the journey through the importer runs",
                 "  CHECK: echo journey.py import",
                 "  EXPECT: journey.py import",
                 "  EVIDENCE: pending")
PLAIN = ticket("- [ ] AC1: the importer writes six rows",
               "  CHECK: echo 'wrote 6 rows'",
               "  EXPECT: wrote 6 rows",
               "  EVIDENCE: pending")
TARGET_CHECK = ticket("- [ ] AC1: the target file is complete",
                      "  CHECK: python3 mmw-v2/skills/ui-acceptance/scripts/target_config.py --check",
                      "  EXPECT: complete: the oracles can drive this repository",
                      "  EVIDENCE: pending")


class TestTargetConfigCheckNeedsNoProduct(unittest.TestCase):
    """Checking `.mmw/target.json` does not start the product, so it takes no slot."""

    def test_target_config_check_needs_no_product(self):
        self.assertFalse(vt.needs_product(TARGET_CHECK))
        self.assertTrue(vt.needs_product(PRODUCT))








if __name__ == "__main__":
    unittest.main()
