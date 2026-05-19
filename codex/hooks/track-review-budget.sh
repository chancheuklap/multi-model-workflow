#!/usr/bin/env bash
set -euo pipefail

BUDGET_DIR=".codex/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"

if [ ! -f "$RUN_ID_FILE" ]; then
  exit 0
fi

RUN_ID="$(cat "$RUN_ID_FILE" 2>/dev/null || true)"
if [ -z "$RUN_ID" ]; then
  exit 0
fi

BUDGET_FILE="${BUDGET_DIR}/budget-${RUN_ID}.json"
if [ ! -f "$BUDGET_FILE" ]; then
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[multi-model-workflow] jq not found; review budget was not updated." >&2
  exit 0
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
LANE="${MULTI_MODEL_WORKFLOW_REVIEW_LANE:-unknown}"
NAME="${MULTI_MODEL_WORKFLOW_REVIEW_NAME:-review}"

jq --arg ts "$TIMESTAMP" --arg lane "$LANE" --arg name "$NAME" '
  .budget_used = (.budget_used // 0) + 1 |
  .dispatches = ((.dispatches // []) + [{
    "timestamp": $ts,
    "lane": $lane,
    "name": $name
  }])
' "$BUDGET_FILE" > "$TMP_FILE"
mv "$TMP_FILE" "$BUDGET_FILE"

USED="$(jq -r '.budget_used // 0' "$BUDGET_FILE")"
TOTAL="$(jq -r '.budget_total // 0' "$BUDGET_FILE")"

if [ "$TOTAL" -eq 0 ] 2>/dev/null; then
  echo "[multi-model-workflow] Review budget used: ${USED}; total not assigned yet." >&2
elif [ "$USED" -ge "$TOTAL" ]; then
  echo "[multi-model-workflow] BUDGET EXHAUSTED: ${USED}/${TOTAL}. Stop dispatching reviews and report to user." >&2
else
  THRESHOLD=$(( TOTAL * 80 / 100 ))
  if [ "$USED" -ge "$THRESHOLD" ]; then
    echo "[multi-model-workflow] DIRECTION CHECK: review budget at ${USED}/${TOTAL}. Confirm next owner and scope before spending more review budget." >&2
  else
    echo "[multi-model-workflow] Review budget: ${USED}/${TOTAL}." >&2
  fi
fi
