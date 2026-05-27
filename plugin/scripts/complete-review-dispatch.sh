#!/usr/bin/env bash
# Marks a reviewer result durable in the registry.
#
# Claude-native split-of-concerns:
#   - Budget counting is performed by the PostToolUse hook
#     (hooks/track-review-budget.sh) the moment `codex-companion result`
#     fires. The hook is the auto-counter; do not double-count here.
#   - This script only writes the registry entry's durability marker
#     (result_file, completed_at, status=completed) so that compaction
#     recovery and disposition tracking can find the durable artifact.
#   - --allow-over-budget / --override-reason are recorded as registry
#     metadata so that audit can see which reviews were explicit
#     user-authorized over-budget dispatches.
set -euo pipefail

RUN_ID=""
GATE=""
AGENT_ID=""
RESULT_FILE=""
ALLOW_OVER_BUDGET="false"
OVERRIDE_REASON=""

usage() {
  cat <<'USAGE'
Usage: complete-review-dispatch.sh --run-id RUN_ID --gate GATE --agent-id AGENT_ID --result-file PATH [--allow-over-budget --override-reason TEXT]

The agent-id is the reviewer identity: on Claude this is the JOB_ID returned by
`codex-companion.mjs task` (or shared across resume calls).
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --gate) GATE="${2:-}"; shift 2 ;;
    --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
    --result-file) RESULT_FILE="${2:-}"; shift 2 ;;
    --allow-over-budget) ALLOW_OVER_BUDGET="true"; shift ;;
    --override-reason) OVERRIDE_REASON="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$RUN_ID" && -n "$GATE" && -n "$AGENT_ID" && -n "$RESULT_FILE" ]] || usage
if [[ "$ALLOW_OVER_BUDGET" == "true" && -z "$OVERRIDE_REASON" ]]; then
  echo "Error: --override-reason required with --allow-over-budget" >&2
  exit 2
fi
[[ -s "$RESULT_FILE" ]] || {
  echo "Error: review result file missing or empty: $RESULT_FILE" >&2
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUDGET_DIR="${STATE_BASE:-.claude/multi-model-workflow}"
REGISTRY_FILE="$BUDGET_DIR/review-registry/${GATE}.json"

if [[ ! -f "$REGISTRY_FILE" ]]; then
  BASELINE_REGISTRY=$(find "$BUDGET_DIR/review-registry" -name '*.json' -type f 2>/dev/null \
    -exec jq -r --arg run "$RUN_ID" --arg agent "$AGENT_ID" 'select(.run_id == $run and .agent_id == $agent and (.review_intent // "baseline") == "baseline") | input_filename' {} \; \
    | head -1)
  if [[ -z "$BASELINE_REGISTRY" ]]; then
    echo "Error: review registry not found for gate: $GATE" >&2
    exit 2
  fi

  mkdir -p "$BUDGET_DIR/review-registry"
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq -n \
    --arg run_id "$RUN_ID" \
    --arg gate "$GATE" \
    --arg agent_id "$AGENT_ID" \
    --arg created_at "$now" \
    '{
      run_id: $run_id,
      gate: $gate,
      phase: null,
      review_intent: "targeted-re-review",
      agent_id: $agent_id,
      prompt_file: null,
      result_file: null,
      status: "dispatched",
      created_at: $created_at,
      completed_at: null,
      budget_counted: false
    }' > "$REGISTRY_FILE"
fi

RECORDED_AGENT=$(jq -r '.agent_id // empty' "$REGISTRY_FILE")
if [[ "$RECORDED_AGENT" != "$AGENT_ID" ]]; then
  echo "Error: completed review agent_id does not match registry" >&2
  exit 2
fi

if [[ "$(jq -r '.status // empty' "$REGISTRY_FILE")" == "completed" ]] \
   || [[ "$(jq -r '.status // empty' "$REGISTRY_FILE")" == "disposition_started" ]] \
   || [[ "$(jq -r '.status // empty' "$REGISTRY_FILE")" == "disposition_done" ]]; then
  echo "OK (already durable)"
  exit 0
fi

now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
tmp="${REGISTRY_FILE}.tmp"
if [[ "$ALLOW_OVER_BUDGET" == "true" ]]; then
  OVER_BUDGET_JSON="true"
else
  OVER_BUDGET_JSON="false"
fi

jq --arg result_file "$RESULT_FILE" --arg completed_at "$now" \
  --argjson over_budget "$OVER_BUDGET_JSON" --arg override_reason "$OVERRIDE_REASON" '
  .result_file = $result_file
  | .status = "completed"
  | .completed_at = $completed_at
  | .over_budget_allowed = $over_budget
  | .over_budget_reason = (if $over_budget then $override_reason else null end)
' "$REGISTRY_FILE" > "$tmp"
mv "$tmp" "$REGISTRY_FILE"

echo "OK"
