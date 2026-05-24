#!/usr/bin/env bash
# Aggregates review effectiveness metrics from review_dispositions.
# Updates review_effectiveness in workflow-state.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/state-lock.sh"

STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

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
  (.review_dispositions | length) as $total |
  ([.review_dispositions[] | select(.disposition == "rejected")] | length) as $reject |
  ([.review_dispositions[] | select(.disposition == "suppress")] | length) as $suppress |
  ([.review_dispositions[] | select(.disposition == "path-a")] | length) as $path_a |
  ([.review_dispositions[] | select(.disposition == "path-b")] | length) as $path_b |

  # Health range checks
  (if $total > 0 then
    []
    | if ($reject * 100 / $total) > 60 then
        . + [("reject rate " + (($reject * 100 / $total) | tostring) + "% > 60% — possible systematic reviewer dismissal")]
      else . end
    | if ($reject * 100 / $total) < 10 then
        . + [("reject rate " + (($reject * 100 / $total) | tostring) + "% < 10% — possible rubber-stamping")]
      else . end
    | if ($suppress * 100 / $total) > 30 then
        . + [("suppress rate " + (($suppress * 100 / $total) | tostring) + "% > 30% — possible low-confidence abuse")]
      else . end
    | if (($path_a + $path_b) > 0) and (($path_a * 100 / ($path_a + $path_b)) > 50) then
        . + [("Path A rate " + (($path_a * 100 / ($path_a + $path_b)) | tostring) + "% > 50% — excessive self-repair")]
      else . end
  else [] end) as $warnings |

  .review_effectiveness = {
    reject_count: $reject,
    suppress_count: $suppress,
    path_a_count: $path_a,
    path_b_count: $path_b,
    total_findings: $total,
    last_aggregated_at: $ts,
    health_warnings: $warnings
  }
' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

# Output warnings to stderr
WARNINGS=$(jq -r '.review_effectiveness.health_warnings[]? // empty' "$SF")
if [[ -n "$WARNINGS" ]]; then
  while IFS= read -r w; do
    echo "WARN: $w" >&2
  done <<< "$WARNINGS"
fi
