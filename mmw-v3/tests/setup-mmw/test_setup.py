"""The setup-mmw skill's scripts: three against a fake `gh`, `nmem` and `git`, and
`migrate_layout.py` and `migrate_products.py` against a real `git` repository made in a temporary directory.

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
        (self.root / "CODING_STANDARDS.md").write_text("# Coding standards\n")
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
                     "Memory Space", ".gitignore", ".mmw/target.json checks",
                     "CODING_STANDARDS.md", "TESTING.md"):
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

    def test_a_feature_map_without_its_lint_is_missing(self):
        self.set_up_repository()
        (self.root / "docs" / "features").mkdir()
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^ok +repository +\.mmw/target\.json checks: 1 command\(s\)$")
        lint = [line for line in out.splitlines() if "feature_map.py" in line]
        self.assertEqual(len(lint), 1, out)
        self.assertTrue(lint[0].startswith("missing"), lint[0])
        self.assertIn("feature map lint:", lint[0])
        self.assertIn("docs/features/ exists", lint[0])
        self.assertIn(".mmw/target.json", lint[0])
        self.assertIn(
            "python3 ~/.agents/skills/verify-ticket/scripts/feature_map.py lint", lint[0])

    def test_feature_map_lint_row_only_when_needed(self):
        lint = "python3 ~/.agents/skills/verify-ticket/scripts/feature_map.py lint"
        self.set_up_repository()
        (self.root / "docs" / "features").mkdir()
        (self.root / ".mmw" / "target.json").write_text(
            json.dumps({"checks": ["make check", lint]}))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertFalse(self.feature_map_lint_missing(out), out)
        self.assertRegex(out, r"(?m)^ok +repository +\.mmw/target\.json checks: 2 command\(s\)$")

        (self.root / "docs" / "features").rmdir()
        (self.root / ".mmw" / "target.json").write_text(json.dumps({"checks": ["make check"]}))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertFalse(self.feature_map_lint_missing(out), out)
        self.assertNotIn("feature_map.py", out)

        (self.root / "docs" / "features").mkdir()
        (self.root / ".mmw" / "target.json").write_text(json.dumps(
            {"checks": [{"run": lint, "timeout": 60}]}))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertFalse(self.feature_map_lint_missing(out), out)
        self.assertRegex(out, r"(?m)^ok +repository +\.mmw/target\.json checks: 1 command\(s\)$")

    def test_a_target_without_a_checks_key_is_missing(self):
        self.set_up_repository()
        (self.root / ".mmw" / "target.json").write_text("{}")
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +\.mmw/target\.json checks: no `checks`")

    def onboarded_product(self, name, **extra):
        """One product file that `target_config.py --check` accepts."""
        directory = self.root / ".mmw" / name
        directory.mkdir(parents=True)
        body = {
            "ports": 1,
            "start": "true",
            "stop": "true",
            "discover": "true",
            "doctor": "true",
            "stories": "true",
            "leaves_machine": [],
            "harness_markers": [],
        }
        body.update(extra)
        (directory / "target.json").write_text(json.dumps(body))

    def test_a_listed_product_without_its_directory_is_missing(self):
        self.set_up_repository()
        (self.root / ".mmw" / "target.json").write_text(json.dumps({
            "checks": ["make check"],
            "products": ["notes"],
        }))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        lines = [line for line in out.splitlines()
                 if line.startswith("missing") and "notes" in line]
        self.assertEqual(len(lines), 1, out)

    def test_every_listed_product_onboarded_is_ok(self):
        self.set_up_repository()
        self.onboarded_product("notes")
        (self.root / ".mmw" / "target.json").write_text(json.dumps({
            "checks": ["make check"],
            "products": ["notes"],
        }))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertFalse(any(
            line.startswith("missing") and "notes" in line for line in out.splitlines()), out)

    def test_a_listed_product_that_fails_its_check_is_missing(self):
        self.set_up_repository()
        directory = self.root / ".mmw" / "notes"
        directory.mkdir(parents=True)
        (directory / "target.json").write_text(json.dumps({"ports": 1}))
        (self.root / ".mmw" / "target.json").write_text(json.dumps({
            "checks": ["make check"],
            "products": ["notes"],
        }))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        lines = [line for line in out.splitlines()
                 if line.startswith("missing") and "notes" in line]
        self.assertEqual(len(lines), 1, out)

    def test_a_products_value_that_is_not_a_list_is_missing(self):
        self.set_up_repository()
        (self.root / ".mmw" / "target.json").write_text(json.dumps({
            "checks": ["make check"],
            "products": "notes",
        }))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        lines = [line for line in out.splitlines()
                 if line.startswith("missing") and "products" in line]
        self.assertEqual(len(lines), 1, out)

    def test_check_reads_checks_from_a_product_layout(self):
        """The count is the root's. Each product file carries a one-command decoy."""
        self.set_up_repository()
        for name in ("gateway", "parrot"):
            self.onboarded_product(name, ports=3, checks=["echo product"])
        (self.root / ".mmw" / "target.json").write_text(json.dumps({
            "checks": ["echo one", "echo two"],
            "products": ["gateway", "parrot"],
            "needs": {"parrot": ["gateway"]},
        }))
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"(?m)^ok +repository +\.mmw/target\.json checks: 2 command\(s\)$")

    def test_an_old_product_layout_is_refused_without_running_checks(self):
        self.set_up_repository()
        (self.root / ".mmw/target.json").write_text(json.dumps({
            "checks": ["make check"], "start": "true",
        }))
        fake = Fake(root=self.root)
        code, out = self.run_check(fake)
        self.assertEqual(code, 2, out)
        self.assertIn("migrate_products.py <产品名>", out)
        self.assertNotIn("SETUP OK", out)
        self.assertEqual(fake.writes(), [])

    def test_a_target_that_is_not_json_is_missing(self):
        self.set_up_repository()
        (self.root / ".mmw" / "target.json").write_text("{")
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +\.mmw/target\.json checks: not JSON")

    @staticmethod
    def feature_map_lint_missing(out):
        return any(
            line.startswith("missing") and ("feature map lint" in line or "feature_map.py" in line)
            for line in out.splitlines())


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


