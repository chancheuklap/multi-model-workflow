#!/usr/bin/env python3
"""真起一次每个 MCP 服务器，握手并列工具。给安装后的体检用。

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
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# pyright: reportMissingImports=false
# resolve 是同目录的兄弟模块，靠上一行的 sys.path 才找得到；静态检查跟不进运行期
# 改的搜索路径。
from resolve import MCP_JSON, Resolver  # noqa: E402  展开规则的唯一来源

HANDSHAKE_TIMEOUT = 40
SMOKE_TIMEOUT = 180

# 服务器默认从仓库根启动。serena 用 --project-from-cwd 认项目，从别处起它就没有
# 项目可查，冒烟那一关会失败在一个跟真实故障无关的地方。
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def probe(spec: dict, smoke: dict | None = None) -> tuple[bool, str, list[str], str]:
    """起服务器、握手、列工具，必要时再真调一次工具。

    回状态、一句话、工具名与服务器下发的 instructions。

    默认 spec 由 Resolver 展开。--config 读到的是宿主最终配置；两种路径都探真正会启动的
    command、args、env 与 cwd。

    stdin 全程开着，用一个后台线程收 stdout，主线程按截止时间等自己要的那几条回应。
    不能写完就关 stdin：实测 serena 答完 tools/list 就跟着 EOF 关掉了，后面那条
    tools/call 根本没被处理，而现象是「没有回应」，跟服务器坏掉长得一模一样。
    也不能在主线程上逐条 readline：stdio 上的 readline 没有超时，服务器一卡住体检
    命令就跟着挂死，而体检本身必须有头。
    """
    command = spec["command"]
    args = spec.get("args", [])
    env = dict(os.environ)
    env.update(spec.get("env") or {})
    timeout = SMOKE_TIMEOUT if smoke else HANDSHAKE_TIMEOUT

    try:
        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=spec.get("cwd") or str(REPO_ROOT),
        )
    except FileNotFoundError:
        return False, f"起不来：找不到命令 {command}", [], ""
    except OSError as exc:
        return False, f"起不来：{exc}", [], ""

    calls = [
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
    ]
    if smoke:
        calls.append({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": smoke["tool"], "arguments": smoke.get("arguments", {})},
        })
    wanted_ids = {2, 3} if smoke else {2}

    seen: dict[int, dict] = {}
    errors: list[str] = []
    instructions = ""

    def collect() -> None:
        for line in proc.stdout:  # type: ignore[union-attr]
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ident = obj.get("id")
            if isinstance(ident, int):
                seen[ident] = obj

    # stderr 也用线程收，不在杀进程之后 read()。serena 会派生 pyright、bash 与
    # typescript 三个语言服务器，它们继承同一个 stderr；杀掉 serena 本身管道不会关，
    # read() 会一直等 EOF 等不到——实测体检命令因此挂死超过十分钟。
    def collect_errors() -> None:
        for line in proc.stderr:  # type: ignore[union-attr]
            errors.append(line)

    reader = threading.Thread(target=collect, daemon=True)
    reader.start()
    threading.Thread(target=collect_errors, daemon=True).start()

    try:
        proc.stdin.write("".join(json.dumps(obj) + "\n" for obj in calls))  # type: ignore[union-attr]
        proc.stdin.flush()  # type: ignore[union-attr]
    except OSError as exc:
        proc.kill()
        return False, f"写不进去：{exc}", [], ""

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if wanted_ids <= seen.keys():
            break
        if proc.poll() is not None and not reader.is_alive():
            break
        time.sleep(0.2)

    proc.kill()
    err = "".join(errors)

    if 1 in seen:
        instructions = seen[1].get("result", {}).get("instructions", "") or ""

    payload = seen.get(2)
    if payload is None:
        tail = err.strip().splitlines()
        return False, f"没要到工具列表：{tail[-1] if tail else '进程没输出就退了'}", [], instructions
    if "error" in payload:
        return False, f"服务器报错：{payload['error']}", [], instructions

    tools = sorted(tool["name"] for tool in payload.get("result", {}).get("tools", []))
    detail = f"{len(tools)} 个工具：{', '.join(tools)}"

    if smoke:
        # 工具列表对得上不等于答得出来。这一关真调一次，答不出就是装坏了。
        answer = seen.get(3)
        if answer is None:
            return False, f"{detail}。{timeout} 秒内没等到 {smoke['tool']} 的回应", tools, instructions
        if "error" in answer:
            return False, f"{detail}。调 {smoke['tool']} 报错：{answer['error']}", tools, instructions
        result = answer.get("result", {})
        body = json.dumps(result, ensure_ascii=False)
        # MCP 的工具错误不走 JSON-RPC 的 error，走 result 里的 isError。不单独认它的话，
        # 一次失败的调用会被当成一次「答得出但内容不对」，报错指向错的地方。
        if result.get("isError"):
            return False, f"{detail}。调 {smoke['tool']} 失败：{body[:300]}", tools, instructions
        if smoke["expect_contains"] not in body:
            return False, (
                f"{detail}。调 {smoke['tool']} 答不出 {smoke['expect_contains']}，"
                "语言服务器可能起不来或版本不合"
            ), tools, instructions
        detail = f"{detail}；{smoke['tool']} 真查得到符号"

    return True, detail, tools, instructions


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


def contract_drift(name: str, tools: list[str], servers: dict) -> str | None:
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
    return "；".join(parts) or None


def pi_cache_path() -> Path:
    """Pi 的说明缓存在哪。跟 install-mcp.sh 用同一条优先级，两边指向同一个文件。"""
    override = os.environ.get("MMW_PI_MCP_FILE")
    if override:
        return Path(override).parent / "mcp-cache.json"
    agent = os.environ.get("PI_CODING_AGENT_DIR")
    if agent:
        return Path(agent) / "mcp-cache.json"
    home = os.environ.get("PI_HOME") or str(Path.home() / ".pi")
    return Path(home) / "agent" / "mcp-cache.json"


def pi_cache_drift(name: str, live: str) -> str | None:
    """Pi 端缓存的说明跟服务器现在下发的对不上时，回一句差异；对得上或没缓存回 None。

    Pi 判缓存失效只看配置哈希——command、args、env、cwd 与工具过滤，说明正文不在里面，
    条目七天有效。于是改完说明不重装，另外四个宿主下一次启动就是新的，只有 Pi 继续把
    上一版读进上下文，而且没有任何一处会说出来。装的时候 install-mcp.sh 会清掉这些条目；
    这里管的是改完直接体检、没重装的那条路。
    """
    try:
        cached = json.loads(pi_cache_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    entry = (cached.get("servers") or {}).get(name)
    if not isinstance(entry, dict) or "instructions" not in entry:
        return None
    stale = entry.get("instructions") or ""
    if stale == live:
        return None
    return (f"Pi 端缓存的还是上一版说明（缓存 {len(stale)} 字，现在下发 {len(live)} 字）；"
            f"跑一次 mmw-v2/install.sh 清掉它")


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
            print(f"ERROR: 没找到 .mcp.json: {MCP_JSON}", file=sys.stderr)
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
        ok, detail, tools, instructions = probe(spec, contract.get(name, {}).get("smoke"))
        drift = contract_drift(name, tools, contract) if ok else None
        if drift:
            ok = False
            detail = f"{detail}。跟裁剪合同对不上：{drift}"
        stale = pi_cache_drift(name, instructions) if ok else None
        if stale:
            ok = False
            detail = f"{detail}。{stale}"
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
