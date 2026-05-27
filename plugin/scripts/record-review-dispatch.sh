#!/usr/bin/env bash
# Records a successful Codex reviewer baseline dispatch after the Agent call returns.
set -euo pipefail

PROMPT_FILE=""
GATE=""
AGENT_ID=""

usage() {
  cat <<'USAGE'
Usage: record-review-dispatch.sh --prompt-file PATH --gate GATE --agent-id AGENT_ID
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    --gate) GATE="${2:-}"; shift 2 ;;
    --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" && -n "$GATE" && -n "$AGENT_ID" ]] || usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
PHASE=$(echo "$ENVELOPE" | jq -r '.phase // empty')
REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "Error: run_id required" >&2
  exit 2
fi

if [[ "$REVIEW_INTENT" != "baseline" ]]; then
  echo "Error: record-review-dispatch only records baseline reviewer dispatches" >&2
  exit 2
fi

BUDGET_DIR="${STATE_BASE:-.claude/multi-model-workflow}"
mkdir -p "$BUDGET_DIR/review-agents" "$BUDGET_DIR/review-registry"

echo "$AGENT_ID" > "$BUDGET_DIR/review-agents/${GATE}.agent-id"

now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq -n \
  --arg run_id "$RUN_ID" \
  --arg gate "$GATE" \
  --arg phase "$PHASE" \
  --arg agent_id "$AGENT_ID" \
  --arg prompt_file "$PROMPT_FILE" \
  --arg created_at "$now" \
  '{
    run_id: $run_id,
    gate: $gate,
    phase: $phase,
    review_intent: "baseline",
    agent_id: $agent_id,
    prompt_file: $prompt_file,
    result_file: null,
    status: "dispatched",
    created_at: $created_at,
    completed_at: null,
    budget_counted: false
  }' > "$BUDGET_DIR/review-registry/${GATE}.json"

echo "OK"
