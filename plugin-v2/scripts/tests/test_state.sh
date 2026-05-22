#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="test-run-001"
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

echo "=== test_state.sh ==="

# --- init ---
run_test "init creates state file" \
  bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test-slug" --route "formal"

run_test "init file is valid JSON" \
  python3 -m json.tool "$FIXTURE_DIR/workflow-state-${RUN_ID}.json"

# --- read ---
run_test "read run_id" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.run_id') == '$RUN_ID' ]]"

run_test "read route" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.route') == 'formal' ]]"

run_test "read default arrays are empty" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.review_dispositions | length') == '0' ]]"

run_test "read self_verifications is empty array" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.self_verifications | length') == '0' ]]"

run_test "read plan_writer_agent_id is null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.plan_writer_agent_id') == 'null' ]]"

# --- init formal: budget_status = pending_plan_count, review_total = null ---
run_test "init formal has budget_status pending_plan_count" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.budget_status') == 'pending_plan_count' ]]"

run_test "init formal has review_total null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_total') == 'null' ]]"

run_test "init formal has effort_total null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.effort_total') == 'null' ]]"

# --- budget initialize ---
run_test "budget initialize with plan-count 4" \
  bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 4

run_test "budget initialize sets review_total to 24 (3*4+12)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_total') == '24' ]]"

run_test "budget initialize sets effort_total to 48 (24*2)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.effort_total') == '48' ]]"

run_test "budget initialize sets budget_status to initialized" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.budget_status') == 'initialized' ]]"

run_test_expect_fail "budget initialize fails when already initialized" \
  bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 5

# --- budget check ---
run_test "budget check passes when initialized" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID"

# --- validate ---
run_test "validate passes on init state" \
  bash "$STATE_SH" validate --run-id "$RUN_ID"

# --- update ---
run_test "update field" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field '.current_step' --value '5'

run_test "updated value readable" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.current_step') == '5' ]]"

# --- disposition append ---
run_test "disposition append accepted with evidence" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F1" --disposition "accepted" --confidence 8 --severity H --evidence "verified by grep"

run_test "disposition append rejected (no evidence needed)" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F2" --disposition "rejected" --confidence 3 --severity L

run_test_expect_fail "disposition append accepted without evidence -> exit 2" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F3" --disposition "accepted" --confidence 7 --severity M

run_test_expect_fail "disposition append accepted with empty evidence -> exit 2" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F4" --disposition "accepted" --confidence 7 --severity M --evidence ""

run_test "dispositions count is 2" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.review_dispositions | length') == '2' ]]"

run_test "disposition F1 evidence readable" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.review_dispositions[0].evidence') == 'verified by grep' ]]"

# --- self-verify append ---
run_test "self-verify append" \
  bash "$STATE_SH" self-verify append --run-id "$RUN_ID" --pack-id "P1" --repair-round 1 --verification-passed yes --exception none

run_test "self-verify readable" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.self_verifications | length') == '1' ]]"

run_test "self-verify exception is none" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.self_verifications[0].exception') == 'none' ]]"

# --- transition matrix tests ---

# Pre-seed cursor.phase to "returned" for the repairing transition tests
run_test "update cursor.phase to returned" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field '.cursor.phase' --value '"returned"'

run_test_expect_fail "transition to repairing without disposition-refs -> exit 2" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor Coordinator --from returned --to repairing

run_test "transition to repairing with valid disposition-refs" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor Coordinator --from returned --to repairing --disposition-refs "F1"

run_test "transition updates cursor phase" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.cursor.phase') == 'repairing' ]]"

run_test_expect_fail "transition to repairing with non-accepted ref -> exit 2" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID' --field '.cursor.phase' --value '\"returned\"' && bash '$STATE_SH' transition --run-id '$RUN_ID' --actor Coordinator --from returned --to repairing --disposition-refs 'F2'"

# Legal: Coordinator pending->dispatched
run_test "transition Coordinator pending->dispatched" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID' --field '.cursor.phase' --value '\"pending\"' && bash '$STATE_SH' transition --run-id '$RUN_ID' --actor Coordinator --from pending --to dispatched"

# Illegal actor: agent-return-handler pending->committed (not in matrix)
run_test_expect_fail "illegal transition: agent-return-handler pending->committed -> exit 2" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID' --field '.cursor.phase' --value '\"pending\"' && bash '$STATE_SH' transition --run-id '$RUN_ID' --actor agent-return-handler --from pending --to committed"

