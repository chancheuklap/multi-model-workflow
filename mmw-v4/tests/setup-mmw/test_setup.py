import importlib.util
import io
import json
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
TABLE = labels.label_table()
event_spec = importlib.util.spec_from_file_location(
    "setup_test_events", SCRIPTS.parents[1] / "verify-ticket" / "scripts" / "events.py")
events = importlib.util.module_from_spec(event_spec)
event_spec.loader.exec_module(events)


def done(cmd, code=0, out="", err=""):
    return mock.Mock(args=cmd, returncode=code, stdout=out, stderr=err)


class Fake:
    """Answers `gh` and `git` as a repository in a given state."""

    def __init__(self, root=None, labels_have=None, issues=True, protected="",
                 ignored=(".worktrees/", ".scratch/"), install=(0, "", ""),
                 issue_pages=None):
        self.root = root
        self.labels_have = dict(labels_have if labels_have is not None else
                                {n: (c, d) for n, (c, d) in TABLE.items()})
        self.issues = issues
        self.protected = protected
        self.ignored = ignored
        self.install = install
        self.calls = []
        self.issue_pages = issue_pages

    def __call__(self, cmd, **kwargs):
        cmd = list(cmd)
        self.calls.append(cmd)
        if cmd[0] == "gh":
            return self.gh(cmd)
        if cmd[0] == "git":
            return self.git(cmd)
        if cmd[0] == "bash" and cmd[1].endswith("/install.sh") and cmd[2:] == ["--check"]:
            return done(cmd, *self.install)
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
        if args[:2] == ["label", "edit"]:
            name = args[2]
            self.labels_have[name] = (self.labels_have[name][0],
                                      args[args.index("--description") + 1])
            return done(cmd)
        if args[:2] == ["issue", "edit"]:
            row = next(row for page in self.issue_pages for row in page
                       if row["number"] == int(args[2]))
            if "--remove-label" in args:
                name = args[args.index("--remove-label") + 1]
                row["labels"] = [label for label in row["labels"] if label["name"] != name]
            if "--add-label" in args:
                row["labels"].append({"name": args[args.index("--add-label") + 1]})
            return done(cmd)
        if args[:2] == ["issue", "view"]:
            row = next(row for page in self.issue_pages for row in page
                       if row["number"] == int(args[2]))
            fields = args[args.index("--json") + 1].split(",")
            return done(cmd, out=json.dumps({field: row[field] for field in fields}))
        if args[0] == "api":
            path = next(a for a in args[1:] if not a.startswith("-"))
            if self.issue_pages is not None:
                if path.endswith("/issues?state=open&per_page=100"):
                    assert "--paginate" in args and "--slurp" in args, cmd
                    return done(cmd, out=json.dumps(self.issue_pages))
                if "/issues/" in path and "/comments?" in path:
                    assert "--paginate" in args and "--slurp" in args, cmd
                    number = int(path.split("/issues/")[1].split("/")[0])
                    row = next(row for page in self.issue_pages for row in page
                               if row["number"] == number)
                    comments = [{"id": index, "body": body}
                                for index, body in enumerate(row["comments"], start=1)]
                    return done(cmd, out=json.dumps([comments[:100], comments[100:]]))
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
        if cmd[1:] == ["ls-files", "-z"]:
            return done(cmd)
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
        for name in ("mmw:map", "mmw:lesson", "mmw:problem", "needs-triage",
                     "junior-worker", "wayfinder:map", "wayfinder:task"):
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


