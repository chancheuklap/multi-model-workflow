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

run_test "read plan_writer_agent_id is null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.plan_writer_agent_id') == 'null' ]]"

# --- init formal: budget_status = pending_plan_count, review_total = null ---
run_test "init formal has budget_status pending_plan_count" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.budget_status') == 'pending_plan_count' ]]"

run_test "init formal has review_total null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_total') == 'null' ]]"

run_test "init formal has attendance_mode afk" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.attendance_mode') == 'afk' ]]"

# --- budget initialize ---
run_test "budget initialize with plan-count 4" \
  bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 4

run_test "budget initialize sets review_total to 24 (3*4+12)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.review_total') == '24' ]]"

run_test "budget initialize sets budget_profile to standard" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.budget.budget_profile') == 'standard' ]]"

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
  bash "$STATE_SH" update --run-id "$RUN_ID" --field '.cursor.step' --value '5'

run_test "updated value readable" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.cursor.step') == '5' ]]"

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

# --- Unlimited budget routes (D10: hotfix/quickfix/spike/maintenance collapsed into Route 1) ---
RUN_ID2="test-unlimited-001"
run_test "init direct-repair route has unlimited review_total" \
  bash "$STATE_SH" init --run-id "$RUN_ID2" --slug "dr" --route "direct-repair"

run_test "direct-repair review_total is unlimited" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID2' --field '.budget.review_total') == 'unlimited' ]]"

run_test "direct-repair budget_status is unlimited" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID2' --field '.budget.budget_status') == 'unlimited' ]]"

# --- Lock: stale lock cleanup ---
STALE_LOCK="$FIXTURE_DIR/${RUN_ID}.lock"
mkdir -p "$STALE_LOCK"
echo $$ > "$STALE_LOCK/pid"
echo $(($(date +%s) - 120)) > "$STALE_LOCK/ts"

run_test "stale lock cleaned and operation succeeds" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field '.cursor.step' --value '10'

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

# --- R3-12: mutation log ---
# mutations are only written when STATE_DEBUG=1; default off → stays empty array.
run_test "mutations array exists after init" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.mutations | type') == 'array' ]]"

run_test "mutations array stays empty without STATE_DEBUG" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID' --field '.mutations | length') == '0' ]]"

# Seed a STATE_DEBUG=1 update and verify records appear
RUN_ID_DBG="test-mutations-debug"
run_test "init run for STATE_DEBUG mutation test" \
  bash "$STATE_SH" init --run-id "$RUN_ID_DBG" --slug "dbgtest" --route "formal"

run_test "STATE_DEBUG=1 update writes mutation record" \
  bash -c "STATE_DEBUG=1 bash '$STATE_SH' update --run-id '$RUN_ID_DBG' --field '.cursor.step' --value '99'"

run_test "mutations array has records with STATE_DEBUG=1" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_DBG' --field '.mutations | length') -gt 0 ]]"

run_test "mutation record has field and writer (STATE_DEBUG=1)" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_DBG' --field '.mutations[0].field') != 'null' ]] && [[ \$(bash '$STATE_SH' read --run-id '$RUN_ID_DBG' --field '.mutations[0].writer') != 'null' ]]"

# --- R3-14: cross-file consistency (committed pack without commit_sha) ---
RUN_ID4="test-validate-xfile"
run_test "init for cross-file validation test" \
  bash "$STATE_SH" init --run-id "$RUN_ID4" --slug "xval" --route "formal"

cat > "$FIXTURE_DIR/execution-state-${RUN_ID4}.json" <<'ESJSON'
{"run_id":"test-validate-xfile","plans":{"001":{"packs":{"1.1":{"status":"committed","agent_id":"a1","commit_sha":null}}}}}
ESJSON

run_test_expect_fail "validate fails on committed pack without commit_sha" \
  bash "$STATE_SH" validate --run-id "$RUN_ID4"

# Fix the execution-state and test that accepted disposition without evidence also fails
cat > "$FIXTURE_DIR/execution-state-${RUN_ID4}.json" <<'ESJSON'
{"run_id":"test-validate-xfile","plans":{"001":{"packs":{"1.1":{"status":"pending","agent_id":null,"commit_sha":null}}}}}
ESJSON

