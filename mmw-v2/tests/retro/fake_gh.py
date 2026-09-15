#!/usr/bin/env python3
"""A fake tracker with issue bodies, native tree, comments and proposal state."""
import json
import os
import sys
from pathlib import Path

path = Path(os.environ["RETRO_GH_STATE"])
state = json.loads(path.read_text(encoding="utf-8"))
args = sys.argv[1:]
state.setdefault("calls", []).append(args)
with Path(os.environ["RETRO_TRACE_PATH"]).open("a", encoding="utf-8") as trace:
    trace.write(json.dumps({"source": "gh", "args": args}) + "\n")


def save():
    path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def option(name, default=""):
    return args[args.index(name) + 1] if name in args else default


def response(value):
    save()
    print(json.dumps(value, ensure_ascii=False))


if args[:2] == ["issue", "view"]:
    number = args[2]
    row = state["issues"].get(number)
    if row is None:
        print(f"no issue #{number}", file=sys.stderr)
        sys.exit(1)
    fields = option("--json", "").split(",")
    response({key: row.get(key) for key in fields})
elif args[:2] == ["api", "graphql"]:
    number = next(arg.split("root=", 1)[1] for arg in args if arg.startswith("root="))
    row = state["tree"]
    if int(number) != row["number"]:
        print("wrong tree root", file=sys.stderr)
        sys.exit(1)
    sizing = any("subIssuesSummary { total }" in arg for arg in args)
    if sizing:
        row = {"subIssuesSummary": row["subIssuesSummary"],
               "subIssues": {"nodes": [
                   {"subIssuesSummary": x["subIssuesSummary"]} for x in row["subIssues"]["nodes"]]}}
    response({"data": {"repository": {"issue": row}}})
elif args[:1] == ["api"] and "/issues/comments/" in args[1]:
    ident = args[1].rsplit("/", 1)[-1]
    found = next((c for issue in state["issues"].values() for c in issue.get("comments", [])
                  if str(c["id"]) == ident), None)
    if not found:
        print(f"comment {ident} not found", file=sys.stderr)
        sys.exit(1)
    response(found)
elif args[:2] == ["issue", "list"]:
    repo = option("--repo")
    response([x for x in state.get("proposals", []) if x["repository"] == repo])
elif args[:2] == ["issue", "create"]:
    number = 900 + len(state.get("proposals", []))
    repo = option("--repo")
    row = {"repository": repo, "number": number,
           "url": f"https://github.com/{repo}/issues/{number}",
           "body": sys.stdin.read(), "title": option("--title"),
           "labels": [option("--label")]}
    state.setdefault("proposals", []).append(row)
    save()
    print(row["url"])
elif args[:2] == ["issue", "comment"]:
    number = args[2]
    body = sys.stdin.read()
    ident = state.get("next_comment", 5000)
    state["next_comment"] = ident + 1
    repo = state["repository"]
    state["issues"][number]["comments"].append({
        "id": ident, "body": body,
        "url": f"https://github.com/{repo}/issues/{number}#issuecomment-{ident}"})
    save()
    print(f"https://github.com/{repo}/issues/{number}#issuecomment-{ident}")
else:
    save()
    print(f"unexpected gh: {args}", file=sys.stderr)
    sys.exit(2)
