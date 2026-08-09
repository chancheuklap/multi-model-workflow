#!/usr/bin/env python3
"""对刚改过的文件跑一遍诊断，把问题按统一格式打回给 agent。

三个宿主共用这一个入口，只是触发方式不同：Claude Code 有原生 LSP 通道，不需要它；
Codex 从 hooks.json 的 PostToolUse 调它；Pi 从扩展的 tool_execution_end 调它。
同一个仓库、同一份规则表、同一批检查器，所以三家看到的诊断是同一套。

为什么不自己写一个 LSP 客户端：跳转定义、找引用、找实现、列符号这四件事 Serena 已经
在四个宿主上都给了。缺的只有"编辑之后这个文件错没错"。而 pyright 的命令行和它的
language server 是同一个引擎，命令行跑出来的诊断和 LSP 推的是同一批——为这一件事再
维护一套 JSON-RPC 进程管理，多出来的只有故障点。

只读：跑检查器，读输出。不改文件。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CHECK_TIMEOUT = 120
MAX_LINES = 40


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def which(name: str) -> str:
    from shutil import which as _which

    return _which(name) or ""


def owning_workspace(repo: Path, rel_file: str, marker: str) -> str:
    """从文件往上找最近的工作区标记。一个仓库里可以有三个 Electron 壳各带一份
    node_modules，检查器必须用文件所属那一个，不是仓库根那一个。"""
    current = (repo / rel_file).parent
    while True:
        if (current / marker).is_file():
            return str(current.relative_to(repo)) or "."
        if current == repo or repo not in current.parents:
            return "."
        current = current.parent


def resolve_checker(repo: Path, workspace: str, checker: dict) -> str:
    for rel in checker.get("project_bin", []):
        candidate = repo / workspace / rel
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return which(checker.get("bin", ""))


def parse_pyright_json(raw: str, repo: Path) -> list[str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [line for line in raw.splitlines() if line.strip()][:MAX_LINES]
    out = []
    for item in payload.get("generalDiagnostics", []):
        if item.get("severity") not in ("error", "warning"):
            continue
        start = item.get("range", {}).get("start", {})
        path = item.get("file", "")
        try:
            path = str(Path(path).relative_to(repo))
        except ValueError:
            pass
        message = " ".join(str(item.get("message", "")).split())
        rule = item.get("rule", "")
        suffix = f" ({rule})" if rule else ""
        out.append(
            f"{path}:{start.get('line', 0) + 1}:{start.get('character', 0) + 1}: "
            f"{item.get('severity')} {message}{suffix}"
        )
    return out


def parse_concise(raw: str, repo: Path) -> list[str]:
    lines = []
    for line in raw.splitlines():
        text = line.strip()
        if not text or text.startswith("Found ") or text.startswith("["):
            continue
        if text.startswith("All checks passed"):
            continue
        lines.append(text)
    return lines


PARSERS = {"pyright_json": parse_pyright_json, "concise": parse_concise}


def run_checker(repo: Path, workspace: str, checker: dict, rel_file: str) -> list[str]:
    executable = resolve_checker(repo, workspace, checker)
    if not executable:
        return []
    workdir = repo / workspace
    try:
        target = str((repo / rel_file).relative_to(workdir))
    except ValueError:
        target = str(repo / rel_file)
    command = [executable, *checker.get("file_args", []), target]
    try:
        result = subprocess.run(
            command,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        # 检查器跑不起来要说出来，不能静默当成"没问题"——那会让漏掉的错误看起来
        # 像通过了。
        return [f"（{checker['id']} 没能跑起来：{exc}）"]
    raw = f"{result.stdout}\n{result.stderr}".strip()
    parser = PARSERS.get(checker.get("parse", "concise"), parse_concise)
    return parser(raw, repo)


LINE_PATTERN = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+):")


def changed_lines(repo: Path, rel_file: str) -> set[int] | None:
    """这个文件相对 HEAD 改了哪几行。返回 None 表示"拿不到"，调用方据此不过滤。

    为什么要这一层：一个有历史类型债的文件，每次编辑都会把那几十条旧账全报一遍。
    报三次之后没有人会再看它，这个通道就废了。只报落在改动行上的，剩下的历史债由
    专门的一轮去清（跑 mmw toolchain detect 或 CI 的全仓审计入口）。
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "diff", "--unified=0", "HEAD", "--", rel_file],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    diff = result.stdout
    if not diff.strip():
        # 相对 HEAD 没有差异。可能是未跟踪的新文件——那种情况整份都是新的，不过滤。
        tracked = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--error-unmatch", rel_file],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return set() if tracked.returncode == 0 else None
    lines: set[int] = set()
    for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.MULTILINE):
        start = int(hunk.group(1))
        count = int(hunk.group(2) or 1)
        lines.update(range(start, start + count))
    return lines


