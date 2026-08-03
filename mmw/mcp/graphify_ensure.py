#!/usr/bin/env python3
"""保证任意 Git 工作树的原生 Graphify 图可用且对应当前内容。"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1
OUT_DIR_NAME = "graphify-out"
GRAPH_NAME = "graph.json"
FRESHNESS_NAME = ".pi-freshness.json"
LOCK_NAME = ".pi-ensure.lock"
BACKUP_GRAPH_NAME = ".pi-backup.graph.json"
BACKUP_FRESHNESS_NAME = ".pi-backup.freshness.json"
HARD_WARNING_MARKERS = (
    "because a dependency is missing",
    "classified as code but graphify has no AST extractor",
)


class EnsureError(RuntimeError):
    """图谱无法诚实更新。"""


def _run(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    text: bool = False,
) -> subprocess.CompletedProcess[Any]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        check=False,
    )
    if check and proc.returncode != 0:
        stderr = proc.stderr if text else proc.stderr.decode("utf-8", errors="replace")
        raise EnsureError(f"命令失败({proc.returncode}): {' '.join(args)}\n{stderr.strip()}")
    return proc


def _repo_root(path: Path) -> Path:
    path = path.expanduser().resolve()
    proc = _run(["git", "rev-parse", "--show-toplevel"], cwd=path, text=True)
    return Path(proc.stdout.strip()).resolve()


def _head(repo: Path) -> str:
    proc = _run(["git", "rev-parse", "--verify", "HEAD"], cwd=repo, check=False, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "UNBORN"


def _git_bytes(repo: Path, *args: str) -> bytes:
    proc = _run(["git", *args], cwd=repo)
    return bytes(proc.stdout)


# 指纹只认图的输入。排除两样：
#
# Markdown——它不进图，文档改动不该让图过期。仓库天天改文档，按全部内容算指纹的话
# 每改一次说明文件就要重建一次几十兆的图。
#
# 图自己的输出目录——把它算进去，指纹会在每次建完图之后立刻变，图永远新鲜不了。
#
# 仓库自己的排除清单（`.graphifyignore`）不在这里解析：那要实现一遍 gitignore 语法，
# 而漏排的代价只是多建一次图，建出来的图仍然正确（那些路径本来就被检索工具忽略）。
_EXCLUDE_PATHSPEC = (":(exclude)*.md", f":(exclude){OUT_DIR_NAME}", f":(exclude){OUT_DIR_NAME}/**")


def _is_graph_input(rel: str) -> bool:
    if rel == OUT_DIR_NAME or rel.startswith(f"{OUT_DIR_NAME}/"):
        return False
    return not rel.lower().endswith(".md")


def _worktree_fingerprint(repo: Path) -> tuple[str, str]:
    """返回 HEAD 与图输入的稳定指纹。

    指纹算的是 HEAD 里每个输入文件的内容哈希，不是提交号——空提交不改任何文件，
    图仍然有效。任务 worktree 建出来时会带一个记录用户原话的空提交，按提交号判
    的话它一建出来就"过期"，主仓库那份现成的图白白复用不了。
    """
    head = _head(repo)
    digest = hashlib.sha256()

    if head == "UNBORN":
        digest.update(b"unborn\0")
    else:
        # 每行形如 "<mode> <type> <object>\t<path>"。用 object 而不是文件内容：
        # 它就是 git 算好的内容哈希，几万个文件也只是一次命令。
        listing = _git_bytes(repo, "ls-tree", "-r", "-z", head)
        for raw in sorted(item for item in listing.split(b"\0") if item):
            entry = raw.decode("utf-8", errors="surrogateescape")
            meta, _, rel = entry.partition("\t")
            if not rel or not _is_graph_input(rel):
                continue
            digest.update(f"tracked\0{meta.split()[2]}\0{rel}\0".encode())

    # 工作区里还没提交的部分，同样只算图的输入。
    if head == "UNBORN":
        digest.update(_git_bytes(repo, "diff", "--binary", "--cached", "--", ".", *_EXCLUDE_PATHSPEC))
        digest.update(_git_bytes(repo, "diff", "--binary", "--", ".", *_EXCLUDE_PATHSPEC))
    else:
        digest.update(
            _git_bytes(repo, "diff", "--binary", "--no-ext-diff", head, "--", ".", *_EXCLUDE_PATHSPEC)
        )

    raw_untracked = _git_bytes(repo, "ls-files", "--others", "--exclude-standard", "-z")
    for raw in sorted(item for item in raw_untracked.split(b"\0") if item):
        rel = raw.decode("utf-8", errors="surrogateescape")
        if not _is_graph_input(rel):
            continue
        path = repo / rel
        digest.update(b"untracked\0" + raw + b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0" + os.readlink(path).encode("utf-8", errors="surrogateescape"))
        elif path.is_file():
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        else:
            digest.update(b"non-file")
        digest.update(b"\0")
    return head, digest.hexdigest()


def _graphify_binary() -> str:
    configured = os.environ.get("PI_GRAPHIFY_BIN", "").strip()
    binary = configured or shutil.which("graphify")
    if not binary:
        raise EnsureError("找不到 graphify；请先安装官方 graphifyy 工具")
    return str(binary)


def _graphify_version(binary: str, repo: Path) -> str:
    proc = _run([binary, "--version"], cwd=repo, text=True)
    output = (proc.stdout or proc.stderr).strip()
    if not output:
        raise EnsureError("graphify --version 没有返回版本")
    return output.splitlines()[0]


def _graph_paths(repo: Path) -> tuple[Path, Path, Path, Path, Path]:
    out_dir = repo / OUT_DIR_NAME
    return (
        out_dir,
        out_dir / GRAPH_NAME,
        out_dir / FRESHNESS_NAME,
        out_dir / BACKUP_GRAPH_NAME,
        out_dir / BACKUP_FRESHNESS_NAME,
    )


def _validate_graph(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EnsureError(f"Graphify 图无法读取:{path}:{exc}") from exc
    nodes = data.get("nodes")
    links = data.get("links")
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise EnsureError(f"Graphify 图缺少 nodes/links 数组:{path}")
    absolute_sources = [
        node.get("source_file")
        for node in nodes
        if isinstance(node, dict)
        and isinstance(node.get("source_file"), str)
        and Path(node["source_file"]).is_absolute()
    ]
    if absolute_sources:
        raise EnsureError(f"Graphify 图含绝对源码路径:{absolute_sources[0]}")
    return data


def _read_freshness(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _freshness_payload(
    *,
    head: str,
    fingerprint: str,
    version: str,
    warnings: list[str],
    source: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "head_sha": head,
        "worktree_fingerprint": fingerprint,
        "graphify_version": version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "warnings": warnings,
    }


def _is_fresh(
    graph_path: Path,
    freshness_path: Path,
    *,
    fingerprint: str,
    version: str,
) -> tuple[bool, int]:
    try:
        _validate_graph(graph_path)
    except EnsureError:
        return False, 0
    meta = _read_freshness(freshness_path)
    if meta is None:
        return False, 0
    # 不比 head_sha：指纹已经把图的每个输入算进去了，提交号只是记录给人看的。
    # 比它的话，一个不改任何文件的空提交也会让图作废。
    expected = (
        meta.get("schema_version") == SCHEMA_VERSION
        and meta.get("worktree_fingerprint") == fingerprint
        and meta.get("graphify_version") == version
    )
    warnings = meta.get("warnings")
    return expected, len(warnings) if isinstance(warnings, list) else 0


def _copy_atomic(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(fd)
    tmp = Path(raw_tmp)
    try:
        shutil.copy2(source, tmp)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def _try_reuse(
    source_repo: Path,
    target_repo: Path,
    *,
    target_head: str,
    target_fingerprint: str,
    version: str,
) -> bool:
    source_head, source_fingerprint = _worktree_fingerprint(source_repo)
    if (source_head, source_fingerprint) != (target_head, target_fingerprint):
        return False
    _, source_graph, source_meta, _, _ = _graph_paths(source_repo)
    fresh, _ = _is_fresh(
        source_graph,
        source_meta,
        fingerprint=source_fingerprint,
        version=version,
    )
    if not fresh:
        return False
    _, target_graph, target_meta, _, _ = _graph_paths(target_repo)
    _copy_atomic(source_graph, target_graph)
    source_payload = _read_freshness(source_meta) or {}
    warnings = source_payload.get("warnings")
    _write_json_atomic(
        target_meta,
        _freshness_payload(
            head=target_head,
            fingerprint=target_fingerprint,
            version=version,
            warnings=warnings if isinstance(warnings, list) else [],
            source=f"reused:{source_repo}",
        ),
    )
    return True


def _restore_backup(graph: Path, meta: Path, backup_graph: Path, backup_meta: Path) -> None:
    if graph.exists():
        graph.unlink()
    if meta.exists():
        meta.unlink()
    if backup_graph.exists():
        os.replace(backup_graph, graph)
    if backup_meta.exists():
        os.replace(backup_meta, meta)


def _build(repo: Path, binary: str, version: str, head: str, fingerprint: str) -> int:
    out_dir, graph, meta, backup_graph, backup_meta = _graph_paths(repo)
    out_dir.mkdir(parents=True, exist_ok=True)
    # 旧备份存在表示上次构建未完成；备份是最后一份已验证状态，优先于半成品新图。
    if backup_graph.exists():
        graph.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
        os.replace(backup_graph, graph)
        if backup_meta.exists():
            os.replace(backup_meta, meta)
    else:
        backup_meta.unlink(missing_ok=True)
    if graph.exists():
        os.replace(graph, backup_graph)
    if meta.exists():
        os.replace(meta, backup_meta)

    warnings: list[str] = []
    hard_warning = False
    try:
        proc = subprocess.Popen(
            [binary, "update", str(repo), "--no-cluster"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", file=sys.stderr)
            lowered = line.lower()
            if "warning:" in lowered or "[graphify] warning" in lowered:
                warnings.append(line.strip())
            if any(marker in lowered for marker in HARD_WARNING_MARKERS):
                hard_warning = True
        returncode = proc.wait()
        if returncode != 0:
            raise EnsureError(f"graphify update 失败，退出码 {returncode}")
        if hard_warning:
            raise EnsureError("Graphify 缺少源码解析能力；拒绝把残缺图标记为新鲜")
        _validate_graph(graph)
        final_head, final_fingerprint = _worktree_fingerprint(repo)
        if (final_head, final_fingerprint) != (head, fingerprint):
            raise EnsureError("建图期间工作树发生变化；拒绝发布与当前内容不一致的图")
        _write_json_atomic(
            meta,
            _freshness_payload(
                head=head,
                fingerprint=fingerprint,
                version=version,
                warnings=warnings,
                source="built",
            ),
        )
        backup_graph.unlink(missing_ok=True)
        backup_meta.unlink(missing_ok=True)
        return len(warnings)
    except BaseException:
        _restore_backup(graph, meta, backup_graph, backup_meta)
        raise


def _main_worktree(repo: Path) -> Path | None:
    """当前这棵树是任务 worktree 时，主仓库那棵树；否则 None。

    自动找出来而不是等调用方传：任务 worktree 刚建出来时内容跟主仓库一样，主仓库
    那份图直接复用就行，没有理由再花几分钟建一份一模一样的。
    """
    proc = _run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo,
        check=False,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    main = Path(proc.stdout.strip()).parent
    return main if main != repo and main.is_dir() else None


def ensure(repo_arg: Path, source_arg: Path | None = None) -> str:
    repo = _repo_root(repo_arg)
    source = _repo_root(source_arg) if source_arg is not None else _main_worktree(repo)
    binary = _graphify_binary()
    version = _graphify_version(binary, repo)
    out_dir, graph, meta, _, _ = _graph_paths(repo)
    out_dir.mkdir(parents=True, exist_ok=True)
    lock_path = out_dir / LOCK_NAME
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        head, fingerprint = _worktree_fingerprint(repo)
        fresh, warning_count = _is_fresh(
            graph,
            meta,
            fingerprint=fingerprint,
            version=version,
        )
        if fresh:
            return f"FRESH repo={repo} warnings={warning_count}"
        if source is not None and source != repo and _try_reuse(
            source,
            repo,
            target_head=head,
            target_fingerprint=fingerprint,
            version=version,
        ):
            reused_meta = _read_freshness(meta) or {}
            warnings = reused_meta.get("warnings")
            count = len(warnings) if isinstance(warnings, list) else 0
            return f"REUSED repo={repo} source={source} warnings={count}"
        warning_count = _build(repo, binary, version, head, fingerprint)
        return f"BUILT repo={repo} warnings={warning_count}"


def status(repo_arg: Path) -> str:
    """只报状态，不建也不复用。

    判据跟 ensure 共用同一个指纹与同一处 _is_fresh：分成两套的话，命令行报新鲜
    而调用时又重建一次，谁都说不清哪个才算数。
    """
    repo = _repo_root(repo_arg)
    _, graph, meta, _, _ = _graph_paths(repo)
    if not graph.is_file():
        return f"MISSING repo={repo}"
    binary = _graphify_binary()
    version = _graphify_version(binary, repo)
    _, fingerprint = _worktree_fingerprint(repo)
    fresh, warnings = _is_fresh(graph, meta, fingerprint=fingerprint, version=version)
    return f"{'FRESH' if fresh else 'STALE'} repo={repo} warnings={warnings}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--source", type=Path)
    parser.add_argument(
        "--status",
        action="store_true",
        help="只报 FRESH / STALE / MISSING，不建图也不复用",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        print(status(args.repo) if args.status else ensure(args.repo, args.source))
        return 0
    except (EnsureError, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        print(f"graphify-ensure: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