# Inject accepted disposition without evidence directly into JSON
jq '.review_dispositions = [{"finding_id":"BF1","disposition":"accepted","evidence":""}]' \
  "$FIXTURE_DIR/workflow-state-${RUN_ID4}.json" > "$FIXTURE_DIR/tmp-val.json" && mv "$FIXTURE_DIR/tmp-val.json" "$FIXTURE_DIR/workflow-state-${RUN_ID4}.json"

run_test_expect_fail "validate fails on accepted disposition without evidence" \
  bash "$STATE_SH" validate --run-id "$RUN_ID4"

# === Pack 2.8 new subcommands ===
echo ""
echo "=== Pack 2.8 new subcommands ==="

# --- agent-id --plan-id (plan-level) ---
RUN_ID5="test-plan-agent-id"
run_test "init for plan-level agent-id test" \
  bash "$STATE_SH" init --run-id "$RUN_ID5" --slug "agent-plan" --route "formal"

cat > "$FIXTURE_DIR/execution-state-${RUN_ID5}.json" <<'ESJSON'
{"run_id":"test-plan-agent-id","plans":{"001":{"packs":{"1.1":{"status":"pending"}}},"002":{"packs":{"2.1":{"status":"pending"}}}}}
ESJSON

run_test "agent-id set --plan-id writes worker_agent_id" \
  bash "$STATE_SH" agent-id set --run-id "$RUN_ID5" --plan-id 001 --agent-id "plan-worker-1"

run_test "agent-id get --plan-id returns set value" \
  bash -c "[[ \$(bash '$STATE_SH' agent-id get --run-id '$RUN_ID5' --plan-id 001) == 'plan-worker-1' ]]"

run_test "agent-id get --plan-id on unset plan returns empty" \
  bash -c "[[ -z \$(bash '$STATE_SH' agent-id get --run-id '$RUN_ID5' --plan-id 002) ]]"

run_test_expect_fail "agent-id set without --plan-id rejected" \
  bash "$STATE_SH" agent-id set --run-id "$RUN_ID5" --agent-id "x"

run_test_expect_fail "agent-id set --plan-id on missing plan rejected" \
  bash "$STATE_SH" agent-id set --run-id "$RUN_ID5" --plan-id 999 --agent-id "x"

# --- disposition append with --plan-id + --coordinator-verified-evidence ---
RUN_ID6="test-disp-extended"
run_test "init for extended disposition test" \
  bash "$STATE_SH" init --run-id "$RUN_ID6" --slug "disp-ext" --route "formal"

run_test "disposition append with --plan-id + --coordinator-verified-evidence" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID6" --finding-id "F1" --disposition accepted \
    --evidence "grep evidence" --plan-id "001" --coordinator-verified-evidence "Coordinator ran grep X"

run_test "disposition plan_id stored correctly" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID6' --field '.review_dispositions[0].plan_id') == '001' ]]"

run_test "disposition coordinator_verified_evidence stored correctly" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID6' --field '.review_dispositions[0].coordinator_verified_evidence') == 'Coordinator ran grep X' ]]"

run_test "disposition without --plan-id stores null" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID6" --finding-id "F2" --disposition rejected
run_test "disposition F2 plan_id is null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID6' --field '.review_dispositions[1].plan_id') == 'null' ]]"
run_test "disposition F2 coordinator_verified_evidence is null" \
  bash -c "[[ \$(bash '$STATE_SH' read --run-id '$RUN_ID6' --field '.review_dispositions[1].coordinator_verified_evidence') == 'null' ]]"

run_test_expect_fail "disposition accepted with explicit empty --coordinator-verified-evidence rejected" \
  bash "$STATE_SH" disposition append --run-id "$RUN_ID6" --finding-id "F3" --disposition accepted \
    --evidence "ok" --coordinator-verified-evidence ""

# --- validate enforces blank coordinator_verified_evidence only when present-but-empty ---
RUN_ID7="test-validate-cve"
run_test "init for cve validate test" \
  bash "$STATE_SH" init --run-id "$RUN_ID7" --slug "cve" --route "formal"

# Inject accepted disposition with cve key but empty value: should FAIL validate
jq '.review_dispositions = [{"finding_id":"X1","disposition":"accepted","evidence":"e","coordinator_verified_evidence":""}]' \
  "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json" > "$FIXTURE_DIR/tmp-cve.json" && mv "$FIXTURE_DIR/tmp-cve.json" "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json"