def filter_to_changed(entries: list[str], rel_file: str, allowed: set[int] | None) -> list[str]:
    if allowed is None:
        return entries
    kept = []
    for entry in entries:
        found = LINE_PATTERN.match(entry)
        if not found:
            kept.append(entry)
            continue
        if not entry.startswith(rel_file):
            kept.append(entry)
            continue
        if int(found.group("line")) in allowed:
            kept.append(entry)
    return kept


def suffix_matches(rule: dict, rel_file: str) -> bool:
    server = rule.get("server") or {}
    extensions = list(server.get("extensions", {}).keys())
    if not extensions:
        globs = rule.get("detect", {}).get("tracked_glob", [])
        extensions = [g[1:] for g in globs if g.startswith("*.")]
    return any(rel_file.endswith(ext) for ext in extensions)


def check(repo: Path, rules_path: Path, files: list[str], changed_only: bool = False) -> dict:
    table = read_json(rules_path)
    rules = table.get("rules", [])
    findings: dict[str, list[str]] = {}
    skipped: list[str] = []
    suppressed = 0

    for raw_file in files:
        path = Path(raw_file)
        if not path.is_absolute():
            path = (repo / raw_file).resolve()
        if not path.is_file():
            continue
        try:
            rel_file = str(path.relative_to(repo))
        except ValueError:
            continue

        allowed = changed_lines(repo, rel_file) if changed_only else None

        matched = False
        for rule in rules:
            if not suffix_matches(rule, rel_file):
                continue
            marker = "package.json" if rule["id"] in ("typescript", "react") else "pyproject.toml"
            workspace = owning_workspace(repo, rel_file, marker)
            for checker in rule.get("checkers", []):
                if not checker.get("per_file"):
                    continue
                matched = True
                lines = run_checker(repo, workspace, checker, rel_file)
                if not lines:
                    continue
                kept = filter_to_changed(lines, rel_file, allowed)
                suppressed += len(lines) - len(kept)
                if kept:
                    findings.setdefault(checker["id"], []).extend(kept)
        if not matched:
            skipped.append(rel_file)

    return {"findings": findings, "skipped": skipped, "suppressed": suppressed}


def render(report: dict) -> int:
    findings = report["findings"]
    suppressed = report.get("suppressed", 0)
    if not findings:
        # 只在真的压掉了东西时才提一句，否则每次干净通过都多一行噪音。
        if suppressed:
            print(
                f"（改动行上没有问题。这些文件另有 {suppressed} 条既有问题，不是这次引入的。）",
                file=sys.stderr,
            )
        return 0
    total = 0
    for checker_id, lines in findings.items():
        shown = lines[:MAX_LINES]
        total += len(lines)
        print(f"{checker_id}:", file=sys.stderr)
        for line in shown:
            print(f"  {line}", file=sys.stderr)
        if len(lines) > len(shown):
            print(f"  （还有 {len(lines) - len(shown)} 条未显示）", file=sys.stderr)
    tail = f"，另有 {suppressed} 条既有问题不是这次引入的" if suppressed else ""
    print(f"改动行上共 {total} 条{tail}。先看一遍再继续。", file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    repo = None
    rules_path = None
    as_json = False
    changed_only = False
    files: list[str] = []
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--repo":
            repo = Path(args.pop(0)).resolve()
        elif arg == "--rules":
            rules_path = Path(args.pop(0)).resolve()
        elif arg == "--json":
            as_json = True
        elif arg == "--changed-only":
            changed_only = True
        else:
            files.append(arg)
    if repo is None or rules_path is None:
        print(
            "用法：toolchain_check.py --repo <仓库根> --rules <规则表> [--changed-only] <文件>...",
            file=sys.stderr,
        )
        return 1
    if not files:
        return 0

    report = check(repo, rules_path, files, changed_only=changed_only)
    if as_json:
        print(json.dumps(report, ensure_ascii=False))
        return 0
    return render(report)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
