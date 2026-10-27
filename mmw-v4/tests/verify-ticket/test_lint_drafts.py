"""`--lint --drafts <dir>`: a batch linted before it is published.

The drafts are files, one per ticket: `TITLE:`, `LABELS:` and `BLOCKED BY:` header lines,
a line `---`, then the issue body; a draft's file name stands in for the issue number
it does not have yet. Each draft gets the same per-ticket lint a published ticket gets,
the graph comes from the `BLOCKED BY:` headers, and the run ends by listing what only a
published batch can show. The spec is the one tracker read, and it is patched here.
"""

import io
import json
import shlex
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from _load import load

vt = load()

SPEC = 555
SPEC_BODY = ("## Implementation Decisions\n\n### 1. One\n\nx\n\n### 2. Two\n\ny\n\n"
             "## Testing Decisions\n\nnone\n")
CRITERION = ("## Acceptance criteria\n\n"
             "- [ ] AC1: the importer writes six rows\n"
             "  CHECK: node scripts/import.mjs fixtures/valid.json\n"
             "  EXPECT: /^6 rows$/m\n  EVIDENCE: pending\n")
MANUAL = ("## Acceptance criteria\n\n"
          "- [ ] AC1: the wording reads well\n  EVIDENCE: pending\n")
LABELS = "mmw:ticket, ready-for-agent, junior-worker"


def draft(blocked="(none)", parent="#555, Implementation Decisions section 1",
          criteria=CRITERION, labels=LABELS, title="A ticket"):
    if "## What to build" not in criteria:
        criteria = "## What to build\n\n1. Import the rows. AC1.\n\n" + criteria
    return (f"TITLE: {title}\nLABELS: {labels}\nBLOCKED BY: {blocked}\n"
            f"WORKER LINE: junior, a note the lint does not read\n---\n"
            f"## Parent\n\n{parent}\n\n{criteria}")


class DraftsFixture:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.root = self.dir / "repo"
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        for key, value in (("user.email", "test@example.com"), ("user.name", "Test")):
            subprocess.run(["git", "config", key, value], cwd=self.root, check=True)
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "import.mjs").write_text('console.log("6 rows");')
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=self.root,
                       check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        (self.dir / f"{name}.md").write_text(text, encoding="utf-8")

    def lint(self, spec_body=SPEC_BODY, outsider=None):
        def body(n):
            if n == SPEC and spec_body is not None:
                return spec_body
            raise vt.TrackerReadError(n, "body", "offline")
        with mock.patch.object(vt, "repo_root", return_value=self.root), \
             mock.patch.object(vt, "fetch_body", side_effect=body), \
             mock.patch.object(vt, "fetch_outsider",
                               side_effect=outsider or (lambda n: {"spec": None, "state": ""})), \
             mock.patch.object(vt, "fetch_sub_issues",
                               side_effect=AssertionError("drafts mode lists no sub-issues")), \
             mock.patch.object(vt, "fetch_blocked_by",
                               side_effect=AssertionError("drafts mode reads no tracker link")):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.main([str(SPEC), "--lint", "--drafts", str(self.dir), "--base", "HEAD"])
        return code, out.getvalue()


