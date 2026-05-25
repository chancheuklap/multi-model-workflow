#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_sendmessage_resume_injection.sh ==="

# Verify send_input Resume content in repair references
run_test "send_input in final-review-repair" \
  grep -q "send_input Resume" "$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md"

run_test "send_input in execution-repair-truncation" \
  grep -q "send_input Resume" "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-repair-truncation.md"

run_test "send_input in plan-review-resolution" \
  grep -q "send_input Resume" "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"

run_test "resume template resumes existing worker" \
  grep -q "resume_agent" "$PLUGIN_DIR/build/templates/sendmessage-resume.md.tmpl"

run_test "worker repair closes completed agent" \
  grep -Fq 'close_agent({ target: "<agent_id>" })' "$PLUGIN_DIR/skills/orchestrate-execution/references/execution-repair-truncation.md"

run_test "plan writer repair closes completed agent" \
  grep -Fq 'close_agent({ target: "<plan_writer_agent_id>" })' "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-review-resolution.md"

# Verify Path B keeps continuation on the existing agent.
run_test "no fresh subagent dispatch in final-review Path B" \
  bash -c "! grep -A3 '路径 B' '$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md' | grep -q 'spawn_agent({'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
