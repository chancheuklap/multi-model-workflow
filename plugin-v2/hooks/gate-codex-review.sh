#!/usr/bin/env bash
# PreToolUse Bash hook (if: "Bash(*codex-companion.mjs task*)")
# Gates Codex review dispatch — blocks targeted re-review without exception.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [[ -z "$COMMAND" ]]; then exit 0; fi
if ! echo "$COMMAND" | grep -qE 'codex-companion.*task'; then exit 0; fi

PROMPT_FILE=$(echo "$COMMAND" | sed -n 's/.*--prompt-file[[:space:]]*\([^[:space:]]*\).*/\1/p')
if [[ -z "$PROMPT_FILE" || ! -f "$PROMPT_FILE" ]]; then exit 0; fi

ENVELOPE=$(bash "$PARSE_ENVELOPE" "$PROMPT_FILE" 2>/dev/null) || exit 0

REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')
EXCEPTION_CODE=$(echo "$ENVELOPE" | jq -r '.exception_code // empty')
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id')

case "$REVIEW_INTENT" in
  baseline)
    exit 0
    ;;
  path-a-re-review)
    BUDGET_DIR=".claude/multi-model-workflow"
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
    if [[ "$EXCEPTION_CODE" == "user_requested" ]]; then
      exit 0
    fi

    BUDGET_DIR=".claude/multi-model-workflow"
    SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
    if [[ -f "$SF" ]]; then
      HAS_EXCEPTION=$(jq '[.self_verifications[] | select(.exception != "none")] | length > 0' "$SF" 2>/dev/null)
      if [[ "$HAS_EXCEPTION" == "true" ]]; then
        exit 0
      fi
    fi
    echo "[multi-model-workflow] BLOCKED: Codex re-review requires qualifying exception. Default is Coordinator self-verify." >&2
    exit 2
    ;;
  *)
    exit 0
    ;;
esac
