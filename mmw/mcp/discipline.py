#!/usr/bin/env python3
"""把检索工具的使用纪律取出来，拼成派 GPT 时要加在提示词前面的一段。

宿主自己的会话从 MCP 握手拿到服务器说明，Codex 不拿——实测问过一个挂着这三个服务器
的 codex 进程，它答「没有说明」。于是派出去的四个 GPT 角色手里有工具、没有说明书：
它们不知道什么问题该问图、哪两类关系静态分析看不见、候选为什么必须回源码验证。

这个模块不写第三份纪律，只从两处唯一事实来源取：Serena 的在 config/serena-readonly.yml
的 prompt，Graphify 的在 mcp/graphify_mcp.py 的 INSTRUCTIONS。取不出来就非零退出——
那说明插件自己装坏了，让工人裸跑比派发失败更糟。

四个执行面各自怎么拿到纪律，看着像重复，其实是四条互不相通的路：

    Claude Code 主 agent   宿主把 MCP 服务器说明摆进系统提示，直接读到
    Claude subagent        同一个宿主，同样读到
    Codex headless         读不到，由本模块拼进提示词（adapters/claude-code.sh）
    pi 的 subagent         adapter 只交参数不执行派发，插不进去。planner、
                           investigator、reviewer 靠各自技能里那一句，worker
                           靠 agents-pi/mmw-worker.md 的「检索」一节

所以 mmw-planner、mmw-research/internal-brief、mmw-reviewer 里那几句不是可以删掉的
重复：删了 pi 那一侧就没有任何地方讲这件事。
"""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SERENA_CONFIG = PLUGIN_ROOT / "config" / "serena-readonly.yml"


class DisciplineError(RuntimeError):
    """纪律取不出来。插件文件缺失或者格式变了。"""


def _serena_prompt() -> str:
    """读 `prompt: |` 那个块。

    不引 YAML 解析器：多一个依赖，而要读的只有一个固定的块标量。格式一变这里就抛，
    test_mcp.sh 守着这条。
    """
    try:
        lines = SERENA_CONFIG.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DisciplineError(f"读不到 {SERENA_CONFIG}：{exc}") from exc
    start = None
    for index, line in enumerate(lines):
        if line.rstrip() == "prompt: |":
            start = index + 1
            break
    if start is None:
        raise DisciplineError(f"{SERENA_CONFIG} 里没有 `prompt: |` 块")
    body: list[str] = []
    for line in lines[start:]:
        if line.strip() and not line.startswith(" "):
            break
        body.append(line[2:] if line.startswith("  ") else line)
    text = "\n".join(body).strip()
    if not text:
        raise DisciplineError(f"{SERENA_CONFIG} 的 prompt 块是空的")
    return text


def _graphify_instructions() -> str:
    sys.path.insert(0, str(PLUGIN_ROOT / "mcp"))
    try:
        from graphify_mcp import INSTRUCTIONS
    except ImportError as exc:
        raise DisciplineError(f"读不到 graphify_mcp 的 INSTRUCTIONS：{exc}") from exc
    finally:
        sys.path.pop(0)
    text = str(INSTRUCTIONS).strip()
    if not text:
        raise DisciplineError("graphify_mcp 的 INSTRUCTIONS 是空的")
    return text


def preamble() -> str:
    return (
        "## Retrieval tools\n\n"
        "You have three MCP servers mounted. Their own instructions do not reach you, "
        "so they are reproduced here. Follow them.\n\n"
        "### Serena\n\n"
        f"{_serena_prompt()}\n\n"
        "### Graphify\n\n"
        f"{_graphify_instructions()}\n\n"
        "### Context7\n\n"
        "Use context7 to fetch current documentation for any library, framework, SDK or CLI "
        "tool before relying on recalled API details. Call resolve-library-id first unless the "
        "caller gave you an explicit /org/project id.\n\n"
        "---\n\n"
    )


def main() -> int:
    try:
        sys.stdout.write(preamble())
    except DisciplineError as exc:
        print(f"mmw discipline: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
