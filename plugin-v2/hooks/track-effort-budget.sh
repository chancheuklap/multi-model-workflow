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

EFFORT_TOTAL=$(jq -r '.budget.effort_total // 0' "$SF")
if [[ "$EFFORT_TOTAL" == "0" || "$EFFORT_TOTAL" == "unlimited" ]]; then exit 0; fi

jq '.budget.effort_used += 1' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

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