run_test_expect_fail "validate fails when accepted has blank coordinator_verified_evidence" \
  bash "$STATE_SH" validate --run-id "$RUN_ID7"

# Replace with null cve: should PASS validate (backward compat)
jq '.review_dispositions = [{"finding_id":"X1","disposition":"accepted","evidence":"e","coordinator_verified_evidence":null}]' \
  "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json" > "$FIXTURE_DIR/tmp-cve.json" && mv "$FIXTURE_DIR/tmp-cve.json" "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json"

run_test "validate passes when accepted has null coordinator_verified_evidence" \
  bash "$STATE_SH" validate --run-id "$RUN_ID7"

# Replace with absent cve (pre-Plan-002 state): should PASS validate (backward compat)
jq '.review_dispositions = [{"finding_id":"X1","disposition":"accepted","evidence":"e"}]' \
  "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json" > "$FIXTURE_DIR/tmp-cve.json" && mv "$FIXTURE_DIR/tmp-cve.json" "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json"

run_test "validate passes when accepted lacks coordinator_verified_evidence key (legacy)" \
  bash "$STATE_SH" validate --run-id "$RUN_ID7"

# Replace with non-empty cve: should PASS validate
jq '.review_dispositions = [{"finding_id":"X1","disposition":"accepted","evidence":"e","coordinator_verified_evidence":"Coordinator verified"}]' \
  "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json" > "$FIXTURE_DIR/tmp-cve.json" && mv "$FIXTURE_DIR/tmp-cve.json" "$FIXTURE_DIR/workflow-state-${RUN_ID7}.json"

run_test "validate passes when accepted has populated coordinator_verified_evidence" \
  bash "$STATE_SH" validate --run-id "$RUN_ID7"

# --- review-history append ---
RUN_ID8="test-review-history"
run_test "init for review-history test" \
  bash "$STATE_SH" init --run-id "$RUN_ID8" --slug "rh-test" --route "formal"

# Create fixture design and plan documents under a temp cwd
REVHIST_WORKDIR=$(mktemp -d)
mkdir -p "$REVHIST_WORKDIR/docs/orchestrate/design"
mkdir -p "$REVHIST_WORKDIR/docs/orchestrate/plans/rh-test"

cat > "$REVHIST_WORKDIR/docs/orchestrate/design/rh-test.md" <<'DOCEOF'
# Test Design

## Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |

## Some other section
DOCEOF

cat > "$REVHIST_WORKDIR/docs/orchestrate/plans/rh-test/001-foo.md" <<'DOCEOF'
# Plan 001

## Plan Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |

## Pack Execution Manifest
DOCEOF

run_test "review-history append to design" \
  bash -c "cd '$REVHIST_WORKDIR' && bash '$STATE_SH' review-history append --run-id '$RUN_ID8' --doc design --slug rh-test --round 1 --verdict pass --reviewer codex-gpt-5.5 --date 2026-05-28"

run_test "review-history row appears in design" \
  bash -c "grep -F '| 1 | pass | codex-gpt-5.5 |' '$REVHIST_WORKDIR/docs/orchestrate/design/rh-test.md'"

run_test "review-history append idempotent" \
  bash -c "cd '$REVHIST_WORKDIR' && bash '$STATE_SH' review-history append --run-id '$RUN_ID8' --doc design --slug rh-test --round 1 --verdict pass --reviewer codex-gpt-5.5 --date 2026-05-28 && [[ \$(grep -c -F '| 1 | pass | codex-gpt-5.5 |' '$REVHIST_WORKDIR/docs/orchestrate/design/rh-test.md') -eq 1 ]]"

run_test "review-history append to plan" \
  bash -c "cd '$REVHIST_WORKDIR' && bash '$STATE_SH' review-history append --run-id '$RUN_ID8' --doc plan --slug rh-test --plan-id 001 --round 1 --verdict pass --reviewer codex-gpt-5.5 --date 2026-05-28"

run_test "review-history row appears in plan" \
  bash -c "grep -F '| 1 | pass | codex-gpt-5.5 |' '$REVHIST_WORKDIR/docs/orchestrate/plans/rh-test/001-foo.md'"

