"""`--touched`: tell open siblings whose `## Owns` covers a file outside this ticket."""

import io
import json
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import checked, event, load

vt = load()

BODY = "## Parent\n\n#118, Implementation Decisions section 11\n"

LEDGER = """- [x] AC1: the importer writes six rows
  CHECK: echo ok
  EXPECT: ok
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=2"""

SELF_RUN = checked("self", LEDGER, "ALL MET (1 met)", outside_owns=["src/helper.py"])
SELF_RUN_NONE = checked("self", LEDGER, "ALL MET (1 met)", outside_owns=[])
SELF_RUN_TWO = checked("self", LEDGER, "ALL MET (1 met)",
                       outside_owns=["src/helper.py", "src/parse.py"])

# The old run comment, typed by hand: it carries no event, so it is not a run.
TYPED_SELF_RUN = ("self-run\nALL MET (1)\n\n" + LEDGER
                  + "\n\nOutside Owns: src/helper.py\n")

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

# The same reports as the scripts post them: each one an event.
DECISIONS, DECISIONS_NO_AC = (event("worker.decided", t) for t in (DECISIONS, DECISIONS_NO_AC))
REVIEW, REVIEW_SHOULD_NOT, REVIEW_SILENT = (
    event("reviewer.reported", t, base="abcdef0", head="1234567")
    for t in (REVIEW, REVIEW_SHOULD_NOT, REVIEW_SILENT))

SIBLING_COVERS = "## Owns\n\n- src/**\n"
SIBLING_OTHER = "## Owns\n\n- lib/**\n"
SIBLING_EXACT = "## Owns\n\n- src/helper.py\n"

SPEC = 200
TICKET = 77


class FakeGh:
    """`gh` by argv: view / api / comment. Git is not used by `--touched`."""

    def __init__(self, comments, children, states=None, parent=SPEC, body=BODY,
                 api_fails=False):
        self.comments = {TICKET: list(comments)}
        self.bodies = {TICKET: body}
        self.bodies.update(children)
        self.children = dict(children)
        self.states = states or {n: "OPEN" for n in children}
        self.parent = parent
        self.api_fails = api_fails
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
        if cmd[:3] == ["gh", "api", "graphql"]:
            if self.api_fails:
                result.returncode = 1
                result.stderr = "Not Found"
                return result
            found = re.search(r"root=(\d+)", " ".join(cmd))
            spec = int(found.group(1)) if found else 0
            kids = list(self.children) if spec == self.parent else []
            result.stdout = json.dumps({"data": {"repository": {"issue": {
                "number": spec, "title": "spec", "state": "OPEN",
                "subIssuesSummary": {"total": len(kids), "completed": 0},
                "subIssues": {"nodes": [
                    {"number": k, "title": f"ticket {k}",
                     "state": self.states.get(k, "OPEN"),
                     "subIssuesSummary": {"total": 0, "completed": 0},
                     "subIssues": {"nodes": []}} for k in kids]}}}}})
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result


def run_touched(comments, children, states=None, parent=SPEC, body=BODY,
                api_fails=False):
    """Run --touched; `children` is `{number: body}` of the spec's sub-issues."""
    fake = FakeGh(comments, children, states=states, parent=parent, body=body,
                  api_fails=api_fails)
    printed = io.StringIO()
    err = io.StringIO()
    with mock.patch.object(vt.subprocess, "run", side_effect=fake.run):
        with redirect_stdout(printed), redirect_stderr(err):
            code = vt.run_touched(TICKET)
    return code, err.getvalue(), fake.posted, printed.getvalue(), fake.recorded


def sub_issues_target(recorded):
    """The issue whose tree `--touched` asked the tracker for, or None."""
    for cmd in recorded:
        if cmd[:3] == ["gh", "api", "graphql"]:
            found = re.search(r"root=(\d+)", " ".join(cmd))
            if found:
                return int(found.group(1))
    return None


def touched(body):
    """A posted body as `(prose, payload)`: it must be one `worker.touched` event."""
    what, payload = vt.events.parse(body)
    assert what == "event" and payload["event"] == "worker.touched", (what, payload)
    return body[:body.index("\n\n<!-- mmw")], payload


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
        prose, payload = touched(posted[0][1])
        self.assertEqual((payload["ticket"], payload["by"], payload["files"]),
                         (80, 77, ["src/helper.py"]))
        self.assertEqual(payload["details"], [{
            "path": "src/helper.py", "sentence": "src/helper.py was required for AC1",
            "ac": "AC1", "judgement": "reasonable"}])
        self.assertIn("src/helper.py was required for AC1", prose)
        self.assertIn("reasonable", prose)
        self.assertNotIn("TOUCHED BY", posted[0][1])
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


