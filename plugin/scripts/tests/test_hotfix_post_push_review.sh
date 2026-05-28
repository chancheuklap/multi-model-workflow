#!/usr/bin/env bash
# Tests hotfix variant post-push review: push writes pending_post_push_reviews.
# Hotfix is now Route 1 + phase_skip flags (D10 collapse).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_hotfix_post_push_review.sh ==="

RUN_ID="test-hotfix"
# Hotfix now uses formal route + phase_skip + commit_format_override (D10)
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "hotfix-1" --route "formal" >/dev/null

# Simulate hotfix variant setup: set phase_skip + budget + commit_format_override
bash "$STATE_SH" update --run-id "$RUN_ID" \
  --field '.phase_skip' \
  --value '["discovery","plan-writing","plan-review","final-review"]' >/dev/null
bash "$STATE_SH" update --run-id "$RUN_ID" \
  --field '.commit_format_override' \
  --value '"hotfix-unreviewed"' >/dev/null
bash "$STATE_SH" update --run-id "$RUN_ID" \
  --field '.budget.budget_status' \
  --value '"unlimited"' >/dev/null

# Verify hotfix variant has unlimited budget
run_test "hotfix variant has unlimited budget" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'unlimited' ]]"

# Verify pending_post_push_reviews starts empty
run_test "pending_post_push_reviews starts empty" \
  bash -c "[[ \$(jq '.pending_post_push_reviews | length' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') -eq 0 ]]"

# Write pending post-push review
bash "$STATE_SH" update --run-id "$RUN_ID" \
  --field '.pending_post_push_reviews' \
  --value '[{"type":"post-push-regression","commit":"abc123def","created_at":"2025-01-01T12:00:00Z"}]' >/dev/null

# Verify post-push review entry was written
run_test "pending_post_push_reviews has 1 entry" \
  bash -c "[[ \$(jq '.pending_post_push_reviews | length' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') -eq 1 ]]"

run_test "entry type is post-push-regression" \
  bash -c "[[ \$(jq -r '.pending_post_push_reviews[0].type' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'post-push-regression' ]]"

run_test "entry commit is recorded" \
  bash -c "[[ \$(jq -r '.pending_post_push_reviews[0].commit' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'abc123def' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
