#!/usr/bin/env bash
# Plan 005 Pack 5.17: need-fresh-worker two-Worker continuation.
#
# Scenario: 5-Pack Plan executed across two Workers.
#   Worker 1: commits 3 packs (5.1, 5.2, 5.3), returns need-fresh-worker
#     with resume_from_pack_id=5.4.
#   Worker 2: claims plan, commits remaining 2 packs (5.4, 5.5), returns pass.
#
# Invariants under test:
#   A. After Worker 2 ingest, execution-state retains Worker 1's 3 committed
#      packs (per_pack merge is ADDITIVE, not clobbering). Decision 6 + ingest
#      merge guarantees this.
#   B. After Worker 2 ingest, worker_verdict = "pass" (Worker 2 supersedes
#      Worker 1's need-fresh-worker).
#   D. Worker 2's agent-id set overwrites worker_agent_id (Worker 1 released).
#   E. plan-returns ingest is idempotent — calling it twice with the same
#      Worker 2 plan-return.json doesn't double-count or corrupt state.
# NOTE: Invariant C (effort budget) removed — effort dimension deleted in P4.
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

BUDGET_DIR=".codex/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="continuation-test"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"
export STATE_BASE="$BUDGET_DIR"

# Workflow-state with budget
cat > "$BUDGET_DIR/workflow-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","attendance_mode":"afk","budget":{"budget_status":"initialized","review_total":24,"review_used":0,"review_credit":0,"budget_profile":"standard","override_count":0,"direction_check_count":0},"pending_direction_check":null,"idempotency_keys":[],"review_dispositions":[]}
EOF

# Plan doc
mkdir -p docs/orchestrate/plans/cont
cat > docs/orchestrate/plans/cont/006-cont.md <<'EOF'
# Plan 006

## Pack Execution Manifest

| pack_id | title |
| --- | --- |
| 6.1 | a |
| 6.2 | b |
| 6.3 | c |
| 6.4 | d |
| 6.5 | e |
EOF

# Execution-state with 5 pending packs
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"006":{"plan_path":"docs/orchestrate/plans/cont/006-cont.md","packs":{"6.1":{"status":"pending"},"6.2":{"status":"pending"},"6.3":{"status":"pending"},"6.4":{"status":"pending"},"6.5":{"status":"pending"}}}}}
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

echo "=== test_need_fresh_worker_continuation.sh ==="

ESF="$BUDGET_DIR/execution-state-${RUN_ID}.json"

# ============================================================================
# Worker 1 phase: claims plan, commits 3 packs, returns need-fresh-worker
# ============================================================================
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "006" --agent-id "worker-1" 2>/dev/null
W1_AGENT=$(jq -r '.plans["006"].worker_agent_id' "$ESF")
assert_eq "Worker 1 claims plan" "$W1_AGENT" "worker-1"

# Worker 1 commits 3 packs
for pid in 6.1 6.2 6.3; do
  git commit --allow-empty -q -m "Pack ${pid}: w1"
  sha=$(git rev-parse HEAD)
  bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "006" \
    --pack-id "$pid" --status committed --commit-sha "$sha" 2>/dev/null
done

S61=$(jq -r '.plans["006"].packs["6.1"].status' "$ESF")
S62=$(jq -r '.plans["006"].packs["6.2"].status' "$ESF")
S63=$(jq -r '.plans["006"].packs["6.3"].status' "$ESF")
assert_eq "Worker 1: 6.1 committed" "$S61" "committed"
assert_eq "Worker 1: 6.2 committed" "$S62" "committed"
assert_eq "Worker 1: 6.3 committed" "$S63" "committed"

# Worker 1 writes plan-return.json with verdict=need-fresh-worker
W1_DIR="$BUDGET_DIR/plan-returns/$RUN_ID/006"
mkdir -p "$W1_DIR"
SHA1=$(git log --format=%H | tail -1)
SHA2=$(git log --format=%H | tail -2 | head -1)
SHA3=$(git rev-parse HEAD)
jq -n --arg s1 "$SHA1" --arg s2 "$SHA2" --arg s3 "$SHA3" \
  '{schema_version:"1",run_id:"continuation-test",plan_id:"006",verdict:"need-fresh-worker",resume_from_pack_id:"6.4",per_pack:{"6.1":{status:"committed",commit_sha:$s1},"6.2":{status:"committed",commit_sha:$s2},"6.3":{status:"committed",commit_sha:$s3}}}' \
  > "$W1_DIR/plan-return.json"

bash "$STATE_SH" execution-plan complete --run-id "$RUN_ID" --plan-id "006" \
  --verdict "need-fresh-worker" 2>/dev/null
bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "006" 2>/dev/null

W1_VERDICT=$(jq -r '.plans["006"].worker_verdict' "$ESF")
assert_eq "Worker 1: worker_verdict = need-fresh-worker" "$W1_VERDICT" "need-fresh-worker"

