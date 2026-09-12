#!/usr/bin/env python3
"""The tree of issues under one issue, read at the size that tree really is.

    tree.py <issue> [--root map|spec|ticket]

The work is four layers deep — a map, its specs, each spec's tickets, each ticket's
children — and the tracker's sub-issue link is what joins each layer to the one above.
Read one list at a time over REST, that is one request per issue per layer, and a page
left unread raises no error: it reads exactly like an issue with fewer children. This
reads the whole tree below `<issue>` in GraphQL, and refuses to answer when any list came
back shorter than the count the tracker gives for it. `--root` says which layer `<issue>`
is (default `spec`), so the lists below it get their own layer's size.

The tracker prices a query by what it asks for, never by what comes back: each list is
charged as though it came back full, the charges are added up and divided by a hundred.
A map with every list at its largest page is 15,151 requests, 152 of the 5,000 points an
hour one user has — the same 152 whether the map holds three specs or fifty. So a read
priced over `SIZING_WORTH` asks a cheaper question first: the counts of the layers below,
one point, and then the tree with every list at the size those counts give. A real map of
24 children with at most 13 tickets under a spec cost 1 + 10 that way, for an answer
byte-identical to the 152-point one. The counts can go stale between the two questions,
and a list that comes back short of its count is read again at the largest pages, so the
answer is never smaller than the largest pages alone would have given.

`PAGE` holds those largest pages: 50 specs under a map, 100 tickets under a spec (the
tracker's own cap on one list), 50 children under a ticket. That is 356,050 nodes against
the tracker's limit of 500,000 per query; one more list at 100 would ask for a million,
which it refuses outright, and a page over 100 is refused per list.

Every issue comes back as its number, title and state; specs and tickets also carry their
labels and blockers, and every issue with a layer below it carries the tracker's own
`total` and `completed` count of that layer. Labels and blockers are capped at ten per
issue so the largest map remains below the tracker's 500,000-node query limit. These
metadata lists may be capped: unlike missing sub-issues, their first ten entries preserve
the output shape used by existing readers without making the structural tree incomplete.

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
# The largest page each layer is read at: how many issues of it are asked for under the
# one issue above it when the tree's own size is not known.
PAGE = {"spec": 50, "ticket": 100, "child": 50}
# The layers that bring their labels and blockers with them.
META_LAYERS = ("spec", "ticket")
# A larger metadata page would breach the 500,000-node cap in the largest map.
META_PAGE = 10
# Above this price, in the tracker's points, a read asks the tree's size first. The sizing
# query costs one point; a map read at the largest pages costs 152.
SIZING_WORTH = 10

GH_ENV = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR_FORCE", "CLICOLOR")}


class TreeUnreadable(RuntimeError):
    """The tree could not be read whole: the question went unanswered, or part of it did."""


class ShortPage(TreeUnreadable):
    """A list came back shorter than the tracker's own count of it."""


def below(root: str) -> list[str]:
    """The layers under an issue of layer `root`, the one just below it first."""
    if root not in LAYERS[:-1]:
        raise ValueError(f"`{root}` is not a layer with issues below it; one of "
                         f"{', '.join(LAYERS[:-1])}")
    return list(LAYERS[LAYERS.index(root) + 1:])


def _pages(sizes: dict[str, int] | None) -> dict[str, int]:
    """The page every layer is read at: the size given for it, held between one and that
    layer's largest page, and the largest page for every layer no size is given for."""
    pages = dict(PAGE)
    for layer, size in (sizes or {}).items():
        if layer in pages and isinstance(size, int):
            pages[layer] = min(PAGE[layer], max(1, size))
    return pages


def query(root: str = "spec", sizes: dict[str, int] | None = None) -> str:
    """The query for the tree below an issue of layer `root`, each layer read at the size
    `sizes` gives for it and at its largest page where it gives none."""
    layers = below(root)
    pages = _pages(sizes)

    def level(remaining: list[str], depth: int) -> str:
        pad = "  " * depth
        head, rest = remaining[0], remaining[1:]
        fields = "number title state"
        if head in META_LAYERS:
            fields += (f" labels(first:{META_PAGE}) {{ totalCount nodes {{ name }} }}"
                       f" blockedBy(first:{META_PAGE}) {{ totalCount nodes {{ number state }} }}")
        if rest:
            fields += " subIssuesSummary { total completed } " + level(rest, depth + 1)
        return (f"subIssues(first:{pages[head]}) {{ nodes {{\n"
                f"{pad}  {fields} }}}}")

    return ("query($o:String!, $n:String!, $root:Int!) {\n"
            "  repository(owner:$o, name:$n) {\n"
            "    issue(number:$root) {\n"
            "      number title state subIssuesSummary { total completed }\n"
            f"      {level(layers, 3)}\n"
            "    }\n"
            "  }\n"
            "}\n")


