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

echo "=== test_repair_routing_injection.sh ==="

TEMPLATE="$PLUGIN_DIR/build/templates/repair-routing.md.tmpl"
RESOLVER="$PLUGIN_DIR/build/resolvers/repair-routing.sh"

run_test "repair-routing template exists" test -f "$TEMPLATE"
run_test "repair-routing resolver exists" test -f "$RESOLVER"
run_test "repair-routing template names Codex native agents" bash -c \
  "grep -q 'complex_pack_executor' '$TEMPLATE' && grep -q 'root_cause_analyst' '$TEMPLATE' && grep -q 'send_input' '$TEMPLATE'"

targets=(
  "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"
  "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-repair-truncation.md"
  "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md"
  "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-release-gate.md"
  "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-release-gate.md"
  "$PLUGIN_DIR/skills/orchestrate-workflow/references/workflow-direct-repair.md"
  "$PLUGIN_DIR/skills/orchestrate-workflow/references/bug-investigation-route.md"
  "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md"
  "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md"
)

for ref in "${targets[@]}"; do
  run_test "$(basename "$ref") has repair-routing anchor" \
    grep -q "BEGIN: repair-routing" "$ref"
  run_test "$(basename "$ref") includes finding-to-owner routing" \
    grep -q "Finding-to-owner 修复分流" "$ref"
done

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
