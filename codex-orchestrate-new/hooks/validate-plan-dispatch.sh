#!/usr/bin/env bash
# Plan 005 Pack 5.8: validate-plan-dispatch.sh (renamed + rewritten from
# validate-pack-dispatch.sh).
#
# PreToolUse hook for subagent (pack_executor / complex_pack_executor) — gates a
# Plan-level Worker dispatch in autonomous mode. New rules vs the legacy hook:
#
#   1. envelope.plan_id non-empty (Plan-level dispatch contract)
#   2. envelope.plan_path resolves to an existing file
#   3. plan.md contains "## Pack Execution Manifest" with at least one pack row
#   4. envelope.run_id matches workflow-state active run_id
#
# Execution dispatch is plan-level ONLY: phase==execution requires plan_id non-empty
# and pack_id null (Step 5b hard-blocks any per-pack execution dispatch). Non-execution
# route-worker phases (bug-investigation / direct-repair / multi-pr-merge) carry
# plan_id=null + pack_id=null and pass through untouched.
# Repair Mode uses send_input, which does not fire this PreToolUse subagent hook.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"
STATE_SH="$SCRIPT_DIR/../scripts/state.sh"
# Source routes library (fail-open if unavailable) —— 裸 source 在 set -e 下,
# routes.sh 缺失会让脚本 rc=1 退出,PreToolUse 非 2 即放行未校验的派发(fail-open)。
# shellcheck source=lib/routes.sh
if [[ -f "$SCRIPT_DIR/lib/routes.sh" ]]; then
  source "$SCRIPT_DIR/lib/routes.sh"
else
  routes_manifest_readable() { return 1; }
  routes_dispatch_shape() { echo ""; }
fi

# Step 1: parse envelope
PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then exit 0; fi

ENVELOPE=$(echo "$PROMPT" | bash "$PARSE_ENVELOPE" 2>/dev/null) || {
  echo "[multi-model-workflow] BLOCKED: DISPATCH_ENVELOPE missing or malformed." >&2
  exit 2
}

