#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

ARCH="$PLUGIN_DIR/architecture-draft.md"
VERIFY="$PLUGIN_DIR/scripts/verify-maturity.sh"
EFFECTIVENESS="$PLUGIN_DIR/scripts/lib/review-effectiveness.sh"
SCHEMA="$PLUGIN_DIR/state-schema/workflow-state-v1.json"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_effectiveness_optional.sh ==="

run_test "architecture marks review_effectiveness optional diagnostic" bash -c \
  "grep -q 'review_effectiveness' '$ARCH' && grep -q '可选诊断' '$ARCH'"

run_test "verify-maturity treats review-effectiveness as optional diagnostic" bash -c \
  "grep -q 'review-effectiveness optional diagnostic script exists' '$VERIFY'"

run_test "review-effectiveness script documents diagnostic-only warnings" bash -c \
  "grep -q 'diagnostic-only' '$EFFECTIVENESS' && grep -q 'not a correctness gate' '$EFFECTIVENESS'"

run_test "schema describes review_effectiveness as optional diagnostic" bash -c \
  "grep -q 'Optional diagnostic' '$SCHEMA'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
