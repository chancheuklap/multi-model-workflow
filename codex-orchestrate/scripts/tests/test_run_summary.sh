#!/usr/bin/env bash
# Tests run-summary.sh: fixture state produces summary output.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
SUMMARY_SH="$SCRIPT_DIR/../run-summary.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_run_summary.sh ==="

RUN_ID="test-summary"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "my-feature" --route "formal" >/dev/null

# Initialize budget
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 2 >/dev/null

# Add some dispositions
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F1" --disposition "accepted" --evidence "checked" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F2" --disposition "rejected" >/dev/null

# Test 1: summary runs without error
run_test "run-summary.sh produces output" \
  bash -c "bash '$SUMMARY_SH' --run-id '$RUN_ID' | grep -q 'Run Summary'"

# Test 2: summary contains route
run_test "summary contains route" \
  bash -c "bash '$SUMMARY_SH' --run-id '$RUN_ID' | grep -q 'formal'"

# Test 3: summary contains budget info
run_test "summary contains budget" \
  bash -c "bash '$SUMMARY_SH' --run-id '$RUN_ID' | grep -q 'Review:'"

# Test 4: summary contains finding counts
run_test "summary contains finding count" \
  bash -c "bash '$SUMMARY_SH' --run-id '$RUN_ID' | grep -q 'Total findings: 2'"

# Test 5: missing run-id fails
run_test_expect_fail "missing run-id fails" \
  bash "$SUMMARY_SH"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
