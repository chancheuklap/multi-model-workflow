#!/usr/bin/env python3
"""Create every label the landing pipeline puts on an issue that this repository lacks.

    python3 labels.py
    python3 labels.py --migrate

Run from inside a clone; origin selects the repository. The set, with each colour and
description, is the one table in the `verify-ticket` skill's `scripts/verify-ticket.py`:
the layer, queue, grade and wayfinder labels. This is the only place a label of that set is
created; every script that puts one on asks first and refuses when the repository lacks it.

Without --migrate, a label the repository already has is left exactly as it is, even when its colour or
description differs from the table: nothing reads either, and the repository's own choice
stands. Those differences are printed, one line each.

Prints one line per label created and per difference, then `LABELS OK <n>` with the size
of the set. Exit 0 when the repository has every label afterwards; 1 when a read or a
create failed, with `gh`'s reason.

--migrate first creates missing labels and updates needs-triage's description, then
migrates open issues using the label state machine. It never deletes a label. Each
changed issue prints its number, labels added and removed, and the rule used. The last
line is MIGRATE OK <n> changed. Read or write failures exit 1 without rolling back
completed changes. A failed issue is reported without stopping the other issues;
rerunning handles only the remaining issues. Run after release to
the installed checkout, with no night or one-ticket watch open.
"""
import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

VERIFY = Path(__file__).resolve().parents[2] / "verify-ticket" / "scripts" / "verify-ticket.py"
sys.path.insert(0, str(VERIFY.parents[2] / "dispatch" / "scripts"))
import tracker


def verify_module():
    spec = importlib.util.spec_from_file_location("verify_ticket", VERIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def label_table() -> dict[str, tuple[str, str]]:
    """Every label of the pipeline, name to (colour, description), from verify-ticket.py."""
    module = verify_module()
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
        state = module.events.fold(comments, issue=number)
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
    module = verify_module()
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
