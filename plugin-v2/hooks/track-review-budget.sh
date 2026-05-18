#!/usr/bin/env bash
# multi-model-workflow: SubagentStop hook for codex:codex-rescue
# Increments review budget counter. Reads active-run-id to find budget file.
# Must exit 0 — never block agent completion.

set -euo pipefail

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"

if [ ! -f "$RUN_ID_FILE" ]; then
  echo "[multi-model-workflow] No active-run-id found. Skipping budget tracking." >&2
  exit 0
fi

RUN_ID=$(cat "$RUN_ID_FILE")
BUDGET_FILE="${BUDGET_DIR}/budget-${RUN_ID}.json"

if [ ! -f "$BUDGET_FILE" ]; then
  echo "[multi-model-workflow] Budget file not found: ${BUDGET_FILE}. Skipping." >&2
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[multi-model-workflow] jq not found — budget tracking requires jq. Skipping." >&2
  exit 0
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq --arg ts "$TIMESTAMP" '
  .budget_used += 1 |
  .dispatches += [{"timestamp": $ts}]
' "$BUDGET_FILE" > "${BUDGET_FILE}.tmp" && mv "${BUDGET_FILE}.tmp" "$BUDGET_FILE"

USED=$(jq -r '.budget_used' "$BUDGET_FILE")
TOTAL=$(jq -r '.budget_total' "$BUDGET_FILE")

echo "[multi-model-workflow] Review budget: ${USED}/${TOTAL} dispatches used." >&2

exit 0
