#!/usr/bin/env bash
# PostToolUse hook for Agent tool.
# Tracks effort budget (weighted agent dispatch count) in workflow-state.
# Triggers Direction Check at 80% threshold.
#
# Plan 005 Decision 5: Plan-level worker dispatch weight = actual Pack count
# (read from plan-return.json per_pack with status="committed"); fallback to 1
# when envelope lacks plan_id or plan-return.json unavailable. need-fresh-worker
# resume (envelope has resume_from_pack_id) → +0.5.
set -euo pipefail

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty' 2>/dev/null)
if [[ -z "$AGENT_TYPE" ]]; then exit 0; fi

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

# --- Plan 005 Decision 5: agent-role weighted effort, fractional supported ---
EFFORT_INCREMENT="0"

case "$AGENT_TYPE" in
  pack-executor|complex-pack-executor)
    PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
    ENVELOPE=""
    if [[ -n "$PROMPT" ]]; then
      ENVELOPE=$(echo "$PROMPT" | bash "$SCRIPT_DIR/lib/parse-envelope.sh" 2>/dev/null || true)
    fi

    PLAN_ID=""
    RESUME_FROM=""
    if [[ -n "$ENVELOPE" ]]; then
      PLAN_ID=$(echo "$ENVELOPE" | jq -r '.plan_id // empty' 2>/dev/null || true)
      RESUME_FROM=$(echo "$ENVELOPE" | jq -r '.resume_from_pack_id // empty' 2>/dev/null || true)
    fi

    if [[ -n "$PLAN_ID" && "$PLAN_ID" != "null" ]]; then
      # Plan-level dispatch — weight = committed pack count from plan-return.json
      PR_FILE="${BUDGET_DIR}/plan-returns/${RUN_ID}/${PLAN_ID}/plan-return.json"
      if [[ -f "$PR_FILE" ]] && jq empty "$PR_FILE" 2>/dev/null; then
        PACK_COUNT=$(jq '[.per_pack | to_entries[] | select(.value.status == "committed")] | length' "$PR_FILE")
        EFFORT_INCREMENT="$PACK_COUNT"
      else
        # plan-return.json not yet written — fall back to 1
        EFFORT_INCREMENT="1"
      fi

      # need-fresh-worker continuation: +0.5 on top
      if [[ -n "$RESUME_FROM" && "$RESUME_FROM" != "null" ]]; then
        EFFORT_INCREMENT=$(jq -n --argjson b "$EFFORT_INCREMENT" '$b + 0.5')
      fi
    else
      # Legacy envelope (no plan_id) — fall back to fixed 1
      EFFORT_INCREMENT="1"
    fi
    ;;
  code-explorer|complex-code-explorer) EFFORT_INCREMENT="1" ;;
  root-cause-analyst)                  EFFORT_INCREMENT="2" ;;
  *)                                   exit 0 ;;
esac

# Numeric add (handles int + float)
jq --argjson inc "$EFFORT_INCREMENT" '.budget.effort_used = ((.budget.effort_used // 0) + $inc)' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

EFFORT_USED=$(jq -r '.budget.effort_used' "$SF")
EXHAUSTED=$(jq -n --argjson u "$EFFORT_USED" --argjson t "$EFFORT_TOTAL" '$u >= $t')
AT_THRESHOLD=$(jq -n --argjson u "$EFFORT_USED" --argjson t "$EFFORT_TOTAL" '$u >= ($t * 0.8)')

if [[ "$EXHAUSTED" == "true" ]]; then
  MSG="⚠ EFFORT BUDGET EXHAUSTED: ${EFFORT_USED}/${EFFORT_TOTAL}. Stop and report."
elif [[ "$AT_THRESHOLD" == "true" ]]; then
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
