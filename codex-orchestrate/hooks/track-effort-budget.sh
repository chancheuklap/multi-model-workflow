#!/usr/bin/env bash
# SubagentStart hook helper.
# Tracks effort budget (weighted agent dispatch count) in workflow-state.
# Triggers Direction Check at 80% threshold.
set -euo pipefail

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.agent_type // .tool_input.subagent_type // empty' 2>/dev/null)
if [[ -z "$AGENT_TYPE" ]]; then exit 0; fi
AGENT_TYPE="${AGENT_TYPE//-/_}"

BUDGET_DIR=".codex/multi-model-workflow"
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

# Agent-role weighted effort
case "$AGENT_TYPE" in
  pack_executor|complex_pack_executor) EFFORT_INCREMENT=1 ;;
  code_explorer|complex_code_explorer) EFFORT_INCREMENT=1 ;;
  root_cause_analyst)                  EFFORT_INCREMENT=2 ;;
  *)                                   exit 0 ;;
esac

jq --argjson inc "$EFFORT_INCREMENT" '.budget.effort_used += $inc' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

EFFORT_USED=$(jq -r '.budget.effort_used' "$SF")
THRESHOLD=$(( EFFORT_TOTAL * 80 / 100 ))

if [[ "$EFFORT_USED" -ge "$EFFORT_TOTAL" ]]; then
  MSG="EFFORT BUDGET EXHAUSTED: ${EFFORT_USED}/${EFFORT_TOTAL}. Stop and report."
elif [[ "$EFFORT_USED" -ge "$THRESHOLD" ]]; then
  DC=$(jq -r '.pending_direction_check // null' "$SF")
  if [[ "$DC" == "null" ]]; then
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg ts "$NOW" \
      '.pending_direction_check = {"triggered_at": $ts, "threshold_type": "effort", "threshold_percent": 80, "ack_status": "pending"} | .budget.direction_check_count += 1' \
      "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"
    MSG="DIRECTION CHECK: Effort budget at ${EFFORT_USED}/${EFFORT_TOTAL} (>=80%). Confirm with user."
  else
    MSG="Effort budget: ${EFFORT_USED}/${EFFORT_TOTAL}."
  fi
else
  exit 0
fi

jq -n --arg msg "[codex-orchestrate] $MSG" \
  '{hookSpecificOutput: {hookEventName: "SubagentStart", additionalContext: $msg}}'
exit 0
