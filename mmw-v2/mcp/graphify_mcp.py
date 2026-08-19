#!/usr/bin/env python3
"""把 Graphify 结构检索包成一个常驻 MCP 工具，各宿主共用。

一次调用内先跑 ensure 保证图对得上当前 checkout，再按 action 查询。查询直接调
官方 `graphify` CLI，本文件不重写检索语义。

刻意不用官方 `graphify-mcp`（`python -m graphify.serve`），两条理由都实测过：
它暴露 10 个工具（query_graph / get_node / … ，其中 list_prs / get_pr_impact /
triage_prs 三个查 GitHub PR，跟结构检索无关，还会跟我们自己的 issue 约定打架），
而且它假定 graph.json 已存在、不检查新鲜度——图过期时它照样回答，回答的是历史。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROTOCOL_VERSION = "2024-11-05"
DEFAULT_BUDGET = 2000
DEFAULT_DEPTH = 2
ENSURE_TIMEOUT = 900
QUERY_TIMEOUT = 120

# 宿主在 MCP 握手时读到这一段，是 Graphify 使用纪律的单一事实来源。
#
# 写在这里而不是技能里：技能是按任务装的，而这段话要在每一次结构性提问时都在场。
#
# 前 150 字符要自足——Pi 的 mcp 元工具只常驻这么长的摘要，能力和触发条件都得在里面。
# 每一句都实测过，尤其是名字歧义那一段：那是真实使用中最常撞的墙。
INSTRUCTIONS = (
    "Graphify answers relationship questions across a repository. Reach for it before you write "
    "down what a change affects, or that nothing reaches a place: reverse impact, dependency "
    "paths, module relationships, cross-service routes, IPC channels, event topics and "
    "cross-language data flow. Grep finds a line; it cannot show that a set of references is "
    "complete.\n\n"
    "If your host defers tool schemas, load this tool now, before exploring relationships by hand."
    "\n\n"
    "affected is the workhorse: name one thing and it lists everything that depends on it, one "
    "per line with the relation and file:line, following calls, imports, inheritance, references "
    "and nine more relation types. It runs one direction — what a change to that thing reaches. "
    "query takes a question in words and returns a neighbourhood in both directions. path shows "
    "how two named nodes connect. explain prints one node's identity, degree and every connection "
    "with direction arrows, and is the right first call when you are getting oriented.\n\n"
    "Names are matched across the whole repository, so a common one like `main` can match dozens "
    "of nodes. The answer tells you when that happened, in one of two shapes: it fails with the "
    "full candidate list and each node id, or it succeeds with a `[graphify] warning: source "
    "match was ambiguous` line appended. Both mean the same thing — retry with a repo-relative "
    "path or a node id from that list. A `no directed path` result carrying that warning is "
    "telling you the name did not resolve, not that the two are unconnected.\n\n"
    "Two kinds of relationship are invisible to a language server and belong here: handlers "
    "registered by a decorator, whose callers hold no static reference to them, and symbols "
    "destructured from a dynamic import. Serena returning nothing for those two is not evidence "
    "of absence; bring the question here. Serena stays primary for one symbol: its definition, "
    "direct references, implementations, and a file's top-level symbols.\n\n"
    "Each call first brings the graph in line with the current checkout, so the first call in a "
    "repository can take a while. When the graph is missing, cannot be built, or is being built "
    "by another process, say so and fall back to grep and read — a graph problem never blocks the "
    "task.\n\n"
    "Results are candidates, not conclusions: open the files it names before you state the "
    "relationship. An empty result never proves absence."
)

TOOL = {
    "name": "graphify",
    "description": (
        "Call this before you claim what a change reaches, what calls a handler, or that nothing "
        "references a place. It answers reverse impact, dependency paths, module relationships, "
        "cross-service routes, IPC channels, event topics, dynamic imports and cross-language data "
        "flow. Text search and a language server both miss decorator-registered handlers and "
        "dynamically imported symbols, so their silence is not absence. A common name can match "
        "many nodes; when the answer reports an ambiguous match, retry with a repo-relative path "
        "or one of the node ids it lists. Returns candidates, not conclusions: verify each one in "
        "current source. Serena remains primary for symbol definitions, direct references, "
        "implementations and file overviews."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["query", "affected", "path", "explain"],
                "description": "query=question, affected=reverse impact, path=connection, explain=node neighbors",
            },
            "query": {"type": "string", "description": "Question or starting node"},
            "to": {"type": "string", "description": "Destination node, required for path"},
            "depth": {
                "type": "integer",
                "minimum": 1,
                "maximum": 8,
                "description": f"Reverse-impact depth; default {DEFAULT_DEPTH}",
            },
            "budget": {
                "type": "integer",
                "minimum": 200,
                "maximum": 8000,
                "description": f"Query output token budget; default {DEFAULT_BUDGET}",
            },
            "cwd": {
                "type": "string",
                "description": "Directory inside the target repository; defaults to GRAPHIFY_PROJECT / workspace / process cwd",
            },
        },
        "required": ["action", "query"],
    },
}


class GraphifyError(RuntimeError):
    """图不可用或查询失败，向调用方如实报告。"""


def _run(args: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False
    )


def _resolve(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    fallback = Path.home() / ".local" / "bin" / name
    if fallback.exists():
        return str(fallback)
    raise GraphifyError(f"找不到命令 {name}；确认它在 PATH 或 ~/.local/bin 下")


def _resolve_ensure() -> str:
    """只用 MMW 自带的 ensure（或 GRAPHIFY_ENSURE_BIN），不依赖 PATH 别名。"""
    configured = (os.environ.get("GRAPHIFY_ENSURE_BIN") or "").strip()
    if configured:
        return configured
    sibling = Path(__file__).resolve().parent / "graphify_ensure.py"
    if sibling.is_file():
        return str(sibling)
    raise GraphifyError(
        "找不到 ensure：期望与 graphify_mcp.py 同目录的 graphify_ensure.py"
    )


def _default_start() -> Path:
    for key in ("GRAPHIFY_PROJECT", "SERENA_PROJECT"):
        value = (os.environ.get(key) or "").strip()
        if value:
            return Path(value).expanduser()
    folders = (os.environ.get("WORKSPACE_FOLDER_PATHS") or "").strip()
    if folders:
        return Path(folders.split(",", 1)[0]).expanduser()
    return Path(os.getcwd())


def _repo_root(start: Path) -> Path:
    proc = _run(["git", "rev-parse", "--show-toplevel"], start, 30)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise GraphifyError(
            f"Graphify 需要 Git 仓库：{proc.stderr.strip() or f'exit {proc.returncode}'}"
        )
    return Path(proc.stdout.strip())


def _ensure_graph(root: Path) -> None:
    ensure = _resolve_ensure()
    if ensure.endswith(".py"):
        cmd = [sys.executable, ensure, "--repo", str(root)]
    else:
        cmd = [ensure, "--repo", str(root)]
    proc = _run(cmd, root, ENSURE_TIMEOUT)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise GraphifyError(f"图谱准备失败：{detail}")


def _query_args(params: dict, graph_path: Path) -> list[str]:
    action = params["action"]
    query = params["query"]
    if action == "query":
        args = ["query", query, "--budget", str(params.get("budget") or DEFAULT_BUDGET)]
    elif action == "affected":
        args = ["affected", query, "--depth", str(params.get("depth") or DEFAULT_DEPTH)]
    elif action == "path":
        target = (params.get("to") or "").strip()
        if not target:
            raise GraphifyError("action=path 必须给 to")
        args = ["path", query, target]
    elif action == "explain":
        args = ["explain", query]
    else:
        raise GraphifyError(f"未知 action：{action}")
    return [*args, "--graph", str(graph_path)]


def _execute(params: dict) -> str:
    if not str(params.get("query") or "").strip():
        raise GraphifyError("query 不能为空")
    start = Path(params.get("cwd") or _default_start()).expanduser()
    if not start.is_dir():
        raise GraphifyError(f"目录不存在：{start}")
    root = _repo_root(start)
    _ensure_graph(root)
    graph_path = root / "graphify-out" / "graph.json"
    proc = _run([_resolve("graphify"), *_query_args(params, graph_path)], root, QUERY_TIMEOUT)
    return _relay(proc)


def _relay(proc: subprocess.CompletedProcess[str]) -> str:
    """把 graphify 说的话原样交给调用方，两条流都要。

    实测这个命令行把诊断分散在两条流上，而且哪条都可能是唯一有用的那条：

        名字有歧义         exit 1，候选清单连同各自的 node id 在 stdout，stderr 空
        名字有歧义但可跑    exit 0，结果在 stdout，`warning: source match was
                          ambiguous` 只在 stderr
        图文件不在          exit 1，原因在 stderr，stdout 空

    上一版失败时只读 stderr、成功时只读 stdout，于是第一种情况回一句「exit 1」、
    第二种情况回一句干净的「No directed path found」。后者最坏：调用方拿到的是
    带十足信心的假阴性——它会断定两者无关，而真相是名字没解析到想要的那个节点。

    正常查询的 stderr 是空的，所以附加的警告只会在真有话说时出现。
    """
    out, err = proc.stdout.rstrip(), proc.stderr.strip()
    if proc.returncode != 0:
        detail = "\n".join(part for part in (err, out.strip()) if part)
        raise GraphifyError(f"查询失败：{detail or f'exit {proc.returncode}'}")
    body = out or "(图中没有匹配结果；空结果不能证明关系不存在)"
    return f"{body}\n\n[graphify] {err}" if err else body


def _write(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle(request: dict) -> dict | None:
    method = request.get("method")
    req_id = request.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "graphify", "version": "1.1.0"},
                "instructions": INSTRUCTIONS,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [TOOL]}}
    if method == "tools/call":
        params = request.get("params") or {}
        if params.get("name") != TOOL["name"]:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"未知工具：{params.get('name')}"},
            }
        try:
            text = _execute(params.get("arguments") or {})
        except (GraphifyError, subprocess.TimeoutExpired, OSError) as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": text}]}}
    if req_id is None:
        return None
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"未实现：{method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = _handle(request)
        if response is not None:
            _write(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
