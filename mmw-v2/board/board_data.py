"""Read-only GitHub index behind ``GET /api/board`` and its refresh endpoint."""

from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import subprocess
import threading
import urllib.parse
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "verify-ticket" / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"mmw_board_{name}", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = _load("events")
tree = _load("tree")


class GitHubReadFailed(RuntimeError):
    """A read did not produce a complete answer."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def plan_read(last_tree_at: dt.datetime | None, tickets: list[dict], now: dt.datetime) -> dict:
    """Choose this poll's GitHub reads from cached state and an explicit clock."""
    first = last_tree_at is None
    stale = first or (now - last_tree_at).total_seconds() >= 600
    numbers = [ticket["n"] for ticket in tickets if first or not ticket["fold"]["landed"]]
    return {"tree": stale, "comments": numbers}


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    run = subprocess.run(["gh", *args], capture_output=True, text=True)
    return run.returncode, run.stdout, run.stderr


def _labels(raw: dict) -> list[str]:
    labels = raw.get("labels") or []
    if isinstance(labels, dict):
        labels = labels.get("nodes") or []
    return [item.get("name") or "" if isinstance(item, dict) else str(item) for item in labels]


def _replay(comments: list[dict]) -> list[dict]:
    replay = []
    for what, record in events._records(comments):
        if what == "event":
            replay.append({key: record[key] for key in
                           ("comment", "event", "at", "actor", "line", "payload")})
    return replay


def _structural_keys(comments: list[dict]) -> set[tuple[int | str, str]]:
    return {
        (event["comment"], event["event"])
        for event in _replay(comments)
        if event["event"] == "child.opened"
        or (event["event"] == "child.closed"
            and event["payload"].get("resolution") == "became-ticket")
    }


