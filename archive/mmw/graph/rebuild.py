#!/usr/bin/env python3
"""重建整张图：原生抽取 → 跨语言边 → 合并 → 路由桥 → 校验 → 发布。

发布是原子的：全过才换上去，任何一步断了旧图原样留着。图是查询的唯一依据，一份
半成品比一份过期的更危险——过期的至少内部自洽。

    python3 rebuild.py --repo-root <绝对路径>
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "graph"

from . import config as config_module
from .bridge import BridgeError, bridge_graph, validate_bridge_contract
from .build import build
from .fragment import CrossEdgeBuildError, write_payload_atomic

MIN_GRAPHIFY = (0, 9, 25)


def _log(message: str) -> None:
    print(f"[mmw-graph] {message}", flush=True)


def _fail(reason: str) -> None:
    raise CrossEdgeBuildError("rebuild", reason)


def _graphify_version() -> tuple[int, ...]:
    if shutil.which("graphify") is None:
        _fail("PATH 里没有 graphify")
    try:
        raw = subprocess.run(
            ["graphify", "--version"], capture_output=True, text=True, check=True
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError) as exc:
        _fail(f"读不到 graphify 版本：{exc}")
        raise AssertionError
    if len(raw) < 2 or raw[0] != "graphify":
        _fail(f"graphify --version 的输出不认得：{' '.join(raw)}")
    try:
        parts = tuple(int(piece) for piece in raw[1].split(".")[:3])
    except ValueError:
        _fail(f"graphify 版本号解析不了：{raw[1]}")
        raise AssertionError
    # 下限而不是等号：钉死一个补丁版本，工具一升级重建就整个停摆，而图会停在最后
    # 一次成功那天，没有任何人看得见。格式真的不兼容时，下面的字段校验会断。
    if parts < MIN_GRAPHIFY:
        want = ".".join(str(x) for x in MIN_GRAPHIFY)
        _fail(f"要 graphify {want} 或更新，当前 {raw[1]}")
    return parts


def _head_sha(repo_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        _fail(f"读不到 HEAD：{exc}")
        raise AssertionError


class _Lock:
    """目录锁。持有者进程没了就接管，不留死锁。"""

    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> _Lock:
        if self._claim():
            return self
        holder = ""
        pid_file = self.path / "pid"
        if pid_file.is_file():
            holder = pid_file.read_text(encoding="utf-8").splitlines()[0].strip()
        if not holder.isdigit():
            _fail(f"锁的持有者读不出来：{holder or '没有 pid'}")
        try:
            os.kill(int(holder), 0)
        except ProcessLookupError:
            shutil.rmtree(self.path, ignore_errors=True)
            if self._claim():
                return self
            _fail("锁被别的进程抢走了")
        except PermissionError:
            pass
        _fail(f"已经有一次重建在跑：pid={holder}")
        raise AssertionError

    def _claim(self) -> bool:
        try:
            self.path.mkdir(parents=True)
        except FileExistsError:
            return False
        (self.path / "pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
        return True

    def __exit__(self, *_exc: object) -> None:
        pid_file = self.path / "pid"
        if pid_file.is_file():
            holder = pid_file.read_text(encoding="utf-8").splitlines()[0].strip()
            if holder != str(os.getpid()):
                return
        shutil.rmtree(self.path, ignore_errors=True)


def _require_lists(payload: object, name: str) -> tuple[list[object], list[object]]:
    if not isinstance(payload, dict):
        _fail(f"{name} 不是一个对象")
        raise AssertionError
    nodes, links = payload.get("nodes"), payload.get("links")
    if not isinstance(nodes, list) or not nodes:
        _fail(f"{name} 没有节点")
    if not isinstance(links, list) or not links:
        _fail(f"{name} 没有边")
    return nodes, links  # type: ignore[return-value]


def _validate(
    native: dict[str, object],
    cross: dict[str, object],
    candidate: dict[str, object],
    repo_root: Path,
    head_sha: str,
    exclude_roots: tuple[str, ...],
) -> None:
    """合并这一步不能悄悄丢东西，也不能把不该进图的东西带进来。"""
    native_nodes, native_links = _require_lists(native, "原生图")
    cross_nodes, _cross_links = _require_lists(cross, "跨语言边")
    candidate_nodes, _candidate_links = _require_lists(candidate, "候选图")

    cross_ids = {
        node["id"]
        for node in cross_nodes
        if isinstance(node, dict) and "id" in node
    }
    native_ids = {
        node["id"]
        for node in native_nodes
        if isinstance(node, dict) and "id" in node
    }
    endpoints = {
        endpoint
        for item in native_links
        if isinstance(item, dict)
        for endpoint in (item.get("source"), item.get("target"))
    }
    _log(f"info native_dangling_endpoints={len(endpoints - native_ids)}")

    candidate_ids = {
        node["id"]
        for node in candidate_nodes
        if isinstance(node, dict) and "id" in node
    }

    def _present(cross_id: object) -> bool:
        if cross_id in candidate_ids:
            return True
        # 合并时可能给节点 id 加了来源前缀。
        return isinstance(cross_id, str) and any(
            isinstance(cid, str) and cid.endswith(f"::{cross_id}")
            for cid in candidate_ids
        )

    dropped = [cross_id for cross_id in cross_ids if not _present(cross_id)]
    if dropped:
        preview = ", ".join(str(item) for item in dropped[:10])
        _fail(f"合并丢了跨语言边的节点：{preview}")
    if len(candidate_nodes) < max(len(native_nodes), len(cross_nodes)):
        _fail(
            f"合并丢了节点：候选 {len(candidate_nodes)} "
            f"原生 {len(native_nodes)} 跨语言 {len(cross_nodes)}"
        )

    validate_bridge_contract(candidate, head_sha)

    forbidden = tuple(tuple(part for part in root.split("/") if part) for root in exclude_roots)
    violations: list[tuple[object, str]] = []
    for node in candidate_nodes:
        if not isinstance(node, dict):
            continue
        raw_source = node.get("source_file")
        if not isinstance(raw_source, str) or not raw_source:
            continue
        source_path = Path(raw_source)
        if source_path.is_absolute():
            try:
                relative = source_path.resolve().relative_to(repo_root)
            except ValueError:
                continue
        else:
            relative = source_path
        parts = tuple(p for p in relative.as_posix().split("/") if p not in ("", "."))
        # Markdown 不是图的输入。它进来一次，此后每改一次文档图就作废一次。
        if relative.suffix.lower() == ".md" or any(
            parts[: len(prefix)] == prefix for prefix in forbidden
        ):
            violations.append((node.get("id", "unknown"), relative.as_posix()))
    if violations:
        preview = ", ".join(f"{nid}:{path}" for nid, path in violations[:10])
        _fail(f"候选图里有不该进图的来源：{preview}")


def rebuild(repo_root: Path) -> tuple[Path, list[str]]:
    """重建并发布，交回图的位置与原生抽取报出的警告。"""
    cfg = config_module.load(repo_root)
    warnings: list[str] = []
    graph_dir = repo_root / "graphify-out"
    final_graph = graph_dir / "graph.json"
    graph_dir.mkdir(parents=True, exist_ok=True)
    _graphify_version()
    start_head = _head_sha(repo_root)

    with _Lock(graph_dir / ".rebuild.lock"):
        stage = Path(tempfile.mkdtemp(prefix=".rebuild.", dir=graph_dir))
        candidate_path = graph_dir / f".graph.json.{os.getpid()}.tmp"
        try:
            # 合并时的命名空间前缀取自图文件的祖父目录名，它会长进每个节点的 id。
            # 目录名必须固定：拿临时目录名当前缀的话，每次重建所有节点 id 都会变一次。
            native_out = stage / "native" / "graphify-out"
            native_out.mkdir(parents=True)
            cross_out = stage / "cross" / "graphify-out"
            cross_out.mkdir(parents=True)
            _log(f"stage=native head={start_head}")
            env = os.environ.copy()
            env["GRAPHIFY_OUT"] = str(native_out)
            # 逐行读原生抽取的输出：里面的警告说的是「哪些文件没进图」，那是调用方
            # 判断这份图完不完整的唯一依据，跑完再回头看输出就来不及了。
            proc = subprocess.Popen(
                ["graphify", "update", str(repo_root), "--no-cluster"],
                cwd=repo_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="", file=sys.stderr)
                if "warning:" in line.lower():
                    warnings.append(line.strip())
            if proc.wait() != 0:
                _fail("原生抽取失败")
            native_graph = native_out / "graph.json"
            if not native_graph.is_file() or not native_graph.stat().st_size:
                _fail("原生图没有产出")

            _log("stage=cross")
            cross_path = cross_out / "cross_edges.json"
            report = build(repo_root, cross_path)
            _log(
                f"info cross nodes={report.nodes} links={report.links} "
                f"unresolved={report.unresolved}"
            )

            _log("stage=merge")
            merged = subprocess.run(
                [
                    "graphify",
                    "merge-graphs",
                    str(native_graph),
                    str(cross_path),
                    "--out",
                    str(candidate_path),
                ],
                check=False,
            )
            if merged.returncode != 0 or not candidate_path.is_file():
                _fail("合并失败")

            _log("stage=bridge")
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            try:
                candidate = bridge_graph(candidate, start_head)
            except BridgeError as exc:
                _fail(f"路由桥失败：{exc}")
            write_payload_atomic(candidate_path, candidate)

            _log("stage=validate")
            _validate(
                json.loads(native_graph.read_text(encoding="utf-8")),
                json.loads(cross_path.read_text(encoding="utf-8")),
                candidate,
                repo_root,
                start_head,
                cfg.exclude_roots,
            )

            end_head = _head_sha(repo_root)
            if end_head != start_head:
                _fail(f"重建过程里 HEAD 变了：开始 {start_head} 结束 {end_head}")
            _log(f"stage=publish head={start_head}")
            os.replace(candidate_path, final_graph)
            _log(f"published={final_graph}")
            return final_graph, warnings
        finally:
            shutil.rmtree(stage, ignore_errors=True)
            candidate_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="重建这个仓库的结构图谱")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        rebuild(root)
        return 0
    except CrossEdgeBuildError as exc:
        print(f"[FAIL] stage={exc.stage} reason={exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[FAIL] stage=internal reason={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
