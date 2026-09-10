"""`--decisions`: post the two-section file as a `DECISIONS` comment, or refuse."""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import checked, event, load

vt = load()

LEDGER = """- [x] AC1: the importer writes six rows
  CHECK: echo ok
  EXPECT: ok
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=2"""

SELF_RUN = checked("self", LEDGER, "ALL MET (1 met)", outside_owns=[])

SELF_RUN_FILES = checked("self", LEDGER, "ALL MET (1 met)",
                         outside_owns=["src/helper.py", "lib/util.py"])

SELF_RUN_UNCHECKED = checked("self", LEDGER, "ALL MET (1 met)",
                             outside_owns_unchecked="main")

# The old run comment, typed by hand: its first line is `self-run`, and it carries no
# event, so nothing reads it as a run.
TYPED_SELF_RUN = "self-run\nALL MET (1)\n\n" + LEDGER + "\n\nOutside Owns: None\n"

TWO_SECTIONS = """## Decisions I made on my own

picked the existing helper over a new one

## Outside Owns

Outside Owns: None
"""

TWO_SECTIONS_FILES = TWO_SECTIONS.replace(
    "Outside Owns: None",
    "Outside Owns: src/helper.py, lib/util.py\n"
    "src/helper.py was required for AC1\n"
    "lib/util.py was required for AC1")

ALREADY_DECISIONS = (
    "#{n} already carries a DECISIONS comment"
)
MISSING_SECTION = "the file is missing section `Decisions I made on my own`"
NO_SELF_RUN = ("#{n} carries no ticket.checked of your own run to check "
               "Outside Owns against")


class FakeGh:
    def __init__(self, comments=()):
        self.comments = list(comments)
        self.recorded = []
        self.posted = []

    def run(self, cmd, **kwargs):
        self.recorded.append(list(cmd))
        result = mock.Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        if cmd[:3] == ["gh", "issue", "view"]:
            fields = cmd[cmd.index("--json") + 1] if "--json" in cmd else ""
            if fields == "comments":
                result.stdout = json.dumps(
                    {"comments": [{"body": b} for b in self.comments]})
            return result
        if cmd[:3] == ["gh", "issue", "comment"]:
            number = int(cmd[3])
            path = cmd[cmd.index("--body-file") + 1]
            self.posted.append((number, Path(path).read_text(encoding="utf-8")))
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result


def run_decisions(text, comments=(SELF_RUN,)):
    """Run --decisions against a made-up ticket; return (exit, stderr, posted, recorded)."""
    fake = FakeGh(comments)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "decisions.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_decisions(77, path)
    return code, err.getvalue(), fake.posted, fake.recorded


class TestPostsTheComment(unittest.TestCase):
    def test_the_comment_opens_with_decisions(self):
        code, err, posted, recorded = run_decisions(TWO_SECTIONS)
        self.assertEqual(code, 0, err)
        comment = next(c for c in recorded if c[:3] == ["gh", "issue", "comment"])
        self.assertEqual(comment[3], "77")
        self.assertIn("--body-file", comment)
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0][0], 77)
        self.assertEqual(posted[0][1].splitlines()[0], "DECISIONS")
        what, payload = vt.events.parse(posted[0][1])
        self.assertEqual((what, payload["event"], payload["ticket"]),
                         ("event", "worker.decided", 77))

    def test_the_file_body_follows_the_first_line(self):
        code, err, posted, _ = run_decisions(TWO_SECTIONS)
        self.assertEqual(code, 0, err)
        body = posted[0][1]
        self.assertIn("## Decisions I made on my own", body)
        self.assertIn("picked the existing helper over a new one", body)
        self.assertIn("Outside Owns: None", body)


class TestRefusesWhenTheTicketAlreadyHasOne(unittest.TestCase):
    def test_a_second_decisions_comment_is_refused(self):
        existing = event("worker.decided", "DECISIONS\n\n## Decisions I made on my own\n\nalready\n\n## Outside Owns\n\nOutside Owns: None\n")
        code, err, posted, recorded = run_decisions(
            TWO_SECTIONS, comments=(SELF_RUN, existing))
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), ALREADY_DECISIONS.format(n=77))
        self.assertEqual(posted, [])
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))


