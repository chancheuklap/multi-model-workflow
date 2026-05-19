#!/usr/bin/env bash
set -euo pipefail

PAYLOAD="$(cat)"
export PAYLOAD

python3 - <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def emit_block(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )


def read_payload() -> dict:
    raw = os.environ.get("PAYLOAD", "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def is_publish_command(command: str) -> bool:
    patterns = [
        r"(^|&&|\|\||;)\s*git\s+push(\s|$)",
        r"(^|&&|\|\||;)\s*git\s+merge(\s|$)",
        r"(^|&&|\|\||;)\s*gh\s+pr\s+create(\s|$)",
    ]
    return any(re.search(pattern, command) for pattern in patterns)


def active_plan_candidates(cwd: Path) -> list[Path]:
    plan_dir = cwd / "docs" / "orchestrate" / "plans"
    if not plan_dir.exists():
        return []
    plans = list(plan_dir.glob("*.md"))
    return sorted(plans, key=lambda p: p.stat().st_mtime, reverse=True)


def has_unchecked_tasks(plan: Path) -> bool:
    text = plan.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r"^\s*-\s+\[\s\]\s+", text, re.MULTILINE))


payload = read_payload()
command = str(payload.get("tool_input", {}).get("command", ""))
cwd = Path(str(payload.get("cwd") or os.getcwd())).resolve()

if not is_publish_command(command):
    raise SystemExit(0)

plans = active_plan_candidates(cwd)
if not plans:
    raise SystemExit(0)

active = plans[0]
if has_unchecked_tasks(active):
    emit_block(
        f"Blocked publish command because active plan still has unchecked tasks: {active}"
    )
    raise SystemExit(0)

raise SystemExit(0)
PY
