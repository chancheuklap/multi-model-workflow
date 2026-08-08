#!/usr/bin/env python3
"""读取 Codex 角色结构，并从 MMW 默认配置解析模型。"""

from __future__ import annotations

import json
from pathlib import Path

CODEX_ROOT = Path(__file__).resolve().parent
MMW_ROOT = CODEX_ROOT.parent
PROFILES_PATH = CODEX_ROOT / "profiles.json"
MODELS_PATH = MMW_ROOT / "cli" / "mmw.default.json"
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
    profiles = read_json(PROFILES_PATH)
    models = read_json(MODELS_PATH).get("models") or {}

    for section in ("background_roles", "subagents"):
        roles = profiles.get(section) or {}
        if not isinstance(roles, dict):
            raise CodexConfigError(f"profiles.json {section} 必须是对象")
        for role, profile in roles.items():
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
