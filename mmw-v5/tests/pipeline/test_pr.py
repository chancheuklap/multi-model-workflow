from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/dispatch/scripts/pr.py"

FAKE_GH = r'''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
p=Path(os.environ['PR_STATE']);s=json.loads(p.read_text());a=sys.argv[1:]
if a[:2]==['repo','view']:
 assert a[2]=='https://github.test/owner/repo.git'
 assert 'GH_REPO' not in os.environ
 print('owner/repo');sys.exit()
assert os.environ.get('GH_REPO')=='owner/repo'
assert 'CLICOLOR_FORCE' not in os.environ and 'CLICOLOR' not in os.environ
s['calls'].append(a)
def save():p.write_text(json.dumps(s))
save()
if a[:2]==['pr','list']:
 print(json.dumps(s.get('existing',[])))
elif a[:2]==['pr','create']:
 if s.get('create_error'):
  print('HTTP 502',file=sys.stderr);sys.exit(1)
 s['body']=Path(a[a.index('--body-file')+1]).read_text();save()
 print(s.get('create_output','https://github.test/owner/repo/pull/7'))
elif a[:2]==['pr','checks']:
 if s.get('checks_error'):
  print('HTTP 502',file=sys.stderr);sys.exit(1)
 if '--watch' in a:
  if s.get('watch_error'):print(s['watch_error'],file=sys.stderr);sys.exit(1)
  sys.exit(0)
 seq=s.get('checks',[[]]);i=s.get('check_index',0)
 s['check_index']=i+1;save();rows=seq[min(i,len(seq)-1)]
 if rows==[]:
  print('no checks reported',file=sys.stderr);sys.exit(1)
 print(json.dumps(rows))
elif a[:2]==['run','list']:
 rows=[{'databaseId':80}]
 if s.get('dispatched'):rows.append({'databaseId':81})
 print(json.dumps(rows))
elif a[:2]==['workflow','run']:
 s['dispatched']=True;save()
 if not s.get('run_no_url'):print('https://github.test/owner/repo/actions/runs/81')
elif a[:2]==['run','watch']:
 if s.get('run_watch_error'):print('watch connection lost',file=sys.stderr);sys.exit(1)
 if s.get('conclusion','success')=='failure':sys.exit(1)
elif a[:2]==['run','view']:
 print(s.get('conclusion','success'))
else:raise AssertionError(a)
'''


