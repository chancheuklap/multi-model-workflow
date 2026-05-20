#!/usr/bin/env bash
# PostToolUse hook for Bash tool.
# Detects codex-companion.mjs "result" commands and auto-increments review budget.
# Outputs budget status via additionalContext so Coordinator sees running count.
# Must exit 0 — PostToolUse cannot block.

set -euo pipefail

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [ -z "$COMMAND" ]; then
  exit 0
fi

if ! echo "$COMMAND" | grep -qE '(codex-companion|CODEX_SCRIPT)'; then
  exit 0
fi
if ! echo "$COMMAND" | grep -qw 'result'; then
  exit 0
fi

EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then
  exit 0
fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"

if [ ! -f "$RUN_ID_FILE" ]; then
  exit 0
fi

RUN_ID=$(cat "$RUN_ID_FILE")
BUDGET_FILE="${BUDGET_DIR}/budget-${RUN_ID}.json"

if [ ! -f "$BUDGET_FILE" ]; then
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq --arg ts "$TIMESTAMP" '
  .budget_used += 1 |
  .dispatches += [{"timestamp": $ts}]
' "$BUDGET_FILE" > "${BUDGET_FILE}.tmp" && mv "${BUDGET_FILE}.tmp" "$BUDGET_FILE"

USED=$(jq -r '.budget_used' "$BUDGET_FILE")
TOTAL=$(jq -r '.budget_total' "$BUDGET_FILE")

if [ "$TOTAL" -eq 0 ] 2>/dev/null; then
  MSG="Review budget: ${USED} dispatches used (budget_total not yet assigned)"
elif [ "$USED" -ge "$TOTAL" ]; then
  MSG="⚠ BUDGET EXHAUSTED: ${USED}/${TOTAL} dispatches. Stop dispatching reviews and report to user."
elif [ "$USED" -ge "$(( TOTAL * 80 / 100 ))" ]; then
  MSG="⚠ DIRECTION CHECK: Review budget at ${USED}/${TOTAL} (≥80%). Confirm with user before spending more."
else
  MSG="Review budget: ${USED}/${TOTAL} dispatches used."
fi

# === Plan Implementation Review → update execution state ===
GATE=$(echo "$COMMAND" | sed -n 's/.*plan-impl-review-\([0-9][0-9]*\).*/\1/p' | head -1)
if [ -n "$GATE" ]; then
  STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
  PLAN_KEY=$(printf "%03d" "$GATE")
  if [ -f "$STATE_FILE" ]; then
    jq --arg plan "$PLAN_KEY" --arg gate "plan-impl-review-${GATE}" '
      .plans[$plan].review_gate = $gate
    ' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  fi
fi

jq -n --arg msg "[multi-model-workflow] $MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'

exit 0
