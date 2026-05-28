#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE="$PLUGIN_DIR/build/templates/repair-routing.md.tmpl"
CANONICAL="$PLUGIN_DIR/skills/_shared/repair-routing.md"
RESOLVER="$PLUGIN_DIR/build/resolvers/repair-routing.sh"

FILES=(
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

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_repair_routing.sh ==="

# Template and resolver still exist (for potential future use)
run_test "repair-routing template exists" test -f "$TEMPLATE"
run_test "repair-routing resolver exists" test -x "$RESOLVER"

# Canonical reference (D1) contains the core content
run_test "canonical repair-routing is Claude native" bash -c \
  "grep -q 'SendMessage' '$CANONICAL' && grep -q 'complex-pack-executor' '$CANONICAL' && grep -q 'root-cause-analyst' '$CANONICAL'"
run_test "canonical includes finding-to-owner repair routing" \
  grep -q "Finding-to-owner 修复分流" "$CANONICAL"

# All former anchor sites now reference canonical via Read directive
for file in "${FILES[@]}"; do
  run_test "$(basename "$file") references canonical repair-routing" \
    grep -q "plugin/skills/_shared/repair-routing.md" "$file"
done

run_test "repair routing does not introduce Codex-only dispatch terms" bash -c \
  "! grep -R 'spawn_agent\\|send_input\\|wait_agent\\|\\.codex/multi-model-workflow\\|codex_reviewer\\|pack_executor\\|complex_pack_executor\\|root_cause_analyst' '$PLUGIN_DIR/build/templates/repair-routing.md.tmpl' >/dev/null"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
