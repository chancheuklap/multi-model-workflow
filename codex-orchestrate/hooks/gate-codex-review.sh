#!/usr/bin/env bash
# SubagentStart hook for codex_reviewer.
# Gates baseline reviewer dispatches and blocks targeted re-review through new agents.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"

HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
if [[ "$HOOK_EVENT" != "SubagentStart" ]]; then exit 0; fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // empty' 2>/dev/null)
if [[ "$AGENT_TYPE" != "codex_reviewer" ]]; then exit 0; fi

PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then
  echo "[multi-model-workflow] BLOCKED: codex_reviewer dispatch missing prompt." >&2
  exit 2
fi

ENVELOPE=$(echo "$PROMPT" | bash "$PARSE_ENVELOPE" 2>/dev/null) || {
  echo "[multi-model-workflow] BLOCKED: codex_reviewer prompt missing/malformed DISPATCH_ENVELOPE." >&2
  exit 2
}

AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role // empty')
REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id')

if [[ "$AGENT_ROLE" != "codex_reviewer" ]]; then
  echo "[multi-model-workflow] BLOCKED: codex_reviewer dispatch envelope agent_role must be codex_reviewer." >&2
  exit 2
fi

case "$REVIEW_INTENT" in
  baseline)
    exit 0
    ;;
  path-a-re-review)
    BUDGET_DIR=".codex/multi-model-workflow"
    SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
    if [[ -f "$SF" ]]; then
      HAS_ENTRY=$(jq '.path_a_escalation | length > 0' "$SF")
      if [[ "$HAS_ENTRY" == "true" ]]; then
        exit 0
      fi
    fi
    echo "[multi-model-workflow] BLOCKED: path-a-re-review requires active path_a_escalation entry." >&2
    exit 2
    ;;
  targeted-re-review)
    echo "[multi-model-workflow] BLOCKED: targeted re-review must use send_input(target: baseline reviewer agent_id), not spawn_agent." >&2
    exit 2
    ;;
  *)
    echo "[multi-model-workflow] BLOCKED: codex_reviewer dispatch requires review_intent=baseline or path-a-re-review." >&2
    exit 2
    ;;
esac
