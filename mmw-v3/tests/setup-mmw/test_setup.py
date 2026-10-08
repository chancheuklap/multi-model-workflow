"""The setup-mmw skill's scripts: three against a fake `gh`, `nmem` and `git`, and
`migrate_layout.py` against a real `git` repository made in a temporary directory.

Nothing here reaches GitHub, Nowledge Mem or a real repository: every subprocess the
first three start is answered by `Fake`, which records the command, and the files
`check.py` reads sit in a temporary directory.
"""
import importlib.util
import io
import json
import os
import subprocess
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
space = load("space")
TABLE = labels.label_table()
EXACT = {"id": "o__r", "name": "o/r", "defaultRetrievalMode": "shared", "sharedSpaceIds": ["mmw-toolbox"]}


def done(cmd, code=0, out="", err=""):
    return mock.Mock(args=cmd, returncode=code, stdout=out, stderr=err)


class Fake:
    """Answers `gh`, `nmem`, `git` and `space.py --check` as a repository in a given state."""

    def __init__(self, root=None, labels_have=None, spaces=None, issues=True, protected="",
                 ignored=(".worktrees/", ".scratch/", "story-shots/"),
                 absent="error: /spaces/{ident} returned 404: Unknown space: {ident}"):
        self.root = root
        self.absent = absent
        self.labels_have = dict(labels_have if labels_have is not None else
                                {n: (c, d) for n, (c, d) in TABLE.items()})
        self.spaces = dict(spaces if spaces is not None else {"o__r": dict(EXACT)})
        self.issues = issues
        self.protected = protected
        self.ignored = ignored
        self.calls = []

    def __call__(self, cmd, **kwargs):
        cmd = list(cmd)
        self.calls.append(cmd)
        if cmd[0] == "gh":
            return self.gh(cmd)
        if cmd[0] == "nmem":
            return self.nmem(cmd)
        if cmd[0] == "git":
            return self.git(cmd)
        if len(cmd) > 1 and cmd[1].endswith("space.py"):
            with redirect_stderr(io.StringIO()) as err, \
                 mock.patch.object(space, "call", side_effect=lambda a: self.nmem(["nmem", "--json", *a])), \
                 mock.patch.object(space.shutil, "which", return_value="/bin/nmem"):
                code = space.main(cmd[2:])
            return done(cmd, code, "", err.getvalue())
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

    def nmem(self, cmd):
        args = [a for a in cmd[1:] if a != "--json"]
        ident = args[2] if len(args) > 2 else ""
        if args[:2] == ["spaces", "show"]:
            if ident == "mmw-toolbox":
                return done(cmd, 0, json.dumps({"id": "mmw-toolbox"}))
            row = self.spaces.get(ident)
            if row is None:
                return done(cmd, 1, "", self.absent.format(ident=ident))
            return done(cmd, 0, json.dumps(row))
        if args[:2] == ["spaces", "create"]:
            ident = args[args.index("--id") + 1]
            self.spaces[ident] = {"id": ident, "name": args[2],
                                  "defaultRetrievalMode": args[args.index("--retrieval-mode") + 1],
                                  "sharedSpaceIds": [args[i + 1] for i, a in enumerate(args[:-1])
                                                     if a == "--share-with"]}
            return done(cmd, 0, json.dumps(self.spaces[ident]))
        if args[:2] == ["spaces", "update"]:
            row = self.spaces.setdefault(ident, {"id": ident})
            row["name"] = args[args.index("--name") + 1]
            row["defaultRetrievalMode"] = args[args.index("--retrieval-mode") + 1]
            row["sharedSpaceIds"] = [args[i + 1] for i, a in enumerate(args[:-1]) if a == "--share-with"]
            return done(cmd, 0, json.dumps(row))
        raise AssertionError(f"unexpected nmem {cmd}")

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
                or (c[0] == "nmem" and ("create" in c or "update" in c))
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


