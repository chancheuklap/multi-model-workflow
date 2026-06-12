#!/usr/bin/env bash
# Repair round caps are enforced by dispatch-review.sh validate. The
# enforce-repair-round-cap hook is intentionally a no-op in Codex because native
# subagent dispatch is not a Bash command payload.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DISPATCH_SH="$SCRIPT_DIR/../dispatch-review.sh"
STATE_SH="$SCRIPT_DIR/../state.sh"

pass=0
fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"; pass=$((pass + 1))
  else
    echo "  FAIL: $name"; fail=$((fail + 1))
  fi
}
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure)"; fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"; pass=$((pass + 1))
  fi
}

echo "=== test_review_repair_round_cap.sh ==="

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR/.codex/multi-model-workflow"
mkdir -p "$STATE_BASE" "$FIXTURE_DIR/prompts"

init_budget() {
  local run_id="$1"
  bash "$STATE_SH" init --run-id "$run_id" --slug "$run_id" --route "formal" >/dev/null
  bash "$STATE_SH" budget initialize --run-id "$run_id" --plan-count 1 >/dev/null
}

make_prompt() {
  local gate="$1" round="$2" phase="$3" run_id="$4"
  local f="$FIXTURE_DIR/prompts/${gate}.md"
  cat > "$f" <<PROMPT
<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"${run_id}","phase":"${phase}","agent_role":"codex_reviewer","agent_id":null,"pack_id":null,"plan_id":null,"repair_round":${round},"idempotency_key":"${run_id}/review/r${round}","disposition_refs":["F-001"],"review_intent":"baseline","exception_code":null} -->
Review content for ${gate}
PROMPT
  echo "$f"
}

RUN_ID="repair-cap"
init_budget "$RUN_ID"

PF=$(make_prompt "plan-impl-review-1-repair-3" 3 "execution" "$RUN_ID")
run_test_expect_fail "execution round=3 (> max=2) blocked" \
  bash "$DISPATCH_SH" validate --prompt-file "$PF" --gate "plan-impl-review-1-repair-3"

PF=$(make_prompt "plan-impl-review-1-repair-2" 2 "execution" "$RUN_ID")
run_test "execution round=2 (= max=2) passes" \
  bash "$DISPATCH_SH" validate --prompt-file "$PF" --gate "plan-impl-review-1-repair-2"

PF=$(make_prompt "plan-review-repair-3" 3 "plan-review" "$RUN_ID")
run_test_expect_fail "plan-review round=3 (> max=2) blocked" \
  bash "$DISPATCH_SH" validate --prompt-file "$PF" --gate "plan-review-repair-3"

PF=$(make_prompt "plan-review-repair-2" 2 "plan-review" "$RUN_ID")
run_test "plan-review round=2 (= max=2) passes" \
  bash "$DISPATCH_SH" validate --prompt-file "$PF" --gate "plan-review-repair-2"

PF=$(make_prompt "final-review-repair-2" 2 "final-review" "$RUN_ID")
run_test_expect_fail "final-review round=2 (> max=1) blocked" \
  bash "$DISPATCH_SH" validate --prompt-file "$PF" --gate "final-review-repair-2"

PF=$(make_prompt "final-review-repair-1" 1 "final-review" "$RUN_ID")
run_test "final-review round=1 (= max=1) passes" \
  bash "$DISPATCH_SH" validate --prompt-file "$PF" --gate "final-review-repair-1"

NO_ENV_FILE="$FIXTURE_DIR/prompts/no-envelope.md"
echo "Some review content without envelope" > "$NO_ENV_FILE"
run_test_expect_fail "missing DISPATCH_ENVELOPE is blocked" \
  bash "$DISPATCH_SH" validate --prompt-file "$NO_ENV_FILE" --gate "no-envelope"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
