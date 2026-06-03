#!/usr/bin/env bash
# Tests for P4 budget-as-instrument changes:
#   - AFK 80% → soft signal only (no DC written)
#   - attended 80% → DC written (dispatch blocked)
#   - 100% any mode → DC written (escape hatch)
#   - budget credit --plans N reduces effective_used
#   - budget initialize --review-total N → custom profile
#   - budget initialize --profile generous → 4P+16 formula
#   - override cap: override_count >= 2 blocks --allow-over-budget
#   - set-attendance writes attendance_mode
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
HOOKS_DIR="$(cd "$SCRIPT_DIR/../../hooks" && pwd)"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
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

echo "=== test_budget_instrument.sh ==="

# ============================================================================
# § set-attendance
# ============================================================================
echo ""
echo "-- set-attendance --"

RUN_ID="test-attend"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "t" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 4 >/dev/null

run_test "default attendance_mode is afk after init" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.attendance_mode') == 'afk' ]]"

run_test "set-attendance --mode attended" \
  bash "$STATE_SH" set-attendance --run-id "$RUN_ID" --mode attended

run_test "attendance_mode is now attended" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.attendance_mode') == 'attended' ]]"

run_test "set-attendance --mode afk" \
  bash "$STATE_SH" set-attendance --run-id "$RUN_ID" --mode afk

run_test "attendance_mode reverted to afk" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.attendance_mode') == 'afk' ]]"

run_test_expect_fail "set-attendance bad mode fails" \
  bash "$STATE_SH" set-attendance --run-id "$RUN_ID" --mode superuser

# ============================================================================
# § ① AFK 80% does NOT write DC
# ============================================================================
echo ""
echo "-- ① AFK 80%: no DC --"

RUN_ID_AFK="test-afk-80"
bash "$STATE_SH" init --run-id "$RUN_ID_AFK" --slug "afk" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_AFK" --plan-count 4 >/dev/null
# review_total = 3*4+12 = 24; 80% threshold = 19

SF_AFK="$FIXTURE_DIR/workflow-state-${RUN_ID_AFK}.json"

# Manually set review_used to 18 (below 80% = 19.2, so int floor 19)
jq '.budget.review_used = 18' "$SF_AFK" > "${SF_AFK}.tmp" && mv "${SF_AFK}.tmp" "$SF_AFK"

# Increment to 19: should hit ≥80% threshold in AFK mode → no DC
bash "$STATE_SH" budget increment-review --run-id "$RUN_ID_AFK" >/dev/null

run_test "AFK 80%: pending_direction_check is still null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_AFK' --field '.pending_direction_check') == 'null' ]]"

run_test "AFK 80%: review_used incremented to 19" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_AFK' --field '.budget.review_used') == '19' ]]"

# ============================================================================
# § ② attended 80% WRITES DC
# ============================================================================
echo ""
echo "-- ② attended 80%: DC written --"

RUN_ID_ATT="test-att-80"
bash "$STATE_SH" init --run-id "$RUN_ID_ATT" --slug "att" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_ATT" --plan-count 4 >/dev/null
bash "$STATE_SH" set-attendance --run-id "$RUN_ID_ATT" --mode attended >/dev/null

SF_ATT="$FIXTURE_DIR/workflow-state-${RUN_ID_ATT}.json"

# Set review_used to 18 then increment to 19 (≥80% of 24)
jq '.budget.review_used = 18' "$SF_ATT" > "${SF_ATT}.tmp" && mv "${SF_ATT}.tmp" "$SF_ATT"
bash "$STATE_SH" budget increment-review --run-id "$RUN_ID_ATT" >/dev/null

run_test "attended 80%: pending_direction_check is pending" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_ATT' --field '.pending_direction_check.ack_status') == 'pending' ]]"

run_test "attended 80%: threshold_percent is 80" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_ATT' --field '.pending_direction_check.threshold_percent') == '80' ]]"

# ============================================================================
# § ③ 100% any mode → DC (escape hatch)
# ============================================================================
echo ""
echo "-- ③ 100% any mode: DC written --"

# Test with AFK mode at 100%
RUN_ID_100="test-100-afk"
bash "$STATE_SH" init --run-id "$RUN_ID_100" --slug "100" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_100" --plan-count 4 >/dev/null
# attendance_mode remains afk (default)

SF_100="$FIXTURE_DIR/workflow-state-${RUN_ID_100}.json"
# Set review_used to 23 (total=24), increment to 24 → 100%
jq '.budget.review_used = 23' "$SF_100" > "${SF_100}.tmp" && mv "${SF_100}.tmp" "$SF_100"
bash "$STATE_SH" budget increment-review --allow-over-budget --override-reason "test" --run-id "$RUN_ID_100" >/dev/null

run_test "AFK 100%: DC written (escape hatch)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_100' --field '.pending_direction_check.ack_status') == 'pending' ]]"

run_test "AFK 100%: threshold_percent is 100" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_100' --field '.pending_direction_check.threshold_percent') == '100' ]]"

