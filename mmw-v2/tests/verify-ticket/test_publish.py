"""`--publish`: the one command `to-spec` and `to-tickets` both use to publish to the
tracker — a spec (`--spec-body`/`--title`[/`--map`]) or a batch of ticket drafts
(`--drafts`) — so building the label, native-parent and blocking-link plumbing by hand
is never something an agent has to run the `gh` calls for itself.
"""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import load

vt = load()


def created(number, url="https://github.com/o/r"):
    """A `gh_issue_create` return value for a clean create of issue `number`."""
    return mock.Mock(returncode=0, stdout=f"{url}/issues/{number}\n", stderr=""), number


def failed_create(stderr="gh: something went wrong"):
    return mock.Mock(returncode=1, stdout="", stderr=stderr), None


def no_number_create():
    return mock.Mock(returncode=0, stdout="ok, but no url\n", stderr=""), None


class TestPublishSpec(unittest.TestCase):
    def publish(self, body="A spec.\n", title="A spec", map_number=None,
               create=None, parent=None):
        create = create if create is not None else created(50)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.md"
            path.write_text(body, encoding="utf-8")
            with mock.patch.object(vt, "ensure_label", return_value=None) as label, \
                 mock.patch.object(vt, "gh_issue_create", return_value=create) as gh, \
                 mock.patch.object(vt, "fetch_parent", return_value=parent):
                with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                    code = vt.run_publish_spec(path, title, map_number)
        return code, out.getvalue(), err.getvalue(), label, gh

    def test_publishes_and_prints_the_number(self):
        code, out, err, label, gh = self.publish()
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "50")
        label.assert_called_once_with(vt.CLASS_SPEC)
        args, body = gh.call_args.args
        self.assertEqual(args[:4], ["--title", "A spec", "--label", "mmw:spec"])
        self.assertNotIn("--parent", args)
        self.assertEqual(body, "A spec.\n")

    def test_an_empty_body_is_refused(self):
        code, out, err, label, gh = self.publish(body="")
        self.assertEqual(code, 2)
        self.assertIn("is empty", err)
        gh.assert_not_called()

    def test_a_missing_label_that_cannot_be_created_is_refused(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.md"
            path.write_text("A spec.\n", encoding="utf-8")
            with mock.patch.object(vt, "ensure_label", return_value="permission denied"), \
                 mock.patch.object(vt, "gh_issue_create") as gh:
                with redirect_stderr(io.StringIO()) as err:
                    code = vt.run_publish_spec(path, "A spec", None)
        self.assertEqual(code, 2)
        self.assertIn("permission denied", err.getvalue())
        gh.assert_not_called()

    def test_a_confirmed_map_parent_is_a_clean_exit(self):
        code, out, err, _, gh = self.publish(map_number=18, parent=18)
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "50")
        args, _ = gh.call_args.args
        self.assertIn("--parent", args)
        self.assertEqual(args[args.index("--parent") + 1], "18")

    def test_a_mismatched_native_parent_is_reported_not_silent(self):
        code, out, err, _, _ = self.publish(map_number=18, parent=None)
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "50")
        self.assertIn("not #18", err)
        self.assertIn("do not replace the native parent", err)

    def test_a_gh_failure_is_refused(self):
        code, out, err, _, _ = self.publish(create=failed_create("gh: no such label"))
        self.assertEqual(code, 2)
        self.assertIn("no such label", err)

    def test_no_issue_number_printed_is_refused(self):
        code, out, err, _, _ = self.publish(create=no_number_create())
        self.assertEqual(code, 2)
        self.assertIn("printed no issue number", err)


def write_draft(directory, name, title, labels, blocked_by, body="Do the thing.\n"):
    (Path(directory) / f"{name}.md").write_text(
        f"TITLE: {title}\nLABELS: {labels}\nBLOCKED BY: {blocked_by}\n---\n{body}\n",
        encoding="utf-8")


