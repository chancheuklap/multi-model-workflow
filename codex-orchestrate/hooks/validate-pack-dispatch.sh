#!/usr/bin/env bash
# SubagentStart hook for pack-executor / complex-pack-executor.
# Parses DISPATCH_ENVELOPE → validates state conditions (10-step ordering).
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"
STATE_SH="$SCRIPT_DIR/../scripts/state.sh"

HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
if [[ "$HOOK_EVENT" != "SubagentStart" ]]; then exit 0; fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
case "$AGENT_TYPE" in
  pack_executor|complex_pack_executor) ;;
  *) exit 0 ;;
esac

# Step 1: parse envelope from Codex SubagentStart prompt
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then
  echo "[multi-model-workflow] BLOCKED: SubagentStart payload missing prompt." >&2
  exit 2
fi

ENVELOPE=$(echo "$PROMPT" | bash "$PARSE_ENVELOPE" 2>/dev/null) || {
  echo "[multi-model-workflow] BLOCKED: DISPATCH_ENVELOPE missing or malformed." >&2
  exit 2
}

# Step 2: validate required fields
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key')
AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role')

BUDGET_DIR=".codex/multi-model-workflow"

# Step 3: load workflow-state + execution-state
SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [[ ! -f "$SF" ]]; then exit 0; fi

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"

# Step 4: read-only idempotency check (exit 2 if key exists)
EXISTING=$(jq -r --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys | index($key) // empty' "$SF")
if [[ -n "$EXISTING" ]]; then
  echo "[multi-model-workflow] BLOCKED: duplicate dispatch (idempotency_key=$IDEMPOTENCY_KEY)." >&2
  exit 2
fi

# Step 5: check formal budget initialized (budget_status != "pending_plan_count")
BUDGET_STATUS=$(jq -r '.budget.budget_status // "unknown"' "$SF")
if [[ "$BUDGET_STATUS" == "pending_plan_count" ]]; then
  echo "[multi-model-workflow] BLOCKED: budget not initialized. Run 'state.sh budget initialize --plan-count N' first." >&2
  exit 2
fi

# Step 6: check pending Direction Check
DC=$(jq -r '.pending_direction_check.ack_status // empty' "$SF")
if [[ "$DC" == "pending" ]]; then
  if [[ "$AGENT_ROLE" != "codex-reviewer" ]]; then
    echo "[multi-model-workflow] BLOCKED: Direction Check pending." >&2
    exit 2
  fi
fi

# Step 7: pack status check — only allow dispatch for pending packs
if [[ -n "$PACK_ID" && "$PACK_ID" != "null" && -f "$ESF" ]]; then
  PACK_STATUS=$(jq -r --arg pid "$PACK_ID" \
    '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.status // "unknown"] | first // "unknown"' \
    "$ESF" 2>/dev/null || echo "unknown")
  if [[ "$PACK_STATUS" != "pending" && "$PACK_STATUS" != "unknown" ]]; then
    echo "[multi-model-workflow] BLOCKED: Pack $PACK_ID status is '$PACK_STATUS', expected 'pending'. Cannot re-dispatch." >&2
    exit 2
  fi
fi

# Step 8: agent_id existence guard (per Ruling 2 + A7: not gated by repair_round)
if [[ -n "$PACK_ID" && "$PACK_ID" != "null" && -f "$ESF" ]]; then
  EXISTING_AGENT_ID=$(jq -r --arg pid "$PACK_ID" \
    '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.agent_id // empty] | first // empty' \
    "$ESF" 2>/dev/null || echo "")
  if [[ -n "$EXISTING_AGENT_ID" && "$EXISTING_AGENT_ID" != "null" ]]; then
    echo "[multi-model-workflow] BLOCKED: Pack $PACK_ID already has agent_id=$EXISTING_AGENT_ID. Repair must use send_input(target: \"$EXISTING_AGENT_ID\") to resume the original worker." >&2
    exit 2
  fi
fi

# Step 9: Path A escalation check
PA_BLOCKED=$(jq '[.path_a_escalation[] | select(.blocked_for_self_fix == true)] | length' "$SF" 2>/dev/null || echo "0")
if [[ "$PA_BLOCKED" -gt 0 ]]; then
  case "$AGENT_ROLE" in
    pack_executor|complex_pack_executor) ;; # Path B worker allowed
    *) echo "[multi-model-workflow] BLOCKED: Path A exhausted, must use Path B worker." >&2; exit 2 ;;
  esac
fi

# Step 10: Disposition refs validation for repair dispatch (repair_round >= 1)
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

# Step 11: mutating idempotency append via state.sh (only reached if all checks pass)
export STATE_BASE="$BUDGET_DIR"
bash "$STATE_SH" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY" 2>/dev/null || true

# Step 12: write pack status dispatched (in execution-state if available)
if [[ -n "$PACK_ID" && "$PACK_ID" != "null" && -f "$ESF" ]]; then
  source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"
  LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
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

# Step 13: exit 0
exit 0