class TestOneEventPerSibling(unittest.TestCase):
    """What a sibling hears is one `worker.touched` naming every file of its own that
    this ticket changed, never one per file and never one on the ticket itself."""

    def test_a_sibling_covering_two_files_gets_one_event_naming_both(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN_TWO, DECISIONS, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])
        _, payload = touched(posted[0][1])
        self.assertEqual(payload["files"], ["src/helper.py", "src/parse.py"])
        self.assertEqual([d["path"] for d in payload["details"]],
                         ["src/helper.py", "src/parse.py"])

    def test_each_covering_sibling_gets_only_the_files_it_owns(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN_TWO, DECISIONS, REVIEW),
            {80: SIBLING_COVERS, 82: SIBLING_EXACT, 81: SIBLING_OTHER})
        self.assertEqual(code, 0, err)
        got = {n: touched(b)[1] for n, b in posted}
        self.assertEqual(sorted(got), [80, 82])
        self.assertEqual(got[80]["files"], ["src/helper.py", "src/parse.py"])
        self.assertEqual(got[82]["files"], ["src/helper.py"])
        self.assertTrue(all(p["by"] == 77 and p["spec"] == SPEC for p in got.values()))

    def test_the_posting_ticket_never_gets_one(self):
        """The ticket is one of the spec's children too, and its own `## Owns` may well
        cover the path; it is the one that changed the file, so it is told nothing."""
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW), {TICKET: SIBLING_COVERS, 80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [80])


class TestCommentShape(unittest.TestCase):
    def test_no_ac_number_omits_the_empty_line(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS_NO_AC, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        prose, payload = touched(posted[0][1])
        lines = prose.splitlines()
        self.assertEqual(lines[0], "#77 changed 1 file(s) this ticket owns")
        self.assertEqual(lines[1:], ["", "src/helper.py",
                                     "src/helper.py was required for the importer",
                                     "reasonable"])
        self.assertNotIn("ac", payload["details"][0])
        self.assertFalse(any(re.fullmatch(r"AC\d+", line) for line in lines))

    def test_no_decisions_comment_says_so_instead_of_repeating_the_path(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        body, _ = touched(posted[0][1])
        self.assertIn("no DECISIONS comment on #77 yet", body)
        path_lines = [ln for ln in body.splitlines() if ln.strip() == "src/helper.py"]
        self.assertEqual(path_lines, ["src/helper.py"])


class TestRefusesWithoutAReview(unittest.TestCase):
    def test_no_review_comment_exits_2(self):
        code, err, posted, _, recorded = run_touched(
            (SELF_RUN, DECISIONS), {80: SIBLING_COVERS})
        self.assertEqual(code, 2)
        self.assertIn("carries no reviewer.reported event", err)
        self.assertEqual(posted, [])
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))


class TestRefusesWithoutARun(unittest.TestCase):
    def test_a_typed_self_run_comment_is_not_a_run(self):
        """A comment whose first line is `self-run` and that carries no event is prose,
        so the ticket has no run of its own to read Outside Owns from."""
        code, err, posted, _, recorded = run_touched(
            (TYPED_SELF_RUN, DECISIONS, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 2)
        self.assertIn("carries no ticket.checked of your own run", err)
        self.assertEqual(posted, [])
        self.assertIsNone(sub_issues_target(recorded))


class TestNonePostsNothing(unittest.TestCase):
    def test_outside_owns_none_posts_nothing_and_exits_0(self):
        code, err, posted, printed, recorded = run_touched(
            (SELF_RUN_NONE, DECISIONS, REVIEW), {80: SIBLING_COVERS})
        self.assertEqual(code, 0, err)
        self.assertEqual(posted, [])
        self.assertEqual(printed.strip(), "")
        self.assertFalse(any(c[:3] == ["gh", "issue", "comment"] for c in recorded))


FOREIGN_PARENT = (
    "## Parent\n\n无 spec；本仓自建票。"
    "[agentflow#655](https://github.com/agentflow-hq/agentflow/issues/655)\n"
)


class TestRefusesAForeignOrUnreadableSpec(unittest.TestCase):
    def test_a_cross_repo_parent_ref_is_refused_not_fetched(self):
        code, err, posted, _, recorded = run_touched(
            (SELF_RUN, DECISIONS, REVIEW),
            {80: SIBLING_COVERS},
            parent=None,
            body=FOREIGN_PARENT,
        )
        self.assertEqual(code, 2)
        self.assertIn("no spec", err)
        self.assertEqual(posted, [])
        self.assertIsNone(sub_issues_target(recorded))

    def test_a_spec_the_tracker_cannot_list_children_of_is_refused(self):
        code, err, posted, _, _ = run_touched(
            (SELF_RUN, DECISIONS, REVIEW), {80: SIBLING_COVERS}, api_fails=True)
        self.assertEqual(code, 2)
        self.assertIn(str(SPEC), err)
        self.assertEqual(posted, [])


if __name__ == "__main__":
    unittest.main()
