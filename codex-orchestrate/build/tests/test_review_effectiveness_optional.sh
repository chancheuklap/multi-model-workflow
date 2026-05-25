#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0

run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

echo "=== test_review_effectiveness_optional.sh ==="

VERIFY="$PLUGIN_DIR/scripts/verify-maturity.sh"
ARCH="$PLUGIN_DIR/architecture-draft.md"

run_test "verify-maturity has optional diagnostics section" \
  grep -q "Optional Diagnostics" "$VERIFY"

run_test "verify-maturity does not gate on review-effectiveness" bash -c \
  "! grep -q 'check \"review-effectiveness.sh exists\"' '$VERIFY'"

run_test "verify-maturity treats review-effectiveness as optional" \
  grep -q 'optional_check "review-effectiveness.sh available"' "$VERIFY"

run_test "architecture marks review_effectiveness optional diagnostic" bash -c \
  "grep -q 'review_effectiveness' '$ARCH' && grep -q '可选诊断' '$ARCH'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
