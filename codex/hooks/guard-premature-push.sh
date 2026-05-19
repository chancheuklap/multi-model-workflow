#!/usr/bin/env bash
set -euo pipefail

PAYLOAD="$(cat)"
export PAYLOAD

python3 - <<'PY'
from __future__ import annotations

import json
import os
import re
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


def active_plan_candidates(cwd: Path) -> list[Path]:
    plan_dirs = [
        cwd / "docs" / "orchestrate" / "plans",
        cwd / "docs" / "plans",
        cwd / ".codex" / "multi-model-workflow",
    ]
    plans: list[Path] = []
    for plan_dir in plan_dirs:
        if plan_dir.exists():
            plans.extend(plan_dir.glob("*.md"))
    return sorted(plans, key=lambda p: p.stat().st_mtime, reverse=True)


def has_unchecked_tasks(plan: Path) -> bool:
    text = plan.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r"^\s*-\s+\[\s\]\s+", text, re.MULTILINE))


payload = read_payload()
command = str(payload.get("tool_input", {}).get("command", ""))
cwd = Path(str(payload.get("cwd") or os.getcwd())).resolve()

if re.search(r"(^|&&|\|\||;)\s*git\s+merge\b[^\n]*\s--squash(\s|$)", command):
    emit_block("Blocked squash merge. multi-model-workflow keeps merge history with git merge --no-ff.")
    raise SystemExit(0)

if re.search(r"(^|&&|\|\||;)\s*git\s+rebase(\s|$)", command):
    emit_block("Blocked git rebase. multi-model-workflow preserves branch history and uses non-rebase merges.")
    raise SystemExit(0)

is_publish = any(
    re.search(pattern, command)
    for pattern in [
        r"(^|&&|\|\||;)\s*git\s+push(\s|$)",
        r"(^|&&|\|\||;)\s*gh\s+pr\s+create(\s|$)",
    ]
)
if not is_publish:
    raise SystemExit(0)

for active in active_plan_candidates(cwd):
    if has_unchecked_tasks(active):
        emit_block(f"Blocked publish command because active plan still has unchecked tasks: {active}")
        raise SystemExit(0)

raise SystemExit(0)
PY
