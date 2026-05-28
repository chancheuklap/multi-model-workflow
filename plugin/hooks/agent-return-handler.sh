#!/usr/bin/env bash
# PostToolUse hook for Agent tool.
#
# Plan 005 Pack 5.9: structural rewrite for Plan-level Worker autonomous mode.
# Handles BOTH legacy pack-level returns (no plan_id) and new plan-level returns.
#
# Plan-level flow (envelope.plan_id non-empty):
#   1. Parse envelope → extract plan_id + run_id
#   2. Read ${STATE_DIR}/plan-returns/<run_id>/<plan_id>/plan-return.json
#   3. Call `state.sh plan-returns ingest` → write per_pack + worker_verdict
#   4. Route by verdict (5 routes):
#        pass / partial-pass → NEXT: Dispatch Plan Implementation Review
#          (doc-patch NOT applied here — Decision 6: applied by Coordinator AFTER review pass)
#        blocked            → NEXT: BLOCKED, coordinator triage
#        need-fresh-worker  → NEXT: dispatch new Agent with resume_from_pack_id
#        needs-plan-revision → NEXT: route to plan-writing for revision
#   5. Failure to parse / missing artifact → BLOCKED with explicit message.
#
# Legacy pack-level fallback retained for transitional Repair Mode dispatches
# that still ship via pack_id envelopes.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../scripts/state.sh"

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
if [ "$TOOL_NAME" != "Agent" ]; then exit 0; fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty' 2>/dev/null)
case "$AGENT_TYPE" in
  pack-executor|complex-pack-executor) ;;
  *) exit 0 ;;
esac

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [ ! -f "$SF" ]; then exit 0; fi

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
ENVELOPE=$(echo "$PROMPT" | bash "$SCRIPT_DIR/lib/parse-envelope.sh" 2>/dev/null) || {
  echo "[multi-model-workflow] WARN: agent return without DISPATCH_ENVELOPE, skipping state tracking" >&2
  exit 0
}

PLAN_ID=$(echo "$ENVELOPE" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"

emit_next() {
  local msg="$1"
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

  # NOTE: doc-patch.diff is NOT applied here (Decision 6).
  # Coordinator applies after Plan Implementation Review passes (orchestrate-execution Step 14).

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
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} Worker returned verdict=pass. Dispatch Plan Implementation Review (Codex). doc-patch.diff at ${BUDGET_DIR}/plan-returns/${RUN_ID}/${PLAN_ID}/doc-patch.diff is STAGED for apply AFTER review pass (Decision 6 — do NOT git apply now)."
      ;;
    partial-pass)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} Worker returned verdict=partial-pass (${PLAN_RETURN_COMMITTED_COUNT} committed, ${PLAN_RETURN_BLOCKED_COUNT} blocked). Dispatch Plan Implementation Review against committed packs. open-items.json carries blocked-pack reasoning. doc-patch.diff stays in plan-returns/ until review pass."
      ;;
    blocked)
      emit_next "[multi-model-workflow] BLOCKED: Plan ${PLAN_ID} Worker returned verdict=blocked. Coordinator: read plan-return.json per_pack[].reason + open-items.json for diagnosis. Decide SendMessage repair / re-plan / abort. doc-patch.diff NOT applied."
      ;;
    need-fresh-worker)
      if [ -n "$NEXT_PACK" ]; then
        emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} Worker returned verdict=need-fresh-worker (context pressure). ${PLAN_RETURN_COMMITTED_COUNT} packs committed; ${NEXT_PACK} is next. Coordinator: dispatch NEW Agent (not SendMessage — same session won't help) with envelope.resume_from_pack_id=${NEXT_PACK}. New Worker will skip committed packs via partial-fail recovery."
      else
        emit_next "[multi-model-workflow] WARN: Plan ${PLAN_ID} verdict=need-fresh-worker but no remaining pack found; effective verdict is pass. Dispatch Plan Implementation Review."
      fi
      ;;
    needs-context)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} Worker returned verdict=needs-context. Coordinator: fetch missing Contract anchors / Mockup specs / verification commands, augment plan, then re-dispatch. doc-patch.diff NOT applied."
      ;;
    needs-plan-revision)
      emit_next "[multi-model-workflow] NEXT: Plan ${PLAN_ID} Worker returned verdict=needs-plan-revision (plan doc missing required fields). Route back to plan-writing for revision. After plan-writer fix + re-review, re-dispatch this Worker. doc-patch.diff NOT applied."
      ;;
    *)
      emit_next "[multi-model-workflow] BLOCKED: Plan ${PLAN_ID} Worker returned unknown verdict '${VERDICT}'. Inspect plan-return.json."
      ;;
  esac

  exit 0
