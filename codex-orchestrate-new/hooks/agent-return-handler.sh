#!/usr/bin/env bash
# SubagentStop hook / legacy synthetic PostToolUse hook for Codex subagents.
#
# Plan 005 Pack 5.9: structural rewrite for Plan-level Worker autonomous mode.
# Handles plan-level returns (envelope.plan_id non-empty); non-plan-level returns
# (route-worker phases) are a graceful no-op. Pack-level execution returns removed.
#
# Plan-level flow (envelope.plan_id non-empty):
#   1. Parse envelope → extract plan_id + run_id
#   2. Read ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json
#   3. Call `state.sh plan-returns ingest` → write per_pack + worker_verdict
#   4. Route by verdict (5 routes):
#        pass / partial-pass → NEXT: Dispatch Plan Implementation Review
#        blocked            → NEXT: BLOCKED, coordinator triage
#        need-fresh-worker  → NEXT: dispatch new subagent with resume_from_pack_id
#        needs-plan-revision → NEXT: route to plan-writing for revision
#   5. Failure to parse / missing artifact → BLOCKED with explicit message.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../scripts/state.sh"

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // .hook_event_name // .hookEventName // empty' 2>/dev/null)
case "$TOOL_NAME" in
  subagent|spawn_agent|SubagentStop|"") ;;
  *) exit 0 ;;
esac

AGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.agent_type // .tool_input.agent_type // .agent_type // .agent_type // empty' 2>/dev/null)
case "$AGENT_TYPE" in
  pack_executor|complex_pack_executor|"") ;;
  *) exit 0 ;;
esac

BUDGET_DIR=".codex/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // .tool_input.message // .prompt // .message // empty' 2>/dev/null)
if [[ -z "$PROMPT" || "$PROMPT" == "null" ]]; then
  exit 0
fi
ENVELOPE=$(echo "$PROMPT" | bash "$SCRIPT_DIR/lib/parse-envelope.sh" 2>/dev/null) || {
  echo "[multi-model-workflow] WARN: agent return without DISPATCH_ENVELOPE, skipping state tracking" >&2
  exit 0
}

PLAN_ID=$(echo "$ENVELOPE" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"

emit_next() {
  local msg="$1"
  echo "⚠️ 写入交付物前必须校验本次返回的事实声明（行号 / 计数 / 存在性 / grep 结果 / 引用关系）" >&2
  jq -n --arg msg "$msg" \
    '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
}

# ============================================================================
# PLAN-LEVEL RETURN (Plan 005)
# ============================================================================
if [ -n "$PLAN_ID" ] && [ "$PLAN_ID" != "null" ]; then
  PR_FILE="${BUDGET_DIR}/plan-returns/${RUN_ID}/${PLAN_ID}/plan-return.json"

  if [ ! -f "$PR_FILE" ]; then
    emit_next "[multi-model-workflow] BLOCKED: plan-return.json missing for plan ${PLAN_ID} at ${PR_FILE}. Worker may have crashed mid-execution. Coordinator: inspect Worker session output, then either re-dispatch or mark plan blocked manually."
    exit 0
  fi

  if ! jq empty "$PR_FILE" 2>/dev/null; then
    emit_next "[multi-model-workflow] BLOCKED: plan-return.json at ${PR_FILE} is not valid JSON. Coordinator: inspect file + re-dispatch."
    exit 0
  fi

  # Use the parser lib for verdict extraction (Pack 5.15)
  # shellcheck source=../scripts/lib/plan-return-parser.sh
  source "$SCRIPT_DIR/../scripts/lib/plan-return-parser.sh"
  if ! parse_plan_return "$PR_FILE"; then
    emit_next "[multi-model-workflow] BLOCKED: plan-return.json failed schema validation. Inspect ${PR_FILE} for malformed verdict / schema_version / missing per_pack."
    exit 0
  fi

  VERDICT="$PLAN_RETURN_VERDICT"

  # Ingest into execution-state (writes per_pack + worker_verdict + finished_at)
  export STATE_BASE="$BUDGET_DIR"
  if ! bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "$PLAN_ID" 2>/dev/null; then
    emit_next "[multi-model-workflow] BLOCKED: state.sh plan-returns ingest failed for plan ${PLAN_ID}. Inspect plan-return.json structure."
    exit 0
  fi

  # Find the next pack to resume from (for need-fresh-worker)
  NEXT_PACK=""
  if [ -f "$ESF" ]; then
    NEXT_PACK=$(jq -r --arg pid "$PLAN_ID" \
      '[.plans[$pid].packs | to_entries[] | select(.value.status != "committed" and .value.status != "skipped") | .key] | sort | first // empty' \
      "$ESF" 2>/dev/null || echo "")
  fi

  # Route by verdict (5 routes)
  case "$VERDICT" in
    pass)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} verdict=pass. Dispatch Plan Implementation Review. After review pass, toggle committed-pack checkboxes per execution SKILL Step 14."
      ;;
    partial-pass)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} verdict=partial-pass (${PLAN_RETURN_COMMITTED_COUNT} committed, ${PLAN_RETURN_BLOCKED_COUNT} blocked). Dispatch Plan Implementation Review on committed packs; open-items.json has blocked reasoning. Toggle committed checkboxes per execution SKILL Step 14."
      ;;
    blocked)
      emit_next "[multi-model-workflow] BLOCKED: Plan ${PLAN_ID} verdict=blocked. Read plan-return.json per_pack[].reason + open-items.json; decide send_input repair / re-plan / abort."
      ;;
    need-fresh-worker)
      if [ -n "$NEXT_PACK" ]; then
        emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} verdict=need-fresh-worker (context pressure, ${PLAN_RETURN_COMMITTED_COUNT} committed, next=${NEXT_PACK}). Dispatch NEW subagent (not send_input) with envelope.resume_from_pack_id=${NEXT_PACK}; it skips committed packs."
      else
        emit_next "[multi-model-workflow] WARN: Plan ${PLAN_ID} need-fresh-worker but no remaining pack; effective pass. Dispatch Plan Implementation Review."
      fi
      ;;
    needs-context)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} verdict=needs-context. Fetch missing Contract anchors / Mockup specs / verification, augment plan, re-dispatch."
      ;;
    needs-plan-revision)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} verdict=needs-plan-revision (plan doc missing required fields). Route to plan-writing for revision; re-dispatch Worker after fix + re-review."
      ;;
    *)
      emit_next "[multi-model-workflow] BLOCKED: Plan ${PLAN_ID} unknown verdict '${VERDICT}'. Inspect plan-return.json."
      ;;
  esac

  exit 0
fi

# Non-plan-level returns (route-worker / bug-investigation / direct-repair / etc.)
# carry no plan_id. Pack-level execution return handling has been removed —
# execution is plan-level only (one autonomous Worker per Plan). Those phases manage
# their own return handling, so this is a graceful no-op.
exit 0
