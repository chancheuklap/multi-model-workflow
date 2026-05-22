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

run_test_expect_fail "disposition append accepted without evidence → exit 2" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id "F3" --disposition "accepted" --confidence 7 --severity M

run_test_expect_fail "disposition append accepted with empty evidence → exit 2" \
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

# --- transition ---
run_test_expect_fail "transition to repairing without disposition-refs → exit 2" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor coordinator --to repairing

run_test "transition to repairing with valid disposition-refs" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor coordinator --to repairing --disposition-refs "F1"

run_test_expect_fail "transition to repairing with non-accepted ref → exit 2" \
  bash "$STATE_SH" transition --run-id "$RUN_ID" --actor coordinator --to repairing --disposition-refs "F2"

run_test "transition updates cursor phase" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.cursor.phase') == 'repairing' ]]"

# --- validate still passes after all operations ---
run_test "validate passes after operations" \
  bash "$STATE_SH" validate --run-id "$RUN_ID"

# --- Route 4-7: unlimited budget ---
RUN_ID2="test-hotfix-001"
run_test "init hotfix route has unlimited review_total" \
  bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "hotfix" --route "hotfix"

run_test "hotfix review_total is unlimited" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID2' --field '.budget.review_total') == 'unlimited' ]]"

# --- Lock: stale lock cleanup ---
STALE_LOCK="$FIXTURE_DIR/${RUN_ID}.lock"
mkdir -p "$STALE_LOCK"
echo $$ > "$STALE_LOCK/pid"
echo $(($(date +%s) - 120)) > "$STALE_LOCK/ts"

run_test "stale lock cleaned and operation succeeds" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field '.current_step' --value '10'

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
