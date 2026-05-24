#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_budget_direction_check.sh ==="

RUN_ID="test-bdc"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null

# 1. Budget check fails when pending_plan_count
run_test_expect_fail "budget check fails on pending_plan_count" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID"

# 2. Budget increment fails before initialization
run_test_expect_fail "budget increment-review fails on pending_plan_count" \
  bash "$STATE_SH" budget increment-review --run-id "$RUN_ID"

# 3. Initialize budget
run_test "budget initialize" \
  bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 2

# 4. Budget check passes after initialization
run_test "budget check passes after init" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID"

# 5. Manual targeted re-review budget increment
run_test "budget increment-review increments review_used" \
  bash "$STATE_SH" budget increment-review --run-id "$RUN_ID"

run_test "review_used is 1 after increment-review" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_used') == '1' ]]"

# 6. Direction check trigger + ack
run_test "direction-check trigger" \
  bash "$STATE_SH" direction-check trigger --run-id "$RUN_ID" --type review --threshold-percent 80

run_test "direction-check status is pending" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.pending_direction_check.ack_status') == 'pending' ]]"

run_test "direction-check ack stop" \
  bash "$STATE_SH" direction-check ack --run-id "$RUN_ID" --action stop

run_test "direction-check stopped" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.pending_direction_check.ack_status') == 'stopped' ]]"

# 7. Unlimited budget route
RUN_ID2="test-bdc-hotfix"
bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "hf" --route "hotfix" >/dev/null

run_test "unlimited budget check passes" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID2"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
