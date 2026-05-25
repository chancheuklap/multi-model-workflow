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

echo "=== test_repair_regression_evidence.sh ==="

TEMPLATE="$PLUGIN_DIR/build/templates/repair-routing.md.tmpl"

run_test "repair-routing template requires regression evidence" \
  grep -q "回归证据" "$TEMPLATE"

run_test "repair-routing template allows manual validation gate" \
  grep -q "manual validation gate" "$TEMPLATE"

run_test "repair-routing template discourages low-value tests" \
  grep -q "低价值实现细节测试" "$TEMPLATE"

for agent in pack_executor complex_pack_executor root_cause_analyst; do
  file="$PLUGIN_DIR/agents/${agent}.toml"
  run_test "$agent requires regression evidence" \
    grep -q "回归证据" "$file"
  run_test "$agent warns against low-value implementation-detail tests" \
    grep -q "低价值实现细节测试" "$file"
done

while IFS= read -r ref; do
  run_test "$(basename "$ref") includes regression evidence contract" \
    grep -q "回归证据" "$ref"
  run_test "$(basename "$ref") includes manual validation gate" \
    grep -q "manual validation gate" "$ref"
done < <(grep -rl "BEGIN: repair-routing" "$PLUGIN_DIR/skills" | sort)

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
