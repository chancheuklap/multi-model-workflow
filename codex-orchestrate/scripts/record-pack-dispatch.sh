#!/usr/bin/env bash
# Records a successful worker spawn_agent dispatch after Codex returns agent_id.
set -euo pipefail

PROMPT_FILE=""
AGENT_ID=""

usage() {
  cat <<'USAGE'
Usage: record-pack-dispatch.sh --prompt-file PATH --agent-id AGENT_ID
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" && -n "$AGENT_ID" ]] || usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key // empty')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" || -z "$PACK_ID" || "$PACK_ID" == "null" ]]; then
  echo "Error: run_id and pack_id required" >&2
  exit 2
fi

BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"
ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [[ ! -f "$ESF" ]]; then
  echo "Error: execution state not found: $ESF" >&2
  exit 2
fi

bash "$SCRIPT_DIR/state.sh" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY"
bash "$SCRIPT_DIR/state.sh" agent-id set --run-id "$RUN_ID" --pack-id "$PACK_ID" --agent-id "$AGENT_ID"

source "$SCRIPT_DIR/lib/state-lock.sh"
LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
trap 'state_lock_release "$LOCK_DIR"' EXIT

jq --arg pid "$PACK_ID" '
  .plans |= with_entries(
    .value.packs |= with_entries(
      if .key == $pid then .value.status = "dispatched" else . end
    )
  )
' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"

echo "OK"
