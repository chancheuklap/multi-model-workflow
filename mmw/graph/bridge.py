#!/usr/bin/env python3
"""把原生抽取出的函数节点，连到路由处理函数节点上。

原生抽取认得 `api_hold` 这个函数，也认得谁调用它；路由那一侧认得 `POST
/api/v1/hold` 由某个处理函数负责。两边说的是同一个函数，但在图上是两个节点——
装饰器注册的处理函数没有任何静态调用者，原生那一侧看它是一座孤岛。这一层按
（源文件，限定名）把它们对上，于是「改这个函数会影响哪个前端页面」这条链才连得起来。

算法跟仓库无关，整段照搬自它第一次落地的地方，只换了图元数据的键名。
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

BRIDGE_RELATION = "implements_route_handler"
BRIDGE_KIND = "native_route_handler_bridge"
MATCH_KEY = ["source_file", "qualified_function_label"]
HEAD_SHA_RE = re.compile(r"[0-9a-f]{40}")
HANDLER_LABEL_RE = re.compile(r"^(?P<qualname>.+)\(\) \([^)]+\)$")
NATIVE_LABEL_RE = re.compile(r"^(?P<qualname>.+)\(\)$")


class BridgeError(RuntimeError):
    pass


def _handler_qualname(node: dict[str, object]) -> str | None:
    match = HANDLER_LABEL_RE.fullmatch(str(node.get("label", "")))
    return match.group("qualname") if match else None


def _native_qualname(node: dict[str, object]) -> str | None:
    match = NATIVE_LABEL_RE.fullmatch(str(node.get("label", "")))
    return match.group("qualname") if match else None


def _nodes_and_links(graph: dict[str, object]) -> tuple[list[object], list[object]]:
    nodes = graph.get("nodes")
    links = graph.get("links")
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise BridgeError("graph must contain nodes and links lists")
    return nodes, links


def _build_metadata(
    graph: dict[str, object], head_sha: str, stats: dict[str, int]
) -> None:
    metadata = graph.get("graph")
    if metadata is None:
        metadata = {}
        graph["graph"] = metadata
    if not isinstance(metadata, dict):
        raise BridgeError("graph metadata must be an object")
    metadata["mmw_build"] = {
        "head_sha": head_sha,
        "route_handler_bridge": stats,
    }


def bridge_graph(graph: dict[str, object], head_sha: str) -> dict[str, object]:
    if HEAD_SHA_RE.fullmatch(head_sha) is None:
        raise BridgeError("head_sha must be 40 lowercase hexadecimal characters")
    result = copy.deepcopy(graph)
    nodes, links = _nodes_and_links(result)
    node_by_id: dict[str, dict[str, object]] = {}
    native_by_key: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    handlers: list[dict[str, object]] = []
    for raw in nodes:
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
            raise BridgeError("every node must be an object with a string id")
        node_id = raw["id"]
        if node_id in node_by_id:
            raise BridgeError(f"duplicate node id: {node_id}")
        node_by_id[node_id] = raw
        source_file = raw.get("source_file")
        qualname = _native_qualname(raw)
        if raw.get("_origin") == "ast" and isinstance(source_file, str) and qualname:
            native_by_key[(source_file, qualname)].append(raw)
        metadata = raw.get("metadata")
        if isinstance(metadata, dict) and metadata.get("kind") == "route_handler":
            handlers.append(raw)

    existing_triples: set[tuple[object, object, object]] = set()
    for link in links:
        if not isinstance(link, dict):
            raise BridgeError("every link must be an object")
        triple = (link.get("source"), link.get("target"), link.get("relation"))
        if triple in existing_triples and link.get("relation") == BRIDGE_RELATION:
            raise BridgeError(f"duplicate bridge triple: {triple}")
        existing_triples.add(triple)

    bridged = ambiguous = missing = unsupported = 0
    bridge_links: list[dict[str, object]] = []
    for handler in sorted(handlers, key=lambda item: str(item["id"])):
        source_file = handler.get("source_file")
        source_location = handler.get("source_location")
        qualname = _handler_qualname(handler)
        if (
            not isinstance(source_file, str)
            or not isinstance(source_location, str)
            or qualname is None
        ):
            missing += 1
            continue
        if ".<locals>." in qualname:
            unsupported += 1
            continue
        candidates = native_by_key.get((source_file, qualname), [])
        if not candidates:
            missing += 1
            continue
        if len(candidates) > 1:
            ambiguous += 1
            continue
        edge: dict[str, object] = {
            "source": candidates[0]["id"],
            "target": handler["id"],
            "relation": BRIDGE_RELATION,
            "confidence": "EXTRACTED",
            "source_file": source_file,
            "source_location": source_location,
            "metadata": {
                "kind": BRIDGE_KIND,
                "match_key": MATCH_KEY,
                "qualified_function_label": qualname,
            },
        }
        triple = (edge["source"], edge["target"], edge["relation"])
        if triple in existing_triples:
            raise BridgeError(f"duplicate bridge triple: {triple}")
        existing_triples.add(triple)
        bridge_links.append(edge)
        bridged += 1

    total = len(handlers)
    eligible = total - unsupported
    stats = {
        "total": total,
        "eligible": eligible,
        "bridged": bridged,
        "unsupported": unsupported,
        "ambiguous": ambiguous,
        "missing": missing,
    }
    if eligible != bridged + ambiguous + missing or ambiguous or missing:
        raise BridgeError(f"route-handler bridge coverage failed: {stats}")
    links.extend(bridge_links)
    _build_metadata(result, head_sha, stats)
    validate_bridge_contract(result, expected_head_sha=head_sha)
    return result


def validate_bridge_contract(graph: dict[str, object], expected_head_sha: str) -> None:
    nodes, links = _nodes_and_links(graph)
    node_by_id: dict[object, dict[str, object]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise BridgeError("every node must be an object with a string id")
        if node["id"] in node_by_id:
            raise BridgeError(f"duplicate node id: {node['id']}")
        node_by_id[node["id"]] = node

    metadata = graph.get("graph")
    if not isinstance(metadata, dict):
        raise BridgeError("graph metadata must be an object")
    build = metadata.get("mmw_build")
    if not isinstance(build, dict) or build.get("head_sha") != expected_head_sha:
        raise BridgeError("graph mmw_build head_sha does not match expected HEAD")
    stats = build.get("route_handler_bridge")
    if not isinstance(stats, dict):
        raise BridgeError("route_handler_bridge metadata is missing")

    handlers = [
        node
        for node in node_by_id.values()
        if isinstance(node.get("metadata"), dict)
        and node["metadata"].get("kind") == "route_handler"
    ]
    native_by_key: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for node in node_by_id.values():
        source_file = node.get("source_file")
        qualname = _native_qualname(node)
        if node.get("_origin") == "ast" and isinstance(source_file, str) and qualname:
            native_by_key[(source_file, qualname)].append(node)

    triples: set[tuple[object, object, object]] = set()
    bridge_count = 0
    for link in links:
        if not isinstance(link, dict) or link.get("relation") != BRIDGE_RELATION:
            continue
        required = {
            "source",
            "target",
            "relation",
            "confidence",
            "source_file",
            "source_location",
            "metadata",
        }
        missing_fields = required.difference(link)
        if missing_fields:
            raise BridgeError(f"bridge missing fields: {sorted(missing_fields)}")
        triple = (link["source"], link["target"], link["relation"])
        if triple in triples:
            raise BridgeError(f"duplicate bridge triple: {triple}")
        triples.add(triple)
        source = node_by_id.get(link["source"])
        target = node_by_id.get(link["target"])
        if source is None or target is None:
            raise BridgeError("bridge has an undeclared endpoint")
        if source.get("_origin") != "ast":
            raise BridgeError("bridge source must be an AST node")
        target_metadata = target.get("metadata")
        if (
            not isinstance(target_metadata, dict)
            or target_metadata.get("kind") != "route_handler"
        ):
            raise BridgeError("bridge target must be a route_handler")
        if link.get("confidence") != "EXTRACTED":
            raise BridgeError("bridge confidence must be EXTRACTED")
        if link.get("source_file") != target.get("source_file") or link.get(
            "source_location"
        ) != target.get("source_location"):
            raise BridgeError("bridge provenance must match handler")
        link_metadata = link.get("metadata")
        if (
            not isinstance(link_metadata, dict)
            or link_metadata.get("kind") != BRIDGE_KIND
            or link_metadata.get("match_key") != MATCH_KEY
        ):
            raise BridgeError("bridge metadata is invalid")
        target_qualname = _handler_qualname(target)
        source_qualname = _native_qualname(source)
        if (
            not target_qualname
            or target_qualname != source_qualname
            or link_metadata.get("qualified_function_label") != target_qualname
        ):
            raise BridgeError("bridge qualified function label is invalid")
        bridge_count += 1

    unsupported = 0
    missing = ambiguous = 0
    for handler in handlers:
        source_file = handler.get("source_file")
        qualname = _handler_qualname(handler)
        if (
            not isinstance(source_file, str)
            or not isinstance(handler.get("source_location"), str)
            or not qualname
        ):
            missing += 1
        elif ".<locals>." in qualname:
            unsupported += 1
        else:
            count = len(native_by_key.get((source_file, qualname), []))
            if count == 0:
                missing += 1
            elif count > 1:
                ambiguous += 1
    computed = {
        "total": len(handlers),
        "eligible": len(handlers) - unsupported,
        "bridged": bridge_count,
        "unsupported": unsupported,
        "ambiguous": ambiguous,
        "missing": missing,
    }
    if (
        computed["eligible"]
        != computed["bridged"] + computed["ambiguous"] + computed["missing"]
    ):
        raise BridgeError(f"bridge statistics do not balance: {computed}")
    if stats != computed:
        raise BridgeError(
            f"bridge statistics do not match: expected {computed}, got {stats}"
        )


def _fixture() -> dict[str, object]:
    return {
        "graph": {},
        "nodes": [
            {
                "id": "native",
                "label": "api_hold()",
                "source_file": "src/example/api.py",
                "_origin": "ast",
            },
            {
                "id": "handler",
                "label": "api_hold() (example)",
                "source_file": "src/example/api.py",
                "source_location": "L927",
                "metadata": {"kind": "route_handler"},
            },
            {"id": "route", "label": "POST /api/v1/hold (example)"},
        ],
        "links": [
            {"source": "handler", "target": "route", "relation": "handles_route"}
        ],
    }


def _expect_error(callback: object) -> None:
    try:
        callback()  # type: ignore[operator]
    except BridgeError:
        return
    raise AssertionError("expected BridgeError")


def _run_self_checks() -> None:
    head = "a" * 40
    original = _fixture()
    bridged = bridge_graph(original, head)
    assert original["links"] == _fixture()["links"]
    assert len(bridged["links"]) == 2
    validate_bridge_contract(bridged, head)

    local = _fixture()
    local["nodes"][1]["label"] = "outer.<locals>.inner() (example)"  # type: ignore[index]
    local_result = bridge_graph(local, head)
    assert (
        local_result["graph"]["mmw_build"]["route_handler_bridge"]["unsupported"]
        == 1
    )  # type: ignore[index]

    missing = _fixture()
    missing["nodes"][0]["label"] = "other()"  # type: ignore[index]
    _expect_error(lambda: bridge_graph(missing, head))

    ambiguous = _fixture()
    ambiguous["nodes"].append(copy.deepcopy(ambiguous["nodes"][0]))  # type: ignore[index]
    ambiguous["nodes"][-1]["id"] = "native-two"  # type: ignore[index]
    _expect_error(lambda: bridge_graph(ambiguous, head))

    for mutate in (
        lambda graph: graph["links"][-1].pop("confidence"),
        lambda graph: graph["links"].__setitem__(
            -1, {**graph["links"][-1], "target": "gone"}
        ),
        lambda graph: graph["links"].append(copy.deepcopy(graph["links"][-1])),
        lambda graph: graph["links"][-1].__setitem__("relation", "wrong"),
        lambda graph: graph["links"][-1].__setitem__("confidence", "INFERRED"),
        lambda graph: graph["links"][-1].__setitem__("source_location", "L1"),
    ):
        invalid = copy.deepcopy(bridged)
        mutate(invalid)
        _expect_error(lambda: validate_bridge_contract(invalid, head))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--head-sha")
    parser.add_argument("--_self-check-only", action="store_true")
    args = parser.parse_args()
    if args._self_check_only:
        if args.graph is not None or args.head_sha is not None:
            parser.error("--_self-check-only does not accept --graph or --head-sha")
    elif args.graph is None or args.head_sha is None:
        parser.error("--graph and --head-sha are required together")
    return args


def main() -> int:
    args = _parse_args()
    if args._self_check_only:
        _run_self_checks()
        print("bridge self-check: ok")
        return 0
    assert args.graph is not None and args.head_sha is not None
    if not args.graph.is_absolute() or not args.graph.is_file():
        raise BridgeError("--graph must be an absolute regular file")
    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            raise BridgeError("graph JSON must be an object")
        bridged = bridge_graph(graph, args.head_sha)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=args.graph.parent, delete=False
        ) as output:
            json.dump(bridged, output, ensure_ascii=False, separators=(",", ":"))
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
            temporary_name = output.name
        os.replace(temporary_name, args.graph)
        return 0
    except (BridgeError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] stage=bridge reason={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