# ============================================================================
# Worker 2 phase: claims plan (overwrites), commits 2 packs, returns pass
# ============================================================================
# Worker 2 claims — overwrites worker_agent_id
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "006" --agent-id "worker-2" 2>/dev/null
W2_AGENT=$(jq -r '.plans["006"].worker_agent_id' "$ESF")
assert_eq "Worker 2 overwrites worker_agent_id" "$W2_AGENT" "worker-2"

# But Worker 1's already-committed pack data should still be there
S61_STILL=$(jq -r '.plans["006"].packs["6.1"].status' "$ESF")
S62_STILL=$(jq -r '.plans["006"].packs["6.2"].status' "$ESF")
S63_STILL=$(jq -r '.plans["006"].packs["6.3"].status' "$ESF")
assert_eq "After Worker 2 claim: 6.1 still committed" "$S61_STILL" "committed"
assert_eq "After Worker 2 claim: 6.2 still committed" "$S62_STILL" "committed"
assert_eq "After Worker 2 claim: 6.3 still committed" "$S63_STILL" "committed"

# Worker 2 commits 2 packs
for pid in 6.4 6.5; do
  git commit --allow-empty -q -m "Pack ${pid}: w2"
  sha=$(git rev-parse HEAD)
  bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "006" \
    --pack-id "$pid" --status committed --commit-sha "$sha" 2>/dev/null
done

# Worker 2 writes its own plan-return (only 2 packs)
SHA4=$(git log --format=%H | tail -2 | head -1)
SHA5=$(git rev-parse HEAD)
jq -n --arg s4 "$SHA4" --arg s5 "$SHA5" \
  '{schema_version:"1",run_id:"continuation-test",plan_id:"006",verdict:"pass",per_pack:{"6.4":{status:"committed",commit_sha:$s4},"6.5":{status:"committed",commit_sha:$s5}}}' \
  > "$W1_DIR/plan-return.json"  # Overwrite (same plan-returns dir)

bash "$STATE_SH" execution-plan complete --run-id "$RUN_ID" --plan-id "006" \
  --verdict "pass" 2>/dev/null
bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "006" 2>/dev/null

# ============================================================================
# INVARIANT A: Worker 1's 3 packs NOT clobbered after Worker 2 ingest
# ============================================================================

S61_FINAL=$(jq -r '.plans["006"].packs["6.1"].status' "$ESF")
S62_FINAL=$(jq -r '.plans["006"].packs["6.2"].status' "$ESF")
S63_FINAL=$(jq -r '.plans["006"].packs["6.3"].status' "$ESF")
S64_FINAL=$(jq -r '.plans["006"].packs["6.4"].status' "$ESF")
S65_FINAL=$(jq -r '.plans["006"].packs["6.5"].status' "$ESF")
assert_eq "Invariant A: 6.1 retained after Worker 2 ingest" "$S61_FINAL" "committed"
assert_eq "Invariant A: 6.2 retained after Worker 2 ingest" "$S62_FINAL" "committed"
assert_eq "Invariant A: 6.3 retained after Worker 2 ingest" "$S63_FINAL" "committed"
assert_eq "Invariant A: 6.4 ingested from Worker 2" "$S64_FINAL" "committed"
assert_eq "Invariant A: 6.5 ingested from Worker 2" "$S65_FINAL" "committed"

# Worker 1's commit_sha for 6.1 should be preserved (not overwritten)
SHA61=$(jq -r '.plans["006"].packs["6.1"].commit_sha' "$ESF")
assert_eq "Invariant A: 6.1 commit_sha preserved (Worker 1's)" "$SHA61" "$SHA1"

# ============================================================================
# INVARIANT B: worker_verdict = pass (Worker 2 supersedes)
# ============================================================================
FINAL_VERDICT=$(jq -r '.plans["006"].worker_verdict' "$ESF")
assert_eq "Invariant B: worker_verdict updated to pass" "$FINAL_VERDICT" "pass"

# ============================================================================
# INVARIANT E: Idempotency — ingest twice should not corrupt
# ============================================================================
bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "006" 2>/dev/null
S64_AGAIN=$(jq -r '.plans["006"].packs["6.4"].status' "$ESF")
VERDICT_AGAIN=$(jq -r '.plans["006"].worker_verdict' "$ESF")
PACK_COUNT=$(jq '.plans["006"].packs | length' "$ESF")
assert_eq "Invariant E: 6.4 status unchanged on second ingest" "$S64_AGAIN" "committed"
assert_eq "Invariant E: worker_verdict unchanged on second ingest" "$VERDICT_AGAIN" "pass"
assert_eq "Invariant E: pack count unchanged (5 packs)" "$PACK_COUNT" "5"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
