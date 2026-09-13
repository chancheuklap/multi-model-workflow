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
DRIVE_TARGET_SCRIPTS = ROOT / "mmw-v2" / "skills" / "drive-target" / "scripts"
sys.path.insert(0, str(DISPATCH_SCRIPTS))
sys.path.insert(0, str(DRIVE_TARGET_SCRIPTS))
import models  # noqa: E402
import statedir  # noqa: E402
from refusal import REPORT_BLOCKED, refusal as refusal_message  # noqa: E402

RESULTS = frozenset({"verifier.passed", "verifier.failed", "verifier.lost"})
RETIRED = RESULTS | {"verifier.started"}
BLOCK = re.compile(r"\n*<!--\s*mmw\s+(\{[^\n]*\})\s*-->\s*$")
REMOTE = re.compile(r"(?:github\.com[:/])([^/]+)/([^/]+?)(?:\.git)?$")


class Refusal(RuntimeError):
    pass


def refuse(what: str, why: str, next_step: str) -> None:
    raise Refusal(refusal_message(what, why, next_step))


def gh_json(*args: str):
    run = subprocess.run(["gh", "api", *args], text=True, capture_output=True)
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip() or f"exit {run.returncode}"
        refuse(f"gh api {' '.join(args)} failed: {detail}",
               "the migration cannot audit every affected issue comment.",
               "Restore GitHub access, then rerun this command.")
    try:
        return json.loads(run.stdout or "null")
    except json.JSONDecodeError as exc:
        refuse(f"gh api {' '.join(args)} returned unreadable JSON: {exc.msg}.",
               "the migration cannot identify the affected comments safely.",
               "Restore a readable GitHub response, then rerun this command.")


def repo_name(path: Path) -> str:
    run = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"],
                         text=True, capture_output=True)
    remote = run.stdout.strip()
    found = REMOTE.search(remote)
    if run.returncode != 0 or not found:
        refuse(f"{path} has no readable GitHub origin.",
               "its issue comments cannot be checked.",
               f"Restore that repository's GitHub origin, then rerun this command.")
    return f"{found.group(1)}/{found.group(2)}"


def repository_paths() -> list[Path]:
    boards_path = statedir.home() / "boards.json"
    try:
        boards = statedir.read_json(boards_path, {})
    except (OSError, ValueError) as exc:
        refuse(f"{boards_path} cannot be read: {exc}.",
               "the migration cannot name every registered repository.",
               f"Repair {boards_path}, then rerun this command.")
    if not isinstance(boards, dict):
        refuse(f"{boards_path} is not an object of repository paths.",
               "the migration cannot name every registered repository.",
               f"Repair {boards_path}, then rerun this command.")
    paths = [Path(path).resolve() for path in boards]
    paths.append(ROOT.resolve())
    return list(dict.fromkeys(paths))


def assert_no_open_watch() -> None:
    state_root = statedir.home() / "state"
    for path in sorted(state_root.glob("*/watches.json")):
        try:
            watches = statedir.read_json(path, {})
        except (OSError, ValueError) as exc:
            refuse(f"{path} cannot be read: {exc}.",
                   "whether a night is open is unknown.",
                   f"Repair {path}, then rerun this command.")
        if watches:
            refuse(f"{path} contains {len(watches)} open watch(es).",
                   "migration while a night is active would erase events its sessions still read.",
                   "Close the night, then rerun this command.")


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
        refuse(f"{repo} did not return lists for comments and open issues.",
               "the migration cannot audit its open verification sessions.",
               "Restore readable GitHub API responses, then rerun this command.")
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
                refuse(f"{repo} returned a retired event comment without a numeric id.",
                       "that comment has no safe PATCH target.", REPORT_BLOCKED)
            retired.append(item)
            if number is not None:
                per_issue[number].append((comment["id"], event))
    for number in sorted(open_numbers):
        pending = False
        for _, event in sorted(per_issue.get(number, [])):
            if event == "verifier.started":
                pending = True
            elif event in RESULTS:
                pending = False
        if pending:
            refuse(f"{repo}#{number} is open with a verifier.started that has no result.",
                   "removing it would erase an active session's hold.",
                   "Finish that run, then rerun this command.")
    return {"repo": repo, "comments": retired}


def edit_comment(repo: str, comment: dict) -> None:
    run = subprocess.run(["gh", "api", "--method", "PATCH",
                          f"repos/{repo}/issues/comments/{comment['id']}",
                          "-f", f"body={comment['body']}"], text=True, capture_output=True)
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip() or f"exit {run.returncode}"
        refuse(f"Could not edit {repo} comment {comment['id']}: {detail}.",
               "the retired event block remains on that comment.",
               "Rerun this command; comments already edited are safe no-ops.")


def migrated_models_text() -> str | None:
    path = models.models_json_path()
    try:
        config = models.read_local_config()
    except (models.ConfigMissing, OSError, ValueError) as exc:
        refuse(f"{path} cannot be prepared for migration: {exc}.",
               "the role configuration cannot be replaced safely.",
               f"Repair {path}, then rerun this command.")
    rows = config.get("rows")
    if not isinstance(rows, dict):
        refuse(f"{path} has no rows object.",
               "the retired role cannot be removed safely.",
               f"Repair {path}, then rerun this command.")
    if "verifier" not in rows:
        return None
    version = config.get("version")
    if not isinstance(version, int):
        refuse(f"{path} has no integer version.",
               "a board already displaying the configuration could accept stale data.",
               f"Repair {path}, then rerun this command.")
    updated = dict(config)
    updated["version"] = version + 1
    updated["rows"] = dict(rows)
    del updated["rows"]["verifier"]
    return json.dumps(updated, ensure_ascii=False, indent=2) + "\n"


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
            models_text = migrated_models_text()
            for item in scans:
                for comment in item["comments"]:
                    edit_comment(item["repo"], comment)
            if models_text is not None:
                statedir.write_atomic(models.models_json_path(), models_text)
    except statedir.LockHeld as exc:
        refuse(str(exc), "configuration writes must be serialized.",
               "Rerun after that process releases the lock.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        return run(args.dry_run)
    except Refusal as exc:
        print(f"remove-verifier: {exc}", file=sys.stderr)
        return 2
    except (OSError, models.ConfigMissing, ValueError) as exc:
        message = refusal_message(f"The migration stopped on {type(exc).__name__}: {exc}.",
                                  "it could not complete safely.", REPORT_BLOCKED)
        print(f"remove-verifier: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