def sizing_query(root: str = "spec") -> str:
    """The counts of the layers below an issue and nothing else, so the read after it can
    ask each list at the size the tree really is. It enumerates every layer above the last
    one, which is one request per issue in them: one point."""
    layers = below(root)[:-1]

    def level(remaining: list[str], depth: int) -> str:
        pad = "  " * depth
        head, rest = remaining[0], remaining[1:]
        fields = "subIssuesSummary { total }"
        if rest:
            fields += " " + level(rest, depth + 1)
        return (f"subIssues(first:{PAGE[head]}) {{ nodes {{\n"
                f"{pad}  {fields} }}}}")

    counts = f"\n      {level(layers, 3)}" if layers else ""
    return ("query($o:String!, $n:String!, $root:Int!) {\n"
            "  repository(owner:$o, name:$n) {\n"
            "    issue(number:$root) {\n"
            "      subIssuesSummary { total }"
            f"{counts}\n"
            "    }\n"
            "  }\n"
            "}\n")


def cost(root: str = "spec", sizes: dict[str, int] | None = None) -> int:
    """What the tracker charges for one `query(root, sizes)`, by its own rule: every list
    counted as though it came back full, added up and divided by a hundred."""
    pages = _pages(sizes)
    requests = 0
    issues = 1
    for layer in below(root):
        requests += issues             # one sub-issue list under each issue of the layer above
        issues *= pages[layer]
        if layer in META_LAYERS:
            requests += 2 * issues     # labels and blockers, one list each, per issue
    return max(1, round(requests / 100))


def _sizes(issue: dict, layers: list[str]) -> dict[str, int]:
    """The size each layer really is, read off a sizing query's counts: a layer's page is
    the largest count any issue above it gives for it. A count the tracker did not give
    leaves that layer, and every layer below it, at its largest page."""
    sizes: dict[str, int] = {}
    level = [issue] if isinstance(issue, dict) else []
    for layer in layers:
        totals = [(node.get("subIssuesSummary") or {}).get("total") for node in level]
        if not level or any(not isinstance(total, int) for total in totals):
            break
        sizes[layer] = min(PAGE[layer], max(1, max(totals)))
        level = [child for node in level
                 for child in ((node.get("subIssues") or {}).get("nodes") or [])
                 if isinstance(child, dict)]
    return sizes


def _run_gh(args: list[str]) -> tuple[int, str, str]:
    run = subprocess.run(["gh", *args], capture_output=True, text=True, env=GH_ENV)
    return run.returncode, run.stdout, run.stderr


def _node(raw: dict, where: str) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("number"), int):
        raise TreeUnreadable(f"{where}: an issue came back with no number")
    node = {"number": raw["number"], "title": raw.get("title") or "",
            "state": (raw.get("state") or "").upper()}
    if "labels" in raw:
        def connection(name: str) -> list[dict]:
            nodes = (raw.get(name) or {}).get("nodes")
            if not isinstance(nodes, list):
                raise TreeUnreadable(
                    f"#{node['number']}: its labels or blockers came back unreadable")
            return nodes

        labels = connection("labels")
        blockers = connection("blockedBy")
        node["labels"] = [label.get("name") or "" for label in labels
                          if isinstance(label, dict)]
        node["blockedBy"] = [
            {"number": blocker["number"], "state": (blocker.get("state") or "").upper()}
            for blocker in blockers
            if isinstance(blocker, dict) and isinstance(blocker.get("number"), int)
        ]
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
            raise ShortPage(f"#{node['number']} has {total} sub-issues and {len(nodes)} "
                            f"came back: the rest are past this query's page, and a "
                            f"tree missing them would read as whole")
        node["total"] = total
        node["completed"] = summary.get("completed")
        node["children"] = [_node(child, f"under #{node['number']}") for child in nodes]
    return node


def _ask(run, number: int, text: str) -> dict:
    """The issue the tracker answers `text` with, or a refusal saying why it could not."""
    code, out, err = run(["api", "graphql", "-F", "o={owner}", "-F", "n={repo}",
                          "-F", f"root={number}", "-f", f"query={text}"])
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
    return issue


def read(number: int, root: str = "spec", gh=None) -> dict:
    """The tree below issue `number`, which is of layer `root`.

    `gh` runs one `gh` command and answers `(exit code, stdout, stderr)`; it is the one
    seam, and tests replace it. Raises `TreeUnreadable` rather than answer with part of
    the tree.
    """
    run = gh or _run_gh
    sizes: dict[str, int] = {}
    if cost(root) > SIZING_WORTH:
        sizes = _sizes(_ask(run, number, sizing_query(root)), below(root))
    try:
        return _node(_ask(run, number, query(root, sizes)), f"#{number}")
    except ShortPage:
        if not sizes:
            raise
        # Something was added to the tree between the counts and this read. Ask again at
        # the largest pages, which is the answer with nothing measured at all.
        return _node(_ask(run, number, query(root)), f"#{number}")


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
