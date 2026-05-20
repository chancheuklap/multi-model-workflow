#!/usr/bin/env bash
# PreToolUse hook for Agent tool (pack-executor / complex-pack-executor).
# Blocks dispatch when upstream dependencies are missing.
# Repair re-dispatches pass through via [repair-round-N] marker in prompt.
set -euo pipefail

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)

# Extract Pack ID from dispatch prompt
PACK_ID=$(echo "$PROMPT" | sed -n 's/.*Pack:*[[:space:]]*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)
PLAN_KEY=$(printf "%03d" "$PLAN_ID")

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi

RUN_ID=$(cat "$RUN_ID_FILE")
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi

if ! jq empty "$STATE_FILE" 2>/dev/null; then
  echo "[multi-model-workflow] BLOCKED: execution-state JSON is corrupted. Fix: inspect and repair .claude/multi-model-workflow/execution-state-${RUN_ID}.json manually." >&2
  exit 2
fi

# Repair re-dispatch → pass through
if echo "$PROMPT" | grep -qE '\[repair-round-[0-9]+\]'; then
  exit 0
fi

# Check 1: start_commit must be recorded
START=$(jq -r --arg plan "$PLAN_KEY" '.plans[$plan].start_commit // "null"' "$STATE_FILE")
if [ "$START" = "null" ]; then
  echo "[multi-model-workflow] BLOCKED: Plan ${PLAN_KEY} has no start_commit. Fix: run 'git rev-parse HEAD' and write result to execution-state plans[${PLAN_KEY}].start_commit before dispatching." >&2
  exit 2
fi

# Check 2: Pack status must be pending (first dispatch)
CURRENT_STATUS=$(jq -r --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" '.plans[$plan].packs[$pack].status // "pending"' "$STATE_FILE")
if [ "$CURRENT_STATUS" != "pending" ]; then
  echo "[multi-model-workflow] BLOCKED: Pack ${PACK_ID} status is '${CURRENT_STATUS}', expected 'pending'. Fix: if this is a repair re-dispatch, add [repair-round-N] to the dispatch prompt." >&2
  exit 2
fi

exit 0
