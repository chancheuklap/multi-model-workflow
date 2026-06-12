#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CANONICAL="$PLUGIN_DIR/skills/_shared/repair-routing.md"

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

# Canonical reference (D1) contains the core content
run_test "canonical repair-routing is Codex native" bash -c \
  "grep -q 'send_input' '$CANONICAL' && grep -q 'complex_pack_executor' '$CANONICAL' && grep -q 'root_cause_analyst' '$CANONICAL'"
run_test "canonical includes finding-to-owner repair routing" \
  grep -q "Finding-to-owner 修复分流" "$CANONICAL"

# All former anchor sites now reference canonical via Read directive
for file in "${FILES[@]}"; do
  run_test "$(basename "$file") references canonical repair-routing" \
    grep -q '${MMW_PLUGIN_ROOT}/skills/_shared/repair-routing.md' "$file"
done

OLD_HOST="cla""ude"
OLD_WORKER="codex""-worker"
OLD_EXEC="codex"" exec"
OLD_COMPANION="codex""-companion"
OLD_SUBAGENT_FIELD="subagent""_type"
OLD_BACKGROUND_FIELD="run_in""_background"
run_test "repair routing has no foreign-host dispatch terms" bash -c \
  "! grep -R -i '${OLD_HOST}\\|${OLD_WORKER}\\|${OLD_EXEC}\\|${OLD_COMPANION}\\|${OLD_SUBAGENT_FIELD}\\|${OLD_BACKGROUND_FIELD}' '$CANONICAL' >/dev/null"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
