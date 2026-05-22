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

echo "=== test_path_a_re_review.sh ==="

RUN_ID="test-pa"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null

# 1. Start Path A escalation
run_test "path-a-escalation start" \
  bash "$STATE_SH" path-a-escalation start --run-id "$RUN_ID" --finding-id "F1" --round 1

# 2. Verify entry created
run_test "path-a entry exists" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.path_a_escalation | length') == '1' ]]"

# 3. Update with needs_repair -> blocked_for_self_fix
run_test "path-a-escalation update needs_repair" \
  bash "$STATE_SH" path-a-escalation update --run-id "$RUN_ID" --finding-id "F1" --verdict needs_repair

run_test "blocked_for_self_fix is true" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.path_a_escalation[0].blocked_for_self_fix') == 'true' ]]"

# 4. Cannot start again for blocked finding
run_test_expect_fail "re-start blocked finding rejected" \
  bash "$STATE_SH" path-a-escalation start --run-id "$RUN_ID" --finding-id "F1"

# 5. Clear
run_test "path-a-escalation clear" \
  bash "$STATE_SH" path-a-escalation clear --run-id "$RUN_ID" --finding-id "F1"

run_test "path-a empty after clear" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.path_a_escalation | length') == '0' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