class BoardStore:
    def __init__(self, gh=None, clock=utc_now):
        self.gh = gh or _run_gh
        self.clock = clock
        self.map_trees: list[dict] = []
        self.comments: dict[int, list[dict]] = {}
        self.comment_pages: dict[int, dict[str, list[dict]]] = {}
        self.etags: dict[int, dict[str, str]] = {}
        self.next_pages: dict[int, dict[str, str | None]] = {}
        self.last_tree_at: dt.datetime | None = None
        self.snapshot = {"tasks": [], "read_at": None}
        self.lock = threading.Lock()

    def _json(self, args: list[str]):
        code, out, err = self.gh(args)
        if code != 0:
            detail = (err or out or "GitHub did not answer").strip().splitlines()[-1]
            raise GitHubReadFailed(detail)
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:
            raise GitHubReadFailed("GitHub returned unreadable JSON") from exc

    def _read_trees(self) -> list[dict]:
        maps = self._json(["issue", "list", "--state", "all", "--label", "mmw:map",
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
    def _comment_headers(output: str) -> tuple[int, dict[str, str], str]:
        normal = output.replace("\r\n", "\n")
        head, separator, body = normal.partition("\n\n")
        if not separator:
            raise GitHubReadFailed("the comments response had no HTTP headers")
        lines = head.splitlines()
        try:
            status = int(lines[0].split()[1].split(".")[0])
        except (IndexError, ValueError) as exc:
            raise GitHubReadFailed("the comments response had no HTTP status") from exc
        headers = {}
        for line in lines[1:]:
            name, found, value = line.partition(":")
            if found:
                headers[name.strip().lower()] = value.strip()
        return status, headers, body

    def _read_comment_page(self, number: int, endpoint: str,
                           etag: str | None) -> tuple[list[dict] | None, str | None, str | None]:
        args = ["api", "-i", endpoint, "-H", "Accept: application/vnd.github+json"]
        if etag:
            args += ["-H", f"If-None-Match: {etag}"]
        code, out, err = self.gh(args)
        status = None
        headers = {}
        body = ""
        if out:
            status, headers, body = self._comment_headers(out)
        if status == 304:
            return None, etag, None
        if code != 0:
            detail = (err or out or "GitHub did not answer").strip().splitlines()[-1]
            raise GitHubReadFailed(f"comments for #{number}: {detail}")
        if status != 200:
            raise GitHubReadFailed(f"comments for #{number}: HTTP {status}")
        try:
            comments = json.loads(body)
        except json.JSONDecodeError as exc:
            raise GitHubReadFailed(f"comments for #{number} were unreadable") from exc
        if not isinstance(comments, list):
            raise GitHubReadFailed(f"comments for #{number} were not an array")
        if not headers.get("etag"):
            raise GitHubReadFailed(f"comments for #{number} had no ETag")
        next_url = None
        for part in headers.get("link", "").split(","):
            if 'rel="next"' in part:
                start = part.find("<")
                end = part.find(">", start + 1)
                if start >= 0 and end > start:
                    next_url = part[start + 1:end]
        return comments, headers["etag"], next_url

    def _read_comments(self, number: int, pages: dict[str, list[dict]],
                       etags: dict[str, str], next_pages: dict[str, str | None]):
        endpoint = f"repos/{{owner}}/{{repo}}/issues/{number}/comments?per_page=100"
        visited = []
        while endpoint:
            result, etag, reported_next = self._read_comment_page(
                number, endpoint, etags.get(endpoint))
            if result is None:
                if endpoint not in pages:
                    raise GitHubReadFailed(f"comments for #{number} returned 304 without a cached page")
                next_url = next_pages.get(endpoint)
            else:
                pages[endpoint] = result
                next_url = reported_next
                next_pages[endpoint] = next_url
            if etag:
                etags[endpoint] = etag
            visited.append(endpoint)
            endpoint = next_url
        pages = {url: pages[url] for url in visited}
        etags = {url: etags[url] for url in visited if url in etags}
        next_pages = {url: next_pages.get(url) for url in visited}
        combined = [comment for url in visited for comment in pages[url]]
        return combined, pages, etags, next_pages

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
                "kind": next((label.split(":", 1)[1] for label in raw_map.get("labels", [])
                              if label.startswith("wayfinder:")), "map"),
                "title": raw_map["title"],
                "state": raw_map["state"].lower(),
                "decisions": [],
                "specs": [],
            }
            for child in raw_map.get("children", []):
                labels = child.get("labels", [])
                blockers = [item["number"] for item in child.get("blockedBy", [])]
                decision_kind = next((label.split(":", 1)[1] for label in labels
                                      if label.startswith("wayfinder:")), None)
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
                        "blockedBy": raw_ticket.get("blockedBy", []),
                        "blockers": [],
                        "blocker_hold": events.blocker_hold(raw_ticket["state"], folded),
                        "closeout": None,
                        "children": raw_ticket.get("children", []),
                        "fold": folded,
                        "events": _replay(ticket_comments),
                    }
                    spec["tickets"].append(ticket)
                    tickets_by_number[number] = ticket
                    specs_by_ticket[number] = spec["n"]
                task["specs"].append(spec)
            tasks.append(task)

        raw_blockers = {node["number"]: node for raw_map in map_trees
                        for spec in raw_map.get("children", [])
                        for node in spec.get("children", [])}
        for ticket in tickets_by_number.values():
            for reference in ticket["blockedBy"]:
                number = reference["number"]
                blocker = tickets_by_number.get(number)
                raw = raw_blockers.get(number, {})
                state = (blocker or raw or reference).get("state", "").upper()
                if not state:
                    state = str(reference.get("state") or "").upper()
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

    def answer(self, refresh: bool = False) -> dict:
        del refresh
        with self.lock:
            now = self.clock()
            map_trees = copy.deepcopy(self.map_trees)
            comments = copy.deepcopy(self.comments)
            comment_pages = copy.deepcopy(self.comment_pages)
            etags = copy.deepcopy(self.etags)
            next_pages = copy.deepcopy(self.next_pages)
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
                    if not flat:
                        plan["comments"] = [node["number"] for node in self._ticket_nodes(map_trees)]

                structural = False
                for number in plan["comments"]:
                    old_structural = _structural_keys(comments.get(number, []))
                    result, pages, tags, links = self._read_comments(
                        number, comment_pages.get(number, {}), etags.get(number, {}),
                        next_pages.get(number, {}))
                    comments[number] = result
                    comment_pages[number] = pages
                    etags[number] = tags
                    next_pages[number] = links
                    structural = structural or bool(_structural_keys(result) - old_structural)

                if structural and not first_read:
                    map_trees = self._read_trees()
                    last_tree_at = now
                new_numbers = [node["number"] for node in self._ticket_nodes(map_trees)
                               if node["number"] not in comments]
                for number in new_numbers:
                    result, pages, tags, links = self._read_comments(number, {}, {}, {})
                    comments[number] = result
                    comment_pages[number] = pages
                    etags[number] = tags
                    next_pages[number] = links

                snapshot = {"tasks": self._shape(map_trees, comments), "read_at": iso(now)}
            except GitHubReadFailed as exc:
                failed = copy.deepcopy(self.snapshot)
                failed["read_failed"] = {"at": iso(now), "message": str(exc)}
                return failed

            self.map_trees = map_trees
            self.comments = comments
            self.comment_pages = comment_pages
            self.etags = etags
            self.next_pages = next_pages
            self.last_tree_at = last_tree_at
            self.snapshot = snapshot
            return copy.deepcopy(snapshot)


STORE = BoardStore()


def handle(request) -> tuple[int, dict[str, str], bytes]:
    path = urllib.parse.urlsplit(request.path).path
    if request.command == "GET" and path == "/api/board":
        answer = STORE.answer()
    elif request.command == "POST" and path == "/api/board/refresh":
        answer = STORE.answer(refresh=True)
    else:
        body = b'{"error":"not found"}\n'
        return 404, {"Content-Type": "application/json"}, body
    body = (json.dumps(answer, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    return 200, {"Content-Type": "application/json; charset=utf-8"}, body
