#!/usr/bin/env bash
# PostToolUse hook for Bash (if: "Bash(git commit *)").
# Updates execution-state via state-lock after successful Pack commit.
set -euo pipefail

INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$ESF" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
# Pack ID from validated commit message (enforce-plan-commit.sh guarantees format "Pack N.M: ...")
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

  # Pack 2.10: aggregate pack-returns/*.json belonging to this plan into
  # execution-state.plans[PLAN_ID].pack_summary. Reviewers consume this via
  # `jq '.plans["NNN"].pack_summary'` instead of asking Coordinator to
  # assemble a Pack summary table on demand.
  #
  # We filter to pack-returns whose `.pack_id` is one of the packs declared
  # under .plans[PLAN_ID].packs. Aggregation writes the full array (not
  # append) — idempotent if the hook re-fires.
  PACK_RETURNS_DIR="${BUDGET_DIR}/pack-returns/${RUN_ID}"
  if [ -d "$PACK_RETURNS_DIR" ]; then
    PLAN_PACK_IDS=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].packs | keys[]' "$ESF" 2>/dev/null)
    if [ -n "$PLAN_PACK_IDS" ]; then
      AGGREGATE='[]'
      for pid in $PLAN_PACK_IDS; do
        # pack-returns file convention: <pack-id>.json (Worker writes via
        # docs/orchestrate/...; see execution-worker-dispatch.md L81).
        PR_FILE="${PACK_RETURNS_DIR}/${pid}.json"
        if [ -f "$PR_FILE" ] && python3 -m json.tool "$PR_FILE" >/dev/null 2>&1; then
          # Filter only when the file's own .pack_id matches (defense against
          # mis-named files); otherwise skip.
          FILE_PACK=$(jq -r '.pack_id // empty' "$PR_FILE")
          if [ "$FILE_PACK" = "$pid" ]; then
            AGGREGATE=$(jq --slurpfile entry "$PR_FILE" --argjson acc "$AGGREGATE" \
              -n '$acc + $entry')
          fi
        fi
      done
      jq --arg pid "$PLAN_ID" --argjson summary "$AGGREGATE" \
        '.plans[$pid].pack_summary = $summary' \
        "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
    fi
  fi

  # Plan 005 Pack 5.10: when worker_agent_id is set (autonomous-mode Worker still
  # in flight), suppress the "Dispatch Plan Implementation Review" NEXT — the
  # Worker is committing all packs in a single session and will return through
  # agent-return-handler.sh, which is the authoritative routing decision point.
  # Emitting Review NEXT here would mislead Coordinator into dispatching review
  # before Worker returns the plan-return.json artifact.
  WORKER_AGENT_ID=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].worker_agent_id // empty' "$ESF" 2>/dev/null || echo "")
  if [ -n "$WORKER_AGENT_ID" ] && [ "$WORKER_AGENT_ID" != "null" ]; then
    MSG="[multi-model-workflow] STATE: All ${PLAN_TOTAL} packs in Plan ${PLAN_ID} committed (end_commit: ${COMMIT_SHA}). Worker ${WORKER_AGENT_ID} still in session — wait for SubagentStop / agent-return-handler.sh. Do NOT dispatch Plan Implementation Review yet."
  else
    MSG="[multi-model-workflow] NEXT: All ${PLAN_TOTAL} packs in Plan ${PLAN_ID} committed (end_commit: ${COMMIT_SHA}). Dispatch Plan Implementation Review."
  fi
else
  MSG="[multi-model-workflow] STATE: Pack ${PACK_ID} committed (${PLAN_DONE}/${PLAN_TOTAL} in Plan ${PLAN_ID})."
fi

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
