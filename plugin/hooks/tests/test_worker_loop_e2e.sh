#!/usr/bin/env bash
# Plan 005 Pack 5.16: Worker Loop end-to-end fixture.
#
# Co-located with hook unit tests because run-all-tests.sh iterates
# plugin/{scripts,hooks,build}/tests/. The "tests/integration/" path
# from the plan body is orphaned in this project — auto-discovery wins.
#
# Scenario: simulate a 3-Pack Plan executed by an autonomous Worker:
#   1. Worker calls state.sh agent-id set --plan-id (claims plan ownership)
#   2. Worker calls pack-progress 3 times (simulates 3 commits)
#   3. Between commits, simulate the track-execution-state hook running
#   4. Verify NEXT-message suppression while worker_agent_id is set
#   5. Worker writes plan-return.json + doc-patch.diff + open-items.json
#   6. Worker calls execution-plan complete
#   7. agent-return-handler.sh fires → ingests artifact → routes verdict
#   8. Verify doc-patch.diff NOT applied (Decision 6)
#   9. Verify execution-state has worker_verdict, per_pack statuses, finished_at
#
# 4 verdict paths covered: pass / partial-pass / blocked / need-fresh-worker.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$(cd "$HOOKS_DIR/.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"

WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

git init -q
git config user.email "t@t"
git config user.name "t"

BUDGET_DIR=".claude/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="e2e-test"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"
export STATE_BASE="$BUDGET_DIR"

# Workflow state
cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","budget":{"budget_status":"initialized","review_total":24,"review_used":0,"effort_total":48,"effort_used":0,"direction_check_count":0},"pending_direction_check":null,"idempotency_keys":[],"review_dispositions":[],"self_verifications":[]}
EOF

# Plan doc
mkdir -p docs/orchestrate/plans/e2e
cat > docs/orchestrate/plans/e2e/005-loop.md <<'EOF'
# Plan 005 E2E

## Pack Execution Manifest

| pack_id | title |
| --- | --- |
| 5.1 | first |
| 5.2 | second |
| 5.3 | third |
EOF

# Helper: reset execution-state for a fresh case
reset_state() {
  local verdict_target="$1"
  cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"plan_path":"docs/orchestrate/plans/e2e/005-loop.md","packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"},"5.3":{"status":"pending"}}}}}
EOF
  # Clean any existing plan-returns
  rm -rf "$BUDGET_DIR/plan-returns/$RUN_ID"
}

# Helper: simulate Worker pack commit + state mutation + track-execution-state hook
worker_commit_pack() {
  local pack_id="$1"
  # 1. Run TDD + verify (simulated). The Worker would have a real commit; here
  #    we make an empty commit to get a real SHA.
  git commit --allow-empty -q -m "Pack ${pack_id}: simulated"
  local sha
  sha=$(git rev-parse HEAD)

  # 2. Worker calls state.sh pack-progress
  bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "005" \
    --pack-id "$pack_id" --status committed --commit-sha "$sha" 2>/dev/null

  # 3. Simulate track-execution-state.sh hook firing (PostToolUse Bash on commit)
  local input
  input=$(jq -n --arg c "git commit -m \"Pack ${pack_id}: simulated\"" \
    '{tool_input:{command:$c},tool_response:{exit_code:0}}')
  echo "$input" | bash "$HOOKS_DIR/track-execution-state.sh" 2>&1
}

