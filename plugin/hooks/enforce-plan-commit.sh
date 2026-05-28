#!/usr/bin/env bash
# PreToolUse hook for Bash (if: "Bash(git commit *)").
# Validates Pack commit message format during Plan-level Worker autonomous execution
# (Plan 005 — renamed from enforce-pack-commit.sh).
#
# Worker still commits each Pack with "Pack N.M: <title> — <summary>" format;
# this hook enforces the format on every git commit. The "plan" in the hook name
# reflects the Plan-level dispatch boundary that owns the Pack lifecycle —
# format / cadence / count rules are checked here so that doc-patch + plan-return
# generation downstream can rely on N commits matching the N committed packs in
# the plan-return artifact.
#
# Behavior:
#   - Non-Pack-prefixed commits (Coordinator commits, merge commits, etc.) pass through.
#   - "Pack N.M: ..." messages MUST match `Pack <plan>.<pack>: <text>`.
#     Repair-mode messages MUST also satisfy `Pack N.M: <title> — repair: <summary>`
#     (the hook only checks the prefix; trailing "repair:" remains a doc convention).
#   - Without an active run / workflow-state, the hook exits 0 silently — same as
#     the legacy enforce-pack-commit.sh behavior.
set -euo pipefail

INPUT=$(cat)
BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
COMMIT_MSG=$(echo "$COMMAND" | sed -n 's/.*-m[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -z "$COMMIT_MSG" ]; then
  COMMIT_MSG=$(echo "$COMMAND" | sed -n "s/.*-m[[:space:]]*'\([^']*\)'.*/\1/p" | head -1)
fi

if [ -z "$COMMIT_MSG" ] || ! echo "$COMMIT_MSG" | grep -qiE '^Pack[[:space:]]'; then
  exit 0
fi

if ! echo "$COMMIT_MSG" | grep -qE '^Pack [0-9]+\.[0-9]+: .+'; then
  echo "[multi-model-workflow] BLOCKED: Pack commit message format invalid. Fix: use 'Pack N.M: <title> — <summary>' (or 'Pack N.M: <title> — repair: <summary>' for review-finding fixes)." >&2
  exit 2
fi

exit 0
