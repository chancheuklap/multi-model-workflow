#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_model_tiers.sh ==="

# Verify review dispatch uses the codex_reviewer TOML model instead of stale
# phase-specific overrides.
run_test "review dispatch points to codex_reviewer TOML" \
  grep -q "agents/codex_reviewer.toml" "$TEMPLATE"

run_test "review dispatch does not mention gpt-5.4" \
  bash -c "! grep -q 'gpt-5.4' '$TEMPLATE'"

run_test "review dispatch does not pass model override" \
  bash -c "! grep -q 'model:' '$TEMPLATE'"

run_test "injected execution review dispatch uses TOML authority" \
  grep -q "agents/codex_reviewer.toml" "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-review-dispatch.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
