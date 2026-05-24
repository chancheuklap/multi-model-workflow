#!/usr/bin/env bash
set -euo pipefail

PAYLOAD="$(cat)"
export PAYLOAD

python3 - <<'PY'
from __future__ import annotations

import json
import os
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


payload = read_payload()
tool_name = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {})

file_path = tool_input.get("file_path", "")
if not file_path:
    sys.exit(0)

p = Path(file_path)
if not (p.name.startswith("budget-") and p.name.endswith(".json")):
    sys.exit(0)

# This is a budget file write/edit. Check if budget_total or pack_count is being changed.

if not p.exists():
    # File doesn't exist yet — creation is allowed (entry gate sets initial values).
    sys.exit(0)

try:
    current = json.loads(p.read_text(encoding="utf-8"))
except (json.JSONDecodeError, OSError):
    sys.exit(0)

phase = current.get("last_gate_phase", "")
plan_writing_phases = {
    "entry",
    "discovery-design-review-pass",
    "issue-split-done",
    "plan-entry-gate",
    "plan-writing",
    "plan-review",
    "plan-review-pass",
}

if phase in plan_writing_phases:
    # Plan-writing phase — budget_total/pack_count assignment is allowed.
    sys.exit(0)

# Past plan-writing. Block any attempt to change budget_total or pack_count.

if tool_name == "Write":
    content = tool_input.get("content", "")
    try:
        proposed = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    old_total = current.get("budget_total")
    new_total = proposed.get("budget_total")
    old_count = current.get("pack_count")
    new_count = proposed.get("pack_count")

    changed = []
    if new_total is not None and new_total != old_total:
        changed.append(f"budget_total: {old_total} → {new_total}")
    if new_count is not None and new_count != old_count:
        changed.append(f"pack_count: {old_count} → {new_count}")

    if changed:
        emit_block(
            f"Blocked budget file modification: {', '.join(changed)}. "
            f"budget_total and pack_count are immutable after plan-writing (current phase: {phase}). "
            f"If pack count genuinely changed, return NEEDS_PLAN_REVISION."
        )
        sys.exit(0)

elif tool_name == "Edit":
    old_string = tool_input.get("old_string", "")
    new_string = tool_input.get("new_string", "")

    for field in ("budget_total", "pack_count"):
        if field in old_string or field in new_string:
            # Check if the value is actually changing
            import re
            old_match = re.search(rf'"{field}"\s*:\s*(\d+)', old_string)
            new_match = re.search(rf'"{field}"\s*:\s*(\d+)', new_string)
            if old_match and new_match and old_match.group(1) != new_match.group(1):
                emit_block(
                    f"Blocked budget file edit: {field} change from {old_match.group(1)} to {new_match.group(1)}. "
                    f"budget_total and pack_count are immutable after plan-writing (current phase: {phase}). "
                    f"If pack count genuinely changed, return NEEDS_PLAN_REVISION."
                )
                sys.exit(0)

sys.exit(0)
PY
