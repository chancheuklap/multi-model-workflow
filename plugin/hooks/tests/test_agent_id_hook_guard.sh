#!/usr/bin/env bash
# Tests validate-pack-dispatch.sh agent_id existence guard (Step 8).
# Per Ruling 2 + A7: if a pack already has agent_id in execution-state,
# re-dispatch via Agent() is BLOCKED — repair must use SendMessage to resume.
#
# Fixture strategy: the hook uses hardcoded BUDGET_DIR=".claude/multi-model-workflow",
# so we create a temp workspace, set up the state files there, and cd into it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../validate-plan-dispatch.sh"

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

# Create workflow-state with initialized budget
cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<'EOF'
{
  "run_id": "test-guard",
  "slug": "test",
  "route": "formal",
  "started_at": "2025-01-01T00:00:00Z",
  "cursor": {"phase": "execution", "reference": null, "step": null},
  "budget": {"budget_status": "initialized", "review_total": 18, "review_used": 0, "effort_total": 36, "effort_used": 0, "direction_check_count": 0},
  "plan_count": 2,
  "plans": [],
  "idempotency_keys": [],
  "plan_writer_agent_id": null,
  "review_dispositions": [],
  "pending_post_push_reviews": [],

  "self_verifications": [],
  "pending_direction_check": null,
  "execution_reflux_count": 0,
  "last_gate_phase": null,
  "last_gate_timestamp": null
}
EOF

# Create execution-state: pack 1.1 has agent_id, pack 1.2 does not
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<'EOF'
{
  "run_id": "test-guard",
  "plans": {
    "001": {
      "packs": {
        "1.1": {"status": "returned", "agent_id": "agent-abc-123", "commit_sha": "abc123", "worker_verdict": "pass", "repair_round": 0},
        "1.2": {"status": "pending", "agent_id": null, "commit_sha": null, "worker_verdict": null, "repair_round": 0}
      }
    }
  }
}
EOF

# Build properly escaped JSON input for the hook using jq
# Pack 1.1 (has agent_id -> should be BLOCKED)
PROMPT_BLOCKED='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test-guard","phase":"execution","agent_role":"pack-executor","pack_id":"1.1","repair_round":0,"idempotency_key":"test-key-blocked","disposition_refs":[],"review_intent":null,"exception_code":null} -->
Do the work for pack 1.1'

INPUT_BLOCKED=$(jq -n --arg p "$PROMPT_BLOCKED" '{"tool_input":{"prompt":$p}}')

# Pack 1.2 (no agent_id -> should be ALLOWED)
PROMPT_ALLOWED='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test-guard","phase":"execution","agent_role":"pack-executor","pack_id":"1.2","repair_round":0,"idempotency_key":"test-key-allowed","disposition_refs":[],"review_intent":null,"exception_code":null} -->
Do the work for pack 1.2'

INPUT_ALLOWED=$(jq -n --arg p "$PROMPT_ALLOWED" '{"tool_input":{"prompt":$p}}')

# Test 1: Pack 1.1 (has agent_id) should be BLOCKED by the hook
run_test_expect_fail "hook blocks dispatch to pack with existing agent_id" \
  bash -c "cd '$WORKSPACE' && echo '$INPUT_BLOCKED' | bash '$HOOK'"

# Test 2: Pack 1.2 (no agent_id) should PASS the hook
run_test "hook allows dispatch to pack without agent_id" \
  bash -c "cd '$WORKSPACE' && echo '$INPUT_ALLOWED' | bash '$HOOK'"

# Test 3: Verify the BLOCKED message mentions the blocking reason (Step 7 pack status or Step 8 agent_id)
run_test "block message references pack status or SendMessage" \
  bash -c "cd '$WORKSPACE' && STDERR=\$(echo '$INPUT_BLOCKED' | bash '$HOOK' 2>&1 >/dev/null || true); echo \"\$STDERR\" | grep -qE 'SendMessage|Cannot re-dispatch'"

# Test 4: Verify idempotency was NOT appended for the blocked dispatch
run_test "blocked dispatch did not append idempotency key" \
  bash -c "! jq -e '.idempotency_keys | index(\"test-key-blocked\")' '$BUDGET_DIR/workflow-state-${RUN_ID}.json' >/dev/null 2>&1"

# Test 5: Verify idempotency WAS appended for the allowed dispatch
run_test "allowed dispatch appended idempotency key" \
  bash -c "jq -e '.idempotency_keys | index(\"test-key-allowed\") != null' '$BUDGET_DIR/workflow-state-${RUN_ID}.json' >/dev/null 2>&1"

# Test 6: Pack 1.2 status should now be "dispatched" in execution-state
run_test "allowed dispatch updated pack status to dispatched" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].packs[\"1.2\"].status' '$BUDGET_DIR/execution-state-${RUN_ID}.json') == 'dispatched' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
