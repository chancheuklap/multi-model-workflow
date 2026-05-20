#!/usr/bin/env bash
# SubagentStop hook for pack-executor / complex-pack-executor.
# Reads Worker's durable return file → updates execution state → outputs NEXT directive.
# Missing return file → BLOCKED (exit 2).
set -euo pipefail

INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
if ! echo "$AGENT_TYPE" | grep -qE 'pack-executor|complex-pack-executor'; then
  exit 0
fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then
  echo "[multi-model-workflow] BLOCKED: Coding agent completed but no active-run-id found. Fix: verify .claude/multi-model-workflow/active-run-id exists." >&2
  exit 2
fi

RUN_ID=$(cat "$RUN_ID_FILE")
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then
  echo "[multi-model-workflow] BLOCKED: Coding agent completed but no execution-state file. Fix: run execution-preparation.md to create execution-state-${RUN_ID}.json." >&2
  exit 2
fi

AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // empty' 2>/dev/null)
CURRENT_PLAN=$(jq -r '.current_plan_id' "$STATE_FILE")

RETURN_DIR="${BUDGET_DIR}/pack-returns"
RETURN_FILE=""
PACK_ID=""
VERDICT=""

if [ -d "$RETURN_DIR" ]; then
  for f in "${RETURN_DIR}/"*.json; do
    [ -f "$f" ] || continue
    FILE_PACK_ID=$(jq -r '.pack_id // empty' "$f" 2>/dev/null)
    if [ -z "$FILE_PACK_ID" ]; then continue; fi
    F_PLAN_KEY=$(printf "%03d" "$(echo "$FILE_PACK_ID" | cut -d. -f1)")
    F_STATUS=$(jq -r --arg plan "$F_PLAN_KEY" --arg pack "$FILE_PACK_ID" '.plans[$plan].packs[$pack].status // ""' "$STATE_FILE")
    if [ "$F_STATUS" = "dispatched" ]; then
      RETURN_FILE="$f"
      PACK_ID="$FILE_PACK_ID"
      VERDICT=$(jq -r '.verdict // empty' "$f")
      break
    fi
  done
fi

if [ -z "$RETURN_FILE" ]; then
  echo "[multi-model-workflow] BLOCKED: Worker completed but no pack-returns file found for a dispatched pack. Fix: check that Worker wrote .claude/multi-model-workflow/pack-returns/<pack-id>.json per the Durable Return contract in Pack Brief." >&2
  exit 2
fi

# Update execution state
PLAN_KEY=$(printf "%03d" "$(echo "$PACK_ID" | cut -d. -f1)")
jq --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" --arg verdict "$VERDICT" --arg agent "$AGENT_ID" '
  .plans[$plan].packs[$pack].worker_verdict = $verdict |
  .plans[$plan].packs[$pack].agent_id = $agent |
  .plans[$plan].packs[$pack].status = "returned"
' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

# Calculate Plan completion (committed count, not returned — commit happens after Open Items)
COMMITTED=$(jq --arg plan "$CURRENT_PLAN" \
  '[.plans[$plan].packs | to_entries[] | select(.value.status == "committed")] | length' "$STATE_FILE")
EXPECTED=$(jq --arg plan "$CURRENT_PLAN" \
  '.plans[$plan].expected_pack_ids | length' "$STATE_FILE")

if [ "$COMMITTED" -eq "$EXPECTED" ] && [ "$EXPECTED" -gt 0 ]; then
  START_SHA=$(jq -r --arg p "$CURRENT_PLAN" '.plans[$p].start_commit' "$STATE_FILE")
  END_SHA=$(jq -r --arg p "$CURRENT_PLAN" '.plans[$p].end_commit' "$STATE_FILE")
  echo "[multi-model-workflow] NEXT: All ${EXPECTED} packs in Plan ${CURRENT_PLAN} committed. Dispatch Plan Implementation Review. Diff range: ${START_SHA}..${END_SHA}. Read execution-review-dispatch.md." >&2
else
  RETURNED=$(jq --arg plan "$CURRENT_PLAN" \
    '[.plans[$plan].packs | to_entries[] | select(.value.status == "returned" or .value.status == "committed")] | length' "$STATE_FILE")
  echo "[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). Progress: ${RETURNED}/${EXPECTED} returned, ${COMMITTED}/${EXPECTED} committed in Plan ${CURRENT_PLAN}. Process Open Items → scope drift check → Git Checkpoint → next pack." >&2
fi

exit 0
