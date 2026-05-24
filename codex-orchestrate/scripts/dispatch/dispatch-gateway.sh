#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_SH="$PLUGIN_ROOT/scripts/state.sh"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

ENVELOPE_FILE=""
MODE="validate"
PACK_BRIEF=""
DRY_RUN=false

usage() {
  cat <<'USAGE'
Usage: dispatch-gateway.sh --envelope-file <file> [--mode validate|worktree] [--pack-brief <file>] [--dry-run]

Validates Codex Orchestrate dispatch envelopes before any worker or reviewer is launched.
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --envelope-file) ENVELOPE_FILE="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --pack-brief) PACK_BRIEF="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

[[ -n "$ENVELOPE_FILE" && -f "$ENVELOPE_FILE" ]] || { echo "dispatch-gateway: --envelope-file is required" >&2; exit 2; }
jq empty "$ENVELOPE_FILE" >/dev/null

PROTOCOL_VERSION="$(jq -r '.protocol_version // empty' "$ENVELOPE_FILE")"
RUN_ID="$(jq -r '.run_id // empty' "$ENVELOPE_FILE")"
PHASE="$(jq -r '.phase // empty' "$ENVELOPE_FILE")"
PACK_ID="$(jq -r '.pack_id // empty' "$ENVELOPE_FILE")"
ROLE="$(jq -r '.agent_role // empty' "$ENVELOPE_FILE")"
IDEMPOTENCY_KEY="$(jq -r '.idempotency_key // empty' "$ENVELOPE_FILE")"
REPAIR_ROUND="$(jq -r '.repair_round // 0' "$ENVELOPE_FILE")"
REVIEW_INTENT="$(jq -r '.review_intent // "null"' "$ENVELOPE_FILE")"
EXCEPTION_CODE="$(jq -r '.exception_code // "null"' "$ENVELOPE_FILE")"

for required in PROTOCOL_VERSION RUN_ID PHASE ROLE IDEMPOTENCY_KEY; do
  value="${!required}"
  [[ -n "$value" && "$value" != "null" ]] || { echo "dispatch-gateway: missing $required" >&2; exit 2; }
done
[[ "$PROTOCOL_VERSION" == "1" ]] || { echo "dispatch-gateway: unsupported protocol_version=$PROTOCOL_VERSION" >&2; exit 2; }
case "$PHASE" in
  plan-writing|execution|final-review|discovery|multi-pr-merge) ;;
  *) echo "dispatch-gateway: invalid phase=$PHASE" >&2; exit 2 ;;
esac
case "$ROLE" in
  plan_writer|pack_executor|complex_pack_executor|reviewer|code_explorer|complex_code_explorer|root_cause_analyst|docs_worker) ;;
  *) echo "dispatch-gateway: invalid agent_role=$ROLE" >&2; exit 2 ;;
esac
case "$REVIEW_INTENT" in
  baseline|targeted-re-review|path-a-re-review|post-push-regression|release-risk|null) ;;
  *) echo "dispatch-gateway: invalid review_intent=$REVIEW_INTENT" >&2; exit 2 ;;
esac
case "$EXCEPTION_CODE" in
  3plus_files_control_flow|user_requested|rca_root_cause|host_resume_failed|path_a_self_fix|null) ;;
  *) echo "dispatch-gateway: invalid exception_code=$EXCEPTION_CODE" >&2; exit 2 ;;
esac