class TestSpace(unittest.TestCase):
    def run_space(self, fake, argv):
        with mock.patch.object(space, "call", side_effect=lambda a: fake.nmem(["nmem", "--json", *a])), \
             mock.patch.object(space.shutil, "which", return_value="/bin/nmem"), \
             redirect_stderr(io.StringIO()) as err:
            code = space.main(argv)
        return code, err.getvalue()

    def test_creates_an_absent_space_in_the_exact_shape(self):
        fake = Fake(spaces={})
        code, err = self.run_space(fake, ["o/r"])
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.spaces["o__r"], EXACT)

    def test_creates_an_absent_space_when_nmem_names_it_unknown_name_or_alias(self):
        fake = Fake(spaces={}, absent='error: Unknown Space name or alias: "{ident}"')
        code, err = self.run_space(fake, ["o/r"])
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.spaces["o__r"], EXACT)

    def test_check_reports_a_space_nmem_names_unknown_name_or_alias_as_absent(self):
        fake = Fake(spaces={}, absent='error: Unknown Space name or alias: "{ident}"')
        code, err = self.run_space(fake, ["--check", "o/r"])
        self.assertEqual(code, 1)
        self.assertIn("setup-mmw", err)
        self.assertNotIn("o__r", fake.spaces)

    def test_repairs_a_wrong_shape(self):
        fake = Fake(spaces={"o__r": {"id": "o__r", "name": "wrong", "defaultRetrievalMode": "strict",
                                     "sharedSpaceIds": ["default", "mmw-toolbox"]}})
        code, err = self.run_space(fake, ["o/r"])
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.spaces["o__r"], EXACT)

    def test_check_reports_an_absent_space_names_setup_mmw_and_creates_nothing(self):
        fake = Fake(spaces={})
        code, err = self.run_space(fake, ["--check", "o/r"])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("repository Memory unavailable:"), err)
        self.assertIn("setup-mmw", err)
        self.assertNotIn("o__r", fake.spaces)

    def test_check_refuses_a_wrong_shape_and_repairs_nothing(self):
        wrong = {"id": "o__r", "name": "wrong", "defaultRetrievalMode": "strict", "sharedSpaceIds": []}
        fake = Fake(spaces={"o__r": dict(wrong)})
        code, err = self.run_space(fake, ["--check", "o/r"])
        self.assertEqual(code, 1)
        self.assertEqual(fake.spaces["o__r"], wrong)

    def test_an_unavailable_service_is_never_answered_with_a_create(self):
        fake = Fake(spaces={})
        fake.nmem = lambda cmd: done(cmd, 1, "", "connection refused")
        code, err = self.run_space(fake, ["o/r"])
        self.assertEqual(code, 1)
        self.assertIn("connection refused", err)
        self.assertNotIn("o__r", fake.spaces)


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
        agents = self.root / "docs" / "agents"
        agents.mkdir(parents=True)
        (agents / "issue-tracker.md").write_text("# x\n\n## Three label sets\n\n## Wayfinding operations\n")
        (agents / "triage-labels.md").write_text("# x\n")
        (agents / "domain.md").write_text("# x\n")
        (self.root / "AGENTS.md").write_text(
            "## External References\n\n| Need | File |\n| --- | --- |\n"
            "| a | `docs/agents/issue-tracker.md` |\n| b | `docs/agents/triage-labels.md` |\n"
            "| c | `docs/agents/domain.md` |\n")
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n")
        (self.root / ".mmw").mkdir()
        (self.root / ".mmw" / "target.json").write_text(json.dumps({"checks": ["make check"]}))
        (self.root / "TESTING.md").write_text("# Testing\n")

    def run_check(self, fake, nmem_space=None):
        check = load("check")
        env = {"MMW_HOME": str(self.home)}
        if nmem_space is not None:
            env["NMEM_SPACE"] = nmem_space
        with mock.patch("subprocess.run", side_effect=fake), \
             mock.patch.object(check.shutil, "which", return_value="/bin/tool"), \
             mock.patch.dict("os.environ", env), \
             redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            if nmem_space is None:
                os.environ.pop("NMEM_SPACE", None)
            code = check.main()
        sys.modules.pop("labels", None)
        sys.modules.pop("space", None)
        return code, out.getvalue()

    def test_a_repository_set_up_is_setup_ok(self):
        self.set_up_repository()
        fake = Fake(root=self.root)
        code, out = self.run_check(fake)
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith("SETUP OK"), out)

    def test_a_bare_repository_lists_every_repository_item_missing_and_writes_nothing(self):
        fake = Fake(root=self.root, labels_have={}, spaces={}, ignored=())
        code, out = self.run_check(fake)
        self.assertEqual(code, 1)
        for item in ("docs/agents/issue-tracker.md", "AGENTS.md", "CLAUDE.md", "labels",
                     "Memory Space", ".gitignore", ".mmw/target.json checks", "TESTING.md"):
            self.assertRegex(out, rf"(?m)^missing +repository +{item}:", item)
        self.assertIn("SETUP INCOMPLETE", out)
        self.assertEqual(fake.writes(), [])
        self.assertNotIn("o__r", fake.spaces)
        self.assertEqual(fake.labels_have, {})

    def test_a_missing_section_is_named(self):
        self.set_up_repository()
        (self.root / "docs" / "agents" / "issue-tracker.md").write_text("# x\n\n## Three label sets\n")
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1)
        self.assertIn("lacks ## Wayfinding operations", out)

    def test_issues_off_is_missing_and_a_protected_branch_is_only_a_note(self):
        self.set_up_repository()
        code, out = self.run_check(Fake(root=self.root, issues=False, protected="main\n"))
        self.assertEqual(code, 1)
        self.assertRegex(out, r"(?m)^missing +repository +tracker: o/r has Issues turned off")
        self.assertRegex(out, r"(?m)^note +repository +branch rules: protected branches main")

    def test_the_session_space_is_only_a_note_naming_where_memory_lands(self):
        self.set_up_repository()
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"(?m)^note +session +NMEM_SPACE: this session's is not set, not o__r, "
                              r"so what it writes to Memory lands in Default")
        code, out = self.run_check(Fake(root=self.root), nmem_space="other__repo")
        self.assertRegex(out, r"(?m)^note +session +NMEM_SPACE: this session's is other__repo, not o__r")
        code, out = self.run_check(Fake(root=self.root), nmem_space="o__r")
        self.assertRegex(out, r"(?m)^ok +session +NMEM_SPACE: o__r$")

    def test_the_earlier_effort_layout_is_missing_and_names_the_migration(self):
        self.set_up_repository()
        (self.root / "docs" / "specs" / "notes").mkdir(parents=True)
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1)
        self.assertRegex(out, r"(?m)^missing +repository +effort layout: docs/specs hold .*migrate_layout.py")


class TestMigrateLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        self.write("docs/specs/notes/screen-contract.yaml",
                   "effort: notes\nbaselines:\n  look: prototypes/notes/claude-design\n")
        self.write("docs/specs/notes/targets/App.aria", "old snapshot\n")
        self.write("prototypes/notes/claude-design/App.dc.html", "<p>data in prototypes/notes/example-data</p>\n")
        self.write("prototypes/notes/example-data/board.js", "x\n")
        self.write("prototypes/notes/claude-design/_ds/kit/readme.md", "data in prototypes/notes/example-data\n")
        self.write("prototypes/notes/12/UI/README.md", "# variant\n\nState list: prototypes/notes/README.md\n")
        self.write("prototypes/notes/12/UI/serve.py", "ROOT = HERE.parents[3]\n")
        self.write("prototypes/other/7/claude-design/App.dc.html", "<p>page</p>\n")
        self.write("docs/specs/reuse/screen-contract.yaml",
                   "effort: reuse\nbaselines:\n  look: prototypes/other/7/claude-design\n")
        self.write("docs/prototypes/older/issue-3/README.md", "# older\n")
        self.write("docs/research/older/issue-4/note.md", "# note\n")
        self.write("docs/research/shared/note.md", "# not an effort\n")
        self.write("AGENTS.md", "the contract is docs/specs/notes/screen-contract.yaml\n")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "earlier layout")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=True)

    def write(self, rel, text):
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(text)

    def migrate(self):
        out = subprocess.run([sys.executable, str(SCRIPTS / "migrate_layout.py")], cwd=self.root,
                             capture_output=True, text=True)
        return out.returncode, out.stdout + out.stderr

    def test_moves_each_effort_into_one_directory_and_rewrites_the_baseline(self):
        code, out = self.migrate()
        self.assertEqual(code, 0, out)
        for rel in ("efforts/notes/screen-contract.yaml", "efforts/notes/claude-design/App.dc.html",
                    "efforts/notes/example-data/board.js", "efforts/notes/prototypes/12/UI/README.md",
                    "efforts/reuse/claude-design/App.dc.html", "efforts/notes/targets/App.aria",
                    "efforts/older/prototypes/issue-3/README.md", "efforts/older/research/issue-4/note.md",
                    "docs/research/shared/note.md"):
            self.assertTrue((self.root / rel).is_file(), rel)
        for rel in ("docs/specs", "prototypes", "docs/prototypes", "docs/research/older", "efforts/other"):
            self.assertFalse((self.root / rel).exists(), rel)
        self.assertIn("look: efforts/notes/claude-design\n",
                      (self.root / "efforts/notes/screen-contract.yaml").read_text())
        self.assertIn("look: efforts/reuse/claude-design\n",
                      (self.root / "efforts/reuse/screen-contract.yaml").read_text())
        self.assertRegex(out, r"STILL NAMED 2:")
        self.assertRegex(out, r"CLIMBS 1:")
        self.assertTrue(out.rstrip().endswith("LAYOUT MIGRATED 9 changes"), out)
        unstaged = [line for line in self.git("status", "--porcelain").stdout.splitlines() if line[1] != " "]
        self.assertEqual(unstaged, [])
        self.assertIn("efforts/notes/claude-design/App.dc.html", self.git("ls-files").stdout)
        self.assertNotIn("docs/specs/", self.git("ls-files").stdout)

    def test_two_sources_for_one_destination_refuse(self):
        self.write("docs/prototypes/notes/12/UI/README.md", "# same leaf, older tree\n")
        code, out = self.migrate()
        self.assertEqual(code, 1)
        self.assertIn("two sources would move to efforts/notes/prototypes/12", out)
        self.assertTrue((self.root / "prototypes/notes/12/UI/README.md").is_file())
        self.assertEqual(self.git("log", "--oneline").stdout.count("\n"), 1)

    def test_a_second_run_moves_nothing(self):
        self.migrate()
        code, out = self.migrate()
        self.assertEqual((code, out.strip()), (0, "LAYOUT OK"))

    def test_an_existing_destination_refuses_and_changes_nothing(self):
        self.write("efforts/notes/screen-contract.yaml", "already here\n")
        code, out = self.migrate()
        self.assertEqual(code, 1)
        self.assertIn("efforts/notes/screen-contract.yaml already exists", out)
        self.assertTrue((self.root / "docs/specs/notes/screen-contract.yaml").is_file())
        self.assertTrue((self.root / "prototypes/notes/claude-design/App.dc.html").is_file())


if __name__ == "__main__":
    unittest.main()
