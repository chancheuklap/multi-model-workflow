#!/usr/bin/env bash
# Tests review-effectiveness.sh: fixture dispositions produce correct counts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
EFFECTIVENESS_SH="$SCRIPT_DIR/../lib/review-effectiveness.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_effectiveness.sh ==="

RUN_ID="test-eff"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null

# Add various dispositions
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F1" --disposition "accepted" --evidence "verified in code" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F2" --disposition "rejected" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F3" --disposition "suppress" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F4" --disposition "accepted" --evidence "also verified" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F5" --disposition "rejected" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F6" --disposition "rejected" >/dev/null

# Run effectiveness aggregation
bash "$EFFECTIVENESS_SH" --run-id "$RUN_ID" >/dev/null

# Verify counts
run_test "total_findings is 6" \
  bash -c "[[ \$(jq '.review_effectiveness.total_findings' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') -eq 6 ]]"

run_test "reject_count is 3" \
  bash -c "[[ \$(jq '.review_effectiveness.reject_count' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') -eq 3 ]]"

run_test "suppress_count is 1" \
  bash -c "[[ \$(jq '.review_effectiveness.suppress_count' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') -eq 1 ]]"

run_test "last_aggregated_at is set" \
  bash -c "[[ \$(jq -r '.review_effectiveness.last_aggregated_at' '$FIXTURE_DIR/workflow-state-${RUN_ID}.json') != 'null' ]]"

# --- R3-17: health range warnings ---
RUN_ID2="test-eff-health"
bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "test" --route "formal" >/dev/null

# Create high reject rate scenario (7/10 = 70% > 60%)
for i in {1..7}; do
  bash "$STATE_SH" disposition append --run-id "$RUN_ID2" --finding-id "HR$i" --disposition "rejected" >/dev/null
done
for i in 8 9 10; do
  bash "$STATE_SH" disposition append --run-id "$RUN_ID2" --finding-id "HR$i" --disposition "accepted" --evidence "verified" >/dev/null
done

bash "$EFFECTIVENESS_SH" --run-id "$RUN_ID2" >/dev/null 2>&1

run_test "health_warnings populated for high reject rate" \
  bash -c "[[ \$(jq '.review_effectiveness.health_warnings | length' '$FIXTURE_DIR/workflow-state-${RUN_ID2}.json') -gt 0 ]]"

run_test "health_warnings mentions reject rate" \
  bash -c "jq -r '.review_effectiveness.health_warnings[]' '$FIXTURE_DIR/workflow-state-${RUN_ID2}.json' | grep -q 'reject rate'"

# Verify empty warnings for balanced dispositions
RUN_ID3="test-eff-balanced"
bash "$STATE_SH" init --run-id "$RUN_ID3" --slug "test" --route "formal" >/dev/null

bash "$STATE_SH" disposition append --run-id "$RUN_ID3" --finding-id "B1" --disposition "rejected" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID3" --finding-id "B2" --disposition "rejected" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID3" --finding-id "B3" --disposition "accepted" --evidence "ok" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID3" --finding-id "B4" --disposition "accepted" --evidence "ok" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID3" --finding-id "B5" --disposition "accepted" --evidence "ok" >/dev/null
bash "$STATE_SH" disposition append --run-id "$RUN_ID3" --finding-id "B6" --disposition "path-b" --evidence "ok" >/dev/null

bash "$EFFECTIVENESS_SH" --run-id "$RUN_ID3" >/dev/null 2>&1

run_test "no health_warnings for balanced dispositions" \
  bash -c "[[ \$(jq '.review_effectiveness.health_warnings | length' '$FIXTURE_DIR/workflow-state-${RUN_ID3}.json') -eq 0 ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
