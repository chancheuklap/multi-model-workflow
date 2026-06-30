#!/usr/bin/env bash
# Pack 2.9: complete-review-dispatch.sh auto-appends Review History rows when the
# gate name matches design-review-* or plan-review-* patterns.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_SCRIPTS="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPLETE_SH="${PLUGIN_SCRIPTS}/complete-review-dispatch.sh"
STATE_SH="${PLUGIN_SCRIPTS}/state.sh"

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

pass=0
fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass + 1))
  else echo "  FAIL: $name"; fail=$((fail + 1)); fi
}
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail + 1))
  else echo "  PASS: $name (expected failure)"; pass=$((pass + 1)); fi
}

echo "=== test_complete_review_dispatch_history.sh ==="

RUN_ID="test-rh-hook-001"
SLUG="rh-hook"
export STATE_BASE="$WORKDIR/.claude/multi-model-workflow"
mkdir -p "$STATE_BASE/review-registry" "$STATE_BASE/review-results"

# Init state so .slug is resolvable
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "$SLUG" --route formal

# Seed design and plan files (path is relative to cwd at hook-call time).
mkdir -p "$WORKDIR/docs/orchestrate/design"
mkdir -p "$WORKDIR/docs/orchestrate/plans/$SLUG"

cat > "$WORKDIR/docs/orchestrate/design/$SLUG.md" <<'DOCEOF'
# RH Hook Test

## Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |

## Other section
DOCEOF

cat > "$WORKDIR/docs/orchestrate/plans/$SLUG/001-foo.md" <<'DOCEOF'
# Plan 001

## Plan Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |

## Pack Execution Manifest
DOCEOF

# Seed review registry + result for design review gate
GATE_DESIGN="design-review-content-1"
RESULT_DESIGN="$STATE_BASE/review-results/$GATE_DESIGN.md"
cat > "$RESULT_DESIGN" <<'RESEOF'
# Review result

### Verdict
pass

### Evidence
something
RESEOF

cat > "$STATE_BASE/review-registry/$GATE_DESIGN.json" <<RREOF
{
  "run_id": "$RUN_ID",
  "gate": "$GATE_DESIGN",
  "agent_id": "job-design",
  "status": "dispatched",
  "completed_at": null,
  "result_file": null
}
RREOF

# Run hook from the workdir (so relative docs paths resolve)
run_test "complete-review-dispatch on design gate succeeds" \
  bash -c "cd '$WORKDIR' && STATE_BASE='$STATE_BASE' bash '$COMPLETE_SH' --run-id '$RUN_ID' --gate '$GATE_DESIGN' --agent-id 'job-design' --result-file '$RESULT_DESIGN'"

run_test "design Review History row appended" \
  bash -c "grep -F '| 1 | pass | job-design |' '$WORKDIR/docs/orchestrate/design/$SLUG.md'"

# Plan review gate (gate name convention: plan-review-<plan_id>-...)
GATE_PLAN="plan-review-001-coverage-1"
RESULT_PLAN="$STATE_BASE/review-results/$GATE_PLAN.md"
cat > "$RESULT_PLAN" <<'RESEOF'
# Review result

### Verdict
needs repair

### Evidence
plan coverage gaps
RESEOF

cat > "$STATE_BASE/review-registry/$GATE_PLAN.json" <<RREOF
{
  "run_id": "$RUN_ID",
  "gate": "$GATE_PLAN",
  "agent_id": "job-plan",
  "status": "dispatched",
  "completed_at": null,
  "result_file": null
}
RREOF

run_test "complete-review-dispatch on plan gate succeeds" \
  bash -c "cd '$WORKDIR' && STATE_BASE='$STATE_BASE' bash '$COMPLETE_SH' --run-id '$RUN_ID' --gate '$GATE_PLAN' --agent-id 'job-plan' --result-file '$RESULT_PLAN'"

run_test "plan Review History row appended with parsed verdict" \
  bash -c "grep -F '| 1 | needs repair | job-plan |' '$WORKDIR/docs/orchestrate/plans/$SLUG/001-foo.md'"

# Unrelated gate name does NOT trigger append (and does not fail).
GATE_OTHER="execution-something-1"
RESULT_OTHER="$STATE_BASE/review-results/$GATE_OTHER.md"
cat > "$RESULT_OTHER" <<'RESEOF'
### Verdict
pass
RESEOF
cat > "$STATE_BASE/review-registry/$GATE_OTHER.json" <<RREOF
{ "run_id": "$RUN_ID", "gate": "$GATE_OTHER", "agent_id": "job-other", "status": "dispatched", "completed_at": null, "result_file": null }
RREOF
run_test "complete-review-dispatch on non-review gate still succeeds" \
  bash -c "cd '$WORKDIR' && STATE_BASE='$STATE_BASE' bash '$COMPLETE_SH' --run-id '$RUN_ID' --gate '$GATE_OTHER' --agent-id 'job-other' --result-file '$RESULT_OTHER'"

# No extra row in design or plan from the unrelated gate.
# After the design append (1 data row) plus 2 header lines, there should be exactly 3 |-prefix lines.
# An unrelated gate must not add another.
run_test "unrelated gate did not touch design file" \
  bash -c "[[ \$(grep -c '^|' '$WORKDIR/docs/orchestrate/design/$SLUG.md') -eq 3 ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
