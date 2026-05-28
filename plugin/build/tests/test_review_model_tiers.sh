#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"
CANONICAL="$PLUGIN_DIR/skills/_shared/review-dispatch.md"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_model_tiers.sh ==="

# Verify template specifies correct model tiers
run_test "template: discovery/plan-writing -> gpt-5.5" \
  grep -q "discovery, plan-writing.*gpt-5.5" "$TEMPLATE"

run_test "template: execution/final-review -> gpt-5.4" \
  grep -q "execution, final-review.*gpt-5.4" "$TEMPLATE"

# Verify canonical reference has model tiers (D1)
run_test "canonical: discovery/plan-writing -> gpt-5.5" \
  grep -q "discovery, plan-writing.*gpt-5.5" "$CANONICAL"

run_test "canonical: execution/final-review -> gpt-5.4" \
  grep -q "execution, final-review.*gpt-5.4" "$CANONICAL"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