# ============================================================================
# § ④ budget credit归还: review_credit increases, effective_used decreases
# ============================================================================
echo ""
echo "-- ④ budget credit --"

RUN_ID_CREDIT="test-credit"
bash "$STATE_SH" init --run-id "$RUN_ID_CREDIT" --slug "credit" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_CREDIT" --plan-count 4 >/dev/null

SF_CREDIT="$FIXTURE_DIR/workflow-state-${RUN_ID_CREDIT}.json"
# Set review_used to 20 (close to 80% of 24 = 19.2)
jq '.budget.review_used = 20' "$SF_CREDIT" > "${SF_CREDIT}.tmp" && mv "${SF_CREDIT}.tmp" "$SF_CREDIT"

run_test "credit --plans 2 → review_credit = 6" \
  bash "$STATE_SH" budget credit --run-id "$RUN_ID_CREDIT" --reason reflux --plans 2

run_test "after credit: review_credit is 6" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_CREDIT' --field '.budget.review_credit') == '6' ]]"

# effective_used = 20 - 6 = 14, which is < 19.2 (80%), so budget check should pass
run_test "after credit: budget check OK (effective below 80%)" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID_CREDIT"

run_test "after credit: increment-review at 14 effective (no DC in AFK)" \
  bash -c "MSG=\$(bash '$STATE_SH' budget increment-review --run-id '$RUN_ID_CREDIT') && echo \"\$MSG\" | grep -qv 'DIRECTION CHECK'"

# Now test budget check output shows effective_used correctly
run_test "budget check reports effective not raw" \
  bash -c "bash '$STATE_SH' budget check --run-id '$RUN_ID_CREDIT' | grep -q 'raw_used=21'"

# ============================================================================
# § ⑤ budget initialize --review-total N (custom) and default (standard)
# ============================================================================
echo ""
echo "-- ⑤ budget initialize --review-total and default --"

RUN_ID_CUSTOM="test-custom"
bash "$STATE_SH" init --run-id "$RUN_ID_CUSTOM" --slug "custom" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_CUSTOM" --plan-count 4 --review-total 50 >/dev/null

run_test "custom --review-total 50: review_total is 50" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_CUSTOM' --field '.budget.review_total') == '50' ]]"

run_test "custom --review-total 50: budget_profile is custom" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_CUSTOM' --field '.budget.budget_profile') == 'custom' ]]"

# Standard: no override → 3*4+12=24, profile=standard
RUN_ID_STD="test-std"
bash "$STATE_SH" init --run-id "$RUN_ID_STD" --slug "std" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_STD" --plan-count 4 >/dev/null

run_test "standard: review_total is 24 (3*4+12)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_STD' --field '.budget.review_total') == '24' ]]"

run_test "standard: budget_profile is standard" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_STD' --field '.budget.budget_profile') == 'standard' ]]"

# ============================================================================
# § ⑥ budget initialize --profile generous → 4P+16
# ============================================================================
echo ""
echo "-- ⑥ --profile generous --"

RUN_ID_GEN="test-generous"
bash "$STATE_SH" init --run-id "$RUN_ID_GEN" --slug "gen" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_GEN" --plan-count 4 --profile generous >/dev/null

run_test "generous: review_total is 32 (4*4+16)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_GEN' --field '.budget.review_total') == '32' ]]"

run_test "generous: budget_profile is generous" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_GEN' --field '.budget.budget_profile') == 'generous' ]]"

# Unknown profile errors
RUN_ID_BAD="test-badprofile"
bash "$STATE_SH" init --run-id "$RUN_ID_BAD" --slug "bad" --route "formal" >/dev/null
run_test_expect_fail "unknown --profile errors exit 2" \
  bash "$STATE_SH" budget initialize --run-id "$RUN_ID_BAD" --plan-count 4 --profile foobar

# ============================================================================
# § ⑦ override cap: override_count >= 2 blocks --allow-over-budget
# ============================================================================
echo ""
echo "-- ⑦ override cap --"

RUN_ID_OVR="test-override-cap"
bash "$STATE_SH" init --run-id "$RUN_ID_OVR" --slug "ovr" --route "formal" >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID_OVR" --plan-count 2 >/dev/null
# review_total = 3*2+12 = 18

SF_OVR="$FIXTURE_DIR/workflow-state-${RUN_ID_OVR}.json"
# Set review_used to 18 (at exhaustion)
jq '.budget.review_used = 18' "$SF_OVR" > "${SF_OVR}.tmp" && mv "${SF_OVR}.tmp" "$SF_OVR"

# First override: should succeed
run_test "first override succeeds (override_count=0→1)" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID_OVR" --allow-over-budget --override-reason "first"

run_test "override_count is now 1" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_OVR' --field '.budget.override_count') == '1' ]]"

# Second override: should succeed (count=1→2)
run_test "second override succeeds (override_count=1→2)" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID_OVR" --allow-over-budget --override-reason "second"

run_test "override_count is now 2" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_OVR' --field '.budget.override_count') == '2' ]]"

