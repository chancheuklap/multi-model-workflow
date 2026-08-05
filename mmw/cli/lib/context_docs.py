#!/usr/bin/env python3
"""同步并检查目标仓库的领域上下文消费合同。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import NoReturn


AGENTS_START = "<!-- MMW-DOMAIN-CONTEXT-START -->"
AGENTS_END = "<!-- MMW-DOMAIN-CONTEXT-END -->"
MAP_START = "<!-- MMW-CONTEXT-MAP-RULES-START -->"
MAP_END = "<!-- MMW-CONTEXT-MAP-RULES-END -->"
CHANGED_STATUSES = {"created", "inserted", "updated", "appended"}


class ContractError(Exception):
    def __init__(self, rel_path: str, code: str, message: str) -> None:
        super().__init__(message)
        self.rel_path = rel_path
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Target:
    kind: str
    rel_path: str
    path: Path
    status: str
    original: bytes | None
    candidate: bytes | None
    mode: int | None


def fail(rel_path: str, code: str, message: str) -> NoReturn:
    raise ContractError(rel_path, code, message)


def read_bytes(path: Path, rel_path: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        fail(rel_path, "io-error", f"无法读取文件：{error}")


def read_seed(name: str) -> bytes:
    path = Path(__file__).resolve().parent.parent / "seeds" / name
    return read_bytes(path, path.name)


def decode_markdown(content: bytes, rel_path: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        fail(rel_path, "io-error", "文件不是有效的 UTF-8 Markdown")


def marker_lines(content: bytes, marker: str, rel_path: str) -> list[int]:
    text = decode_markdown(content, rel_path)
    return [
        index
        for index, line in enumerate(text.splitlines(keepends=True))
        if line.rstrip("\r\n") == marker
    ]


def replace_managed_block(
    original: bytes,
    seed: bytes,
    start_marker: str,
    end_marker: str,
    rel_path: str,
) -> tuple[bytes, bool]:
    start_lines = marker_lines(original, start_marker, rel_path)
    end_lines = marker_lines(original, end_marker, rel_path)
    if not start_lines and not end_lines:
        return original, False
    if (
        len(start_lines) != 1
        or len(end_lines) != 1
        or start_lines[0] >= end_lines[0]
    ):
        fail(rel_path, "invalid-markers", "受管区块标记缺失、重复或次序错误")

    lines = original.splitlines(keepends=True)
    before = b"".join(lines[: start_lines[0]])
    after = b"".join(lines[end_lines[0] + 1 :])
    return before + seed + after, True


def append_block(original: bytes, seed: bytes) -> bytes:
    if not original:
        return seed
    separator = b"\n" if original.endswith(b"\n") else b"\n\n"
    return original + separator + seed


def insert_map_block(original: bytes, seed: bytes, rel_path: str) -> bytes:
    text = decode_markdown(original, rel_path)
    lines = text.splitlines(keepends=True)
    context_line = next(
        (
            index
            for index, line in enumerate(lines)
            if line.rstrip("\r\n").rstrip(" \t") == "## Contexts"
        ),
        None,
    )
    if context_line is None:
        fail(rel_path, "missing-section", "Map 缺少 ## Contexts，无法插入使用规则")
    before = "".join(lines[:context_line]).encode("utf-8")
    after = "".join(lines[context_line:]).encode("utf-8")
    separator = b"" if not before or before.endswith(b"\n") else b"\n"
    return before + separator + seed + b"\n" + after


def target_mode(path: Path, rel_path: str) -> int:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError as error:
        fail(rel_path, "io-error", f"无法读取文件权限：{error}")


def managed_target(
    kind: str,
    root: Path,
    rel_path: str,
    seed: bytes,
    start_marker: str,
    end_marker: str,
) -> Target:
    path = root / rel_path
    if not path.exists():
        return Target(kind, rel_path, path, "created", None, seed, None)

    original = read_bytes(path, rel_path)
    candidate, had_markers = replace_managed_block(
        original, seed, start_marker, end_marker, rel_path
    )
    if not had_markers:
        candidate = (
            append_block(original, seed)
            if kind == "agents"
            else insert_map_block(original, seed, rel_path)
        )
    if candidate == original:
        status = "current"
    else:
        status = "updated" if had_markers else "inserted"
    return Target(
        kind,
        rel_path,
        path,
        status,
        original,
        candidate,
        target_mode(path, rel_path),
    )


def claude_target(root: Path, host: str) -> Target:
    rel_path = "CLAUDE.md"
    path = root / rel_path
    if host != "claude-code":
        return Target("claude", rel_path, path, "not-required", None, None, None)
    if not path.exists():
        return Target("claude", rel_path, path, "created", None, b"@AGENTS.md\n", None)

    original = read_bytes(path, rel_path)
    text = decode_markdown(original, rel_path)
    if any(line.rstrip("\r\n") == "@AGENTS.md" for line in text.splitlines(keepends=True)):
        return Target(
            "claude",
            rel_path,
            path,
            "current",
            original,
            original,
            target_mode(path, rel_path),
        )
    candidate = append_block(original, b"@AGENTS.md\n")
    return Target(
        "claude",
        rel_path,
        path,
        "appended",
        original,
        candidate,
        target_mode(path, rel_path),
    )


def run_git(root: Path, *arguments: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def ensure_safe_target(root: Path, target: Target) -> None:
    if target.status not in CHANGED_STATUSES or target.original is None:
        return
    tracked = run_git(root, "ls-files", "--error-unmatch", "--", target.rel_path)
    worktree_clean = run_git(root, "diff", "--quiet", "--", target.rel_path)
    index_clean = run_git(root, "diff", "--cached", "--quiet", "--", target.rel_path)
    if not tracked or not worktree_clean or not index_clean:
        fail(
            target.rel_path,
            "dirty-target",
            "待更新的既有目标必须已跟踪，且暂存区和工作区都干净",
        )


def atomic_write_targets(targets: list[Target]) -> None:
    changed = [target for target in targets if target.status in CHANGED_STATUSES]
    staged: dict[Path, Path] = {}
    replaced: list[Target] = []
    try:
        for target in changed:
            target.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                dir=target.path.parent,
                prefix=f".{target.path.name}.mmw-",
            )
            temp_path = Path(temp_name)
            staged[target.path] = temp_path
            with os.fdopen(descriptor, "wb") as temp_file:
                temp_file.write(target.candidate or b"")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.chmod(temp_path, target.mode if target.mode is not None else 0o644)

        for target in changed:
            os.replace(staged[target.path], target.path)
            staged.pop(target.path, None)
            replaced.append(target)
    except OSError as error:
        for target in reversed(replaced):
            try:
                if target.original is None:
                    target.path.unlink(missing_ok=True)
                    continue
                descriptor, rollback_name = tempfile.mkstemp(
                    dir=target.path.parent,
                    prefix=f".{target.path.name}.mmw-rollback-",
                )
                rollback_path = Path(rollback_name)
                with os.fdopen(descriptor, "wb") as rollback_file:
                    rollback_file.write(target.original)
                    rollback_file.flush()
                    os.fsync(rollback_file.fileno())
                os.chmod(rollback_path, target.mode if target.mode is not None else 0o644)
                os.replace(rollback_path, target.path)
            except OSError:
                pass
        fail("-", "io-error", f"无法原子写入领域规则：{error}")
    finally:
        for temp_path in staged.values():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def load_domain_config(root: Path, config_path: Path) -> dict[str, str]:
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        domain = raw["domain"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        fail(".mmw.json", "invalid-config", f"无法读取 domain 配置：{error}")

    result: dict[str, str] = {}
    for field, default in (
        ("map", "CONTEXT-MAP.md"),
        ("fallback", "CONTEXT.md"),
        ("context_dir", "docs/context"),
    ):
        value = domain.get(field, default)
        if not isinstance(value, str) or not value:
            fail(".mmw.json", "invalid-config", f"domain.{field} 必须是非空相对路径")
        path = Path(value)
        if path.is_absolute():
            fail(".mmw.json", "invalid-config", f"domain.{field} 必须是仓库相对路径")
        resolved = (root / path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            fail(".mmw.json", "invalid-config", f"domain.{field} 不得越出仓库")
        result[field] = path.as_posix()
    return result


def sync_contracts(root: Path, config_path: Path, host: str) -> list[Target]:
    if host not in {"claude-code", "pi", "codex"}:
        fail("-", "invalid-config", f"无法识别宿主：{host}")
    domain = load_domain_config(root, config_path)
    agents_seed = read_seed("AGENTS-domain-context.md")
    map_seed = read_seed("CONTEXT-MAP-rules.md")

    targets = [
        managed_target(
            "agents",
            root,
            "AGENTS.md",
            agents_seed,
            AGENTS_START,
            AGENTS_END,
        )
    ]
    map_rel = domain["map"]
    map_path = root / map_rel
    if map_path.exists():
        targets.append(
            managed_target(
                "map", root, map_rel, map_seed, MAP_START, MAP_END
            )
        )
    else:
        targets.append(Target("map", map_rel, map_path, "not-present", None, None, None))
    targets.append(claude_target(root, host))

    for target in targets:
        ensure_safe_target(root, target)
    atomic_write_targets(targets)
    return targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync = subparsers.add_parser("sync")
    sync.add_argument("--root", required=True, type=Path)
    sync.add_argument("--config", required=True, type=Path)
    sync.add_argument("--host", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    try:
        if args.command == "sync":
            targets = sync_contracts(root, args.config.resolve(), args.host)
            for target in targets:
                print(f"sync\t{target.kind}\t{target.rel_path}\t{target.status}")
            return 0
    except ContractError as error:
        print(
            f"error\t{error.rel_path}\t{error.code}\t{error.message}",
            file=sys.stderr,
        )
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