run_test_expect_fail "review-history append rejects missing doc kind" \
  bash -c "cd '$REVHIST_WORKDIR' && bash '$STATE_SH' review-history append --run-id '$RUN_ID8' --slug rh-test --round 1 --verdict pass"

run_test_expect_fail "review-history append rejects plan without --plan-id" \
  bash -c "cd '$REVHIST_WORKDIR' && bash '$STATE_SH' review-history append --run-id '$RUN_ID8' --doc plan --slug rh-test --round 1 --verdict pass"

# --- merge-brief lifecycle (Pack 6.8: 9-section schema, ephemeral path) ---
RUN_ID9="test-mb"
run_test "init for merge-brief test" \
  bash "$STATE_SH" init --run-id "$RUN_ID9" --slug "mb-test" --route "multi-pr-merge"

# merge-brief init now uses STATE_BASE path, no --brief-path needed
run_test "merge-brief init creates file in STATE_BASE" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID9" --slug "mb-test"

run_test "merge-brief init idempotent (second call is OK)" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID9" --slug "mb-test"

# merge-brief stage uses valid stage enum value
run_test "merge-brief stage to conflict_discovery" \
  bash -c "bash '$STATE_SH' merge-brief stage --run-id '$RUN_ID9' --stage 'conflict_discovery'"

run_test "merge-brief stage updates META current_stage" \
  bash -c "grep -q '\"current_stage\": \"conflict_discovery\"' '$FIXTURE_DIR/merge-brief-$RUN_ID9.md'"

run_test "merge-brief stage to rca (enum progress)" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID9" --stage "rca"

run_test_expect_fail "merge-brief stage invalid enum fails" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID9" --stage "compositional-model"

run_test "merge-brief verify passes on scaffold" \
  bash "$STATE_SH" merge-brief verify --run-id "$RUN_ID9"

# Corrupt the brief by removing a required section, verify must fail
MB_FILE="$FIXTURE_DIR/merge-brief-$RUN_ID9.md"
sed -i.bak '/## 3\. 合并后正确状态模型/d' "$MB_FILE" 2>/dev/null || sed -i '' '/## 3\. 合并后正确状态模型/d' "$MB_FILE"
run_test_expect_fail "merge-brief verify fails when section missing" \
  bash "$STATE_SH" merge-brief verify --run-id "$RUN_ID9"

# Cleanup temp dirs
rm -rf "$REVHIST_WORKDIR"

# === Pack 2.14 transition matrix: plan-level transitions ===
echo ""
echo "=== Pack 2.14 plan-level transitions ==="

RUN_ID10="test-plan-trans"
run_test "init for plan-level transition test" \
  bash "$STATE_SH" init --run-id "$RUN_ID10" --slug "plan-trans" --route "formal"

# Coordinator pending → in_progress (plan-level Worker first dispatch)
run_test "Coordinator pending → in_progress allowed (plan-level dispatch)" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID10' --field '.cursor.phase' --value '\"pending\"' && bash '$STATE_SH' transition --run-id '$RUN_ID10' --actor Coordinator --from pending --to in_progress"

# A6: agent-return-handler actor entries removed from transition matrices —
# that hook never calls state.sh transition (work-item state goes through
# execution-state via plan-returns ingest). Denied now.
run_test_expect_fail "agent-return-handler in_progress → returned DENIED (A6 dangling entry removed)" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID10' --field '.cursor.phase' --value '\"in_progress\"' && bash '$STATE_SH' transition --run-id '$RUN_ID10' --actor agent-return-handler --from in_progress --to returned"
# restore cursor for the next assertion (the denied transition leaves phase untouched)
bash "$STATE_SH" update --run-id "$RUN_ID10" --field '.cursor.phase' --value '"in_progress"' >/dev/null

# Coordinator returned → review_pending (enter Plan Implementation Review)
run_test "Coordinator returned → review_pending allowed (Plan Implementation Review)" \
  bash -c "bash '$STATE_SH' update --run-id '$RUN_ID10' --field '.cursor.phase' --value '\"returned\"' && bash '$STATE_SH' transition --run-id '$RUN_ID10' --actor Coordinator --from returned --to review_pending"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
