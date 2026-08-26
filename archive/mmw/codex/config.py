#!/usr/bin/env python3
"""读取 Codex 角色结构，并从 MMW 默认配置解析模型。"""

from __future__ import annotations

import json
from pathlib import Path

CODEX_ROOT = Path(__file__).resolve().parent
MMW_ROOT = CODEX_ROOT.parent
PROFILES_PATH = CODEX_ROOT / "profiles.json"
MODELS_PATH = MMW_ROOT / "cli" / "mmw.default.json"
ROLES_PATH = MMW_ROOT / "agent-src" / "roles.json"
THINKING_LEVELS = {"low", "medium", "high", "xhigh", "max", "ultra"}


class CodexConfigError(ValueError):
    pass


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CodexConfigError(f"读不到 {path}: {exc}") from exc
    if data.get("version") != 1:
        raise CodexConfigError(f"{path} version 必须是 1")
    return data


def load_profiles() -> dict:
    """把三份来源合成 Codex 要的角色结构。

    `profiles.json` 只说 Codex 自己的事：哪些角色走后台 worktree、哪些走原生
    subagent、各自的 sandbox_mode。角色叫什么、描述、正文和方法论技能都从
    `agent-src/roles.json` 取——那是五个宿主共用的角色真源，Codex 再存一份
    只会漂：取消打包前，同一个 reviewer-gpt 在 roles.json 里是「Isolated
    in-session reviewer (GPT side)...」，在这里却是另一句话。模型从
    `cli/mmw.default.json` 取，`hosts.codex` 覆盖按字段生效。
    """
    profiles = read_json(PROFILES_PATH)
    models = read_json(MODELS_PATH).get("models") or {}
    role_source = read_roles()

    for section in ("background_roles", "subagents"):
        roles = profiles.get(section) or {}
        if not isinstance(roles, dict):
            raise CodexConfigError(f"profiles.json {section} 必须是对象")
        for role, profile in roles.items():
            source = role_source.get(role)
            if not source:
                raise CodexConfigError(
                    f"Codex 角色 {role} 在 {ROLES_PATH.name} 里不存在；"
                    "角色真源在那一份，profiles.json 只补 Codex 自己的字段"
                )
            for target, key in (
                ("name", "agent"),
                ("description", "description"),
                ("body", "body"),
            ):
                value = source.get(key)
                if not value:
                    raise CodexConfigError(f"角色 {role} 在角色真源里缺 {key}")
                profile[target] = value
            skill = str(source.get("skill") or "").strip()
            if skill:
                profile["method_skill"] = skill
            else:
                profile.pop("method_skill", None)

            model = models.get(role) or {}
            override = (model.get("hosts") or {}).get("codex") or {}
            family = override.get("family", model.get("family"))
            model_id = override.get("id", model.get("id"))
            thinking = override.get("effort", model.get("effort"))
            if family != "gpt" or not str(model_id or "").startswith("gpt-"):
                raise CodexConfigError(f"Codex 角色 {role} 必须使用内置 GPT 模型")
            if thinking not in THINKING_LEVELS:
                raise CodexConfigError(f"Codex 角色 {role} 的思考档无效: {thinking}")
            profile["model"] = model_id
            profile["thinking"] = thinking
    return profiles


def read_roles() -> dict:
    """角色真源。它没有 version 字段，所以不走 read_json。"""
    try:
        data = json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CodexConfigError(f"读不到 {ROLES_PATH}: {exc}") from exc
    roles = data.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise CodexConfigError(f"{ROLES_PATH} 的 roles 必须是非空对象")
    return roles
