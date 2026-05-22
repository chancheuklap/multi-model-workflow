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

# Direction check gate
DC=$(jq -r '.pending_direction_check.ack_status // empty' "$SF")
if [[ "$DC" == "pending" ]]; then
  AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role')
  if [[ "$AGENT_ROLE" != "codex-reviewer" ]]; then
    echo "[multi-model-workflow] BLOCKED: Direction Check pending." >&2
    exit 2
  fi
fi

exit 0
