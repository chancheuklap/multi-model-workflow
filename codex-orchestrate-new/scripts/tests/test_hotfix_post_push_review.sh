#!/usr/bin/env bash
# Tests hotfix variant post-push review: push writes pending_post_push_reviews.
# Hotfix is now Light Lane (route=light) + commit_format_override="hotfix-unreviewed"
# + pending_post_push_reviews as post-push review ledger.
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
# Hotfix uses Light Lane: route=light (unlimited), commit_format_override=hotfix-unreviewed
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "hotfix-1" --route "light" >/dev/null

# Simulate hotfix submode setup: set commit_format_override (no phase_skip — deprecated P6)
bash "$STATE_SH" update --run-id "$RUN_ID" \
  --field '.commit_format_override' \
  --value '"hotfix-unreviewed"' >/dev/null

# Verify hotfix variant has unlimited budget (Light Lane default)
run_test "hotfix variant has unlimited budget" \
  bash -c "[[ \$(jq -r '.budget.budget_status' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'unlimited' ]]"

# Verify route is light
run_test "hotfix variant uses route=light" \
  bash -c "[[ \$(jq -r '.route' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'light' ]]"

# Verify commit_format_override is hotfix-unreviewed
run_test "hotfix variant has commit_format_override=hotfix-unreviewed" \
  bash -c "[[ \$(jq -r '.commit_format_override' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') == 'hotfix-unreviewed' ]]"

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
