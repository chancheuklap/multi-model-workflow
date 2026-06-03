#!/usr/bin/env bash
# Tests the Light→Formal escape-hatch upgrade command `budget reinitialize`:
#   - init --route light → budget unlimited (D-A)
#   - budget reinitialize --plan-count 2 → budget_status=initialized,
#     route=formal, review_total=3*2+12=18, effort_total=36
#   - reinitialize from a non-unlimited (formal pending_plan_count) entry errors (exit≠0)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_budget_reinitialize.sh ==="

# --- Light run starts unlimited (D-A) ---
RUN_ID="test-reinit-light"
SF="$FIXTURE_DIR/workflow-state-${RUN_ID}.json"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "light" >/dev/null

run_test "light init budget_status == unlimited" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$SF') == 'unlimited' ]]"
run_test "light init route == light" \
  bash -c "[[ \$(jq -r '.route' '$SF') == 'light' ]]"

# --- Escape-hatch upgrade: reinitialize from unlimited ---
bash "$STATE_SH" budget reinitialize --run-id "$RUN_ID" --plan-count 2 >/dev/null

run_test "reinitialize sets budget_status == initialized" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$SF') == 'initialized' ]]"
run_test "reinitialize flips route → formal" \
  bash -c "[[ \$(jq -r '.route' '$SF') == 'formal' ]]"
run_test "reinitialize review_total == 18 (3*2+12)" \
  bash -c "[[ \$(jq -r '.budget.review_total' '$SF') == '18' ]]"
run_test "reinitialize effort_total == 36 (review_total*2)" \
  bash -c "[[ \$(jq -r '.budget.effort_total' '$SF') == '36' ]]"
run_test "reinitialize plan_count == 2" \
  bash -c "[[ \$(jq -r '.plan_count' '$SF') == '2' ]]"

# --- Entry guard: reinitialize from non-unlimited (formal pending_plan_count) must error ---
RUN_ID2="test-reinit-formal"
SF2="$FIXTURE_DIR/workflow-state-${RUN_ID2}.json"
bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "test" --route "formal" >/dev/null

run_test "formal init defers via pending_plan_count" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$SF2') == 'pending_plan_count' ]]"
run_test "reinitialize from pending_plan_count errors (exit≠0)" \
  bash -c "! bash '$STATE_SH' budget reinitialize --run-id '$RUN_ID2' --plan-count 2"
run_test "failed reinitialize leaves route unchanged (still formal, not flipped)" \
  bash -c "[[ \$(jq -r '.route' '$SF2') == 'formal' && \$(jq -r '.budget.budget_status' '$SF2') == 'pending_plan_count' ]]"

# --- Entry guard: reinitialize from already-initialized must also error ---
run_test "reinitialize from already-initialized errors (exit≠0)" \
  bash -c "! bash '$STATE_SH' budget reinitialize --run-id '$RUN_ID' --plan-count 3"

# --- Missing --plan-count errors ---
RUN_ID3="test-reinit-noarg"
bash "$STATE_SH" init --run-id "$RUN_ID3" --slug "test" --route "light" >/dev/null
run_test "reinitialize without --plan-count errors (exit≠0)" \
  bash -c "! bash '$STATE_SH' budget reinitialize --run-id '$RUN_ID3'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
