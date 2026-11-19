#!/usr/bin/env python3
"""Create missing v5 issue labels without replacing repository-owned choices.

Run from the consuming repository. --migrate applies the existing label-state
migration to open issues; it never deletes labels or runs acceptance commands.
"""
import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

DEFINITIONS = Path(__file__).resolve().parents[2] / "verify-ticket" / "scripts" / "labels.py"
sys.path.insert(0, str(DEFINITIONS.parents[2] / "dispatch" / "scripts"))
import tracker

_event_spec = importlib.util.spec_from_file_location("mmw_v5_label_events", DEFINITIONS.with_name("events.py"))
events = importlib.util.module_from_spec(_event_spec)
_event_spec.loader.exec_module(events)


def label_definitions():
    spec = importlib.util.spec_from_file_location("mmw_v5_labels", DEFINITIONS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def label_table() -> dict[str, tuple[str, str]]:
    """Every label of the pipeline, name to (colour, description), from the shared labels.py definitions."""
    module = label_definitions()
    table: dict[str, tuple[str, str]] = {}
    for part in (module.CLASS_LABELS, module.QUEUE_LABELS, module.GRADE_LABELS,
                 module.WAYFINDER_LABELS):
        table.update(part)
    return table


def gh(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["gh", *args], capture_output=True, text=True, env=tracker.environment())
    except (OSError, tracker.RepositoryError) as exc:
        return subprocess.CompletedProcess(["gh", *args], 127, "", str(exc))


def reason(proc: subprocess.CompletedProcess) -> str:
    return (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip().replace("\n", "; ")


def existing() -> dict[str, tuple[str, str]] | str:
    """The repository's labels, name to (colour, description); the reason when unreadable."""
    proc = gh(["label", "list", "--limit", "1000", "--json", "name,color,description"])
    if proc.returncode != 0:
        return reason(proc)
    try:
        rows = json.loads(proc.stdout)
    except ValueError:
        return f"gh label list did not return JSON ({proc.stdout.strip()[:80]})"
    return {row["name"]: (row.get("color", ""), row.get("description", "")) for row in rows}


class MigrationError(RuntimeError):
    pass


def read_json(args: list[str]):
    proc = gh(args)
    if proc.returncode != 0:
        raise MigrationError(f"gh {' '.join(args)} failed: {reason(proc)}")
    try:
        return json.loads(proc.stdout)
    except ValueError:
        raise MigrationError(f"gh {' '.join(args)} did not return JSON") from None


def pages(path: str) -> list[dict]:
    data = read_json(["api", "--paginate", "--slurp", path])
    if not isinstance(data, list) or any(not isinstance(page, list) for page in data):
        raise MigrationError(f"gh api {path} did not return pages of rows")
    rows = [row for page in data for row in page]
    if any(not isinstance(row, dict) for row in rows):
        raise MigrationError(f"gh api {path} did not return issue or comment objects")
    return rows


def migrate_issue(module, row: dict) -> bool:
    if "pull_request" in row:
        return False
    number = row["number"]
    names = {label["name"] for label in row["labels"]}
    if "needs-info" in names:
        print(f"NEEDS-INFO #{number}: left for the owner")
        return False
    if "mmw:child" in names:
        return False
    if names.intersection(module.WAYFINDER_LABELS):
        return False
    remove = []
    if "mmw:ticket" in names:
        parent = read_json(["issue", "view", str(number), "--json", "parent"])["parent"]
        if parent:
            parent_labels = read_json(["issue", "view", str(parent["number"]), "--json", "labels"])["labels"]
            if any(label["name"] == "mmw:spec" for label in parent_labels):
                return False
        comments = pages(f"repos/{{owner}}/{{repo}}/issues/{number}/comments?per_page=100")
        state = events.fold(comments, issue=number)
        if state["unreadable"]:
            raise MigrationError(f"could not read events of #{number}: {state['unreadable']}")
        if any(event["event"] in ("ticket.claimed", "worker.started") for event in state["events"]):
            return False
        rule = 2
        remove = ["--remove-label", "mmw:ticket"]
    elif "needs-triage" in names and not names.intersection(module.CLASS_LABELS):
        if not re.search(r"^## Problem\s*$", row.get("body") or "", re.MULTILINE):
            print(f"SKIP #{number}: not opened by MMW")
            return False
        rule = 1
    else:
        return False
    proc = gh(["issue", "edit", str(number), "--add-label", "mmw:problem", *remove])
    if proc.returncode != 0:
        raise MigrationError(f"could not edit #{number} by rule {rule}: {reason(proc)}")
    print(f"#{number}: added mmw:problem; removed {'mmw:ticket' if remove else 'none'}; rule {rule}")
    return True


def migrate() -> tuple[int, int]:
    module = label_definitions()
    changed = 0
    failed = 0
    for row in pages("repos/{owner}/{repo}/issues?state=open&per_page=100"):
        try:
            changed += migrate_issue(module, row)
        except (MigrationError, KeyError, TypeError, AttributeError) as exc:
            print(f"could not migrate #{row.get('number', '?')}: {exc}", file=sys.stderr)
            failed += 1
    return changed, failed


def main(argv=()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--migrate", action="store_true", help="migrate open issues to the label state machine")
    args = parser.parse_args(argv)
    table = label_table()
    have = existing()
    if isinstance(have, str):
        print(f"could not read the repository's labels: {have}", file=sys.stderr)
        return 1
    failed = 0
    for name, (color, description) in table.items():
        if name in have:
            got_color, got_description = have[name]
            if args.migrate and name == "needs-triage" and got_description != description:
                proc = gh(["label", "edit", name, "--description", description])
                if proc.returncode != 0:
                    print(f"could not edit {name}: {reason(proc)}", file=sys.stderr)
                    failed += 1
                else:
                    print(f"updated {name} description")
                continue
            if (got_color.lower(), got_description) != (color.lower(), description):
                print(f"kept {name}: the repository has colour {got_color} and description "
                      f"{got_description!r}; the table has {color} and {description!r}")
            continue
        proc = gh(["label", "create", name, "--color", color, "--description", description])
        if proc.returncode != 0:
            print(f"could not create {name}: {reason(proc)}", file=sys.stderr)
            failed += 1
            continue
        print(f"created {name}")
    if failed:
        return 1
    if args.migrate:
        try:
            changed, failed = migrate()
        except (MigrationError, KeyError, TypeError, AttributeError) as exc:
            print(f"could not migrate the repository's issues: {exc}", file=sys.stderr)
            return 1
        if failed:
            return 1
        print(f"MIGRATE OK {changed} changed")
    else:
        print(f"LABELS OK {len(table)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
