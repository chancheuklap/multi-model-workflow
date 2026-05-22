#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_segmentation.sh ==="

# Verify review-dispatch template distinguishes baseline vs targeted
TMPL="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"

run_test "template has baseline review" \
  grep -q "Baseline review" "$TMPL"

run_test "template has targeted re-review" \
  grep -q "Targeted re-review" "$TMPL"

run_test "targeted re-review uses --resume" \
  grep -q "\-\-resume" "$TMPL"

run_test "baseline does NOT use --resume" \
  bash -c "! sed -n '/Baseline review/,/Targeted/p' '$TMPL' | grep -q '\-\-resume'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
