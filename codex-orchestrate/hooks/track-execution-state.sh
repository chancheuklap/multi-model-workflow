#!/usr/bin/env bash
# PostToolUse hook for Bash (if: "Bash(git commit *)").
# Updates execution-state via state-lock after successful Pack commit.
set -euo pipefail

INPUT=$(cat)
EXIT_CODE=$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.tool_response.exit_code // 0) else 0 end' 2>/dev/null || echo 0)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

BUDGET_DIR=".codex/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$ESF" ]; then exit 0; fi

COMMAND=$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.tool_input.command // empty) else empty end' 2>/dev/null || true)
# Pack ID from validated commit message (enforce-pack-commit.sh guarantees format "Pack N.M: ...")
# Uses bash regex instead of sed — input is commit message text, not prompt/control-plane
if [[ "$COMMAND" =~ Pack[[:space:]]+([0-9]+\.[0-9]+) ]]; then
  PACK_ID="${BASH_REMATCH[1]}"
else
  PACK_ID=""
fi
if [ -z "$PACK_ID" ]; then exit 0; fi

COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"

LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

# Update execution-state (pack-level data per Ruling 2)
jq --arg pack "$PACK_ID" --arg sha "$COMMIT_SHA" '
  .plans |= with_entries(
    .value.packs |= with_entries(
      if .key == $pack then
        .value.status = "committed" | .value.commit_sha = $sha
      else . end
    )
  )
' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"

# Count completed packs across all plans
DONE=$(jq '[.plans | to_entries[] | .value.packs | to_entries[] | select(.value.status == "committed")] | length' "$ESF")
TOTAL=$(jq '[.plans | to_entries[] | .value.packs | to_entries[]] | length' "$ESF")

# Find which plan this pack belongs to
PLAN_ID=$(jq -r --arg pack "$PACK_ID" '[.plans | to_entries[] | select(.value.packs[$pack] != null) | .key] | first // empty' "$ESF")

# Count packs in this plan
PLAN_DONE=0
PLAN_TOTAL=0
if [ -n "$PLAN_ID" ]; then
  PLAN_DONE=$(jq --arg pid "$PLAN_ID" '[.plans[$pid].packs | to_entries[] | select(.value.status == "committed")] | length' "$ESF")
  PLAN_TOTAL=$(jq --arg pid "$PLAN_ID" '[.plans[$pid].packs | to_entries[]] | length' "$ESF")
fi

if [ "$PLAN_DONE" -eq "$PLAN_TOTAL" ] && [ "$PLAN_TOTAL" -gt 0 ]; then
  # Write end_commit for plan review diff (start_commit..end_commit)
  jq --arg pid "$PLAN_ID" --arg sha "$COMMIT_SHA" '
    .plans[$pid].end_commit = $sha
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
  MSG="[codex-orchestrate] NEXT: All ${PLAN_TOTAL} packs in Plan ${PLAN_ID} committed (end_commit: ${COMMIT_SHA}). Dispatch Plan Implementation Review."
else
  MSG="[codex-orchestrate] STATE: Pack ${PACK_ID} committed (${PLAN_DONE}/${PLAN_TOTAL} in Plan ${PLAN_ID})."
fi

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
