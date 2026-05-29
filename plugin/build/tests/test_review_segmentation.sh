#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_segmentation.sh ==="

# Verify review-dispatch canonical has baseline review only (D13a: targeted-re-review removed)
TMPL="$PLUGIN_DIR/skills/_shared/review-dispatch.md"

run_test "canonical has baseline review" \
  grep -q "Baseline review" "$TMPL"

run_test "targeted re-review removed from canonical" \
  bash -c "! grep -q 'Targeted re-review' '$TMPL'"

run_test "no --resume in canonical" \
  bash -c "! grep -q '\-\-resume' '$TMPL'"

run_test "baseline does NOT use --resume" \
  bash -c "! grep -A5 'Baseline review' '$TMPL' | grep -q '\-\-resume'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
