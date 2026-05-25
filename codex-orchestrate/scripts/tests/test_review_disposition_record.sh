#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"
RECORD="$PLUGIN_DIR/scripts/record-review-dispatch.sh"
COMPLETE="$PLUGIN_DIR/scripts/complete-review-dispatch.sh"
DISPOSITION="$PLUGIN_DIR/scripts/record-review-disposition.sh"

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

echo "=== test_review_disposition_record.sh ==="

RUN_ID="review-disposition"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "$RUN_ID" --route "formal" >/dev/null
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
needs repair
### Result
Critical:
- F1
EOF

run_test_expect_fail "disposition cannot start before durable result completion" \
  bash "$DISPOSITION" --run-id "$RUN_ID" --gate plan-review --status started

run_test "record and complete review result" \
  bash -c "bash '$RECORD' --prompt-file '$PROMPT_FILE' --gate plan-review --agent-id reviewer-1 && bash '$COMPLETE' --run-id '$RUN_ID' --gate plan-review --agent-id reviewer-1 --result-file '$RESULT_FILE'"

run_test "disposition start marks registry" \
  bash "$DISPOSITION" --run-id "$RUN_ID" --gate plan-review --status started

run_test "registry status is disposition_started" \
  bash -c "[[ \$(jq -r '.status' '$FIXTURE_DIR/review-registry/plan-review.json') == 'disposition_started' ]]"

run_test "disposition complete marks registry" \
  bash "$DISPOSITION" --run-id "$RUN_ID" --gate plan-review --status completed

run_test "registry status is disposition_done" \
  bash -c "[[ \$(jq -r '.status' '$FIXTURE_DIR/review-registry/plan-review.json') == 'disposition_done' ]]"

run_test "disposition start is idempotent after done" \
  bash "$DISPOSITION" --run-id "$RUN_ID" --gate plan-review --status started

run_test "registry remains disposition_done" \
  bash -c "[[ \$(jq -r '.status' '$FIXTURE_DIR/review-registry/plan-review.json') == 'disposition_done' ]]"

run_test_expect_fail "wrong run id rejected" \
  bash "$DISPOSITION" --run-id wrong-run --gate plan-review --status completed

rm -f "$RESULT_FILE"
run_test_expect_fail "missing durable result rejected" \
  bash "$DISPOSITION" --run-id "$RUN_ID" --gate plan-review --status completed

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
