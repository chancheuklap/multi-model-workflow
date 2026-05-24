#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_TYPE="$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.agent_type // empty) else empty end' 2>/dev/null || true)"
AGENT_ID="$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.agent_id // empty) else empty end' 2>/dev/null || true)"
PROMPT="$(printf '%s' "$INPUT" | jq -r '
  if type == "object" then
    .message
    // .prompt
    // .tool_input.message
    // .tool_input.prompt
    // ((.items // .tool_input.items // []) | map(select((.type // "") == "text") | (.text // "")) | join("\n"))
    // empty
  else empty end
' 2>/dev/null || true)"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

case "$AGENT_TYPE" in
  pack_executor|complex_pack_executor|plan_writer|root_cause_analyst|code_explorer|complex_code_explorer|docs_worker) ;;
  *) exit 0 ;;
esac

if [[ "$AGENT_TYPE" == "pack_executor" || "$AGENT_TYPE" == "complex_pack_executor" ]]; then
  if [[ -z "$PROMPT" ]]; then
    CONTEXT_SUFFIX=" Codex SubagentStart payload did not expose the dispatch message; Coordinator must include a visible DISPATCH_ENVELOPE in every worker prompt before spawning."
  else
    jq -n --arg prompt "$PROMPT" '{tool_input:{prompt:$prompt}}' | bash "$SCRIPT_DIR/validate-pack-dispatch.sh"
    CONTEXT_SUFFIX=""
  fi
else
  CONTEXT_SUFFIX=""
fi

CONTEXT="Codex Orchestrate subagent context: obey the parent dispatch only; write durable return files when requested; do not expand scope."
if [[ -f "$STATE_BASE/active-run-id" ]]; then
  RUN_ID="$(cat "$STATE_BASE/active-run-id")"
  CONTEXT="$CONTEXT Active run_id: $RUN_ID. Subagent id: ${AGENT_ID:-unknown}."
fi
CONTEXT="$CONTEXT$CONTEXT_SUFFIX"

printf '%s' "$INPUT" | bash "$SCRIPT_DIR/track-effort-budget.sh" >/dev/null 2>&1 || true

jq -n --arg msg "$CONTEXT" \
  '{hookSpecificOutput:{hookEventName:"SubagentStart",additionalContext:$msg}}'
