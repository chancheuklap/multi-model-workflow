#!/usr/bin/env python3
"""真起一次每个 MCP 服务器，握手并列工具。给 mmw doctor 用。

为什么不能只看配置文件在不在：旧实现出过一次真事故——配置在、工具名在工具列表里、
直到模型真去调用才报错，而那时它已经在一次审查中途了。本脚本把服务器进程真拉起来、
走完 MCP 握手、要一次工具列表，能挡住命令不存在、参数写错、白名单文件缺失、Python
依赖缺失这几类。

挡不住的写明：它不发 tools/call，所以查询本身失败（比如图建不起来）这里看不出来。
tools/call 会触发 Graphify 建图，那是分钟级操作，不适合放进一条体检命令。

    probe.py [--json] [--config 文件]  逐个探，逐行报
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve import MCP_JSON, Resolver  # noqa: E402  展开规则的唯一来源

HANDSHAKE_TIMEOUT = 40


def probe(spec: dict) -> tuple[bool, str, list[str], str, dict[str, dict]]:
    """起服务器、握手、列工具。回状态、说明、工具名、服务器说明与工具定义。

    默认 spec 由 Resolver 展开。--config 读到的是宿主最终配置；两种路径都探真正会启动的
    command、args、env 与 cwd。

    三条请求一次性写进 stdin 再用 communicate 收全部输出：stdio 上逐条 readline
    没有超时机制，服务器一卡住体检命令就跟着挂死，而体检本身必须有头。
    """
    command = spec["command"]
    args = spec.get("args", [])
    env = dict(os.environ)
    env.update(spec.get("env") or {})

    try:
        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=spec.get("cwd"),
        )
    except FileNotFoundError:
        return False, f"起不来：找不到命令 {command}", [], "", {}
    except OSError as exc:
        return False, f"起不来：{exc}", [], "", {}

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
        return False, f"{HANDSHAKE_TIMEOUT} 秒内没应答", [], "", {}
    finally:
        if proc.poll() is None:
            proc.kill()

    init_payload = None
    payload = None
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == 1:
            init_payload = obj
        elif obj.get("id") == 2:
            payload = obj

    if payload is None:
        tail = (err or "").strip().splitlines()
        return False, f"没要到工具列表：{tail[-1] if tail else '进程没输出就退了'}", [], "", {}
    if "error" in payload:
        return False, f"服务器报错：{payload['error']}", [], "", {}
    tool_specs = {
        tool["name"]: tool for tool in payload.get("result", {}).get("tools", [])
    }
    tools = sorted(tool_specs)
    instructions = ""
    if init_payload:
        instructions = str(init_payload.get("result", {}).get("instructions") or "")
    return True, f"{len(tools)} 个工具：{', '.join(tools)}", tools, instructions, tool_specs


CONTRACT = Path(__file__).resolve().parent.parent / "config" / "retrieval-contract.json"


def contract_servers() -> tuple[dict, str | None]:
    """读裁剪面合同。回 (每个服务器要什么, 读不出来的原因)。

    读不出来不当场停：探测本身的价值不该被合同缺失抹掉。但也不能悄悄跳过——
    护栏没检查跟护栏检查通过是两回事，所以单报一行，并且让退出码非零。
    """
    try:
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"读不出 {CONTRACT}：{exc}"
    return payload.get("servers", {}), None


def contract_drift(
    name: str,
    tools: list[str],
    instructions: str,
    tool_specs: dict[str, dict],
    servers: dict,
) -> str | None:
    """比对集合相等，回一句说人话的差异；对得上回 None。

    多一个和少一个都算失败，而且不是同一件事：少了是能力缺失，多了是护栏破了——
    上游默认多暴露一个工具，五个派出去的角色立刻都拿得到。
    """
    spec = servers.get(name)
    if not spec or "exact_tools" not in spec:
        return None
    extra = sorted(set(tools) - set(spec["exact_tools"]))
    missing = sorted(set(spec["exact_tools"]) - set(tools))
    parts = []
    if extra:
        parts.append(f"多了 {', '.join(extra)}")
    if missing:
        parts.append(f"少了 {', '.join(missing)}")
    missing_instructions = [
        token for token in spec.get("instruction_tokens", []) if token not in instructions
    ]
    if missing_instructions:
        parts.append(f"服务器说明少了 {', '.join(missing_instructions)}")
    if "actions" in spec:
        action_enum = (
            tool_specs.get(name, {})
            .get("inputSchema", {})
            .get("properties", {})
            .get("action", {})
            .get("enum", [])
        )
        if set(action_enum) != set(spec["actions"]):
            parts.append(
                "action 不一致："
                f"实际 {', '.join(sorted(action_enum)) or '(空)'}；"
                f"合同 {', '.join(sorted(spec['actions']))}"
            )
    return "；".join(parts) or None


def configured_servers(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    servers = payload.get("mcpServers") or payload.get("mcp_servers") or payload
    if not isinstance(servers, dict):
        raise ValueError("MCP 配置不是服务器 map")
    return servers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--config", type=Path)
    opts = parser.parse_args()
    as_json = opts.json
    if opts.config:
        try:
            servers = configured_servers(opts.config)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"ERROR: 读不到 MCP 配置 {opts.config}: {exc}", file=sys.stderr)
            return 2
    else:
        if not MCP_JSON.is_file():
            print(f"ERROR: 插件里没有 .mcp.json: {MCP_JSON}", file=sys.stderr)
            return 2
        servers = Resolver().servers(want_type=False)
    contract, contract_error = contract_servers()
    results, status = {}, 0
    if contract_error:
        status = 1
        results["_contract"] = {"ok": False, "detail": contract_error}
        if not as_json:
            print(f"不可用  裁剪合同：{contract_error}。这一轮没做护栏检查")
    for name, spec in servers.items():
        ok, detail, tools, instructions, tool_specs = probe(spec)
        drift = (
            contract_drift(name, tools, instructions, tool_specs, contract) if ok else None
        )
        if drift:
            ok = False
            detail = f"{detail}。跟裁剪合同对不上：{drift}"
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
