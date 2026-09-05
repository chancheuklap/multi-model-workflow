"""`--touched`: tell open siblings whose `## Owns` covers a file outside this ticket."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from tests._load import load

vt = load()

BODY = "## Parent\n\n#118, Implementation Decisions section 11\n"

SELF_RUN = """self-run
ALL MET (1)

- [x] AC1: the importer writes six rows
  CHECK: echo ok
  EXPECT: ok
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=2

Outside Owns: src/helper.py
"""

SELF_RUN_NONE = SELF_RUN.replace("Outside Owns: src/helper.py", "Outside Owns: None")

DECISIONS = """DECISIONS

## Decisions I made on my own

picked the existing helper

## Outside Owns

Outside Owns: src/helper.py
src/helper.py was required for AC1
"""

REVIEW = """REVIEW abcdef0..1234567

## Standards

None

## Spec

### Decisions

- `src/helper.py`: reasonable — the ticket left the helper unnamed
- picked the existing helper: reasonable — the spec names no helper

## Tests

None
"""

REVIEW_SHOULD_NOT = """REVIEW abcdef0..1234567

## Spec

### Decisions

- `src/helper.py`: should not — it goes against this ticket's ## Owns

## Tests

None
"""

REVIEW_SILENT = """REVIEW abcdef0..1234567

## Spec

### Decisions

- picked the existing helper: reasonable — the spec names no helper

## Tests

None
"""

SIBLING_COVERS = "## Owns\n\n- src/**\n"
SIBLING_OTHER = "## Owns\n\n- lib/**\n"
SIBLING_EXACT = "## Owns\n\n- src/helper.py\n"


def run_touched(comments, children, states=None):
    """Run --touched; `children` is `{number: body}` of the spec's sub-issues."""
    posted = []
    printed = io.StringIO()
    err = io.StringIO()
    states = states or {n: "OPEN" for n in children}

    def fake_ticket(n):
        return {"state": states.get(n, "OPEN"), "labels": [], "assignees": []}

    def fake_body(n):
        if n == 77:
            return BODY
        return children[n]

    with mock.patch.object(vt, "fetch_body", side_effect=fake_body), \
         mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
         mock.patch.object(vt, "fetch_sub_issues", return_value=list(children)), \
         mock.patch.object(vt, "fetch_ticket", side_effect=fake_ticket), \
         mock.patch.object(vt, "post_comment",
                           side_effect=lambda n, b: posted.append((n, b))):
        with redirect_stdout(printed), redirect_stderr(err):
            code = vt.run_touched(77)
    return code, err.getvalue(), posted, printed.getvalue()


class TestPostsOnlyOnCoveringOpenTickets(unittest.TestCase):
    def test_a_covering_glob_gets_the_comment(self):
        code, err, posted, printed = run_touched(
            (SELF_RUN, DECISIONS, REVIEW),
            {80: SIBLING_COVERS, 81: SIBLING_OTHER},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])
        self.assertEqual(posted[0][1].splitlines()[0], "TOUCHED BY #77")
        self.assertIn("src/helper.py", posted[0][1])
        self.assertIn("src/helper.py was required for AC1", posted[0][1])
        self.assertIn("reasonable", posted[0][1])
        self.assertIn("80", printed)

    def test_a_should_not_judgement_is_copied(self):
        code, err, posted, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW_SHOULD_NOT),
            {80: SIBLING_COVERS},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])
        self.assertIn("should not", posted[0][1])
        self.assertNotIn("reasonable", posted[0][1])

    def test_a_review_that_names_no_line_for_the_file_invents_no_judgement(self):
        code, err, posted, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW_SILENT),
            {80: SIBLING_COVERS},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])
        self.assertNotIn("reasonable", posted[0][1])
        self.assertNotIn("should not", posted[0][1])

    def test_an_exact_owns_path_is_a_cover(self):
        code, err, posted, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW), {82: SIBLING_EXACT})
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [82])

    def test_a_closed_sibling_is_skipped(self):
        code, err, posted, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW),
            {80: SIBLING_COVERS},
            states={80: "CLOSED"},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(posted, [])


class TestRefusesWithoutAReview(unittest.TestCase):
    def test_no_review_comment_exits_2(self):
        code, err, posted, _ = run_touched(
            (SELF_RUN, DECISIONS), {80: SIBLING_COVERS})
        self.assertEqual(code, 2)
        self.assertIn("REVIEW", err)
        self.assertEqual(posted, [])


class TestNonePostsNothing(unittest.TestCase):
    def test_outside_owns_none_posts_nothing_and_exits_0(self):
        code, err, posted, printed = run_touched(
            (SELF_RUN_NONE, DECISIONS, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        self.assertEqual(posted, [])
        self.assertEqual(printed.strip(), "")


if __name__ == "__main__":
    unittest.main()