# Step 2: pull fields
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id')
PLAN_ID=$(echo "$ENVELOPE" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
PLAN_PATH=$(echo "$ENVELOPE" | jq -r '.plan_path // empty')
REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key')
AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role')
PHASE=$(echo "$ENVELOPE" | jq -r '.phase // empty')

BUDGET_DIR=".codex/multi-model-workflow"

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [[ ! -f "$SF" ]]; then exit 0; fi

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"

# Step 3: read-only idempotency check (exit 2 if key exists)
EXISTING=$(jq -r --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys | index($key) // empty' "$SF")
if [[ -n "$EXISTING" ]]; then
  echo "[multi-model-workflow] BLOCKED: duplicate dispatch (idempotency_key=$IDEMPOTENCY_KEY)." >&2
  exit 2
fi

# Step 4: budget initialized
BUDGET_STATUS=$(jq -r '.budget.budget_status // "unknown"' "$SF")
if [[ "$BUDGET_STATUS" == "pending_plan_count" ]]; then
  echo "[multi-model-workflow] BLOCKED: budget not initialized. Run 'state.sh budget initialize --plan-count N' first." >&2
  exit 2
fi

# Step 5: pending Direction Check
DC=$(jq -r '.pending_direction_check.ack_status // empty' "$SF")
if [[ "$DC" == "pending" ]]; then
  if [[ "$AGENT_ROLE" != "codex_reviewer" ]]; then
    echo "[multi-model-workflow] BLOCKED: Direction Check pending." >&2
    exit 2
  fi
fi

# Step 5b: plan-level dispatch phases MUST be plan-level (legacy pack-level path removed).
# Machine source: routes-v1.json[route].dispatch_shape[PHASE] == "plan-level".
# Fail-open: if the manifest is unreadable or yields no shape, fall back to the
# legacy literal PHASE == "execution".
ROUTE=$(jq -r '.route // empty' "$SF" 2>/dev/null)
DISPATCH_SHAPE=$(routes_dispatch_shape "$ROUTE" "$PHASE")
IS_PLAN_LEVEL=false
if [[ -n "$DISPATCH_SHAPE" ]]; then
  [[ "$DISPATCH_SHAPE" == "plan-level" ]] && IS_PLAN_LEVEL=true
else
  [[ "$PHASE" == "execution" ]] && IS_PLAN_LEVEL=true
fi

if [[ "$IS_PLAN_LEVEL" == "true" ]]; then
  if [[ -z "$PLAN_ID" || "$PLAN_ID" == "null" ]]; then
    echo "[multi-model-workflow] BLOCKED: execution dispatch must be plan-level — envelope.plan_id is empty. Per-pack execution dispatch is no longer supported; dispatch one autonomous Worker per Plan (set plan_id, leave pack_id null)." >&2
    exit 2
  fi
  if [[ -n "$PACK_ID" && "$PACK_ID" != "null" ]]; then
    echo "[multi-model-workflow] BLOCKED: execution dispatch must leave pack_id null (plan-level autonomous Worker owns the whole Plan). Per-pack execution dispatch is no longer supported." >&2
    exit 2
  fi
fi

# Step 6: PLAN-LEVEL dispatch gate (Plan 005)
# When envelope carries plan_id, this is autonomous-mode Worker — extra checks.
if [[ -n "$PLAN_ID" && "$PLAN_ID" != "null" ]]; then
  # plan_path must resolve
  if [[ -z "$PLAN_PATH" || ! -f "$PLAN_PATH" ]]; then
    echo "[multi-model-workflow] BLOCKED: envelope.plan_id=$PLAN_ID but plan_path missing or not a file: '$PLAN_PATH'." >&2
    exit 2
  fi

  # plan.md should contain Pack Execution Manifest (D9 降级: WARN instead of BLOCK)
  if ! grep -q '## Pack Execution Manifest' "$PLAN_PATH"; then
    echo "[multi-model-workflow] WARN: plan $PLAN_ID at $PLAN_PATH missing '## Pack Execution Manifest' — Worker may work from plan body. (D9 降级)" >&2
    # 不 exit 2，继续后续 step
  fi

  # plans entry exists in execution-state
  if [[ -f "$ESF" ]] && ! jq -e --arg pid "$PLAN_ID" '.plans[$pid] != null' "$ESF" >/dev/null 2>&1; then
    echo "[multi-model-workflow] BLOCKED: plan_id $PLAN_ID has no entry in execution-state. Coordinator must run 'state.sh execution-plan start --plan-id $PLAN_ID --start-commit <sha>' first." >&2
    exit 2
  fi

  # plan is not already in_progress with a different worker
  # （Codex 路径看 worker_agent_id；Codex 路径看 session_id——修复轮必须
  #   send_input resume 续会话，不得重新 dispatch 开新 session）
  if [[ -f "$ESF" ]]; then
    EXISTING_WID=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].worker_agent_id // empty' "$ESF" 2>/dev/null)
    EXISTING_SID=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].session_id // empty' "$ESF" 2>/dev/null)
    PLAN_STATUS=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].status // empty' "$ESF" 2>/dev/null)
    RESUME_FROM=$(echo "$ENVELOPE" | jq -r '.resume_from_pack_id // empty' 2>/dev/null)
    if [[ "$PLAN_STATUS" == "in_progress" && -z "$RESUME_FROM" ]]; then
      if [[ -n "$EXISTING_WID" && "$EXISTING_WID" != "null" ]]; then
        echo "[multi-model-workflow] BLOCKED: plan $PLAN_ID already in_progress with worker $EXISTING_WID. Use send_input to resume." >&2
        exit 2
      fi
      if [[ -n "$EXISTING_SID" && "$EXISTING_SID" != "null" ]]; then
        echo "[multi-model-workflow] BLOCKED: plan $PLAN_ID already in_progress with codex session $EXISTING_SID. Use send_input resume（修复轮续会话），need-fresh-worker 续派须带 resume_from_pack_id。" >&2
        exit 2
      fi
    fi
  fi
fi

# (Step 7 removed: per-pack execution dispatch gating no longer exists — execution is
# plan-level only. The plan-level "already in_progress with worker" guard in Step 6 is
# the agent_id re-dispatch guard. Repair resumes the plan Worker via send_input.)

# Step 9: Disposition refs validation for repair dispatch (repair_round >= 1)
if [[ "$REPAIR_ROUND" -ge 1 ]] 2>/dev/null; then
  DISP_REFS=$(echo "$ENVELOPE" | jq -r '.disposition_refs // [] | .[]' 2>/dev/null)
  for ref in $DISP_REFS; do
    FOUND_DISP=$(jq -r --arg fid "$ref" '.review_dispositions[] | select(.finding_id == $fid) | .disposition' "$SF" 2>/dev/null)
    if [[ "$FOUND_DISP" != "accepted" ]]; then
      echo "[multi-model-workflow] BLOCKED: finding $ref not accepted in review_dispositions." >&2
      exit 2
    fi
    FOUND_EV=$(jq -r --arg fid "$ref" '.review_dispositions[] | select(.finding_id == $fid) | .evidence // ""' "$SF" 2>/dev/null)
    if [[ -z "$FOUND_EV" || "$FOUND_EV" == "null" ]]; then
      echo "[multi-model-workflow] BLOCKED: finding $ref has no evidence." >&2
      exit 2
    fi
  done
fi

# Step 10: mutating idempotency append
export STATE_BASE="$BUDGET_DIR"
bash "$STATE_SH" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY" 2>/dev/null || true

# Step 11: Plan-level dispatch — plans[N].status moves to in_progress when the Worker
# first calls `state.sh agent-id set --plan-id`. We don't pre-mutate here to avoid
# races. (Pack-level status mutation removed: execution is plan-level only.)

exit 0
