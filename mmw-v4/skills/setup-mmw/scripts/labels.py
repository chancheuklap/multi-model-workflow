#!/usr/bin/env python3
"""Create every label the landing pipeline puts on an issue that this repository lacks.

    python3 labels.py

Run from inside a clone; `gh` infers the repository. The set, with each colour and
description, is the one table in the `verify-ticket` skill's `scripts/verify-ticket.py`:
the layer, queue, grade and wayfinder labels. This is the only place a label of that set is
created; every script that puts one on asks first and refuses when the repository lacks it.

A label the repository already has is left exactly as it is, even when its colour or
description differs from the table: nothing reads either, and the repository's own choice
stands. Those differences are printed, one line each.

Prints one line per label created and per difference, then `LABELS OK <n>` with the size
of the set. Exit 0 when the repository has every label afterwards; 1 when a read or a
create failed, with `gh`'s reason.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

VERIFY = Path(__file__).resolve().parents[2] / "verify-ticket" / "scripts" / "verify-ticket.py"


def label_table() -> dict[str, tuple[str, str]]:
    """Every label of the pipeline, name to (colour, description), from verify-ticket.py."""
    spec = importlib.util.spec_from_file_location("verify_ticket", VERIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    table: dict[str, tuple[str, str]] = {}
    for part in (module.CLASS_LABELS, module.QUEUE_LABELS, module.GRADE_LABELS,
                 module.WAYFINDER_LABELS):
        table.update(part)
    return table


def gh(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


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


def main() -> int:
    table = label_table()
    have = existing()
    if isinstance(have, str):
        print(f"could not read the repository's labels: {have}", file=sys.stderr)
        return 1
    failed = 0
    for name, (color, description) in table.items():
        if name in have:
            got_color, got_description = have[name]
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
    print(f"LABELS OK {len(table)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
