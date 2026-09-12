from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v2" / "board" / "server.py"
FAKE_BIN = ROOT / "mmw-v2" / "tests" / "board" / "github"
sys.path.insert(0, str(SERVER.parent))
import board_data  # noqa: E402
from board_process import RunningBoard  # noqa: E402


def event(name: str, ticket: int, **fields) -> dict:
    ident = fields.pop("id", ticket * 100)
    body = board_data.events.build(name, ticket=ticket, spec=10, line=name,
                                   at=fields.pop("at", "2026-09-11T00:00:00Z"), **fields)
    return {"id": ident, "body": body,
            "created_at": "2026-09-11T00:00:00Z"}


def leaf(number, title, state="OPEN", labels=None, blocked=None, children=None):
    return {
        "number": number, "title": title, "state": state,
        "labels": {"totalCount": len(labels or ["mmw:ticket"]),
                   "nodes": [{"name": label} for label in (labels or ["mmw:ticket"])]},
        "blockedBy": {"totalCount": len(blocked or []), "nodes": blocked or []},
        "subIssuesSummary": {"total": len(children or []), "completed": 0},
        "subIssues": {"nodes": children or []},
    }


def container(number, title, children, labels):
    return {
        "number": number, "title": title, "state": "OPEN",
        "labels": {"totalCount": len(labels), "nodes": [{"name": label} for label in labels]},
        "blockedBy": {"totalCount": 0, "nodes": []},
        "subIssuesSummary": {"total": len(children), "completed": 0},
        "subIssues": {"nodes": children},
    }


def tree_fixture():
    child = {"number": 50, "title": "decision needed", "state": "OPEN"}
    ticket12 = leaf(12, "blocked work", blocked=[
        {"number": 11, "state": "CLOSED"}, {"number": 13, "state": "CLOSED"},
        {"number": 99, "state": "CLOSED"}], children=[child])
    ticket11 = leaf(11, "landed blocker", state="CLOSED")
    ticket13 = leaf(13, "passed blocker", state="CLOSED")
    ignored_ticket = leaf(14, "not a ticket", labels=["other"])
    decision = container(2, "research", [], ["wayfinder:research"])
    ignored_map_child = container(3, "not a spec", [], ["other"])
    spec10 = container(10, "first spec", [ticket12, ignored_ticket], ["mmw:spec"])
    spec20 = container(20, "other spec", [ticket11, ticket13], ["mmw:spec"])
    return {
        "number": 1, "title": "task", "state": "OPEN",
        "subIssuesSummary": {"total": 4, "completed": 0},
        "subIssues": {"nodes": [decision, ignored_map_child, spec10, spec20]},
    }


def scenario():
    landed = event("ticket.landed", 11)
    routed = event("child.closed", 11, id=1101, child=40,
                   resolution="became-ticket", became=12)
    claimed = event("ticket.claimed", 12)
    opened = event("child.opened", 12, child=50, kind="decision", title="choose")
    fixed = event("child.closed", 12, id=1202, child=50, resolution="fixed")
    became = event("child.closed", 12, id=1203, child=51,
                   resolution="became-ticket", became=15)
    passed = event("ticket.passed", 13, commit="a" * 40)
    return {
        "maps": [{"number": 1, "title": "task", "state": "OPEN",
                  "labels": [{"name": "mmw:map"}, {"name": "wayfinder:map"}]}],
        "trees": [tree_fixture()],
        "comments": {
            "11": [{"etag": '"eleven"', "comments": [landed, routed]}],
            "12": [{"etag": '"twelve-a"', "comments": [claimed]},
                   {"etag": '"twelve-b"', "comments": [claimed, opened]},
                   {"etag": '"twelve-c"', "comments": [claimed, opened, fixed]},
                   {"etag": '"twelve-d"', "comments": [claimed, opened, fixed, became]}],
            "13": [{"etag": '"thirteen"', "comments": [passed]}],
        },
        "comment_active": {"11": 0, "12": 0, "13": 0},
    }


