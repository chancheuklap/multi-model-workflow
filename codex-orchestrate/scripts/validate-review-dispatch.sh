#!/usr/bin/env bash
# Explicit Coordinator gate for Codex reviewer dispatch.
# Codex SubagentStart hooks do not receive the spawn_agent message, so review
# envelopes must be validated before spawn_agent/send_input is called.
set -euo pipefail

PROMPT_FILE=""
TRANSPORT=""

usage() {
  cat <<'USAGE'
Usage: validate-review-dispatch.sh --prompt-file PATH --transport spawn_agent|send_input
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
[[ "$TRANSPORT" == "spawn_agent" || "$TRANSPORT" == "send_input" ]] || usage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role // empty')
REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
AGENT_ID=$(echo "$ENVELOPE" | jq -r '.agent_id // empty')
EXCEPTION_CODE=$(echo "$ENVELOPE" | jq -r '.exception_code // empty')

if [[ "$AGENT_ROLE" != "codex_reviewer" ]]; then
  echo "Error: review dispatch envelope agent_role must be codex_reviewer" >&2
  exit 2
fi

case "$TRANSPORT:$REVIEW_INTENT" in
  spawn_agent:baseline)
    ;;
  send_input:targeted-re-review)
    if [[ -z "$AGENT_ID" || "$AGENT_ID" == "null" ]]; then
      echo "Error: targeted re-review must include baseline reviewer agent_id" >&2
      exit 2
    fi
    if [[ -z "$EXCEPTION_CODE" || "$EXCEPTION_CODE" == "null" ]]; then
      echo "Error: targeted re-review must include exception_code" >&2
      exit 2
    fi
    ;;
  spawn_agent:targeted-re-review)
    echo "Error: targeted re-review must use send_input, not spawn_agent" >&2
    exit 2
    ;;
  *)
    echo "Error: invalid review transport/intent combination: ${TRANSPORT}/${REVIEW_INTENT}" >&2
    exit 2
    ;;
esac

if [[ "$RUN_ID" != adhoc-* ]]; then
  bash "$SCRIPT_DIR/state.sh" budget check --run-id "$RUN_ID" >/dev/null
fi

echo "OK"
