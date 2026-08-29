"""The ticket graph: cycles, dangling references, and which tickets start first.

`validate_dag` and `compute_levels` are grok-bundled's
`execute-plan/scripts/validate-plan.py` L145-280 with one change of shape: an id is
an issue number and dependencies come from `## Blocked by`. The cases below are the
ones that file's `_detect_cycles` and `compute_levels` distinguish — the two-node
cycle Kahn's algorithm cannot drain, the longer cycle `_trace_cycle` walks back to a
path, and the diamond where a level is the longest path, not the shortest.
"""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests._load import load

vt = load()


def entries(**graph):
    """`entries(a61=[], a62=[61])` reads as `{61: [], 62: [61]}` without quoting keys."""
    return [{"id": int(name[1:]), "dependencies": deps} for name, deps in graph.items()]


def body(parent=76, blockers=("None (can start immediately)",)):
    lines = ["## Parent", "", f"#{parent}, Implementation Decisions section 1", "",
             "## Blocked by", ""]
    lines += [f"- {b}" for b in blockers]
    return "\n".join(lines) + "\n"


def lint_graph(ticket=77, spec=76, batch=(), bodies=None):
    """Run the graph half of --lint over a made-up batch; return (exit code, output)."""
    bodies = bodies or {}
    with mock.patch.object(vt, "fetch_sub_issues", return_value=list(batch)), \
         mock.patch.object(vt, "fetch_body", side_effect=lambda n: bodies.get(n, body())):
        with redirect_stdout(io.StringIO()) as out:
            code = vt.lint_ticket_graph(ticket, body(parent=spec))
    return code, out.getvalue()


class TestValidateDag(unittest.TestCase):
    def test_a_clean_chain_reports_nothing(self):
        self.assertEqual(vt.validate_dag(entries(a61=[], a62=[61], a63=[62])), [])

    def test_two_tickets_blocking_each_other_are_a_cycle(self):
        errors = vt.validate_dag(entries(a61=[62], a62=[61]))
        self.assertEqual(len(errors), 1)
        self.assertIn("cycle", errors[0])
        self.assertIn("#61", errors[0])
        self.assertIn("#62", errors[0])

    def test_a_longer_cycle_is_reported_as_a_path(self):
        errors = vt.validate_dag(entries(a61=[63], a62=[61], a63=[62]))
        self.assertEqual(len(errors), 1)
        self.assertRegex(errors[0], r"cycle detected: (#\d+ -> ){2,}#\d+")

    def test_a_dependency_outside_the_batch_is_dangling(self):
        errors = vt.validate_dag(entries(a61=[], a62=[999]))
        self.assertEqual(len(errors), 1)
        self.assertIn("dangling", errors[0])
        self.assertIn("#999", errors[0])

    def test_a_dangling_reference_is_reported_instead_of_a_cycle(self):
        # Kahn's algorithm cannot tell the two apart, so references are checked first.
        errors = vt.validate_dag(entries(a61=[999], a62=[61]))
        self.assertTrue(all("cycle" not in e for e in errors))

    def test_the_same_ticket_twice_is_a_duplicate(self):
        errors = vt.validate_dag([{"id": 61, "dependencies": []},
                                  {"id": 61, "dependencies": []}])
        self.assertIn("duplicate", errors[0])


class TestComputeLevels(unittest.TestCase):
    def test_a_ticket_nothing_blocks_starts_at_level_zero(self):
        levels = vt.compute_levels(entries(a61=[], a62=[61]))
        self.assertEqual(levels, {61: 0, 62: 1})

    def test_a_level_is_the_longest_path_not_the_shortest(self):
        # 64 waits for 63, which waits for 61 — so 64 is level 3 even though 61
        # would also let it start at level 1.
        levels = vt.compute_levels(entries(a61=[], a62=[61], a63=[62], a64=[61, 63]))
        self.assertEqual(levels[64], 3)

    def test_independent_tickets_share_a_level(self):
        levels = vt.compute_levels(entries(a61=[], a62=[], a63=[61, 62]))
        self.assertEqual(levels, {61: 0, 62: 0, 63: 1})


class TestLintTicketGraph(unittest.TestCase):
    def test_a_cycle_is_printed_and_exits_one(self):
        bodies = {61: body(blockers=("#62",)), 62: body(blockers=("#61",))}
        code, out = lint_graph(batch=(61, 62), bodies=bodies)
        self.assertEqual(code, 1)
        self.assertIn("cycle", out)

    def test_a_dangling_reference_is_printed_and_exits_one(self):
        bodies = {61: body(), 62: body(blockers=("#999",))}
        code, out = lint_graph(batch=(61, 62), bodies=bodies)
        self.assertEqual(code, 1)
        self.assertIn("dangling", out)

    def test_a_clean_batch_prints_its_start_levels(self):
        bodies = {61: body(), 62: body(blockers=("#61",)), 63: body(blockers=("#61",))}
        code, out = lint_graph(batch=(61, 62, 63), bodies=bodies)
        self.assertEqual(code, 0)
        self.assertIn("level 0: #61", out)
        self.assertIn("level 1: #62, #63", out)

    def test_a_ticket_with_no_parent_section_checks_nothing(self):
        with mock.patch.object(vt, "fetch_sub_issues") as fetch:
            with redirect_stdout(io.StringIO()) as out:
                code = vt.lint_ticket_graph(77, "## What to build\n\nsomething\n")
        self.assertEqual(code, 0)
        self.assertIn("no `## Parent` section", out.getvalue())
        fetch.assert_not_called()

    def test_a_spec_with_no_sub_issues_checks_nothing(self):
        code, out = lint_graph(batch=())
        self.assertEqual(code, 0)
        self.assertIn("no sub-issues", out)


class TestBlockedBy(unittest.TestCase):
    def test_none_reads_as_no_blockers(self):
        self.assertEqual(vt.blocked_by(body()), [])

    def test_each_referenced_ticket_is_a_blocker(self):
        self.assertEqual(vt.blocked_by(body(blockers=("#61", "#62"))), [61, 62])

    def test_the_parent_spec_is_read_off_the_parent_section(self):
        self.assertEqual(vt.parent_spec(body(parent=60)), 60)


if __name__ == "__main__":
    unittest.main()
