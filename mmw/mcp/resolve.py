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

pi 那一面的 `env` 不写密钥明文，只写 `${VAR}`。`~/.pi/agent/mcp.json` 是入库文件，
写进去的密钥下一次 `git add` 就跟着进仓库。Pi 启动服务器时自己把 `${VAR}` 换成
进程环境里的值，所以值必须已经导出到 shell 环境；光写在密钥文件里 Pi 看不到。
install-mcp.sh 装完会对每个保留下来的变量查一次可达性，取不到当场报出来。

    resolve.py                逐行报每个占位符解析成了什么，不输出值本身
    resolve.py --format raw    展开后的 {"mcpServers": {...}}
    resolve.py --format pi     pi 的 ~/.pi/agent/mcp.json 要的服务器 map（带 type）
    resolve.py --format cursor Cursor 的 ~/.cursor/mcp.json 要的服务器 map（不带 type）
    resolve.py --format codex  Claude Code 启动 headless Codex 时注入的 key=value
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
# 整个值恰好是一个占位符。只有这种形状能改写成宿主自己展开的 ${VAR}：
# 拼了前缀后缀的值改写之后，宿主只认变量那一段，周围的字面量会掉。
SOLE_PLACEHOLDER = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}$")


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
        # 以 ${VAR} 原样写出去、交给宿主自己展开的变量名。
        self.kept_placeholders: set[str] = set()

    def lookup(self, name: str) -> str:
        """变量在这台机器上的真值。没配返回空串，不看占位符自带的默认值。"""
        return os.environ.get(name) or self.secrets.get(name) or ""

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

    def env_value(self, raw: str, *, keep_placeholder: bool) -> str | None:
        """算一个 env 值。返回 None 表示这个键要丢掉。"""
        expanded = self.expand(raw)
        if not expanded:
            return None
        if not keep_placeholder:
            return expanded
        match = SOLE_PLACEHOLDER.match(raw)
        if not match:
            return expanded
        name = match.group(1)
        # 值来自占位符自带的默认值时不能改写：那个默认值不在环境里，宿主会展成空串。
        if not self.lookup(name):
            return expanded
        self.kept_placeholders.add(name)
        return f"${{{name}}}"

    def server(self, spec: dict, *, want_type: bool, keep_env_placeholders: bool = False) -> dict:
        out: dict = {"type": "stdio"} if want_type else {}
        out["command"] = self.expand(spec["command"])
        args = [self.expand(a) for a in spec.get("args") or []]
        if args:
            out["args"] = args
        env = {
            key: self.env_value(value, keep_placeholder=keep_env_placeholders)
            for key, value in (spec.get("env") or {}).items()
        }
        env = {key: value for key, value in env.items() if value}
        if env:
            out["env"] = env
        return out

    def servers(self, *, want_type: bool, keep_env_placeholders: bool = False) -> dict[str, dict]:
        source = json.loads(MCP_JSON.read_text(encoding="utf-8"))["mcpServers"]
        return {
            name: self.server(spec, want_type=want_type, keep_env_placeholders=keep_env_placeholders)
            for name, spec in source.items()
        }


def unreachable_note(resolver: Resolver, name: str) -> str:
    """pi 那一面留了占位符，而 Pi 自己取不到值时的提醒。

    Pi 启动服务器时只查自己的进程环境，不读密钥文件。取不到就展成空串，
    服务器拿到空 key 当成配错，而配置文件看上去是对的——这种失败要当场看得见。
    """
    if name not in resolver.kept_placeholders or os.environ.get(name):
        return ""
    return f"（pi 写 ${{{name}}}，但它不在进程环境里，Pi 会展成空串；在 shell 启动文件里导出它）"


def toml_scalar(value: str) -> str:
    return json.dumps(value)