class TestMigrate(unittest.TestCase):
    def event(self, name, **fields):
        return events.build(name, ticket=1, line="An event", at="2026-09-10T00:00:00Z", **fields)

    def issue(self, number=1, names=("needs-triage",), body="## Problem\n\nA problem.",
              parent=None, comments=()):
        return {"number": number, "labels": [{"name": name} for name in names],
                "body": body, "parent": parent, "comments": list(comments)}

    def run_migrate(self, fake):
        with mock.patch.object(labels.subprocess, "run", side_effect=fake), \
             redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = labels.main(["--migrate"])
        return code, out.getvalue(), err.getvalue()

    def test_migrate_creates_the_two_new_kinds(self):
        fake = Fake(labels_have={n: v for n, v in TABLE.items()
                                 if n not in ("mmw:lesson", "mmw:problem")}, issue_pages=[[]])
        code, out, err = self.run_migrate(fake)
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.labels_have["mmw:lesson"], ("8e44ad", "做法上的问题，等复盘"))
        self.assertEqual(fake.labels_have["mmw:problem"],
                         ("f1c40f", "不在任何票里的产品问题，或计划还没批的 issue"))
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 0 changed")

    def test_migrate_rewrites_needs_triage_and_deletes_no_label(self):
        fake = Fake(issue_pages=[[]])
        fake.labels_have["needs-triage"] = ("000000", "old meaning")
        fake.labels_have["needs-info"] = ("abcdef", "owner's label")
        code, out, err = self.run_migrate(fake)
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.labels_have["needs-triage"],
                         ("000000", "等你决定：只有主人能让它离开"))
        self.assertEqual(fake.labels_have["needs-info"], ("abcdef", "owner's label"))
        self.assertFalse(any(c[:3] == ["gh", "label", "delete"] for c in fake.calls))
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 0 changed")

    def test_an_untyped_mmw_registration_becomes_a_problem(self):
        row = self.issue(names=("needs-triage", "bug"))
        code, out, err = self.run_migrate(Fake(issue_pages=[[row]]))
        self.assertEqual(code, 0, err)
        self.assertEqual(row["labels"], [{"name": "needs-triage"}, {"name": "bug"},
                                         {"name": "mmw:problem"}])
        self.assertIn("#1: added mmw:problem; removed none; rule 1", out)
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_an_issue_mmw_did_not_open_is_skipped(self):
        row = self.issue(body="## Problems\nExternal bug report")
        code, out, err = self.run_migrate(Fake(issue_pages=[[row, self.issue(2)]]))
        self.assertEqual(code, 0, err)
        self.assertEqual(row["labels"], [{"name": "needs-triage"}])
        self.assertIn("SKIP #1: not opened by MMW", out)
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_an_unapproved_ticket_becomes_a_problem(self):
        for parent in (None, {"number": 2}):
            with self.subTest(parent=parent):
                row = self.issue(names=("mmw:ticket", "needs-triage", "senior-worker"),
                                 parent=parent)
                fake = Fake(issue_pages=[[row, self.issue(2, names=("mmw:map",))]])
                code, out, err = self.run_migrate(fake)
                self.assertEqual(code, 0, err)
                self.assertEqual(row["labels"], [{"name": "needs-triage"},
                                                 {"name": "senior-worker"},
                                                 {"name": "mmw:problem"}])
                self.assertIn("#1: added mmw:problem; removed mmw:ticket; rule 2", out)
                self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_a_ticket_a_worker_claimed_is_left_a_ticket(self):
        histories = [
            [self.event("ticket.claimed", login="owner", branch="issue-1", commit="0" * 40)],
            [self.event("worker.started", session="wk-1", runner="paseo", machine="mac-1",
                        host="codex", model="gpt-5", effort="high", grade="senior-worker",
                        worktree="/repo/.worktrees/issue-1", branch="issue-1", base="0" * 40),
             self.event("worker.lost", session="wk-1", runner="paseo", reason="ended")],
        ]
        for history in histories:
            with self.subTest(history=history):
                row = self.issue(names=("mmw:ticket", "needs-triage"),
                                 comments=["ordinary comment"] * 100 + history)
                code, out, err = self.run_migrate(Fake(issue_pages=[[row, self.issue(2)]]))
                self.assertEqual(code, 0, err)
                self.assertEqual(row["labels"], [{"name": "mmw:ticket"}, {"name": "needs-triage"}])
                self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_a_ticket_under_a_spec_is_left_a_ticket(self):
        row = self.issue(names=("mmw:ticket", "needs-triage"), parent={"number": 2})
        parent = self.issue(2, names=("mmw:spec",))
        code, out, err = self.run_migrate(Fake(issue_pages=[[row, parent, self.issue(3)]]))
        self.assertEqual(code, 0, err)
        self.assertEqual(row["labels"], [{"name": "mmw:ticket"}, {"name": "needs-triage"}])
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_children_are_left_as_they_are(self):
        for names in (("mmw:child", "needs-triage"),
                      ("mmw:child", "mmw:ticket", "needs-triage")):
            with self.subTest(names=names):
                row = self.issue(names=names)
                code, out, err = self.run_migrate(Fake(issue_pages=[[row, self.issue(2)]]))
                self.assertEqual(code, 0, err)
                self.assertEqual(row["labels"], [{"name": name} for name in names])
                self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_needs_info_issues_are_listed_not_changed(self):
        rows = [self.issue(names=("needs-info", "needs-triage")),
                self.issue(2, names=("needs-info", "mmw:ticket")),
                self.issue(3, names=("needs-info", "mmw:child")), self.issue(4)]
        code, out, err = self.run_migrate(Fake(issue_pages=[rows]))
        self.assertEqual(code, 0, err)
        self.assertEqual([row["labels"] for row in rows], [
            [{"name": "needs-info"}, {"name": "needs-triage"}],
            [{"name": "needs-info"}, {"name": "mmw:ticket"}],
            [{"name": "needs-info"}, {"name": "mmw:child"}],
            [{"name": "needs-triage"}, {"name": "mmw:problem"}],
        ])
        for number in (1, 2, 3):
            self.assertIn(f"NEEDS-INFO #{number}: left for the owner", out)
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_a_second_migrate_changes_nothing(self):
        fake = Fake(issue_pages=[[self.issue(), self.issue(2, names=("mmw:ticket",))]])
        fake.labels_have["needs-triage"] = ("123456", "old meaning")
        code, out, err = self.run_migrate(fake)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 2 changed")
        fake.calls.clear()
        code, out, err = self.run_migrate(fake)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 0 changed")
        self.assertFalse(any(c[:3] in (["gh", "issue", "edit"], ["gh", "label", "edit"],
                                     ["gh", "label", "create"]) for c in fake.calls))
        self.assertEqual(fake.issue_pages[0][0]["labels"],
                         [{"name": "needs-triage"}, {"name": "mmw:problem"}])
        self.assertEqual(fake.issue_pages[0][1]["labels"], [{"name": "mmw:problem"}])

    def test_migrate_reads_every_page(self):
        first = [self.issue(number, names=("mmw:spec",)) for number in range(1, 101)]
        row = self.issue(101)
        code, out, err = self.run_migrate(Fake(issue_pages=[first, [row]]))
        self.assertEqual(code, 0, err)
        self.assertEqual(row["labels"], [{"name": "needs-triage"}, {"name": "mmw:problem"}])
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_wayfinder_decisions_and_pull_requests_are_not_migrated(self):
        decision = self.issue(names=("needs-triage", "wayfinder:research"))
        pull = self.issue(2)
        pull["pull_request"] = {"url": "https://example.test/pull/2"}
        code, out, err = self.run_migrate(Fake(issue_pages=[[decision, pull, self.issue(3)]]))
        self.assertEqual(code, 0, err)
        self.assertEqual(decision["labels"], [{"name": "needs-triage"}, {"name": "wayfinder:research"}])
        self.assertEqual(pull["labels"], [{"name": "needs-triage"}])
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")

    def test_a_failed_write_can_be_retried_without_changing_completed_issues(self):
        fake = Fake(issue_pages=[[self.issue(), self.issue(2, names=("mmw:ticket",)), self.issue(3)]])

        def refusing(cmd, **kwargs):
            if cmd[:4] == ["gh", "issue", "edit", "2"]:
                return done(cmd, 1, err="HTTP 403: cannot edit issue")
            return fake(cmd, **kwargs)

        code, out, err = self.run_migrate(refusing)
        self.assertEqual(code, 1)
        self.assertIn("could not edit #2 by rule 2: HTTP 403", err)
        self.assertNotIn("MIGRATE OK", out)
        self.assertEqual(fake.issue_pages[0][0]["labels"],
                         [{"name": "needs-triage"}, {"name": "mmw:problem"}])
        self.assertEqual(fake.issue_pages[0][1]["labels"], [{"name": "mmw:ticket"}])
        self.assertEqual(fake.issue_pages[0][2]["labels"],
                         [{"name": "needs-triage"}, {"name": "mmw:problem"}])
        code, out, err = self.run_migrate(refusing)
        self.assertEqual(code, 1)
        self.assertIn("could not edit #2 by rule 2: HTTP 403", err)
        self.assertNotIn("MIGRATE OK", out)
        fake.calls.clear()
        code, out, err = self.run_migrate(fake)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines()[-1], "MIGRATE OK 1 changed")
        self.assertEqual([c[3] for c in fake.calls if c[:3] == ["gh", "issue", "edit"]], ["2"])
        self.assertEqual(fake.issue_pages[0][1]["labels"], [{"name": "mmw:problem"}])

    def test_read_and_label_failures_exit_one_without_migrating_an_issue(self):
        endpoint = "repos/{owner}/{repo}/issues?state=open&per_page=100"
        failures = [
            (["label", "list"], 1, "", "HTTP 403: labels unreadable", "labels unreadable"),
            (["label", "create"], 1, "", "HTTP 403: labels unwritable", "labels unwritable"),
            (["label", "edit"], 1, "", "HTTP 403: description unwritable", "description unwritable"),
            (["api"], 1, "", "HTTP 502: issues unreadable", f"{endpoint} failed: HTTP 502"),
            (["api"], 0, "invalid JSON", "", f"{endpoint} did not return JSON"),
            (["api"], 0, "{}", "", f"{endpoint} did not return pages of rows"),
            (["issue", "view", "1"], 1, "", "HTTP 502: parent unreadable",
             "gh issue view 1 --json parent failed: HTTP 502"),
            (["issue", "view", "2"], 1, "", "HTTP 502: parent labels unreadable",
             "gh issue view 2 --json labels failed: HTTP 502"),
        ]
        for prefix, status, stdout, stderr, expected in failures:
            with self.subTest(prefix=prefix, stdout=stdout):
                fake = Fake(issue_pages=[[self.issue(names=("mmw:ticket",), parent={"number": 2}),
                                          self.issue(2, names=("mmw:map",))]])
                fake.labels_have.pop("mmw:lesson")
                fake.labels_have["needs-triage"] = ("123456", "old")

                def refusing(cmd, **kwargs):
                    if cmd[1:1 + len(prefix)] == prefix:
                        return done(cmd, status, stdout, stderr)
                    return fake(cmd, **kwargs)

                code, out, err = self.run_migrate(refusing)
                self.assertEqual(code, 1)
                self.assertIn(expected, err)
                self.assertNotIn("MIGRATE OK", out)
                self.assertEqual(fake.issue_pages[0][0]["labels"], [{"name": "mmw:ticket"}])
                self.assertFalse(any(c[:3] == ["gh", "issue", "edit"] for c in fake.calls))

    def test_unreadable_comments_do_not_turn_a_ticket_into_a_problem(self):
        endpoint = "repos/{owner}/{repo}/issues/1/comments?per_page=100"
        failures = [(1, "", "HTTP 502: comments unreadable", f"{endpoint} failed: HTTP 502"),
                    (0, "invalid JSON", "", f"{endpoint} did not return JSON"),
                    (0, "[[null]]", "", f"{endpoint} did not return issue or comment objects"),
                    (0, json.dumps([[{"body": "An event\n<!-- mmw {broken} -->"}]]), "",
                     "could not read events of #1:")]
        for status, stdout, stderr, expected in failures:
            with self.subTest(stdout=stdout, stderr=stderr):
                row = self.issue(names=("mmw:ticket",))
                later = self.issue(2)
                fake = Fake(issue_pages=[[row, later]])

                def refusing(cmd, **kwargs):
                    if any("/comments?" in arg for arg in cmd):
                        return done(cmd, status, stdout, stderr)
                    return fake(cmd, **kwargs)

                code, out, err = self.run_migrate(refusing)
                self.assertEqual(code, 1)
                self.assertIn(expected, err)
                self.assertNotIn("MIGRATE OK", out)
                self.assertEqual(row["labels"], [{"name": "mmw:ticket"}])
                self.assertEqual(later["labels"], [{"name": "needs-triage"}, {"name": "mmw:problem"}])


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "mmw-home"
        self.home.mkdir()
        self.toolbox = self.root / "toolbox" / "mmw-v4"
        self.toolbox.mkdir(parents=True)
        (self.toolbox / "install.sh").write_text("#!/usr/bin/env bash\n")
        (self.home / "installed-root").write_text(f"{self.toolbox}\n")

    def tearDown(self):
        self.tmp.cleanup()

    def set_up_repository(self):
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "check").write_text("#!/usr/bin/env bash\nexit 0\n")
        (self.root / "scripts" / "check").chmod(0o755)
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n")

    def run_check(self, fake):
        check = load("check")
        with mock.patch("subprocess.run", side_effect=fake), \
             mock.patch.dict("os.environ", {"MMW_HOME": str(self.home)}), \
             redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            code = check.main()
        sys.modules.pop("labels", None)
        return code, out.getvalue()

    def env_repository(self, resource='"shared-db"', fail="", failure_message="fixture failure"):
        self.set_up_repository()
        self.log = self.root / "env-calls.jsonl"
        script = self.root / "scripts" / "env"
        script.write_text(
            f"#!{sys.executable}\n"
            "import json, pathlib, sys\n"
            "verb, tree = sys.argv[1:]\n"
            f"with open({str(self.log)!r}, 'a') as log:\n"
            "    log.write(json.dumps([verb, tree, str(pathlib.Path.cwd())]) + '\\n')\n"
            f"if verb == {fail!r}:\n"
            f"    print({failure_message!r}, file=sys.stderr)\n"
            "    sys.exit(1)\n"
            f"if verb == 'up': print({resource})\n")
        script.chmod(0o755)
        for args in (["init", "-q"], ["add", "scripts/env"],
                     ["-c", "user.name=Test", "-c", "user.email=test@example.test",
                      "commit", "-qm", "environment fixture"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        real_run = subprocess.run
        fake = Fake(root=self.root)

        def boundary(cmd, **kwargs):
            if (cmd[0] == "git" and "worktree" in cmd) or str(cmd[0]).endswith("/scripts/env"):
                return real_run(cmd, **kwargs)
            return fake(cmd, **kwargs)

        return boundary

    def test_env_row_missing_on_shared_resources(self):
        boundary = self.env_repository()
        code, out = self.run_check(boundary)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +scripts/env:.*shared-db")

    def test_env_row_ok_on_separate_resources(self):
        boundary = self.env_repository(resource='"db-" + pathlib.Path(tree).name')
        code, out = self.run_check(boundary)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"(?m)^ok +repository +scripts/env:")

    def test_env_row_missing_when_up_names_no_resources(self):
        boundary = self.env_repository(resource=repr(" \t "))
        code, out = self.run_check(boundary)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +scripts/env:.*scripts/env up")

    def test_env_failure_without_message_reports_exit(self):
        boundary = self.env_repository(fail="setup", failure_message=" ")
        code, out = self.run_check(boundary)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +scripts/env:.*scripts/env setup.*exit 1")

    def test_env_probe_cleans_up(self):
        for failure in ("", "setup", "up", "down"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                original = self.root
                self.root = Path(temporary)
                try:
                    boundary = self.env_repository(resource='"db-" + pathlib.Path(tree).name',
                                                   fail=failure)
                    code, out = self.run_check(boundary)
                    self.assertEqual(code, 1 if failure else 0, out)
                    if failure:
                        self.assertIn(f"scripts/env {failure}", out)
                        self.assertIn("fixture failure", out)
                    calls = [json.loads(line) for line in self.log.read_text().splitlines()]
                    trees = {tree for verb, tree, cwd in calls}
                    self.assertEqual(len(trees), 2)
                    for tree in trees:
                        verbs = [verb for verb, path, cwd in calls if path == tree]
                        self.assertEqual(verbs, ["setup", "down"] if failure == "setup"
                                         else ["setup", "up", "down"])
                    self.assertTrue(all(Path(cwd).resolve() == Path(tree).resolve()
                                        for verb, tree, cwd in calls))
                    listed = subprocess.run(["git", "worktree", "list", "--porcelain"],
                                            cwd=self.root, capture_output=True, text=True, check=True)
                    self.assertEqual(listed.stdout.count("worktree "), 1, listed.stdout)
                finally:
                    self.root = original

    def test_env_row_reads_the_tests_not_testing_md(self):
        self.set_up_repository()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True, capture_output=True)
        real_run = subprocess.run
        fake = Fake(root=self.root)

        def boundary(cmd, **kwargs):
            if cmd[:2] == ["git", "ls-files"]:
                return real_run(cmd, **kwargs)
            return fake(cmd, **kwargs)

        for directory in ("test", "tests", "__tests__", "spec", "e2e"):
            path = self.root / "packages" / "a" / directory / "nested" / "resource test.py"
            path.parent.mkdir(parents=True)
            path.write_text("Tests use Postgres.\n")
            subprocess.run(["git", "add", str(path)], cwd=self.root, check=True, capture_output=True)
            with self.subTest(directory=directory):
                code, out = self.run_check(boundary)
                self.assertEqual(code, 1, out)
                self.assertRegex(out, r"(?m)^missing +repository +scripts/env:")
            subprocess.run(["git", "rm", "-f", str(path)], cwd=self.root, check=True, capture_output=True)

        path = self.root / "tests" / "resources.py"
        path.parent.mkdir()
        path.touch()
        subprocess.run(["git", "add", str(path)], cwd=self.root, check=True, capture_output=True)
        for source in (path, self.root / "scripts" / "check"):
            for word in ("Postgres", "POSTGRESQL", "mysql", "Redis", "Docker", "database",
                         "databases", "container", "containers", "port", "ports", "数据库", "端口", "容器",
                         "测试用到数据库和容器", "测试使用端口", "测试用到数据库。", "测试使用数据库进行"):
                with self.subTest(source=source, word=word):
                    source.write_text(f"Tests use {word}.\n")
                    code, out = self.run_check(boundary)
                    self.assertEqual(code, 1, out)
                    self.assertRegex(out, r"(?m)^missing +repository +scripts/env:")
            source.write_text("Tests use files. Export reports.\n")

        for name in ("TESTING.md", "docs/database.md", "testing/resources.py", "tests/untracked.py"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Tests use database containers and ports.\n")
            if name != "tests/untracked.py":
                subprocess.run(["git", "add", str(path)], cwd=self.root, check=True, capture_output=True)
        code, out = self.run_check(boundary)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"(?m)^ok +repository +scripts/env:")

    def test_env_row_reports_unreadable_sources_without_losing_other_rows(self):
        self.set_up_repository()
        (self.root / "tests").mkdir()
        test = self.root / "tests" / "resources.py"
        test.write_text("port = 5432\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "add", str(test)], cwd=self.root, check=True, capture_output=True)
        real_run = subprocess.run
        fake = Fake(root=self.root)

        def boundary(cmd, **kwargs):
            if cmd[:2] == ["git", "ls-files"]:
                return real_run(cmd, **kwargs)
            return fake(cmd, **kwargs)

        for source in (test, self.root / "scripts" / "check"):
            with self.subTest(source=source):
                mode = source.stat().st_mode
                source.chmod(0o111)
                try:
                    code, out = self.run_check(boundary)
                    self.assertRegex(out, r"(?m)^unchecked +repository +scripts/env:")
                    self.assertIn(str(source), out)
                    self.assertIn("Permission denied", out)
                    self.assertRegex(out, r"(?m)^ok +machine +install:")
                    self.assertIn("SETUP OK", out)
                finally:
                    source.chmod(mode)
            test.write_text("Tests use files.\n")

    def test_env_row_missing_without_scripts_env(self):
        self.set_up_repository()
        for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
            with self.subTest(compose=name):
                compose = self.root / name
                compose.write_text("services: {}\n")
                fake = Fake(root=self.root)

                def failing_index(cmd, **kwargs):
                    if cmd[:2] == ["git", "ls-files"]:
                        return done(cmd, 1, err="index unavailable")
                    return fake(cmd, **kwargs)

                code, out = self.run_check(failing_index)
                self.assertEqual(code, 1, out)
                self.assertRegex(out, r"(?m)^missing +repository +scripts/env:")
                compose.unlink()

    def test_env_row_ok_when_not_needed(self):
        self.set_up_repository()
        (self.root / "scripts" / "check").write_text("Tests use files. Export reports.\n")
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"(?m)^ok +repository +scripts/env:")

    def test_a_repository_set_up_is_setup_ok(self):
        self.set_up_repository()
        (self.root / "design" / "notes").mkdir(parents=True)
        fake = Fake(root=self.root)
        code, out = self.run_check(fake)
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith("SETUP OK"), out)

    def test_check_has_no_testing_md_row(self):
        fake = Fake(root=self.root, labels_have={}, ignored=())
        code, out = self.run_check(fake)
        self.assertEqual(code, 1)
        for item in ("labels", ".gitignore", "scripts/check", "CLAUDE.md"):
            self.assertRegex(out, rf"(?m)^missing +repository +{item}:", item)
        self.assertTrue(out.rstrip().endswith("SETUP INCOMPLETE 4 missing"), out)
        self.assertNotIn("TESTING.md", out)
        self.assertEqual(fake.writes(), [])
        self.assertEqual(fake.labels_have, {})
        (self.root / "TESTING.md").write_text("Tests use files.\n")
        code, out = self.run_check(fake)
        self.assertEqual(code, 1, out)
        self.assertNotIn("TESTING.md", out)
        self.assertTrue(out.rstrip().endswith("SETUP INCOMPLETE 4 missing"), out)

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

    def test_a_missing_claude_md_is_missing_and_check_writes_none(self):
        self.set_up_repository()
        (self.root / "CLAUDE.md").unlink()
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +repository +CLAUDE.md: absent; setup creates it, "
                              r"holding the one line @AGENTS.md")
        self.assertTrue(out.rstrip().endswith("SETUP INCOMPLETE 1 missing"), out)
        self.assertFalse((self.root / "CLAUDE.md").exists())

    def test_any_existing_claude_md_is_ok_and_left_as_it_is(self):
        self.set_up_repository()
        own = "# House rules\n\nSee docs/CONTRIBUTING.md.\n"
        (self.root / "CLAUDE.md").write_text(own)
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"(?m)^ok +repository +CLAUDE.md: present$")
        self.assertEqual((self.root / "CLAUDE.md").read_text(), own)

    def test_the_install_is_read_through_its_own_check(self):
        self.set_up_repository()
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 0, out)
        self.assertRegex(out, rf"(?m)^ok +machine +install: {self.toolbox}/install.sh --check passes$")

        gaps = (1, "", "缺    /home/.claude/skills/dispatch\n缺    /home/.codex/hooks.json\n")
        code, out = self.run_check(Fake(root=self.root, install=gaps))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +machine +install: .* --check exits 1, 2 line\(s\) on stderr, "
                              r"first: 缺    /home/.claude/skills/dispatch; run bash .*/install.sh to repair it$")
        self.assertTrue(out.rstrip().endswith("SETUP INCOMPLETE 1 missing"), out)

    def test_the_machine_is_one_install_row_and_check_asks_nothing_else_of_it(self):
        self.set_up_repository()
        fake = Fake(root=self.root)
        code, out = self.run_check(fake)
        self.assertEqual(code, 0, out)
        machine = [line.split(":", 1)[0].split() for line in out.splitlines() if " machine " in line]
        self.assertEqual(machine, [["ok", "machine", "install"]])
        self.assertFalse([c for c in fake.calls if c[:3] == ["gh", "auth", "status"]], fake.calls)

    def test_a_machine_with_no_install_is_missing_and_runs_nothing(self):
        self.set_up_repository()
        (self.home / "installed-root").unlink()
        fake = Fake(root=self.root)
        code, out = self.run_check(fake)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +machine +install: no .*installed-root; MMW is not installed")
        self.assertFalse([c for c in fake.calls if c[0] == "bash"], fake.calls)

        (self.home / "installed-root").write_text(f"{self.root / 'gone'}\n")
        code, out = self.run_check(Fake(root=self.root))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"(?m)^missing +machine +install: .* which has no install.sh")

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
