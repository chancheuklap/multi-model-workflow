#!/usr/bin/env bash
# Explicit Coordinator gate for non-execution worker dispatch.
# Execution Packs use validate-pack-dispatch.sh because they require
# execution-state and durable return handling. Route workers still need a
# native prompt envelope, budget gate, and idempotency guard.
set -euo pipefail

PROMPT_FILE=""
TRANSPORT="Agent"

usage() {
  cat <<'USAGE'
Usage: validate-route-worker-dispatch.sh --prompt-file PATH [--transport Agent|SendMessage]
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    --transport) TRANSPORT="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" ]] || usage
[[ "$TRANSPORT" == "Agent" || "$TRANSPORT" == "SendMessage" ]] || usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
PHASE=$(echo "$ENVELOPE" | jq -r '.phase // empty')
AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role // empty')
AGENT_ID=$(echo "$ENVELOPE" | jq -r '.agent_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round // 0')
IDEMPOTENCY_KEY=$(echo "$ENVELOPE" | jq -r '.idempotency_key // empty')

case "$AGENT_ROLE" in
  pack-executor|complex-pack-executor) ;;
  *)
    echo "Error: route worker dispatch agent_role must be pack-executor or complex-pack-executor" >&2
    exit 2
    ;;
esac

case "$PHASE" in
  bug-investigation|direct-repair|multi-pr-merge|hotfix|quickfix|spike|maintenance) ;;
  *)
    echo "Error: route worker dispatch phase must be a non-execution route phase" >&2
    exit 2
    ;;
esac

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "Error: route worker dispatch requires run_id" >&2
  exit 2
fi

if [[ -n "$PACK_ID" && "$PACK_ID" != "null" ]]; then
  echo "Error: route worker dispatch must set pack_id to null; execution Packs use validate-pack-dispatch.sh" >&2
  exit 2
fi

if [[ -z "$IDEMPOTENCY_KEY" || "$IDEMPOTENCY_KEY" == "null" ]]; then
  echo "Error: route worker dispatch requires idempotency_key" >&2
  exit 2
fi

if [[ "$TRANSPORT" == "SendMessage" ]]; then
  if [[ -z "$AGENT_ID" || "$AGENT_ID" == "null" ]]; then
    echo "Error: route worker repair must include original worker agent_id" >&2
    exit 2
  fi
  if [[ "$REPAIR_ROUND" -lt 1 ]] 2>/dev/null; then
    echo "Error: route worker repair must set repair_round >= 1" >&2
    exit 2
  fi
else
  if [[ -n "$AGENT_ID" && "$AGENT_ID" != "null" ]]; then
    echo "Error: first route worker dispatch must set agent_id to null" >&2
    exit 2
  fi
fi

bash "$SCRIPT_DIR/state.sh" budget check --run-id "$RUN_ID" >/dev/null
bash "$SCRIPT_DIR/state.sh" idempotency check --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY" >/dev/null

echo "OK"