class TestDrafts(DraftsFixture, unittest.TestCase):
    def test_clean_drafts_are_linted_each_then_graphed_by_name(self):
        self.write("T1-contract", draft())
        self.write("T2-page", draft(blocked="T1-contract",
                                    parent="#555, Implementation Decisions section 2"))
        code, printed = self.lint()
        self.assertEqual(code, 0, printed)
        self.assertIn("T1-contract", printed)
        self.assertIn("T2-page LINT OK", printed)
        self.assertIn("level 0: T1-contract", printed)
        self.assertIn("level 1: T2-page", printed)
        self.assertIn("sections named by a ticket: 2/2", printed)

    def test_a_per_ticket_finding_fails_the_run_and_names_the_draft(self):
        self.write("T1", draft())
        self.write("T2", draft(criteria=MANUAL))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("manual-gate", printed)
        self.assertIn("drafts with findings: T2", printed)

    def test_a_cycle_between_drafts_is_named_by_draft_name(self):
        self.write("T1", draft(blocked="T2"))
        self.write("T2", draft(blocked="T1"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[cycle]", printed)
        self.assertRegex(printed, r"T\d -> T\d -> T\d")

    def test_a_blocker_that_is_no_draft_is_an_error(self):
        self.write("T1", draft(blocked="T9-missing"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("`T9-missing`", printed)
        self.assertIn("[unknown-draft]", printed)

    def test_a_published_blocker_is_looked_up_like_a_tracker_one(self):
        self.write("T1", draft(blocked="#42"))
        code, printed = self.lint(
            outsider=lambda n: {"spec": 318, "state": "OPEN"} if n == 42 else {})
        self.assertEqual(code, 0, printed)
        self.assertIn("#42", printed)
        self.assertIn("#318", printed)
        self.assertIn("waiting on another spec: T1 ← #42", printed)

    def test_a_draft_whose_parent_names_another_spec_first_is_an_error(self):
        self.write("T1", draft(parent="#318 Implementation Decisions section 4; "
                                      "#555, Implementation Decisions section 1"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[parent-order]", printed)

    def test_a_draft_without_the_ticket_layer_label_is_an_error(self):
        self.write("T1", draft(labels="ready-for-agent, junior-worker"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("`mmw:ticket`", printed)

    def test_the_worker_label_is_read_off_the_header(self):
        self.write("T1", draft(labels="mmw:ticket, ready-for-agent, junior-worker, senior-worker"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[worker-label]", printed)

    def test_a_header_without_the_separator_is_an_error_not_a_skip(self):
        self.write("T1", "TITLE: x\nLABELS: mmw:ticket\nBLOCKED BY: (none)\n## Parent\n\n#555\n")
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[draft-unreadable]", printed)
        self.assertIn("drafts with findings: T1", printed)

    def test_an_unreadable_spec_is_said_and_the_per_ticket_checks_still_run(self):
        self.write("T1", draft(criteria=MANUAL))
        code, printed = self.lint(spec_body=None)
        self.assertEqual(code, 1)
        self.assertIn("[spec-unreadable]", printed)
        self.assertIn("manual-gate", printed)
        self.assertNotIn("sections named by a ticket", printed)

    def test_drafts_belongs_to_lint(self):
        with redirect_stdout(io.StringIO()), \
             mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            with self.assertRaises(SystemExit):
                vt.main([str(SPEC), "--drafts", str(self.dir)])
        self.assertIn("--drafts", err.getvalue())


class TestBuildPoints(DraftsFixture, unittest.TestCase):
    def test_replay_build_points(self):
        fixtures = Path(__file__).parent / "fixtures"
        for ticket, missing_point in ((65, "共用请求"), (66, "FormData"), (68, "Blob")):
            with self.subTest(ticket=ticket):
                body = (fixtures / f"erp-frontend-{ticket}.md").read_text()
                with redirect_stdout(io.StringIO()) as out:
                    code = vt.lint_criteria(ticket, body, LABELS.split(", "))
                self.assertEqual(code, 1, out.getvalue())
                errors = [line for line in out.getvalue().splitlines()
                          if "[build-point-without-criterion]" in line]
                self.assertTrue(any(missing_point in line for line in errors), errors)
                self.assertTrue(all("ERROR" in line for line in errors), errors)

    def test_build_point_without_criterion(self):
        cases = [
            ("1. Import the rows. AC1 verifies it.", False, ""),
            ("1) Import the rows.\n   Decided by AC1.", False, ""),
            ("1. Import the rows.", True, "Import the rows"),
            ("1. Import the rows. AC9 verifies it.", True, "AC9"),
            ("1. Import the rows. AC1 and AC9 verify it.", True, "AC9"),
            ("Import the rows. AC1 verifies it.", True, "numbered point"),
            ("", True, "numbered point"),
            ("```\n1. Example only. AC1.\n```", True, "numbered point"),
            ("1. Import the rows.\n\n2. Publish the rows. AC1.", True, "Import the rows"),
        ]
        for points, error, fact in cases:
            with self.subTest(points=points):
                body = ("## What to build\n\n" + points + "\n\n" + CRITERION)
                self.write("T1", draft(criteria=body))
                code, printed = self.lint()
                self.assertEqual(code, int(error), printed)
                self.assertEqual("[build-point-without-criterion]" in printed, error, printed)
                if error:
                    self.assertIn(fact, printed)
                    self.assertIn("ERROR", printed)
                with mock.patch.object(vt, "fetch_body", return_value=body), \
                     mock.patch.object(vt, "fetch_ticket", return_value={
                         "labels": [{"name": x.strip()} for x in LABELS.split(",")]}), \
                     mock.patch.object(vt, "fetch_parent", return_value=None), \
                     mock.patch.object(vt, "fetch_sub_issues", return_value=[]), \
                     mock.patch.object(vt, "repo_root", return_value=self.root), \
                     redirect_stdout(io.StringIO()) as out:
                    code = vt.main(["77", "--lint"])
                self.assertEqual(code, int(error), out.getvalue())
                self.assertEqual("[build-point-without-criterion]" in out.getvalue(), error)


class TestDraftBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.root = self.home / "repo"
        self.origin = self.home / "origin.git"
        self.git("init", "--bare", str(self.origin), cwd=self.home)
        self.git("clone", str(self.origin), str(self.root), cwd=self.home)
        self.git("checkout", "-b", "project")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.calls = self.home / "calls"
        script = ("#!/usr/bin/env python3\nimport os, sys\n"
                  f"with open({str(self.calls)!r}, 'a') as f: "
                  "f.write(os.environ['MMW_TICKET'] + ':' + os.environ['MMW_BASE_REF'] + '\\n')\n"
                  "print('old-line')\n"
                  "print('tail-1\\ntail-2\\ntail-3\\ntail-4')\n"
                  "print(sys.argv[1])\nsys.exit(int(sys.argv[2]))\n")
        (self.root / "check.py").write_text(script)
        for runner in ("pytest", "vitest"):
            path = self.root / runner
            path.write_text('#!/bin/sh\nexec python3 check.py "$@"\n')
            path.chmod(0o755)
        self.git("add", ".")
        self.git("commit", "-m", "base")
        self.git("push", "origin", "project")
        self.drafts = self.home / "drafts"
        self.drafts.mkdir()

    def git(self, *args, cwd=None):
        return subprocess.check_output(["git", *args], cwd=cwd or self.root,
                                       stderr=subprocess.STDOUT, text=True)

    def write(self, name="T1", check="python3 check.py base-ok 1", expect="/^base-ok$/m", timeout=""):
        criteria = ("## Acceptance criteria\n\n- [ ] AC1: base result\n"
                    f"  CHECK: {check}\n  EXPECT: {expect}\n  EVIDENCE: pending\n")
        if timeout:
            criteria += f"  TIMEOUT: {timeout}\n"
        (self.drafts / f"{name}.md").write_text(draft(criteria=criteria))

    def lint(self, *extra):
        with mock.patch.object(vt, "repo_root", return_value=self.root), \
             mock.patch.object(vt, "fetch_body", return_value=SPEC_BODY), \
             redirect_stdout(io.StringIO()) as out:
            code = vt.main([str(SPEC), "--lint", "--drafts", str(self.drafts), *extra])
        return code, out.getvalue()

    def test_drafts_base_run(self):
        self.write()
        self.write("T2", "python3 check.py another 0", "/^missing$/m")
        (self.root / "check.py").write_text("raise RuntimeError('working checkout')")
        head = self.git("rev-parse", "HEAD")
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertIn("T1 AC1 FAIL on origin/project", out)
        self.assertIn("T2 AC1 FAIL on origin/project", out)
        self.assertIn("tail-1\n", out)
        self.assertIn("base-ok", out)
        self.assertNotIn("old-line", out)
        self.assertNotIn("working checkout", out)
        self.assertNotIn("[passes-on-base]", out)
        self.assertEqual(self.calls.read_text().splitlines(),
                         ["T1:origin/project", "T2:origin/project"])
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("worktree", "list", "--porcelain").count("worktree "), 1)

    def test_drafts_base_run_explicit_and_missing_ref(self):
        self.write()
        code, out = self.lint("--base", "missing-ref")
        self.assertEqual(code, 2, out)
        self.assertIn("--base", out)
        self.assertFalse(self.calls.exists())
        code, out = self.lint("--base", "HEAD")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.calls.read_text().splitlines(), ["T1:HEAD"])

    def test_passes_on_base(self):
        self.write(check="python3 check.py base-ok 0")
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertIn("WARN", out)
        self.assertIn("[passes-on-base]", out)
        self.assertIn("T1 AC1 PASS on origin/project", out)
        self.assertIn("tail-1\n", out)

    def test_no_runner_summary(self):
        standards = json.loads((vt.HERE / "runner-summaries.json").read_text())
        for runner, contract in standards.items():
            other_summaries = {
                "pytest": ["=== 3 passed, 2 deselected in 0.04s ===",
                           "3 passed, 2 warnings in 0.5s", "2 failed, 3 passed in 0.1s",
                           "=== 1 error in 0.1s ===", "1 passed, 1 xfailed in 0.1s",
                           "=== 3 failed, 2 skipped in 0.10s ==="],
                "vitest": ["Tests  1 failed | 2 skipped (3)", "Test Files  1 failed (1)"],
            }
            absent = ("quiet", "done: 3 passed", "Tests  banana passed (1)")
            for output in (*absent, *[s["summary"] for s in contract["samples"]],
                           *other_summaries[runner]):
                with self.subTest(runner=runner, output=output):
                    self.write(check=f"./{runner} {shlex.quote(output)} 1",
                               expect=contract["expect"])
                    code, out = self.lint()
                    self.assertEqual("[no-runner-summary]" in out, output in absent, out)
                    self.assertEqual(code, 1 if output in absent else 0, out)

    def test_published_lint_runs_nothing(self):
        self.write()
        body = vt.read_draft(self.drafts / "T1.md")["body"]
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_ticket", return_value={"labels": [{"name": "mmw:ticket"}]}), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             mock.patch.object(vt, "fetch_sub_issues", return_value=[77]), \
             mock.patch.object(vt, "fetch_blocked_by", return_value=[]), \
             mock.patch.object(vt, "repo_root", return_value=self.root), \
             redirect_stdout(io.StringIO()) as out:
            code = vt.main(["77", "--lint"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertFalse(self.calls.exists())
        with mock.patch.object(vt, "fetch_body", side_effect=lambda n: SPEC_BODY if n == SPEC else body), \
             mock.patch.object(vt, "fetch_ticket", side_effect=lambda n: {
                 "labels": [{"name": "mmw:spec" if n == SPEC else "mmw:ticket"}]}), \
             mock.patch.object(vt, "fetch_sub_issues", return_value=[77]), \
             mock.patch.object(vt, "fetch_blocked_by", return_value=[]), \
             mock.patch.object(vt, "fetch_parent", return_value=SPEC), \
             mock.patch.object(vt, "repo_root", return_value=self.root), \
             redirect_stdout(io.StringIO()) as out:
            code = vt.main([str(SPEC), "--lint"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertFalse(self.calls.exists())

    def test_drafts_base_run_name_checkout(self):
        self.write("checkout")
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertIn("checkout AC1 FAIL on origin/project", out)
        self.assertEqual(self.calls.read_text().splitlines(), ["checkout:origin/project"])

    def test_drafts_base_run_timeout(self):
        self.write(check="python3 -c 'import time; print(42, flush=True); time.sleep(10)'",
                   timeout="2")
        with mock.patch.object(vt, "DEFAULT_TIMEOUT", 1):
            code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertIn("timed out after 2s", out)
        self.assertIn("T1 AC1 FAIL on origin/project", out)
        self.assertEqual(self.git("worktree", "list", "--porcelain").count("worktree "), 1)


if __name__ == "__main__":
    unittest.main()
