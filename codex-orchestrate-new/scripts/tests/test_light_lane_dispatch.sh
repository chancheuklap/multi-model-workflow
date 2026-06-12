#!/usr/bin/env bash
# Tests Light Lane dispatch/transition behavior (P3):
#   - init --route light → budget_status=unlimited
#     (D-B 数据前提：light 跳过 validate-plan-dispatch.sh 的 budget-init 门，因
#      budget_status=unlimited ≠ pending_plan_count)
#   - transition workflow→execution 对 light 允许（routes 清单声明，直派 Worker）
#   - transition workflow→discovery 对 light 拒绝（清单无此跳，机器拦轻档误跳）
#   - 对照：formal 的 workflow→discovery 允许、workflow→execution 也允许
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_light_lane_dispatch.sh ==="

# --- D-B 数据前提：light init → unlimited（跳过 budget-init 门）---
RUN_ID="test-light-lane"
SF="$FIXTURE_DIR/workflow-state-${RUN_ID}.json"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "light" >/dev/null

run_test "light init budget_status == unlimited (skips budget-init gate)" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$SF') == 'unlimited' ]]"
run_test "light init review_total == unlimited" \
  bash -c "[[ \$(jq -r '.budget.review_total' '$SF') == 'unlimited' ]]"
run_test "light init cursor.phase == workflow" \
  bash -c "[[ \$(jq -r '.cursor.phase' '$SF') == 'workflow' ]]"

# --- transition workflow→execution 对 light 允许（cursor 已在 workflow）---
run_test "light: transition workflow→execution allowed" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor Coordinator --from workflow --to execution

run_test "light: cursor.phase now execution" \
  bash -c "[[ \$(jq -r '.cursor.phase' '$SF') == 'execution' ]]"

# --- transition workflow→discovery 对 light 拒绝（fresh light run）---
RUN_ID2="test-light-deny"
bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "test" --route "light" >/dev/null
run_test "light: transition workflow→discovery DENIED (exit≠0)" \
  bash -c "! bash '$STATE_SH' transition --run-id '$RUN_ID2' --actor Coordinator --from workflow --to discovery"

# --- 对照组 formal：workflow→discovery 允许、workflow→execution 允许 ---
RUN_ID3="test-formal-ctrl"
bash "$STATE_SH" init --run-id "$RUN_ID3" --slug "test" --route "formal" >/dev/null
run_test "formal: transition workflow→discovery allowed" \
  bash "$STATE_SH" transition --run-id "$RUN_ID3" --actor Coordinator --from workflow --to discovery

RUN_ID4="test-formal-exec"
bash "$STATE_SH" init --run-id "$RUN_ID4" --slug "test" --route "formal" >/dev/null
run_test "formal: transition workflow→execution allowed" \
  bash "$STATE_SH" transition --run-id "$RUN_ID4" --actor Coordinator --from workflow --to execution

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
