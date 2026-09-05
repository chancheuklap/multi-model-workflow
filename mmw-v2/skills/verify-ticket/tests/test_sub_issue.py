"""`--sub-issue`: open one needs-triage child of this ticket, or refuse."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests._load import load

vt = load()

KINDS = ("baseline", "outside-owns", "review", "decision", "pipeline")


def run_sub_issue(kind, text):
    """Run --sub-issue; return (exit, stdout, stderr, gh argv list, posted bodies)."""
    recorded = []
    posted_bodies = []

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

    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "body.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt.subprocess, "run", side_effect=fake_run):
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = vt.run_sub_issue(77, kind, path)
    return code, out.getvalue(), err.getvalue(), recorded, posted_bodies


class TestCreatesForEachKind(unittest.TestCase):
    def test_each_kind_fires_gh_issue_create_with_parent_and_label(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                code, out, err, recorded, _ = run_sub_issue(
                    kind, f"The {kind} case\n\nbody of the sub-issue\n")
                self.assertEqual(code, 0, err)
                create = next(c for c in recorded if c[:3] == ["gh", "issue", "create"])
                self.assertIn("--parent", create)
                self.assertEqual(create[create.index("--parent") + 1], "77")
                self.assertIn("--label", create)
                self.assertEqual(create[create.index("--label") + 1], "needs-triage")
                self.assertEqual(create[create.index("--title") + 1], f"The {kind} case")
                self.assertIn("99", out.strip().splitlines()[-1])

    def test_parent_is_the_ticket(self):
        """`--parent` is this ticket; the ticket body is not consulted."""
        code, _, err, recorded, _ = run_sub_issue(
            "baseline", "The handoff and the spec disagree\n\ndetail\n")
        self.assertEqual(code, 0, err)
        create = next(c for c in recorded if c[:3] == ["gh", "issue", "create"])
        self.assertEqual(create[create.index("--parent") + 1], "77")
        self.assertNotIn("118", create)

    def test_the_body_opens_with_the_sub_issue_marker(self):
        code, _, err, recorded, bodies = run_sub_issue(
            "baseline", "The handoff and the spec disagree\n\ndetail\n")
        self.assertEqual(code, 0, err)
        self.assertTrue(any(c[:3] == ["gh", "issue", "create"] for c in recorded))
        posted = bodies[0]
        self.assertEqual(posted.splitlines()[0], "SUB-ISSUE baseline from #77")
        self.assertIn("The handoff and the spec disagree", posted)
        self.assertIn("detail", posted)


class TestRefusesEmptyOrUnknown(unittest.TestCase):
    def test_an_empty_file_exits_2_and_creates_nothing(self):
        code, _, err, recorded, _ = run_sub_issue("baseline", "")
        self.assertEqual(code, 2)
        self.assertTrue(err.strip())
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))

    def test_whitespace_only_is_empty(self):
        code, _, err, recorded, _ = run_sub_issue("review", "  \n\n")
        self.assertEqual(code, 2)
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))

    def test_an_unknown_kind_exits_2_and_creates_nothing(self):
        code, _, err, recorded, _ = run_sub_issue(
            "other", "A title\n\nbody\n")
        self.assertEqual(code, 2)
        self.assertIn("kind", err.lower())
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))

    def test_pipeline_kind_is_accepted_and_a_sixth_name_exits_2(self):
        code, _, err, recorded, _ = run_sub_issue(
            "pipeline", "The driver would not start\n\nran the start; saw the lease refused\n")
        self.assertEqual(code, 0, err)
        self.assertTrue(any(c[:3] == ["gh", "issue", "create"] for c in recorded))
        code, _, err, recorded, _ = run_sub_issue(
            "toolbox", "A title\n\nbody\n")
        self.assertEqual(code, 2)
        self.assertFalse(any(c[:3] == ["gh", "issue", "create"] for c in recorded))


if __name__ == "__main__":
    unittest.main()
