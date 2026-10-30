import importlib.util
import fcntl
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "skills"
SCRIPT = SCRIPTS / "register-problem" / "scripts" / "register.py"
VERIFY_TESTS = Path(__file__).resolve().parents[1] / "verify-ticket"
sys.path.insert(0, str(VERIFY_TESTS))
from _load import event, load_events


def load():
    spec = importlib.util.spec_from_file_location("register", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


register = load()
events = load_events()
REAL_RUN = subprocess.run


def problem(code="test-compares-empty-lists", angle="判断"):
    return (f"## Problem\n\n问题代号：{code}\n角度：{angle}\n发生了什么：测试比较空列表\n"
            "证据：tests/test_board.py:193\n代价：看板漏角色仍然通过\n该谁修：o/r\n")


def issue(number=10, state="open", reason=None, labels=("mmw:lesson",), body=None):
    return dict(number=number, title="测试比较空列表", body=body or problem(), state=state,
                state_reason=reason, labels=[{"name": n} for n in labels], comments=[],
                parent=None, closer=None, html_url=f"https://github.com/o/r/issues/{number}")


class Fake:
    def __init__(self):
        self.repos = {"o/r": [], "acme/toolbox": []}
        self.labels = {"o/r": {}, "acme/toolbox": {}}
        self.calls = []
        self.fail = None
        self.session = None

    def __call__(self, cmd, **kwargs):
        if cmd[0] in ("git", "ps"):
            return REAL_RUN(cmd, **kwargs)
        if cmd[0] == "bash" and cmd[-1] == "self":
            out = "\t".join(self.session) if self.session else ""
            return subprocess.CompletedProcess(cmd, 0 if out else 2, out, "")
        if cmd[0] != "gh":
            raise AssertionError(cmd)
        self.calls.append(cmd)
        if self.fail and self.fail(cmd):
            return subprocess.CompletedProcess(cmd, 1, "", "HTTP 503 unavailable")
        args = cmd[1:]
        def flag(name):
            return args[args.index(name) + 1]
        if args[:2] == ["repo", "view"]:
            if "--jq" in args:
                repo = "o/r" if args[2] == "https://github.com/o/r.git" else "upstream/skills"
                return subprocess.CompletedProcess(cmd, 0, repo + "\n", "")
            data = {"nameWithOwner": "o/r"}
        elif args[:2] == ["label", "create"]:
            repo, name = flag("--repo"), args[2]
            if name in self.labels[repo]:
                return subprocess.CompletedProcess(cmd, 1, "", "already exists")
            self.labels[repo][name] = (flag("--color"), flag("--description"))
            data = {}
        elif args[:2] == ["issue", "create"]:
            repo = flag("--repo")
            next_number = max((r["number"] for r in self.repos[repo]), default=99) + 1
            row = issue(number=next_number, body=Path(flag("--body-file")).read_text(), labels=())
            row["title"] = flag("--title")
            row["labels"] = [{"name": args[i + 1]} for i, a in enumerate(args) if a == "--label"]
            self.repos[repo].append(row)
            return subprocess.CompletedProcess(cmd, 0, f"https://github.com/{repo}/issues/{next_number}\n", "")
        elif args[:2] == ["issue", "view"]:
            data = self.row(flag("--repo"), int(args[2]))
        elif args[:2] == ["issue", "reopen"]:
            data = self.row(flag("--repo"), int(args[2]))
            data["state"], data["state_reason"] = "open", "reopened"
        elif args[:2] == ["issue", "edit"]:
            data = self.row(flag("--repo"), int(args[2]))
            name = flag("--add-label")
            if {"name": name} not in data["labels"]:
                data["labels"].append({"name": name})
        elif args[:2] == ["issue", "comment"]:
            row = self.row(flag("--repo"), int(args[2]))
            body = Path(flag("--body-file")).read_text()
            data = {"id": len(row["comments"]) + 1, "body": body}
            row["comments"].append(data)
        elif args[0] == "api":
            endpoint = args[1]
            if endpoint == "graphql":
                variables = dict(a.split("=", 1) for i, a in enumerate(args) if args[i-1] in ("-F", "-f"))
                row = self.row(variables["o"] + "/" + variables["r"], int(variables["n"]))
                data = {"data": {"repository": {"issue": {
                    "timelineItems": {"nodes": [{"closer": row["closer"]}]}}}}}
            else:
                parts = endpoint.split("?")[0].split("/")
                repo = "/".join(parts[1:3])
                if len(parts) == 4:
                    self.assert_paginated(args)
                    if parts[3] == "labels":
                        rows = [{"name": n, "color": c, "description": d}
                                for n, (c, d) in self.labels[repo].items()]
                    else:
                        rows = [{k: v for k, v in r.items() if k not in ("comments", "parent", "closer")}
                                for r in self.repos[repo]]
                    data = [rows[:1], rows[1:]]
                elif parts[-1] == "comments":
                    self.assert_paginated(args)
                    data = [self.row(repo, int(parts[4]))["comments"]]
                else:
                    data = self.row(repo, int(parts[4]))
        else:
            raise AssertionError(cmd)
        return subprocess.CompletedProcess(cmd, 0, json.dumps(data, ensure_ascii=False), "")

    def assert_paginated(self, args):
        if "--paginate" not in args or "--slurp" not in args or "per_page=100" not in args[1]:
            raise AssertionError(f"incomplete list read: {args}")

    def row(self, repo, number):
        return next(r for r in self.repos[repo] if r["number"] == number)


class Registration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "mmw"
        self.home.mkdir()
        self.toolbox = self.root / "toolbox"
        self.toolbox.mkdir()
        REAL_RUN(["git", "init", "-q", str(self.toolbox)], check=True)
        REAL_RUN(["git", "-C", str(self.toolbox), "remote", "add", "origin", "git@github.com:acme/toolbox.git"], check=True)
        (self.home / "installed-root").write_text(str(self.toolbox))
        self.product = self.root / "product"
        REAL_RUN(["git", "init", "-q", "-b", "main", str(self.product)], check=True)
        REAL_RUN(["git", "-C", str(self.product), "remote", "add", "origin", "https://github.com/o/r.git"], check=True)
        self.path = self.root / "problem.md"
        self.path.write_text(problem())
        self.fake = Fake()

    def run_register(self, *args, env=None):
        clean = {k: v for k, v in os.environ.items() if not k.startswith("MMW_")}
        clean["MMW_HOME"] = str(self.home)
        clean.update(env or {})
        with chdir(self.product), mock.patch.dict(os.environ, clean, clear=True), \
             mock.patch.object(register.subprocess, "run", side_effect=self.fake), \
             redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            rc = register.main(list(args))
        return rc, out.getvalue(), err.getvalue()

    def test_find_lists_open_and_closed_matches(self):
        nonmatch = issue(21, body=problem("unrelated-problem").replace("空列表", "账户"))
        nonmatch["title"] = "账户问题"
        self.fake.repos["o/r"] = [issue(), issue(11, "closed", "not_planned"), nonmatch]
        self.fake.repos["acme/toolbox"] = [issue(12), nonmatch]
        rc, out, err = self.run_register("find", "空列表")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.splitlines(), [
            "#10\to/r\topen\tmmw:lesson\ttest-compares-empty-lists\t测试比较空列表",
            "#11\to/r\tclosed\tmmw:lesson\ttest-compares-empty-lists\t测试比较空列表",
            "#12\tacme/toolbox\topen\tmmw:lesson\ttest-compares-empty-lists\t测试比较空列表",
        ])

    def test_a_new_lesson_is_opened_with_only_its_kind(self):
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 0, err)
        self.assertEqual(len(self.fake.repos["o/r"]), 1)
        row = self.fake.repos["o/r"][0]
        self.assertEqual(row["labels"], [{"name": "mmw:lesson"}])
        self.assertEqual(row["body"], problem())
        self.assertEqual(events.fold(row["comments"])["occurrences"][0]["source"], "noticed")
        self.assertIn("#100", out)

    def test_default_registration_uses_origin_despite_gh_repo(self):
        rc, out, err = self.run_register("add", str(self.path), env={"GH_REPO": "upstream/skills"})
        self.assertEqual(rc, 0, err)
        self.assertEqual(len(self.fake.repos["o/r"]), 1)
        self.assertIn("in o/r", out)

    def test_missing_origin_refuses_registration_before_writes(self):
        REAL_RUN(["git", "-C", str(self.product), "remote", "remove", "origin"], check=True)
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 2, out)
        self.assertIn("origin", err)
        self.assertFalse(self.fake.calls)

    def test_a_new_product_problem_is_opened_awaiting_the_owner(self):
        self.path.write_text(problem(angle="产品"))
        rc, out, err = self.run_register("add", str(self.path), "--source", "owner-correction")
        self.assertEqual(rc, 0, err)
        row = self.fake.repos["o/r"][0]
        self.assertEqual(row["labels"], [{"name": "mmw:problem"}, {"name": "needs-triage"}])
        self.assertEqual(events.fold(row["comments"])["occurrences"][0]["source"], "owner-correction")

    def test_title_limit_keeps_full_body_and_duplicate_registration(self):
        description = "故障😀界" * 100
        body = problem().replace("测试比较空列表", description)
        self.path.write_text(body)
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 0, err)
        create = next(c for c in self.fake.calls if c[1:3] == ["issue", "create"])
        title = create[create.index("--title") + 1]
        self.assertEqual(len(title), 256)
        self.assertTrue(title.startswith("test-compares-empty-lists: "))
        self.assertTrue(title.endswith("…"))
        row = self.fake.repos["o/r"][0]
        self.assertEqual(row["body"], body)
        rc, out, err = self.run_register("find", "test-compares-empty-lists", description)
        self.assertEqual(rc, 0, err)
        self.assertIn("#100\to/r\topen\tmmw:lesson\ttest-compares-empty-lists\t", out)
        second = self.root / "second.md"
        second.write_text(body.replace(description, "另一次发生"))
        rc, out, err = self.run_register("add", str(second))
        self.assertEqual((rc, out), (0, "APPENDED: #100 in o/r\n"), err)
        self.assertEqual(len(self.fake.repos["o/r"]), 1)
        self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2)

    def test_code_limit_refuses_81_before_writes_and_accepts_80(self):
        self.path.write_text(problem("a" * 81))
        rc, out, err = self.run_register("add", str(self.path))
        self.assertNotEqual(rc, 0)
        self.assertIn("80", err)
        self.assertIn("81", err)
        writes = [c for c in self.fake.calls if c[1:3] in (
            ["label", "create"], ["issue", "create"], ["issue", "comment"],
            ["issue", "edit"], ["issue", "reopen"])]
        self.assertEqual(writes, [])
        self.assertEqual(self.fake.repos, {"o/r": [], "acme/toolbox": []})
        self.assertEqual(self.fake.labels, {"o/r": {}, "acme/toolbox": {}})
        body = problem("a" * 80)
        self.path.write_text(body)
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual((rc, out), (0, "OPENED: #100 in o/r\n"), err)
        row = self.fake.repos["o/r"][0]
        self.assertEqual(row["title"], "a" * 80 + ": 测试比较空列表")
        self.assertEqual(row["body"], body)

    def existing(self, **kwargs):
        row = issue(**kwargs)
        row["comments"] = [{"id": 1, "body": event("lesson.seen", "Seen #10", ticket=61,
                            lesson=row["number"], seen_in="o/r", source="noticed", session="none")}]
        self.fake.repos["acme/toolbox"] = [row]
        return row

    def test_an_open_match_gets_one_more_occurrence(self):
        row = self.existing()
        row["body"] = row["body"].replace("\n", "\r\n")
        self.fake.repos["o/r"] = [issue(20, body=problem("test-compares-empty-lists-other"))]
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 0, err)
        self.assertEqual([r["number"] for r in self.fake.repos["o/r"]], [20])
        self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2)
        self.assertEqual(row["state"], "open")
        self.assertEqual(len([line for line in row["comments"][-1]["body"].splitlines() if line.strip()]), 2)

    def test_a_second_registration_from_the_same_session_adds_no_occurrence(self):
        self.fake.session = ("orca", "same-session")
        rc, out, err = self.run_register("add", str(self.path), "--source", "retro-signal")
        self.assertEqual(rc, 0, err)
        row = self.fake.repos["o/r"][0]
        first_comment = row["comments"][0]["id"]
        second = self.root / "second.md"
        second.write_text(problem().replace("测试比较空列表", "另一次登记同一信号"))
        rc, out, err = self.run_register("add", str(second))
        self.assertEqual(rc, 0, err)
        self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 1)
        self.assertIn(f"https://github.com/o/r/issues/100#issuecomment-{first_comment}", out)
        row.update(state="closed", state_reason="completed",
                   closer={"url": "https://github.com/o/r/pull/9"})
        rc, out, err = self.run_register("add", str(second))
        self.assertEqual(rc, 0, err)
        self.assertEqual(row["state"], "open")
        self.assertIn({"name": "needs-triage"}, row["labels"])
        self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 1)
        self.assertIn(f"https://github.com/o/r/issues/100#issuecomment-{first_comment}", out)

    def test_one_session_on_two_tickets_adds_two_occurrences(self):
        self.fake.session = ("orca", "same-session")
        self.fake.repos["o/r"] = [issue(61, body="First ticket"), issue(62, body="Second ticket")]
        for ticket in (61, 62, 62):
            rc, out, err = self.run_register("add", str(self.path), "--ticket", str(ticket))
            self.assertEqual(rc, 0, err)
        row = self.fake.repos["o/r"][-1]
        occurrences = events.fold(row["comments"])["occurrences"]
        self.assertEqual([(r["session"], r["ticket"]) for r in occurrences],
                         [("orca:same-session", 61), ("orca:same-session", 62)])
        self.assertIn("ALREADY RECORDED", out)

    def test_registrations_from_two_sessions_add_two_occurrences(self):
        for session in ("first-session", "second-session"):
            self.fake.session = ("orca", session)
            rc, out, err = self.run_register("add", str(self.path))
            self.assertEqual(rc, 0, err)
        row = self.fake.repos["o/r"][0]
        self.assertEqual([r["session"] for r in events.fold(row["comments"])["occurrences"]],
                         ["orca:first-session", "orca:second-session"])

    def test_registrations_with_no_session_each_add_an_occurrence(self):
        for _ in range(2):
            rc, out, err = self.run_register("add", str(self.path))
            self.assertEqual(rc, 0, err)
        row = self.fake.repos["o/r"][0]
        self.assertEqual([r["session"] for r in events.fold(row["comments"])["occurrences"]],
                         ["none", "none"])

    def test_an_expired_lesson_is_reopened_as_pending(self):
        for labels, expected in ((("mmw:lesson",), [{"name": "mmw:lesson"}]),
                                 (("mmw:problem",), [{"name": "mmw:problem"}, {"name": "needs-triage"}])):
            with self.subTest(labels=labels):
                row = self.existing(state="closed", reason="not_planned", labels=labels)
                rc, out, err = self.run_register("add", str(self.path))
                self.assertEqual(rc, 0, err)
                self.assertEqual((row["state"], row["labels"]), ("open", expected))
                self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2)

    def test_a_fixed_problem_that_recurs_is_reopened_for_the_owner(self):
        for closed_by_pr in (True, False):
            with self.subTest(closed_by_pr=closed_by_pr):
                row = self.existing(state="closed", reason="completed")
                if closed_by_pr:
                    row["closer"] = {"url": "https://github.com/acme/toolbox/pull/9"}
                    expected = "https://github.com/acme/toolbox/pull/9"
                else:
                    row["comments"].append({"id": 2, "body": event("ticket.passed", "ALL MET", ticket=10, commit="a"*40)})
                    expected = "https://github.com/acme/toolbox/commit/" + "a"*40
                rc, out, err = self.run_register("add", str(self.path))
                self.assertEqual(rc, 0, err)
                self.assertEqual((row["state"], row["labels"]),
                                 ("open", [{"name": "mmw:lesson"}, {"name": "needs-triage"}]))
                self.assertIn("修了又犯", row["comments"][-1]["body"])
                self.assertIn(expected, row["comments"][-1]["body"])

    def test_a_ticket_of_an_unfinished_spec_is_not_reopened(self):
        for finished in (False, True):
            with self.subTest(finished=finished):
                row = self.existing(state="closed", reason="completed", labels=("mmw:ticket",))
                row["parent"] = {"number": 76}
                spec = issue(76, labels=("mmw:spec",), body="A batch")
                if finished:
                    spec["comments"] = [{"id": 1, "body": event("spec.merged", "Merged", ticket=None,
                                         spec=76, into="night", project="dev", merge="a"*40, base="b"*40)}]
                self.fake.repos["acme/toolbox"].append(spec)
                rc, out, err = self.run_register("add", str(self.path))
                self.assertEqual(rc, 0, err)
                self.assertEqual(row["state"], "open" if finished else "closed")
                self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2)
                if not finished:
                    self.assertIn("NOT REOPENED: #10 sits under spec #76, which has not finished", out)

    def test_a_refused_problem_stays_closed_and_is_counted(self):
        for reason in ("completed", "not_planned"):
            with self.subTest(reason=reason):
                row = self.existing(state="closed", reason=reason, labels=("mmw:lesson", "wontfix"))
                rc, out, err = self.run_register("add", str(self.path))
                self.assertEqual(rc, 0, err)
                self.assertEqual(row["state"], "closed")
                self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2)

    def test_refused_writes_exit_two_when_github_accepted_nothing(self):
        for verb in ("create", "comment", "reopen", "label-create"):
            with self.subTest(verb=verb):
                self.fake = Fake()
                if verb != "label-create":
                    self.fake.labels["o/r"]["mmw:lesson"] = ("123456", "already present")
                if verb not in ("create", "label-create"):
                    self.existing(state="closed" if verb == "reopen" else "open",
                                  reason="not_planned" if verb == "reopen" else None)
                before = json.dumps((self.fake.repos, self.fake.labels))
                self.fake.fail = lambda c: c[1:3] == (["label", "create"] if verb == "label-create" else ["issue", verb])
                path = self.root / f"refused-{verb}.md"
                path.write_text(problem())
                rc, out, err = self.run_register("add", str(path))
                self.assertEqual(rc, 2, err)
                self.assertIn("503", err)
                self.assertEqual(json.dumps((self.fake.repos, self.fake.labels)), before)

    def test_a_half_written_registration_is_finished_by_running_again(self):
        for failure in ("comment", "edit", "lost-comment-response", "lost-create-response", "lost-edit-response"):
            with self.subTest(failure=failure):
                self.fake = Fake()
                if failure in ("edit", "lost-edit-response"):
                    row = self.existing(state="closed", reason="completed")
                    row["closer"] = {"url": "https://github.com/acme/toolbox/pull/9"}
                self.fake.fail = lambda c: c[1:3] == ["issue", "edit" if failure == "edit" else "comment"]
                if failure.startswith("lost-"):
                    self.fake.fail = None
                    original = self.fake
                    def lost(cmd, **kwargs):
                        result = original(cmd, **kwargs)
                        if cmd[1:3] == ["issue", failure.split("-")[1]]:
                            return subprocess.CompletedProcess(cmd, 1, "", "connection lost after acceptance")
                        return result
                    self.fake = lost
                rc, out, err = self.run_register("add", str(self.path))
                if failure.startswith("lost-"):
                    self.assertEqual(rc, 0, err)
                    self.fake = original
                else:
                    self.assertEqual(rc, 1, err)
                    self.assertIn("#10" if failure == "edit" else "#100", err)
                    self.fake.fail = None
                    rc, out, err = self.run_register("add", str(self.path))
                    self.assertEqual(rc, 0, err)
                reopening = failure in ("edit", "lost-edit-response")
                repo = "acme/toolbox" if reopening else "o/r"
                row = self.fake.repos[repo][0]
                self.assertEqual(len(self.fake.repos[repo]), 1)
                self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2 if reopening else 1)
                if reopening:
                    self.assertIn({"name": "needs-triage"}, row["labels"])
                    self.assertIn("修了又犯", row["comments"][-1]["body"])
                    self.assertIn("https://github.com/acme/toolbox/pull/9", row["comments"][-1]["body"])

    def test_the_toolbox_repository_comes_from_the_installed_checkout(self):
        row = self.existing()
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 0, err)
        self.assertEqual([r["number"] for r in self.fake.repos["acme/toolbox"]], [10])
        self.assertEqual(self.fake.repos["o/r"], [])
        self.assertEqual(len(events.fold(row["comments"])["occurrences"]), 2)
        (self.home / "installed-root").unlink()
        before = len(self.fake.calls)
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("installed-root", err)
        self.assertEqual(len(self.fake.calls), before)

    def test_add_refuses_a_registration_for_another_repository(self):
        env, store = self.cli_environment()
        for responsible, target, expected in (("other/product", None, "other/product"),
                                               ("erp-frontend", "o/r", "<owner>/erp-frontend"),
                                               ("MMW", None, "acme/toolbox"),
                                               ("MMW 仓库", "o/r", "acme/toolbox")):
            with self.subTest(responsible=responsible, target=target):
                self.path.write_text(problem().replace("该谁修：o/r", f"该谁修：{responsible}"))
                args = ("--repo", target) if target else ()
                before = store.read_text()
                run = REAL_RUN([sys.executable, str(SCRIPT), "add", str(self.path), *args],
                               cwd=self.product, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn("--repo " + expected, run.stderr)
                self.assertEqual(store.read_text(), before)
                self.assertFalse((self.home / "state").exists())
        for responsible, target in (("o/r", None), ("r", "o/r"),
                                    ("MMW", "acme/toolbox"), ("MMW 仓库", "acme/toolbox"),
                                    ("由产品团队修复", "o/r")):
            with self.subTest(accepted=responsible):
                self.fake = Fake()
                self.path.write_text(problem().replace("该谁修：o/r", f"该谁修：{responsible}"))
                args = ("--repo", target) if target else ()
                rc, out, err = self.run_register("add", str(self.path), *args)
                self.assertEqual(rc, 0, err)
                row = self.fake.repos[target or "o/r"][0]
                payload = events.parse(row["comments"][0]["body"])[1]
                self.assertEqual(payload["seen_in"], "o/r")

    def test_add_with_ticket_records_ticket_and_parent_spec(self):
        for parent, unreadable in ((76, None), (None, None), (76, "61"), (76, "76")):
            with self.subTest(parent=parent, unreadable=unreadable):
                self.fake = Fake()
                ticket = issue(61, body="Active ticket", labels=("mmw:ticket",))
                ticket["parent"] = {"number": parent} if parent else None
                self.fake.repos["o/r"] = [ticket, issue(76, body="Batch", labels=("mmw:spec",))]
                if unreadable:
                    self.fake.fail = lambda c: c[1:4] == ["issue", "view", unreadable]
                rc, out, err = self.run_register("add", str(self.path), "--ticket", "61",
                                                 env={"MMW_TICKET": "99", "MMW_SPEC": "98"})
                self.assertEqual(rc, 0, err)
                payload = events.parse(self.fake.repos["o/r"][-1]["comments"][0]["body"])[1]
                self.assertEqual((payload["ticket"], payload["spec"]),
                                 (61, None if unreadable else parent))
                if unreadable:
                    self.assertIn("spec", err)
                    self.assertIn("o/r#61", err)
                    self.assertIn("503", err)
                else:
                    self.assertEqual(err, "")

    def test_nonpositive_ticket_is_refused_before_any_write(self):
        env, store = self.cli_environment()
        env.update(MMW_TICKET="61", MMW_SPEC="76")
        before = store.read_text()
        for value in ("0", "-1"):
            with self.subTest(value=value):
                run = REAL_RUN([sys.executable, str(SCRIPT), "add", str(self.path), "--ticket", value],
                               cwd=self.product, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn("--ticket", run.stderr)
                self.assertIn("positive", run.stderr)
                self.assertEqual(store.read_text(), before)
                self.assertFalse((self.home / "state").exists())

    def test_ticket_context_stays_in_product_when_fix_belongs_to_mmw(self):
        ticket = issue(61, body="Product ticket", labels=("mmw:ticket",))
        ticket["parent"] = {"number": 76}
        self.fake.repos["o/r"] = [ticket, issue(76, body="Product spec", labels=("mmw:spec",))]
        unrelated = issue(61, body="MMW ticket", labels=("mmw:ticket",))
        unrelated["parent"] = {"number": 98}
        self.fake.repos["acme/toolbox"] = [unrelated, issue(98, body="MMW spec", labels=("mmw:spec",))]
        self.path.write_text(problem().replace("该谁修：o/r", "该谁修：MMW"))
        env, store = self.cli_environment()
        env.update(MMW_TICKET="99", MMW_SPEC="98")
        run = REAL_RUN([sys.executable, str(SCRIPT), "add", str(self.path), "--repo", "acme/toolbox",
                        "--ticket", "61", "--source", "stall"], cwd=self.product,
                       env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        row = json.loads(store.read_text())["repos"]["acme/toolbox"][-1]
        payload = events.parse(row["comments"][0]["body"])[1]
        self.assertEqual((payload["seen_in"], payload["ticket"], payload["spec"], payload["source"]),
                         ("o/r", 61, 76, "stall"))

    def test_occurrence_carries_the_active_ticket_spec_runner_and_role(self):
        ticket = issue(61, body="Active ticket", labels=("mmw:ticket",))
        ticket["parent"] = {"number": 76}
        ticket["comments"] = [{"id": 1, "body": event("worker.started", "Started", ticket=61,
                               spec=76, session="t1", runner="orca", machine="test", host="codex",
                               model="test", effort="high", grade="senior-worker",
                               worktree=str(self.product), branch="issue-61", base="a"*40)}]
        self.fake.repos["o/r"] = [ticket, issue(76, body="Batch", labels=("mmw:spec",))]
        self.fake.session = ("orca", "t1")
        self.path.write_text(problem().replace("该谁修：o/r", "该谁修：MMW"))
        rc, out, err = self.run_register("add", str(self.path), "--repo", "acme/toolbox",
                                         env={"MMW_TICKET": "61"})
        self.assertEqual(rc, 0, err)
        payload = events.parse(self.fake.repos["acme/toolbox"][-1]["comments"][0]["body"])[1]
        self.assertEqual((payload["seen_in"], payload["ticket"], payload["spec"], payload["session"], payload["actor"]),
                         ("o/r", 61, 76, "orca:t1", "senior-worker"))

    def test_bad_input_and_failed_reads_leave_github_unchanged(self):
        self.path.write_text(problem().replace("证据：tests/test_board.py:193\n", ""))
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 2, err)
        self.assertEqual(self.fake.repos, {"o/r": [], "acme/toolbox": []})
        self.path.write_text(problem())
        self.fake.fail = lambda c: c[1] == "api"
        rc, out, err = self.run_register("add", str(self.path))
        self.assertEqual(rc, 2, err)
        self.assertIn("503", err)
        self.assertEqual(self.fake.repos, {"o/r": [], "acme/toolbox": []})

    def cli_environment(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        store = self.root / "github.json"
        store.write_text(json.dumps({"repos": self.fake.repos, "labels": self.fake.labels}))
        gh = bin_dir / "gh"
        gh.write_text(f"#!{sys.executable}\nimport sys\nsys.path.insert(0, {str(Path(__file__).parent)!r})\n"
                      "from test_register import fake_server\nfake_server()\n")
        gh.chmod(0o755)
        bash = bin_dir / "bash"
        bash.write_text("#!/bin/sh\nif [ \"$2\" = self ]; then exit 2; fi\nexec /bin/bash \"$@\"\n")
        bash.chmod(0o755)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("MMW_", "NMEM_"))}
        env.update(MMW_HOME=str(self.home), PATH=str(bin_dir) + os.pathsep + env["PATH"],
                   FAKE_REGISTER_STORE=str(store))
        return env, store

    def test_the_cli_process_registers_and_finds_against_fake_github(self):
        env, store = self.cli_environment()
        run = REAL_RUN([sys.executable, str(SCRIPT), "add", str(self.path)], cwd=self.product,
                       env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        data = json.loads(store.read_text())
        self.assertEqual(data["repos"]["o/r"][0]["labels"], [{"name": "mmw:lesson"}])
        self.assertEqual(len(events.fold(data["repos"]["o/r"][0]["comments"])["occurrences"]), 1)
        run = REAL_RUN([sys.executable, str(SCRIPT), "find", "空列表"], cwd=self.product,
                       env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("#100\to/r\topen\tmmw:lesson\ttest-compares-empty-lists", run.stdout)

    def test_different_problem_codes_register_while_another_read_is_blocked(self):
        env, store = self.cli_environment()
        gate = self.root / "read-gate"
        first = subprocess.Popen([sys.executable, str(SCRIPT), "add", str(self.path)],
                                 cwd=self.product, env={**env, "FAKE_REGISTER_GATE": str(gate)},
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not gate.exists() and time.monotonic() < deadline:
                if first.poll() is not None:
                    self.fail(first.communicate())
                time.sleep(0.02)
            self.assertTrue(gate.exists(), "the first registration reached its issue read")
            second_path = self.root / "second.md"
            second_path.write_text(problem("different-problem"))
            second = REAL_RUN([sys.executable, str(SCRIPT), "add", str(second_path)],
                              cwd=self.product, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(second.returncode, 0, second.stderr)
        finally:
            gate.with_suffix(".release").touch()
            out, err = first.communicate(timeout=15)
        self.assertEqual(first.returncode, 0, err)
        data = json.loads(store.read_text())
        self.assertEqual(sorted(r["body"].split("问题代号：")[1].splitlines()[0]
                                for r in data["repos"]["o/r"]),
                         ["different-problem", "test-compares-empty-lists"])
        self.assertEqual([len(events.fold(r["comments"])["occurrences"])
                          for r in data["repos"]["o/r"]], [1, 1])


def fake_server():
    path = Path(os.environ["FAKE_REGISTER_STORE"])
    gate = os.environ.get("FAKE_REGISTER_GATE")
    if gate and sys.argv[1] == "api" and "/issues?" in sys.argv[2]:
        gate = Path(gate)
        gate.touch()
        deadline = time.monotonic() + 25
        while not gate.with_suffix(".release").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
    with path.with_suffix(".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text())
        fake = Fake()
        fake.repos, fake.labels = data["repos"], data["labels"]
        result = fake(["gh", *sys.argv[1:]])
        path.write_text(json.dumps({"repos": fake.repos, "labels": fake.labels}))
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    sys.exit(result.returncode)


if __name__ == "__main__":
    unittest.main()
