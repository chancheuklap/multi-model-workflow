#!/usr/bin/env bash
# Records Coordinator consumption of a durable reviewer result.
set -euo pipefail

RUN_ID=""
GATE=""
STATUS=""

usage() {
  cat <<'USAGE'
Usage: record-review-disposition.sh --run-id RUN_ID --gate GATE --status started|completed
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --gate) GATE="${2:-}"; shift 2 ;;
    --status) STATUS="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$RUN_ID" && -n "$GATE" && -n "$STATUS" ]] || usage
[[ "$STATUS" == "started" || "$STATUS" == "completed" ]] || usage

BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"
REGISTRY_FILE="$BUDGET_DIR/review-registry/${GATE}.json"

[[ -f "$REGISTRY_FILE" ]] || {
  echo "Error: review registry not found for gate: $GATE" >&2
  exit 2
}

RECORDED_RUN=$(jq -r '.run_id // empty' "$REGISTRY_FILE")
if [[ "$RECORDED_RUN" != "$RUN_ID" ]]; then
  echo "Error: review registry run_id does not match" >&2
  exit 2
fi

RESULT_FILE=$(jq -r '.result_file // empty' "$REGISTRY_FILE")
if [[ -z "$RESULT_FILE" || "$RESULT_FILE" == "null" || ! -s "$RESULT_FILE" ]]; then
  echo "Error: durable review result missing for gate: $GATE" >&2
  exit 2
fi

CURRENT_STATUS=$(jq -r '.status // empty' "$REGISTRY_FILE")
case "$STATUS:$CURRENT_STATUS" in
  started:completed|started:disposition_started|started:disposition_done) ;;
  completed:completed|completed:disposition_started|completed:disposition_done) ;;
  *)
    echo "Error: cannot mark disposition $STATUS from registry status '$CURRENT_STATUS'" >&2
    exit 2
    ;;
esac

now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
tmp="${REGISTRY_FILE}.tmp"

if [[ "$STATUS" == "started" ]]; then
  jq --arg now "$now" '
    if .status == "disposition_done" then
      .
    else
      .status = "disposition_started"
      | .disposition_started_at = (.disposition_started_at // $now)
    end
  ' "$REGISTRY_FILE" > "$tmp"
else
  jq --arg now "$now" '
    .status = "disposition_done"
    | .disposition_started_at = (.disposition_started_at // $now)
    | .disposition_completed_at = (.disposition_completed_at // $now)
  ' "$REGISTRY_FILE" > "$tmp"
fi

mv "$tmp" "$REGISTRY_FILE"
echo "OK"
