import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import load

vt = load()

KINDS = ("finding", "contract", "deferred", "decision", "fault")


def run_sub_issue(kind, text, label_problem=None):
    """Run --sub-issue; return (exit, stdout, stderr, gh argv list, posted bodies).

    `label_problem` is what `ensure_label` answers: None when the repository has the
    label or it was created, a reason when it could not be created.
    """
    recorded = []
    posted_bodies = []
    labels_asked = []

    def fake_run(cmd, **kwargs):
        recorded.append(list(cmd))
        if "--body-file" in cmd:
            posted_bodies.append(Path(cmd[cmd.index("--body-file") + 1]).read_text(
                encoding="utf-8"))
        result = mock.Mock()
        result.returncode = 0
        result.stdout = "https://github.com/chancheuklap/multi-model-workflow/issues/99\n"
        result.stderr = ""
        return result

    def fake_label(name):
        labels_asked.append(name)
        return label_problem

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "body.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt.subprocess, "run", side_effect=fake_run), \
             mock.patch.object(vt, "ensure_label", side_effect=fake_label):
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = vt.run_sub_issue(77, kind, path)
    run_sub_issue.labels_asked = labels_asked
    return code, out.getvalue(), err.getvalue(), recorded, posted_bodies


def create_of(recorded):
    return next(c for c in recorded if c[:3] == ["gh", "issue", "create"])


def labels_of(create):
    return [create[i + 1] for i, a in enumerate(create) if a == "--label"]


class TestCreatesForEachKind(unittest.TestCase):
    def test_title_limit_keeps_full_body_and_records_the_created_title(self):
        for first_line, expected in (
            ("界🧪" * 200, "界🧪" * 127 + "界…"),
            ("界🧪" * 128 + "尾", "界🧪" * 127 + "界…"),
            ("界🧪" * 128, "界🧪" * 128),
            ("A short title", "A short title"),
        ):
            with self.subTest(length=len(first_line)):
                text = first_line + "\n\nFull details stay here.\n"
                code, _, err, recorded, bodies = run_sub_issue("finding", text)
                self.assertEqual(code, 0, err)
                create = create_of(recorded)
                title = create[create.index("--title") + 1]
                self.assertEqual(title, expected)
                self.assertLessEqual(len(title), 256)
                self.assertEqual(bodies[0], "A `finding` child of #77.\n\n" + text)
                what, payload = vt.events.parse(bodies[-1])
                self.assertEqual((what, payload["event"], payload["title"]),
                                 ("event", "child.opened", title))

    def test_each_kind_fires_gh_issue_create_with_parent_and_labels(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                code, out, err, recorded, _ = run_sub_issue(
                    kind, f"The {kind} case\n\nbody of the sub-issue\n")
                self.assertEqual(code, 0, err)
                create = create_of(recorded)
                self.assertEqual(create[create.index("--parent") + 1], "77")
                self.assertEqual(create.count("--parent"), 1)
                self.assertEqual(create[create.index("--title") + 1], f"The {kind} case")
                self.assertIn("99", out.strip().splitlines()[-1])

    def test_a_finding_child_is_born_with_only_its_kind(self):
        code, _, err, recorded, _ = run_sub_issue("finding", "A finding\n\nbody\n")
        self.assertEqual(code, 0, err)
        self.assertCountEqual(labels_of(create_of(recorded)), ["mmw:child"])

    def test_a_contract_child_is_born_with_only_its_kind(self):
        code, _, err, recorded, _ = run_sub_issue("contract", "A contract\n\nbody\n")
        self.assertEqual(code, 0, err)
        self.assertCountEqual(labels_of(create_of(recorded)), ["mmw:child"])

    def test_a_fault_child_is_born_with_only_its_kind(self):
        code, _, err, recorded, _ = run_sub_issue("fault", "A fault\n\nbody\n")
        self.assertEqual(code, 0, err)
        self.assertCountEqual(labels_of(create_of(recorded)), ["mmw:child"])

    def test_a_decision_child_is_born_awaiting_the_owner(self):
        code, _, err, recorded, _ = run_sub_issue("decision", "A decision\n\nbody\n")
        self.assertEqual(code, 0, err)
        self.assertCountEqual(labels_of(create_of(recorded)), ["mmw:child", "needs-triage"])

    def test_a_deferred_child_is_born_awaiting_the_owner(self):
        code, _, err, recorded, _ = run_sub_issue("deferred", "A deferred\n\nbody\n")
        self.assertEqual(code, 0, err)
        self.assertCountEqual(labels_of(create_of(recorded)), ["mmw:child", "needs-triage"])

    def test_the_body_opens_with_a_line_naming_the_kind_and_the_ticket(self):
        code, _, err, recorded, bodies = run_sub_issue(
            "contract", "The handoff and the spec disagree\n\ndetail\n")
        self.assertEqual(code, 0, err)
        self.assertTrue(any(c[:3] == ["gh", "issue", "create"] for c in recorded))
        posted = bodies[0]
        self.assertIn("contract", posted.splitlines()[0])
        self.assertIn("#77", posted.splitlines()[0])
        self.assertNotIn("SUB-ISSUE", posted)
        self.assertIn("The handoff and the spec disagree", posted)
        self.assertIn("detail", posted)


class TestTheKindLabel(unittest.TestCase):
    def test_both_labels_are_made_sure_of_before_anything_is_opened(self):
        code, _, err, recorded, _ = run_sub_issue("decision", "A decision\n\nbody\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(run_sub_issue.labels_asked, ["needs-triage", "mmw:child"])
        self.assertEqual(sorted(labels_of(create_of(recorded))), ["mmw:child", "needs-triage"])

    def test_a_label_that_cannot_be_created_refuses_and_opens_nothing(self):
        code, _, err, recorded, bodies = run_sub_issue(
            "finding", "A finding\n\nbody\n", label_problem="HTTP 403: not allowed")
        self.assertEqual(code, 2)
        self.assertIn("mmw:child", err)
        self.assertIn("HTTP 403", err)
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))
        self.assertEqual(bodies, [])

    def test_ensure_label_leaves_an_existing_label_alone(self):
        def fake_run(cmd, **kwargs):
            return mock.Mock(returncode=1, stdout="",
                             stderr='label with name "mmw:child" already exists; use `--force`')
        with mock.patch.object(vt.subprocess, "run", side_effect=fake_run) as run:
            self.assertIsNone(load().ensure_label("mmw:child"))
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:4], ["gh", "label", "create", "mmw:child"])
        self.assertNotIn("--force", cmd)

    def test_ensure_label_names_any_other_failure(self):
        def fake_run(cmd, **kwargs):
            return mock.Mock(returncode=1, stdout="", stderr="HTTP 403: Resource not accessible")
        with mock.patch.object(vt.subprocess, "run", side_effect=fake_run):
            self.assertEqual(load().ensure_label("mmw:child"),
                             "HTTP 403: Resource not accessible")