class TestPublishDrafts(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def draft(self, name, title, labels="mmw:ticket", blocked_by="(none)", **kwargs):
        write_draft(self.dir, name, title, labels, blocked_by, **kwargs)

    def test_an_empty_directory_is_refused(self):
        with redirect_stderr(io.StringIO()) as err:
            code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 2)
        self.assertIn("nothing to publish", err.getvalue())

    def test_an_unknown_blocker_is_refused_before_anything_is_created(self):
        self.draft("a", "A", blocked_by="not-a-draft")
        with mock.patch.object(vt, "gh_issue_create") as create:
            with redirect_stderr(io.StringIO()) as err:
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 2)
        self.assertIn("neither a draft", err.getvalue())
        create.assert_not_called()

    def test_a_cycle_is_refused_before_anything_is_created(self):
        self.draft("a", "A", blocked_by="b")
        self.draft("b", "B", blocked_by="a")
        with mock.patch.object(vt, "gh_issue_create") as create:
            with redirect_stderr(io.StringIO()) as err:
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 2)
        self.assertIn("cycle", err.getvalue())
        create.assert_not_called()

    def test_the_blocker_is_created_before_what_it_blocks(self):
        self.draft("a", "A")
        self.draft("b", "B", blocked_by="a")
        titles = []

        def fake_create(args, body):
            titles.append(args[args.index("--title") + 1])
            return created(100 + len(titles))

        with mock.patch.object(vt, "ensure_label", return_value=None), \
             mock.patch.object(vt, "gh_issue_create", side_effect=fake_create), \
             mock.patch.object(vt, "add_blocking_link", return_value=None) as link, \
             mock.patch.object(vt, "lint_spec", return_value=0) as lint:
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual(titles, ["A", "B"])
        link.assert_called_once_with(102, 101)
        lint.assert_called_once_with(76)
        self.assertIn("a -> #101", out.getvalue())
        self.assertIn("b -> #102", out.getvalue())

    def test_an_issue_number_blocker_is_linked_without_being_created(self):
        self.draft("a", "A", blocked_by="#40")
        with mock.patch.object(vt, "ensure_label", return_value=None), \
             mock.patch.object(vt, "gh_issue_create", return_value=created(101)), \
             mock.patch.object(vt, "add_blocking_link", return_value=None) as link, \
             mock.patch.object(vt, "lint_spec", return_value=0):
            with redirect_stdout(io.StringIO()):
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 0)
        link.assert_called_once_with(101, 40)

    def test_a_failed_create_names_what_already_published(self):
        self.draft("a", "A")
        self.draft("b", "B")
        calls = {"n": 0}

        def fake_create(args, body):
            calls["n"] += 1
            if calls["n"] == 1:
                return created(101)
            return failed_create("gh: rate limited")

        with mock.patch.object(vt, "ensure_label", return_value=None), \
             mock.patch.object(vt, "gh_issue_create", side_effect=fake_create):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 2)
        self.assertIn("rate limited", err.getvalue())
        self.assertIn("a -> #101", err.getvalue())

    def test_a_missing_label_that_cannot_be_created_stops_before_that_draft(self):
        self.draft("a", "A")
        with mock.patch.object(vt, "ensure_label", return_value="permission denied"), \
             mock.patch.object(vt, "gh_issue_create") as create:
            with redirect_stderr(io.StringIO()) as err:
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 2)
        self.assertIn("permission denied", err.getvalue())
        create.assert_not_called()

    def test_a_link_that_cannot_be_recorded_fails_the_run_but_keeps_the_issues(self):
        self.draft("a", "A")
        self.draft("b", "B", blocked_by="a")
        counter = {"n": 100}

        def fake_create(args, body):
            counter["n"] += 1
            return created(counter["n"])

        with mock.patch.object(vt, "ensure_label", return_value=None), \
             mock.patch.object(vt, "gh_issue_create", side_effect=fake_create), \
             mock.patch.object(vt, "add_blocking_link", return_value="gh: not found"), \
             mock.patch.object(vt, "lint_spec", return_value=0):
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 1)
        self.assertIn("could not be linked", err.getvalue())
        self.assertIn("a -> #101", out.getvalue())
        self.assertIn("b -> #102", out.getvalue())

    def test_lint_on_the_published_spec_decides_the_final_exit(self):
        self.draft("a", "A")
        with mock.patch.object(vt, "ensure_label", return_value=None), \
             mock.patch.object(vt, "gh_issue_create", return_value=created(101)), \
             mock.patch.object(vt, "add_blocking_link", return_value=None), \
             mock.patch.object(vt, "lint_spec", return_value=1) as lint:
            code = vt.run_publish_drafts(76, self.dir)
        self.assertEqual(code, 1)
        lint.assert_called_once_with(76)


