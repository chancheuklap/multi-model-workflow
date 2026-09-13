#!/usr/bin/env python3
"""Remove retired verification-session events and its local model row once."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCH_SCRIPTS = ROOT / "mmw-v2" / "skills" / "dispatch" / "scripts"
sys.path.insert(0, str(DISPATCH_SCRIPTS))
import models  # noqa: E402
import statedir  # noqa: E402

RETIRED = frozenset({
    "verifier.started", "verifier.passed", "verifier.failed", "verifier.lost",
})
RESULTS = frozenset({"verifier.passed", "verifier.failed", "verifier.lost"})
BLOCK = re.compile(r"\n*<!--\s*mmw\s+(\{[^\n]*\})\s*-->\s*$")
REMOTE = re.compile(r"(?:github\.com[:/])([^/]+)/([^/]+?)(?:\.git)?$")


class Refusal(RuntimeError):
    pass


def gh_json(*args: str):
    run = subprocess.run(["gh", "api", *args], text=True, capture_output=True)
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip() or f"exit {run.returncode}"
        raise Refusal(f"gh api {' '.join(args)} failed: {detail}")
    try:
        return json.loads(run.stdout or "null")
    except json.JSONDecodeError as exc:
        raise Refusal(f"gh api {' '.join(args)} returned unreadable JSON: {exc.msg}") from None


def repo_name(path: Path) -> str:
    run = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"],
                         text=True, capture_output=True)
    remote = run.stdout.strip()
    found = REMOTE.search(remote)
    if run.returncode != 0 or not found:
        raise Refusal(f"{path} has no GitHub origin, so its issue comments cannot be checked")
    return f"{found.group(1)}/{found.group(2)}"


def repository_paths() -> list[Path]:
    boards_path = statedir.home() / "boards.json"
    try:
        boards = statedir.read_json(boards_path, {})
    except (OSError, ValueError) as exc:
        raise Refusal(f"{boards_path} cannot be read: {exc}") from None
    if not isinstance(boards, dict):
        raise Refusal(f"{boards_path} is not an object of repository paths")
    paths = [Path(path).resolve() for path in boards]
    paths.append(ROOT.resolve())
    return list(dict.fromkeys(paths))


def assert_no_open_watch() -> None:
    state_root = statedir.home() / "state"
    for path in sorted(state_root.glob("*/watches.json")):
        try:
            watches = statedir.read_json(path, {})
        except (OSError, ValueError) as exc:
            raise Refusal(f"{path} cannot be read, so whether a night is open is unknown: {exc}")
        if watches:
            raise Refusal(f"{path} contains {len(watches)} open watch(es); close the night, then rerun")


def event_at_end(body: str) -> tuple[str | None, re.Match | None]:
    found = BLOCK.search(body or "")
    if not found:
        return None, None
    try:
        payload = json.loads(found.group(1))
    except json.JSONDecodeError:
        return None, None
    return payload.get("event"), found


def scan(repo: str) -> dict:
    comments = gh_json("--paginate", f"repos/{repo}/issues/comments?per_page=100")
    issues = gh_json("--paginate", f"repos/{repo}/issues?state=open&per_page=100")
    if not isinstance(comments, list) or not isinstance(issues, list):
        raise Refusal(f"{repo} did not return lists for comments and open issues")
    open_numbers = {int(item["number"]) for item in issues
                    if isinstance(item, dict) and "pull_request" not in item
                    and isinstance(item.get("number"), int)}
    retired = []
    per_issue = defaultdict(list)
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        body = comment.get("body") or ""
        event, match = event_at_end(body)
        issue_url = str(comment.get("issue_url") or "")
        number = int(issue_url.rsplit("/", 1)[-1]) if issue_url.rsplit("/", 1)[-1].isdigit() else None
        if event in RETIRED and match is not None:
            item = {"id": comment.get("id"), "body": body[:match.start()].rstrip() + "\n",
                    "event": event, "number": number}
            if not isinstance(item["id"], int):
                raise Refusal(f"{repo} returned a retired event comment without a numeric id")
            retired.append(item)
            if number is not None:
                per_issue[number].append((int(comment.get("id")), event))
    for number in sorted(open_numbers):
        pending = False
        for _, event in sorted(per_issue.get(number, [])):
            if event == "verifier.started":
                pending = True
            elif event in RESULTS:
                pending = False
        if pending:
            raise Refusal(f"{repo}#{number} is open with a verifier.started that has no result; finish that run, then rerun")
    return {"repo": repo, "comments": retired}


def edit_comment(repo: str, comment: dict) -> None:
    run = subprocess.run(["gh", "api", "--method", "PATCH",
                          f"repos/{repo}/issues/comments/{comment['id']}",
                          "-f", f"body={comment['body']}"], text=True, capture_output=True)
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip() or f"exit {run.returncode}"
        raise Refusal(f"could not edit {repo} comment {comment['id']}: {detail}")


def migrate_models() -> None:
    path = models.models_json_path()
    config = models.read_local_config()
    rows = config.get("rows")
    if not isinstance(rows, dict):
        raise Refusal(f"{path} has no rows object; nothing was changed")
    if "verifier" not in rows:
        return
    updated = dict(config)
    updated["rows"] = dict(rows)
    del updated["rows"]["verifier"]
    statedir.write_atomic(path, json.dumps(updated, ensure_ascii=False, indent=2) + "\n")


def run(dry_run: bool) -> int:
    assert_no_open_watch()
    scans = []
    seen = set()
    for path in repository_paths():
        repo = repo_name(path)
        if repo not in seen:
            scans.append(scan(repo))
            seen.add(repo)
    for item in scans:
        print(f"{item['repo']}: {len(item['comments'])} comment(s)")
    if dry_run:
        return 0
    try:
        with models.config_lock(purpose="remove retired verification role"):
            for item in scans:
                for comment in item["comments"]:
                    edit_comment(item["repo"], comment)
            migrate_models()
    except models.ConfigLockHeld as exc:
        raise Refusal(str(exc)) from None
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        return run(args.dry_run)
    except (OSError, Refusal, models.ConfigMissing, ValueError) as exc:
        print(f"remove-verifier: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
