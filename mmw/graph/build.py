#!/usr/bin/env python3
"""跨语言边的构建入口。

跑四个提取器，自检，落盘。四类边各自独立：配了才提取，没配就跳过，不因为缺一类
而失败。一个只有后端的仓库照样能建出路由与 HTTP 调用的边。

    python3 build.py --repo-root <绝对路径> --output <绝对路径的 json>
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "graph"

from . import config as config_module
from .fragment import (
    BuildReport,
    CrossEdgeBuildError,
    GraphFragmentBuilder,
    UnresolvedItem,
    route_node_id,
    write_payload_atomic,
)
from .http import extract_http_edges
from .ipc import extract_ipc_edges
from .routes import add_route_edges, enumerate_routes
from .topics import extract_topic_edges


def _expected_relations(cfg: config_module.GraphConfig) -> set[str]:
    """配了哪几类，图里就必须有哪几类。

    某一类配了却一条边都没建出来，说明配置跟当前代码结构对不上——比如客户端换了
    封装写法。那种情况下图看起来只是「少了几条边」，不会有任何人发现。
    """
    expected: set[str] = set()
    if cfg.routes:
        expected.add("handles_route")
    if cfg.ipc:
        expected.update({"ipc_handles", "ipc_invokes"})
    for spec in cfg.topics:
        expected.add(spec.relation)
    if cfg.http and cfg.http.python_clients:
        expected.add("http_calls")
    if cfg.http and cfg.http.ts_clients:
        expected.add("http_calls")
    return expected


def _structural_checks(
    builder: GraphFragmentBuilder,
    cfg: config_module.GraphConfig,
    coverage_map: dict[str, dict[str, object]],
    unresolved: list[UnresolvedItem],
) -> None:
    for node in builder.nodes.values():
        if Path(str(node["source_file"])).is_absolute() or not re.fullmatch(
            r"L[1-9][0-9]*", str(node["source_location"])
        ):
            raise CrossEdgeBuildError(
                "self_check", f"节点位置不是相对且稳定的：{node['id']}"
            )
    for name, entry in coverage_map.items():
        if int(str(entry["total"])) != int(str(entry["resolved"])) + int(
            str(entry["unresolved"])
        ):
            raise CrossEdgeBuildError("self_check", f"{name} 的覆盖率加不起来")
    relations = {str(item["relation"]) for item in builder.links}
    missing = _expected_relations(cfg) - relations
    if missing:
        raise CrossEdgeBuildError(
            "self_check", f"配了但一条边都没建出来：{sorted(missing)}"
        )
    counted = sum(int(str(coverage_map[name]["unresolved"])) for name in coverage_map)
    if counted != len(unresolved):
        raise CrossEdgeBuildError(
            "self_check", f"unresolved 数对不上：覆盖率 {counted} 清单 {len(unresolved)}"
        )
    for item in unresolved:
        if Path(item.source_file).is_absolute() or item.line <= 0 or not item.reason:
            raise CrossEdgeBuildError("self_check", "unresolved 条目格式不对")


def _topology_assertions(
    builder: GraphFragmentBuilder, cfg: config_module.GraphConfig
) -> None:
    """仓库自己声明的拓扑事实。覆盖率是数字，数字掉了没人看得见；这些钉的是事实。"""
    checks = cfg.assertions
    for want in checks.route_handler:
        route_id = route_node_id(want["service"], want["method"], want["path"])
        edges = [
            item
            for item in builder.links
            if item["relation"] == "handles_route" and item["target"] == route_id
        ]
        if len(edges) != 1:
            raise CrossEdgeBuildError(
                "self_check",
                f"{want['method']} {want['path']} 应当恰好有一个处理函数，"
                f"实际 {len(edges)} 个",
            )
        handler = builder.nodes[str(edges[0]["source"])]
        if handler["source_file"] != want["file"] or want[
            "handler_contains"
        ] not in str(handler["label"]):
            raise CrossEdgeBuildError(
                "self_check",
                f"{want['method']} {want['path']} 没有解析到 "
                f"{want['file']} 的 {want['handler_contains']}"
                "（这条断言写在 .mmw.json 里，处理函数合法搬家时同步改它）",
            )
    if checks.route_per_service:
        method, _, path = checks.route_per_service.partition(" ")
        for service in cfg.services:
            if route_node_id(service, method.upper(), path) not in builder.nodes:
                raise CrossEdgeBuildError(
                    "self_check", f"{service} 上没有 {checks.route_per_service}"
                )
    if checks.http_methods:
        seen: set[str] = set()
        for item in builder.links:
            if item["relation"] != "http_calls":
                continue
            metadata = item.get("metadata")
            if isinstance(metadata, dict) and "method" in metadata:
                seen.add(str(metadata["method"]))
        absent = set(checks.http_methods) - seen
        if absent:
            raise CrossEdgeBuildError(
                "self_check",
                f"http_calls 没有覆盖到这些方法：{sorted(absent)}"
                "（提取器把非 GET 调用退化成 GET 时就会这样）",
            )
    for topic, want_relations in checks.topic_relations.items():
        actual = {
            str(item["relation"])
            for item in builder.links
            if item["target"] == f"sync-topic::{topic}"
        }
        if actual != set(want_relations):
            raise CrossEdgeBuildError(
                "self_check",
                f"主题 {topic} 的关系集合变了：期望 {sorted(want_relations)} "
                f"实际 {sorted(actual)}"
                "（这条断言写在 .mmw.json 里，拓扑合法演进时同步改它）",
            )


def build(repo_root: Path, output: Path) -> BuildReport:
    cfg = config_module.load(repo_root)
    if not cfg.enabled:
        raise CrossEdgeBuildError(
            "config", "retrieval.graph 里四类边一类都没配，没有跨语言边可建"
        )
    builder = GraphFragmentBuilder()
    coverage_map: dict[str, dict[str, object]] = {}
    unresolved: list[UnresolvedItem] = []
    user_data_unchanged = True

    if cfg.routes:
        records, user_data_unchanged = enumerate_routes(
            repo_root, cfg.routes, cfg.services
        )
        coverage_map["routes"] = add_route_edges(builder, records, cfg.services)
    if cfg.ipc:
        ipc_coverage, ipc_warnings = extract_ipc_edges(repo_root, builder, cfg.ipc)
        coverage_map["ipc"] = ipc_coverage
        for warning in ipc_warnings:
            print(
                f"[WARN] kind={warning.kind} "
                f"source={warning.source_file}:{warning.line} reason={warning.reason}",
                file=sys.stderr,
            )
    if cfg.topics:
        topic_coverage, topic_unresolved = extract_topic_edges(
            repo_root, builder, cfg.topics
        )
        coverage_map["topics"] = topic_coverage
        unresolved.extend(topic_unresolved)
    if cfg.http:
        http_coverage, http_unresolved = extract_http_edges(repo_root, builder, cfg.http)
        coverage_map["http"] = http_coverage
        unresolved.extend(http_unresolved)

    _structural_checks(builder, cfg, coverage_map, unresolved)
    _topology_assertions(builder, cfg)
    payload = builder.payload(coverage_map, unresolved)
    write_payload_atomic(output, payload)
    return BuildReport(
        "ok",
        str(output),
        len(payload["nodes"]),  # type: ignore[arg-type]
        len(payload["links"]),  # type: ignore[arg-type]
        coverage_map,
        len(unresolved),
        user_data_unchanged,
    )


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CrossEdgeBuildError("preflight", message)


def _preflight(repo_root: str | None, output: str | None) -> tuple[Path, Path]:
    if not repo_root or not output:
        raise CrossEdgeBuildError("preflight", "--repo-root 与 --output 都是必填")
    raw_root, raw_output = Path(repo_root), Path(output)
    if not raw_root.is_absolute() or not raw_output.is_absolute():
        raise CrossEdgeBuildError("preflight", "--repo-root 与 --output 必须是绝对路径")
    if raw_output.exists() and raw_output.is_dir():
        raise CrossEdgeBuildError("preflight", "--output 要指一个 JSON 文件，不是目录")
    return raw_root.resolve(), raw_output


def main(argv: list[str] | None = None) -> int:
    try:
        parser = _Parser(description="建这个仓库的跨语言边")
        parser.add_argument("--repo-root")
        parser.add_argument("--output")
        args = parser.parse_args(argv)
        root, output = _preflight(args.repo_root, args.output)
        report = build(root, output)
        print(json.dumps(dataclasses.asdict(report), ensure_ascii=False, sort_keys=True))
        return 0
    except CrossEdgeBuildError as exc:
        print(f"[FAIL] stage={exc.stage} reason={exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:  # 兜底：任何异常都要让失败可见，不静默退出 0
        print(f"[FAIL] stage=internal reason={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
