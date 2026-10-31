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
tree = _load("issue_tree")
ghlist = _load("ghlist", DISPATCH_SCRIPTS)


GitHubReadFailed = ghlist.ListReadError


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


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


def _comments_address(number: int) -> str:
    return f"repos/{{owner}}/{{repo}}/issues/{number}/comments?per_page=100"


class BoardStore:
    def __init__(self, gh=None, clock=utc_now):
        self.clock = clock
        self.map_trees: list[dict] = []
        self.comments: dict[int, list[dict]] = {}
        self.comment_reader = ghlist.ConditionalListReader(gh or ghlist.run_gh)
        self.comment_reader.clock = lambda: self.clock().timestamp()
        self.last_tree_at: dt.datetime | None = None
        self.repo: str | None = None
        self.snapshot = {"tasks": [], "repo": None, "read_at": None}
        self.lock = threading.Condition()
        self.refreshing = False
        self.last_answer = self.snapshot

    def _json(self, args: list[str]):
        code, out, err = self.comment_reader.request(args)
        if code != 0:
            raise GitHubReadFailed(_last_error(err, out, "GitHub did not answer"))
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:
            raise GitHubReadFailed("GitHub returned unreadable JSON") from exc

    def _read_roots(self) -> dict:
        query = """query($o:String!, $n:String!, $mapsAfter:String, $specsAfter:String,
                         $mapsMore:Boolean! = true, $specsMore:Boolean! = true) {
          repository(owner:$o, name:$n) {
            nameWithOwner
            maps: issues(first:100, states:OPEN, labels:["mmw:map"], after:$mapsAfter)
                @include(if:$mapsMore) {
              nodes { number title state labels(first:100) { nodes { name } } }
              pageInfo { hasNextPage endCursor }
            }
            specs: issues(first:100, states:OPEN, labels:["mmw:spec"], after:$specsAfter)
                @include(if:$specsMore) {
              nodes { number title state labels(first:100) { nodes { name } } }
              pageInfo { hasNextPage endCursor }
            }
          }
        }"""
        result = {"maps": {}, "specs": {}}
        pending = {"maps": None, "specs": None}
        while pending:
            args = ["api", "graphql", "-F", "o={owner}", "-F", "n={repo}", "-f", f"query={query}"]
            for name in ("maps", "specs"):
                args += ["-F", f"{name}More={'true' if name in pending else 'false'}"]
                if pending.get(name):
                    args += ["-f", f"{name}After={pending[name]}"]
            raw = self._json(args)
            try:
                if raw.get("errors"):
                    raise GitHubReadFailed(str(raw["errors"]))
                repo = raw["data"]["repository"]
                result["repo"] = repo["nameWithOwner"]
                for name in list(pending):
                    connection = repo[name]
                    for node in connection["nodes"]:
                        result[name][node["number"]] = {**node, "labels": node["labels"]["nodes"]}
                    page = connection["pageInfo"]
                    if not page["hasNextPage"]:
                        del pending[name]
                    else:
                        cursor = page["endCursor"]
                        if not cursor or cursor == pending[name]:
                            raise GitHubReadFailed(f"the {name} root list did not advance its page")
                        pending[name] = cursor
            except (KeyError, TypeError) as exc:
                raise GitHubReadFailed("GitHub returned incomplete repository roots") from exc
        return {**result, "maps": list(result["maps"].values()),
                "specs": list(result["specs"].values())}

    def _read_trees(self, roots: dict) -> list[dict]:
        """One tree per top-level task: every open map, then every open spec that no open
        map holds as a child. A spec with no map above it is a task of its own, so a spec
        published straight from a conversation is on the board like any other."""
        result = []
        under_a_map: set[int] = set()
        for item in roots["maps"]:
            try:
                read = tree.read(int(item["number"]), "map", gh=self.comment_reader.request)
            except (KeyError, TypeError, ValueError, tree.TreeUnreadable) as exc:
                raise GitHubReadFailed(str(exc)) from exc
            read["labels"] = _labels(item)
            result.append(read)
            under_a_map.update(child["number"] for child in read.get("children", [])
                               if "number" in child)
        for item in roots["specs"]:
            try:
                number = int(item["number"])
            except (KeyError, TypeError, ValueError) as exc:
                raise GitHubReadFailed(str(exc)) from exc
            if number in under_a_map:
                continue
            try:
                read = tree.read(number, "spec", gh=self.comment_reader.request)
            except tree.TreeUnreadable as exc:
                raise GitHubReadFailed(str(exc)) from exc
            read["labels"] = _labels(item)
            read["top_spec"] = True
            result.append(read)
        return result

    @staticmethod
    def _spec_trees(task_tree: dict) -> list[dict]:
        """The spec nodes a task holds: the tree itself for a top-level spec, else the
        map's spec children."""
        if task_tree.get("top_spec"):
            return [task_tree]
        return [spec for spec in task_tree.get("children", [])
                if "mmw:spec" in spec.get("labels", [])]

    @classmethod
    def _ticket_nodes(cls, map_trees: list[dict]) -> list[dict]:
        return [ticket for task in map_trees for spec in cls._spec_trees(task)
                for ticket in spec.get("children", [])
                if "mmw:ticket" in ticket.get("labels", [])]

    def _shape(self, map_trees: list[dict], comments: dict[int, list[dict]]) -> list[dict]:
        tickets_by_number = {}
        specs_by_ticket = {}
        tasks = []
        for raw_map in map_trees:
            top_spec = bool(raw_map.get("top_spec"))
            task = {
                "n": raw_map["number"],
                "kind": "spec" if top_spec else _wayfinder_kind(raw_map.get("labels", []), "map"),
                "title": raw_map["title"],
                "state": raw_map["state"].lower(),
                "decisions": [],
                "specs": [],
            }
            for child in ([raw_map] if top_spec else raw_map.get("children", [])):
                labels = child.get("labels", [])
                blockers = [item["number"] for item in child.get("blockedBy", [])]
                decision_kind = None if top_spec else _wayfinder_kind(labels)
                if decision_kind:
                    task["decisions"].append({"n": child["number"], "kind": decision_kind,
                                              "title": child["title"],
                                              "state": child["state"].lower(), "blocked": blockers})
                    continue
                if not top_spec and "mmw:spec" not in labels:
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
                        for spec in self._spec_trees(raw_map)
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

    def answer(self, force: bool = False) -> dict:
        with self.lock:
            if self.refreshing:
                self.lock.wait_for(lambda: not self.refreshing)
                return copy.deepcopy(self.last_answer)
            now = self.clock()
            if not force and self.last_tree_at is not None and (now - self.last_tree_at).total_seconds() < 60:
                return copy.deepcopy(self.last_answer)
            self.refreshing = True
        try:
            comment_reader = self.comment_reader.clone()
            self.comment_reader.ensure_ready()
            roots = self._read_roots()
            map_trees = self._read_trees(roots)
            numbers = dict.fromkeys(node["number"] for node in self._ticket_nodes(map_trees))
            comments = {number: comment_reader.read(_comments_address(number)) for number in numbers}
            snapshot = {"tasks": self._shape(map_trees, comments), "repo": roots["repo"],
                        "read_at": iso(self.clock())}
            with self.lock:
                self.map_trees = map_trees
                self.comments = comments
                self.comment_reader = comment_reader
                self.last_tree_at = self.clock()
                self.repo = roots["repo"]
                self.snapshot = snapshot
                self.last_answer = snapshot
        except GitHubReadFailed as exc:
            with self.lock:
                failed = copy.deepcopy(self.snapshot)
                failed["read_failed"] = {"at": iso(self.clock()), "message": str(exc)}
                if self.comment_reader.retry_at > self.clock().timestamp():
                    failed["read_failed"]["retry_at"] = iso(dt.datetime.fromtimestamp(
                        self.comment_reader.retry_at, dt.timezone.utc))
                self.last_answer = failed
        finally:
            with self.lock:
                self.refreshing = False
                self.lock.notify_all()
        return copy.deepcopy(self.last_answer)


STORE = BoardStore()


def handle(request) -> tuple[int, dict[str, str], bytes]:
    path = urllib.parse.urlsplit(request.path).path
    if request.command == "GET" and path == "/api/board":
        answer = STORE.answer()
    elif request.command == "POST" and path == "/api/board/refresh":
        answer = STORE.answer(force=True)
    else:
        body = b'{"error":"not found"}\n'
        return 404, {"Content-Type": "application/json"}, body
    body = (json.dumps(answer, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    return 200, {"Content-Type": "application/json; charset=utf-8"}, body
