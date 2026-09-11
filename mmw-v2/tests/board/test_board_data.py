from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v2" / "board" / "server.py"
FAKE_BIN = ROOT / "mmw-v2" / "tests" / "board" / "github"
sys.path.insert(0, str(SERVER.parent))
import board_data  # noqa: E402


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


class RunningBoard:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.write(self.data)
        env = os.environ.copy()
        env["MMW_BOARD_FAKE_DIR"] = str(self.directory)
        env["PATH"] = str(FAKE_BIN) + os.pathsep + env.get("PATH", "")
        self.process = subprocess.Popen(
            ["python3", "-u", str(SERVER), "--port", "0"], cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.origin = self.process.stdout.readline().strip()
        if not self.origin.startswith("http://127.0.0.1:"):
            raise RuntimeError(self.process.stderr.read())
        return self

    def __exit__(self, *args):
        self.process.terminate()
        self.process.wait(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()
        self.temp.cleanup()

    def write(self, data):
        self.data = data
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "scenario.json").write_text(json.dumps(data))

    def request(self, method="GET", path="/api/board"):
        request = urllib.request.Request(self.origin + path, method=method)
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read())

    def calls(self):
        path = self.directory / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def state(self):
        return json.loads((self.directory / "state.json").read_text())


def tickets(answer):
    return {ticket["n"]: ticket for task in answer["tasks"] for spec in task["specs"]
            for ticket in spec["tickets"]}


class BoardDataTest(unittest.TestCase):
    def test_every_comment_page_is_read_and_cached_by_etag(self):
        calls = []
        second_url = "https://api.github.test/repos/x/issues/12/comments?per_page=100&page=2"

        def gh(args):
            calls.append(args)
            url = args[2]
            tag = '"page-two"' if url == second_url else '"page-one"'
            conditional = f"If-None-Match: {tag}" in args
            if conditional:
                return 1, "HTTP/2 304 Not Modified\n\n", "gh: HTTP 304\n"
            link = f"Link: <{second_url}>; rel=\"next\"\n" if url != second_url else ""
            ident = 2 if url == second_url else 1
            return 0, f"HTTP/2 200 OK\nETag: {tag}\n{link}\n[{{\"id\":{ident},\"body\":\"\"}}]\n", ""

        store = board_data.BoardStore(gh=gh)
        cache = board_data.CommentCache()
        comments = store._read_comments(12, cache)
        self.assertEqual([comment["id"] for comment in comments], [1, 2])
        cached = store._read_comments(12, cache)
        self.assertEqual(cached, comments)
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(any(value.startswith("If-None-Match:") for value in call)
                            for call in calls[2:]))

    def test_board_answers_the_tree_with_each_fold(self):
        data = scenario()
        with RunningBoard(data) as board:
            answer = board.request()
        task = answer["tasks"][0]
        self.assertEqual((task["n"], task["decisions"][0]["kind"]), (1, "research"))
        self.assertEqual([spec["n"] for spec in task["specs"]], [10, 20])
        self.assertEqual([item["n"] for item in task["specs"][0]["tickets"]], [12])
        got = tickets(answer)[12]
        expected = board_data.events.fold(data["comments"]["12"][0]["comments"], 12)
        self.assertEqual(got["fold"], expected)
        self.assertEqual(got["events"][0]["event"], "ticket.claimed")
        self.assertEqual(got["children"][0]["number"], 50)
        self.assertEqual(got["closeout"], {"from": 11, "child": 40})

    def test_blockers_carry_hold_and_where(self):
        with RunningBoard(scenario()) as board:
            got = tickets(board.request())[12]
        blockers = {item["number"]: item for item in got["blockers"]}
        self.assertEqual(blockers[11]["blocker_hold"], "")
        self.assertEqual((blockers[11]["spec"], blockers[11]["readable"]), (20, True))
        self.assertEqual(blockers[13]["blocker_hold"], "passed, not landed")
        self.assertEqual((blockers[99]["spec"], blockers[99]["readable"]), (None, False))
        self.assertEqual(blockers[99]["blocker_hold"], "the tracker did not answer for it")

    def test_later_reads_send_etags_for_unlanded_only(self):
        with RunningBoard(scenario()) as board:
            first = board.request()
            second = board.request()
            calls = board.calls()
        self.assertEqual(first["tasks"], second["tasks"])
        comment_calls = [call for call in calls if call[:2] == ["api", "-i"]]
        self.assertEqual(sum("/issues/11/comments" in call[2] for call in comment_calls), 1)
        twelve = [call for call in comment_calls if "/issues/12/comments" in call[2]]
        self.assertEqual(len(twelve), 2)
        self.assertIn("If-None-Match: \"twelve-a\"", twelve[1])

    def test_structure_event_rereads_the_tree(self):
        data = scenario()
        with RunningBoard(data) as board:
            board.request()
            board.request()
            self.assertEqual(board.state()["tree_reads"], 1)
            data["comment_active"]["12"] = 1
            board.write(data)
            board.request()
            self.assertEqual(board.state()["tree_reads"], 2)
            board.request()
            self.assertEqual(board.state()["tree_reads"], 2)
            data["comment_active"]["12"] = 2
            board.write(data)
            board.request()
            self.assertEqual(board.state()["tree_reads"], 2)
            data["comment_active"]["12"] = 3
            board.write(data)
            board.request()
            reads = board.state()["tree_reads"]
        self.assertEqual(reads, 3)

    def test_tree_is_reread_after_ten_minutes(self):
        now = dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc)
        active = [{"n": 12, "fold": {"landed": False}}, {"n": 11, "fold": {"landed": True}}]
        self.assertEqual(board_data.plan_read(now - dt.timedelta(seconds=599), active, now),
                         {"tree": False, "comments": [12]})
        self.assertEqual(board_data.plan_read(now - dt.timedelta(seconds=600), active, now),
                         {"tree": True, "comments": [12]})

    def test_failed_read_keeps_the_last_data(self):
        data = scenario()
        with RunningBoard(data) as board:
            first = board.request()
            time.sleep(1.05)
            data["comment_active"]["12"] = 1
            data["fail_comments"] = [12]
            board.write(data)
            failed = board.request()
        self.assertEqual(failed["tasks"], first["tasks"])
        self.assertEqual(failed["read_at"], first["read_at"])
        self.assertIn("read_failed", failed)

    def test_refresh_reads_now(self):
        with RunningBoard(scenario()) as board:
            first = board.request()
            before = len(board.calls())
            time.sleep(1.05)
            refreshed = board.request("POST", "/api/board/refresh")
            refresh_calls = board.calls()[before:]
        self.assertGreater(refreshed["read_at"], first["read_at"])
        self.assertEqual(refreshed.keys(), first.keys())
        self.assertEqual(refreshed["tasks"], first["tasks"])
        twelve = [call for call in refresh_calls if call[:2] == ["api", "-i"]
                  and "/issues/12/comments" in call[2]]
        self.assertEqual(len(twelve), 1)
        self.assertIn("If-None-Match: \"twelve-a\"", twelve[0])

    def test_never_writes_github(self):
        with RunningBoard(scenario()) as board:
            answers = [board.request(), board.request("POST", "/api/board/refresh"),
                       board.request()]
            calls = board.calls()
        self.assertTrue(all("read_failed" not in answer for answer in answers))
        for call in calls:
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
