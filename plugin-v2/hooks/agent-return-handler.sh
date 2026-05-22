#!/usr/bin/env bash
# PostToolUse hook for Agent tool.
# Reads Worker's return → updates workflow-state via state.sh → emits NEXT.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../scripts/state.sh"

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
if [ "$TOOL_NAME" != "Agent" ]; then exit 0; fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty' 2>/dev/null)
case "$AGENT_TYPE" in
  pack-executor|complex-pack-executor) ;;
  *) exit 0 ;;
esac

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
PACK_ID=$(echo "$PROMPT" | sed -n 's/.*Pack:*[[:space:]]*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)

RETURN_DIR="${BUDGET_DIR}/pack-returns/${RUN_ID}"
RETURN_FILE="${RETURN_DIR}/${PACK_ID}.json"
VERDICT=""

if [ -f "$RETURN_FILE" ] && jq empty "$RETURN_FILE" 2>/dev/null; then
  VERDICT=$(jq -r '.verdict // empty' "$RETURN_FILE")
fi

if [ -z "$VERDICT" ]; then
  RESPONSE_TEXT=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null || true)
  VERDICT_LINE=$(echo "$RESPONSE_TEXT" | grep -iE '[#]*[[:space:]]*verdict' | head -1 || true)
  VERDICT_INLINE=$(echo "$VERDICT_LINE" | sed 's/.*[Vv]erdict[[:space:]]*:*[[:space:]]*//' | tr -d '[:space:]#' || true)
  if [ -n "$VERDICT_INLINE" ] && echo "$VERDICT_INLINE" | grep -qiE '^(pass|blocked|needs)'; then
    VERDICT="$VERDICT_INLINE"
  else
    VERDICT=$(echo "$RESPONSE_TEXT" | grep -iA1 '[#]*[[:space:]]*verdict' | tail -1 | tr -d '[:space:]' || true)
  fi
fi
if [ -z "$VERDICT" ] || ! echo "$VERDICT" | grep -qiE '^(pass|blocked|needs|unknown)'; then
  VERDICT="unknown"
fi

export STATE_BASE="$BUDGET_DIR"
bash "$STATE_SH" update --run-id "$RUN_ID" \
  --field ".plans[$((PLAN_ID - 1))].packs |= (if . == null then [] else . end | . + [{\"pack_id\":\"$PACK_ID\",\"status\":\"returned\",\"worker_verdict\":\"$VERDICT\",\"agent_type\":\"$AGENT_TYPE\"}])" \
  --value 'null' 2>/dev/null || {
  jq --arg pack "$PACK_ID" --arg v "$VERDICT" \
    '.plans[0].packs[$pack] = {"status":"returned","worker_verdict":$v}' \
    "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"
}

MSG="[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). Process Open Items → scope drift check → Git Checkpoint → next pack."
jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
