#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENGINE = str(SOURCE_ROOT / "mmwstack/skills/repo-checks/scripts/check.mjs")

MINIMAL_CONFIG = {
    "integration": "main",
    "ci_workflow": None,
    "test_files": [],
    "inert": ["scripts/check", ".githooks/**", ".gitignore"],
    "affects_all": [".agents/checks.json"],
    "checks": [
        {
            "id": "syntax",
            "run": "python3 scripts/syntax-check.py",
            "inputs": [
                "scripts/syntax-check.py",
                "scripts/**/*.py",
                "scripts/**/*.sh",
                "scripts/**/*.mjs",
                "scripts/**/*.js",
                "scripts/**/*.cjs",
                "mmwstack/**/*.py",
                "mmwstack/**/*.sh",
                "mmwstack/**/*.mjs",
                "mmwstack/**/*.js",
                "mmwstack/**/*.cjs",
            ],
            "tests": [],
            "needs": ["cmd:python3", "cmd:bash", "cmd:node"],
            "ci": False,
            "ci_reason": "Disposable syntax regression fixture.",
        }
    ],
    "lanes": [],
    "excluded": [],
}

FILES = {
    "mmwstack/probe.py": ("def invalid(\n", "def valid():\n    return 1\n"),
    "scripts/probe.sh": ("if then\n", "echo ok\n"),
    "mmwstack/probe.mjs": ("function invalid( {\n", "export const ok = 1;\n"),
}


class SyntaxCheckRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="syntax-check-test-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.home = root / "home"
        self.repo = root / "repo"
        self.remote = root / "origin.git"
        self.home.mkdir()
        self.repo.mkdir()

        self.env = {
            "PATH": os.environ["PATH"],
            "HOME": str(self.home),
            "MMW_REPO_CHECKS_ENGINE": os.environ.get("MMW_REPO_CHECKS_ENGINE", DEFAULT_ENGINE),
        }

        self.git("init", "--bare", "--template=", str(self.remote), cwd=root)
        self.git("--git-dir", str(self.remote), "symbolic-ref", "HEAD", "refs/heads/main", cwd=root)
        self.git("init", "--template=", "-b", "main")
        self.git("config", "user.name", "Syntax Check Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", str(self.remote))

        for rel in ("scripts/check", "scripts/syntax-check.py", ".githooks/pre-commit", ".githooks/pre-push"):
            dst = self.repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_ROOT / rel, dst)

        (self.repo / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        (self.repo / ".agents").mkdir()
        (self.repo / ".agents" / "checks.json").write_text(json.dumps(MINIMAL_CONFIG, indent=2) + "\n", encoding="utf-8")

        self.git("add", "--all")
        self.git("commit", "-m", "Baseline")
        self.git("push", "-u", "origin", "main")
        self.git("config", "core.hooksPath", ".githooks")
        self.git("switch", "-c", "feat")

        for rel, (bad, _) in (
            ("scripts/ignored/bad.py", FILES["mmwstack/probe.py"]),
            ("scripts/ignored/bad.sh", FILES["scripts/probe.sh"]),
            ("mmwstack/ignored/bad.mjs", FILES["mmwstack/probe.mjs"]),
        ):
            self.write_file(rel, bad)

    def run_cmd(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            cwd=cwd or self.repo,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def git(self, *args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        res = self.run_cmd("git", *args, cwd=cwd)
        if check and res.returncode != 0:
            self.fail(f"git {' '.join(args)} failed ({res.returncode}):\n{res.stdout}\n{res.stderr}")
        return res

    def check_syntax(self) -> subprocess.CompletedProcess[str]:
        return self.run_cmd(str(self.repo / "scripts/check"), "--only", "syntax")

    def write_file(self, rel: str, content: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def assert_syntax_fails(self, res: subprocess.CompletedProcess[str]) -> None:
        output = res.stdout + res.stderr
        self.assertEqual(res.returncode, 1, output)
        for rel in FILES:
            self.assertIn(rel, output)

    def assert_syntax_passes(self, res: subprocess.CompletedProcess[str]) -> None:
        output = res.stdout + res.stderr
        self.assertEqual(res.returncode, 0, output)
        self.assertIn("PASS syntax", output)

    def test_syntax_covers_untracked_staged_committed_and_skips_ignored(self) -> None:
        for rel, (bad, _) in FILES.items():
            self.write_file(rel, bad)
        self.assert_syntax_fails(self.check_syntax())

        for rel, (_, good) in FILES.items():
            self.write_file(rel, good)
        self.assert_syntax_passes(self.check_syntax())

        for rel, (bad, _) in FILES.items():
            self.write_file(rel, bad)
        self.git("add", *FILES)
        self.assert_syntax_fails(self.check_syntax())

        for rel, (_, good) in FILES.items():
            self.write_file(rel, good)
        self.git("add", *FILES)
        self.assert_syntax_passes(self.check_syntax())

        for rel, (bad, _) in FILES.items():
            self.write_file(rel, bad)
        self.git("add", *FILES)
        self.git("commit", "-m", "Add malformed files")
        self.assert_syntax_fails(self.check_syntax())

        bad_push = self.git("push", "-u", "origin", "feat", check=False)
        self.assertNotEqual(bad_push.returncode, 0, bad_push.stdout + bad_push.stderr)
        for rel in FILES:
            self.assertIn(rel, bad_push.stdout + bad_push.stderr)

        for rel, (_, good) in FILES.items():
            self.write_file(rel, good)
        self.git("add", *FILES)
        self.git("commit", "-m", "Repair files")
        self.assert_syntax_passes(self.check_syntax())

        good_push = self.git("push", "-u", "origin", "feat")
        self.assertEqual(good_push.returncode, 0, good_push.stdout + good_push.stderr)

    def test_syntax_parses_hooks_and_reports_only_files_it_parses(self) -> None:
        hook = ".githooks/pre-push"
        self.write_file("mmwstack/note.md", "this is not a script\n")
        self.write_file(hook, "#!/bin/sh\nif true; then :; fi\n")
        good = self.run_cmd("python3", "scripts/syntax-check.py", hook, "mmwstack/note.md")
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(good.stdout.strip(), "PASS syntax (1 parsed, 1 skipped)")

        self.write_file(hook, "#!/bin/sh\nif then\n")
        bad = self.run_cmd("python3", "scripts/syntax-check.py")
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
        self.assertIn(hook, bad.stderr)

        skipped = self.run_cmd("python3", "scripts/syntax-check.py", "mmwstack/note.md")
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertEqual(skipped.stdout.strip(), "SKIP syntax (0 parsed, 1 skipped)")

    def test_node_checks_erasable_types_without_running_the_script(self) -> None:
        entry = "scripts/probe.ts"
        self.write_file(
            entry,
            "#!/usr/bin/env node\ninterface Options { size: number }\n"
            "export const options: Options = { size: 1 };\nthrow new Error('must not run');\n",
        )
        good = self.run_cmd("python3", "scripts/syntax-check.py", entry)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(good.stdout.strip(), "PASS syntax (1 parsed, 0 skipped)")

        self.write_file(entry, "#!/usr/bin/env node\nexport const options: number = ;\n")
        bad = self.run_cmd("python3", "scripts/syntax-check.py", entry)
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertIn(f"{entry}:", bad.stderr)
        self.assertIn("ERR_INVALID_TYPESCRIPT_SYNTAX", bad.stderr)


if __name__ == "__main__":
    unittest.main()
