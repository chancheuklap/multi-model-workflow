#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DISPATCH_SH="$SCRIPT_DIR/../dispatch-review.sh"
STATE_SH="$SCRIPT_DIR/../state.sh"
HOOK="$SCRIPT_DIR/../../hooks/gate-codex-review.sh"

pass=0
fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"; pass=$((pass + 1))
  else
    echo "  FAIL: $name"; fail=$((fail + 1))
  fi
}
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure)"; fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"; pass=$((pass + 1))
  fi
}

echo "=== test_review_dispatch_gates.sh ==="

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR/.codex/multi-model-workflow"
mkdir -p "$STATE_BASE" "$FIXTURE_DIR/prompts"

RUN_ID="review-gates"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "$RUN_ID" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 1 >/dev/null

run_test "gate-codex-review hook does not infer native subagent prompts from Bash" \
  bash -c "echo '{\"tool_input\":{\"command\":\"node spawn_agent(agent_type=codex_reviewer) --prompt-file /nonexistent\"}}' | bash '$HOOK'"

run_test_expect_fail "validate blocks missing prompt file" \
  bash "$DISPATCH_SH" validate --prompt-file "$FIXTURE_DIR/prompts/missing.md" --gate "missing"

TARGETED="$FIXTURE_DIR/prompts/targeted.md"
cat > "$TARGETED" <<PROMPT
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"$RUN_ID","phase":"execution","agent_role":"codex_reviewer","agent_id":null,"pack_id":null,"plan_id":null,"repair_round":0,"idempotency_key":"$RUN_ID/review/r0","disposition_refs":null,"review_intent":"targeted-re-review","exception_code":"user_requested"} -->
Review prompt content
PROMPT

run_test_expect_fail "validate blocks removed targeted-re-review intent" \
  bash "$DISPATCH_SH" validate --prompt-file "$TARGETED" --gate "targeted"

BASELINE="$FIXTURE_DIR/prompts/plan-impl-review-1.md"
cat > "$BASELINE" <<PROMPT
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"$RUN_ID","phase":"execution","agent_role":"codex_reviewer","agent_id":null,"pack_id":null,"plan_id":null,"repair_round":0,"idempotency_key":"$RUN_ID/review/r0","disposition_refs":null,"review_intent":"baseline","exception_code":null} -->
Review prompt content
PROMPT

cat > "$STATE_BASE/execution-state-$RUN_ID.json" <<JSON
{
  "plans": {
    "001": {
      "start_commit": "abc123",
      "packs": {
        "1.1": { "status": "pending", "commit_sha": null }
      }
    }
  }
}
JSON

run_test_expect_fail "validate blocks plan implementation review with uncommitted packs" \
  bash "$DISPATCH_SH" validate --prompt-file "$BASELINE" --gate "plan-impl-review-1"

jq '.plans["001"].packs["1.1"].status = "committed" | .plans["001"].packs["1.1"].commit_sha = "def456"' \
  "$STATE_BASE/execution-state-$RUN_ID.json" > "$STATE_BASE/execution-state-$RUN_ID.tmp"
mv "$STATE_BASE/execution-state-$RUN_ID.tmp" "$STATE_BASE/execution-state-$RUN_ID.json"

run_test "validate passes plan implementation review after packs are committed" \
  bash "$DISPATCH_SH" validate --prompt-file "$BASELINE" --gate "plan-impl-review-1"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
