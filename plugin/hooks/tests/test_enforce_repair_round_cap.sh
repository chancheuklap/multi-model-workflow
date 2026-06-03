#!/usr/bin/env bash
# Tests for enforce-repair-round-cap.sh
# 覆盖：超限 exit2 拦截 / 未超 exit0 放行 / fail-open（无 routes / 解析失败 / 非 re-review）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../enforce-repair-round-cap.sh"

pass=0; fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"; pass=$((pass+1))
  else
    echo "  FAIL: $name"; fail=$((fail+1))
  fi
}
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure)"; fail=$((fail+1))
  else
    echo "  PASS: $name (expected failure)"; pass=$((pass+1))
  fi
}

echo "=== test_enforce_repair_round_cap.sh ==="

# ─── 共用 fixture helper ───────────────────────────────────────────────────
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# 构造 review prompt 文件，gate 名作为文件名（basename .md = gate 名）
make_prompt() {
  local gate="$1" round="$2" phase="$3" run_id="${4:-test-run}"
  local f="$FIXTURE_DIR/${gate}.md"
  cat > "$f" <<PROMPT
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"${run_id}","phase":"${phase}","agent_role":"codex-reviewer","agent_id":null,"pack_id":null,"repair_round":${round},"idempotency_key":"${run_id}/null/r${round}","disposition_refs":["F-001"],"review_intent":"baseline"} -->
Review content for ${gate}
PROMPT
  echo "$f"
}

make_cmd() {
  local prompt_file="$1"
  # Returns a shell command string that echoes the JSON payload — safe for bash -c
  echo "echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --background --prompt-file ${prompt_file}\"}}'"
}

# ─── 1. Execution: round=3 > max(2) → exit 2 拦截 ──────────────────────────
PF=$(make_prompt "plan-impl-review-1-repair-3" 3 "execution")
run_test_expect_fail "execution round=3 (> max=2) blocked" \
  bash -c "$(make_cmd "$PF") | bash '$HOOK' 2>/dev/null"

# ─── 2. Execution: round=2 = max(2) → exit 0 放行 ──────────────────────────
PF=$(make_prompt "plan-impl-review-1-repair-2" 2 "execution")
run_test "execution round=2 (= max=2) passes" \
  bash -c "$(make_cmd "$PF") | bash '$HOOK'"

# ─── 3. Execution: round=1 < max(2) → exit 0 放行 ──────────────────────────
PF=$(make_prompt "plan-impl-review-1-repair-1" 1 "execution")
run_test "execution round=1 (< max=2) passes" \
  bash -c "$(make_cmd "$PF") | bash '$HOOK'"

# ─── 4. Plan-review: round=3 > max(2) → exit 2 拦截 ────────────────────────
PF=$(make_prompt "plan-review-repair-3" 3 "plan-review")
run_test_expect_fail "plan-review round=3 (> max=2) blocked" \
  bash -c "$(make_cmd "$PF") | bash '$HOOK' 2>/dev/null"

# ─── 5. Plan-review: round=2 = max(2) → exit 0 放行 ────────────────────────
PF=$(make_prompt "plan-review-repair-2" 2 "plan-review")
run_test "plan-review round=2 (= max=2) passes" \
  bash -c "$(make_cmd "$PF") | bash '$HOOK'"

# ─── 6. Unknown gate name (final-review-repair-2 不匹配任何 re-review 格式) → fail-open ──
# final-review 不派 targeted Codex re-review（见 final-review-repair.md:9），
# gate 名 final-review-repair-2 不匹配 plan-impl-review-*-repair-* 或 plan-review-repair-*。
PF=$(make_prompt "final-review-repair-2" 2 "final-review")
run_test "unknown gate name (final-review-repair-2) fail-open passes" \
  bash -c "$(make_cmd "$PF") | bash '$HOOK'"

# ─── 7. Non-codex command → fail-open, exit 0 ──────────────────────────────
run_test "non-codex command fail-open passes" \
  bash -c 'echo "{\"tool_input\":{\"command\":\"ls -la\"}}" | bash "'"$HOOK"'"'

# ─── 8. No command → fail-open, exit 0 ─────────────────────────────────────
run_test "empty command fail-open passes" \
  bash -c 'echo "{\"tool_input\":{}}" | bash "'"$HOOK"'"'

# ─── 9. Codex task but no prompt-file → fail-open, exit 0 ───────────────────
run_test "codex task no prompt-file fail-open passes" \
  bash -c 'echo "{\"tool_input\":{\"command\":\"node codex-companion.mjs task --background\"}}" | bash "'"$HOOK"'"'

# ─── 10. Codex task with prompt-file that has no DISPATCH_ENVELOPE → fail-open ──
NO_ENV_FILE="$FIXTURE_DIR/no-envelope.md"
echo "Some review content without envelope" > "$NO_ENV_FILE"
run_test "no-envelope prompt fail-open passes" \
  bash -c "echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --background --prompt-file $NO_ENV_FILE\"}}' | bash '$HOOK'"

# ─── 11. Baseline review (plan-impl-review-1 without -repair-) → fail-open ──
BASELINE_FILE="$FIXTURE_DIR/plan-impl-review-1.md"
cat > "$BASELINE_FILE" <<PROMPT
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test-run","phase":"execution","agent_role":"codex-reviewer","agent_id":null,"pack_id":null,"repair_round":0,"idempotency_key":"test/null/r0","disposition_refs":null,"review_intent":"baseline"} -->
Baseline review content
PROMPT
run_test "baseline review (plan-impl-review-1) fail-open passes" \
  bash -c "echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --background --prompt-file $BASELINE_FILE\"}}' | bash '$HOOK'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
