#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_model_tiers.sh ==="

# Verify template specifies correct model tiers
run_test "discovery/plan-writing -> gpt-5.5" \
  grep -q "discovery, plan-writing.*gpt-5.5" "$TEMPLATE"

run_test "execution/final-review -> gpt-5.4" \
  grep -q "execution, final-review.*gpt-5.4" "$TEMPLATE"

# Verify injected content in actual files
run_test "execution-review-dispatch has gpt-5.5 for discovery" \
  grep -q "gpt-5.5" "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-review-dispatch.md"

run_test "design-review-angles has gpt-5.5" \
  grep -q "gpt-5.5" "$PLUGIN_DIR/skills/orchestrate-discovery/references/design-review-angles.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
