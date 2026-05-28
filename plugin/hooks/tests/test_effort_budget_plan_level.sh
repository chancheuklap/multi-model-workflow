#!/usr/bin/env bash
# Plan 005 Pack 5.12: track-effort-budget.sh Plan-level weighted counting.
# Decision 5: weight = N committed packs from plan-return.json; +0.5 for need-fresh-worker resume.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../track-effort-budget.sh"

WORKSPACE=$(mktemp -d)
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

BUDGET_DIR="$WORKSPACE/.claude/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="test-effort-plan"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","budget":{"budget_status":"initialized","review_total":24,"review_used":0,"effort_total":100,"effort_used":0,"direction_check_count":0},"pending_direction_check":null}
EOF
SF="$BUDGET_DIR/workflow-state-${RUN_ID}.json"

pass=0
fail=0

assert_eq() {
  local name="$1" actual="$2" expected="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name — expected '$expected', got '$actual'"
    fail=$((fail + 1))
  fi
}

# Helper: build envelope-bearing prompt for pack-executor dispatch
make_input_with_envelope() {
  local plan_id="$1" resume_from="${2:-}"
  local envelope
  if [[ -n "$resume_from" ]]; then
    envelope=$(jq -nc --arg pid "$plan_id" --arg rfp "$resume_from" \
      '{protocol_version:"1",run_id:"r1",phase:"execution",agent_role:"plan-executor",repair_round:0,idempotency_key:"k1",plan_id:$pid,resume_from_pack_id:$rfp}')
  else
    envelope=$(jq -nc --arg pid "$plan_id" \
      '{protocol_version:"1",run_id:"r1",phase:"execution",agent_role:"plan-executor",repair_round:0,idempotency_key:"k1",plan_id:$pid}')
  fi
  local prompt="<!-- DISPATCH_ENVELOPE $envelope -->\nstart"
  jq -n --arg p "$(printf '%b' "$prompt")" \
    '{tool_input:{subagent_type:"pack-executor",prompt:$p},tool_response:{output:"done"}}'
}

echo "=== test_effort_budget_plan_level.sh ==="

# Test 1: plan-level dispatch with 5 committed packs → effort += 5
PLAN_ID="001"
PR_DIR="$BUDGET_DIR/plan-returns/$RUN_ID/$PLAN_ID"
mkdir -p "$PR_DIR"
cat > "$PR_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"$PLAN_ID","verdict":"pass","per_pack":{"1.1":{"status":"committed"},"1.2":{"status":"committed"},"1.3":{"status":"committed"},"1.4":{"status":"committed"},"1.5":{"status":"committed"}}}
EOF
# Reset effort_used
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
make_input_with_envelope "$PLAN_ID" "" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "5-pack plan → effort +5" "$ACTUAL" "5"

# Test 2: plan-level dispatch with 3 committed + 2 blocked → effort += 3 (committed only)
cat > "$PR_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"$PLAN_ID","verdict":"partial-pass","per_pack":{"1.1":{"status":"committed"},"1.2":{"status":"committed"},"1.3":{"status":"committed"},"1.4":{"status":"blocked"},"1.5":{"status":"skipped"}}}
EOF
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
make_input_with_envelope "$PLAN_ID" "" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "3-committed + 2-blocked → effort +3" "$ACTUAL" "3"

# Test 3: need-fresh-worker continuation → +0.5 on top of committed count
cat > "$PR_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"$PLAN_ID","verdict":"need-fresh-worker","per_pack":{"1.1":{"status":"committed"},"1.2":{"status":"committed"},"1.3":{"status":"committed"},"1.4":{"status":"committed"},"1.5":{"status":"committed"}}}
EOF
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
make_input_with_envelope "$PLAN_ID" "1.6" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "need-fresh-worker resume → effort +5.5" "$ACTUAL" "5.5"

# Test 4: plan-return.json missing → fallback to 1
rm -f "$PR_DIR/plan-return.json"
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
make_input_with_envelope "$PLAN_ID" "" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "plan-return.json missing → fallback to 1" "$ACTUAL" "1"

# Test 5: legacy envelope (no plan_id) → fallback to 1
LEGACY_INPUT=$(jq -n '{tool_input:{subagent_type:"pack-executor",prompt:"no envelope here"},tool_response:{output:"done"}}')
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
echo "$LEGACY_INPUT" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "legacy envelope (no plan_id) → fallback to 1" "$ACTUAL" "1"

# Test 6: complex-pack-executor with plan_id also uses pack count
ENV2=$(jq -nc --arg pid "$PLAN_ID" \
  '{protocol_version:"1",run_id:"r1",phase:"execution",agent_role:"complex-plan-executor",repair_round:0,idempotency_key:"k2",plan_id:$pid}')
cat > "$PR_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"$PLAN_ID","verdict":"pass","per_pack":{"2.1":{"status":"committed"},"2.2":{"status":"committed"}}}
EOF
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
PROMPT2="<!-- DISPATCH_ENVELOPE $ENV2 -->\nstart"
INPUT2=$(jq -n --arg p "$(printf '%b' "$PROMPT2")" \
  '{tool_input:{subagent_type:"complex-pack-executor",prompt:$p},tool_response:{output:"done"}}')
echo "$INPUT2" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "complex-pack-executor with plan_id → effort +2" "$ACTUAL" "2"

# Test 7: code-explorer unchanged
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
EXPL_INPUT=$(jq -n '{tool_input:{subagent_type:"code-explorer",prompt:"x"},tool_response:{output:"done"}}')
echo "$EXPL_INPUT" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "code-explorer still +1" "$ACTUAL" "1"

# Test 8: root-cause-analyst unchanged
jq '.budget.effort_used = 0' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
RCA_INPUT=$(jq -n '{tool_input:{subagent_type:"root-cause-analyst",prompt:"x"},tool_response:{output:"done"}}')
echo "$RCA_INPUT" | bash "$HOOK" >/dev/null 2>&1
ACTUAL=$(jq -r '.budget.effort_used' "$SF")
assert_eq "root-cause-analyst still +2" "$ACTUAL" "2"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