class TestRecordsTheChildOnTheTicket(unittest.TestCase):
    """The ticket's own events are where its children are found."""

    def test_child_opened_is_posted_on_the_ticket_with_the_new_number_and_kind(self):
        code, _, err, recorded, bodies = run_sub_issue(
            "finding", "RUNNER is now a Path\n\nthe finding\n")
        self.assertEqual(code, 0, err)
        comment = next(c for c in recorded if c[:3] == ["gh", "issue", "comment"])
        self.assertEqual(comment[3], "77")
        what, payload = vt.events.parse(bodies[-1])
        self.assertEqual((what, payload["event"], payload["child"], payload["kind"],
                          payload["title"], payload["ticket"]),
                         ("event", "child.opened", 99, "finding", "RUNNER is now a Path", 77))

    def test_a_child_whose_event_could_not_be_written_exits_1_and_says_not_to_open_it_again(self):
        def fake_run(cmd, **kwargs):
            result = mock.Mock(returncode=0, stderr="",
                               stdout="https://github.com/o/r/issues/99\n")
            if cmd[:3] == ["gh", "issue", "comment"]:
                raise vt.subprocess.CalledProcessError(1, cmd)
            return result

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "body.md"
            path.write_text("A title\n\nbody\n", encoding="utf-8")
            with mock.patch.object(vt.subprocess, "run", side_effect=fake_run), \
                 mock.patch.object(vt, "ensure_label", return_value=None):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                    code = vt.run_sub_issue(77, "decision", path)
        self.assertEqual(code, 1)
        self.assertIn("99", err.getvalue())


class TestRefusesEmptyOrUnknown(unittest.TestCase):
    def test_an_empty_file_exits_2_and_creates_nothing(self):
        code, _, err, recorded, _ = run_sub_issue("contract", "")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))

    def test_whitespace_only_is_empty(self):
        code, _, err, recorded, _ = run_sub_issue("finding", "  \n\n")
        self.assertEqual(code, 2)
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))

    def test_the_retired_kind_names_are_refused(self):
        for kind in ("review", "baseline", "outside-owns", "pipeline"):
            with self.subTest(kind=kind):
                code, _, err, recorded, _ = run_sub_issue(
                    kind, "A title\n\nbody\n")
                self.assertEqual(code, 2)
                self.assertIn("finding, contract, deferred, decision, fault", err)
                self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))


if __name__ == "__main__":
    unittest.main()
