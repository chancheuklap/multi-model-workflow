#!/usr/bin/env bash
# Plan 005 Pack 5.8: validate-plan-dispatch.sh tests.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/validate-plan-dispatch.sh"

WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

BUDGET_DIR=".codex/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="vpd-test"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","attendance_mode":"afk","budget":{"budget_status":"initialized","review_total":24,"review_used":0,"review_credit":0,"budget_profile":"standard","override_count":0,"direction_check_count":0},"pending_direction_check":null,"idempotency_keys":[],"review_dispositions":[]}
EOF

cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"packs":{"5.1":{"status":"pending"}}}}}
EOF

# Plan doc
mkdir -p docs/orchestrate/plans/test
cat > docs/orchestrate/plans/test/005-foo.md <<'EOF'
# Plan 005

## Pack Execution Manifest

| pack_id | title |
| --- | --- |
| 5.1 | foo |
EOF

pass=0
fail=0

make_input() {
  local envelope="$1"
  local prompt="<!-- DISPATCH_ENVELOPE $envelope -->\nrun"
  jq -n --arg p "$(printf '%b' "$prompt")" \
    '{tool_input:{agent_type:"pack_executor",prompt:$p}}'
}

run_pass() {
  local name="$1" envelope="$2"
  local input
  input=$(make_input "$envelope")
  if echo "$input" | bash "$HOOK" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected pass)"
    fail=$((fail + 1))
  fi
}

run_block() {
  local name="$1" envelope="$2"
  local input
  input=$(make_input "$envelope")
  if ! echo "$input" | bash "$HOOK" >/dev/null 2>&1; then
    echo "  PASS: $name (correctly blocked)"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected block)"
    fail=$((fail + 1))
  fi
}

echo "=== test_validate_plan_dispatch.sh ==="

# Old hook is deleted
if [[ ! -e "$(cd "$SCRIPT_DIR/.." && pwd)/validate-pack-dispatch.sh" ]]; then
  echo "  PASS: validate-pack-dispatch.sh is removed"
  pass=$((pass + 1))
else
  echo "  FAIL: validate-pack-dispatch.sh still exists"
  fail=$((fail + 1))
fi

# Test 1: valid plan-level envelope passes
ENV=$(jq -nc --arg pp "docs/orchestrate/plans/test/005-foo.md" \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k1",plan_id:"005",pack_id:null,plan_path:$pp}')
run_pass "valid plan-level envelope" "$ENV"

# Test 2: missing plan_path → block
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k2",plan_id:"005",pack_id:null,plan_path:null}')
run_block "missing plan_path" "$ENV"

# Test 3: plan_path does not exist → block
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k3",plan_id:"005",pack_id:null,plan_path:"docs/nonexistent.md"}')
run_block "plan_path does not exist" "$ENV"

# Test 4: plan.md missing Pack Execution Manifest → WARN (D9 降级, no longer blocks)
mkdir -p docs/orchestrate/plans/empty
echo "# Empty plan" > docs/orchestrate/plans/empty/001-bad.md
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k4",plan_id:"005",pack_id:null,plan_path:"docs/orchestrate/plans/empty/001-bad.md"}')
run_pass "plan.md missing Pack Execution Manifest (WARN not block)" "$ENV"

# Test 5: unknown plan_id in execution-state → block
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k5",plan_id:"999",pack_id:null,plan_path:"docs/orchestrate/plans/test/005-foo.md"}')
run_block "unknown plan_id in execution-state" "$ENV"

# Test 6: duplicate idempotency_key → block
# First, append k1 to idempotency_keys
jq '.idempotency_keys = ["dup-k"]' "$BUDGET_DIR/workflow-state-${RUN_ID}.json" \
  > "$BUDGET_DIR/workflow-state-${RUN_ID}.json.tmp" && \
  mv "$BUDGET_DIR/workflow-state-${RUN_ID}.json.tmp" "$BUDGET_DIR/workflow-state-${RUN_ID}.json"
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"dup-k",plan_id:"005",pack_id:null,plan_path:"docs/orchestrate/plans/test/005-foo.md"}')
run_block "duplicate idempotency_key" "$ENV"
# Clean idempotency_keys back
jq '.idempotency_keys = []' "$BUDGET_DIR/workflow-state-${RUN_ID}.json" \
  > "$BUDGET_DIR/workflow-state-${RUN_ID}.json.tmp" && \
  mv "$BUDGET_DIR/workflow-state-${RUN_ID}.json.tmp" "$BUDGET_DIR/workflow-state-${RUN_ID}.json"

# Test 7: pack-level execution envelope is now BLOCKED (legacy path removed)
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k7",pack_id:"5.1",plan_id:null}')
run_block "pack-level execution envelope rejected (plan-level only)" "$ENV"

# Test 8: execution envelope carrying BOTH plan_id and pack_id → block (must leave pack_id null)
ENV=$(jq -nc --arg pp "docs/orchestrate/plans/test/005-foo.md" \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k8",plan_id:"005",pack_id:"5.1",plan_path:$pp}')
run_block "execution envelope with non-null pack_id rejected" "$ENV"

# Test 9: non-execution route-worker envelope (plan_id + pack_id both null) passes the gate
ENV=$(jq -nc \
  '{protocol_version:"1",run_id:"vpd-test",phase:"bug-investigation",agent_role:"pack_executor",repair_round:0,idempotency_key:"k9",pack_id:null,plan_id:null}')
run_pass "non-execution route-worker envelope (both null) passes" "$ENV"

# Test 10: unknown plan-level execution agent_role is blocked
ENV=$(jq -nc --arg pp "docs/orchestrate/plans/test/005-foo.md" \
  '{protocol_version:"1",run_id:"vpd-test",phase:"execution",agent_role:"plan-executor",repair_round:0,idempotency_key:"k10",plan_id:"005",pack_id:null,plan_path:$pp}')
run_block "unknown execution agent_role rejected" "$ENV"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
