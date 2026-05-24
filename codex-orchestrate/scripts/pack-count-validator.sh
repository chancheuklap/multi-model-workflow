#!/usr/bin/env bash
# Validates that a plan file's Pack count is within threshold.
# Two-level thresholds (承诺 9a):
#   $1 = plan file path (required)
#   $2 = WARN threshold (default 8): pack count > warn triggers WARN
#   $3 = OVER threshold (default 12): pack count > over triggers OVER_THRESHOLD
#
# Exit codes: 0 = OK or WARN, 1 = OVER_THRESHOLD
# Output: OK / WARN / OVER_THRESHOLD with pack count
set -euo pipefail

PLAN_FILE="$1"
WARN_THRESHOLD="${2:-8}"
OVER_THRESHOLD="${3:-12}"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "Error: plan file not found: $PLAN_FILE" >&2
  exit 1
fi

PACK_COUNT=$(grep -cE '^### Pack [0-9]' "$PLAN_FILE" || echo "0")

# Bootstrap exception: plans that self-acknowledge over-threshold pack count
if grep -qiE 'self-violation acknowledgment|bootstrap' "$PLAN_FILE" 2>/dev/null; then
  if [[ "$PACK_COUNT" -gt "$OVER_THRESHOLD" ]]; then
    echo "WARN: bootstrap plan with $PACK_COUNT packs (over threshold $OVER_THRESHOLD)" >&2
    echo "BOOTSTRAP_OK: $PACK_COUNT packs"
    exit 0
  fi
fi

if [[ "$PACK_COUNT" -gt "$OVER_THRESHOLD" ]]; then
  echo "OVER_THRESHOLD: $PACK_COUNT packs (warn: $WARN_THRESHOLD, over: $OVER_THRESHOLD)" >&2
  echo "Plan needs splitting — pack count exceeds maximum threshold."
  exit 1
fi

if [[ "$PACK_COUNT" -gt "$WARN_THRESHOLD" ]]; then
  echo "WARN: $PACK_COUNT packs (warn: $WARN_THRESHOLD, over: $OVER_THRESHOLD)" >&2
  echo "Pack count exceeds recommended range. Consider splitting."
  exit 0
fi

echo "OK: $PACK_COUNT packs (warn: $WARN_THRESHOLD, over: $OVER_THRESHOLD)"
exit 0
