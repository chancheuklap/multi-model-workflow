#!/usr/bin/env bash
# Tests track-effort-budget.sh agent-role weighted effort increments.
# worker (pack-executor) = 1, explorer (code-explorer) = 1, RCA (root-cause-analyst) = 2, other = 0
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../track-effort-budget.sh"

WORKSPACE=$(mktemp -d)
trap 'rm -rf "$WORKSPACE"' EXIT

BUDGET_DIR="$WORKSPACE/.claude/multi-model-workflow"
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

echo "=== test_effort_budget_weighting.sh ==="

RUN_ID="test-effort"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

# Create workflow-state with initialized budget
cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<'EOF'
{
  "run_id": "test-effort",
  "slug": "test",
  "route": "formal",
  "started_at": "2025-01-01T00:00:00Z",
  "current_phase": "execution",
  "cursor": {"phase": "execution"},
  "budget": {"budget_status": "initialized", "review_total": 24, "review_used": 0, "effort_total": 48, "effort_used": 0, "direction_check_count": 0},
  "plan_count": 4,
  "plans": [],
  "idempotency_keys": [],
  "plan_writer_agent_id": null,
  "review_dispositions": [],
  "review_effectiveness": {"reject_count":0,"suppress_count":0,"path_a_count":0,"path_b_count":0,"total_findings":0,"last_aggregated_at":null},
  "pending_post_push_reviews": [],
  "path_a_escalation": [],
  "self_verifications": [],
  "pending_direction_check": null,
  "execution_reflux_count": 0,
  "last_gate_phase": null,
  "last_gate_timestamp": null,
  "mutations": []
}
EOF

SF="$BUDGET_DIR/workflow-state-${RUN_ID}.json"

# Helper: build hook input JSON
make_input() {
  local cmd="$1"
  jq -n --arg c "$cmd" '{"tool_input":{"command":$c},"tool_response":{"exit_code":0}}'
}

# Test 1: plain Bash (ls) should NOT increment effort
run_test "plain bash does not increment effort" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "ls -la")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 0 ]]"

# Test 2: worker dispatch (pack-executor) should increment by 1
run_test "worker dispatch increments by 1" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "claude agent pack-executor --task foo")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 1 ]]"

# Test 3: explorer dispatch (code-explorer) should increment by 1
run_test "explorer dispatch increments by 1" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "claude agent code-explorer --analyze")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 2 ]]"

# Test 4: RCA dispatch (root-cause-analyst) should increment by 2
run_test "RCA dispatch increments by 2" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "claude agent root-cause-analyst --investigate")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 4 ]]"

# Test 5: complex-pack-executor should increment by 1
run_test "complex-pack-executor increments by 1" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "claude agent complex-pack-executor --task bar")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 5 ]]"

# Test 6: complex-code-explorer should increment by 1
run_test "complex-code-explorer increments by 1" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "claude agent complex-code-explorer --scan")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 6 ]]"

# Test 7: another plain bash (git status) should NOT increment
run_test "git status does not increment effort" \
  bash -c "cd '$WORKSPACE' && echo '$(make_input "git status")' | bash '$HOOK' && [[ \$(jq '.budget.effort_used' '$SF') -eq 6 ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
