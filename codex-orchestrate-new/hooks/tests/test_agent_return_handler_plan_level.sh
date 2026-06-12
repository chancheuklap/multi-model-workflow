#!/usr/bin/env bash
# Plan 005 Pack 5.9: agent-return-handler.sh structural rewrite.
# 5 verdict routes: pass / partial-pass / blocked / need-fresh-worker / needs-plan-revision.
# Doc-patch NOT applied here (Decision 6).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/agent-return-handler.sh"

WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

BUDGET_DIR=".codex/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="arh-test"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","review_dispositions":[]}
EOF

# Two-plan scenario: plan 005 has worker-X, plan 006 has worker-Y
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{
  "005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"}}},
  "006":{"worker_agent_id":"worker-Y","packs":{"6.1":{"status":"pending"}}}
}}
EOF

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

make_pr() {
  local plan_id="$1" verdict="$2"
  shift 2
  local per_pack="{}"
  while [[ $# -gt 0 ]]; do
    local pid="$1" st="$2"; shift 2
    per_pack=$(echo "$per_pack" | jq --arg k "$pid" --arg s "$st" '. + {($k):{status:$s}}')
  done
  local prdir="$BUDGET_DIR/plan-returns/$RUN_ID/$plan_id"
  mkdir -p "$prdir"
  jq -n --arg pid "$plan_id" --arg v "$verdict" --argjson pp "$per_pack" \
    '{schema_version:"1",run_id:"arh-test",plan_id:$pid,verdict:$v,per_pack:$pp,doc_patch_path:"plan-returns/arh-test/\($pid)/doc-patch.diff",open_items_path:"plan-returns/arh-test/\($pid)/open-items.json"}' \
    > "$prdir/plan-return.json"
  # Always include a sentinel doc-patch.diff so the handler can find it
  echo "# patch" > "$prdir/doc-patch.diff"
}

make_input() {
  local plan_id="$1" agent_id="$2" subagent="${3:-pack_executor}"
  local envelope
  envelope=$(jq -nc --arg rid "$RUN_ID" --arg pid "$plan_id" \
    '{protocol_version:"1",run_id:$rid,phase:"execution",agent_role:"plan-executor",repair_round:0,idempotency_key:"k",plan_id:$pid,agent_id:"placeholder"}')
  local prompt="<!-- DISPATCH_ENVELOPE $envelope -->\nrun"
  jq -n --arg t "$subagent" --arg p "$(printf '%b' "$prompt")" \
    '{tool_name:"subagent",tool_input:{agent_type:$t,prompt:$p},tool_response:"Verdict: pass"}'
}

run_handler() {
  local plan_id="$1" agent_id="$2"
  make_input "$plan_id" "$agent_id" | bash "$HOOK"
}

echo "=== test_agent_return_handler_plan_level.sh ==="

# --- Case 1: verdict=pass ---
make_pr "005" "pass" "5.1" "committed" "5.2" "committed"
OUT=$(run_handler "005" "worker-X" 2>&1)
RC=$?
assert_eq "pass: handler exits 0" "$RC" "0"

# Verify execution-state updated
WV=$(jq -r '.plans["005"].worker_verdict' "$BUDGET_DIR/execution-state-${RUN_ID}.json")
assert_eq "pass: worker_verdict mirrored" "$WV" "pass"
S51=$(jq -r '.plans["005"].packs["5.1"].status' "$BUDGET_DIR/execution-state-${RUN_ID}.json")
assert_eq "pass: per_pack status ingested" "$S51" "committed"

# Verify doc-patch NOT yet applied — file still exists in plan-returns/
test -f "$BUDGET_DIR/plan-returns/$RUN_ID/005/doc-patch.diff"
DP_EXISTS=$?
assert_eq "pass: doc-patch.diff still exists (NOT applied — Decision 6)" "$DP_EXISTS" "0"

# Handler should emit a NEXT message mentioning Plan Implementation Review
if echo "$OUT" | grep -q "Plan Implementation Review"; then
  echo "  PASS: pass → NEXT mentions Plan Implementation Review"
  pass=$((pass + 1))
else
  echo "  FAIL: pass → NEXT does not mention Plan Implementation Review (actual: $OUT)"
  fail=$((fail + 1))
fi

# --- Case 2: verdict=partial-pass ---
# Reset state
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"}}}}}
EOF
make_pr "005" "partial-pass" "5.1" "committed" "5.2" "blocked"
OUT=$(run_handler "005" "worker-X" 2>&1)
WV=$(jq -r '.plans["005"].worker_verdict' "$BUDGET_DIR/execution-state-${RUN_ID}.json")
assert_eq "partial-pass: worker_verdict mirrored" "$WV" "partial-pass"
if echo "$OUT" | grep -qE "Plan Implementation Review|partial"; then
  echo "  PASS: partial-pass → NEXT routes to Review or partial-handling"
  pass=$((pass + 1))
else
  echo "  FAIL: partial-pass → unclear NEXT (actual: $OUT)"
  fail=$((fail + 1))
fi

# --- Case 3: verdict=blocked ---
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"pending"}}}}}
EOF
make_pr "005" "blocked" "5.1" "blocked"
OUT=$(run_handler "005" "worker-X" 2>&1)
WV=$(jq -r '.plans["005"].worker_verdict' "$BUDGET_DIR/execution-state-${RUN_ID}.json")
assert_eq "blocked: worker_verdict mirrored" "$WV" "blocked"
if echo "$OUT" | grep -qiE "BLOCKED|block"; then
  echo "  PASS: blocked → NEXT mentions BLOCKED"
  pass=$((pass + 1))
