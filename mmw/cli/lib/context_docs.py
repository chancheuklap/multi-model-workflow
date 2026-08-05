#!/usr/bin/env python3
"""同步并检查目标仓库的领域上下文消费合同。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
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


@dataclass(frozen=True)
class CheckResult:
    shape: str
    rel_path: str


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


def reject_unsafe_target(path: Path, rel_path: str) -> None:
    if path.is_symlink():
        fail(rel_path, "unsafe-target", "受管目标不得是符号链接")
    if path.exists() and not path.is_file():
        fail(rel_path, "unsafe-target", "受管目标必须是普通文件")


def check_managed_content(
    original: bytes,
    rel_path: str,
    seed: bytes,
    start_marker: str,
    end_marker: str,
) -> None:
    candidate, had_markers = replace_managed_block(
        original, seed, start_marker, end_marker, rel_path
    )
    if not had_markers or candidate != original:
        fail(rel_path, "managed-drift", "领域上下文受管区块与 MMW 种子不一致")


def check_managed_block(
    path: Path,
    rel_path: str,
    seed: bytes,
    start_marker: str,
    end_marker: str,
) -> None:
    reject_unsafe_target(path, rel_path)
    if not path.is_file():
        fail(rel_path, "managed-drift", "缺少领域上下文受管区块")
    original = read_bytes(path, rel_path)
    check_managed_content(original, rel_path, seed, start_marker, end_marker)


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
    reject_unsafe_target(path, rel_path)
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
    reject_unsafe_target(path, rel_path)
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


def rollback_replaced_targets(targets: list[Target]) -> tuple[list[str], list[str]]:
    unrestored: list[str] = []
    uncleared: list[str] = []
    for target in reversed(targets):
        if target.original is None:
            try:
                target.path.unlink(missing_ok=True)
            except OSError:
                unrestored.append(target.rel_path)
            continue

        rollback_path: Path | None = None
        try:
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
            unrestored.append(target.rel_path)
        finally:
            if rollback_path is not None and rollback_path.exists():
                try:
                    rollback_path.unlink()
                except OSError:
                    uncleared.append(rollback_path.name)
    return unrestored, uncleared


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
        unrestored, uncleared = rollback_replaced_targets(replaced)
        message = f"无法原子写入领域规则：{error}"
        if unrestored:
            message += f"；未恢复目标：{', '.join(unrestored)}"
        if uncleared:
            message += f"；未清理回滚临时文件：{', '.join(uncleared)}"
        fail("-", "io-error", message)
    finally:
        for temp_path in staged.values():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def load_domain_config(root: Path, config_path: Path) -> dict[str, str]:
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        fail(".mmw.json", "invalid-config", f"无法读取 domain 配置：{error}")
    if not isinstance(raw, dict) or "domain" not in raw:
        fail(".mmw.json", "invalid-config", "配置必须包含 domain object")
    domain = raw["domain"]
    if not isinstance(domain, dict):
        fail(".mmw.json", "invalid-config", "domain 必须是 object")

    result: dict[str, str] = {}
    for field, default in (
        ("map", "CONTEXT-MAP.md"),
        ("fallback", "CONTEXT.md"),
        ("context_dir", "docs/context"),
        ("adr_dir", "docs/adr"),
    ):
        value = domain.get(field, default)
        if not isinstance(value, str) or not value:
            fail(".mmw.json", "invalid-config", f"domain.{field} 必须是非空相对路径")
        if any(separator in value for separator in ("\t", "\r", "\n")):
            fail(".mmw.json", "invalid-config", f"domain.{field} 不得包含 TAB 或换行")
        path = Path(value)
        if path.is_absolute():
            fail(".mmw.json", "invalid-config", f"domain.{field} 必须是仓库相对路径")
        try:
            resolved = (root / path).resolve()
            resolved.relative_to(root)
        except (OSError, RuntimeError, ValueError):
            fail(".mmw.json", "invalid-config", f"domain.{field} 不得越出仓库")
        result[field] = path.as_posix()
    return result


def is_readable_file(path: Path) -> bool:
    if not path.is_file() or not os.access(path, os.R_OK):
        return False
    try:
        with path.open("rb") as source:
            source.read(1)
    except OSError:
        return False
    return True


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def section_lines(text: str, heading: str, rel_path: str) -> list[str]:
    lines = text.splitlines()
    matches = [
        index for index, line in enumerate(lines) if line.rstrip(" \t") == heading
    ]
    if len(matches) != 1:
        fail(rel_path, "missing-section", f"Map 必须包含唯一的 {heading}")
    start = matches[0] + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if re.match(r"^##\s+\S", lines[index])
        ),
        len(lines),
    )
    return lines[start:end]


def table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if (
        not stripped.startswith("|")
        or not stripped.endswith("|")
        or is_escaped_character(stripped, len(stripped) - 1)
    ):
        return None
    cells: list[str] = []
    current: list[str] = []
    code_delimiter = 0
    content = stripped[1:-1]
    index = 0
    while index < len(content):
        character = content[index]
        if character == "`":
            run_end = index
            while run_end < len(content) and content[run_end] == "`":
                run_end += 1
            run_length = run_end - index
            current.append(content[index:run_end])
            if code_delimiter == 0:
                code_delimiter = run_length
            elif code_delimiter == run_length:
                code_delimiter = 0
            index = run_end
            continue
        if (
            character == "|"
            and code_delimiter == 0
            and not is_escaped_character(content, index)
        ):
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
        index += 1
    cells.append("".join(current).strip())
    return cells


def is_escaped_character(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def resolve_leaf(
    raw_target: str,
    base_dir: Path,
    context_dir: Path,
    map_rel: str,
) -> Path:
    if (
        Path(raw_target).is_absolute()
        or raw_target.startswith("\\")
        or re.match(r"^[A-Za-z]:[\\/]", raw_target)
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw_target)
    ):
        fail(map_rel, "invalid-leaf", f"Leaf 必须使用 Map 相对路径：{raw_target}")
    resolved = (base_dir / raw_target).resolve()
    if (
        not is_within(resolved, context_dir)
        or resolved.suffix != ".md"
        or not is_readable_file(resolved)
    ):
        fail(map_rel, "invalid-leaf", f"Leaf 越界、失效、不可读或不是 Markdown：{raw_target}")
    return resolved


def check_context_table(
    lines: list[str], map_path: Path, map_rel: str, context_dir: Path
) -> set[Path]:
    content = [line for line in lines if line.strip()]
    if len(content) < 3:
        fail(map_rel, "invalid-context-table", "Contexts 必须包含三列表格和至少一个上下文")
    header = table_cells(content[0])
    separator = table_cells(content[1])
    if header != ["Context", "Leaf", "Owns"] or separator is None or len(separator) != 3:
        fail(map_rel, "invalid-context-table", "Contexts 表头必须依次为 Context、Leaf、Owns")
    if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
        fail(map_rel, "invalid-context-table", "Contexts 表格分隔行无效")

    names: set[str] = set()
    leaves: set[Path] = set()
    link_pattern = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")
    for line in content[2:]:
        cells = table_cells(line)
        if cells is None or len(cells) != 3:
            fail(map_rel, "invalid-context-table", "Contexts 每一行都必须有三列")
        context, leaf_cell, owns = cells
        if not context or context in names:
            fail(map_rel, "invalid-context-table", "Context 必须非空且唯一")
        match = link_pattern.fullmatch(leaf_cell)
        if match is None or not match.group(1).strip():
            fail(map_rel, "invalid-context-table", "Leaf 单元格必须且只能包含一个 Markdown 链接")
        if not owns:
            fail(map_rel, "invalid-context-table", "Owns 必须是非空所有权说明")
        names.add(context)
        leaves.add(resolve_leaf(match.group(2), map_path.parent, context_dir, map_rel))
    return leaves


def check_relationships(lines: list[str], map_rel: str) -> None:
    if not any(re.match(r"^\s*(?:[-+*]|\d+\.)\s+\S", line) for line in lines):
        fail(map_rel, "invalid-relationships", "Relationships 必须包含至少一个 Markdown 列表项")


def check_authoritative_references(
    leaves: set[Path], context_dir: Path, root: Path
) -> None:
    reference_pattern = re.compile(
        r"\(authoritative: \[([^\]]+)\]\(([^)]+)\)\)"
    )
    for leaf in sorted(leaves):
        rel_path = leaf.relative_to(root).as_posix()
        text = decode_markdown(read_bytes(leaf, rel_path), rel_path)
        matches = list(reference_pattern.finditer(text))
        if text.count("authoritative:") != len(matches):
            fail(rel_path, "invalid-authoritative", "authoritative 引用格式无效")
        for match in matches:
            raw_target = match.group(2)
            if (
                Path(raw_target).is_absolute()
                or raw_target.startswith("\\")
                or re.match(r"^[A-Za-z]:[\\/]", raw_target)
                or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", raw_target)
            ):
                fail(rel_path, "invalid-authoritative", f"authoritative 引用越界：{raw_target}")
            target = (leaf.parent / raw_target).resolve()
            if (
                not match.group(1).strip()
                or not is_within(target, context_dir)
                or target.suffix != ".md"
                or target not in leaves
                or not is_readable_file(target)
            ):
                fail(
                    rel_path,
                    "invalid-authoritative",
                    f"authoritative 引用必须指向 Map 已登记的可读 leaf：{raw_target}",
                )


def check_map_content(
    root: Path,
    map_path: Path,
    map_rel: str,
    context_rel: str,
    map_seed: bytes,
    content: bytes,
) -> None:
    check_managed_content(content, map_rel, map_seed, MAP_START, MAP_END)
    text = decode_markdown(content, map_rel)
    contexts = section_lines(text, "## Contexts", map_rel)
    relationships = section_lines(text, "## Relationships", map_rel)
    lines = text.splitlines()
    context_index = next(
        index for index, line in enumerate(lines) if line.rstrip(" \t") == "## Contexts"
    )
    relationship_index = next(
        index
        for index, line in enumerate(lines)
        if line.rstrip(" \t") == "## Relationships"
    )
    if context_index >= relationship_index:
        fail(map_rel, "missing-section", "Map 必须先列 Contexts，再列 Relationships")
    context_dir = (root / context_rel).resolve()
    leaves = check_context_table(contexts, map_path, map_rel, context_dir)
    check_relationships(relationships, map_rel)
    check_authoritative_references(leaves, context_dir, root)


def check_map(root: Path, map_rel: str, context_rel: str, map_seed: bytes) -> None:
    map_path = root / map_rel
    reject_unsafe_target(map_path, map_rel)
    if not map_path.is_file():
        fail(map_rel, "managed-drift", "缺少领域上下文受管区块")
    content = read_bytes(map_path, map_rel)
    check_map_content(root, map_path, map_rel, context_rel, map_seed, content)


def ensure_unique_managed_targets(root: Path, map_rel: str) -> None:
    seen: dict[Path, tuple[str, str]] = {}
    for kind, rel_path in (
        ("agents", "AGENTS.md"),
        ("map", map_rel),
        ("claude", "CLAUDE.md"),
    ):
        resolved = (root / rel_path).resolve()
        previous = seen.get(resolved)
        if previous is not None:
            previous_kind, previous_rel = previous
            fail(
                ".mmw.json",
                "conflicting-targets",
                f"{previous_kind} ({previous_rel}) 与 {kind} ({rel_path}) 解析到同一路径",
            )
        seen[resolved] = (kind, rel_path)


def check_single_document(path: Path, rel_path: str) -> None:
    if (
        path.suffix != ".md"
        or path.is_symlink()
        or not path.is_file()
        or not os.access(path, os.R_OK)
    ):
        fail(rel_path, "unreadable-single", "单领域文档必须是可读的普通 UTF-8 Markdown 文件")
    try:
        content = path.read_bytes()
        content.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        fail(rel_path, "unreadable-single", "单领域文档必须是可读的普通 UTF-8 Markdown 文件")


def check_contracts(root: Path, config_path: Path, host: str) -> CheckResult:
    if host not in {"claude-code", "pi", "codex"}:
        fail("-", "invalid-config", f"无法识别宿主：{host}")
    domain = load_domain_config(root, config_path)
    ensure_unique_managed_targets(root, domain["map"])
    agents_seed = read_seed("AGENTS-domain-context.md")
    map_seed = read_seed("CONTEXT-MAP-rules.md")
    check_managed_block(
        root / "AGENTS.md", "AGENTS.md", agents_seed, AGENTS_START, AGENTS_END
    )
    if host == "claude-code":
        claude_path = root / "CLAUDE.md"
        reject_unsafe_target(claude_path, "CLAUDE.md")
        if not claude_path.is_file():
            fail("CLAUDE.md", "missing-claude-import", "Claude Code 缺少根 AGENTS.md 导入")
        claude_text = decode_markdown(read_bytes(claude_path, "CLAUDE.md"), "CLAUDE.md")
        if not any(
            line.rstrip("\r\n") == "@AGENTS.md"
            for line in claude_text.splitlines(keepends=True)
        ):
            fail("CLAUDE.md", "missing-claude-import", "Claude Code 缺少根 AGENTS.md 导入")

    map_rel = domain["map"]
    fallback_rel = domain["fallback"]
    map_path = root / map_rel
    fallback_path = root / fallback_rel
    if map_path.exists() or map_path.is_symlink():
        check_map(root, map_rel, domain["context_dir"], map_seed)
        return CheckResult("map", map_rel)
    if fallback_path.exists() or fallback_path.is_symlink():
        check_single_document(fallback_path, fallback_rel)
        return CheckResult("single", fallback_rel)
    return CheckResult("none", "-")


def sync_contracts(root: Path, config_path: Path, host: str) -> list[Target]:
    if host not in {"claude-code", "pi", "codex"}:
        fail("-", "invalid-config", f"无法识别宿主：{host}")
    domain = load_domain_config(root, config_path)
    ensure_unique_managed_targets(root, domain["map"])
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
    map_target: Target | None = None
    if map_path.exists() or map_path.is_symlink():
        map_target = managed_target(
            "map", root, map_rel, map_seed, MAP_START, MAP_END
        )
        targets.append(map_target)
    else:
        targets.append(Target("map", map_rel, map_path, "not-present", None, None, None))
    targets.append(claude_target(root, host))

    for target in targets:
        ensure_safe_target(root, target)
    if map_target is not None:
        check_map_content(
            root,
            map_path,
            map_rel,
            domain["context_dir"],
            map_seed,
            map_target.candidate or b"",
        )
    atomic_write_targets(targets)
    return targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync = subparsers.add_parser("sync")
    sync.add_argument("--root", required=True, type=Path)
    sync.add_argument("--config", required=True, type=Path)
    sync.add_argument("--host", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--root", required=True, type=Path)
    check.add_argument("--config", required=True, type=Path)
    check.add_argument("--host", required=True)
    paths = subparsers.add_parser("paths")
    paths.add_argument("--root", required=True, type=Path)
    paths.add_argument("--config", required=True, type=Path)
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
        if args.command == "check":
            result = check_contracts(root, args.config.resolve(), args.host)
            print(f"check\t{result.shape}\t{result.rel_path}\tvalid")
            return 0
        if args.command == "paths":
            domain = load_domain_config(root, args.config.resolve())
            print(json.dumps(domain, ensure_ascii=False))
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
