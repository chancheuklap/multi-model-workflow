#!/usr/bin/env bash
# Generates a run summary from workflow-state.
# Called at the end of a run to aggregate metrics.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/state.sh"
STATE_BASE="${STATE_BASE:-.claude/multi-model-workflow}"

RUN_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$RUN_ID" ]]; then
  echo "Usage: run-summary.sh --run-id <id>" >&2
  exit 1
fi

SF="${STATE_BASE}/workflow-state-${RUN_ID}.json"
if [[ ! -f "$SF" ]]; then
  echo "Error: state file not found: $SF" >&2
  exit 1
fi

echo "# Run Summary: $RUN_ID"
echo ""
echo "**Route**: $(jq -r '.route' "$SF")"
echo "**Started**: $(jq -r '.started_at' "$SF")"
echo ""

echo "## Budget"
echo "- Review: $(jq -r '.budget.review_used' "$SF") / $(jq -r '.budget.review_total' "$SF")"
echo "- Effort: $(jq -r '.budget.effort_used' "$SF") / $(jq -r '.budget.effort_total' "$SF")"
echo "- Direction Checks: $(jq -r '.budget.direction_check_count' "$SF")"
echo ""

echo "## Review Effectiveness"
TOTAL=$(jq '.review_dispositions | length' "$SF")
ACCEPTED=$(jq '[.review_dispositions[] | select(.disposition == "accepted")] | length' "$SF")
REJECTED=$(jq '[.review_dispositions[] | select(.disposition == "rejected")] | length' "$SF")
SUPPRESSED=$(jq '[.review_dispositions[] | select(.disposition == "suppress")] | length' "$SF")
echo "- Total findings: $TOTAL"
echo "- Accepted: $ACCEPTED"
echo "- Rejected: $REJECTED"
echo "- Suppressed: $SUPPRESSED"
if [[ "$TOTAL" -gt 0 ]]; then
  REJECT_RATE=$((REJECTED * 100 / TOTAL))
  echo "- Reject rate: ${REJECT_RATE}%"
fi
echo ""

echo "## Plans"
jq -r '.plans[] | "- Plan \(.plan_id): \(.status) (\(.packs | length) packs)"' "$SF" 2>/dev/null || echo "- No plans"
echo ""

echo "## Path A Escalations"
PA_COUNT=$(jq '.path_a_escalation | length' "$SF")
echo "- Active: $PA_COUNT"