class PullRequests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin",
                        "https://github.test/owner/repo.git"], check=True)
        binary = self.root / "bin"
        binary.mkdir()
        (binary / "gh").write_text(FAKE_GH)
        (binary / "gh").chmod(0o755)
        self.state = {"calls": [], "checks": [[{"name": "build", "bucket": "pass"}]]}
        self.store = self.root / "pr.json"
        self.body = self.root / "body.md"
        self.body.write_text("Changed requested behavior.\n\nValidation: literal $text and `code`.\n")
        self.env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                    "PR_STATE": str(self.store), "GH_REPO": "foreign/repo", "CLICOLOR_FORCE": "1",
                    "CLICOLOR": "1", "MMW_PR_CHECKS_GRACE_SECONDS": "0", "MMW_HOME": str(self.root / "home")}
        self.workflow("on: pull_request\n")

    def workflow(self, text, name="ci.yml"):
        directory = self.repo / ".github/workflows"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(text)

    def run_pr(self, base="main", **env):
        self.store.write_text(json.dumps(self.state))
        result = subprocess.run([sys.executable, str(SCRIPT), "--base", base, "--head", "feature",
                                 "--title", "Requested changes", "--body-file", str(self.body)],
                                cwd=self.repo, env={**self.env, **env}, capture_output=True, text=True, timeout=8)
        self.state = json.loads(self.store.read_text())
        return result

    def test_ready_pr_uses_exact_request_origin_body_and_check_reader(self):
        result = self.run_pr()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state["body"], self.body.read_text())
        self.assertIn(["pr", "create", "--base", "main", "--head", "feature", "--title",
                       "Requested changes", "--body-file", str(self.body)], self.state["calls"])
        self.assertIn(["pr", "checks", "7", "--watch"], self.state["calls"])
        self.assertIn("https://github.test/owner/repo/pull/7\nchecks: green", result.stdout)
        self.assertTrue(all(call[:2] not in (["pr", "merge"], ["release", "create"])
                            for call in self.state["calls"]))
        self.assertFalse(any("--draft" in call for call in self.state["calls"]))

    def test_red_cancelled_and_pending_checks_preserve_real_results(self):
        self.state["checks"] = [[{"name": "build", "bucket": "pending"}],
                                [{"name": "build", "bucket": "fail"}, {"name": "unit", "bucket": "cancel"}]]
        result = self.run_pr()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("checks: red build, unit", result.stdout)
        self.assertEqual(self.state["check_index"], 2)

    def test_expected_ci_missing_after_grace_is_red(self):
        self.state["checks"] = [[]]
        result = self.run_pr()
        self.assertEqual(result.returncode, 1)
        self.assertIn("checks: none", result.stdout)
        self.assertIn("expected CI for main", result.stderr)

    def test_absent_ci_and_absent_checks_do_not_claim_ci_was_green(self):
        (self.repo / ".github/workflows/ci.yml").unlink()
        self.state["checks"] = [[]]
        result = self.run_pr(base="integration")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GitHub CI does not run", result.stdout)
        self.assertIn("checks: none", result.stdout)
        self.assertNotIn("checks: green", result.stdout)

    def test_branch_filters_and_supported_yaml_forms_keep_ci_selection(self):
        for text, base, expected in (
            ("on: {pull_request: {branches: [main]}}", "integration", False),
            ("on:\n  pull_request:\n    branches:\n      - main", "main", True),
            ("on: {pull_request: {branches: ['releases/**', '!releases/**-alpha']}}", "releases/v1-alpha", False),
            ("'on': [push, pull_request]", "integration", True),
        ):
            with self.subTest(text=text, base=base):
                self.workflow(text)
                self.state = {"calls": [], "checks": [[]]}
                result = self.run_pr(base=base)
                self.assertEqual(result.returncode, int(expected), result.stderr)
                self.assertEqual("GitHub CI does not run" in result.stdout, not expected)

    def test_unreadable_workflow_assumes_ci_and_cannot_silently_pass_missing_checks(self):
        self.workflow("on: *unsupported\n")
        self.state["checks"] = [[]]
        result = self.run_pr()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("could not read triggers", result.stdout)
        self.assertIn("expected CI", result.stderr)

    def test_safe_fallback_workflow_uses_requested_head_and_records_its_conclusion(self):
        self.workflow("on:\n  pull_request:\n    branches: [main]\n  workflow_dispatch:\n")
        self.workflow("on: workflow_dispatch\n", "deploy.yml")
        self.workflow("on:\n  pull_request:\n    branches: [main]\n  workflow_dispatch:\n    inputs:\n      target:\n        required: true\n", "required.yml")
        self.state["run_no_url"] = True
        result = self.run_pr(base="integration")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["workflow", "run", "ci.yml", "--ref", "feature"], self.state["calls"])
        self.assertIn(["run", "watch", "81", "--exit-status"], self.state["calls"])
        self.assertIn("dispatched ci.yml: success", result.stdout)
        self.assertIn("skipped deploy.yml", result.stdout)
        self.assertIn("skipped required.yml: required input target", result.stdout)
        self.assertEqual(sum(call[:2] == ["workflow", "run"] for call in self.state["calls"]), 1)

    def test_fallback_failure_still_returns_the_opened_pr_and_a_red_exit(self):
        self.workflow("on: {pull_request: {branches: [main]}, workflow_dispatch: {}}\n")
        for fields, conclusion in (({"conclusion": "failure"}, "failure"),
                                   ({"run_watch_error": True}, "success")):
            with self.subTest(fields=fields):
                self.state = {"calls": [], **fields}
                result = self.run_pr(base="integration")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(f"dispatched ci.yml: {conclusion}", result.stdout)
                self.assertIn("https://github.test/owner/repo/pull/7", result.stdout)
                if fields.get("run_watch_error"):
                    self.assertIn("watch connection lost", result.stderr)

    def test_existing_pr_prevents_reopening_and_repeated_workflow_dispatch(self):
        self.workflow("on: {pull_request: {branches: [main]}, workflow_dispatch: {}}\n")
        self.state["existing"] = [{"url": "https://github.test/owner/repo/pull/7"}]
        result = self.run_pr(base="integration")
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)
        self.assertTrue(all(call[:2] not in (["pr", "create"], ["workflow", "run"])
                            for call in self.state["calls"]))

    def test_create_watch_and_malformed_check_errors_are_operational_errors(self):
        for fields in ({"create_error": True}, {"checks_error": True},
                       {"watch_error": "connection failed"},
                       {"checks": [[{"name": "build", "bucket": "impossible"}]]}):
            with self.subTest(fields=fields):
                self.state = {"calls": [], **fields}
                result = self.run_pr()
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn("checks: green", result.stdout)

    def test_missing_origin_and_invalid_grace_never_create_a_pr(self):
        result = self.run_pr(MMW_PR_CHECKS_GRACE_SECONDS="nan")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.state["calls"], [])
        subprocess.run(["git", "-C", str(self.repo), "remote", "remove", "origin"], check=True)
        result = self.run_pr()
        self.assertEqual(result.returncode, 2)
        self.assertIn("origin", result.stderr)
        self.assertEqual(self.state["calls"], [])