def grok_table(name: str, spec: dict) -> str:
    lines = [f"[mcp_servers.{name}]"]
    lines.append(f"command = {json.dumps(spec['command'])}")
    if spec.get("args"):
        args = ", ".join(json.dumps(item) for item in spec["args"])
        lines.append(f"args = [{args}]")
    env = spec.get("env") or {}
    if env:
        inner = ", ".join(f"{key} = {json.dumps(value)}" for key, value in env.items())
        lines.append(f"env = {{ {inner} }}")
    return "\n".join(lines) + "\n"


def table_header(line: str) -> str | None:
    """这一行是表头就返回表名，否则返回 None。`[[a.b]]` 与 `[a.b]` 都返回 `a.b`。"""
    text = line.strip()
    if not text.startswith("[") or not text.endswith("]"):
        return None
    if text.startswith("[["):
        return text[2:-2].strip() if text.endswith("]]") else None
    return text[1:-1].strip()


def owns_table(table: str, name: str) -> bool:
    """这个表属于服务器 name 自己：`mcp_servers.name` 或它的子表。"""
    root = f"mcp_servers.{name}"
    return table == root or table.startswith(root + ".")


def upsert_grok_config(path: Path, servers: dict[str, dict]) -> None:
    """把三台服务器写进 Grok 的 config.toml，保留文件里其他内容。

    整块替换，而且连子表一起替换：Grok 自己保存配置时会把 `env = { … }` 内联表
    改写成 `[mcp_servers.<name>.env]` 子表。只替换到子表前面就会留下那份子表，
    加上新写的内联 env，同一个 key 出现两次，Grok 下次启动报 duplicate key。

    按行找表头，不做完整 TOML 解析。config.toml 里出现以 `[` 起头的多行字符串
    时这个判断会错——这份文件由 Grok 和本函数写，两边都不产生那种值。
    """
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    for name, spec in servers.items():
        text = replace_grok_server(text, name, grok_table(name, spec))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_grok_server(text: str, name: str, block: str) -> str:
    kept: list[str] = []
    insert_at: int | None = None
    dropping = False
    for line in text.splitlines(keepends=True):
        table = table_header(line)
        if table is not None:
            dropping = owns_table(table, name)
            if dropping and insert_at is None:
                insert_at = len(kept)
        if not dropping:
            kept.append(line)
    if insert_at is None:
        if kept and kept[-1].strip():
            kept.append("\n")
        kept.append(block)
        return "".join(kept)
    if insert_at < len(kept) and kept[insert_at].strip():
        block += "\n"
    kept.insert(insert_at, block)
    return "".join(kept)


def grok_config_has_servers(path: Path, servers: dict[str, dict]) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    for name, spec in servers.items():
        if f"[mcp_servers.{name}]" not in text:
            return False
        if spec["command"] not in text:
            return False
    return True


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
    parser.add_argument("--format", choices=["raw", "pi", "cursor", "codex", "grok"])
    parser.add_argument(
        "--merge-grok",
        metavar="PATH",
        help="把 Grok 格式的三台服务器合并进这份 config.toml",
    )
    opts = parser.parse_args()

    if not MCP_JSON.is_file():
        print(f"ERROR: 插件里没有 .mcp.json: {MCP_JSON}", file=sys.stderr)
        return 2

    resolver = Resolver()
    if opts.merge_grok:
        servers = resolver.servers(want_type=False, keep_env_placeholders=False)
        upsert_grok_config(Path(opts.merge_grok).expanduser(), servers)
        return 0
    fmt = opts.format
    # 只有 pi 那一面的目标文件入库。codex 靠命令行注入、退出即无痕，raw 要拿真值去拉
    # 服务器做体检，Cursor 的配置不在任何仓库里。
    # 缺省报告跟着 pi 面的规则跑：只有它会把值留成占位符，报告要能说出这件事。
    keep_placeholders = fmt in (None, "pi")
    servers = resolver.servers(want_type=(fmt == "pi"), keep_env_placeholders=keep_placeholders)

    if fmt == "raw":
        print(json.dumps({"mcpServers": servers}, ensure_ascii=False, indent=2))
    elif fmt in ("pi", "cursor", "grok"):
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
            print(f"{name}: {origin}{unreachable_note(resolver, name)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
