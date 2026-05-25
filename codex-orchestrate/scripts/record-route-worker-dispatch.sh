#!/usr/bin/env bash
# Records a successful non-execution worker dispatch after Codex returns agent_id.
set -euo pipefail

PROMPT_FILE=""
AGENT_ID=""
AGENT_FILE=""

usage() {
  cat <<'USAGE'
Usage: record-route-worker-dispatch.sh --prompt-file PATH --agent-id AGENT_ID --agent-file PATH
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
    --agent-file) AGENT_FILE="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" && -n "$AGENT_ID" && -n "$AGENT_FILE" ]] || usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" || -z "$IDEMPOTENCY_KEY" || "$IDEMPOTENCY_KEY" == "null" ]]; then
  echo "Error: run_id and idempotency_key required" >&2
  exit 2
fi

if [[ -n "$PACK_ID" && "$PACK_ID" != "null" ]]; then
  echo "Error: route worker record must not receive an execution pack_id" >&2
  exit 2
fi

bash "$SCRIPT_DIR/state.sh" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY"
mkdir -p "$(dirname "$AGENT_FILE")"
printf '%s\n' "$AGENT_ID" > "$AGENT_FILE"

echo "OK"