# Helper: write plan-return.json + run handler
worker_return() {
  local verdict="$1"
  shift
  local per_pack="{}"
  while [[ $# -gt 0 ]]; do
    local pid="$1" st="$2" sha="${3:-}"
    if [[ -n "$sha" ]]; then
      per_pack=$(echo "$per_pack" | jq --arg k "$pid" --arg s "$st" --arg sha "$sha" \
        '. + {($k):{status:$s, commit_sha:$sha}}')
    else
      per_pack=$(echo "$per_pack" | jq --arg k "$pid" --arg s "$st" \
        '. + {($k):{status:$s}}')
    fi
    shift 3
  done
  local prdir="$BUDGET_DIR/plan-returns/$RUN_ID/005"
  mkdir -p "$prdir"
  jq -n --arg v "$verdict" --argjson pp "$per_pack" \
    '{schema_version:"1",run_id:"e2e-test",plan_id:"005",verdict:$v,per_pack:$pp,doc_patch_path:"plan-returns/e2e-test/005/doc-patch.diff",open_items_path:"plan-returns/e2e-test/005/open-items.json"}' \
    > "$prdir/plan-return.json"
  # Doc-patch sentinel (Worker would write the real diff)
  echo "# sentinel" > "$prdir/doc-patch.diff"
  jq -n '{schema_version:"1",plan_id:"005",items:[]}' > "$prdir/open-items.json"

  # Mark Worker complete
  bash "$STATE_SH" execution-plan complete --run-id "$RUN_ID" --plan-id "005" \
    --verdict "$verdict" 2>/dev/null

  # Run agent-return-handler.sh (PostToolUse Agent on Worker return)
  local envelope
  envelope=$(jq -nc '{protocol_version:"1",run_id:"e2e-test",phase:"execution",agent_role:"plan-executor",repair_round:0,idempotency_key:"e2e-k1",plan_id:"005",pack_id:null,plan_path:"docs/orchestrate/plans/e2e/005-loop.md"}')
  local prompt="<!-- DISPATCH_ENVELOPE $envelope -->"
  local input
  input=$(jq -n --arg p "$prompt" \
    '{tool_name:"Agent",tool_input:{subagent_type:"pack-executor",prompt:$p},tool_response:"done"}')
  echo "$input" | bash "$HOOKS_DIR/agent-return-handler.sh" 2>&1
}

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

assert_contains() {
  local name="$1" haystack="$2" needle="$3"
  if echo "$haystack" | grep -q "$needle"; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name — expected substring '$needle' in: $haystack"
    fail=$((fail + 1))
  fi
}

echo "=== test_worker_loop_e2e.sh ==="

# ============================================================================
# Case 1: verdict=pass — 3 packs all committed
# ============================================================================
reset_state "pass"
# Worker claims plan
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "005" --agent-id "worker-1" 2>/dev/null

# Worker commits 3 packs
OUT1=$(worker_commit_pack "5.1")
OUT2=$(worker_commit_pack "5.2")
OUT3=$(worker_commit_pack "5.3")  # third commit triggers "all packs committed"

# NEXT suppression — worker_agent_id is set, so even at PLAN_DONE we expect "still in session"
assert_contains "track-execution-state: 3rd commit suppressed (worker active)" "$OUT3" "still in session"
# Bonus: no premature Review NEXT
if echo "$OUT3" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  FAIL: track-execution-state emitted premature Review NEXT"
  fail=$((fail + 1))
else
  echo "  PASS: no premature Review NEXT during Worker session"
  pass=$((pass + 1))
fi

# Worker writes plan-return.json and returns
SHA1=$(git log --format=%H | tail -3 | tail -1)
SHA2=$(git log --format=%H | tail -2 | head -1)
SHA3=$(git log --format=%H | head -1)
HANDLER_OUT=$(worker_return "pass" "5.1" "committed" "$SHA1" "5.2" "committed" "$SHA2" "5.3" "committed" "$SHA3")

assert_contains "pass: handler NEXT mentions Plan Implementation Review" "$HANDLER_OUT" "Plan Implementation Review"

# State validation
ESF="$BUDGET_DIR/execution-state-${RUN_ID}.json"
WV=$(jq -r '.plans["005"].worker_verdict' "$ESF")
FINISHED=$(jq -r '.plans["005"].finished_at' "$ESF")
assert_eq "pass: worker_verdict ingested" "$WV" "pass"
if [[ "$FINISHED" != "null" ]] && [[ -n "$FINISHED" ]]; then
  echo "  PASS: pass: finished_at populated"
  pass=$((pass + 1))
else
  echo "  FAIL: pass: finished_at not populated"
  fail=$((fail + 1))
fi

# Decision 6: doc-patch.diff NOT applied — file still exists in plan-returns/
if [[ -f "$BUDGET_DIR/plan-returns/$RUN_ID/005/doc-patch.diff" ]]; then
  echo "  PASS: doc-patch.diff still in plan-returns/ (Decision 6 — not applied at handler)"
  pass=$((pass + 1))
else
  echo "  FAIL: doc-patch.diff missing"
  fail=$((fail + 1))
fi

# ============================================================================
# Case 2: verdict=partial-pass — 2 committed, 1 blocked
# ============================================================================
reset_state "partial-pass"
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "005" --agent-id "worker-2" 2>/dev/null
HANDLER_OUT=$(worker_return "partial-pass" "5.1" "committed" "" "5.2" "committed" "" "5.3" "blocked" "")
WV=$(jq -r '.plans["005"].worker_verdict' "$ESF")
assert_eq "partial-pass: worker_verdict ingested" "$WV" "partial-pass"
S53=$(jq -r '.plans["005"].packs["5.3"].status' "$ESF")
assert_eq "partial-pass: 5.3 status blocked" "$S53" "blocked"
assert_contains "partial-pass: handler routes to Review" "$HANDLER_OUT" "Plan Implementation Review"

# ============================================================================
# Case 3: verdict=blocked
# ============================================================================
reset_state "blocked"
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "005" --agent-id "worker-3" 2>/dev/null
HANDLER_OUT=$(worker_return "blocked" "5.1" "blocked" "")
WV=$(jq -r '.plans["005"].worker_verdict' "$ESF")
assert_eq "blocked: worker_verdict ingested" "$WV" "blocked"
assert_contains "blocked: handler emits BLOCKED route" "$HANDLER_OUT" "BLOCKED"

# ============================================================================
# Case 4: verdict=need-fresh-worker
# ============================================================================
reset_state "need-fresh-worker"
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "005" --agent-id "worker-4" 2>/dev/null
HANDLER_OUT=$(worker_return "need-fresh-worker" "5.1" "committed" "")
WV=$(jq -r '.plans["005"].worker_verdict' "$ESF")
assert_eq "need-fresh-worker: worker_verdict ingested" "$WV" "need-fresh-worker"
assert_contains "need-fresh-worker: handler instructs new Agent" "$HANDLER_OUT" "NEW Agent"
assert_contains "need-fresh-worker: handler provides resume_from_pack_id" "$HANDLER_OUT" "resume_from_pack_id"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
