#!/usr/bin/env bash
# PreToolUse hook for Agent (pack-executor / complex-pack-executor).
# Parses DISPATCH_ENVELOPE → validates state conditions.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then exit 0; fi

ENVELOPE=$(echo "$PROMPT" | bash "$PARSE_ENVELOPE" 2>/dev/null) || {
  echo "[multi-model-workflow] BLOCKED: DISPATCH_ENVELOPE missing or malformed." >&2
  exit 2
}

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key')

BUDGET_DIR=".claude/multi-model-workflow"
SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
if [[ ! -f "$SF" ]]; then exit 0; fi

# Idempotency check
EXISTING=$(jq -r --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys | index($key) // empty' "$SF")
if [[ -n "$EXISTING" ]]; then
  echo "[multi-model-workflow] BLOCKED: duplicate dispatch (idempotency_key=$IDEMPOTENCY_KEY)." >&2
  exit 2
fi

jq --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys += [$key]' "$SF" > "${SF}.tmp" && mv "${SF}.tmp" "$SF"

# Disposition refs validation (§3b-2 亲验卡扣)
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

# Path A escalation check
AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role')
PA_BLOCKED=$(jq '[.path_a_escalation[] | select(.blocked_for_self_fix == true)] | length' "$SF" 2>/dev/null || echo "0")
if [[ "$PA_BLOCKED" -gt 0 ]]; then
  case "$AGENT_ROLE" in
    pack-executor|complex-pack-executor) ;; # Path B worker allowed
    *) echo "[multi-model-workflow] BLOCKED: Path A exhausted, must use Path B worker." >&2; exit 2 ;;
  esac
fi

# Direction check gate
DC=$(jq -r '.pending_direction_check.ack_status // empty' "$SF")
if [[ "$DC" == "pending" ]]; then
  if [[ "$AGENT_ROLE" != "codex-reviewer" ]]; then
    echo "[multi-model-workflow] BLOCKED: Direction Check pending." >&2
    exit 2
  fi
fi

exit 0
