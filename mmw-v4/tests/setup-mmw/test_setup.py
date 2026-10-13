"""The setup-mmw skill's scripts: `labels.py` and `check.py` against a fake `gh` and
`git`.

Nothing here reaches GitHub or a real repository: every subprocess `labels.py` and `check.py` start
is answered by `Fake`, which records the command, and the files `check.py` reads sit in
a temporary directory.
"""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "setup-mmw" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(f"setup_{name}", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


labels = load("labels")
TABLE = labels.label_table()


def done(cmd, code=0, out="", err=""):
    return mock.Mock(args=cmd, returncode=code, stdout=out, stderr=err)


class Fake:
    """Answers `gh` and `git` as a repository in a given state."""

    def __init__(self, root=None, labels_have=None, issues=True, protected="",
                 ignored=(".worktrees/", ".scratch/")):
        self.root = root
        self.labels_have = dict(labels_have if labels_have is not None else
                                {n: (c, d) for n, (c, d) in TABLE.items()})
        self.issues = issues
        self.protected = protected
        self.ignored = ignored
        self.calls = []

    def __call__(self, cmd, **kwargs):
        cmd = list(cmd)
        self.calls.append(cmd)
        if cmd[0] == "gh":
            return self.gh(cmd)
        if cmd[0] == "git":
            return self.git(cmd)
        raise AssertionError(f"unexpected command {cmd}")

    def gh(self, cmd):
        args = cmd[1:]
        if args[:2] == ["repo", "view"]:
            return done(cmd, 0, json.dumps({"nameWithOwner": "o/r", "hasIssuesEnabled": self.issues,
                                            "defaultBranchRef": {"name": "main"}}))
        if args[:2] == ["label", "list"]:
            return done(cmd, 0, json.dumps([{"name": n, "color": c, "description": d}
                                            for n, (c, d) in self.labels_have.items()]))
        if args[:2] == ["label", "create"]:
            name = args[2]
            self.labels_have[name] = (args[args.index("--color") + 1],
                                      args[args.index("--description") + 1])
            return done(cmd, 0, f'✓ Label "{name}" created')
        if args[:2] == ["auth", "status"]:
            return done(cmd, 0)
        if args[0] == "api":
            path = next(a for a in args[1:] if not a.startswith("-"))
            if path.startswith("repos/o/r/issues?"):
                return done(cmd, 0, "7\n")
            if "protected=true" in path:
                return done(cmd, 0, self.protected)
            if path.endswith("/rulesets"):
                return done(cmd, 0, "")
            return done(cmd, 0, "[]")
        raise AssertionError(f"unexpected gh {cmd}")

    def git(self, cmd):
        if cmd[1:3] == ["rev-parse", "--show-toplevel"]:
            return done(cmd, 0, f"{self.root}\n")
        if cmd[1:3] == ["check-ignore", "-q"]:
            probe = cmd[3]
            return done(cmd, 0 if any(probe.startswith(d) for d in self.ignored) else 1)
        raise AssertionError(f"unexpected git {cmd}")

    def writes(self):
        """Every command recorded that changes something."""
        return [c for c in self.calls
                if c[:3] == ["gh", "label", "create"]
                or (c[0] == "gh" and "--method" in c)]


class TestLabels(unittest.TestCase):
    def run_labels(self, fake):
        with mock.patch.object(labels.subprocess, "run", side_effect=fake), \
             redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = labels.main()
        return code, out.getvalue(), err.getvalue()

    def test_the_table_is_every_set_including_wayfinder(self):
        for name in ("mmw:map", "needs-triage", "junior-worker", "wayfinder:map", "wayfinder:task"):
            self.assertIn(name, TABLE)

    def test_creates_only_the_missing_labels_and_never_overwrites(self):
        have = {n: v for n, v in TABLE.items() if not n.startswith("wayfinder:")}
        have["needs-triage"] = ("000000", "the repository's own description")
        fake = Fake(labels_have=have)
        code, out, err = self.run_labels(fake)
        self.assertEqual(code, 0, err)
        created = sorted(c[3] for c in fake.calls if c[:3] == ["gh", "label", "create"])
        self.assertEqual(created, sorted(n for n in TABLE if n.startswith("wayfinder:")))
        self.assertFalse(any("--force" in c for c in fake.calls))
        self.assertIn("kept needs-triage", out)
        self.assertEqual(fake.labels_have["needs-triage"], ("000000", "the repository's own description"))
        self.assertIn(f"LABELS OK {len(TABLE)}", out)

    def test_a_second_run_creates_nothing(self):
        fake = Fake()
        code, out, _ = self.run_labels(fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.writes(), [])

    def test_a_refused_create_exits_1_with_the_reason(self):
        fake = Fake(labels_have={})

        def refusing(cmd, **kwargs):
            if cmd[:3] == ["gh", "label", "create"]:
                return done(cmd, 1, "", "HTTP 403: Resource not accessible")
            return fake(cmd, **kwargs)

        code, out, err = self.run_labels(refusing)
        self.assertEqual(code, 1)
        self.assertIn("HTTP 403", err)
        self.assertNotIn("LABELS OK", out)


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "mmw-home"
        self.home.mkdir()
        (self.home / "models.json").write_text("{}")

    def tearDown(self):
        self.tmp.cleanup()

    def set_up_repository(self):
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "check").write_text("#!/usr/bin/env bash\nexit 0\n")
        (self.root / "scripts" / "check").chmod(0o755)
        (self.root / "TESTING.md").write_text("# Testing\n")

    def run_check(self, fake):
        check = load("check")
        with mock.patch("subprocess.run", side_effect=fake), \
             mock.patch.object(check.shutil, "which", return_value="/bin/tool"), \
             mock.patch.dict("os.environ", {"MMW_HOME": str(self.home)}), \
             redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            code = check.main()
        sys.modules.pop("labels", None)
        return code, out.getvalue()

    def test_a_repository_set_up_is_setup_ok(self):
        self.set_up_repository()
        fake = Fake(root=self.root)
        code, out = self.run_check(fake)
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith("SETUP OK"), out)

    def test_a_bare_repository_lists_every_repository_item_missing_and_writes_nothing(self):
        fake = Fake(root=self.root, labels_have={}, ignored=())
        code, out = self.run_check(fake)
        self.assertEqual(code, 1)
        for item in ("labels", ".gitignore", "scripts/check", "TESTING.md"):
            self.assertRegex(out, rf"(?m)^missing +repository +{item}:", item)
        self.assertTrue(out.rstrip().endswith("SETUP INCOMPLETE 4 missing"), out)
        self.assertEqual(fake.writes(), [])
        self.assertEqual(fake.labels_have, {})

    def test_a_check_that_cannot_be_run_is_missing(self):
        self.set_up_repository()
        (self.root / "scripts" / "check").chmod(0o644)
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +scripts/check:")
        (self.root / "scripts" / "check").unlink()
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +scripts/check:")

    def test_target_json_checks_are_not_read(self):
        self.set_up_repository()
        (self.root / ".mmw").mkdir()
        (self.root / ".mmw" / "target.json").write_text(json.dumps({"checks": ["make check"]}))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith("SETUP OK"), out)
        self.assertNotIn("target.json", out)

    def test_issues_off_is_missing_and_a_protected_branch_is_only_a_note(self):
        self.set_up_repository()
        code, out = self.run_check(Fake(root=self.root, issues=False, protected="main\n"))
        self.assertEqual(code, 1)
        self.assertRegex(out, r"(?m)^missing +repository +tracker: o/r has Issues turned off")
        self.assertRegex(out, r"(?m)^note +repository +branch rules: protected branches main")

    def test_an_earlier_effort_layout_is_not_reported(self):
        self.set_up_repository()
        (self.root / "docs" / "specs" / "notes").mkdir(parents=True)
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith("SETUP OK"), out)
        self.assertNotIn("effort layout", out)


if __name__ == "__main__":
    unittest.main()
