#!/usr/bin/env bash
# SubagentStop hook for Codex workers.
# Reads the durable worker return file → updates execution-state → emits NEXT.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
if [ "$HOOK_EVENT" != "SubagentStop" ]; then exit 0; fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
case "$AGENT_TYPE" in
  pack_executor|complex_pack_executor) ;;
  *) exit 0 ;;
esac

BUDGET_DIR=".codex/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$ESF" ]; then exit 0; fi

# Codex SubagentStop does not carry the original prompt. The execution state is
# the authority because orchestrate execution dispatches one worker pack at a time.
PACK_ID=$(jq -r '
  [.plans | to_entries[] | .value.packs // {} | to_entries[] |
   select(.value.status == "dispatched") | .key] | first // empty
' "$ESF" 2>/dev/null)
if [ -z "$PACK_ID" ] || [ "$PACK_ID" = "null" ]; then exit 0; fi

# Read verdict from structured return file first, then tool_response
RETURN_DIR="${BUDGET_DIR}/pack-returns/${RUN_ID}"
RETURN_FILE="${RETURN_DIR}/${PACK_ID}.json"
VERDICT=""

if [ -f "$RETURN_FILE" ] && jq empty "$RETURN_FILE" 2>/dev/null; then
  VERDICT=$(jq -r '.verdict // empty' "$RETURN_FILE")
fi

if [ -z "$VERDICT" ] || ! echo "$VERDICT" | grep -qiE '^(pass|blocked|needs|unknown)'; then
  echo "[multi-model-workflow] BLOCKED: worker durable return missing or invalid for Pack ${PACK_ID}: ${RETURN_FILE}" >&2
  exit 2
fi

# Update execution-state (per Ruling 2: pack-level data in execution-state, not workflow-state)
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
  '{hookSpecificOutput: {hookEventName: "SubagentStop", additionalContext: $msg}}'
exit 0
