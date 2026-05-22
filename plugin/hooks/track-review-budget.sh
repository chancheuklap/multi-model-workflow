#!/usr/bin/env bash
# PostToolUse hook for Bash tool.
# Detects codex-companion "result" commands → increments review budget in workflow-state.
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [ -z "$COMMAND" ]; then exit 0; fi

if ! echo "$COMMAND" | grep -qE '(codex-companion|CODEX_SCRIPT)'; then exit 0; fi
if ! echo "$COMMAND" | grep -qw 'result'; then exit 0; fi

EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

jq '.budget.review_used += 1' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

USED=$(jq -r '.budget.review_used' "$SF")
TOTAL=$(jq -r '.budget.review_total' "$SF")

if [ "$TOTAL" = "unlimited" ]; then
  MSG="Review budget: ${USED} dispatches used (unlimited)."
elif [ "$USED" -ge "$TOTAL" ] 2>/dev/null; then
  MSG="⚠ BUDGET EXHAUSTED: ${USED}/${TOTAL}. Stop dispatching reviews and report to user."
elif [ "$USED" -ge "$(( TOTAL * 80 / 100 ))" ] 2>/dev/null; then
  CURRENT_DC=$(jq -r '.pending_direction_check // "null"' "$SF")
  if [ "$CURRENT_DC" = "null" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    bash "$SCRIPT_DIR/../scripts/state.sh" direction-check trigger \
      --run-id "$RUN_ID" --type review --threshold-percent 80 2>/dev/null || true
  fi
  MSG="⚠ DIRECTION CHECK: Review budget at ${USED}/${TOTAL} (≥80%). Confirm with user."
else
  MSG="Review budget: ${USED}/${TOTAL} dispatches used."
fi

jq -n --arg msg "[multi-model-workflow] $MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
