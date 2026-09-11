"""Read-only GitHub index behind ``GET /api/board`` and its refresh endpoint."""

from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import threading
import urllib.parse
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "verify-ticket" / "scripts"
DISPATCH_SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "dispatch" / "scripts"


def _load(name: str, directory: Path = SCRIPTS):
    spec = importlib.util.spec_from_file_location(f"mmw_board_{name}", directory / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = _load("events")
tree = _load("tree")
ghlist = _load("ghlist", DISPATCH_SCRIPTS)


GitHubReadFailed = ghlist.ListReadError


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def plan_read(last_tree_at: dt.datetime | None, tickets: list[dict], now: dt.datetime) -> dict:
    """Choose this poll's GitHub reads from cached state and an explicit clock."""
    stale = last_tree_at is None or (now - last_tree_at).total_seconds() >= 600
    numbers = [ticket["n"] for ticket in tickets if not ticket["fold"]["landed"]]
    return {"tree": stale, "comments": numbers}


def _labels(raw: dict) -> list[str]:
    return [item.get("name") or "" for item in raw.get("labels") or []]


def _last_error(err: str, out: str, fallback: str) -> str:
    return (err or out or fallback).strip().splitlines()[-1]


def _wayfinder_kind(labels: list[str], fallback=None):
    return next((label.split(":", 1)[1] for label in labels
                 if label.startswith("wayfinder:")), fallback)


def _replay(comments: list[dict]) -> list[dict]:
    replay = []
    for comment in events.normalise(comments):
        what, payload = events.parse(comment["body"])
        if what == "event":
            replay.append({
                "comment": comment["id"] if comment["id"] is not None else comment["position"],
                "event": payload["event"],
                "at": payload.get("at"),
                "actor": payload.get("actor"),
                "line": events.first_line(comment["body"]),
                "payload": payload,
            })
    return replay


def _structural_keys(comments: list[dict]) -> set[tuple[int | str, str]]:
    return {
        (event["comment"], event["event"])
        for event in _replay(comments)
        if event["event"] == "child.opened"
        or (event["event"] == "child.closed"
            and event["payload"].get("resolution") == "became-ticket")
    }


def _comments_address(number: int) -> str:
    return f"repos/{{owner}}/{{repo}}/issues/{number}/comments?per_page=100"


class BoardStore:
    def __init__(self, gh=None, clock=utc_now):
        self.gh = gh or ghlist.run_gh
        self.clock = clock
        self.map_trees: list[dict] = []
        self.comments: dict[int, list[dict]] = {}
        self.comment_reader = ghlist.ConditionalListReader(self.gh)
        self.last_tree_at: dt.datetime | None = None
        self.snapshot = {"tasks": [], "read_at": None}
        self.lock = threading.Lock()

    def _json(self, args: list[str]):
        code, out, err = self.gh(args)
        if code != 0:
            raise GitHubReadFailed(_last_error(err, out, "GitHub did not answer"))
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:
            raise GitHubReadFailed("GitHub returned unreadable JSON") from exc

    def _read_trees(self) -> list[dict]:
        maps = self._json(["issue", "list", "--state", "open", "--label", "mmw:map",
                           "--limit", "1000", "--json", "number,title,state,labels"])
        if not isinstance(maps, list):
            raise GitHubReadFailed("the map list was not an array")
        result = []
        for item in maps:
            try:
                read = tree.read(int(item["number"]), "map", gh=self.gh)
            except (KeyError, TypeError, ValueError, tree.TreeUnreadable) as exc:
                raise GitHubReadFailed(str(exc)) from exc
            read["labels"] = _labels(item)
            result.append(read)
        return result

    @staticmethod
    def _ticket_nodes(map_trees: list[dict]) -> list[dict]:
        return [ticket for task in map_trees for spec in task.get("children", [])
                if "mmw:spec" in spec.get("labels", [])
                for ticket in spec.get("children", [])
                if "mmw:ticket" in ticket.get("labels", [])]

    def _shape(self, map_trees: list[dict], comments: dict[int, list[dict]]) -> list[dict]:
        tickets_by_number = {}
        specs_by_ticket = {}
        tasks = []
        for raw_map in map_trees:
            task = {
                "n": raw_map["number"],
                "kind": _wayfinder_kind(raw_map.get("labels", []), "map"),
                "title": raw_map["title"],
                "state": raw_map["state"].lower(),
                "decisions": [],
                "specs": [],
            }
            for child in raw_map.get("children", []):
                labels = child.get("labels", [])
                blockers = [item["number"] for item in child.get("blockedBy", [])]
                decision_kind = _wayfinder_kind(labels)
                if decision_kind:
                    task["decisions"].append({"n": child["number"], "kind": decision_kind,
                                              "title": child["title"],
                                              "state": child["state"].lower(), "blocked": blockers})
                    continue
                if "mmw:spec" not in labels:
                    continue
                spec = {"n": child["number"], "title": child["title"], "tickets": []}
                for raw_ticket in child.get("children", []):
                    if "mmw:ticket" not in raw_ticket.get("labels", []):
                        continue
                    number = raw_ticket["number"]
                    ticket_comments = comments.get(number, [])
                    folded = events.fold(ticket_comments, number)
                    ticket = {
                        "n": number,
                        "title": raw_ticket["title"],
                        "state": raw_ticket["state"].lower(),
                        "blocked": [item["number"] for item in raw_ticket.get("blockedBy", [])],
                        "blockers": [],
                        "blocker_hold": events.blocker_hold(raw_ticket["state"], folded),
                        "closeout": None,
                        "children": raw_ticket.get("children", []),
                        "fold": folded,
                        "events": _replay(ticket_comments),
                    }
                    spec["tickets"].append(ticket)
                    ticket["_blocked_by"] = raw_ticket.get("blockedBy", [])
                    tickets_by_number[number] = ticket
                    specs_by_ticket[number] = spec["n"]
                task["specs"].append(spec)
            tasks.append(task)

        raw_blockers = {node["number"]: node for raw_map in map_trees
                        for spec in raw_map.get("children", [])
                        for node in spec.get("children", [])}
        for ticket in tickets_by_number.values():
            for reference in ticket.pop("_blocked_by"):
                number = reference["number"]
                blocker = tickets_by_number.get(number)
                raw = raw_blockers.get(number, {})
                state = (blocker or raw or reference).get("state", "").upper()
                ticket["blockers"].append({
                    "number": number,
                    "title": (blocker or raw).get("title", ""),
                    "state": state.lower(),
                    "spec": specs_by_ticket.get(number),
                    "readable": blocker is not None,
                    "blocker_hold": events.blocker_hold(state, blocker["fold"] if blocker else None),
                })

        for source in tickets_by_number.values():
            for event in source["events"]:
                payload = event["payload"]
                if event["event"] == "child.closed" and payload.get("resolution") == "became-ticket":
                    became = tickets_by_number.get(payload.get("became"))
                    if became:
                        became["closeout"] = {"from": source["n"], "child": payload.get("child")}
        return tasks

    def answer(self) -> dict:
        with self.lock:
            now = self.clock()
            map_trees = copy.deepcopy(self.map_trees)
            comments = copy.deepcopy(self.comments)
            comment_reader = self.comment_reader.clone()
            last_tree_at = self.last_tree_at
            first_read = last_tree_at is None
            try:
                cached_tasks = self._shape(map_trees, comments) if map_trees else []
                flat = [ticket for task in cached_tasks for spec in task["specs"]
                        for ticket in spec["tickets"]]
                plan = plan_read(last_tree_at, flat, now)
                if plan["tree"]:
                    map_trees = self._read_trees()
                    last_tree_at = now
                    current = self._shape(map_trees, comments)
                    flat = [ticket for task in current for spec in task["specs"]
                            for ticket in spec["tickets"]]
                    plan["comments"] = [ticket["n"] for ticket in flat
                                        if not ticket["fold"]["landed"]]

                structural = False
                for number in plan["comments"]:
                    old_structural = _structural_keys(comments.get(number, []))
                    result = comment_reader.read(_comments_address(number))
                    comments[number] = result
                    structural = structural or bool(_structural_keys(result) - old_structural)

                if structural and not first_read:
                    map_trees = self._read_trees()
                    last_tree_at = now
                new_numbers = [node["number"] for node in self._ticket_nodes(map_trees)
                               if node["number"] not in comments]
                for number in new_numbers:
                    result = comment_reader.read(_comments_address(number))
                    comments[number] = result

                snapshot = {"tasks": self._shape(map_trees, comments), "read_at": iso(now)}
            except GitHubReadFailed as exc:
                failed = copy.deepcopy(self.snapshot)
                failed["read_failed"] = {"at": iso(now), "message": str(exc)}
                return failed

            self.map_trees = map_trees
            self.comments = comments
            self.comment_reader = comment_reader
            self.last_tree_at = last_tree_at
            self.snapshot = snapshot
            return copy.deepcopy(snapshot)


STORE = BoardStore()


def handle(request) -> tuple[int, dict[str, str], bytes]:
    path = urllib.parse.urlsplit(request.path).path
    if request.command == "GET" and path == "/api/board":
        answer = STORE.answer()
    elif request.command == "POST" and path == "/api/board/refresh":
        answer = STORE.answer()
    else:
        body = b'{"error":"not found"}\n'
        return 404, {"Content-Type": "application/json"}, body
    body = (json.dumps(answer, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    return 200, {"Content-Type": "application/json; charset=utf-8"}, body
