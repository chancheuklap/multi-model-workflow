#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"
VALIDATE="$PLUGIN_DIR/scripts/validate-review-dispatch.sh"

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

write_prompt() {
  local path="$1" run_id="$2" gate="$3" intent="$4" agent_id="$5" repair_round="$6" disposition_refs="$7" exception_code="$8"
  cat > "$path" <<EOF
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "$run_id",
  "phase": "execution",
  "agent_role": "codex_reviewer",
  "agent_id": $agent_id,
  "pack_id": null,
  "repair_round": $repair_round,
  "idempotency_key": "$run_id/$gate/r$repair_round",
  "disposition_refs": $disposition_refs,
  "review_intent": "$intent",
  "exception_code": $exception_code,
  "correlation_id": "$run_id/$gate"
}
-->

# $gate

## Scope
Review fixture for $gate.

## Aggregate diff
--- BEGIN UNTRUSTED CODE DIFF ---
diff --git a/app.py b/app.py
--- END UNTRUSTED CODE DIFF ---

## Changed files
- app.py

## Source artifacts
- docs/orchestrate/design/fixture.md
EOF
}

echo "=== test_review_dispatch_validation.sh ==="

RUN_ID="review-gate"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "review-gate" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 1 >/dev/null

cat > "$FIXTURE_DIR/execution-state-${RUN_ID}.json" <<'JSON'
{
  "run_id": "review-gate",
  "current_plan_id": "001",
  "plans": {
    "001": {
      "status": "in_progress",
      "start_commit": "abc123",
      "packs": {
        "1.1": {"status": "committed", "agent_id": "worker-1", "commit_sha": "c1"},
        "1.2": {"status": "pending", "agent_id": null, "commit_sha": null}
      }
    }
  }
}
JSON

BASELINE_PROMPT="$FIXTURE_DIR/plan-impl-review-1.md"
write_prompt "$BASELINE_PROMPT" "$RUN_ID" "plan-impl-review-1" "baseline" "null" 0 "null" "null"

run_test_expect_fail "plan impl review blocks pending packs" \
  bash "$VALIDATE" --prompt-file "$BASELINE_PROMPT" --transport spawn_agent --gate plan-impl-review-1

jq '.plans["001"].packs["1.2"].status = "committed" | .plans["001"].packs["1.2"].agent_id = "worker-2" | .plans["001"].packs["1.2"].commit_sha = "c2" | .plans["001"].status = "completed" | .plans["001"].end_commit = "def456"' \
  "$FIXTURE_DIR/execution-state-${RUN_ID}.json" > "$FIXTURE_DIR/execution-state-${RUN_ID}.tmp"
mv "$FIXTURE_DIR/execution-state-${RUN_ID}.tmp" "$FIXTURE_DIR/execution-state-${RUN_ID}.json"

run_test "plan impl review allows all committed packs" \
  bash "$VALIDATE" --prompt-file "$BASELINE_PROMPT" --transport spawn_agent --gate plan-impl-review-1

mkdir -p "$FIXTURE_DIR/review-agents" "$FIXTURE_DIR/review-results" "$FIXTURE_DIR/review-registry"
echo "reviewer-123" > "$FIXTURE_DIR/review-agents/plan-impl-review-1.agent-id"
cat > "$FIXTURE_DIR/review-results/plan-impl-review-1.md" <<'EOF'
### Verdict
needs repair
EOF
cat > "$FIXTURE_DIR/review-registry/plan-impl-review-1.json" <<'EOF'
{"run_id":"review-gate","gate":"plan-impl-review-1","agent_id":"reviewer-123","status":"completed"}
EOF
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F1" --disposition accepted --confidence 8 --severity H --evidence "verified" --path "app.py:1" >/dev/null

TARGETED_OK="$FIXTURE_DIR/plan-impl-review-1-repair-1.md"
write_prompt "$TARGETED_OK" "$RUN_ID" "plan-impl-review-1-repair-1" "targeted-re-review" "\"reviewer-123\"" 1 "[\"F1\"]" "\"user_requested\""

run_test "targeted re-review accepts recorded baseline reviewer" \
  bash "$VALIDATE" --prompt-file "$TARGETED_OK" --transport send_input --gate plan-impl-review-1-repair-1

TARGETED_BAD_AGENT="$FIXTURE_DIR/plan-impl-review-1-repair-1-bad-agent.md"
write_prompt "$TARGETED_BAD_AGENT" "$RUN_ID" "plan-impl-review-1-repair-1" "targeted-re-review" "\"wrong-reviewer\"" 1 "[\"F1\"]" "\"user_requested\""

run_test_expect_fail "targeted re-review rejects wrong reviewer agent id" \
  bash "$VALIDATE" --prompt-file "$TARGETED_BAD_AGENT" --transport send_input --gate plan-impl-review-1-repair-1

TARGETED_BAD_REF="$FIXTURE_DIR/plan-impl-review-1-repair-1-bad-ref.md"
write_prompt "$TARGETED_BAD_REF" "$RUN_ID" "plan-impl-review-1-repair-1" "targeted-re-review" "\"reviewer-123\"" 1 "[\"F2\"]" "\"user_requested\""

run_test_expect_fail "targeted re-review rejects non-accepted disposition ref" \
  bash "$VALIDATE" --prompt-file "$TARGETED_BAD_REF" --transport send_input --gate plan-impl-review-1-repair-1

RUN_ID_EXHAUSTED="review-budget-override"
bash "$STATE_SH" init --run-id "$RUN_ID_EXHAUSTED" --slug "review-budget-override" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_EXHAUSTED" --plan-count 1 >/dev/null
bash "$STATE_SH" update --run-id "$RUN_ID_EXHAUSTED" --field '.budget.review_used' --value 15 >/dev/null

cat > "$FIXTURE_DIR/execution-state-${RUN_ID_EXHAUSTED}.json" <<'JSON'
{
  "run_id": "review-budget-override",
  "current_plan_id": "001",
  "plans": {
    "001": {
      "status": "completed",
      "start_commit": "abc123",
      "packs": {
        "1.1": {"status": "committed", "agent_id": "worker-1", "commit_sha": "c1"}
      }
    }
  }
}
JSON

EXHAUSTED_PROMPT="$FIXTURE_DIR/plan-impl-review-1-exhausted.md"
write_prompt "$EXHAUSTED_PROMPT" "$RUN_ID_EXHAUSTED" "plan-impl-review-1" "baseline" "null" 0 "null" "null"

run_test_expect_fail "baseline review blocks exhausted review budget" \
  bash "$VALIDATE" --prompt-file "$EXHAUSTED_PROMPT" --transport spawn_agent --gate plan-impl-review-1

run_test_expect_fail "over-budget review validation requires override reason" \
  bash "$VALIDATE" --prompt-file "$EXHAUSTED_PROMPT" --transport spawn_agent --gate plan-impl-review-1 --allow-over-budget

run_test "baseline review allows explicit over-budget override" \
  bash "$VALIDATE" --prompt-file "$EXHAUSTED_PROMPT" --transport spawn_agent --gate plan-impl-review-1 --allow-over-budget --override-reason "user requested one more review"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
