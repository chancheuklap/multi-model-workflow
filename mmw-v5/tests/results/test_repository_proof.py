from __future__ import annotations

import io
import socket
import subprocess
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from test_repository_checks import vt, write_check


class CheckProof(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        (self.root / "data.txt").write_text("original\n")
        (self.root / ".gitignore").write_text(".scratch/\n")
        self.check_script("printf 'PASS unit 1s\\n'; exit 0")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def check_script(self, body):
        write_check(self.root, body)
        self.git("add", ".")
        self.git("commit", "-qm", "check fixture", "--allow-empty")
        self.head = self.git("rev-parse", "HEAD")

    def test_green_proof_identifies_the_clean_commit_base_machine_and_steps(self):
        result = vt.run_repository_check(self.root, "HEAD")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["proof"], {
            "tier": "default", "commit": self.head, "base": self.head,
            "machine": socket.gethostname(), "steps": ["unit"]})

    def test_proof_resolves_the_base_independently_of_head(self):
        base = self.head
        self.check_script("printf 'PASS changed\\n'; exit 0")
        result = vt.run_repository_check(self.root, base)
        self.assertEqual(result["status"], "pass")
        self.assertEqual((result["proof"]["commit"], result["proof"]["base"]),
                         (self.head, base))
        self.assertNotEqual(self.head, base)

    def test_dirty_or_untracked_work_produces_no_commit_proof(self):
        (self.root / "data.txt").write_text("changed\n")
        first = vt.run_repository_check(self.root, "HEAD")
        self.assertEqual((first["status"], first["proof"]), ("pass", None))
        (self.root / "data.txt").write_text("original\n")
        (self.root / "untracked.txt").write_text("uncommitted\n")
        second = vt.run_repository_check(self.root, "HEAD")
        self.assertEqual((second["status"], second["proof"]), ("pass", None))

    def test_a_check_that_changes_the_worktree_produces_no_commit_proof(self):
        self.check_script("printf changed > data.txt; exit 0")
        result = vt.run_repository_check(self.root, "HEAD")
        self.assertEqual((result["status"], result["proof"]), ("pass", None))

    def test_a_check_that_moves_head_produces_no_commit_proof(self):
        self.check_script("git commit --allow-empty -qm moved; exit 0")
        result = vt.run_repository_check(self.root, "HEAD")
        self.assertEqual((result["status"], result["proof"]), ("pass", None))
        self.assertNotEqual(self.git("rev-parse", "HEAD"), self.head)

    def test_a_check_that_moves_the_selected_base_produces_no_commit_proof(self):
        self.check_script("git update-ref refs/heads/check-base HEAD^; exit 0")
        self.git("branch", "check-base", "HEAD")
        result = vt.run_repository_check(self.root, "check-base")
        self.assertEqual((result["status"], result["proof"]), ("pass", None))
        self.assertEqual(self.git("rev-parse", "HEAD"), self.head)
        self.assertNotEqual(self.git("rev-parse", "check-base"), self.head)

    def test_an_unreadable_base_produces_no_commit_proof(self):
        result = vt.run_repository_check(self.root, "missing-base")
        self.assertEqual((result["status"], result["proof"]), ("pass", None))

    def test_check_process_has_no_time_limit(self):
        calls = []
        original = subprocess.run

        def run(args, **kwargs):
            if args[0] == str(self.root / "scripts" / "check"):
                calls.append((list(args), kwargs))
            return original(args, **kwargs)

        with mock.patch.object(vt.subprocess, "run", side_effect=run):
            self.assertEqual(vt.run_repository_check(self.root, "HEAD")["status"], "pass")
        self.assertEqual(calls[0][0], [str(self.root / "scripts" / "check")])
        self.assertNotIn("timeout", calls[0][1])

    def test_failed_excerpt_requires_no_node_and_full_log_is_preserved(self):
        self.check_script("printf 'src/file.py:7 problem\\nFAIL unit\\n' >&2; exit 1")
        original = subprocess.run

        def run(args, **kwargs):
            if args[0] == "node":
                raise FileNotFoundError("Node is unavailable")
            return original(args, **kwargs)

        with mock.patch.object(vt.subprocess, "run", side_effect=run):
            result = vt.run_repository_check(self.root, "HEAD", self.root, 61)
        self.assertEqual(result["status"], "red")
        self.assertIn("src/file.py:7 problem", result["failed"][0]["tail"])
        self.assertEqual(result["proof"]["steps"], ["unit"])
        self.assertEqual((self.root / result["failed"][0]["log"]).read_text(), result["output"])

    def test_executable_with_a_missing_interpreter_cannot_run(self):
        path = self.root / "scripts" / "check"
        path.write_text("#!/missing/interpreter\n")
        result = vt.run_repository_check(self.root, "HEAD")
        self.assertEqual((result["status"], result["proof"], result["failed"]),
                         ("cannot-run", None, []))
        self.assertIn("could not be started", result["detail"])