fi

# ============================================================================
# LEGACY PACK-LEVEL RETURN (pre-Plan-005 / transitional)
# ============================================================================
if [ -z "$PACK_ID" ] || [ "$PACK_ID" = "null" ]; then exit 0; fi

RETURN_DIR="${BUDGET_DIR}/pack-returns/${RUN_ID}"
RETURN_FILE="${RETURN_DIR}/${PACK_ID}.json"
VERDICT=""

if [ -f "$RETURN_FILE" ] && jq empty "$RETURN_FILE" 2>/dev/null; then
  VERDICT=$(jq -r '.verdict // empty' "$RETURN_FILE")
fi

if [ -z "$VERDICT" ]; then
  RESPONSE_TEXT=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null || true)
  if [ -n "$RESPONSE_TEXT" ]; then
    VERDICT_LINE=$(echo "$RESPONSE_TEXT" | grep -iE '^[#]*[[:space:]]*verdict' | head -1 || true)
    if [ -n "$VERDICT_LINE" ]; then
      VERDICT=$(echo "$VERDICT_LINE" | sed 's/.*[Vv]erdict[[:space:]]*:*[[:space:]]*//' | tr -d '[:space:]#' || true)
    fi
  fi
fi

if [ -z "$VERDICT" ] || ! echo "$VERDICT" | grep -qiE '^(pass|blocked|needs|unknown)'; then
  VERDICT="unknown"
fi

# Update execution-state (pack-level)
if [ -f "$ESF" ]; then
  source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
  LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
  state_lock_acquire "$LOCK_DIR"
  jq --arg pack "$PACK_ID" --arg v "$VERDICT" --arg at "$AGENT_TYPE" '
    .plans |= with_entries(
      .value.packs |= with_entries(
        if .key == $pack then
          .value.status = "returned" | .value.worker_verdict = $v
        else . end
      )
    )
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
  state_lock_release "$LOCK_DIR"
fi

REMAINING=999
CUR_PLAN=""
if [ -f "$ESF" ]; then
  CUR_PLAN=$(jq -r --arg pack "$PACK_ID" '[.plans | to_entries[] | select(.value.packs[$pack] != null) | .key] | first // empty' "$ESF")
  if [ -n "$CUR_PLAN" ]; then
    REMAINING=$(jq --arg pid "$CUR_PLAN" '[.plans[$pid].packs | to_entries[] | select(.value.status == "pending" or .value.status == "dispatched")] | length' "$ESF")
  fi
fi

if [ "$REMAINING" -eq 0 ]; then
  MSG="[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). All packs in Plan ${CUR_PLAN} have returned. Process Open Items → scope drift check → Git Checkpoint for each → then Step 8 (Plan Implementation Review). Do NOT dispatch review until all Git Checkpoints complete."
else
  MSG="[multi-model-workflow] NEXT: Pack ${PACK_ID} returned (verdict: ${VERDICT}). Process Open Items → scope drift check → Git Checkpoint. ${REMAINING} packs still pending/dispatched in Plan ${CUR_PLAN}."
fi

emit_next "$MSG"
exit 0
