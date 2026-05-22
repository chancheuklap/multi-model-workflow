#!/usr/bin/env bash
# PostToolUse hook for Bash tool.
# Tracks effort budget (Sonnet/Opus tool calls) in workflow-state.
# Triggers Direction Check at 80% threshold.
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [[ -z "$COMMAND" ]]; then exit 0; fi

EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [[ "$EXIT_CODE" != "0" ]]; then exit 0; fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [[ ! -f "$RUN_ID_FILE" ]]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [[ ! -f "$SF" ]]; then exit 0; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

EFFORT_TOTAL=$(jq -r '.budget.effort_total // 0' "$SF")
if [[ "$EFFORT_TOTAL" == "0" || "$EFFORT_TOTAL" == "unlimited" ]]; then exit 0; fi

# Agent-role weighted effort: detect agent dispatch from command content
# worker (pack-executor/complex-pack-executor) = 1
# explorer (code-explorer/complex-code-explorer) = 1 (design says 0.5 rounded up)
# RCA (root-cause-analyst) = 2
# Other Bash calls = 0 (not effort-bearing)
# NOTE: Follow-up Task needed to move trigger to PostToolUse Agent for cleaner dispatch detection
EFFORT_INCREMENT=0
if echo "$COMMAND" | grep -qE 'pack-executor|complex-pack-executor'; then
  EFFORT_INCREMENT=1
elif echo "$COMMAND" | grep -qE 'code-explorer|complex-code-explorer'; then
  EFFORT_INCREMENT=1
elif echo "$COMMAND" | grep -qE 'root-cause-analyst'; then
  EFFORT_INCREMENT=2
fi

if [[ "$EFFORT_INCREMENT" -eq 0 ]]; then exit 0; fi

jq --argjson inc "$EFFORT_INCREMENT" '.budget.effort_used += $inc' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

EFFORT_USED=$(jq -r '.budget.effort_used' "$SF")
THRESHOLD=$(( EFFORT_TOTAL * 80 / 100 ))

if [[ "$EFFORT_USED" -ge "$EFFORT_TOTAL" ]]; then
  MSG="⚠ EFFORT BUDGET EXHAUSTED: ${EFFORT_USED}/${EFFORT_TOTAL}. Stop and report."
elif [[ "$EFFORT_USED" -ge "$THRESHOLD" ]]; then
  DC=$(jq -r '.pending_direction_check // null' "$SF")
  if [[ "$DC" == "null" ]]; then
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg ts "$NOW" \
      '.pending_direction_check = {"triggered_at": $ts, "threshold_type": "effort", "threshold_percent": 80, "ack_status": "pending"} | .budget.direction_check_count += 1' \
      "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"
    MSG="⚠ DIRECTION CHECK: Effort budget at ${EFFORT_USED}/${EFFORT_TOTAL} (≥80%). Confirm with user."
  else
    MSG="Effort budget: ${EFFORT_USED}/${EFFORT_TOTAL}."
  fi
else
  exit 0
fi

jq -n --arg msg "[multi-model-workflow] $MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
