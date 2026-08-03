#!/usr/bin/env python3
"""真起一次每个 MCP 服务器，握手并列工具。给 mmw doctor 用。

为什么不能只看配置文件在不在：旧实现出过一次真事故——配置在、工具名在工具列表里、
直到模型真去调用才报错，而那时它已经在一次审查中途了。本脚本把服务器进程真拉起来、
走完 MCP 握手、要一次工具列表，能挡住命令不存在、参数写错、白名单文件缺失、Python
依赖缺失这几类。

挡不住的写明：它不发 tools/call，所以查询本身失败（比如图建不起来）这里看不出来。
tools/call 会触发 Graphify 建图，那是分钟级操作，不适合放进一条体检命令。

    probe.py [--json]      读插件根的 .mcp.json，逐个探，逐行报
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = PLUGIN_ROOT / ".mcp.json"
HANDSHAKE_TIMEOUT = 40


def expand(value: str) -> str:
    return value.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT))


def probe(spec: dict) -> tuple[bool, str]:
    """起服务器、握手、列工具。回 (成不成, 说人话的一句)。

    三条请求一次性写进 stdin 再用 communicate 收全部输出：stdio 上逐条 readline
    没有超时机制，服务器一卡住体检命令就跟着挂死，而体检本身必须有头。
    """
    command = expand(spec["command"])
    args = [expand(a) for a in spec.get("args", [])]
    env = dict(os.environ)
    env.update({k: expand(v) for k, v in (spec.get("env") or {}).items()})

    try:
        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        return False, f"起不来：找不到命令 {command}"
    except OSError as exc:
        return False, f"起不来：{exc}"

    requests = "".join(json.dumps(obj) + "\n" for obj in (
        {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mmw-doctor", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ))

    try:
        out, err = proc.communicate(input=requests, timeout=HANDSHAKE_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return False, f"{HANDSHAKE_TIMEOUT} 秒内没应答"
    finally:
        if proc.poll() is None:
            proc.kill()

    payload = None
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == 2:
            payload = obj
            break

    if payload is None:
        tail = (err or "").strip().splitlines()
        return False, f"没要到工具列表：{tail[-1] if tail else '进程没输出就退了'}"
    if "error" in payload:
        return False, f"服务器报错：{payload['error']}"
    tools = sorted(t["name"] for t in payload.get("result", {}).get("tools", []))
    return True, f"{len(tools)} 个工具：{', '.join(tools)}"


def main() -> int:
    as_json = "--json" in sys.argv[1:]
    if not MCP_JSON.is_file():
        print(f"ERROR: 插件里没有 .mcp.json: {MCP_JSON}", file=sys.stderr)
        return 2
    servers = json.loads(MCP_JSON.read_text(encoding="utf-8")).get("mcpServers", {})
    results, status = {}, 0
    for name, spec in servers.items():
        ok, detail = probe(spec)
        results[name] = {"ok": ok, "detail": detail}
        if not ok:
            status = 1
        if not as_json:
            print(f"{'可用' if ok else '不可用'}  {name}：{detail}")
    if as_json:
        print(json.dumps(results, ensure_ascii=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