SF="$STATE_BASE/workflow-state-${RUN_ID}.json"
if [[ -f "$SF" ]]; then
  EXISTING="$(jq -r --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys | index($key) // empty' "$SF")"
  [[ -z "$EXISTING" ]] || { echo "dispatch-gateway: duplicate idempotency key $IDEMPOTENCY_KEY" >&2; exit 2; }

  BUDGET_STATUS="$(jq -r '.budget.budget_status // empty' "$SF")"
  [[ "$BUDGET_STATUS" != "pending_plan_count" ]] || { echo "dispatch-gateway: budget not initialized" >&2; exit 2; }

  DC="$(jq -r '.pending_direction_check.ack_status // empty' "$SF")"
  if [[ "$DC" == "pending" && "$ROLE" != "reviewer" ]]; then
    echo "dispatch-gateway: direction check pending" >&2
    exit 2
  fi

  PA_BLOCKED="$(jq '[.path_a_escalation[]? | select(.blocked_for_self_fix == true)] | length' "$SF" 2>/dev/null || echo "0")"
  if [[ "$PA_BLOCKED" -gt 0 ]]; then
    case "$ROLE" in
      pack_executor|complex_pack_executor) ;;
      *) echo "dispatch-gateway: Path A exhausted; use Path B worker" >&2; exit 2 ;;
    esac
  fi

  if [[ "$REPAIR_ROUND" -ge 1 ]] 2>/dev/null; then
    missing=0
    missing_evidence=0
    while IFS= read -r ref; do
      [[ -n "$ref" ]] || continue
      disp="$(jq -r --arg fid "$ref" '.review_dispositions[]? | select(.finding_id == $fid) | .disposition // empty' "$SF")"
      [[ "$disp" == "accepted" ]] || missing=1
      evidence="$(jq -r --arg fid "$ref" '.review_dispositions[]? | select(.finding_id == $fid) | .evidence // empty' "$SF")"
      [[ -n "$evidence" && "$evidence" != "null" ]] || missing_evidence=1
    done < <(jq -r '.disposition_refs // [] | .[]' "$ENVELOPE_FILE")
    [[ "$missing" -eq 0 ]] || { echo "dispatch-gateway: repair dispatch references non-accepted finding" >&2; exit 2; }
    [[ "$missing_evidence" -eq 0 ]] || { echo "dispatch-gateway: accepted repair finding missing evidence" >&2; exit 2; }
  fi

  ESF="$STATE_BASE/execution-state-${RUN_ID}.json"
  if [[ -n "$PACK_ID" && "$PACK_ID" != "null" && -f "$ESF" ]]; then
    PACK_STATUS="$(jq -r --arg pid "$PACK_ID" \
      '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.status // "unknown"] | first // "unknown"' \
      "$ESF" 2>/dev/null || echo "unknown")"
    if [[ "$PACK_STATUS" != "pending" && "$PACK_STATUS" != "unknown" ]]; then
      echo "dispatch-gateway: Pack $PACK_ID status is '$PACK_STATUS', expected pending" >&2
      exit 2
    fi

    EXISTING_AGENT_ID="$(jq -r --arg pid "$PACK_ID" \
      '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.agent_id // empty] | first // empty' \
      "$ESF" 2>/dev/null || echo "")"
    if [[ -n "$EXISTING_AGENT_ID" && "$EXISTING_AGENT_ID" != "null" ]]; then
      echo "dispatch-gateway: Pack $PACK_ID already has agent_id=$EXISTING_AGENT_ID; repair must resume original agent" >&2
      exit 2
    fi
  fi

  STATE_BASE="$STATE_BASE" bash "$STATE_SH" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY" >/dev/null 2>&1 || true

  if [[ -n "$PACK_ID" && "$PACK_ID" != "null" && -f "${ESF:-}" ]]; then
    source "$PLUGIN_ROOT/scripts/lib/state-lock.sh"
    LOCK_DIR="${STATE_BASE}/${RUN_ID}.lock"
    state_lock_acquire "$LOCK_DIR"
    jq --arg pid "$PACK_ID" '
      .plans |= with_entries(
        .value.packs |= with_entries(
          if .key == $pid then .value.status = "dispatched" else . end
        )
      )
    ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
    state_lock_release "$LOCK_DIR"
  fi
fi

if [[ "$MODE" == "worktree" ]]; then
  [[ -n "$PACK_BRIEF" && -f "$PACK_BRIEF" ]] || { echo "dispatch-gateway: --pack-brief required for worktree mode" >&2; exit 2; }
  exec "$SCRIPT_DIR/worktree-exec.sh" --envelope-file "$ENVELOPE_FILE" --pack-brief "$PACK_BRIEF" ${DRY_RUN:+--dry-run}
fi

if [[ "$DRY_RUN" == "true" ]]; then
  jq -n --arg run_id "$RUN_ID" --arg role "$ROLE" --arg pack_id "$PACK_ID" \
    '{status:"validated", run_id:$run_id, agent_role:$role, pack_id:$pack_id}'
else
  echo "dispatch-gateway: validated $ROLE for run $RUN_ID"
fi
