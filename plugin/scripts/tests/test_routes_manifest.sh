#!/usr/bin/env bash
# Tests routes-v1.json declarative flow-shape manifest (P1):
#   - 清单与 meta-schema 可被 jq 解析
#   - 每个 workflow-state route enum 值都有对应 route 记录（enum↔manifest 一致性）
#   - 每条 route 记录字段完整、budget.init 合法
#   - 行为等价锚点：global_transitions ∪ formal.phase_transitions 覆盖旧 TRANSITION_MATRIX
#     的全部 Coordinator phase 推进（保证 P2 改读清单后 formal 行为不回归）
#   - light 子形态预置且不含 workflow:discovery（机器拦轻档误跳的数据前提）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCHEMA_DIR="$SCRIPT_DIR/../../state-schema"
ROUTES="$SCHEMA_DIR/routes-v1.json"
ROUTES_SCHEMA="$SCHEMA_DIR/routes-v1.schema.json"
WF_SCHEMA="$SCHEMA_DIR/workflow-state-v1.json"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_routes_manifest.sh ==="

# --- 解析性 ---
run_test "routes-v1.json parses with jq" jq -e . "$ROUTES"
run_test "routes-v1.schema.json parses with jq" jq -e . "$ROUTES_SCHEMA"
run_test "schema_version == 1" bash -c "[[ \$(jq -r '.schema_version' '$ROUTES') == '1' ]]"
run_test "global_transitions is non-empty array" bash -c "[[ \$(jq -r '.global_transitions | type' '$ROUTES') == 'array' && \$(jq '.global_transitions | length' '$ROUTES') -gt 0 ]]"

# --- enum ↔ manifest 一致性：每个 route enum 值有记录 ---
ENUM_ROUTES=$(jq -r '.properties.route.enum[]' "$WF_SCHEMA")
for r in $ENUM_ROUTES; do
  run_test "enum route '$r' has manifest record" \
    bash -c "jq -e --arg r '$r' '.routes[\$r]' '$ROUTES'"
done

# --- light 子形态预置（P3 接 hook，P1 仅备数据）---
run_test "light sub-form pre-placed" bash -c "jq -e '.routes.light' '$ROUTES'"
run_test "light has no workflow:discovery transition (机器拦误跳前提)" \
  bash -c "! jq -e '.routes.light.phase_transitions | index(\"Coordinator:workflow:discovery\")' '$ROUTES'"
run_test "light exempts discovery+plan-review gates" \
  bash -c "[[ \$(jq -r '.routes.light.gate_exemptions | sort | join(\",\")' '$ROUTES') == 'discovery,plan-review' ]]"

# --- 每条 route 记录字段完整 + budget.init 合法 ---
for r in $(jq -r '.routes | keys[]' "$ROUTES"); do
  run_test "route '$r' has all required fields" \
    bash -c "jq -e --arg r '$r' '.routes[\$r] | has(\"phases\") and has(\"phase_transitions\") and has(\"gate_exemptions\") and has(\"dispatch_shape\") and has(\"budget\") and has(\"commit_format\")' '$ROUTES'"
  run_test "route '$r' budget.init valid" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r].budget.init' '$ROUTES') =~ ^(pending_plan_count|unlimited)\$ ]]"
done

# --- budget 一致性：unlimited-init routes vs formal/light pending_plan_count ---
run_test "formal budget.init == pending_plan_count" \
  bash -c "[[ \$(jq -r '.routes.formal.budget.init' '$ROUTES') == 'pending_plan_count' ]]"
for r in direct-repair multi-pr-merge bug-investigation; do
  run_test "$r budget.init == unlimited" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r].budget.init' '$ROUTES') == 'unlimited' ]]"
done

# --- 行为等价锚点：旧 TRANSITION_MATRIX 的全部 Coordinator phase 推进
#     必须能在 global_transitions ∪ formal.phase_transitions 找到（P2 不回归 formal）---
OLD_FORMAL_PHASE_TRANSITIONS=(
  "Coordinator:workflow:discovery"
  "Coordinator:workflow:plan-writing"
  "Coordinator:workflow:execution"
  "Coordinator:workflow:final-review"
  "Coordinator:discovery:plan-writing"
  "Coordinator:plan-writing:execution"
  "Coordinator:execution:final-review"
  "Coordinator:final-review:closed"
)
UNION=$(jq -r '(.global_transitions + .routes.formal.phase_transitions)[]' "$ROUTES")
for t in "${OLD_FORMAL_PHASE_TRANSITIONS[@]}"; do
  run_test "formal covers old transition '$t'" \
    bash -c "echo '$UNION' | grep -qx '$t'"
done

# --- 旧 work-item 状态机转换必须在 global_transitions（route 无关）---
OLD_WORK_ITEM=(
  "Coordinator:pending:dispatched"
  "Coordinator:pending:in_progress"
  "Coordinator:dispatched:returned"
  "Coordinator:returned:committed"
  "Coordinator:returned:review_pending"
  "Coordinator:review_pending:pass"
  "Coordinator:review_pending:needs_repair"
  "Coordinator:returned:repairing"
  "Coordinator:repairing:returned"
  "agent-return-handler:dispatched:returned"
  "agent-return-handler:in_progress:returned"
  "track-execution-state:returned:committed"
)
GLOBALS=$(jq -r '.global_transitions[]' "$ROUTES")
for t in "${OLD_WORK_ITEM[@]}"; do
  run_test "global_transitions has work-item '$t'" \
    bash -c "echo '$GLOBALS' | grep -qx '$t'"
done

# --- repair_policy 断言（P5d-1：三套修复截断统一为 routes 参数）---
# formal / light 必须有 repair_policy；各 phase 取值与现状等价
for r in formal light; do
  run_test "route '$r' has repair_policy" \
    bash -c "jq -e --arg r '$r' '.routes[\$r].repair_policy != null' '$ROUTES'"
  run_test "route '$r' repair_policy.execution.max_repair_rounds == 2" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r].repair_policy.execution.max_repair_rounds' '$ROUTES') == '2' ]]"
  run_test "route '$r' repair_policy.execution.escalate_to_rca == true" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r].repair_policy.execution.escalate_to_rca' '$ROUTES') == 'true' ]]"
  run_test "route '$r' repair_policy.final-review.max_repair_rounds == 1" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r][\"repair_policy\"][\"final-review\"].max_repair_rounds' '$ROUTES') == '1' ]]"
  run_test "route '$r' repair_policy.final-review.escalate_to_rca == true" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r][\"repair_policy\"][\"final-review\"].escalate_to_rca' '$ROUTES') == 'true' ]]"
  run_test "route '$r' repair_policy.plan-review.max_repair_rounds == 2" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r][\"repair_policy\"][\"plan-review\"].max_repair_rounds' '$ROUTES') == '2' ]]"
  run_test "route '$r' repair_policy.plan-review.escalate_to_rca == false" \
    bash -c "[[ \$(jq -r --arg r '$r' '.routes[\$r][\"repair_policy\"][\"plan-review\"].escalate_to_rca' '$ROUTES') == 'false' ]]"
done

# --- 无历史注释泄漏（JSON 天然无注释，防有人塞进字符串）---
run_test "no Pack 2.14 / Plan 005 history leaked into manifest" \
  bash -c "! grep -qE 'Pack 2\\.14|Plan 005' '$ROUTES'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