class TestMigrateProducts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, check=True)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self):
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "old layout")

    def migrate(self, *args):
        out = subprocess.run([sys.executable, str(SCRIPTS / "migrate_products.py"), *args],
                             cwd=self.root, capture_output=True, text=True)
        return out.returncode, out.stdout, out.stderr

    def old_layout(self):
        self.write(".mmw/target.json", json.dumps({
            "checks": ["make check"],
            "start": "python3 .mmw/harness/target.py start",
            "stop": "python3 .mmw/harness/target.py stop",
            "discover": "python3 .mmw/harness/target.py discover",
            "stories": "python3 -u .mmw/stories/serve.py",
            "journeys": ".mmw/journeys",
            "leaves_machine": ["uses .mmw/harness/bin/gh"],
            "harness_markers": ["MMW_BREAK"],
        }, indent=2) + "\n")
        self.write(".mmw/harness/target.py", "ROOT = HERE.parents[2]\n")
        self.write(".mmw/stories/serve.py", "ROOT = Path(__file__).resolve().parents[2]\n")
        self.write(".mmw/journeys/smoke/run.sh", "echo ok\n")
        self.write(".mmw/AGENTS.md", "stay at the root\n")
        self.write(".mmw/CLAUDE.md", "@AGENTS.md\n")
        self.write("README.md", "the harness is .mmw/harness/target.py\n")

    def test_an_old_layout_moves_into_its_product(self):
        self.old_layout()
        self.commit()
        code, stdout, stderr = self.migrate("task-board")
        self.assertEqual(code, 0, stdout + stderr)
        self.assertEqual(stderr, "")
        product = json.loads((self.root / ".mmw/task-board/target.json").read_text())
        self.assertEqual(product["start"], "python3 .mmw/task-board/harness/target.py start")
        self.assertEqual(product["stop"], "python3 .mmw/task-board/harness/target.py stop")
        self.assertEqual(product["discover"], "python3 .mmw/task-board/harness/target.py discover")
        self.assertEqual(product["stories"], "python3 -u .mmw/task-board/stories/serve.py")
        self.assertEqual(product["journeys"], ".mmw/task-board/journeys")
        self.assertEqual(product["leaves_machine"], ["uses .mmw/task-board/harness/bin/gh"])
        self.assertEqual(product["harness_markers"], ["MMW_BREAK"])
        self.assertNotIn("checks", product)
        root = json.loads((self.root / ".mmw/target.json").read_text())
        self.assertEqual(list(root), ["checks", "products"])
        self.assertEqual(root["checks"], ["make check"])
        self.assertEqual(root["products"], ["task-board"])
        for rel in ("harness/target.py", "stories/serve.py", "journeys/smoke/run.sh"):
            self.assertTrue((self.root / ".mmw/task-board" / rel).is_file(), rel)
            self.assertFalse((self.root / ".mmw" / rel).exists(), rel)
        self.assertEqual((self.root / ".mmw/AGENTS.md").read_text(), "stay at the root\n")
        self.assertEqual((self.root / ".mmw/CLAUDE.md").read_text(), "@AGENTS.md\n")
        for rel in ("harness", "stories", "journeys"):
            self.assertIn(f"MOVED .mmw/{rel} -> .mmw/task-board/{rel}", stdout)
        self.assertIn("CLIMBS 2:", stdout)
        self.assertIn(".mmw/task-board/harness/target.py", stdout)
        self.assertIn(".mmw/task-board/stories/serve.py", stdout)
        self.assertIn("STILL NAMED 1:", stdout)
        self.assertTrue(stdout.rstrip().endswith("PRODUCTS MIGRATED 4 changes"), stdout)
        unstaged = [line for line in self.git("status", "--porcelain").stdout.splitlines() if line[1] != " "]
        self.assertEqual(unstaged, [])
        self.assertEqual(self.git("rev-list", "--count", "HEAD").stdout.strip(), "1")

    def test_an_existing_product_directory_is_refused(self):
        self.old_layout()
        self.write(".mmw/task-board/keep.txt", "already\n")
        self.commit()
        before = self.git("status", "--porcelain").stdout
        head = self.git("rev-parse", "HEAD").stdout
        code, stdout, stderr = self.migrate("task-board")
        self.assertEqual(code, 2, stdout + stderr)
        self.assertEqual(stdout, "")
        self.assertIn(".mmw/task-board", stderr)
        self.assertEqual(self.git("status", "--porcelain").stdout, before)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, head)
        self.assertTrue((self.root / ".mmw/harness/target.py").is_file())
        self.assertEqual((self.root / ".mmw/task-board/keep.txt").read_text(), "already\n")
        self.assertIn('"start"', (self.root / ".mmw/target.json").read_text())

    def test_a_migrated_repository_is_products_ok(self):
        self.old_layout()
        self.commit()
        code, stdout, stderr = self.migrate("task-board")
        self.assertEqual(code, 0, stdout + stderr)
        status = self.git("status", "--porcelain").stdout
        target = (self.root / ".mmw/task-board/target.json").read_text()
        code, stdout, stderr = self.migrate("task-board")
        self.assertEqual((code, stderr, stdout.strip()), (0, "", "PRODUCTS OK"))
        self.assertEqual(self.git("status", "--porcelain").stdout, status)
        self.assertEqual((self.root / ".mmw/task-board/target.json").read_text(), target)
        self.assertIn(".mmw/task-board/harness/target.py start", target)
        self.assertNotIn(".mmw/harness/", target)

    def test_migration_rewrites_contracts_and_feature_map_journeys(self):
        self.write(".mmw/target.json", json.dumps({
            "checks": ["make check"],
            "start": "python3 .mmw/harness/target.py start",
        }, indent=2) + "\n")
        self.write("efforts/notes/screen-contract.yaml",
                   "effort: notes\nbaselines:\n  look: efforts/notes/claude-design\n")
        self.write("efforts/other/screen-contract.yaml", "effort: other\n")
        self.write("docs/features/board/open.md",
                   "check: journey.py run smoke\n"
                   "again: python3 path/journey.py run smoke --break \"POST /x\"\n"
                   "kept: journey.py run task-board/smoke\n")
        self.commit()
        code, stdout, stderr = self.migrate("task-board")
        self.assertEqual(code, 0, stdout + stderr)
        for rel in ("efforts/notes/screen-contract.yaml", "efforts/other/screen-contract.yaml"):
            text = (self.root / rel).read_text()
            self.assertTrue(text.startswith("product: task-board\n"), text)
            self.assertEqual(text.count("\nproduct:"), 0, text)
            self.assertIn(f"REWROTE {rel} product", stdout)
        feature = (self.root / "docs/features/board/open.md").read_text()
        self.assertEqual(feature, "check: journey.py run task-board/smoke\n"
                         "again: python3 path/journey.py run task-board/smoke --break \"POST /x\"\n"
                         "kept: journey.py run task-board/smoke\n")
        self.assertEqual(stdout.count("REWROTE docs/features/board/open.md journeys"), 1)
        self.assertTrue(stdout.rstrip().endswith("PRODUCTS MIGRATED 4 changes"), stdout)

    def test_needs_stays_on_the_root_and_the_given_name_is_the_product_list(self):
        self.old_layout()
        doc = json.loads((self.root / ".mmw/target.json").read_text())
        doc["needs"] = {"parrot": ["gateway"]}
        doc["products"] = ["old"]
        self.write(".mmw/target.json", json.dumps(doc, indent=2) + "\n")
        self.commit()
        code, stdout, stderr = self.migrate("task-board")
        self.assertEqual(code, 0, stdout + stderr)
        root = json.loads((self.root / ".mmw/target.json").read_text())
        self.assertEqual(list(root), ["checks", "needs", "products"])
        self.assertEqual(root["needs"], {"parrot": ["gateway"]})
        self.assertEqual(root["products"], ["task-board"])
        product = json.loads((self.root / ".mmw/task-board/target.json").read_text())
        self.assertNotIn("needs", product)
        self.assertNotIn("products", product)

    def test_a_product_name_outside_the_alphabet_is_refused(self):
        self.old_layout()
        self.commit()
        before = self.git("status", "--porcelain").stdout
        for args in [(), ("Task",), ("a/b",), ("task_board",)]:
            code, stdout, stderr = self.migrate(*args)
            self.assertEqual(code, 2, args)
            self.assertEqual(stdout, "", args)
            self.assertNotEqual(stderr, "", args)
            self.assertEqual(self.git("status", "--porcelain").stdout, before)
        self.assertTrue((self.root / ".mmw/harness/target.py").is_file())


if __name__ == "__main__":
    unittest.main()
