#!/usr/bin/env bash
# Pack 2.12 (R1 atomic migration): cross-plan contract surface is now hosted
# inside design.md under "## Cross-Plan Contract Anchors", replacing the
# legacy independent file `docs/orchestrate/plans/<slug>/cross-plan-contract-map.md`.
# This test validates all readers point at the new location and no skill still
# instructs Read on the legacy filename.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

PLAN_SKILL="$PLUGIN_DIR/skills/orchestrate-plan-writing/SKILL.md"
PLAN_REVIEW="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-dispatch.md"
PLAN_GATES="$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-gates.md"
FINAL_PRE="$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-preconditions.md"
FINAL_ANGLES="$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-angles.md"
DESIGN_TPL="$PLUGIN_DIR/skills/orchestrate-discovery/references/discovery-design-document.md"
ARCH="$PLUGIN_DIR/architecture-draft.md"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_cross_plan_contract_map.sh ==="

# --- New behavior: design.md hosts the section ---
run_test "design template declares Cross-Plan Contract Anchors section" \
  grep -q "## Cross-Plan Contract Anchors" "$DESIGN_TPL"

run_test "plan-writing SKILL.md points Plan Entry Gate at design.md Cross-Plan Contract Anchors section" \
  grep -q "Cross-Plan Contract Anchors" "$PLAN_SKILL"

run_test "plan gates step requires the Cross-Plan Contract Anchors section" \
  grep -q "Cross-Plan Contract Anchors" "$PLAN_GATES"

run_test "plan gates retains semantic fields (owner / provider / consumer)" bash -c \
  "grep -q -i 'owner\|provider' '$PLAN_GATES' && grep -q -i 'consumer' '$PLAN_GATES'"

run_test "plan review dispatch consumes design.md#cross-plan-contract-anchors" \
  grep -q "cross-plan-contract-anchors" "$PLAN_REVIEW"

run_test "final review preconditions read Cross-Plan Contract Anchors" \
  grep -q "Cross-Plan Contract Anchors" "$FINAL_PRE"

run_test "final review angles validate Cross-Plan Contract Anchors with git diff" bash -c \
  "grep -q 'Cross-Plan Contract Anchors' '$FINAL_ANGLES' && grep -q 'git diff <starting_commit>..HEAD' '$FINAL_ANGLES'"

run_test "final review can return NEEDS_EXECUTION for cross-plan contract failure" \
  grep -q "NEEDS_EXECUTION" "$FINAL_ANGLES"

run_test "architecture-draft documents Cross-Plan Contract Anchors section" \
  grep -q "Cross-Plan Contract Anchors" "$ARCH"

# --- Old behavior: no reader directs you to Read the legacy file ---
run_test_expect_fail "no skill instructs readers to Read the legacy cross-plan-contract-map.md" \
  grep -rq 'Read.*cross-plan-contract-map.md' "$PLUGIN_DIR/skills/"

# --- Fallback / migration context is still allowed as a callout ---
run_test "fallback / migration note acknowledges the old filename in plan-gates" \
  grep -q "cross-plan-contract-map.md" "$PLAN_GATES"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
