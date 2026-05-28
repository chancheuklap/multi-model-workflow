#!/usr/bin/env bash
# Plan 005 Pack 5.19: detect-worker-scope-drift.sh tests.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/detect-worker-scope-drift.sh"

WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

BUDGET_DIR=".claude/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="drift-test"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"
echo "005" > "$BUDGET_DIR/worker-active"

# Plan doc with owned_files for two packs
mkdir -p docs/orchestrate/plans/foo
cat > docs/orchestrate/plans/foo/005-bar.md <<'EOF'
# Plan 005

## Pack 5.1

### Owned files

- Edit: src/auth/login.py
- Create: src/auth/login_test.py

## Pack 5.2

### Owned files

- Edit: src/billing/charge.py
EOF

cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","plan_path":"docs/orchestrate/plans/foo/005-bar.md","packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"}}}}}
EOF

pass=0
fail=0

run_hook() {
  local fp="$1"
  local input
  input=$(jq -n --arg fp "$fp" '{tool_input:{file_path:$fp}}')
  echo "$input" | bash "$HOOK" 2>&1
}

drift_count() {
  jq '[.plans["005"].drift_warnings // []] | flatten | length' "$BUDGET_DIR/execution-state-${RUN_ID}.json"
}

echo "=== test_detect_worker_scope_drift.sh ==="

# Case 1: file in plan owned_files (Pack 5.1) → silent allow
OUT=$(run_hook "$WORKSPACE/src/auth/login.py")
CNT=$(drift_count)
if [[ -z "$OUT" ]] && [[ "$CNT" -eq 0 ]]; then
  echo "  PASS: in-scope edit (5.1 owned_file) silent + no drift_warning"
  pass=$((pass + 1))
else
  echo "  FAIL: in-scope edit produced output or drift (out: $OUT count: $CNT)"
  fail=$((fail + 1))
fi

# Case 2: file in another pack's owned_files (still in plan) → silent allow
OUT=$(run_hook "$WORKSPACE/src/billing/charge.py")
CNT=$(drift_count)
if [[ -z "$OUT" ]] && [[ "$CNT" -eq 0 ]]; then
  echo "  PASS: cross-pack same-plan edit (5.2 owned_file) silent"
  pass=$((pass + 1))
else
  echo "  FAIL: cross-pack same-plan edit produced output/drift (out: $OUT count: $CNT)"
  fail=$((fail + 1))
fi

# Case 3: file outside plan owned_files → WARN + drift_warning recorded
OUT=$(run_hook "$WORKSPACE/src/unrelated/module.py")
CNT=$(drift_count)
if echo "$OUT" | grep -q "scope drift"; then
  echo "  PASS: out-of-scope edit emits WARN"
  pass=$((pass + 1))
else
  echo "  FAIL: out-of-scope edit missing WARN (out: $OUT)"
  fail=$((fail + 1))
fi
if [[ "$CNT" -eq 1 ]]; then
  echo "  PASS: out-of-scope edit recorded as drift_warning"
  pass=$((pass + 1))
else
  echo "  FAIL: drift_warning not recorded (count: $CNT)"
  fail=$((fail + 1))
fi

# Case 4: hook does NOT exit non-zero (no BLOCK)
input=$(jq -n --arg fp "/var/random/x.py" '{tool_input:{file_path:$fp}}')
if echo "$input" | bash "$HOOK" >/dev/null 2>&1; then
  echo "  PASS: out-of-scope edit returns 0 (does not BLOCK)"
  pass=$((pass + 1))
else
  echo "  FAIL: hook returned non-zero (should never BLOCK)"
  fail=$((fail + 1))
fi

# Case 5: no worker-active marker → silent (Coordinator context)
rm -f "$BUDGET_DIR/worker-active"
OUT=$(run_hook "$WORKSPACE/anything.py")
if [[ -z "$OUT" ]]; then
  echo "  PASS: no worker-active marker → silent"
  pass=$((pass + 1))
else
  echo "  FAIL: hook emitted output without worker-active (out: $OUT)"
  fail=$((fail + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
