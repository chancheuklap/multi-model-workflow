#!/usr/bin/env python3
"""按当前宿主打印一条派发动作。

技能正文只写 `mmw launch <角色> --scope <范围>`，不写任何宿主名。宿主差异全部收在
`cli/host-actions.json` 这张表里，运行期查，不在物化时把五份不同的正文烧进技能产物。

加一个宿主 = 表里加一个 key。技能源和这个脚本都不用动。
"""

from __future__ import annotations

# codex/config.py 靠运行期 sys.path 找到，静态分析看不见这一跳。
# ruff: noqa: I001
import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CODEX_ROOT = PLUGIN_ROOT / "codex"
sys.path.insert(0, str(CODEX_ROOT))
from config import CodexConfigError, load_profiles as load_codex_profiles  # type: ignore[import-not-found]

TABLE_PATH = PLUGIN_ROOT / "cli" / "host-actions.json"
ROLES_PATH = PLUGIN_ROOT / "agent-src" / "roles.json"
SCOPES = ("worktree", "current", "none")


def die(message: str, code: int = 1) -> NoReturn:
    print(f"mmw launch: {message}", file=sys.stderr)
    raise SystemExit(code)


def load_table() -> dict:
    if not TABLE_PATH.is_file():
        die(f"找不到宿主动作表 {TABLE_PATH}")
    try:
        return json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"宿主动作表不是合法 JSON：{exc}")


def load_role_agents() -> dict[str, str]:
    data = json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    roles = data.get("roles") or {}
    agents: dict[str, str] = {}
    for role, metadata in roles.items():
        agent = (metadata or {}).get("agent")
        if not agent:
            die(f"roles.json 角色 {role} 缺 agent")
        agents[str(role)] = str(agent)
    return agents


def codex_values(table_key: str, role: str, scope: str, profiles: dict) -> dict[str, str]:
    """Codex 的两处动作要从 profiles.json 取值，做不成纯查表。"""
    del table_key
    if scope == "worktree":
        profile = (profiles.get("background_roles") or {}).get(role)
        if not profile:
            die(f"Codex 没有后台 worktree profile：{role}")
        method = profile.get("method_skill")
        return {
            "model": str(profile["model"]),
            "thinking": str(profile["thinking"]),
            "method_clause": (
                f", and reads `${method}` in full before starting work" if method else ""
            ),
        }
    profile = (profiles.get("subagents") or {}).get(role)
    if not profile:
        die(f"Codex 没有原生 subagent profile：{role}")
    return {"subagent_name": str(profile["name"])}


def fill(template: str, values: dict[str, str]) -> str:
    text = template
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


def launch_action(
    table: dict, host: str, role: str, scope: str, agents: dict[str, str], profiles: dict
) -> str:
    by_host = (table.get("launch") or {}).get(host)
    if not by_host:
        die(f"宿主动作表没有 launch.{host}；加宿主时给它补一条")
    template = by_host.get(scope)
    if not template:
        die(f"宿主动作表没有 launch.{host}.{scope}")
    if role not in agents:
        die(f"角色不在 roles.json：{role}")
    values = {"agent": agents[role], "role": role}
    if host == "codex":
        values.update(codex_values("launch", role, scope, profiles))
    return fill(template, values)


def resume_action(
    table: dict, host: str, role: str, scope: str, agents: dict[str, str]
) -> str:
    if role not in agents:
        die(f"角色不在 roles.json：{role}")
    material = str(table["resume_material"])
    template = ((table.get("resume") or {}).get(host) or {}).get(scope)
    # 表里没有这个组合就是「这个宿主这条路没有续跑通道」。退路显式写明重派要带什么，
    # 不静默降级成一次全新派发——那会让调用方以为上下文还在。
    if not template:
        template = str(table["resume_fallback"])
    return fill(template, {"role": role, "resume_material": material})


def reviewers_action(
    table: dict, host: str, agents: dict[str, str], profiles: dict
) -> str:
    block = table.get("reviewers") or {}
    if host == "codex":
        profile = (profiles.get("subagents") or {}).get("reviewer-gpt")
        if not profile:
            die("Codex 缺 reviewer-gpt subagent profile")
        return fill(str(block["codex"]), {"reviewer_name": str(profile["name"])})
    for role in ("reviewer-gpt", "reviewer-claude"):
        if role not in agents:
            die(f"启动组角色不在 roles.json：{role}")
    return fill(
        str(block["_default"]),
        {
            "gpt_launch": launch_action(
                table, host, "reviewer-gpt", "none", agents, profiles
            ),
            "claude_launch": launch_action(
                table, host, "reviewer-claude", "none", agents, profiles
            ),
        },
    )


def render(action: str, host: str, role: str, scope: str, *, bare: bool) -> str:
    table = load_table()
    agents = load_role_agents()
    try:
        profiles = load_codex_profiles()
    except CodexConfigError as exc:
        # Codex 配置坏了不该拖垮别的宿主：只有 codex 真要用它时才报错。
        if host == "codex":
            die(str(exc))
        profiles = {}

    if action == "launch":
        body = launch_action(table, host, role, scope, agents, profiles)
    elif action == "launch-group":
        if role != "reviewers":
            die(f"不认识的启动组：{role}")
        body = reviewers_action(table, host, agents, profiles)
    elif action == "resume":
        body = resume_action(table, host, role, scope, agents)
    else:
        die(f"不认识的动作：{action}")

    if action in ("launch", "launch-group"):
        rule = (table.get("post_launch_rule") or {}).get(host)
        if rule:
            body = f"{body}\n\n{rule}"
    # 派发出问题时，光看技能正文已经看不出当时该干什么了。宿主名跟着输出走，
    # 让「它以为自己在哪个宿主」当场可见。
    return body if bare else f"Host: {host}\n\n{body}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="打印当前宿主的派发动作")
    parser.add_argument("action", choices=("launch", "launch-group", "resume"))
    parser.add_argument("role")
    parser.add_argument("--host", required=True)
    parser.add_argument("--scope", default="none", choices=SCOPES)
    parser.add_argument("--bare", action="store_true", help="只打动作正文，不打 Host 行")
    args = parser.parse_args(argv)
    print(render(args.action, args.host, args.role, args.scope, bare=args.bare))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