class TestRefusesAFileMissingASection(unittest.TestCase):
    def test_no_decisions_section_is_refused(self):
        text = "## Outside Owns\n\nOutside Owns: None\n"
        code, err, posted, recorded = run_decisions(text)
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), MISSING_SECTION)
        self.assertEqual(posted, [])
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))

    def test_no_outside_owns_section_is_refused(self):
        text = "## Decisions I made on my own\n\npicked one\n"
        code, err, posted, _ = run_decisions(text)
        self.assertEqual(code, 2)
        self.assertIn("Outside Owns", err)
        self.assertEqual(posted, [])

    def test_a_third_section_is_refused(self):
        text = TWO_SECTIONS + "\n## Extra\n\nno\n"
        code, err, posted, _ = run_decisions(text)
        self.assertEqual(code, 2)
        self.assertIn("Extra", err)
        self.assertEqual(posted, [])


class TestRefusesWithoutASelfRun(unittest.TestCase):
    def test_no_self_run_comment_is_refused(self):
        code, err, posted, recorded = run_decisions(TWO_SECTIONS, comments=())
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), NO_SELF_RUN.format(n=77))
        self.assertEqual(posted, [])
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))

    def test_a_typed_self_run_comment_is_not_a_run(self):
        """A comment whose first line is `self-run` and that carries no event is prose:
        the worker still has no run of its own to check the file against."""
        code, err, posted, _ = run_decisions(TWO_SECTIONS, comments=(TYPED_SELF_RUN,))
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), NO_SELF_RUN.format(n=77))
        self.assertEqual(posted, [])

    def test_a_reverify_is_not_the_workers_own_run(self):
        """The verifier's run says nothing about what the worker wrote outside `## Owns`."""
        reverify = checked("reverify", LEDGER, "ALL MET (1 met)")
        code, err, posted, _ = run_decisions(TWO_SECTIONS, comments=(reverify,))
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), NO_SELF_RUN.format(n=77))
        self.assertEqual(posted, [])


class TestTheThreeRefusalsDiffer(unittest.TestCase):
    def test_already_missing_section_and_no_self_run_are_three_wordings(self):
        already = ALREADY_DECISIONS.format(n=77)
        missing = MISSING_SECTION
        no_run = NO_SELF_RUN.format(n=77)
        self.assertEqual(len({already, missing, no_run}), 3)
        cases = [
            (TWO_SECTIONS, (SELF_RUN, event("worker.decided", "DECISIONS\n\n## Decisions I made on my own\n\nx\n\n## Outside Owns\n\nOutside Owns: None\n")), already),
            ("## Outside Owns\n\nOutside Owns: None\n", (SELF_RUN,), missing),
            (TWO_SECTIONS, (), no_run),
        ]
        seen = []
        for text, comments, want in cases:
            code, err, posted, _ = run_decisions(text, comments=comments)
            self.assertEqual(code, 2)
            self.assertEqual(err.strip(), want)
            self.assertEqual(posted, [])
            seen.append(err.strip())
        self.assertEqual(len(set(seen)), 3)


class TestOutsideOwnsMustMatchTheSelfRun(unittest.TestCase):
    def test_a_mismatching_line_is_refused(self):
        code, err, posted, recorded = run_decisions(TWO_SECTIONS_FILES, comments=(SELF_RUN,))
        self.assertEqual(code, 2)
        self.assertIn("does not match your newest run", err)
        self.assertIn("`Outside Owns: None`", err)
        self.assertNotIn("missing section", err)
        self.assertEqual(posted, [])
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))

    def test_the_matching_line_is_posted(self):
        code, err, posted, recorded = run_decisions(
            TWO_SECTIONS_FILES, comments=(SELF_RUN_FILES,))
        self.assertEqual(code, 0, err)
        comment = next(c for c in recorded if c[:3] == ["gh", "issue", "comment"])
        self.assertEqual(comment[3], "77")
        self.assertEqual(posted[0][1].splitlines()[0], "DECISIONS")
        self.assertIn("Outside Owns: src/helper.py, lib/util.py", posted[0][1])

    def test_the_newest_self_run_is_the_one_compared(self):
        code, err, posted, _ = run_decisions(
            TWO_SECTIONS_FILES, comments=(SELF_RUN_FILES, SELF_RUN))
        self.assertEqual(code, 2)
        self.assertIn("does not match your newest run", err)
        self.assertEqual(posted, [])

    def test_a_run_off_its_own_branch_is_matched_by_the_same_words(self):
        text = TWO_SECTIONS.replace(
            "Outside Owns: None",
            "Outside Owns: not checked on main, which carries more than this ticket")
        code, err, posted, _ = run_decisions(text, comments=(SELF_RUN_UNCHECKED,))
        self.assertEqual(code, 0, err)
        self.assertEqual(len(posted), 1)


if __name__ == "__main__":
    unittest.main()
