#!/usr/bin/env bash
# Validates that a plan file's Pack count is within threshold.
# Default threshold: ≤12 Packs per plan (承诺 9a).
set -euo pipefail

PLAN_FILE="$1"
THRESHOLD="${2:-12}"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "Error: plan file not found: $PLAN_FILE" >&2
  exit 1
fi

PACK_COUNT=$(grep -cE '^### Pack [0-9]' "$PLAN_FILE" || echo "0")

if [[ "$PACK_COUNT" -gt "$THRESHOLD" ]]; then
  echo "OVER_THRESHOLD: $PACK_COUNT packs (threshold: $THRESHOLD)" >&2
  echo "Plan may need splitting or the threshold needs explicit override."
  exit 1
fi

echo "OK: $PACK_COUNT packs (threshold: $THRESHOLD)"
exit 0
