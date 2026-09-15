#!/usr/bin/env python3
"""A fake Space: only memories and call order, with a one-shot add failure."""
import json
import os
import sys
from pathlib import Path

path = Path(os.environ["RETRO_NMEM_STATE"])
state = json.loads(path.read_text(encoding="utf-8"))
args = [arg for arg in sys.argv[1:] if arg != "--json"]
state.setdefault("calls", []).append(args)


def save():
    path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def response(value):
    save()
    print(json.dumps(value, ensure_ascii=False))


if args[:2] == ["spaces", "show"]:
    response({"id": args[2], "defaultRetrievalMode": "shared",
              "sharedSpaceIds": ["mmw-toolbox"]})
elif args[:2] == ["memories", "list"]:
    rows = list(state.get("memories", {}).values())[::-1]
    limit = int(args[args.index("--limit") + 1])
    response({"memories": rows[:limit], "total": len(rows), "returned": len(rows[:limit])})
elif args[:2] == ["memories", "show"]:
    row = state.get("memories", {}).get(args[2])
    if not row:
        print("Memory missing", file=sys.stderr)
        sys.exit(1)
    response(row)
elif args[:2] == ["memories", "search"]:
    query = args[2]
    rows = [row for row in state.get("memories", {}).values() if
            all(word.lower() in row["content"].lower() for word in query.split())]
    response({"memories": rows, "total": len(rows), "returned": len(rows)})
elif args[:2] == ["memories", "add"]:
    content = sys.stdin.read()
    if state.get("fail_add_once"):
        state["fail_add_once"] = False
        save()
        print("injected Memory write failure", file=sys.stderr)
        sys.exit(1)
    ident = args[args.index("--id") + 1]
    row = {"id": ident, "content": content,
           "space_id": args[args.index("--space") + 1],
           "labels": [args[args.index("--label") + 1]],
           "unit_type": args[args.index("--unit-type") + 1]}
    state.setdefault("memories", {})[ident] = row
    response(row)
else:
    save()
    print(f"unexpected nmem: {args}", file=sys.stderr)
    sys.exit(2)
