#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_sendmessage_resume_injection.sh ==="

# Verify SendMessage Resume content in repair references
run_test "SendMessage in final-review-repair" \
  grep -q "SendMessage Resume 操作步骤" "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md"

run_test "SendMessage in execution-repair-truncation" \
  grep -q "SendMessage Resume 操作步骤" "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-repair-truncation.md"

run_test "SendMessage in plan-review-resolution" \
  grep -q "SendMessage Resume 操作步骤" "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"

# Verify no Agent() in Path B
run_test "no Agent() in final-review Path B" \
  bash -c "! grep -A3 '路径 B' '$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md' | grep -q 'Agent({'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
