#!/usr/bin/env bash
# PostToolUse hook for Bash tool.
# Detects codex-companion "result" commands → increments review budget in workflow-state.
#
# Dual-mode (P4 D3):
#   attendance_mode=attended: ≥80% → writes pending_direction_check (stops dispatch)
#   attendance_mode=afk:      ≥80% → soft signal only (no DC, continues); 100% → DC (escape hatch)
# effective_used = review_used - review_credit (credit归还合理回流额度)
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

USED=$(jq -r '.budget.review_used' "$SF")
TOTAL=$(jq -r '.budget.review_total' "$SF")
CREDIT=$(jq -r '.budget.review_credit // 0' "$SF")
EFFECTIVE=$(( USED - CREDIT ))

# Cap guard: refuse to count past effective exhaustion.
# Hook is observational — dispatch validation already enforces budget upstream.
if [ "$TOTAL" != "unlimited" ] && [ "$EFFECTIVE" -ge "$TOTAL" ] 2>/dev/null; then
  SKIPPED=true
else
  SKIPPED=false
  jq '.budget.review_used += 1' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"
  USED=$(jq -r '.budget.review_used' "$SF")
  EFFECTIVE=$(( USED - CREDIT ))
fi

ATTENDANCE=$(jq -r '.attendance_mode // "afk"' "$SF")

NEEDS_DC=false
DC_THRESHOLD=80
if [ "$TOTAL" = "unlimited" ]; then
  MSG="Review budget: ${USED} dispatches used (unlimited)."
elif [ "$SKIPPED" = "true" ]; then
  MSG="⚠ BUDGET EXHAUSTED: ${EFFECTIVE}/${TOTAL} (raw=${USED}, credit=${CREDIT}). Skipped counting an over-cap dispatch — stop dispatching reviews and report to user."
elif [ "$EFFECTIVE" -ge "$TOTAL" ] 2>/dev/null; then
  # 100%: both modes → escape hatch DC
  CURRENT_DC=$(jq -r '.pending_direction_check // "null"' "$SF")
  if [ "$CURRENT_DC" = "null" ]; then
    NEEDS_DC=true
    DC_THRESHOLD=100
  fi
  MSG="⚠ BUDGET EXHAUSTED: ${EFFECTIVE}/${TOTAL} (raw=${USED}, credit=${CREDIT}). Escape hatch: 报告用户，需显式 --allow-over-budget 或 stop。"
elif [ "$EFFECTIVE" -ge "$(( TOTAL * 80 / 100 ))" ] 2>/dev/null; then
  # 80-100%: mode-dependent
  if [ "$ATTENDANCE" = "attended" ]; then
    CURRENT_DC=$(jq -r '.pending_direction_check // "null"' "$SF")
    if [ "$CURRENT_DC" = "null" ]; then
      NEEDS_DC=true
      DC_THRESHOLD=80
    fi
    MSG="⚠ DIRECTION CHECK: Review budget at ${EFFECTIVE}/${TOTAL} (≥80%, attended). Confirm with user."
  else
    # AFK: soft signal only, no DC written
    MSG="⚠ Review budget ${EFFECTIVE}/${TOTAL} (≥80%)，AFK 继续中，到顶将停。"
  fi
else
  MSG="Review budget: ${EFFECTIVE}/${TOTAL} dispatches used (raw=${USED}, credit=${CREDIT})."
fi

# Release lock before calling state.sh (which acquires the same lock)
state_lock_release "$LOCK_DIR"
trap - EXIT

if [ "$NEEDS_DC" = "true" ]; then
  bash "$SCRIPT_DIR/../scripts/state.sh" direction-check trigger \
    --run-id "$RUN_ID" --type review --threshold-percent "$DC_THRESHOLD" 2>/dev/null || true
fi

jq -n --arg msg "[multi-model-workflow] $MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
