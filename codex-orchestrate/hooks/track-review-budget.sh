#!/usr/bin/env bash
# SubagentStart hook for codex_reviewer.
# Counts native reviewer dispatches against workflow-state review budget.
set -euo pipefail

INPUT=$(cat)

HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
if [[ "$HOOK_EVENT" != "SubagentStart" ]]; then exit 0; fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
if [[ "$AGENT_TYPE" != "codex_reviewer" ]]; then exit 0; fi

PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then exit 0; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"
ENVELOPE=$(echo "$PROMPT" | bash "$PARSE_ENVELOPE" 2>/dev/null) || exit 0
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then exit 0; fi

BUDGET_DIR=".codex/multi-model-workflow"
SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

jq '.budget.review_used += 1' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

USED=$(jq -r '.budget.review_used' "$SF")
TOTAL=$(jq -r '.budget.review_total' "$SF")

NEEDS_DC=false
if [ "$TOTAL" = "unlimited" ]; then
  MSG="Review budget: ${USED} dispatches used (unlimited)."
elif [ "$USED" -ge "$TOTAL" ] 2>/dev/null; then
  MSG="⚠ BUDGET EXHAUSTED: ${USED}/${TOTAL}. Stop dispatching reviews and report to user."
elif [ "$USED" -ge "$(( TOTAL * 80 / 100 ))" ] 2>/dev/null; then
  CURRENT_DC=$(jq -r '.pending_direction_check // "null"' "$SF")
  if [ "$CURRENT_DC" = "null" ]; then
    NEEDS_DC=true
  fi
  MSG="⚠ DIRECTION CHECK: Review budget at ${USED}/${TOTAL} (≥80%). Confirm with user."
else
  MSG="Review budget: ${USED}/${TOTAL} dispatches used."
fi

# Release lock before calling state.sh (which acquires the same lock)
state_lock_release "$LOCK_DIR"
trap - EXIT

if [ "$NEEDS_DC" = "true" ]; then
  bash "$SCRIPT_DIR/../scripts/state.sh" direction-check trigger \
    --run-id "$RUN_ID" --type review --threshold-percent 80 2>/dev/null || true
fi

jq -n --arg msg "[multi-model-workflow] $MSG" \
  '{hookSpecificOutput: {hookEventName: "SubagentStart", additionalContext: $msg}}'
exit 0
