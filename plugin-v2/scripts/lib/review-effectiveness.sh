#!/usr/bin/env bash
# Aggregates review effectiveness metrics from review_dispositions.
# Updates review_effectiveness in workflow-state.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/state-lock.sh"

STATE_BASE="${STATE_BASE:-.claude/multi-model-workflow}"

RUN_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SF="${STATE_BASE}/workflow-state-${RUN_ID}.json"
if [[ ! -f "$SF" ]]; then exit 1; fi

LOCK_DIR="${STATE_BASE}/${RUN_ID}.lock"

state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq --arg ts "$NOW" '
  .review_effectiveness = {
    reject_count: [.review_dispositions[] | select(.disposition == "rejected")] | length,
    suppress_count: [.review_dispositions[] | select(.disposition == "suppress")] | length,
    path_a_count: [.review_dispositions[] | select(.disposition == "path-a")] | length,
    path_b_count: [.review_dispositions[] | select(.disposition == "path-b")] | length,
    total_findings: (.review_dispositions | length),
    last_aggregated_at: $ts
  }
' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"
