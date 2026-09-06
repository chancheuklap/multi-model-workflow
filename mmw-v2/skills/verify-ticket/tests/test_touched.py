"""`--touched`: tell open siblings whose `## Owns` covers a file outside this ticket."""

import io
import json
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
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

DECISIONS_NO_AC = """DECISIONS

## Decisions I made on my own

picked the existing helper because it already parsed the file

## Outside Owns

Outside Owns: src/helper.py
src/helper.py was required for the importer
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

SPEC = 200
TICKET = 77


class FakeGh:
    """`gh` by argv: view / api / comment. Git is not used by `--touched`."""

    def __init__(self, comments, children, states=None, parent=SPEC, body=BODY):
        self.comments = {TICKET: list(comments)}
        self.bodies = {TICKET: body}
        self.bodies.update(children)
        self.children = dict(children)
        self.states = states or {n: "OPEN" for n in children}
        self.parent = parent
        self.recorded = []
        self.posted = []

    def run(self, cmd, **kwargs):
        self.recorded.append(list(cmd))
        result = mock.Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        if cmd[:3] == ["gh", "issue", "view"]:
            number = int(cmd[3])
            fields = cmd[cmd.index("--json") + 1] if "--json" in cmd else ""
            if fields == "comments":
                result.stdout = json.dumps(
                    {"comments": [{"body": b} for b in self.comments.get(number, [])]})
            elif fields == "body":
                result.stdout = self.bodies.get(number, "")
            elif fields == "parent":
                result.stdout = json.dumps(
                    {"parent": None if self.parent is None else {"number": self.parent}})
            else:
                result.stdout = json.dumps({
                    "state": self.states.get(number, "OPEN"),
                    "labels": [],
                    "assignees": [],
                    "blockedBy": {"nodes": []},
                })
            return result
        if cmd[:3] == ["gh", "issue", "comment"]:
            number = int(cmd[3])
            path = cmd[cmd.index("--body-file") + 1]
            self.posted.append((number, Path(path).read_text(encoding="utf-8")))
            return result
        if cmd[:2] == ["gh", "api"]:
            joined = " ".join(cmd)
            found = re.search(r"issues/(\d+)/sub_issues", joined)
            spec = int(found.group(1)) if found else 0
            kids = list(self.children) if spec == self.parent else []
            result.stdout = "\n".join(str(n) for n in kids) + ("\n" if kids else "")
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result


def run_touched(comments, children, states=None, parent=SPEC, body=BODY):
    """Run --touched; `children` is `{number: body}` of the spec's sub-issues."""
    fake = FakeGh(comments, children, states=states, parent=parent, body=body)
    printed = io.StringIO()
    err = io.StringIO()
    with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
        with redirect_stdout(printed), redirect_stderr(err):
            code = vt.run_touched(TICKET)
    return code, err.getvalue(), fake.posted, printed.getvalue(), fake.recorded


def sub_issues_target(recorded):
    for cmd in recorded:
        if cmd[:2] == ["gh", "api"]:
            found = re.search(r"issues/(\d+)/sub_issues", " ".join(cmd))
            if found:
                return int(found.group(1))
    return None


class TestPostsOnlyOnCoveringOpenTickets(unittest.TestCase):
    def test_a_covering_glob_gets_the_comment(self):
        code, err, posted, printed, recorded = run_touched(
            (SELF_RUN, DECISIONS, REVIEW),
            {80: SIBLING_COVERS, 81: SIBLING_OTHER},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(sub_issues_target(recorded), SPEC)
        self.assertNotEqual(sub_issues_target(recorded), TICKET)
        self.assertEqual([n for n, _ in posted], [80])
        comment = next(c for c in recorded if c[:3] == ["gh", "issue", "comment"])
        self.assertEqual(comment[3], "80")
        self.assertIn("--body-file", comment)
        self.assertEqual(posted[0][1].splitlines()[0], "TOUCHED BY #77")
        self.assertIn("src/helper.py", posted[0][1])
        self.assertIn("src/helper.py was required for AC1", posted[0][1])
        self.assertIn("reasonable", posted[0][1])
        self.assertIn("80", printed)

    def test_sub_issues_are_queried_on_the_linked_spec_not_the_ticket(self):
        """`## Parent` names #118 first; the tracker parent is the batch."""
        code, err, posted, _, recorded = run_touched(
            (SELF_RUN, DECISIONS, REVIEW),
            {80: SIBLING_COVERS},
            parent=SPEC,
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(posted[0][0], 80)
        self.assertEqual(sub_issues_target(recorded), SPEC)
        self.assertNotEqual(sub_issues_target(recorded), TICKET)
        self.assertNotEqual(sub_issues_target(recorded), 118)

    def test_a_should_not_judgement_is_copied(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW_SHOULD_NOT),
            {80: SIBLING_COVERS},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])
        self.assertIn("should not", posted[0][1])
        self.assertNotIn("reasonable", posted[0][1])

    def test_a_review_that_names_no_line_for_the_file_invents_no_judgement(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW_SILENT),
            {80: SIBLING_COVERS},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])
        self.assertNotIn("reasonable", posted[0][1])
        self.assertNotIn("should not", posted[0][1])

    def test_an_exact_owns_path_is_a_cover(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW), {82: SIBLING_EXACT})
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [82])

    def test_a_closed_sibling_is_skipped(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW),
            {80: SIBLING_COVERS},
            states={80: "CLOSED"},
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(posted, [])


class TestCommentShape(unittest.TestCase):
    def test_no_ac_number_omits_the_empty_line(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS_NO_AC, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        lines = posted[0][1].splitlines()
        self.assertEqual(lines[0], "TOUCHED BY #77")
        self.assertEqual(lines[1], "")
        self.assertEqual(lines[2], "src/helper.py")
        self.assertEqual(lines[3], "src/helper.py was required for the importer")
        self.assertEqual(lines[4], "reasonable")
        self.assertEqual(sum(1 for ln in lines if ln == ""), 1)
        self.assertFalse(any(re.fullmatch(r"AC\d+", line) for line in lines))

    def test_no_decisions_comment_says_so_instead_of_repeating_the_path(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        body = posted[0][1]
        self.assertIn("no DECISIONS comment on #77 yet", body)
        path_lines = [ln for ln in body.splitlines() if ln.strip() == "src/helper.py"]
        self.assertEqual(path_lines, ["src/helper.py"])


class TestRefusesWithoutAReview(unittest.TestCase):
    def test_no_review_comment_exits_2(self):
        code, err, posted, _, recorded = run_touched(
            (SELF_RUN, DECISIONS), {80: SIBLING_COVERS})
        self.assertEqual(code, 2)
        self.assertIn("REVIEW", err)
        self.assertEqual(posted, [])
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))


class TestNonePostsNothing(unittest.TestCase):
    def test_outside_owns_none_posts_nothing_and_exits_0(self):
        code, err, posted, printed, recorded = run_touched(
            (SELF_RUN_NONE, DECISIONS, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        self.assertEqual(posted, [])
        self.assertEqual(printed.strip(), "")
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))


if __name__ == "__main__":
    unittest.main()