class TestGhIssueCreate(unittest.TestCase):
    def test_the_number_is_parsed_from_the_printed_url(self):
        result = mock.Mock(returncode=0, stdout="https://github.com/o/r/issues/77\n", stderr="")
        with mock.patch.object(vt.subprocess, "run", return_value=result) as run:
            out, number = vt.gh_issue_create(["--title", "x"], "body text")
        self.assertEqual(number, 77)
        self.assertEqual(out, result)
        args = run.call_args.args[0]
        self.assertEqual(args[:3], ["gh", "issue", "create"])
        self.assertIn("--title", args)
        self.assertIn("--body-file", args)

    def test_no_url_is_no_number(self):
        result = mock.Mock(returncode=0, stdout="done\n", stderr="")
        with mock.patch.object(vt.subprocess, "run", return_value=result):
            _, number = vt.gh_issue_create([], "body")
        self.assertIsNone(number)


class TestIssueDbId(unittest.TestCase):
    def test_reads_the_numeric_id(self):
        result = mock.Mock(returncode=0, stdout="123456\n", stderr="")
        with mock.patch.object(vt.subprocess, "run", return_value=result) as run:
            self.assertEqual(vt.issue_db_id(40), 123456)
        args = run.call_args.args[0]
        self.assertIn("repos/{owner}/{repo}/issues/40", args)

    def test_a_failed_call_raises_a_tracker_read_error(self):
        result = mock.Mock(returncode=1, stdout="", stderr="gh: not found\n")
        with mock.patch.object(vt.subprocess, "run", return_value=result):
            with self.assertRaises(vt.TrackerReadError) as caught:
                vt.issue_db_id(40)
        self.assertIn("not found", str(caught.exception))


class TestAddBlockingLink(unittest.TestCase):
    def test_posts_the_dependency_with_the_blockers_database_id(self):
        api_result = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(vt, "issue_db_id", return_value=555), \
             mock.patch.object(vt.subprocess, "run", return_value=api_result) as run:
            problem = vt.add_blocking_link(child=10, blocker=5)
        self.assertIsNone(problem)
        args = run.call_args.args[0]
        self.assertIn("--method", args)
        self.assertIn("POST", args)
        self.assertIn("repos/{owner}/{repo}/issues/10/dependencies/blocked_by", args)
        self.assertIn("issue_id=555", args)

    def test_a_blocker_whose_id_cannot_be_read_is_a_problem(self):
        with mock.patch.object(vt, "issue_db_id",
                               side_effect=vt.TrackerReadError(5, "database id", "not found")):
            problem = vt.add_blocking_link(child=10, blocker=5)
        self.assertIn("not found", problem)

    def test_a_failed_post_is_a_problem(self):
        api_result = mock.Mock(returncode=1, stdout="", stderr="gh: already linked\n")
        with mock.patch.object(vt, "issue_db_id", return_value=555), \
             mock.patch.object(vt.subprocess, "run", return_value=api_result):
            problem = vt.add_blocking_link(child=10, blocker=5)
        self.assertIn("already linked", problem)


class TestLabelDefined(unittest.TestCase):
    def test_every_set_is_recognised(self):
        for name in ("mmw:ticket", "ready-for-agent", "junior-worker"):
            with self.subTest(name=name):
                self.assertTrue(vt.label_defined(name))

    def test_an_unknown_label_is_not(self):
        self.assertFalse(vt.label_defined("bug"))


if __name__ == "__main__":
    unittest.main()
