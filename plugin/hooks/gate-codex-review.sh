#!/usr/bin/env bash
# PreToolUse Bash hook (if: "Bash(*codex-companion.mjs task*)")
# Gates Codex review dispatch — blocks targeted re-review without exception.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [[ -z "$COMMAND" ]]; then exit 0; fi
if ! echo "$COMMAND" | grep -qE '(codex-companion|CODEX_SCRIPT).*[[:space:]]task([[:space:]]|$)'; then exit 0; fi

PROMPT_FILE=$(echo "$COMMAND" | sed -n 's/.*--prompt-file[[:space:]]*\([^[:space:]]*\).*/\1/p')
if [[ -z "$PROMPT_FILE" || ! -f "$PROMPT_FILE" ]]; then
  echo "[multi-model-workflow] BLOCKED: codex review dispatch missing --prompt-file or file unreadable." >&2
  exit 2
fi

ENVELOPE=$(bash "$PARSE_ENVELOPE" "$PROMPT_FILE" 2>/dev/null) || {
  echo "[multi-model-workflow] BLOCKED: codex review prompt missing/malformed DISPATCH_ENVELOPE." >&2
  exit 2
}

REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')
EXCEPTION_CODE=$(echo "$ENVELOPE" | jq -r '.exception_code // empty')
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id')

case "$REVIEW_INTENT" in
  baseline)
    # For Plan Implementation Review: verify all packs in the plan are committed
    GATE_NAME=$(basename "$PROMPT_FILE" .md)
    PLAN_NUM=$(echo "$GATE_NAME" | sed -n 's/.*plan-impl-review-\([0-9]*\).*/\1/p')
    if [ -n "$PLAN_NUM" ]; then
      # Normalize to 3-digit zero-padded key (execution-state uses "001", "002", ...)
      PLAN_NUM=$(printf "%03d" "$PLAN_NUM")
      BUDGET_DIR=".claude/multi-model-workflow"
      ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
      if [ -f "$ESF" ]; then
        PLAN_EXISTS=$(jq --arg pid "$PLAN_NUM" '.plans[$pid] != null' "$ESF")
        if [ "$PLAN_EXISTS" != "true" ]; then
          echo "[multi-model-workflow] BLOCKED: Plan ${PLAN_NUM} not found in execution-state. Cannot verify pack completion." >&2
          exit 2
        fi
        UNCOMMITTED=$(jq --arg pid "$PLAN_NUM" '[.plans[$pid].packs | to_entries[] | select(.value.status != "committed")] | length' "$ESF")
        if [ "$UNCOMMITTED" -gt 0 ]; then
          echo "[multi-model-workflow] BLOCKED: Plan ${PLAN_NUM} has ${UNCOMMITTED} uncommitted packs. Complete all packs before dispatching Plan Implementation Review." >&2
          exit 2
        fi
      fi
    fi
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
