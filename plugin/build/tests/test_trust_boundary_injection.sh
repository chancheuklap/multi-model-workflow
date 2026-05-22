#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_trust_boundary_injection.sh ==="

# Verify trust-boundary template exists
run_test "trust-boundary template exists" \
  test -f "$PLUGIN_DIR/build/templates/trust-boundary.md.tmpl"

# Verify resolver exists
run_test "trust-boundary resolver exists" \
  test -f "$PLUGIN_DIR/build/resolvers/trust-boundary.sh"

# Verify variants are extractable
run_test "review variant extractable" \
  bash -c "bash '$PLUGIN_DIR/build/resolvers/trust-boundary.sh' '$PLUGIN_DIR/build/templates' trust-boundary review | grep -q 'UNTRUSTED REVIEW OUTPUT'"

run_test "worker variant extractable" \
  bash -c "bash '$PLUGIN_DIR/build/resolvers/trust-boundary.sh' '$PLUGIN_DIR/build/templates' trust-boundary worker | grep -q 'UNTRUSTED CODE DIFF'"

run_test "learning variant extractable" \
  bash -c "bash '$PLUGIN_DIR/build/resolvers/trust-boundary.sh' '$PLUGIN_DIR/build/templates' trust-boundary learning | grep -q 'UNTRUSTED LEARNING'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
