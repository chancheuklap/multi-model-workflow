#!/usr/bin/env bash
# Explicit Coordinator gate for worker spawn_agent dispatch.
# Validates the DISPATCH_ENVELOPE and state preconditions before spawning.
set -euo pipefail

PROMPT_FILE=""

usage() {
  cat <<'USAGE'
Usage: validate-pack-dispatch.sh --prompt-file PATH
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" ]] || usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round // 0')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key // empty')
AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role // empty')

case "$AGENT_ROLE" in
  pack_executor|complex_pack_executor) ;;
  *)
    echo "Error: worker dispatch agent_role must be pack_executor or complex_pack_executor" >&2
    exit 2
    ;;
esac

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" || -z "$PACK_ID" || "$PACK_ID" == "null" ]]; then
  echo "Error: worker dispatch requires run_id and pack_id" >&2
  exit 2
fi

BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"
SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"

if [[ ! -f "$SF" ]]; then
  echo "Error: workflow state not found: $SF" >&2
  exit 2
fi

if [[ ! -f "$ESF" ]]; then
  echo "Error: execution state not found: $ESF" >&2
  exit 2
fi

if jq -e --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys | index($key) != null' "$SF" >/dev/null; then
  echo "Error: duplicate dispatch idempotency_key=$IDEMPOTENCY_KEY" >&2
  exit 2
fi

BUDGET_STATUS=$(jq -r '.budget.budget_status // "unknown"' "$SF")
if [[ "$BUDGET_STATUS" == "pending_plan_count" ]]; then
  echo "Error: budget not initialized. Run state.sh budget initialize first." >&2
  exit 2
fi

DC=$(jq -r '.pending_direction_check.ack_status // empty' "$SF")
if [[ "$DC" == "pending" ]]; then
  echo "Error: Direction Check pending" >&2
  exit 2
fi

PACK_STATUS=$(jq -r --arg pid "$PACK_ID" \
  '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.status // "unknown"] | first // "unknown"' \
  "$ESF")
if [[ "$PACK_STATUS" != "pending" ]]; then
  echo "Error: Pack $PACK_ID status is '$PACK_STATUS', expected 'pending'" >&2
  exit 2
fi

EXISTING_AGENT_ID=$(jq -r --arg pid "$PACK_ID" \
  '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.agent_id // empty] | first // empty' \
  "$ESF")
if [[ -n "$EXISTING_AGENT_ID" && "$EXISTING_AGENT_ID" != "null" ]]; then
  echo "Error: Pack $PACK_ID already has agent_id=$EXISTING_AGENT_ID; repair must use send_input" >&2
  exit 2
fi

PA_BLOCKED=$(jq '[.path_a_escalation[] | select(.blocked_for_self_fix == true)] | length' "$SF" 2>/dev/null || echo "0")
if [[ "$PA_BLOCKED" -gt 0 ]]; then
  case "$AGENT_ROLE" in
    pack_executor|complex_pack_executor) ;;
    *) echo "Error: Path A exhausted; use Path B worker" >&2; exit 2 ;;
  esac
fi

if [[ "$REPAIR_ROUND" -ge 1 ]] 2>/dev/null; then
  while IFS= read -r ref; do
    [[ -n "$ref" ]] || continue
    FOUND_DISP=$(jq -r --arg fid "$ref" '.review_dispositions[] | select(.finding_id == $fid) | .disposition' "$SF" 2>/dev/null)
    if [[ "$FOUND_DISP" != "accepted" ]]; then
      echo "Error: finding $ref is not accepted in review_dispositions" >&2
      exit 2
    fi
    FOUND_EV=$(jq -r --arg fid "$ref" '.review_dispositions[] | select(.finding_id == $fid) | .evidence // ""' "$SF" 2>/dev/null)
    if [[ -z "$FOUND_EV" || "$FOUND_EV" == "null" ]]; then
      echo "Error: finding $ref has no disposition evidence" >&2
      exit 2
    fi
  done < <(echo "$ENVELOPE" | jq -r '.disposition_refs // [] | .[]')
fi

echo "OK"
