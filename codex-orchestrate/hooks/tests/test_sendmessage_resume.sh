#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../../scripts/state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_sendmessage_resume.sh ==="

RUN_ID="test-sendmsg"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "test" --route "formal" >/dev/null

# Create execution-state with agent_id
cat > "$FIXTURE_DIR/execution-state-${RUN_ID}.json" <<'EOF'
{"run_id":"test-sendmsg","plans":{"001":{"packs":{"1.1":{"status":"returned","agent_id":"agent-abc","commit_sha":"abc123","worker_verdict":"pass"},"1.2":{"status":"pending","agent_id":null,"commit_sha":null,"worker_verdict":null}}}}}
EOF

# 1. agent_id present -> get returns value
run_test "agent-id get returns value when present" \
  bash -c "[[ \$(bash '$STATE_SH' agent-id get --run-id '$RUN_ID' --pack-id '1.1') == 'agent-abc' ]]"

# 2. agent_id null -> get returns empty
run_test "agent-id get returns empty when null" \
  bash -c "[[ -z \$(bash '$STATE_SH' agent-id get --run-id '$RUN_ID' --pack-id '1.2') ]]"

# 3. Verify agent_id existence is detectable for guard
run_test "agent_id exists is detectable" \
  bash -c "EXISTING=\$(jq -r --arg pid '1.1' '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == \$pid) | .value.agent_id // empty] | first // empty' '$FIXTURE_DIR/execution-state-${RUN_ID}.json'); [[ \"\$EXISTING\" == 'agent-abc' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
