#!/usr/bin/env bash
# PostToolUse hook for Bash (if: "Bash(git commit *)").
# Updates workflow-state via state.sh after successful Pack commit.
set -euo pipefail

INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
PACK_ID=$(echo "$COMMAND" | sed -n 's/.*Pack \([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
if [ -z "$PACK_ID" ]; then exit 0; fi

COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
PLAN_ID=$(echo "$PACK_ID" | cut -d. -f1)

export STATE_BASE="$BUDGET_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../scripts/state.sh"

jq --arg pack "$PACK_ID" --arg sha "$COMMIT_SHA" --argjson pidx "$((PLAN_ID - 1))" '
  if .plans[$pidx] then
    .plans[$pidx].packs |= map(if .pack_id == $pack then .status = "committed" | .commit_sha = $sha else . end)
  else . end
' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

DONE=$(jq --argjson pidx "$((PLAN_ID - 1))" '[.plans[$pidx].packs[]? | select(.status == "committed")] | length' "$SF")
TOTAL=$(jq --argjson pidx "$((PLAN_ID - 1))" '[.plans[$pidx].packs[]?] | length' "$SF")

if [ "$DONE" -eq "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
  MSG="[multi-model-workflow] NEXT: All ${TOTAL} packs in Plan ${PLAN_ID} committed. Dispatch Plan Implementation Review."
else
  MSG="[multi-model-workflow] STATE: Pack ${PACK_ID} committed (${DONE}/${TOTAL} in Plan ${PLAN_ID})."
fi

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
