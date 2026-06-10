#!/usr/bin/env bash
# A1: state.sh verdict-route — workflow-level verdict 机械路由查询。
#   - 每张表的机械 verdict 解析到正确动作/目标
#   - 判断类 verdict 标记 judgment=true（不被误僵化，数据只给候选）
#   - reflux-counter：execution_reflux_count 0→goto execution 并递增；≥1→report-user
#   - fail-open：未知 verdict / phase → exit 0 输出 no-data
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_verdict_route.sh ==="

RUN_ID="test-vr"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "vr" --route "formal" >/dev/null

# --- 机械跳转 ---
run_test "discovery DISCOVERY_READY → goto plan-writing" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase discovery --verdict DISCOVERY_READY | jq -r '.action + \"/\" + .target') == 'goto/plan-writing' ]]"
run_test "plan-writing PLAN_CREATED → goto execution" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase plan-writing --verdict PLAN_CREATED | jq -r '.action + \"/\" + .target') == 'goto/execution' ]]"
run_test "execution EXECUTION_PASSED → goto final-review" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase execution --verdict EXECUTION_PASSED | jq -r '.action + \"/\" + .target') == 'goto/final-review' ]]"
run_test "final-review FINAL_REVIEW_PASSED → goto closing" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase final-review --verdict FINAL_REVIEW_PASSED | jq -r '.action + \"/\" + .target') == 'goto/closing' ]]"
run_test "multi-pr-merge MERGE_COMPLETE → goto closing" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase multi-pr-merge --verdict MERGE_COMPLETE | jq -r '.action + \"/\" + .target') == 'goto/closing' ]]"
run_test "direct-repair pass → goto closing" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase direct-repair --verdict pass | jq -r '.action + \"/\" + .target') == 'goto/closing' ]]"
run_test "plan-writing NEEDS_TRIAGE → invoke-skill triage" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase plan-writing --verdict NEEDS_TRIAGE | jq -r '.action + \"/\" + .target') == 'invoke-skill/triage' ]]"

# --- 判断类分支不被僵化：judgment=true 且 action 非 goto ---
for pv in "plan-writing NEEDS_ISSUES" "plan-writing NEEDS_CONTEXT" "execution NEEDS_ARCHITECTURE" "direct-repair:needs repair"; do
  phase="${pv%% *}"; verdict="${pv#* }"
  if [[ "$pv" == "direct-repair:needs repair" ]]; then phase="direct-repair"; verdict="needs repair"; fi
  run_test "$phase '$verdict' marked judgment=true" \
    bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase '$phase' --verdict '$verdict' | jq -r '.judgment') == 'true' ]]"
done
run_test "BLOCKED is report-user with judgment=true (措辞留散文)" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase execution --verdict BLOCKED | jq -r '.action + \"/\" + (.judgment|tostring)') == 'report-user/true' ]]"

# --- reflux-counter 完全下沉 ---
run_test "NEEDS_EXECUTION first time → goto execution, count 0→1" \
  bash -c "out=\$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase final-review --verdict NEEDS_EXECUTION); \
    [[ \$(echo \"\$out\" | jq -r '.action') == 'goto' ]] && \
    [[ \$(echo \"\$out\" | jq -r '.reflux_count') == '1' ]] && \
    [[ \$(jq -r '.execution_reflux_count' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == '1' ]]"
run_test "NEEDS_EXECUTION second time → report-user (cap reached)" \
  bash -c "[[ \$(bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase final-review --verdict NEEDS_EXECUTION | jq -r '.action') == 'report-user' ]]"

# --- fail-open ---
run_test "unknown verdict → exit 0 with no-data message" \
  bash -c "bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase execution --verdict NO_SUCH_VERDICT | grep -q 'no-data'"
run_test "unknown phase → exit 0 with no-data message" \
  bash -c "bash '$STATE_SH' verdict-route --run-id '$RUN_ID' --phase nonsense --verdict BLOCKED | grep -q 'no-data'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
