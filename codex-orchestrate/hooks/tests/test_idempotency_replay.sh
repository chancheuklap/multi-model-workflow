#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../../scripts/state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_idempotency_replay.sh ==="

RUN_ID="test-idemp"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 1 >/dev/null

KEY="test-idemp/1.1/r0"

# 1. First check -> NEW
run_test "first idempotency check is NEW" \
  bash "$STATE_SH" idempotency check --run-id "$RUN_ID" --key "$KEY"

# 2. Append key
run_test "idempotency append succeeds" \
  bash "$STATE_SH" idempotency append --run-id "$RUN_ID" --key "$KEY"

# 3. Second check -> DUPLICATE
run_test_expect_fail "second idempotency check is DUPLICATE" \
  bash "$STATE_SH" idempotency check --run-id "$RUN_ID" --key "$KEY"

# 4. Different key -> still NEW
run_test "different key is NEW" \
  bash "$STATE_SH" idempotency check --run-id "$RUN_ID" --key "test-idemp/1.1/r1"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
