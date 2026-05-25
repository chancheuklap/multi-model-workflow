#!/usr/bin/env bash
# Tests route keyword routing: every non-formal route gets unlimited budget;
# only formal starts with pending_plan_count until plan count is known.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_route_keyword_routing.sh ==="

# Non-formal routes: unlimited budget
for route in direct-repair multi-pr-merge bug-investigation hotfix quickfix spike maintenance; do
  RUN_ID="test-route-${route}"
  bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "$route" >/dev/null
  run_test "$route route gets unlimited budget" \
    bash -c "[[ \$(jq -r '.budget.budget_status' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'unlimited' ]]"
done

# Formal route: pending_plan_count
for route in formal; do
  RUN_ID="test-route-${route}"
  bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "$route" >/dev/null
  run_test "$route route gets pending_plan_count" \
    bash -c "[[ \$(jq -r '.budget.budget_status' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'pending_plan_count' ]]"
done

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