# Third override: should be BLOCKED (count=2 >= MAX_OVERRIDES=2)
run_test_expect_fail "third override BLOCKED (override_count>=2)" \
  bash "$STATE_SH" budget check --run-id "$RUN_ID_OVR" --allow-over-budget --override-reason "third"

# ============================================================================
# § track-review-budget.sh hook tests (if hook available)
# ============================================================================
echo ""
echo "-- track-review-budget.sh hook dual-mode --"

HOOK="$HOOKS_DIR/track-review-budget.sh"

if [ ! -f "$HOOK" ]; then
  echo "  SKIP: track-review-budget.sh not found at $HOOK"
else
  # The hook uses CWD-relative paths (.claude/multi-model-workflow).
  # state.sh also reads STATE_BASE env. We run hook tests in a dedicated
  # workspace with STATE_BASE unset so both hook and state.sh use the same
  # CWD-relative path.
  HOOK_WORKSPACE=$(mktemp -d)
  HOOK_BUDGET_DIR="$HOOK_WORKSPACE/.claude/multi-model-workflow"
  mkdir -p "$HOOK_BUDGET_DIR"

  HOOK_INPUT='{"tool_input":{"command":"node codex-companion.mjs result --run-id x"},"tool_response":{"exit_code":0}}'

  # --- AFK 80% test ---
  HOOK_RUN_ID="hook-test-afk"
  echo "$HOOK_RUN_ID" > "$HOOK_BUDGET_DIR/active-run-id"
  HOOK_SF="$HOOK_BUDGET_DIR/workflow-state-${HOOK_RUN_ID}.json"

  jq -n '{
    "run_id": "hook-test-afk",
    "attendance_mode": "afk",
    "budget": {
      "budget_status": "initialized",
      "review_total": 10,
      "review_used": 7,
      "review_credit": 0,
      "budget_profile": "standard",
      "override_count": 0,
      "direction_check_count": 0
    },
    "pending_direction_check": null,
    "idempotency_keys": [],
    "review_dispositions": [],
    "self_verifications": []
  }' > "$HOOK_SF"

  # Increment to 8/10 = 80% in AFK mode → should NOT write DC
  # Run hook in HOOK_WORKSPACE with STATE_BASE unset so hook and state.sh agree on path
  (cd "$HOOK_WORKSPACE" && unset STATE_BASE && echo "$HOOK_INPUT" | bash "$HOOK" >/dev/null 2>&1) || true

  run_test "hook AFK 80%: DC not written" \
    bash -c "[[ \$(jq -r '.pending_direction_check' '$HOOK_SF') == 'null' ]]"

  run_test "hook AFK 80%: review_used incremented to 8" \
    bash -c "[[ \$(jq -r '.budget.review_used' '$HOOK_SF') == '8' ]]"

  # Set to 9/10 = 90%, run again → 10/10 = 100% → DC written (AFK escape hatch)
  jq '.budget.review_used = 9' "$HOOK_SF" > "${HOOK_SF}.tmp" && mv "${HOOK_SF}.tmp" "$HOOK_SF"
  (cd "$HOOK_WORKSPACE" && unset STATE_BASE && echo "$HOOK_INPUT" | bash "$HOOK" >/dev/null 2>&1) || true

  run_test "hook AFK 100%: DC written (escape hatch)" \
    bash -c "[[ \$(jq -r '.pending_direction_check.ack_status' '$HOOK_SF') == 'pending' ]]"

  run_test "hook AFK 100%: threshold_percent is 100" \
    bash -c "[[ \$(jq -r '.pending_direction_check.threshold_percent' '$HOOK_SF') == '100' ]]"

  # --- attended 80% test ---
  HOOK_RUN_ID2="hook-test-att"
  echo "$HOOK_RUN_ID2" > "$HOOK_BUDGET_DIR/active-run-id"
  HOOK_SF2="$HOOK_BUDGET_DIR/workflow-state-${HOOK_RUN_ID2}.json"

  jq -n '{
    "run_id": "hook-test-att",
    "attendance_mode": "attended",
    "budget": {
      "budget_status": "initialized",
      "review_total": 10,
      "review_used": 7,
      "review_credit": 0,
      "budget_profile": "standard",
      "override_count": 0,
      "direction_check_count": 0
    },
    "pending_direction_check": null,
    "idempotency_keys": [],
    "review_dispositions": [],
    "self_verifications": []
  }' > "$HOOK_SF2"

  # 7→8/10 = 80% in attended mode → DC should be written
  (cd "$HOOK_WORKSPACE" && unset STATE_BASE && echo "$HOOK_INPUT" | bash "$HOOK" >/dev/null 2>&1) || true

  run_test "hook attended 80%: DC written" \
    bash -c "[[ \$(jq -r '.pending_direction_check.ack_status' '$HOOK_SF2') == 'pending' ]]"

  run_test "hook attended 80%: threshold_percent is 80" \
    bash -c "[[ \$(jq -r '.pending_direction_check.threshold_percent' '$HOOK_SF2') == '80' ]]"

  rm -rf "$HOOK_WORKSPACE"
fi

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
