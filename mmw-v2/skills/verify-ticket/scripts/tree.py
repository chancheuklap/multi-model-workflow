#!/usr/bin/env python3
"""The tree of issues under one issue, read with one GraphQL query.

    tree.py <issue> [--root map|spec|ticket]

The work is four layers deep — a map, its specs, each spec's tickets, each ticket's
children — and the tracker's sub-issue link is what joins each layer to the one above.
Read one list at a time over REST, that is one request per issue per layer, and a page
left unread raises no error: it reads exactly like an issue with fewer children. This
reads the whole tree below `<issue>` in one request, and refuses to answer when any list
came back shorter than the count the tracker gives for it.

Each layer is read at a fixed page size, the same wherever the tree is entered: at most 50
specs under a map, 100 tickets under a spec (the tracker's own cap on one issue's
children), and 50 children under a ticket. Entered at a map that is three nested lists,
50 × 100 × 50, and 255,050 nodes against the tracker's limit of 500,000 per query; one
more list at 100 would ask for a million, which the tracker refuses outright, and a page
over 100 is refused per list. `--root` says which layer `<issue>` is (default `spec`),
so the lists below it get their own layer's size.

Every issue comes back as its number, title and state; every issue with a layer below it
also as the tracker's own `total` and `completed` count of that layer.

Prints the tree as JSON and exits 0; exit 2, with the reason on stderr, when the tracker
could not be asked, answered with an error, has no such issue, or returned a list shorter
than its count.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

LAYERS = ("map", "spec", "ticket", "child")
# How many issues of a layer are read under the one issue above it.
PAGE = {"spec": 50, "ticket": 100, "child": 50}

GH_ENV = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR_FORCE", "CLICOLOR")}


class TreeUnreadable(RuntimeError):
    """The tree could not be read whole: the question went unanswered, or part of it did."""


def query(root: str = "spec") -> str:
    """The query for the tree below an issue of layer `root`."""
    if root not in LAYERS[:-1]:
        raise ValueError(f"`{root}` is not a layer with issues below it; one of "
                         f"{', '.join(LAYERS[:-1])}")
    below = list(LAYERS[LAYERS.index(root) + 1:])

    def level(layers: list[str], depth: int) -> str:
        pad = "  " * depth
        head, rest = layers[0], layers[1:]
        fields = "number title state"
        if rest:
            fields += " subIssuesSummary { total completed } " + level(rest, depth + 1)
        return (f"subIssues(first:{PAGE[head]}) {{ nodes {{\n"
                f"{pad}  {fields} }}}}")

    return ("query($o:String!, $n:String!, $root:Int!) {\n"
            "  repository(owner:$o, name:$n) {\n"
            "    issue(number:$root) {\n"
            "      number title state subIssuesSummary { total completed }\n"
            f"      {level(below, 3)}\n"
            "    }\n"
            "  }\n"
            "}\n")


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    run = subprocess.run(["gh", *args], capture_output=True, text=True, env=GH_ENV)
    return run.returncode, run.stdout, run.stderr


def _node(raw: dict, where: str) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("number"), int):
        raise TreeUnreadable(f"{where}: an issue came back with no number")
    node = {"number": raw["number"], "title": raw.get("title") or "",
            "state": (raw.get("state") or "").upper()}
    if "subIssues" in raw:
        summary = raw.get("subIssuesSummary") or {}
        nodes = (raw.get("subIssues") or {}).get("nodes")
        if not isinstance(nodes, list):
            raise TreeUnreadable(f"#{node['number']}: its sub-issues came back unreadable")
        total = summary.get("total")
        if not isinstance(total, int):
            raise TreeUnreadable(f"#{node['number']}: the tracker gave no count of its "
                                 f"sub-issues")
        if len(nodes) < total:
            raise TreeUnreadable(f"#{node['number']} has {total} sub-issues and {len(nodes)} "
                                 f"came back: the rest are past this query's page, and a "
                                 f"tree missing them would read as whole")
        node["total"] = total
        node["completed"] = summary.get("completed")
        node["children"] = [_node(child, f"under #{node['number']}") for child in nodes]
    return node


def read(number: int, root: str = "spec", gh=None) -> dict:
    """The tree below issue `number`, which is of layer `root`.

    `gh` runs one `gh` command and answers `(exit code, stdout, stderr)`; it is the one
    seam, and tests replace it. Raises `TreeUnreadable` rather than answer with part of
    the tree.
    """
    run = gh or _run_gh
    code, out, err = run(["api", "graphql", "-F", "o={owner}", "-F", "n={repo}",
                          "-F", f"root={number}", "-f", f"query={query(root)}"])
    try:
        data = json.loads(out) if (out or "").strip() else None
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and data.get("errors"):
        first = data["errors"][0] if isinstance(data["errors"], list) else data["errors"]
        message = first.get("message") if isinstance(first, dict) else str(first)
        raise TreeUnreadable(f"the tracker answered the tree of #{number} with an error: "
                             f"{message}")
    if code != 0 or not isinstance(data, dict):
        detail = (err or out or "").strip().splitlines()
        raise TreeUnreadable(f"`gh api graphql` for the tree of #{number} failed"
                             + (f": {detail[-1]}" if detail else ""))
    issue = ((data.get("data") or {}).get("repository") or {}).get("issue")
    if not isinstance(issue, dict):
        raise TreeUnreadable(f"the tracker has no issue #{number}")
    return _node(issue, f"#{number}")


def children(tree: dict) -> list[dict]:
    return list(tree.get("children") or [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tree.py", description=__doc__.splitlines()[0])
    parser.add_argument("issue", type=int)
    parser.add_argument("--root", choices=LAYERS[:-1], default="spec")
    args = parser.parse_args(argv)
    try:
        tree = read(args.issue, args.root)
    except TreeUnreadable as exc:
        sys.stderr.write(f"tree: {exc}\n")
        return 2
    print(json.dumps(tree, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
