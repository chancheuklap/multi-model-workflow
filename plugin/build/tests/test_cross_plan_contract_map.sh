#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

PLAN_SKILL="$PLUGIN_DIR/skills/orchestrate-plan-writing/SKILL.md"
PLAN_REVIEW="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-dispatch.md"
PLAN_GATES="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-gates.md"
FINAL_PRE="$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-preconditions.md"
FINAL_ANGLES="$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-angles.md"
ARCH="$PLUGIN_DIR/architecture-draft.md"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_cross_plan_contract_map.sh ==="

run_test "plan-writing skill creates cross-plan contract map before review" \
  grep -q "cross-plan-contract-map.md" "$PLAN_SKILL"

run_test "plan gates require cross-plan contract map fields" bash -c \
  "grep -q 'producer' '$PLAN_GATES' && grep -q 'consumer' '$PLAN_GATES' && grep -q 'ownership' '$PLAN_GATES' && grep -q 'verification' '$PLAN_GATES'"

run_test "plan review consumes cross-plan contract map" \
  grep -q "cross-plan-contract-map.md" "$PLAN_REVIEW"

run_test "final review preconditions read cross-plan contract map" \
  grep -q "cross-plan-contract-map.md" "$FINAL_PRE"

run_test "final review angles use cross-plan contract map with integration diff" bash -c \
  "grep -q 'cross-plan-contract-map.md' '$FINAL_ANGLES' && grep -q 'git diff <starting_commit>..HEAD' '$FINAL_ANGLES'"

run_test "final review can return NEEDS_EXECUTION for cross-plan contract failure" \
  grep -q "NEEDS_EXECUTION" "$FINAL_ANGLES"

run_test "architecture documents cross-plan contract map artifact" \
  grep -q "cross-plan-contract-map.md" "$ARCH"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
