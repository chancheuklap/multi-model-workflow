#!/usr/bin/env python3
"""把插件根的 .mcp.json 展开成某个执行面要的形状。唯一的展开器。

`.mcp.json` 是服务器定义的唯一事实来源，但四个执行面各要不同的形状，而且里面的
`${…}` 占位符要在写出去之前换成这台机器上的真值。展开规则收在本文件一处——分散
到 install-mcp.sh、claude-code.sh、probe.py 各写一遍，加一条新占位符就要改三处，
漏改的那一处会静默写出带 `${…}` 原文的配置。

两类占位符：

    ${CLAUDE_PLUGIN_ROOT}   插件根的绝对路径
    ${VAR} / ${VAR:-默认}   先查进程环境，再查密钥文件，都没有就用默认值

密钥文件是 ~/.mmw/secrets.env（`MMW_SECRETS_FILE` 可覆盖），`KEY=value` 一行一条，
`#` 开头是注释。密钥不进仓库，所以 .mcp.json 里只写声明不写值。

`env` 字段里展开成空串的键会被丢掉，不写成空值——空值和「没配」对下游是两回事，
而我们要的就是「没配」这个语义（比如没有 API key 时按免费额度跑）。

    resolve.py                逐行报每个占位符解析成了什么，不输出值本身
    resolve.py --format raw    展开后的 {"mcpServers": {...}}
    resolve.py --format pi     pi 的 ~/.pi/agent/mcp.json 要的服务器 map（带 type）
    resolve.py --format cursor Cursor 的 ~/.cursor/mcp.json 要的服务器 map（不带 type）
    resolve.py --format codex  codex exec -c 要的 key=value，一行一条
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = PLUGIN_ROOT / ".mcp.json"

# ${VAR} 与 ${VAR:-默认}。默认值里不允许再出现 }，够用且不用写递归解析。
PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def secrets_file() -> Path:
    return Path(os.environ.get("MMW_SECRETS_FILE") or Path.home() / ".mmw" / "secrets.env")


def load_secrets() -> dict[str, str]:
    path = secrets_file()
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip("'\"")
    return out


class Resolver:
    def __init__(self) -> None:
        self.secrets = load_secrets()
        # 每个变量解析自哪里，给 --format 缺省的那个报告用。不记值。
        self.origins: dict[str, str] = {}

    def expand(self, value: str) -> str:
        value = value.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT))

        def sub(match: re.Match[str]) -> str:
            name, default = match.group(1), match.group(2)
            if os.environ.get(name):
                self.origins[name] = "进程环境"
                return os.environ[name]
            if self.secrets.get(name):
                self.origins[name] = f"密钥文件 {secrets_file()}"
                return self.secrets[name]
            self.origins[name] = "没配，用默认值" if default is not None else "没配，也没有默认值"
            return default if default is not None else match.group(0)

        return PLACEHOLDER.sub(sub, value)

    def server(self, spec: dict, *, want_type: bool) -> dict:
        out: dict = {"type": "stdio"} if want_type else {}
        out["command"] = self.expand(spec["command"])
        args = [self.expand(a) for a in spec.get("args") or []]
        if args:
            out["args"] = args
        env = {k: self.expand(v) for k, v in (spec.get("env") or {}).items()}
        env = {k: v for k, v in env.items() if v}
        if env:
            out["env"] = env
        return out

    def servers(self, *, want_type: bool) -> dict[str, dict]:
        source = json.loads(MCP_JSON.read_text(encoding="utf-8"))["mcpServers"]
        return {name: self.server(spec, want_type=want_type) for name, spec in source.items()}


def toml_scalar(value: str) -> str:
    return json.dumps(value)


def as_codex(servers: dict[str, dict]) -> str:
    lines = []
    for name, spec in servers.items():
        lines.append(f"mcp_servers.{name}.command={toml_scalar(spec['command'])}")
        if spec.get("args"):
            lines.append(f"mcp_servers.{name}.args={json.dumps(spec['args'])}")
        if spec.get("env"):
            inner = ", ".join(f"{k}={toml_scalar(v)}" for k, v in spec["env"].items())
            lines.append(f"mcp_servers.{name}.env={{{inner}}}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--format", choices=["raw", "pi", "cursor", "codex"])
    opts = parser.parse_args()

    if not MCP_JSON.is_file():
        print(f"ERROR: 插件里没有 .mcp.json: {MCP_JSON}", file=sys.stderr)
        return 2

    resolver = Resolver()
    fmt = opts.format
    servers = resolver.servers(want_type=(fmt == "pi"))

    if fmt == "raw":
        print(json.dumps({"mcpServers": servers}, ensure_ascii=False, indent=2))
    elif fmt in ("pi", "cursor"):
        print(json.dumps(servers, ensure_ascii=False, indent=2))
    elif fmt == "codex":
        text = as_codex(servers)
        if text:
            print(text)
    else:
        # 缺省是给人看的报告：哪个占位符从哪儿来。不打印值——里面有密钥。
        if not resolver.origins:
            print("这份 .mcp.json 里没有要解析的占位符")
        for name, origin in sorted(resolver.origins.items()):
            print(f"{name}: {origin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
