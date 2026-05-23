#!/usr/bin/env bash
# PostToolUse hook for Agent tool.
# Reads Worker's return via DISPATCH_ENVELOPE → updates execution-state via state.sh → emits NEXT.
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

# Parse DISPATCH_ENVELOPE from the dispatch prompt
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
ENVELOPE=$(echo "$PROMPT" | bash "$SCRIPT_DIR/lib/parse-envelope.sh" 2>/dev/null) || {
  # Per Ruling 3: PostToolUse hook, agent already returned — skip is safe
  echo "[multi-model-workflow] WARN: agent return without DISPATCH_ENVELOPE, skipping state tracking" >&2
  exit 0
}

PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
if [ -z "$PACK_ID" ] || [ "$PACK_ID" = "null" ]; then exit 0; fi

PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)

# Read verdict from structured return file first, then tool_response
RETURN_DIR="${BUDGET_DIR}/pack-returns/${RUN_ID}"
RETURN_FILE="${RETURN_DIR}/${PACK_ID}.json"
VERDICT=""

if [ -f "$RETURN_FILE" ] && jq empty "$RETURN_FILE" 2>/dev/null; then
  VERDICT=$(jq -r '.verdict // empty' "$RETURN_FILE")
fi

if [ -z "$VERDICT" ]; then
  RESPONSE_TEXT=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null || true)
  if [ -n "$RESPONSE_TEXT" ]; then
    VERDICT_LINE=$(echo "$RESPONSE_TEXT" | grep -iE '^[#]*[[:space:]]*verdict' | head -1 || true)
    if [ -n "$VERDICT_LINE" ]; then
      VERDICT=$(echo "$VERDICT_LINE" | sed 's/.*[Vv]erdict[[:space:]]*:*[[:space:]]*//' | tr -d '[:space:]#' || true)
    fi
  fi
fi

if [ -z "$VERDICT" ] || ! echo "$VERDICT" | grep -qiE '^(pass|blocked|needs|unknown)'; then
  VERDICT="unknown"
fi

# Update execution-state (per Ruling 2: pack-level data in execution-state, not workflow-state)
ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ -f "$ESF" ]; then
  source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
  LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
  state_lock_acquire "$LOCK_DIR"
  jq --arg pack "$PACK_ID" --arg v "$VERDICT" --arg at "$AGENT_TYPE" '
    .plans |= with_entries(
      .value.packs |= with_entries(
        if .key == $pack then
          .value.status = "returned" | .value.worker_verdict = $v
        else . end
      )
    )
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
  state_lock_release "$LOCK_DIR"
fi

# Check remaining packs in this plan to differentiate NEXT message
REMAINING=999
CUR_PLAN=""
if [ -f "$ESF" ]; then
  CUR_PLAN=$(jq -r --arg pack "$PACK_ID" '[.plans | to_entries[] | select(.value.packs[$pack] != null) | .key] | first // empty' "$ESF")
  if [ -n "$CUR_PLAN" ]; then
    REMAINING=$(jq --arg pid "$CUR_PLAN" '[.plans[$pid].packs | to_entries[] | select(.value.status == "pending" or .value.status == "dispatched")] | length' "$ESF")
  fi
fi

if [ "$REMAINING" -eq 0 ]; then
  MSG="[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). All packs in Plan ${CUR_PLAN} have returned. Process Open Items → scope drift check → Git Checkpoint for each → then Step 8 (Plan Implementation Review). Do NOT dispatch review until all Git Checkpoints complete."
else
  MSG="[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). Process Open Items → scope drift check → Git Checkpoint. ${REMAINING} packs still pending/dispatched in Plan ${CUR_PLAN}."
fi

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
