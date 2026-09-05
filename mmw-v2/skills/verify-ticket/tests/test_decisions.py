"""`--decisions`: post the two-section file as a `DECISIONS` comment, or refuse."""

import io
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


def run_decisions(text, comments=(SELF_RUN,)):
    """Run --decisions against a made-up ticket; return (exit, stderr, posted)."""
    posted = []
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "decisions.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
             mock.patch.object(vt, "post_comment",
                               side_effect=lambda n, b: posted.append((n, b))):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_decisions(77, path)
    return code, err.getvalue(), posted


class TestPostsTheComment(unittest.TestCase):
    def test_the_comment_opens_with_decisions(self):
        code, err, posted = run_decisions(TWO_SECTIONS)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0][0], 77)
        self.assertEqual(posted[0][1].splitlines()[0], "DECISIONS")

    def test_the_file_body_follows_the_first_line(self):
        code, err, posted = run_decisions(TWO_SECTIONS)
        self.assertEqual(code, 0, err)
        body = posted[0][1]
        self.assertIn("## Decisions I made on my own", body)
        self.assertIn("picked the existing helper over a new one", body)
        self.assertIn("Outside Owns: None", body)


class TestRefusesWhenTheTicketAlreadyHasOne(unittest.TestCase):
    def test_a_second_decisions_comment_is_refused(self):
        existing = "DECISIONS\n\n## Decisions I made on my own\n\nalready\n\n## Outside Owns\n\nOutside Owns: None\n"
        code, err, posted = run_decisions(TWO_SECTIONS, comments=(SELF_RUN, existing))
        self.assertEqual(code, 2)
        self.assertIn("DECISIONS", err)
        self.assertEqual(posted, [])


class TestRefusesAFileMissingASection(unittest.TestCase):
    def test_no_decisions_section_is_refused(self):
        text = "## Outside Owns\n\nOutside Owns: None\n"
        code, err, posted = run_decisions(text)
        self.assertEqual(code, 2)
        self.assertIn("Decisions I made on my own", err)
        self.assertEqual(posted, [])

    def test_no_outside_owns_section_is_refused(self):
        text = "## Decisions I made on my own\n\npicked one\n"
        code, err, posted = run_decisions(text)
        self.assertEqual(code, 2)
        self.assertIn("Outside Owns", err)
        self.assertEqual(posted, [])

    def test_a_third_section_is_refused(self):
        text = TWO_SECTIONS + "\n## Extra\n\nno\n"
        code, err, posted = run_decisions(text)
        self.assertEqual(code, 2)
        self.assertEqual(posted, [])


class TestOutsideOwnsMustMatchTheSelfRun(unittest.TestCase):
    def test_a_mismatching_line_is_refused(self):
        code, err, posted = run_decisions(TWO_SECTIONS_FILES, comments=(SELF_RUN,))
        self.assertEqual(code, 2)
        self.assertIn("Outside Owns", err)
        self.assertEqual(posted, [])

    def test_the_matching_line_is_posted(self):
        code, err, posted = run_decisions(TWO_SECTIONS_FILES, comments=(SELF_RUN_FILES,))
        self.assertEqual(code, 0, err)
        self.assertEqual(posted[0][1].splitlines()[0], "DECISIONS")
        self.assertIn("Outside Owns: src/helper.py, lib/util.py", posted[0][1])


if __name__ == "__main__":
    unittest.main()
