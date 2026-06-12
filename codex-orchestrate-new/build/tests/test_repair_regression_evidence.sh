#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CANONICAL="$PLUGIN_DIR/skills/_shared/repair-routing.md"

AGENTS=(
  "$PLUGIN_DIR/agents/pack_executor.toml"
  "$PLUGIN_DIR/agents/complex_pack_executor.toml"
  "$PLUGIN_DIR/agents/root_cause_analyst.toml"
)

REFERENCES=(
  "$PLUGIN_DIR/skills/orchestrate-workflow/references/workflow-direct-repair.md"
  "$PLUGIN_DIR/skills/orchestrate-workflow/references/bug-investigation-route.md"
  "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md"
  "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md"
  "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"
  "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-repair-truncation.md"
  "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md"
  "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-release-gate.md"
  "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-release-gate.md"
)

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_repair_regression_evidence.sh ==="

# Canonical repair-routing now inlines the finding-type→evidence table
# (was _shared/repair-regression-evidence.md; merged in — it had a single referrer)
run_test "canonical repair-routing requires regression evidence" \
  grep -q "回归证据" "$CANONICAL"

run_test "canonical has finding-type→evidence table" \
  grep -q "回归证据要求" "$CANONICAL"

run_test "canonical allows manual validation gate" \
  grep -q "manual validation gate" "$CANONICAL"

run_test "canonical has Repair Return Contract fields" \
  grep -q "Regression evidence" "$CANONICAL"

# subagent files still have inline regression evidence requirement (from worker-loop template)
for file in "${AGENTS[@]}"; do
  agent="$(basename "$file")"
  run_test "$agent requires regression evidence" \
    grep -q "回归证据" "$file"
  run_test "$agent avoids low-value implementation-detail tests" \
    grep -q "低价值实现细节测试" "$file"
done

# References now point to canonical via Read directive
for ref in "${REFERENCES[@]}"; do
  run_test "$(basename "$ref") references canonical repair-routing" \
    grep -q '${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md' "$ref"
done

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
