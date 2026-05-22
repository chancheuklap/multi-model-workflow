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

echo "=== test_disposition_refs_validation.sh ==="

RUN_ID="test-disp-refs"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 1 >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F1" --disposition "accepted" --evidence "verified" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F2" --disposition "rejected" >/dev/null

# Set cursor to returned for repairing transition
bash "$STATE_SH" update --run-id "$RUN_ID" --field '.cursor.phase' --value '"returned"' >/dev/null

# 1. Valid disposition ref -> pass
run_test "valid accepted ref passes" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor Coordinator --from returned --to repairing --disposition-refs "F1"

# Reset cursor
bash "$STATE_SH" update --run-id "$RUN_ID" --field '.cursor.phase' --value '"returned"' >/dev/null

# 2. Rejected ref -> fail
run_test_expect_fail "rejected ref blocked" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor Coordinator --from returned --to repairing --disposition-refs "F2"

# 3. Non-existent ref -> fail
run_test_expect_fail "non-existent ref blocked" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor Coordinator --from returned --to repairing --disposition-refs "F99"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
