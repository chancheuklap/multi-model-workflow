#!/usr/bin/env python3
"""从唯一 MCP 定义启动一台服务器，供 Codex plugin 的稳定入口调用。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve import Resolver  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("用法：mmw mcp serve <服务器名>", file=sys.stderr)
        return 2

    name = args[0]
    servers = Resolver().servers(want_type=False)
    if name not in servers:
        print(f"mmw mcp serve: 认不出服务器 {name}", file=sys.stderr)
        return 2

    spec = servers[name]
    command = spec.get("command")
    if not isinstance(command, str) or not command:
        print(f"mmw mcp serve: {name} 不是本地 stdio 服务器", file=sys.stderr)
        return 1
    env = dict(os.environ)
    env.update(spec.get("env") or {})
    os.execvpe(command, [command, *(spec.get("args") or [])], env)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
