"""Lint a screen contract against the handoff skeleton and, when given, openapi.json.

Usage: uv run python lint_contract.py <screen-contract.yaml> <skeleton.json> [<openapi.json>]
Exit 0 with no errors; 1 with errors listed one per line; warnings never fail.
Rules are the table in ../references/contract-format.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

GAPS = {"aligned", "design-only", "backend-only"}
REACH = re.compile(r"^(seed|stub|dev):[a-z0-9][a-z0-9-]*$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")


def lint(doc: dict, skeleton: dict, openapi: dict | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = doc.get("rows") or []
    mechanisms = set(doc.get("mechanisms") or [])
    # retired_ids entries are either a bare id or {id, note, trigger?}; a retired entry that names
    # its trigger says the handoff still shows a control the product no longer has.
    retired_entries = [e if isinstance(e, dict) else {"id": e} for e in doc.get("retired_ids") or []]
    retired = {str(e.get("id")) for e in retired_entries}
    retired_triggers = {(e["trigger"].get("role"), e["trigger"].get("name"))
                        for e in retired_entries if isinstance(e.get("trigger"), dict)}
    # A control shared by several pages is one key; its scenes are the union over those pages.
    triggers: dict[tuple[str, str], set[str]] = {}
    for r in skeleton["table"]:
        triggers.setdefault((r["role"], r["name"]), set()).update(r["scenes"])
    ops = ({(m.upper(), p) for p, methods in openapi["paths"].items() for m in methods}
           if openapi else None)
    proposed = {tuple(str(o).split(" ", 1)) for o in doc.get("proposed_operations") or []}
    proposed = {(m.upper(), p) for m, p in proposed}

    def op_known(method: str, path: str) -> str:
        """'yes' when openapi has it, 'proposed' when proposed_operations lists it, else 'no'."""
        if ops is not None and (method.upper(), path) in ops:
            return "yes"
        if (method.upper(), path) in proposed:
            return "proposed"
        return "no"

    seen_ids: set[str] = set()
    seen_triggers: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        rid = str(row.get("id", "<no id>"))
        if not ID.match(rid):
            errors.append(f"{rid}: id must look like <component>.<behaviour>")
        if rid in seen_ids:
            errors.append(f"{rid}: duplicate id")
        seen_ids.add(rid)
        if rid in retired:
            errors.append(f"{rid}: id is in retired_ids and still has a row")
        t = row.get("trigger") or {}
        key = (t.get("role"), t.get("name"))
        if key not in triggers:
            errors.append(f"{rid}: trigger {key[0]} {key[1]!r} not in handoff skeleton")
        else:
            if not (row.get("scenes") or []):
                warnings.append(f"{rid}: scenes is [] — the handoff shows no scene for this precondition")
            for sc in row.get("scenes") or []:
                if sc not in triggers[key]:
                    errors.append(f"{rid}: scene {sc!r} does not show this trigger in the skeleton")
        seen_triggers.setdefault(key, []).append(row.get("precondition") or {})
        calls = row.get("calls") or []
        if not calls:
            errors.append(f"{rid}: calls is empty (use [none])")
        for call in calls:
            if call == "none" or str(call).startswith("ipc "):
                continue
            method, _, path = str(call).partition(" ")
            known = op_known(method, path)
            if known == "proposed":
                warnings.append(f"{rid}: call is a proposed operation, not in openapi yet: {call}")
            elif ops is None:
                warnings.append(f"{rid}: call unverified (no openapi.json): {call}")
            elif known == "no":
                errors.append(f"{rid}: call not in openapi: {call}")
        if calls != ["none"] and not (row.get("on_failure") or {}):
            errors.append(f"{rid}: on_failure missing for a row with calls")
        if calls != ["none"]:
            if not row.get("route"):
                errors.append(f"{rid}: route missing for a row with calls")
            observe = row.get("observe") or []
            ipc_only = all(str(c).startswith("ipc ") for c in calls)
            if not observe and ipc_only:
                warnings.append(f"{rid}: observe is empty on an ipc-only row; the wiring check reads nothing")
            elif not observe:
                errors.append(f"{rid}: observe missing for a row with calls; a wiring check has nothing to read")
            for line in observe:
                op, arrow, _ = str(line).partition("->")
                method, _, path = op.strip().partition(" ")
                if not arrow:
                    errors.append(f"{rid}: observe line has no '->' expression: {line}")
                else:
                    known = op_known(method, path)
                    if known == "proposed":
                        warnings.append(f"{rid}: observe reads a proposed operation: {op.strip()}")
                    elif ops is not None and known == "no":
                        errors.append(f"{rid}: observe operation not in openapi: {op.strip()}")
        for shown, expr in (row.get("shows") or {}).items():
            if "@" not in str(expr):
                errors.append(f"{rid}: shows.{shown} names no field@operation: {expr!r}")
            if re.search(r"(?<![\w{])\d+(?![\w}])", str(expr)):
                errors.append(f"{rid}: shows.{shown} carries a literal number: {expr!r}")
        if not row.get("source"):
            errors.append(f"{rid}: source is empty")
        elif row.get("gap") == "aligned" and all(
                "README" in str(s) or str(s).startswith("code:") for s in row["source"]):
            errors.append(f"{rid}: aligned but every source is the README or code:")
        reach = str(row.get("reach", ""))
        if not REACH.match(reach):
            errors.append(f"{rid}: reach {reach!r} is not seed:/stub:/dev: plus a name")
        elif reach not in mechanisms:
            errors.append(f"{rid}: reach {reach!r} not in mechanisms")
        gap = row.get("gap")
        if gap not in GAPS:
            errors.append(f"{rid}: gap {gap!r} not one of {sorted(GAPS)}")
        elif gap != "aligned":
            errors.append(f"{rid}: gap {gap} unresolved")

    for key, pres in seen_triggers.items():
        if len(pres) > 1 and len({json.dumps(p, sort_keys=True, ensure_ascii=False) for p in pres}) < len(pres):
            errors.append(f"trigger {key[0]} {key[1]!r}: rows share a precondition")
    # Completeness is judged per page: every control of a page the contract covers needs a
    # row. Pages the contract does not touch at all are reported once, as a warning.
    controls = {(r["page"], r["role"], r["name"]) for r in skeleton["table"]}
    covered_pages = {page for page, role, name in controls if (role, name) in seen_triggers}
    untouched = sorted({r["page"] for r in skeleton["table"]} - covered_pages)
    for page, role, name in sorted(controls):
        if (role, name) in retired_triggers:
            continue
        if page in covered_pages and (role, name) not in seen_triggers:
            errors.append(f"skeleton control without a row: {page} / {role} {name!r}")
    for page in untouched:
        warnings.append(f"page has no rows yet: {page}")
    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) not in (3, 4):
        print(__doc__)
        return 2
    doc = yaml.safe_load(Path(argv[1]).read_text(encoding="utf-8"))
    skeleton = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    openapi = json.loads(Path(argv[3]).read_text(encoding="utf-8")) if len(argv) == 4 else None
    errors, warnings = lint(doc, skeleton, openapi)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} errors, {len(warnings)} warnings over {len(doc.get('rows') or [])} rows")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
