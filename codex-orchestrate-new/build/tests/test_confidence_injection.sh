#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_confidence_injection.sh ==="

# Confidence calibration table in canonical references (D1)
run_test "confidence in canonical disposition-table" \
  grep -q "8-10 (high)" "$PLUGIN_DIR/skills/_shared/disposition-table.md"

# Confidence rubric moved to review-prompt-quartet.md (§1: auto-injected into每个 review prompt)
run_test "confidence rubric in review-prompt-quartet" \
  grep -q "7-10: high" "$PLUGIN_DIR/skills/_shared/review-prompt-quartet.md"

# Files referencing canonical disposition-table (have Read directives)
run_test "execution SKILL.md references disposition-table canonical" \
  grep -q '${MMW_PLUGIN_ROOT}/skills/_shared/disposition-table.md' "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"

run_test "final-review-disposition references disposition-table canonical" \
  grep -q '${MMW_PLUGIN_ROOT}/skills/_shared/disposition-table.md' "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-disposition.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
