#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_disposition_audit_injection.sh ==="

# Verify state.sh disposition append is injected in skill files
run_test "disposition append in execution SKILL.md" \
  grep -q 'state.sh.*disposition append' "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"

run_test "disposition append in final-review-disposition.md" \
  grep -q 'state.sh.*disposition append' "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-disposition.md"

run_test "disposition append in plan-review-resolution.md" \
  grep -q 'state.sh.*disposition append' "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"

run_test "disposition append in design-review-angles.md" \
  grep -q 'state.sh.*disposition append' "$PLUGIN_DIR/skills/orchestrate-discovery/references/design-review-angles.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
