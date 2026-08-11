#!/usr/bin/env python3
"""校验 spec 与 plan 的产物引用声明。"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

FRONTMATTER_DELIMITER = "---"
ALLOWED_KEYS = {"category", "name", "issue", "sub"}


@dataclass(frozen=True)
class HistoricalDocument:
    reason: str


@dataclass(frozen=True)
class InvalidDeclaration:
    reason: str


def frontmatter_lines(path: Path) -> HistoricalDocument | InvalidDeclaration | list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return InvalidDeclaration(f"无法读取文件：{error.strerror}")

    if not lines or lines[0] != FRONTMATTER_DELIMITER:
        return HistoricalDocument("缺少 YAML 元数据块")
    try:
        closing = lines.index(FRONTMATTER_DELIMITER, 1)
    except ValueError:
        return InvalidDeclaration("YAML 元数据块没有结束标记")
    return lines[1:closing]


def scalar(raw_value: str) -> str | None:
    value = raw_value.strip()
    if not value:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value or None


def parse_artifact_refs(path: Path) -> HistoricalDocument | InvalidDeclaration | list[dict[str, str]]:
    frontmatter = frontmatter_lines(path)
    if isinstance(frontmatter, (HistoricalDocument, InvalidDeclaration)):
        return frontmatter

    artifact_line: int | None = None
    for index, line in enumerate(frontmatter):
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, _ = line.split(":", 1)
        if key.strip() == "artifact_refs":
            if artifact_line is not None:
                return InvalidDeclaration("artifact_refs 重复出现")
            artifact_line = index

    if artifact_line is None:
        return HistoricalDocument("缺少 artifact_refs")

    _, raw_value = frontmatter[artifact_line].split(":", 1)
    value = raw_value.strip()
    if value == "[]":
        return []
    if value:
        return InvalidDeclaration("artifact_refs 必须是映射列表或 []")

    refs: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in frontmatter[artifact_line + 1 :]:
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            break
        stripped = line.lstrip()
        if stripped.startswith("- "):
            current = {}
            refs.append(current)
            entry = stripped[2:]
        elif current is not None:
            entry = stripped
        else:
            return InvalidDeclaration("artifact_refs 必须是映射列表或 []")

        if ":" not in entry:
            return InvalidDeclaration("产物引用条目必须是键值映射")
        key, raw_entry_value = entry.split(":", 1)
        key = key.strip()
        entry_value = scalar(raw_entry_value)
        if not key or entry_value is None:
            return InvalidDeclaration("产物引用条目必须是非空键值映射")
        if key in current:
            return InvalidDeclaration(f"产物引用条目重复键 {key}")
        current[key] = entry_value

    if not refs:
        return InvalidDeclaration("artifact_refs 必须是映射列表或 []")
    return refs


def validate_shape(reference: dict[str, str]) -> str | None:
    unexpected = sorted(set(reference) - ALLOWED_KEYS)
    if unexpected:
        return f"产物引用有未允许的键 {', '.join(unexpected)}"
    for key in ("category", "name"):
        if not reference.get(key):
            return f"缺少或无效的 {key}"
    if "issue" in reference and not reference["issue"].isdigit():
        return "缺少或无效的 issue"
    if "sub" in reference and not reference["sub"]:
        return "缺少或无效的 sub"
    return None


def check_reference(mmw: Path, repository: Path, reference: dict[str, str]) -> str | None:
    command = [str(mmw), "artifact", "path", reference["category"], "--name", reference["name"]]
    if "issue" in reference:
        command.extend(("--issue", reference["issue"]))
    if "sub" in reference:
        command.extend(("--sub", reference["sub"]))

    completed = subprocess.run(
        command,
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return None
    return completed.stderr.strip() or "mmw artifact path 失败"


def documents(repository: Path) -> list[Path]:
    found: list[Path] = []
    for category in ("specs", "plans"):
        root = repository / "docs" / category
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            if category == "specs" and path.name == "README.md":
                continue
            found.append(path)
    return sorted(found, key=lambda path: path.relative_to(repository).as_posix())


def main(arguments: list[str]) -> int:
    if len(arguments) != 2:
        print("mmw artifact check: 内部调用参数错误", file=sys.stderr)
        return 2

    repository = Path(arguments[0]).resolve()
    mmw = Path(arguments[1]).resolve()
    failures = 0
    for path in documents(repository):
        relative = path.relative_to(repository).as_posix()
        parsed = parse_artifact_refs(path)
        if isinstance(parsed, HistoricalDocument):
            print(f"mmw artifact check: {relative}: 历史文件，{parsed.reason}")
            continue
        if isinstance(parsed, InvalidDeclaration):
            print(f"mmw artifact check: {relative}: {parsed.reason}", file=sys.stderr)
            failures += 1
            continue
        for index, reference in enumerate(parsed):
            reason = validate_shape(reference)
            if reason is None:
                reason = check_reference(mmw, repository, reference)
            if reason is None:
                continue
            print(
                f"mmw artifact check: {relative}: artifact_refs[{index}]: {reason}",
                file=sys.stderr,
            )
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
