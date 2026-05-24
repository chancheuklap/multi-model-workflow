#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../gate-codex-review.sh"

pass=0
fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

make_input() {
  local agent_type="$1"
  local prompt="$2"
  jq -n --arg t "$agent_type" --arg p "$prompt" \
    '{"hook_event_name":"SubagentStart","agent_type":$t,"prompt":$p}'
}

echo "=== test_gate_codex_review.sh ==="

BASELINE_PROMPT='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test","phase":"execution","agent_role":"codex_reviewer","agent_id":null,"pack_id":null,"repair_round":0,"idempotency_key":"test/review/r0","disposition_refs":null,"review_intent":"baseline","exception_code":null} -->
Review prompt content'

TARGETED_PROMPT='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test","phase":"execution","agent_role":"codex_reviewer","agent_id":"reviewer-1","pack_id":null,"repair_round":0,"idempotency_key":"test/review/r1","disposition_refs":null,"review_intent":"targeted-re-review","exception_code":"user_requested"} -->
Targeted prompt content'

PATH_A_PROMPT='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test","phase":"execution","agent_role":"codex_reviewer","agent_id":null,"pack_id":null,"repair_round":0,"idempotency_key":"test/path-a/r0","disposition_refs":null,"review_intent":"path-a-re-review","exception_code":null} -->
Path A prompt content'

run_test "non-SubagentStart payload passes" \
  bash -c "echo '{\"tool_input\":{\"command\":\"echo hello\"}}' | bash '$HOOK'"

non_reviewer_passes() {
  make_input pack_executor "$BASELINE_PROMPT" | bash "$HOOK"
}
run_test "non-reviewer SubagentStart passes" non_reviewer_passes

run_test_expect_fail "reviewer missing prompt blocked" \
  bash -c "echo '{\"hook_event_name\":\"SubagentStart\",\"agent_type\":\"codex_reviewer\"}' | bash '$HOOK' 2>/dev/null"

missing_envelope_blocked() {
  make_input codex_reviewer "no envelope" | bash "$HOOK" 2>/dev/null
}
run_test_expect_fail "reviewer missing envelope blocked" missing_envelope_blocked

baseline_dispatch_passes() {
  make_input codex_reviewer "$BASELINE_PROMPT" | bash "$HOOK"
}
run_test "baseline reviewer dispatch passes" baseline_dispatch_passes

targeted_new_reviewer_blocked() {
  make_input codex_reviewer "$TARGETED_PROMPT" | bash "$HOOK" 2>/dev/null
}
run_test_expect_fail "targeted re-review through new reviewer blocked" targeted_new_reviewer_blocked

WORKSPACE=$(mktemp -d)
trap 'rm -rf "$WORKSPACE"' EXIT
mkdir -p "$WORKSPACE/.codex/multi-model-workflow"
cat > "$WORKSPACE/.codex/multi-model-workflow/workflow-state-test.json" <<'JSON'
{"path_a_escalation":[]}
JSON

path_a_without_escalation_blocked() {
  (cd "$WORKSPACE" && make_input codex_reviewer "$PATH_A_PROMPT" | bash "$HOOK" 2>/dev/null)
}
run_test_expect_fail "path-a re-review without escalation blocked" path_a_without_escalation_blocked

cat > "$WORKSPACE/.codex/multi-model-workflow/workflow-state-test.json" <<'JSON'
{"path_a_escalation":[{"pack_id":"1.1","blocked_for_self_fix":true}]}
JSON

path_a_with_escalation_passes() {
  (cd "$WORKSPACE" && make_input codex_reviewer "$PATH_A_PROMPT" | bash "$HOOK")
}
run_test "path-a re-review with escalation passes" path_a_with_escalation_passes

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
