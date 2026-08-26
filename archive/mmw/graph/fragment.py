"""图片段的构造与落盘。

四个提取器共用这一层：造节点、造边、拒绝身份冲突、按稳定顺序序列化。它不认识
任何一个仓库——路由、IPC、消息主题、HTTP 调用的差别全在各自的提取器里，到这一
层只剩「节点」和「边」。
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import tempfile
from collections.abc import Iterable
from pathlib import Path

ORIGIN = "mmw-cross-edges"

ALLOWED_RELATIONS = frozenset(
    {
        "handles_route",
        "ipc_handles",
        "ipc_invokes",
        "produces_topic",
        "drains_topic",
        "consumes_topic",
        "http_calls",
    }
)
REQUIRED_NODE_FIELDS = frozenset(
    {
        "id",
        "label",
        "file_type",
        "source_file",
        "source_location",
        "metadata",
        "_origin",
    }
)
REQUIRED_LINK_FIELDS = frozenset(
    {
        "source",
        "target",
        "relation",
        "confidence",
        "source_file",
        "source_location",
        "metadata",
    }
)


class CrossEdgeBuildError(RuntimeError):
    """一次受控失败。stage 是命令行合同的一部分，调用方按它定位是哪一阶段断的。"""

    def __init__(self, stage: str, reason: str) -> None:
        super().__init__(reason)
        self.stage = stage
        self.reason = reason


@dataclasses.dataclass(frozen=True)
class RouteRecord:
    service: str
    method: str
    path: str
    handler_name: str
    source_file: str
    line: int


@dataclasses.dataclass(frozen=True)
class UnresolvedItem:
    kind: str
    source_file: str
    line: int
    reason: str


@dataclasses.dataclass(frozen=True)
class BuildReport:
    status: str
    output: str
    nodes: int
    links: int
    coverage: dict[str, dict[str, object]]
    unresolved: int
    real_user_data_unchanged: bool


def json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def relative_file(repo_root: Path, value: str | Path, *, stage: str) -> str:
    try:
        return Path(value).resolve().relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise CrossEdgeBuildError(stage, f"源文件在仓库外：{value}") from exc


def line_location(line: int) -> str:
    if line <= 0:
        raise CrossEdgeBuildError("self_check", f"行号必须为正，收到 {line}")
    return f"L{line}"


def normalize_route_template(path: str) -> str:
    """归一路由模板，但不猜动态参数叫什么名字。

    `/items/{item_id}` 与 `/items/{id}` 归一成同一个 `/items/{param}`：调用方写的
    参数名和处理函数写的参数名本来就不必相同，按名字比对会把同一条路由拆成两个
    互不相连的节点。
    """
    if not isinstance(path, str) or not path.startswith("/"):
        raise CrossEdgeBuildError("routes", f"路由必须是绝对路径：{path!r}")
    path = re.sub(r"/+", "/", path)
    path = re.sub(r"\{[^{}]+\}", "{param}", path)
    if path != "/":
        path = path.rstrip("/")
    return path or "/"


def route_node_id(service: str, method: str, path: str) -> str:
    return f"route::{service}::{method}::{path}"


def coverage(
    total: int, resolved: int, unresolved: int, **extra: object
) -> dict[str, object]:
    if min(total, resolved, unresolved) < 0 or resolved + unresolved != total:
        raise CrossEdgeBuildError("self_check", "覆盖率算术不成立")
    result: dict[str, object] = {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "support_rate": round(resolved / total, 4) if total else 0.0,
        "unresolved_rate": round(unresolved / total, 4) if total else 0.0,
    }
    result.update(extra)
    return result


class GraphFragmentBuilder:
    """收集图元素，身份冲突当场失败。

    同一个 id 出现两次而内容不同，说明两个提取器对同一件东西的认知不一致。合并
    成后者会静默丢掉前者，所以这里直接断。
    """

    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, object]] = {}
        self._links: dict[tuple[object, ...], dict[str, object]] = {}

    def add_node(self, node: dict[str, object]) -> None:
        missing = REQUIRED_NODE_FIELDS - node.keys()
        if missing:
            raise CrossEdgeBuildError("self_check", f"节点缺字段：{sorted(missing)}")
        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id:
            raise CrossEdgeBuildError("self_check", "节点 id 必须是非空字符串")
        canonical = dict(node)
        previous = self._nodes.get(node_id)
        if previous is not None and json_bytes(previous) != json_bytes(canonical):
            raise CrossEdgeBuildError("self_check", f"节点身份冲突：{node_id}")
        self._nodes[node_id] = canonical

    def add_link(self, link: dict[str, object]) -> None:
        missing = REQUIRED_LINK_FIELDS - link.keys()
        if missing:
            raise CrossEdgeBuildError("self_check", f"边缺字段：{sorted(missing)}")
        if link["relation"] not in ALLOWED_RELATIONS:
            raise CrossEdgeBuildError("self_check", f"不认识的关系：{link['relation']}")
        key = (
            link["relation"],
            link["source"],
            link["target"],
            link["source_file"],
            link["source_location"],
            json_bytes(link["metadata"]),
        )
        self._links[key] = dict(link)

    @property
    def nodes(self) -> dict[str, dict[str, object]]:
        return self._nodes

    @property
    def links(self) -> list[dict[str, object]]:
        return list(self._links.values())

    def payload(
        self,
        coverage_map: dict[str, dict[str, object]],
        unresolved: Iterable[UnresolvedItem],
    ) -> dict[str, object]:
        for link in self._links.values():
            if link["source"] not in self._nodes or link["target"] not in self._nodes:
                raise CrossEdgeBuildError("self_check", "边的端点不在节点表里")
        unresolved_rows = [dataclasses.asdict(item) for item in unresolved]
        unresolved_rows.sort(
            key=lambda item: (
                item["kind"],
                item["source_file"],
                item["line"],
                item["reason"],
            )
        )
        return {
            "directed": True,
            "multigraph": False,
            "graph": {
                "generator": ORIGIN,
                "coverage": coverage_map,
                "unresolved": unresolved_rows,
            },
            "nodes": [self._nodes[key] for key in sorted(self._nodes)],
            "links": sorted(
                self._links.values(),
                key=lambda item: (
                    str(item["relation"]),
                    str(item["source"]),
                    str(item["target"]),
                    str(item["source_file"]),
                    str(item["source_location"]),
                ),
            ),
            "input_tokens": 0,
            "output_tokens": 0,
        }


def node(
    node_id: str, label: str, source_file: str, line: int, metadata: dict[str, object]
) -> dict[str, object]:
    return {
        "id": node_id,
        "label": label,
        "file_type": "code",
        "source_file": source_file,
        "source_location": line_location(line),
        "metadata": metadata,
        "_origin": ORIGIN,
    }


def link(
    source: str,
    target: str,
    relation: str,
    source_file: str,
    line: int,
    metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "confidence": "EXTRACTED",
        "source_file": source_file,
        "source_location": line_location(line),
        "metadata": metadata,
    }


def write_payload_atomic(output: Path, payload: dict[str, object]) -> None:
    temp_path: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        )
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, output)
        temp_path = None
    except OSError as exc:
        raise CrossEdgeBuildError("write", str(exc)) from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
