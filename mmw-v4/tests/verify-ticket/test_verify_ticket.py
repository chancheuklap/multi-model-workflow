"""Ledger behaviour, run against fixed ticket bodies. Never calls the tracker.

A run of the criteria is one `ticket.checked` event on the ticket: its prose is the
updated ledger for a person, and its payload — run, commit, result, counts, each
criterion's outcome, the files outside `## Owns` — is what
every later reader decides on.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import checked, load, started

vt = load()

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
    """Runs the real gate-check against a fixed body and captures what it posts."""

    def run_ticket(self, body: str, reverify: bool = False, comments: list[str] | None = None,
                   actor: str | None = None, outside=(), started_event=STARTED):
        posted: list[str] = []
        history = ([] if started_event is None else [started_event]) + (comments or [])
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_comments", return_value=history), \
             mock.patch.object(vt, "outside_owns", return_value=list(outside)), \
             mock.patch.object(vt, "current_branch", return_value="issue-1"), \
             mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_checks(1, reverify, actor)
        self.posted = posted
        return code, (posted[0] if posted else ""), out.getvalue()


class TestWorkerRunRunsNoRepositoryCheck(unittest.TestCase):
    def test_only_ticket_criteria_run_on_the_workers_integrated_tree(self):
        for reverify in (False, True):
            with self.subTest(reverify=reverify), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                marker = root / "repository-check-ran"
                (root / "scripts").mkdir()
                check = root / "scripts/check"
                check.write_text(f"#!/bin/sh\ntouch '{marker}'\necho 'FAIL unit 0s'\nexit 1\n")
                check.chmod(0o755)
                for args in (("init", "-q", "-b", "issue-1"),
                             ("add", "."),
                             ("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"),
                             ("update-ref", "refs/remotes/origin/main", "HEAD")):
                    subprocess.run(["git", "-C", str(root), *args], check=True,
                                   capture_output=True)
                head = vt.git("rev-parse", "HEAD", cwd=root)
                posted = []
                with mock.patch.object(vt, "repo_root", return_value=root), \
                     mock.patch.object(vt, "fetch_body", return_value=PLAIN), \
                     mock.patch.object(vt, "fetch_comments", return_value=[
                         started(ticket=1, base=head, into="main")]), \
                     mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)), \
                     redirect_stdout(io.StringIO()) as out:
                    code = vt.run_checks(1, reverify, "worker")
                self.assertEqual(code, 0, out.getvalue())
                self.assertFalse(marker.exists(), "the worker ran scripts/check")
                self.assertEqual([payload_of(c)["run"] for c in posted],
                                 ["reverify" if reverify else "self"])


class TestWorkerRunWithoutStarted(LedgerRun):
    def test_worker_run_without_started_leaves_outside_owns_unchecked(self):
        code, comment, _ = self.run_ticket(PLAIN, started_event=None)
        self.assertEqual(code, 0, comment)
        payload = payload_of(comment)
        self.assertEqual(payload["outside_owns_unchecked"], "issue-1")


class TestSelectedCriteria(unittest.TestCase):
    def test_a_selected_timeout_is_red_instead_of_unrunnable(self):
        body = ticket("- [ ] AC1: timed out", "  CHECK: sleep 5; echo complete",
                      "  EXPECT: complete", "  EVIDENCE: pending")
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(vt, "DEFAULT_TIMEOUT", 1), redirect_stdout(io.StringIO()):
            code, rows = vt.selected_checks(61, ["AC1"], body, Path(tmp))
        self.assertEqual(code, 1)
        self.assertEqual([(r["id"], r["ok"]) for r in rows], [("AC1", False)])
        self.assertIn("timed out", rows[0]["error"])

    def test_only_runs_the_named_criteria_without_tracker_writes(self):
        body = ticket(
            "- [x] AC1: selected", "  CHECK: printf 'selected-green'", "  EXPECT: selected-green",
            "  EVIDENCE: old", "- [ ] AC2: not selected", "  CHECK: touch should-not-run",
            "  EXPECT: impossible", "  EVIDENCE: pending")
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "repo_root", return_value=Path(tmp)), \
             mock.patch.object(vt, "post_comment") as post, redirect_stdout(io.StringIO()):
            self.assertEqual(vt.main(["61", "--only", "AC1"]), 0)
            self.assertFalse((Path(tmp) / "should-not-run").exists())
            post.assert_not_called()


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
        self.assertEqual(payload_of(comment)["criteria"][0]["met"], False)

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
        self.assertEqual(payload_of(comment)["failed"], ["AC2"])


class TestTheRunIsOneTicketCheckedEvent(LedgerRun):
    """The worker's own run and a reverify each post exactly one `ticket.checked`, and
    everything a later reader decides on is in its payload, never in its first line."""

    BODY = ticket(
        "- [ ] AC1: the importer writes six rows",
        "  CHECK: echo 'wrote 6 rows'",
        "  EXPECT: wrote 6 rows",
        "  EVIDENCE: pending",
        "- [ ] AC2: the importer refuses an empty file",
        "  CHECK: echo 'accepted'",
        "  EXPECT: refused",
        "  EVIDENCE: pending",
    )

    def test_the_workers_own_run_carries_its_result_counts_outcomes_and_outside_owns(self):
        code, comment, _ = self.run_ticket(self.BODY, outside=["docs/stray.md"])
        self.assertEqual(code, 1)
        self.assertEqual(len(self.posted), 1)
        payload = payload_of(comment)
        self.assertEqual((payload["event"], payload["run"], payload["actor"],
                          payload["stage"], payload["result"]),
                         ("ticket.checked", "self", "worker", "work", "unmet"))
        self.assertRegex(payload["commit"], HEAD_RE)
        self.assertEqual(payload["counts"],
                         {"met": 1, "unmet": 1, "abandoned": 0, "total": 2})
        self.assertEqual([(c["id"], c["met"]) for c in payload["criteria"]],
                         [("AC1", True), ("AC2", False)])
        self.assertTrue(payload["criteria"][0]["evidence"].startswith("automatic-evidence=v1; "))
        self.assertEqual(payload["failed"], ["AC2"])
        self.assertEqual(payload["outside_owns"], ["docs/stray.md"])
        self.assertEqual(payload["shape"],
                         vt.shape_digest(vt.section(self.BODY, "Acceptance criteria")))
        self.assertIn("Outside Owns: docs/stray.md", comment)

    def test_all_met_is_result_met(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        code, comment, _ = self.run_ticket(body)
        self.assertEqual((code, payload_of(comment)["result"], payload_of(comment)["failed"]),
                         (0, "met", []))

    def test_a_reverify_by_the_main_agent_says_so(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        code, comment, _ = self.run_ticket(body, reverify=True, actor="main")
        self.assertEqual(code, 0)
        payload = payload_of(comment)
        self.assertEqual((payload["run"], payload["actor"], payload["stage"]),
                         ("reverify", "main", "regress"))
        self.assertNotIn("outside_owns", payload)
        self.assertNotIn("Outside Owns:", comment)

    def test_a_worker_reverify_records_outside_owns_for_the_closing_comment(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        _, comment, _ = self.run_ticket(body, reverify=True, actor="worker",
                                        outside=["docs/stray.md"])
        self.assertEqual(payload_of(comment)["outside_owns"], ["docs/stray.md"])

    def test_a_worker_reverify_has_the_verify_stage(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        _, comment, _ = self.run_ticket(body, reverify=True, actor="worker")
        payload = payload_of(comment)
        self.assertEqual((payload["actor"], payload["stage"]), ("worker", "verify"))

    def test_a_head_that_is_not_a_commit_is_refused_before_anything_runs(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        with mock.patch.object(vt, "git", return_value=""), \
             redirect_stderr(io.StringIO()):
            code, comment, printed = self.run_ticket(body)
        self.assertEqual((code, comment), (2, ""))
        self.assertNotIn("ALL MET", printed)


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


class TestReverify(LedgerRun):
    def test_reverify_reruns_what_the_last_run_ticked(self):
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        )
        previous = checked("self", [
            "- [x] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: " + current_evidence("echo 'wrote 6 rows'", "wrote 6 rows"),
        ], ticket=1)
        code, comment, printed = self.run_ticket(body, reverify=True, comments=[previous])
        self.assertEqual(code, 0)
        self.assertEqual(payload_of(comment)["run"], "reverify")
        self.assertIn("previously met reverified: 1", printed)

    def test_evidence_written_before_the_definition_digest_is_rerun_not_trusted(self):
        """A run recorded by the gate-check before evidence named its definition: the
        reverify still re-runs it and it passes, but it does not count as previously met."""
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        )
        previous = checked("self", [
            "- [x] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: exit=0; shell=/bin/sh; cwd=.; EXPECT=matched",
        ], ticket=1)
        code, comment, printed = self.run_ticket(body, reverify=True, comments=[previous])
        self.assertEqual(code, 0)
        self.assertEqual(payload_of(comment)["result"], "met")
        self.assertIn("reran: 1, previously met reverified: 0", printed)

    def test_a_first_line_saying_self_run_carries_nothing_forward(self):
        """The old ledger comment, typed by hand, is prose: nothing is carried from it."""
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        typed = "self-run\nALL MET (1 met)\n\n- [x] AC1: a\n  CHECK: echo ok\n  EXPECT: ok\n" \
                "  EVIDENCE: exit=0; EXPECT=matched"
        _, _, printed = self.run_ticket(body, reverify=True, comments=[typed])
        self.assertIn("previously met reverified: 0", printed)


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
        body = "## What to build\n\n1. Import the rows. AC1.\n\n" + ticket(
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
        code, printed = self.lint("## What to build\n\n1. Import the rows. AC1.\n\n" + ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("weak-expect", printed)

    def test_a_criterion_with_no_command_fails_the_run(self):
        """Nobody but the ticket's own author decides it, which the section forbids."""
        code, printed = self.lint("## What to build\n\n1. Import the rows. AC1.\n\n" + ticket(
            "- [ ] AC1: the wording reads well",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("manual-gate", printed)
        self.assertIn("ERROR", printed)

    def test_lint_runs_no_check_and_posts_no_comment(self):
        posted: list[str] = []
        body = "## What to build\n\n1. Import the rows. AC1.\n\n" + ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo LINT-MUST-NOT-RUN-THIS",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        )
        with mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            _, printed = self.lint(body)
        self.assertNotIn("LINT-MUST-NOT-RUN-THIS\n", printed.replace("CHECK: echo LINT-MUST-NOT-RUN-THIS", ""))
        self.assertEqual(posted, [])


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

    def test_owns_note_parenthesised_file_does_not_authorise_a_sibling(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "issue-4")
            owned = "src/app/(auth)/login/page.tsx"
            sibling = "src/app/(auth)/login/sibling.tsx"
            (tmp / owned).parent.mkdir(parents=True)
            (tmp / owned).write_text("owned\n")
            (tmp / sibling).write_text("outside\n")
            sh("add", "-A")
            sh("commit", "-qm", "write owned file and sibling")
            for entry in (owned + " (new)", "`" + owned + "` （新文件）",
                          owned + "（新文件）"):
                with self.subTest(entry=entry):
                    globs = vt.owns_globs("## Owns\n\n- " + entry + "\n")
                    fields = vt.outside_owns_fields(4, globs, tmp, "main")
                    self.assertEqual(fields, {"outside_owns": [sibling]})

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
            self.assertIn("spec-branch", vt.outside_owns_text(fields))

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
                    code = vt.run_checks(4, False)
            self.assertEqual(code, 0, posted)
            payload = payload_of(posted[0])
            self.assertEqual(payload["outside_owns"], [])
            self.assertEqual(vt.outside_owns(["mine.txt"], tmp, "main"),
                             ["spec-start.txt"])


PLAIN = ticket("- [ ] AC1: the importer writes six rows",
               "  CHECK: echo 'wrote 6 rows'",
               "  EXPECT: wrote 6 rows",
               "  EVIDENCE: pending")


class TestARunNotRecorded(unittest.TestCase):
    def test_a_run_whose_result_could_not_be_written_is_not_red(self):
        """A red run and an unrecorded one must never share an exit: the night's
        reverify reopens a landed ticket on 1."""

        def tracker_down(number, body):
            raise vt.subprocess.CalledProcessError(1, ["gh", "issue", "comment"])

        failing = ticket("- [ ] AC1: fails", "  CHECK: false", "  EXPECT: x",
                         "  EVIDENCE: pending")
        for body in (PLAIN, failing):
            with self.subTest(body=body[:40]), \
                 mock.patch.object(vt, "fetch_body", return_value=body), \
                 mock.patch.object(vt, "fetch_comments", return_value=[STARTED]), \
                 mock.patch.object(vt, "outside_owns", return_value=[]), \
                 mock.patch.object(vt, "post_comment", side_effect=tracker_down), \
                 redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_checks(1, False)
            self.assertEqual(code, vt.NOT_RECORDED, err.getvalue())


class TestReverifyActorIsExplicit(unittest.TestCase):
    def test_reverify_without_actor_is_a_usage_error(self):
        with redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as caught:
            vt.main(["1", "--reverify"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--reverify", err.getvalue())
        self.assertIn("--actor", err.getvalue())

    def test_actor_without_reverify_is_a_usage_error(self):
        with redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as caught:
            vt.main(["1", "--actor", "worker"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--actor", err.getvalue())
        self.assertIn("--reverify", err.getvalue())


class TestExitCodesHelp(unittest.TestCase):
    """`--lint`, `--sub-issue` and `--review` each have their own exit codes documented
    beside the rest, so `references/linting.md` and `references/sub-issues.md` no
    longer have to carry a second copy."""

    def test_help_prints_the_exit_codes(self):
        with redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit) as caught:
            vt.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("--sub-issue", out.getvalue())
        self.assertIn("--review", out.getvalue())


if __name__ == "__main__":
    unittest.main()
