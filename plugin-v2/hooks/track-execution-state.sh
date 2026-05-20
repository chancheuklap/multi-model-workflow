#!/usr/bin/env bash
# PostToolUse hook for Bash (if: "Bash(git commit *)").
# Updates execution-state file after successful Pack commit.
# Pure state tracking — never blocks.
set -euo pipefail

INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")
STATE_FILE="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
PACK_ID=$(echo "$COMMAND" | sed -n 's/.*Pack \([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

PLAN_KEY=$(printf "%03d" "$(echo "$PACK_ID" | cut -d. -f1)")
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

jq --arg plan "$PLAN_KEY" --arg pack "$PACK_ID" --arg sha "$COMMIT_SHA" '
  .plans[$plan].packs[$pack].status = "committed" |
  .plans[$plan].packs[$pack].commit_sha = $sha |
  .plans[$plan].end_commit = $sha
' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

DONE=$(jq --arg plan "$PLAN_KEY" '[.plans[$plan].packs | to_entries[] | select(.value.status == "committed")] | length' "$STATE_FILE")
TOTAL=$(jq --arg plan "$PLAN_KEY" '.plans[$plan].expected_pack_ids | length' "$STATE_FILE")

jq -n --arg msg "[multi-model-workflow] STATE: Pack ${PACK_ID} committed (${DONE}/${TOTAL} in Plan ${PLAN_KEY})." \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
