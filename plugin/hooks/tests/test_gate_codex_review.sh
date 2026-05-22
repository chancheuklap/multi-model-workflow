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

# 5. targeted-re-review without --resume -> exit 2
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
mkdir -p "$FIXTURE_DIR"
cat > "$FIXTURE_DIR/test-prompt.md" <<'PROMPT'
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"test","phase":"execution","agent_role":"codex-reviewer","agent_id":null,"pack_id":null,"repair_round":0,"idempotency_key":"test/null/r0","disposition_refs":null,"review_intent":"targeted-re-review","exception_code":"user_requested"} -->
Review prompt content
PROMPT

run_test_expect_fail "targeted-re-review without --resume blocked" \
  bash -c "echo '{\"tool_input\":{\"command\":\"node codex-companion.mjs task --background --prompt-file $FIXTURE_DIR/test-prompt.md\"}}' | bash '$HOOK' 2>/dev/null"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
