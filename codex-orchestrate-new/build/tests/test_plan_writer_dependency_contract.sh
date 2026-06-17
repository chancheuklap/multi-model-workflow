#!/usr/bin/env bash
# Regression contract for plan-writing churn seen in real Codex threads:
# direct cross-issue dependencies and HITL/conditional decisions must be locked
# before plan writers run, and semantic repairs must return to the original
# plan_writer instead of being hand-edited by the Coordinator.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

ISSUE_SPLIT="$PLUGIN_DIR/skills/orchestrate-discovery/references/issue-splitting.md"
PLAN_DISPATCH="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md"
PLAN_METHOD="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-writing-methodology.md"
PLAN_GATES="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-gates.md"
PLAN_REPAIR="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"
PLAN_PRE="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-preconditions.md"
PLAN_WRITER="$PLUGIN_DIR/agents/plan_writer.toml"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_plan_writer_dependency_contract.sh ==="

run_test "issue splitting requires direct dependencies for conditional/HITL slices" bash -c \
  "grep -q 'Blocked by.*直接依赖' '$ISSUE_SPLIT' && grep -q '条件项 / HITL slice 必须同时列出决策门和它直接消费的 producer slice' '$ISSUE_SPLIT'"

run_test "plan writer dispatch keeps dependency facts in issue hierarchy, not a new index" bash -c \
  "grep -q '不新增派发索引或中间文档' '$PLAN_DISPATCH' && ! grep -q 'Large issue index' '$PLAN_DISPATCH' && ! grep -q 'Large issue index' '$PLAN_METHOD'"

run_test "plan writer methodology returns NEEDS_ISSUES for missing direct producer dependency" bash -c \
  "grep -q '当前 issue 缺直接 producer / decision 依赖' '$PLAN_METHOD' && grep -q 'NEEDS_ISSUES' '$PLAN_METHOD'"

run_test "plan writer self-check rejects hidden transitive dependencies and automatic thresholds" bash -c \
  "grep -q '直接 producer 依赖藏成传递依赖' '$PLAN_WRITER' && grep -q '未 review 的阈值写成自动通过' '$PLAN_WRITER'"

run_test "plan gates cannot introduce new dependency semantics at Cross-Plan anchor time" bash -c \
  "grep -q '不得在 Step 12b 首次引入新的 plan dependency' '$PLAN_GATES' && grep -q '不由 Coordinator 手工补多份 plan 正文' '$PLAN_GATES'"

run_test "plan repair sends semantic changes back to original plan_writer" bash -c \
  "grep -q '不手工重写 plan body 来代替原 plan_writer' '$PLAN_REPAIR' && grep -q 'send_input 受影响的原 plan_writer' '$PLAN_REPAIR'"

run_test "plan revision preconditions reserve direct Coordinator edits for non-semantic formatting" bash -c \
  "grep -q '只需修改非语义格式' '$PLAN_PRE' && grep -q 'plan header 的语义字段' '$PLAN_PRE'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
