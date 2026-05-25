#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_model_tiers.sh ==="

# Codex custom agent roles currently own reviewer model selection. The dispatch
# template must not promise per-dispatch phase overrides that the host ignores.
run_test "template delegates model authority to codex_reviewer role" \
  grep -q "agents/codex_reviewer.toml" "$TEMPLATE"

run_test "template does not use phase-selected model placeholder" \
  bash -c "! grep -q '<phase-selected model>' '$TEMPLATE'"

run_test "template does not promise per-dispatch model overrides" \
  bash -c "! grep -q 'Select model by phase\\|model: \"gpt-' '$TEMPLATE'"

# Verify injected content in actual files
run_test "execution-review-dispatch delegates model authority" \
  grep -q "agents/codex_reviewer.toml" "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-review-dispatch.md"

run_test "design-review-angles delegates model authority" \
  grep -q "agents/codex_reviewer.toml" "$PLUGIN_DIR/skills/orchestrate-discovery/references/design-review-angles.md"

run_test "execution SKILL delegates model authority" \
  grep -q "agents/codex_reviewer.toml" "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"

run_test "execution SKILL does not contain stale per-dispatch model override" \
  bash -c "! grep -q 'phase-selected model\\|model: \"gpt-\\|reasoning_effort' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
