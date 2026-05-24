#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"
RECORD="$PLUGIN_DIR/scripts/record-review-dispatch.sh"
COMPLETE="$PLUGIN_DIR/scripts/complete-review-dispatch.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

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

run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure)"
    fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass + 1))
  fi
}

echo "=== test_review_completion.sh ==="

RUN_ID="review-complete"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "review-complete" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 1 >/dev/null

PROMPT_FILE="$FIXTURE_DIR/plan-review.md"
cat > "$PROMPT_FILE" <<EOF
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "$RUN_ID",
  "phase": "plan-writing",
  "agent_role": "codex_reviewer",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "$RUN_ID/plan-review/r0",
  "disposition_refs": null,
  "review_intent": "baseline",
  "exception_code": null,
  "correlation_id": "$RUN_ID/plan-review"
}
-->

# Plan Review
EOF

RESULT_FILE="$FIXTURE_DIR/review-results/plan-review.md"
mkdir -p "$(dirname "$RESULT_FILE")"
cat > "$RESULT_FILE" <<'EOF'
### Verdict
pass
EOF

run_test "record-review-dispatch writes agent id and registry" \
  bash "$RECORD" --prompt-file "$PROMPT_FILE" --gate plan-review --agent-id reviewer-1

run_test "review agent id file exists" \
  bash -c "[[ \$(cat '$FIXTURE_DIR/review-agents/plan-review.agent-id') == 'reviewer-1' ]]"

run_test "complete-review-dispatch increments review budget" \
  bash "$COMPLETE" --run-id "$RUN_ID" --gate plan-review --agent-id reviewer-1 --result-file "$RESULT_FILE"

run_test "review_used is 1 after completion" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_used') == '1' ]]"

run_test "complete-review-dispatch is idempotent for same gate" \
  bash "$COMPLETE" --run-id "$RUN_ID" --gate plan-review --agent-id reviewer-1 --result-file "$RESULT_FILE"

run_test "review_used stays 1 after replay" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_used') == '1' ]]"

run_test_expect_fail "complete-review-dispatch rejects missing result" \
  bash "$COMPLETE" --run-id "$RUN_ID" --gate missing-result --agent-id reviewer-1 --result-file "$FIXTURE_DIR/missing.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
