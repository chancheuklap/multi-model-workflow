#!/usr/bin/env bash
# Tests validate-plan-dispatch.sh plan-level worker re-dispatch guard.
# Execution is plan-level only: a Plan already in_progress with a worker_agent_id
# cannot be re-dispatched via subagent() — repair must use send_input to resume the
# plan worker. A fresh Plan (no worker_agent_id) is allowed.
#
# Fixture strategy: the hook uses hardcoded BUDGET_DIR=".codex/multi-model-workflow",
# so we create a temp workspace, set up the state + plan files there, and cd into it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../validate-plan-dispatch.sh"

WORKSPACE=$(mktemp -d)
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

BUDGET_DIR=".codex/multi-model-workflow"
mkdir -p "$BUDGET_DIR"

pass=0; fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass+1))
  else
    echo "  FAIL: $name"
    fail=$((fail+1))
  fi
}
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure)"
    fail=$((fail+1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass+1))
  fi
}

echo "=== test_agent_id_hook_guard.sh ==="

RUN_ID="test-guard"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

# workflow-state with initialized budget
cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<'EOF'
{
  "run_id": "test-guard",
  "attendance_mode": "afk",
  "budget": {"budget_status": "initialized", "review_total": 18, "review_used": 0, "review_credit": 0, "budget_profile": "standard", "override_count": 0, "direction_check_count": 0},
  "pending_direction_check": null,
  "idempotency_keys": [],
  "review_dispositions": []
}
EOF

# execution-state: plan 001 already in_progress with a worker; plan 002 is fresh
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<'EOF'
{
  "run_id": "test-guard",
  "plans": {
    "001": {"status": "in_progress", "worker_agent_id": "agent-abc-123", "packs": {"1.1": {"status": "committed"}}},
    "002": {"status": "pending", "worker_agent_id": null, "packs": {"2.1": {"status": "pending"}}}
  }
}
EOF

# Plan docs (Step 6 requires plan_path to resolve)
mkdir -p docs/orchestrate/plans/test
cat > docs/orchestrate/plans/test/001-foo.md <<'EOF'
# Plan 001

## Pack Execution Manifest

| pack_id | title |
| --- | --- |
| 1.1 | foo |
EOF
cat > docs/orchestrate/plans/test/002-bar.md <<'EOF'
# Plan 002

## Pack Execution Manifest

| pack_id | title |
| --- | --- |
| 2.1 | bar |
EOF

make_input() {
  local envelope="$1"
  local prompt="<!-- DISPATCH_ENVELOPE $envelope -->\nrun"
  jq -n --arg p "$(printf '%b' "$prompt")" \
    '{tool_input:{agent_type:"pack_executor",prompt:$p}}'
}

# Plan 001 (already in_progress with worker_agent_id) → re-dispatch BLOCKED
ENV_BLOCKED=$(jq -nc --arg pp "docs/orchestrate/plans/test/001-foo.md" \
  '{protocol_version:"1",run_id:"test-guard",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k-blocked",plan_id:"001",pack_id:null,plan_path:$pp}')
INPUT_BLOCKED=$(make_input "$ENV_BLOCKED")

# Plan 002 (fresh, no worker) → ALLOWED
ENV_ALLOWED=$(jq -nc --arg pp "docs/orchestrate/plans/test/002-bar.md" \
  '{protocol_version:"1",run_id:"test-guard",phase:"execution",agent_role:"pack_executor",repair_round:0,idempotency_key:"k-allowed",plan_id:"002",pack_id:null,plan_path:$pp}')
INPUT_ALLOWED=$(make_input "$ENV_ALLOWED")

# Test 1: Plan 001 (in_progress with worker) re-dispatch is BLOCKED
run_test_expect_fail "hook blocks re-dispatch of plan in_progress with worker" \
  bash -c "echo '$INPUT_BLOCKED' | bash '$HOOK'"

# Test 2: Plan 002 (fresh) is ALLOWED
run_test "hook allows dispatch of fresh plan without worker" \
  bash -c "echo '$INPUT_ALLOWED' | bash '$HOOK'"

# Test 3: BLOCKED message references the plan-level guard (in_progress / send_input)
run_test "block message references in_progress worker / send_input" \
  bash -c "STDERR=\$(echo '$INPUT_BLOCKED' | bash '$HOOK' 2>&1 >/dev/null || true); echo \"\$STDERR\" | grep -qE 'already in_progress with worker|send_input'"

# Test 4: blocked dispatch did NOT append idempotency key
run_test "blocked dispatch did not append idempotency key" \
  bash -c "! jq -e '.idempotency_keys | index(\"k-blocked\")' '$BUDGET_DIR/workflow-state-${RUN_ID}.json' >/dev/null 2>&1"

# Test 5: allowed dispatch appended idempotency key
run_test "allowed dispatch appended idempotency key" \
  bash -c "jq -e '.idempotency_keys | index(\"k-allowed\") != null' '$BUDGET_DIR/workflow-state-${RUN_ID}.json' >/dev/null 2>&1"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