# Wildcard: Coordinator anything->blocked
run_test "wildcard transition: Coordinator anything->blocked" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID' --field '.cursor.phase' --value '\"some_state\"' && bash '$STATE_SH' transition --run-id '$RUN_ID' --actor Coordinator --from some_state --to blocked"

# Missing --actor -> exit 2
run_test_expect_fail "transition without --actor -> exit 2" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --from pending --to dispatched

# --from mismatches current state -> exit 2
run_test_expect_fail "transition --from mismatch -> exit 2" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID' --field '.cursor.phase' --value '\"pending\"' && bash '$STATE_SH' transition --run-id '$RUN_ID' --actor Coordinator --from dispatched --to returned"

# Illegal transition: random actor
run_test_expect_fail "transition denied for unknown actor" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID' --field '.cursor.phase' --value '\"pending\"' && bash '$STATE_SH' transition --run-id '$RUN_ID' --actor evil --from pending --to dispatched"

# --- validate still passes after all operations ---
run_test "validate passes after operations" \
  bash "$STATE_SH" validate --run-id "$RUN_ID"

# --- Route 4-7: unlimited budget ---
RUN_ID2="test-hotfix-001"
run_test "init hotfix route has unlimited review_total" \
  bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "hotfix" --route "hotfix"

run_test "hotfix review_total is unlimited" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID2' --field '.budget.review_total') == 'unlimited' ]]"

run_test "hotfix budget_status is unlimited" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID2' --field '.budget.budget_status') == 'unlimited' ]]"

run_test "hotfix effort_total is unlimited" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID2' --field '.budget.effort_total') == 'unlimited' ]]"

# --- Lock: stale lock cleanup ---
STALE_LOCK="$FIXTURE_DIR/${RUN_ID}.lock"
mkdir -p "$STALE_LOCK"
echo $$ > "$STALE_LOCK/pid"
echo $(($(date +%s) - 120)) > "$STALE_LOCK/ts"

run_test "stale lock cleaned and operation succeeds" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field '.current_step' --value '10'

# --- agent-id subcommand (execution-state) ---
RUN_ID3="test-agent-id-001"
run_test "init for agent-id test" \
  bash "$STATE_SH" init --run-id "$RUN_ID3" --slug "agent-test" --route "formal"

# Create execution-state file for agent-id tests
cat > "$FIXTURE_DIR/execution-state-${RUN_ID3}.json" <<'ESJSON'
{"run_id":"test-agent-id-001","plans":{"001":{"packs":{"1.1":{"status":"pending","agent_id":null,"commit_sha":null,"worker_verdict":null},"1.2":{"status":"pending","agent_id":null,"commit_sha":null,"worker_verdict":null}}}}}
ESJSON

run_test "agent-id set writes to execution-state" \
  bash "$STATE_SH" agent-id set --run-id "$RUN_ID3" --pack-id "1.1" --agent-id "agent-xyz"

run_test "agent-id get returns set value" \
  bash -c "[[ \$(bash '$STATE_SH' agent-id get --run-id '$RUN_ID3' --pack-id '1.1') == 'agent-xyz' ]]"

run_test "agent-id get on unset pack returns empty" \
  bash -c "[[ -z \$(bash '$STATE_SH' agent-id get --run-id '$RUN_ID3' --pack-id '1.2') ]]"

# --- direction-check ---
run_test "direction-check trigger" \
  bash "$STATE_SH" direction-check trigger --run-id "$RUN_ID" --type review --threshold-percent 80

run_test "direction-check pending" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.pending_direction_check.ack_status') == 'pending' ]]"

run_test "direction-check ack continue" \
  bash "$STATE_SH" direction-check ack --run-id "$RUN_ID" --action continue

run_test "direction-check acknowledged" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.pending_direction_check.ack_status') == 'acknowledged' ]]"

# --- idempotency ---
run_test "idempotency check new key" \
  bash "$STATE_SH" idempotency check --run-id "$RUN_ID" --key "test/1.1/r0"

run_test "idempotency append" \
  bash "$STATE_SH" idempotency append --run-id "$RUN_ID" --key "test/1.1/r0"

run_test_expect_fail "idempotency check duplicate key" \
  bash "$STATE_SH" idempotency check --run-id "$RUN_ID" --key "test/1.1/r0"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
