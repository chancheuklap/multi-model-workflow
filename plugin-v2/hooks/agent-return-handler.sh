#!/usr/bin/env bash
# PostToolUse hook for Agent tool.
# Fires when pack-executor / complex-pack-executor returns to Coordinator.
# Reads Worker's durable return file → updates execution state → emits NEXT via additionalContext.
# Non-execution routes (no execution-state file) silently pass through.
set -euo pipefail

INPUT=$(cat)

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
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi

# Validate state file is parseable JSON
if ! jq empty "$STATE_FILE" 2>/dev/null; then
  jq -n --arg msg "[multi-model-workflow] STATE: execution-state JSON is corrupted. Fix: inspect and repair .claude/multi-model-workflow/execution-state-${RUN_ID}.json manually." \
    '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
  exit 0
fi

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
PACK_ID=$(echo "$PROMPT" | sed -n 's/.*Pack:*[[:space:]]*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)
PLAN_KEY=$(printf "%03d" "$PLAN_ID")
CURRENT_PLAN=$(jq -r '.current_plan_id' "$STATE_FILE")

# Read durable return file (absolute path, written by Worker)
RETURN_DIR="${BUDGET_DIR}/pack-returns/${RUN_ID}"
RETURN_FILE="${RETURN_DIR}/${PACK_ID}.json"
VERDICT=""
CHANGED_FILES=""

if [ -f "$RETURN_FILE" ] && jq empty "$RETURN_FILE" 2>/dev/null; then
  VERDICT=$(jq -r '.verdict // empty' "$RETURN_FILE")
  CHANGED_FILES=$(jq -r '.changed_files // [] | join(", ")' "$RETURN_FILE")
fi

# Fallback: parse verdict from tool_response if no durable return file
if [ -z "$VERDICT" ]; then
  RESPONSE_TEXT=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null || true)
  # Handle both "Verdict: pass" (same line) and "### Verdict\npass" (next line)
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

# Update execution state: pack → returned
jq --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" --arg verdict "$VERDICT" --arg agent "$AGENT_TYPE" '
  .plans[$plan].packs[$pack].worker_verdict = $verdict |
  .plans[$plan].packs[$pack].agent_type = $agent |
  .plans[$plan].packs[$pack].status = "returned"
' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

# Report progress
RETURNED=$(jq --arg plan "$CURRENT_PLAN" \
  '[.plans[$plan].packs | to_entries[] | select(.value.status == "returned" or .value.status == "committed")] | length' "$STATE_FILE")
EXPECTED=$(jq --arg plan "$CURRENT_PLAN" \
  '.plans[$plan].expected_pack_ids | length' "$STATE_FILE")
COMMITTED=$(jq --arg plan "$CURRENT_PLAN" \
  '[.plans[$plan].packs | to_entries[] | select(.value.status == "committed")] | length' "$STATE_FILE")

MSG="[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). Progress: ${RETURNED}/${EXPECTED} returned, ${COMMITTED}/${EXPECTED} committed in Plan ${CURRENT_PLAN}. Process Open Items → scope drift check → Git Checkpoint → next pack."

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
