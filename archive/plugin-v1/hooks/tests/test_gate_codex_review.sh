#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../gate-codex-review.sh"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_gate_codex_review.sh ==="

# 1. Non-codex command -> pass
run_test "non-codex command passes" bash -c 'echo "{\"tool_input\":{\"command\":\"echo hello\"}}" | bash "'"$HOOK"'"'

# 2. Missing prompt-file -> exit 2
run_test_expect_fail "missing prompt-file blocked" bash -c 'echo "{\"tool_input\":{\"command\":\"node codex-companion.mjs task --prompt-file /nonexistent\"}}" | bash "'"$HOOK"'" 2>/dev/null'

# 3. No command -> pass
run_test "empty command passes" bash -c 'echo "{\"tool_input\":{}}" | bash "'"$HOOK"'"'

# 4. Non-task codex command -> pass
run_test "codex non-task passes" bash -c 'echo "{\"tool_input\":{\"command\":\"node codex-companion.mjs status abc\"}}" | bash "'"$HOOK"'"'

# 5. targeted-re-review is now rejected (D13b: enum removed from dispatch-envelope)
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
mkdir -p "$FIXTURE_DIR"
cat > "$FIXTURE_DIR/test-prompt.md" <<'PROMPT'
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test","phase":"execution","agent_role":"codex-reviewer","agent_id":null,"pack_id":null,"repair_round":0,"idempotency_key":"test/null/r0","disposition_refs":null,"review_intent":"targeted-re-review","exception_code":"user_requested"} -->
Review prompt content
PROMPT

run_test_expect_fail "targeted-re-review blocked (D13b)" \
  bash -c "echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --background --prompt-file $FIXTURE_DIR/test-prompt.md\"}}' | bash '$HOOK' 2>/dev/null"

# --- C8: routes 驱动的 baseline 闸门（同 baseline + 同未提交 pack，route 决定拦不拦）---
# 构造一个带未提交 pack 的 execution-state + 一个 plan-impl-review-1 baseline prompt，
# 在两种 route 下分别跑：formal（review_required 含 baseline）应拦，direct-repair（[]）应放行。
mk_state() {  # $1=run_id $2=route  →  在 CWD 的 .claude/multi-model-workflow 下建 state
  mkdir -p ".claude/multi-model-workflow"
  printf '{"route":"%s","run_id":"%s"}\n' "$2" "$1" > ".claude/multi-model-workflow/workflow-state-$1.json"
  printf '{"plans":{"001":{"packs":{"1.1":{"status":"pending"}}}}}\n' > ".claude/multi-model-workflow/execution-state-$1.json"
}
mk_baseline_prompt() {  # $1=run_id  →  echo 出 prompt 文件路径（basename=plan-impl-review-1）
  local f="$FIXTURE_DIR/plan-impl-review-1.md"
  printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"%s","phase":"execution","agent_role":"codex-reviewer","agent_id":null,"pack_id":null,"repair_round":0,"idempotency_key":"%s/null/r0","disposition_refs":null,"review_intent":"baseline","exception_code":null} -->\nReview prompt\n' "$1" "$1" > "$f"
  echo "$f"
}
CWD_TMP=$(mktemp -d)
P1=$(mk_baseline_prompt gatef)

# formal: review_required=["baseline"] → 未提交 pack → 拦截（exit 2）
run_test_expect_fail "C8 formal baseline gate blocks uncommitted packs" \
  bash -c "cd '$CWD_TMP' && mkdir -p .claude/multi-model-workflow && printf '{\"route\":\"formal\",\"run_id\":\"gatef\"}\n' > .claude/multi-model-workflow/workflow-state-gatef.json && printf '{\"plans\":{\"001\":{\"packs\":{\"1.1\":{\"status\":\"pending\"}}}}}\n' > .claude/multi-model-workflow/execution-state-gatef.json && echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --prompt-file $P1\"}}' | bash '$HOOK' 2>/dev/null"

# direct-repair: review_required=[] → 同样未提交 pack → 不拦（exit 0），证明闸门由 routes 决定
P2=$(mk_baseline_prompt gated)
run_test "C8 direct-repair route skips baseline gate (routes-driven)" \
  bash -c "cd '$CWD_TMP' && mkdir -p .claude/multi-model-workflow && printf '{\"route\":\"direct-repair\",\"run_id\":\"gated\"}\n' > .claude/multi-model-workflow/workflow-state-gated.json && printf '{\"plans\":{\"001\":{\"packs\":{\"1.1\":{\"status\":\"pending\"}}}}}\n' > .claude/multi-model-workflow/execution-state-gated.json && echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --prompt-file $P2\"}}' | bash '$HOOK' 2>/dev/null"
rm -rf "$CWD_TMP"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