else
  echo "  FAIL: blocked → NEXT missing BLOCKED keyword (actual: $OUT)"
  fail=$((fail + 1))
fi

# --- Case 4: verdict=need-fresh-worker ---
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"}}}}}
EOF
make_pr "005" "need-fresh-worker" "5.1" "committed"
OUT=$(run_handler "005" "worker-X" 2>&1)
if echo "$OUT" | grep -qE "resume_from_pack_id|new subagent|新 subagent"; then
  echo "  PASS: need-fresh-worker → NEXT mentions new subagent + resume_from_pack_id"
  pass=$((pass + 1))
else
  echo "  FAIL: need-fresh-worker → NEXT missing new-agent guidance (actual: $OUT)"
  fail=$((fail + 1))
fi

# --- Case 5: verdict=needs-plan-revision ---
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"pending"}}}}}
EOF
make_pr "005" "needs-plan-revision" "5.1" "skipped"
OUT=$(run_handler "005" "worker-X" 2>&1)
if echo "$OUT" | grep -qE "plan-writing|NEEDS_PLAN_REVISION|revision"; then
  echo "  PASS: needs-plan-revision → NEXT routes to plan-writing"
  pass=$((pass + 1))
else
  echo "  FAIL: needs-plan-revision → NEXT missing revision route (actual: $OUT)"
  fail=$((fail + 1))
fi

# --- Case 6: missing plan-return.json → BLOCKED ---
rm -rf "$BUDGET_DIR/plan-returns/$RUN_ID/005"
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"pending"}}}}}
EOF
OUT=$(run_handler "005" "worker-X" 2>&1)
if echo "$OUT" | grep -qiE "BLOCKED|missing|not found|plan-return"; then
  echo "  PASS: missing plan-return.json → BLOCKED-ish guidance"
  pass=$((pass + 1))
else
  echo "  FAIL: missing plan-return.json → handler silent (actual: $OUT)"
  fail=$((fail + 1))
fi

# --- Case 7: doc-patch NEVER applied by handler (Decision 6) ---
# This is the load-bearing invariant. Sanity grep handler source for "git apply"
# only in the context of a NOT-APPLY decision.
if grep -q 'doc-patch-apply\|apply_doc_patch' "$HOOK"; then
  echo "  FAIL: handler must NOT reference doc-patch-apply lib (Decision 6)"
  fail=$((fail + 1))
else
  echo "  PASS: handler does not source doc-patch-apply lib (Decision 6)"
  pass=$((pass + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
