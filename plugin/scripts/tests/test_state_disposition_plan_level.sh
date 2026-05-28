#!/usr/bin/env bash
# Plan 005 Pack 5.6: state.sh disposition append --plan-id verification.
# Already implemented in state.sh (Plan 002 Pack 2.4 + 2.6). This test pins behavior.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="disp-plan-test"
pass=0
fail=0

assert_eq() {
  local name="$1" actual="$2" expected="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name — expected '$expected', got '$actual'"
    fail=$((fail + 1))
  fi
}

echo "=== test_state_disposition_plan_level.sh ==="

# init workflow-state
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null 2>&1

# Append disposition with --plan-id
bash "$STATE_SH" disposition append --run-id "$RUN_ID" \
  --review-round 1 --finding-id F-001 --disposition accepted \
  --confidence 90 --severity H --evidence "fix here" --path "plan-review" \
  --plan-id "005" 2>/dev/null

SF="$FIXTURE_DIR/workflow-state-$RUN_ID.json"
LAST_PLAN=$(jq -r '.review_dispositions[-1].plan_id' "$SF")
assert_eq "plan_id field written" "$LAST_PLAN" "005"
LAST_FID=$(jq -r '.review_dispositions[-1].finding_id' "$SF")
assert_eq "finding_id field written" "$LAST_FID" "F-001"

# Append disposition WITHOUT --plan-id (backward compat) → plan_id is null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" \
  --review-round 1 --finding-id F-002 --disposition rejected \
  --confidence 70 --severity L --evidence "" --path "plan-review" 2>/dev/null

LAST_PLAN=$(jq -r '.review_dispositions[-1].plan_id' "$SF")
assert_eq "no --plan-id → plan_id is null" "$LAST_PLAN" "null"

# Counts both
COUNT=$(jq '.review_dispositions | length' "$SF")
assert_eq "two dispositions appended" "$COUNT" "2"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
