#!/usr/bin/env python3
"""校验 spec 与 plan 的产物引用声明。

元数据使用受限 YAML 子集。它支持首行和结束行都是 `---` 的元数据块、
无缩进的唯一键、单行普通标量、无转义的单行引号字符串，以及行尾注释。
无引号的纯十进制数字是整数。它还支持 `[]` 和只含整数的 `[1, 2]`。
`artifact_refs` 可以是 `[]`，或由两空格列表项和四空格键值行组成的映射列表。
它不支持折叠或字面字符串、嵌套映射、其他列表、锚点、别名、标签、制表符，
或多行和带转义的引号字符串。遇到这些语法会报告所在行并退出失败。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

FRONTMATTER_DELIMITER = "---"
ALLOWED_KEYS = {"category", "name", "issue", "sub"}
KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
INTEGER_PATTERN = re.compile(r"^[0-9]+$")

Scalar = str | int
MetadataValue = Scalar | list[int] | list[dict[str, Scalar]]


@dataclass(frozen=True)
class HistoricalDocument:
    reason: str


@dataclass(frozen=True)
class InvalidDeclaration:
    reason: str


@dataclass(frozen=True)
class ParsedFrontmatter:
    metadata: dict[str, MetadataValue]
    body: list[str]


class ArtifactCheckError(Exception):
    """产物声明校验的调用输入无效。"""


def unsupported(line_number: int, syntax: str) -> InvalidDeclaration:
    return InvalidDeclaration(f"第 {line_number} 行不支持 {syntax}")


def without_inline_comment(raw_value: str, line_number: int) -> InvalidDeclaration | str:
    quote = ""
    for index, character in enumerate(raw_value):
        if quote:
            if character == "\\":
                return unsupported(line_number, "YAML 引号转义")
            if character == quote:
                quote = ""
            continue
        if character in {"'", '"'}:
            quote = character
            continue
        if character == "#" and (index == 0 or raw_value[index - 1].isspace()):
            return raw_value[:index].strip()
    if quote:
        return unsupported(line_number, "未结束的 YAML 引号字符串")
    return raw_value.strip()


def parse_inline_integer_list(value: str, line_number: int) -> InvalidDeclaration | list[int]:
    if value == "[]":
        return []
    if not value.endswith("]"):
        return unsupported(line_number, "YAML 流式列表")
    contents = value[1:-1].strip()
    if not contents:
        return []
    numbers: list[int] = []
    for item in contents.split(","):
        number = item.strip()
        if not INTEGER_PATTERN.fullmatch(number):
            return unsupported(line_number, "非整数的 YAML 流式列表")
        numbers.append(int(number))
    return numbers


def parse_scalar(raw_value: str, line_number: int) -> InvalidDeclaration | MetadataValue | None:
    value = without_inline_comment(raw_value, line_number)
    if isinstance(value, InvalidDeclaration):
        return value
    if not value:
        return None
    if value.startswith(">"):
        return unsupported(line_number, "YAML 折叠字符串")
    if value.startswith("|"):
        return unsupported(line_number, "YAML 字面字符串")
    if value.startswith("["):
        return parse_inline_integer_list(value, line_number)
    if value.startswith("{"):
        return unsupported(line_number, "YAML 流式映射")
    if value.startswith(("&", "*", "!")):
        return unsupported(line_number, "YAML 锚点、别名或标签")
    if value[0] in {"'", '"'}:
        if len(value) < 2 or value[-1] != value[0]:
            return unsupported(line_number, "未结束的 YAML 引号字符串")
        return value[1:-1]
    if INTEGER_PATTERN.fullmatch(value):
        return int(value)
    return value


def parse_mapping_entry(
    entry: str, line_number: int
) -> InvalidDeclaration | tuple[str, Scalar]:
    if ":" not in entry:
        return unsupported(line_number, "非映射的 YAML 列表项")
    key, raw_value = entry.split(":", 1)
    key = key.strip()
    if not KEY_PATTERN.fullmatch(key):
        return unsupported(line_number, "无效的 YAML 键")
    value = parse_scalar(raw_value, line_number)
    if isinstance(value, InvalidDeclaration):
        return value
    if value is None or isinstance(value, list):
        return unsupported(line_number, "非标量的产物引用值")
    return key, value


def parse_frontmatter(
    path: Path,
) -> HistoricalDocument | InvalidDeclaration | ParsedFrontmatter:
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

    metadata: dict[str, MetadataValue] = {}
    references: list[dict[str, Scalar]] | None = None
    current_reference: dict[str, Scalar] | None = None
    empty_reference_line: int | None = None
    for offset, line in enumerate(lines[1:closing], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            return unsupported(offset, "YAML 制表符缩进")
        if line[0].isspace():
            if references is None:
                return unsupported(offset, "YAML 缩进映射")
            indentation = len(line) - len(line.lstrip(" "))
            entry = line[indentation:]
            if indentation == 2 and entry.startswith("- "):
                parsed_entry = parse_mapping_entry(entry[2:], offset)
                if isinstance(parsed_entry, InvalidDeclaration):
                    return parsed_entry
                key, value = parsed_entry
                current_reference = {key: value}
                references.append(current_reference)
                empty_reference_line = None
                continue
            if indentation == 4 and current_reference is not None:
                parsed_entry = parse_mapping_entry(entry, offset)
                if isinstance(parsed_entry, InvalidDeclaration):
                    return parsed_entry
                key, value = parsed_entry
                if key in current_reference:
                    return InvalidDeclaration(f"第 {offset} 行产物引用条目重复键 {key}")
                current_reference[key] = value
                continue
            return unsupported(offset, "artifact_refs 以外的 YAML 缩进结构")

        references = None
        current_reference = None
        if ":" not in line:
            return unsupported(offset, "非映射的 YAML 顶层内容")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not KEY_PATTERN.fullmatch(key):
            return unsupported(offset, "无效的 YAML 键")
        if key in metadata:
            return InvalidDeclaration(f"第 {offset} 行 YAML 元数据块重复键 {key}")
        value = parse_scalar(raw_value, offset)
        if isinstance(value, InvalidDeclaration):
            return value
        if value is None:
            if key != "artifact_refs":
                return unsupported(offset, "YAML 嵌套值")
            references = []
            empty_reference_line = offset
            metadata[key] = references
            continue
        metadata[key] = value

    if empty_reference_line is not None:
        return InvalidDeclaration(
            f"第 {empty_reference_line} 行 artifact_refs 必须是映射列表或 []"
        )
    return ParsedFrontmatter(metadata=metadata, body=lines[closing + 1 :])


def parse_artifact_refs(
    path: Path,
) -> HistoricalDocument | InvalidDeclaration | list[dict[str, Scalar]]:
    frontmatter = parse_frontmatter(path)
    if isinstance(frontmatter, (HistoricalDocument, InvalidDeclaration)):
        return frontmatter

    if "artifact_refs" not in frontmatter.metadata:
        return InvalidDeclaration("缺少 artifact_refs")
    references = frontmatter.metadata["artifact_refs"]
    if not isinstance(references, list):
        return InvalidDeclaration("artifact_refs 必须是映射列表或 []")
    mappings: list[dict[str, Scalar]] = []
    for item in references:
        if not isinstance(item, dict):
            return InvalidDeclaration("artifact_refs 必须是映射列表或 []")
        mappings.append(item)
    return mappings


def validate_shape(reference: dict[str, Scalar]) -> str | None:
    unexpected = sorted(set(reference) - ALLOWED_KEYS)
    if unexpected:
        return f"产物引用有未允许的键 {', '.join(unexpected)}"
    for key in ("category", "name"):
        if not isinstance(reference.get(key), str) or not reference[key]:
            return f"缺少或无效的 {key}"
    if "issue" in reference and not isinstance(reference["issue"], int):
        return "缺少或无效的 issue"
    if "sub" in reference and (not isinstance(reference["sub"], str) or not reference["sub"]):
        return "缺少或无效的 sub"
    return None


def check_reference(mmw: Path, repository: Path, reference: dict[str, Scalar]) -> str | None:
    category = reference["category"]
    name = reference["name"]
    if not isinstance(category, str) or not isinstance(name, str):
        return "缺少或无效的 category 或 name"
    command = [str(mmw), "artifact", "path", category, "--name", name]
    if "issue" in reference:
        command.extend(("--issue", str(reference["issue"])))
    if "sub" in reference:
        command.extend(("--sub", str(reference["sub"])))

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


def category_root(data_path: Path, category: str) -> str:
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactCheckError(f"无法读取产物落点数据 {data_path}: {error}") from error
    record = data.get(category)
    if not isinstance(record, dict):
        raise ArtifactCheckError(f"产物落点数据没有 {category} 类别")
    if record.get("root_kind") != "fixed" or record.get("status") != "active":
        raise ArtifactCheckError(f"{category} 不是可校验的固定活动类别")
    root = record.get("root")
    if not isinstance(root, str) or not root:
        raise ArtifactCheckError(f"{category} 缺少类别根")
    return root


def documents(repository: Path, data_path: Path) -> list[Path]:
    found: list[Path] = []
    for category in ("spec", "plan"):
        root = repository / category_root(data_path, category)
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            if category == "spec" and path.name == "README.md":
                continue
            found.append(path)
    return sorted(found, key=lambda path: path.relative_to(repository).as_posix())


def main(arguments: list[str]) -> int:
    if len(arguments) != 3:
        print("mmw artifact check: 内部调用参数错误", file=sys.stderr)
        return 2

    repository = Path(arguments[0]).resolve()
    mmw = Path(arguments[1]).resolve()
    data_path = Path(arguments[2]).resolve()
    try:
        paths = documents(repository, data_path)
    except ArtifactCheckError as error:
        print(f"mmw artifact check: {error}", file=sys.stderr)
        return 1

    failures = 0
    for path in paths:
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
