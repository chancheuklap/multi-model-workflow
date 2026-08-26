#!/usr/bin/env python3
"""计算 `mmw artifact index` 的 Markdown 清单。

元数据使用与 `artifact_check.py` 相同的受限 YAML 子集。它支持 `---`
元数据块、无缩进的唯一键、单行普通标量、无转义的单行引号字符串、行尾注释、
纯十进制整数、`[]`、只含整数的流式列表，以及 `artifact_refs` 的两级映射列表。
它不支持折叠或字面字符串、嵌套映射、其他列表、锚点、别名、标签、制表符，
或多行和带转义的引号字符串。解析器会说明不支持的行和语法。
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

from artifact_check import (
    HistoricalDocument,
    InvalidDeclaration,
    ParsedFrontmatter,
    parse_frontmatter as parse_artifact_frontmatter,
)

class ArtifactIndexError(Exception):
    """索引输入不符合元数据合同。"""


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ADR_FILENAME_PATTERN = re.compile(r"^(\d{4})-[a-z0-9][a-z0-9._-]*\.md$")
TITLE_PATTERN = re.compile(r"^#\s+(.+?)\s*$")


def command_usage() -> int:
    print("mmw artifact index <类别>\n\n类别只能是 adr 或 spec。", file=sys.stderr)
    return 2


def parse_frontmatter(path: Path, relative: str) -> tuple[dict[str, object], list[str]]:
    parsed = parse_artifact_frontmatter(path)
    if isinstance(parsed, HistoricalDocument):
        raise ArtifactIndexError(f"{relative}: {parsed.reason}")
    if isinstance(parsed, InvalidDeclaration):
        raise ArtifactIndexError(f"{relative}: {parsed.reason}")
    if not isinstance(parsed, ParsedFrontmatter):
        raise ArtifactIndexError(f"{relative}: 元数据块格式错误")
    return parsed.metadata, parsed.body


def required_string(metadata: dict[str, object], field: str, relative: str) -> str:
    value = metadata.get(field)
    if not isinstance(value, str) or not value:
        raise ArtifactIndexError(f"{relative}: 缺少或无效的 {field}")
    return value


def required_date(metadata: dict[str, object], relative: str) -> str:
    value = required_string(metadata, "date", relative)
    if not DATE_PATTERN.fullmatch(value):
        raise ArtifactIndexError(f"{relative}: 缺少或无效的 date")
    return value


def required_number(metadata: dict[str, object], field: str, relative: str) -> int:
    value = metadata.get(field)
    if not isinstance(value, int):
        raise ArtifactIndexError(f"{relative}: 缺少或无效的 {field}")
    return value


def required_amends(metadata: dict[str, object], relative: str) -> list[int]:
    value = metadata.get("amends")
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        raise ArtifactIndexError(f"{relative}: 缺少或无效的 amends")
    return value


def title_from(lines: list[str], relative: str) -> str:
    for line in lines:
        match = TITLE_PATTERN.match(line)
        if match:
            return match.group(1)
    raise ArtifactIndexError(f"{relative}: 缺少一级标题")


def markdown_value(value: object) -> str:
    return str(value).replace("|", "\\|")


def discover_documents(root: Path, category: str) -> list[Path]:
    if not root.exists():
        return []

    documents: list[Path] = []
    for path in root.rglob("*.md"):
        if path.name == "README.md":
            continue
        if category == "adr" and not ADR_FILENAME_PATTERN.fullmatch(path.name):
            continue
        documents.append(path)
    return documents


def render_adr_index(documents: list[Path], repo_root: Path) -> str:
    entries: list[dict[str, object]] = []
    for path in documents:
        relative = path.relative_to(repo_root).as_posix()
        filename = ADR_FILENAME_PATTERN.fullmatch(path.name)
        if filename is None:
            continue
        metadata, body = parse_frontmatter(path, relative)
        entries.append(
            {
                "number": int(filename.group(1)),
                "title": title_from(body, relative),
                "date": required_date(metadata, relative),
                "amends": required_amends(metadata, relative),
            }
        )

    entries.sort(key=lambda entry: int(entry["number"]))
    amended_by: dict[int, list[int]] = {int(entry["number"]): [] for entry in entries}
    for entry in entries:
        for amended in entry["amends"]:
            if amended in amended_by:
                amended_by[amended].append(int(entry["number"]))

    lines = [
        "# ADR 索引",
        "",
        "由 `mmw artifact index adr` 生成。",
        "",
        "| 编号 | 标题 | 日期 | 改写了哪几份 | 被哪几份改写 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        number = int(entry["number"])
        amends = ", ".join(f"{item:04d}" for item in entry["amends"]) or "无"
        reverse = ", ".join(f"{item:04d}" for item in amended_by[number]) or "无"
        lines.append(
            "| {number:04d} | {title} | {date} | {amends} | {reverse} |".format(
                number=number,
                title=markdown_value(entry["title"]),
                date=entry["date"],
                amends=amends,
                reverse=reverse,
            )
        )
    return "\n".join(lines) + "\n"


def render_spec_index(documents: list[Path], repo_root: Path) -> str:
    entries: list[dict[str, object]] = []
    for path in documents:
        relative = path.relative_to(repo_root).as_posix()
        metadata, _ = parse_frontmatter(path, relative)
        for field in ("slug", "summary", "date", "branch", "spec_issue", "artifact_refs"):
            if field not in metadata:
                raise ArtifactIndexError(f"{relative}: 缺少或无效的 {field}")
        entries.append(
            {
                "slug": required_string(metadata, "slug", relative),
                "summary": required_string(metadata, "summary", relative),
                "date": required_date(metadata, relative),
                "branch": required_string(metadata, "branch", relative),
                "spec_issue": required_number(metadata, "spec_issue", relative),
            }
        )

    entries.sort(key=lambda entry: str(entry["slug"]))
    lines = [
        "# spec 索引",
        "",
        "由 `mmw artifact index spec` 生成。",
        "",
        "| 名字段 | 摘要 | 日期 | 任务分支名 | spec issue 编号 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| {slug} | {summary} | {date} | {branch} | {spec_issue} |".format(
                slug=markdown_value(entry["slug"]),
                summary=markdown_value(entry["summary"]),
                date=entry["date"],
                branch=markdown_value(entry["branch"]),
                spec_issue=entry["spec_issue"],
            )
        )
    return "\n".join(lines) + "\n"


def write_copy(copy_path: Path, body: str) -> str | None:
    encoded = body.encode("utf-8")
    try:
        existing = copy_path.read_bytes()
    except FileNotFoundError:
        existing = None
    except OSError as error:
        return f"无法读取索引副本 {copy_path}: {error.strerror}；跳过写入"

    if existing == encoded:
        return None

    try:
        copy_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".mmw-artifact-index-", dir=copy_path.parent
        )
        try:
            with os.fdopen(descriptor, "wb") as temporary:
                temporary.write(encoded)
            os.replace(temporary_name, copy_path)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
    except OSError as error:
        return f"无法写入索引副本 {copy_path}: {error.strerror}；跳过写入"
    return None


def load_category(data_path: Path, category: str) -> dict[str, object]:
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactIndexError(f"无法读取产物落点数据 {data_path}: {error}") from error

    record = data.get(category)
    if not isinstance(record, dict):
        raise ArtifactIndexError(f"产物落点数据没有 {category} 类别")
    if record.get("root_kind") != "fixed" or record.get("status") != "active":
        raise ArtifactIndexError(f"{category} 不是可建索引的固定活动类别")
    if not isinstance(record.get("root"), str):
        raise ArtifactIndexError(f"{category} 缺少类别根")
    return record


def main(arguments: list[str]) -> int:
    if len(arguments) != 3:
        return command_usage()
    category, repository, data_file = arguments
    if category not in {"adr", "spec"}:
        return command_usage()

    repo_root = Path(repository)
    record = load_category(Path(data_file), category)
    category_root = repo_root / str(record["root"])
    documents = discover_documents(category_root, category)
    if category == "adr":
        body = render_adr_index(documents, repo_root)
    else:
        body = render_spec_index(documents, repo_root)

    sys.stdout.write(body)
    warning = write_copy(category_root / "README.md", body)
    if warning:
        print(f"mmw artifact index: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except ArtifactIndexError as error:
        print(f"mmw artifact index: {error}", file=sys.stderr)
        raise SystemExit(1)
