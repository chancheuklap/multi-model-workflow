"""`--decisions`: post the two-section file as a `DECISIONS` comment, or refuse."""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests._load import load

vt = load()

SELF_RUN = """self-run
ALL MET (1)

- [x] AC1: the importer writes six rows
  CHECK: echo ok
  EXPECT: ok
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=2

Outside Owns: None
"""

SELF_RUN_FILES = SELF_RUN.replace(
    "Outside Owns: None", "Outside Owns: src/helper.py, lib/util.py")

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
NO_SELF_RUN = "#{n} carries no self-run comment to check Outside Owns against"


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

    def test_the_file_body_follows_the_first_line(self):
        code, err, posted, _ = run_decisions(TWO_SECTIONS)
        self.assertEqual(code, 0, err)
        body = posted[0][1]
        self.assertIn("## Decisions I made on my own", body)
        self.assertIn("picked the existing helper over a new one", body)
        self.assertIn("Outside Owns: None", body)


class TestRefusesWhenTheTicketAlreadyHasOne(unittest.TestCase):
    def test_a_second_decisions_comment_is_refused(self):
        existing = "DECISIONS\n\n## Decisions I made on my own\n\nalready\n\n## Outside Owns\n\nOutside Owns: None\n"
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


class TestTheThreeRefusalsDiffer(unittest.TestCase):
    def test_already_missing_section_and_no_self_run_are_three_wordings(self):
        already = ALREADY_DECISIONS.format(n=77)
        missing = MISSING_SECTION
        no_run = NO_SELF_RUN.format(n=77)
        self.assertEqual(len({already, missing, no_run}), 3)
        cases = [
            (TWO_SECTIONS, (SELF_RUN, "DECISIONS\n\n## Decisions I made on my own\n\nx\n\n## Outside Owns\n\nOutside Owns: None\n"), already),
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
        self.assertIn("does not match the newest self-run", err)
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


if __name__ == "__main__":
    unittest.main()
