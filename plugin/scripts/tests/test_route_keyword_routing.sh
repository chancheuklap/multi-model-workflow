#!/usr/bin/env bash
# Tests route keyword routing:
#   direct-repair/multi-pr-merge/bug-investigation → unlimited budget at init
#   formal → pending_plan_count
#   Route 1 variants (hotfix/quickfix/spike/maintenance) now use formal + phase_skip flags (D10)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_route_keyword_routing.sh ==="

# Unlimited-init routes (4 enum values minus formal)
for route in direct-repair multi-pr-merge bug-investigation; do
  RUN_ID="test-route-${route}"
  bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "$route" >/dev/null
  run_test "$route route gets unlimited budget" \
    bash -c "[[ \$(jq -r '.budget.budget_status' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'unlimited' ]]"
done

# Formal route still defers via pending_plan_count
RUN_ID="test-route-formal"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null
run_test "formal route gets pending_plan_count" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'pending_plan_count' ]]"

# Route 1 variants: formal + phase_skip (D10 collapse)
run_test "formal route has phase_skip array" \
  bash -c "[[ \$(jq -r '.phase_skip | type' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'array' ]]"
run_test "formal route has commit_format_override null" \
  bash -c "[[ \$(jq -r '.commit_format_override // \"null\"' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'null' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
