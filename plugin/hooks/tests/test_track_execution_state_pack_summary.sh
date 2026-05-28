#!/usr/bin/env bash
# Pack 2.10: track-execution-state.sh aggregates pack-returns into
# execution-state.plans[N].pack_summary on PLAN_DONE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SH="$(cd "$SCRIPT_DIR/.." && pwd)/track-execution-state.sh"

pass=0
fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass + 1))
  else echo "  FAIL: $name"; fail=$((fail + 1)); fi
}

echo "=== test_track_execution_state_pack_summary.sh ==="

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

# Set up a fake git repo so `git rev-parse HEAD` returns a real sha.
cd "$WORKDIR"
git init -q
git config user.email test@example.com
git config user.name test
echo init > seed.txt
git add seed.txt
git commit -qm "initial"

RUN_ID="test-pack-summary-001"
BUDGET_DIR="$WORKDIR/.claude/multi-model-workflow"
mkdir -p "$BUDGET_DIR/pack-returns/$RUN_ID"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

# Create execution-state with two packs in plan 001
cat > "$BUDGET_DIR/execution-state-$RUN_ID.json" <<ESJSON
{
  "run_id": "$RUN_ID",
  "plans": {
    "001": {
      "packs": {
        "1.1": { "status": "committed", "commit_sha": "abc1" },
        "1.2": { "status": "pending", "commit_sha": null }
      }
    }
  }
}
ESJSON

# Pack-return files
cat > "$BUDGET_DIR/pack-returns/$RUN_ID/1.1.json" <<'PRJ'
{ "pack_id": "1.1", "verdict": "pass", "changed_files": ["a.py"], "open_items": [] }
PRJ

cat > "$BUDGET_DIR/pack-returns/$RUN_ID/1.2.json" <<'PRJ'
{ "pack_id": "1.2", "verdict": "pass", "changed_files": ["b.py"], "open_items": [{"tag":"out-of-scope","summary":"x"}] }
PRJ

# Simulate a Pack 1.2 commit by appending a file and creating a commit
echo p2 > p2.txt
git add p2.txt
git commit -qm "Pack 1.2: finish"
COMMIT_SHA=$(git rev-parse HEAD)

# Build the hook input JSON
HOOK_INPUT=$(jq -nc --arg cmd "git commit -m \"Pack 1.2: finish\"" \
  '{tool_input: {command: $cmd}, tool_response: {exit_code: 0}}')

# Pre-mark 1.2 as committed in execution-state (the hook normally does this for the
# pack-id parsed from the commit message; we leave it to the hook by passing the
# commit message via tool_input).
echo "$HOOK_INPUT" | bash "$HOOK_SH" >/dev/null 2>&1 || true

run_test "execution-state has pack_summary array for plan 001" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].pack_summary | type' '$BUDGET_DIR/execution-state-$RUN_ID.json') == 'array' ]]"

run_test "pack_summary contains two entries (one per pack)" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].pack_summary | length' '$BUDGET_DIR/execution-state-$RUN_ID.json') == '2' ]]"

run_test "pack_summary entry preserves pack_id 1.1" \
  bash -c "jq -e '.plans[\"001\"].pack_summary | map(.pack_id) | contains([\"1.1\"])' '$BUDGET_DIR/execution-state-$RUN_ID.json'"

run_test "pack_summary entry preserves verdict pass" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].pack_summary[0].verdict' '$BUDGET_DIR/execution-state-$RUN_ID.json') == 'pass' ]]"

run_test "end_commit recorded" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].end_commit' '$BUDGET_DIR/execution-state-$RUN_ID.json') == '$COMMIT_SHA' ]]"

# Idempotency: re-running the hook with the same context should not duplicate entries.
echo "$HOOK_INPUT" | bash "$HOOK_SH" >/dev/null 2>&1 || true
run_test "pack_summary remains length 2 after re-run (idempotent)" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].pack_summary | length' '$BUDGET_DIR/execution-state-$RUN_ID.json') == '2' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
