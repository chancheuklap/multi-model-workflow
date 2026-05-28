#!/usr/bin/env bash
# Tests that old shim scripts (validate-review-dispatch.sh, record-review-dispatch.sh)
# correctly forward to the new dispatch-review.sh with identical behavior.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/.."

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_dispatch_review_shim.sh ==="

# Test 1: dispatch-review.sh exists and is executable
run_test "dispatch-review.sh is executable" test -x "$SCRIPTS_DIR/dispatch-review.sh"

# Test 2: dispatch-route-worker.sh exists and is executable
run_test "dispatch-route-worker.sh is executable" test -x "$SCRIPTS_DIR/dispatch-route-worker.sh"

# Test 3: old shim files exist and are ≤ 10 lines
for shim in validate-review-dispatch.sh record-review-dispatch.sh validate-route-worker-dispatch.sh record-route-worker-dispatch.sh; do
  run_test "$shim is shim (≤ 10 lines)" bash -c "[ \$(wc -l < '$SCRIPTS_DIR/$shim') -le 10 ]"
done

# Test 4: --help subcommand works for both new scripts
run_test "dispatch-review.sh --help works" bash -c "bash '$SCRIPTS_DIR/dispatch-review.sh' --help 2>&1 | grep -q 'validate'"
run_test "dispatch-route-worker.sh --help works" bash -c "bash '$SCRIPTS_DIR/dispatch-route-worker.sh' --help 2>&1 | grep -q 'validate'"

# Test 5: shim exit code matches new script (both should fail with no args → exit 2)
OLD_RC=0; bash "$SCRIPTS_DIR/validate-review-dispatch.sh" 2>/dev/null || OLD_RC=$?
NEW_RC=0; bash "$SCRIPTS_DIR/dispatch-review.sh" validate 2>/dev/null || NEW_RC=$?
run_test "validate-review-dispatch shim exit code matches dispatch-review.sh validate" bash -c "[[ $OLD_RC -eq $NEW_RC ]]"

OLD_RC=0; bash "$SCRIPTS_DIR/validate-route-worker-dispatch.sh" 2>/dev/null || OLD_RC=$?
NEW_RC=0; bash "$SCRIPTS_DIR/dispatch-route-worker.sh" validate 2>/dev/null || NEW_RC=$?
run_test "validate-route-worker-dispatch shim exit code matches dispatch-route-worker.sh validate" bash -c "[[ $OLD_RC -eq $NEW_RC ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
