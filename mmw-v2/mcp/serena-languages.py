#!/usr/bin/env python3
"""把一个仓库的 serena 项目配置补齐成「这个仓库里真有的、我们又装了服务器的」那几门语言。

为什么需要这一步：serena 头一次遇到一个仓库时，非交互地**只启用文件数最多的那一门语言**
（serena/config/serena_config.py 里 `languages_to_use = [top_language_pair[0]]`，其余的只在
`interactive` 为真时才逐个问，而它当 MCP 服务器跑时 `interactive` 是 False）。

后果不是「那门语言慢一点」，是**直接查不到**：`solidlsp/ls.py` 的 `is_ignored_path` 会把不属于
已启用语言的文件判成 ignored，`find_symbol` 于是抛
`Explicitly requested symbols in '…' while the path is ignored`。一个 335 个 .sh 对 75 个 .py
的仓库拿到的就是 `languages: [bash]`，之后每一次查 Python 符号都被拒绝，而报错文字完全不提
语言这回事。

后缀表来自 `mmw-v2/tools/tools.json` 里每个 `language_server` 的 `extensions`——跟装服务器用的
是同一张表，所以不会出现「补了一门语言但没有服务器」。

只改 `languages:` 那一段的文本，不做 YAML 读写往返：serena 生成的 `project.yml` 里每个键上面
都有一段说明，`yaml.safe_dump` 会把它们全抹掉。顺带这个脚本就只用标准库，系统 `python3` 直接
跑得起来，SessionStart 那种每次会话都跑一遍的地方不必再等 uv 起解释器。

    serena-languages.py <仓库>          补齐，改动了就打印一行
    serena-languages.py <仓库> --check  只看齐没齐。齐了回 0，缺东西回 1
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools" / "tools.json"

# `languages:` 到下一个顶格键之间。serena 生成的文件里这一段是 `- 名字` 的列表，
# 中间可能夹注释行。
LANGUAGES_KEY = re.compile(r"^languages:[ \t]*(.*)$")
LIST_ITEM = re.compile(r"^-[ \t]+(\S+)")
TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:")


def extension_map() -> dict[str, list[str]]:
    """{serena 的语言名: [后缀…]}。只包含我们真的装了语言服务器的那几门。"""
    payload = json.loads(TOOLS.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for tool in payload.get("tools", []):
        spec = tool.get("language_server")
        if not spec or not spec.get("extensions"):
            continue
        out.setdefault(spec["serena_language"], []).extend(spec["extensions"])
    return out


def repo_files(repo: Path) -> list[str]:
    """仓库里被跟踪的文件加未忽略的新文件。

    用 git 而不是自己走目录：node_modules、.venv、build 产物都在 .gitignore 里，自己走
    会把它们算进去，于是一个前端仓库会因为 node_modules 里的 .js 被判成一大堆语言。
    """
    out: list[str] = []
    for args in (["ls-files"], ["ls-files", "--others", "--exclude-standard"]):
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True, text=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []
        if result.returncode != 0:
            return []
        out.extend(line for line in result.stdout.splitlines() if line)
    return out


def languages_present(repo: Path) -> list[str]:
    """这个仓库里真有的语言，按文件数从多到少。

    顺序有意义：serena 拿第一门当默认语言，一个文件不属于任何已启用语言时由它兜底。
    """
    mapping = extension_map()
    counts = {lang: 0 for lang in mapping}
    for name in repo_files(repo):
        for lang, extensions in mapping.items():
            if any(name.endswith(ext) for ext in extensions):
                counts[lang] += 1
    present = [(lang, n) for lang, n in counts.items() if n > 0]
    present.sort(key=lambda pair: (-pair[1], pair[0]))
    return [lang for lang, _ in present]


def read_languages(lines: list[str]) -> tuple[int, int, list[str]] | None:
    """找出 `languages:` 那一段。回 (起始行, 结束行的下一行, 现有语言)；找不到回 None。"""
    for start, line in enumerate(lines):
        found = LANGUAGES_KEY.match(line)
        if not found:
            continue
        inline = found.group(1).strip()
        if inline and inline != "[]":
            # `languages: [a, b]` 这种写法。serena 不这么生成，但人可能这么写。
            names = [n.strip().strip("'\"") for n in inline.strip("[]").split(",")]
            return start, start + 1, [n for n in names if n]
        end = start + 1
        names = []
        while end < len(lines):
            text = lines[end]
            if LIST_ITEM.match(text):
                names.append(LIST_ITEM.match(text).group(1))  # type: ignore[union-attr]
                end += 1
                continue
            if text.strip() == "" or text.lstrip().startswith("#"):
                # 空行和注释可能夹在列表中间，也可能已经是下一段。往后看有没有列表项。
                probe = end
                while probe < len(lines) and (
                    lines[probe].strip() == "" or lines[probe].lstrip().startswith("#")
                ):
                    probe += 1
                if probe < len(lines) and LIST_ITEM.match(lines[probe]):
                    end = probe
                    continue
                break
            if TOP_LEVEL_KEY.match(text):
                break
            break
        return start, end, names
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--check", action="store_true")
    opts = parser.parse_args()

    repo = opts.repo.resolve()
    config = repo / ".serena" / "project.yml"
    want = languages_present(repo)
    if not want:
        return 0

    # 配置还不在：serena 还没认过这个仓库。不替它建——它建的时候会写一大堆带默认值的键，
    # 我们凭空造一份就等于把它的默认值抄进来，抄错了没人看得出来。等它建完下一次再补。
    if not config.is_file():
        if opts.check:
            print(f"未配  {config} 还不在，serena 还没认过这个仓库", file=sys.stderr)
            return 1
        return 0

    lines = config.read_text(encoding="utf-8").splitlines(keepends=True)
    block = read_languages(lines)
    if block is None:
        print(f"看不懂  {config} 里没有 languages: 这一段，没有改动", file=sys.stderr)
        return 1
    start, end, have = block
    missing = [lang for lang in want if lang not in have]

    if not missing:
        if opts.check:
            print(f"已配  serena 在 {repo.name} 里认得 {', '.join(have)}")
        return 0

    if opts.check:
        print(f"未配  serena 在 {repo.name} 里少了 {', '.join(missing)}，这些语言的符号查不到",
              file=sys.stderr)
        return 1

    # 只加不删：用户自己加过的语言留着，哪怕我们没装那门的服务器。
    block_lines = [f"- {lang}\n" for lang in list(have) + missing]
    lines[start:end] = ["languages:\n", *block_lines]

    tmp = config.with_suffix(config.suffix + ".mmw-tmp")
    tmp.write_text("".join(lines), encoding="utf-8")
    tmp.replace(config)
    print(f"配好  serena 在 {repo.name} 里补上 {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