def running_board(data):
    path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
    return RunningBoard(environment={"PATH": path}, fixture=data)


def read_board(board, method="GET", path="/api/board"):
    headers = {} if method == "GET" else board.write_headers
    status, raw = board.request(method, path, headers=headers)
    if status != 200:
        raise AssertionError(f"board request returned HTTP {status}: {raw}")
    return json.loads(raw)


def tickets(answer):
    return {ticket["n"]: ticket for task in answer["tasks"] for spec in task["specs"]
            for ticket in spec["tickets"]}


def prepared_store(gh):
    now = dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc)
    store = board_data.BoardStore(gh=gh, clock=lambda: now)
    store.map_trees = [board_data.tree._node(tree_fixture(), "#1")]
    store.last_tree_at = now
    return store


class BoardDataTest(unittest.TestCase):
    def test_every_comment_page_is_read_and_cached_by_etag(self):
        calls = []
        second_url = "https://api.github.test/repos/x/issues/12/comments?per_page=100&page=2"
        first = event("ticket.claimed", 12, id=1201)
        second = event("ticket.claimed", 12, id=1202)

        def gh(args):
            calls.append(args)
            url = args[2]
            number = int(re.search(r"/issues/(\d+)/comments", url).group(1))
            tag = ('"page-two"' if url == second_url else
                   '"page-one"' if number == 12 else f'"ticket-{number}"')
            conditional = f"If-None-Match: {tag}" in args
            if conditional:
                return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304\n"
            link = f"Link: <{second_url}>; rel=\"next\"\n" if number == 12 and url != second_url else ""
            rows = [second] if url == second_url else [first] if number == 12 else []
            return 0, f"HTTP/2 200 OK\nETag: {tag}\n{link}\n{json.dumps(rows)}\n", ""

        store = prepared_store(gh)
        first_answer = store.answer()
        second_answer = store.answer()
        self.assertEqual([row["comment"] for row in tickets(first_answer)[12]["events"]],
                         [1201, 1202])
        self.assertEqual(tickets(second_answer)[12]["events"], tickets(first_answer)[12]["events"])
        twelve = [call for call in calls if "/issues/12/comments" in call[2]]
        self.assertEqual(len(twelve), 4)
        self.assertIn('If-None-Match: "page-one"', twelve[2])
        self.assertIn('If-None-Match: "page-two"', twelve[3])

    def test_past_a_full_page(self):
        next_url = "https://api.github.test/comments?per_page=100&page=2"
        calls = []
        first_page = [event("ticket.claimed", 12, id=1200 + n) for n in range(1, 101)]
        last = event("ticket.claimed", 12, id=1301)
        first_page_reads = 0

        def gh(args):
            nonlocal first_page_reads
            calls.append(args)
            url = args[2]
            if url == next_url:
                return 0, f"HTTP/2 200 OK\nETag: \"two\"\n\n{json.dumps([last])}", ""
            number = int(re.search(r"/issues/(\d+)/comments", url).group(1))
            if number != 12:
                tag = f'"ticket-{number}"'
                if f"If-None-Match: {tag}" in args:
                    return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304"
                return 0, f"HTTP/2 200 OK\nETag: {tag}\n\n[]", ""
            if 'If-None-Match: "full"' in args:
                return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304"
            first_page_reads += 1
            link = f'Link: <{next_url}>; rel="next"\n' if first_page_reads > 1 else ""
            return 0, f"HTTP/2 200 OK\nETag: \"full\"\n{link}\n{json.dumps(first_page)}", ""

        store = prepared_store(gh)
        self.assertEqual(len(tickets(store.answer())[12]["events"]), 100)
        self.assertEqual(len(tickets(store.answer())[12]["events"]), 101)
        twelve = [call for call in calls if "/issues/12/comments" in call[2]]
        self.assertNotIn('If-None-Match: "full"', twelve[1])
        self.assertEqual([call[2] for call in calls if call[2] == next_url], [next_url])

    def test_board_answers_the_tree_with_each_fold(self):
        data = scenario()
        with running_board(data) as board:
            result = read_board(board)
        task = result["tasks"][0]
        self.assertEqual((task["n"], task["decisions"][0]["kind"]), (1, "research"))
        self.assertEqual([spec["n"] for spec in task["specs"]], [10, 20])
        self.assertEqual([item["n"] for item in task["specs"][0]["tickets"]], [12])
        got = tickets(result)[12]
        expected = board_data.events.fold(data["comments"]["12"][0]["comments"], 12)
        self.assertEqual(got["fold"], expected)
        self.assertEqual(got["events"][0]["event"], "ticket.claimed")
        self.assertEqual(got["children"][0]["number"], 50)
        self.assertEqual(got["closeout"], {"from": 11, "child": 40})

    def test_a_spec_with_no_map_is_a_task_of_its_own(self):
        data = scenario()
        spec30 = container(30, "lone spec", [container(31, "its ticket", [], ["mmw:ticket"])],
                           ["mmw:spec"])
        spec30["subIssuesSummary"] = {"total": 1, "completed": 0}
        data["specs"] = [{"number": 10, "title": "first spec", "state": "OPEN",
                          "labels": [{"name": "mmw:spec"}]},
                         {"number": 30, "title": "lone spec", "state": "OPEN",
                          "labels": [{"name": "mmw:spec"}]}]
        data["trees"] = [tree_fixture(), spec30]
        data["tree_by_root"] = {"1": 0, "30": 1}
        with running_board(data) as board:
            result = read_board(board)
        by_number = {task["n"]: task for task in result["tasks"]}
        self.assertEqual(sorted(by_number), [1, 30])
        lone = by_number[30]
        self.assertEqual((lone["kind"], lone["decisions"], [s["n"] for s in lone["specs"]]),
                         ("spec", [], [30]))
        self.assertEqual([t["n"] for t in lone["specs"][0]["tickets"]], [31])
        self.assertNotIn(10, by_number, "a spec under an open map is not a second task")

    def test_board_names_its_repository(self):
        data = scenario()
        data["repo"] = "owner/board-repo"
        with running_board(data) as board:
            first = read_board(board)
            second = read_board(board)
            calls = board.fixture_calls()
        self.assertEqual((first["repo"], second["repo"]), ("owner/board-repo", "owner/board-repo"))
        self.assertEqual(sum(call[:2] == ["repo", "view"] for call in calls), 1)

    def test_blockers_carry_hold_and_where(self):
        with running_board(scenario()) as board:
            got = tickets(read_board(board))[12]
        blockers = {item["number"]: item for item in got["blockers"]}
        self.assertEqual(blockers[11]["blocker_hold"], "")
        self.assertEqual((blockers[11]["spec"], blockers[11]["readable"]), (20, True))
        self.assertEqual(blockers[13]["blocker_hold"], "passed, not landed")
        self.assertEqual((blockers[99]["spec"], blockers[99]["readable"]), (None, False))
        self.assertEqual(blockers[99]["blocker_hold"], "the tracker did not answer for it")

    def test_later_reads_send_etags_for_unlanded_only(self):
        with running_board(scenario()) as board:
            first = read_board(board)
            second = read_board(board)
            calls = board.fixture_calls()
        self.assertEqual(first["tasks"], second["tasks"])
        comment_calls = [call for call in calls if call[:2] == ["api", "-i"]]
        self.assertEqual(sum("/issues/11/comments" in call[2] for call in comment_calls), 1)
        twelve = [call for call in comment_calls if "/issues/12/comments" in call[2]]
        self.assertEqual(len(twelve), 2)
        self.assertIn("If-None-Match: \"twelve-a\"", twelve[1])

    def test_structure_event_rereads_the_tree(self):
        data = scenario()
        with running_board(data) as board:
            read_board(board)
            read_board(board)
            self.assertEqual(board.fixture_state()["tree_reads"], 1)
            data["comment_active"]["12"] = 1
            board.write_fixture(data)
            read_board(board)
            self.assertEqual(board.fixture_state()["tree_reads"], 2)
            read_board(board)
            self.assertEqual(board.fixture_state()["tree_reads"], 2)
            data["comment_active"]["12"] = 2
            board.write_fixture(data)
            read_board(board)
            self.assertEqual(board.fixture_state()["tree_reads"], 2)
            data["comment_active"]["12"] = 3
            board.write_fixture(data)
            read_board(board)
            reads = board.fixture_state()["tree_reads"]
        self.assertEqual(reads, 3)

    def test_tree_is_reread_after_ten_minutes(self):
        now = dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc)
        active = [{"n": 12, "fold": {"landed": False}, "blocker_hold": "open"},
                  {"n": 11, "fold": {"landed": True}, "blocker_hold": ""}]
        self.assertEqual(board_data.plan_read(now - dt.timedelta(seconds=599), active, now),
                         {"tree": False, "comments": [12]})
        self.assertEqual(board_data.plan_read(now - dt.timedelta(seconds=600), active, now),
                         {"tree": True, "comments": [12]})

    def test_a_ticket_closed_by_hand_stops_being_reread(self):
        now = dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc)
        # Closed outside the pipeline: no `ticket.landed`, an empty ledger, and nothing
        # that will ever land. One that passed and has not landed yet is still to come.
        by_hand = {"n": 24, "fold": {"landed": False}, "blocker_hold": ""}
        passed = {"n": 25, "fold": {"landed": False}, "blocker_hold": "passed, not landed"}
        unreadable = {"n": 26, "fold": {"landed": False},
                      "blocker_hold": "its events cannot be read"}
        self.assertEqual(board_data.plan_read(now, [by_hand, passed, unreadable], now),
                         {"tree": False, "comments": [25, 26]})
        self.assertEqual([board_data.finished(row) for row in (by_hand, passed, unreadable)],
                         [True, False, False])

    def test_failed_read_keeps_the_last_data(self):
        data = scenario()
        with running_board(data) as board:
            first = read_board(board)
            time.sleep(1.05)
            data["comment_active"]["12"] = 1
            data["fail_comments"] = [12]
            board.write_fixture(data)
            failed = read_board(board)
        self.assertEqual(failed["tasks"], first["tasks"])
        self.assertEqual(failed["read_at"], first["read_at"])
        self.assertIn("read_failed", failed)

    def test_refresh_reads_now(self):
        with running_board(scenario()) as board:
            first = read_board(board)
            before = len(board.fixture_calls())
            time.sleep(1.05)
            refreshed = read_board(board, "POST", "/api/board/refresh")
            refresh_calls = board.fixture_calls()[before:]
        self.assertGreater(refreshed["read_at"], first["read_at"])
        self.assertEqual(refreshed.keys(), first.keys())
        self.assertEqual(refreshed["tasks"], first["tasks"])
        twelve = [call for call in refresh_calls if call[:2] == ["api", "-i"]
                  and "/issues/12/comments" in call[2]]
        self.assertEqual(len(twelve), 1)
        self.assertIn("If-None-Match: \"twelve-a\"", twelve[0])

    def test_never_writes_github(self):
        with running_board(scenario()) as board:
            answers = [read_board(board), read_board(board, "POST", "/api/board/refresh"),
                       read_board(board)]
            calls = board.fixture_calls()
        self.assertTrue(all("read_failed" not in answer for answer in answers))
        for call in calls:
            if call[:2] == ["repo", "view"]:
                continue
            if call[:2] == ["issue", "list"]:
                self.assertEqual(call[call.index("--state") + 1], "open")
                continue
            if call[:2] == ["api", "graphql"]:
                query_arg = next(value for value in call if value.startswith("query="))
                self.assertTrue(query_arg.startswith("query=query("))
                self.assertNotIn("mutation", query_arg.lower())
                continue
            self.assertEqual(call[:2], ["api", "-i"])
            self.assertRegex(call[2], r"/issues/\d+/comments")
            self.assertFalse(any(value in call for value in
                                 ["-X", "--method", "-f", "-F", "--input"]))


if __name__ == "__main__":
    unittest.main()
