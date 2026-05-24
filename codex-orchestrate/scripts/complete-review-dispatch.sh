#!/usr/bin/env bash
# Marks a reviewer result durable and increments review budget exactly once.
set -euo pipefail

RUN_ID=""
GATE=""
AGENT_ID=""
RESULT_FILE=""

usage() {
  cat <<'USAGE'
Usage: complete-review-dispatch.sh --run-id RUN_ID --gate GATE --agent-id AGENT_ID --result-file PATH
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --gate) GATE="${2:-}"; shift 2 ;;
    --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
    --result-file) RESULT_FILE="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$RUN_ID" && -n "$GATE" && -n "$AGENT_ID" && -n "$RESULT_FILE" ]] || usage
[[ -s "$RESULT_FILE" ]] || {
  echo "Error: review result file missing or empty: $RESULT_FILE" >&2
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"
REGISTRY_FILE="$BUDGET_DIR/review-registry/${GATE}.json"

if [[ ! -f "$REGISTRY_FILE" ]]; then
  echo "Error: review registry not found for gate: $GATE" >&2
  exit 2
fi

RECORDED_AGENT=$(jq -r '.agent_id // empty' "$REGISTRY_FILE")
if [[ "$RECORDED_AGENT" != "$AGENT_ID" ]]; then
  echo "Error: completed review agent_id does not match registry" >&2
  exit 2
fi

if [[ "$(jq -r '.budget_counted // false' "$REGISTRY_FILE")" == "true" ]]; then
  echo "OK"
  exit 0
fi

bash "$SCRIPT_DIR/state.sh" budget increment-review --run-id "$RUN_ID" >/dev/null

now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
tmp="${REGISTRY_FILE}.tmp"
jq --arg result_file "$RESULT_FILE" --arg completed_at "$now" '
  .result_file = $result_file
  | .status = "completed"
  | .completed_at = $completed_at
  | .budget_counted = true
' "$REGISTRY_FILE" > "$tmp"
mv "$tmp" "$REGISTRY_FILE"

echo "OK"