class ProofReuse(unittest.TestCase):
    COMMIT = "a" * 40
    BASE = "b" * 40

    def proof(self, **fields):
        payload = {"v": 1, "event": "spec.checked", "tier": "default",
                   "commit": self.COMMIT, "base": self.BASE, "result": "met",
                   "machine": socket.gethostname(), "steps": ["unit"], **fields}
        return "Checked\n\n" + vt.events.block(payload)

    def test_default_proof_requires_the_exact_commit_base_and_machine(self):
        good = self.proof()
        self.assertEqual(vt.covering_proof([good], self.COMMIT, self.BASE)["steps"], ["unit"])
        for fields in ({"commit": "c" * 40}, {"base": "c" * 40},
                       {"machine": "another-machine"}, {"result": "unmet"},
                       {"tier": "unknown"}):
            with self.subTest(fields=fields):
                self.assertIsNone(vt.covering_proof([self.proof(**fields)], self.COMMIT, self.BASE))

    def test_all_proof_covers_a_different_base_on_the_same_commit_and_machine(self):
        result = vt.covering_proof([self.proof(tier="all", base="c" * 40)], self.COMMIT, self.BASE)
        self.assertEqual((result["tier"], result["base"]), ("all", "c" * 40))

    def test_newest_matching_proof_follows_comment_ids(self):
        comments = [{"id": 9, "body": self.proof(steps=["later"])},
                    {"id": 3, "body": self.proof(steps=["earlier"])}]
        self.assertEqual(vt.covering_proof(comments, self.COMMIT, self.BASE)["steps"], ["later"])

    def test_plain_comments_do_not_hide_a_valid_proof(self):
        self.assertIsNotNone(vt.covering_proof(["ordinary comment", self.proof()],
                                              self.COMMIT, self.BASE))

    def test_unreadable_events_refuse_reuse_even_after_a_matching_proof(self):
        for body in ("<!-- mmw {broken} -->", "<!-- mmw {\"v\":999,\"event\":\"spec.checked\"} -->",
                     "<!-- mmw {\"v\":1,\"event\":\"unknown.event\"} -->"):
            with self.subTest(body=body):
                with self.assertRaisesRegex(ValueError, "unreadable"):
                    vt.covering_proof([self.proof(), {"id": 99, "body": body}],
                                      self.COMMIT, self.BASE)


class WorktreeEnvironment(unittest.TestCase):
    def test_missing_environment_script_needs_no_setup(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(vt.run_worktree_environment(Path(tmp), "up"), 0)

    def test_environment_receives_step_worktree_and_working_directory(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "env"
            script.parent.mkdir()
            script.write_text('#!/bin/sh\nprintf "%s\\n%s\\n%s\\n" "$1" "$2" "$PWD"\n')
            script.chmod(0o755)
            with redirect_stderr(output := io.StringIO()):
                code = vt.run_worktree_environment(root, "up")
            self.assertEqual(code, 0)
            step, worktree, cwd = output.getvalue().splitlines()
            self.assertEqual((step, worktree), ("up", str(root)))
            self.assertEqual(Path(cwd).resolve(), root.resolve())

    def test_failed_environment_names_the_step_and_retains_useful_output(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "env"
            script.parent.mkdir()
            script.write_text('#!/bin/sh\necho "dependency unavailable" >&2\nexit 1\n')
            script.chmod(0o755)
            with redirect_stderr(output := io.StringIO()):
                code = vt.run_worktree_environment(root, "down")
            self.assertEqual(code, 2)
            self.assertIn("scripts/env down failed", output.getvalue())
            self.assertIn("dependency unavailable", output.getvalue())
