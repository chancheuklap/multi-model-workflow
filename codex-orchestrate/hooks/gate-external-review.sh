#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"

COMMAND="$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.tool_input.command // empty) else empty end' 2>/dev/null || true)"
[[ -z "$COMMAND" ]] && exit 0

if ! echo "$COMMAND" | grep -qE 'scripts/review/review-lane\.sh[[:space:]]+submit'; then
  exit 0
fi

PROMPT_FILE="$(echo "$COMMAND" | sed -n 's/.*--prompt-file[[:space:]]\{1,\}\([^[:space:]]*\).*/\1/p' | head -1)"
if [[ -z "$PROMPT_FILE" || ! -f "$PROMPT_FILE" ]]; then
  echo "[codex-orchestrate] BLOCKED: review-lane submit requires readable --prompt-file." >&2
  exit 2
fi

ENVELOPE="$(bash "$PARSE_ENVELOPE" "$PROMPT_FILE" 2>/dev/null)" || {
  echo "[codex-orchestrate] BLOCKED: review prompt missing DISPATCH_ENVELOPE." >&2
  exit 2
}

RUN_ID="$(echo "$ENVELOPE" | jq -r '.run_id // empty')"
REVIEW_INTENT="$(echo "$ENVELOPE" | jq -r '.review_intent // empty')"
EXCEPTION_CODE="$(echo "$ENVELOPE" | jq -r '.exception_code // empty')"
[[ -n "$RUN_ID" && "$RUN_ID" != "null" ]] || {
  echo "[codex-orchestrate] BLOCKED: review DISPATCH_ENVELOPE missing run_id." >&2
  exit 2
}

case "$REVIEW_INTENT" in
  baseline|targeted-re-review|path-a-re-review|post-push-regression|release-risk) ;;
  *)
    echo "[codex-orchestrate] BLOCKED: review_intent is required for review dispatch." >&2
    exit 2
    ;;
esac

STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

case "$REVIEW_INTENT" in
  baseline)
    GATE_NAME="$(basename "$PROMPT_FILE" .md)"
    PLAN_NUM="$(echo "$GATE_NAME" | sed -n 's/.*plan-impl-review-\([0-9]*\).*/\1/p')"
    if [[ -n "$PLAN_NUM" ]]; then
      PLAN_NUM="$(printf "%03d" "$PLAN_NUM")"
      ESF="${STATE_BASE}/execution-state-${RUN_ID}.json"
      if [[ -f "$ESF" ]]; then
        PLAN_EXISTS="$(jq --arg pid "$PLAN_NUM" '.plans[$pid] != null' "$ESF")"
        if [[ "$PLAN_EXISTS" != "true" ]]; then
          echo "[codex-orchestrate] BLOCKED: Plan ${PLAN_NUM} not found in execution-state. Cannot verify pack completion." >&2
          exit 2
        fi
        UNCOMMITTED="$(jq --arg pid "$PLAN_NUM" '[.plans[$pid].packs | to_entries[] | select(.value.status != "committed")] | length' "$ESF")"
        if [[ "$UNCOMMITTED" -gt 0 ]]; then
          echo "[codex-orchestrate] BLOCKED: Plan ${PLAN_NUM} has ${UNCOMMITTED} uncommitted packs. Complete all packs before Plan Implementation Review." >&2
          exit 2
        fi
      fi
    fi
    ;;
  path-a-re-review)
    SF="${STATE_BASE}/workflow-state-${RUN_ID}.json"
    if [[ -f "$SF" ]]; then
      HAS_ENTRY="$(jq '[.path_a_escalation[]? | select(.blocked_for_self_fix == true)] | length > 0' "$SF")"
      [[ "$HAS_ENTRY" == "true" ]] && exit 0
    fi
    echo "[codex-orchestrate] BLOCKED: path-a-re-review requires active path_a_escalation entry." >&2
    exit 2
    ;;
  targeted-re-review)
    if ! echo "$COMMAND" | grep -q -- '--resume'; then
      echo "[codex-orchestrate] BLOCKED: targeted re-review must pass --resume." >&2
      exit 2
    fi

    [[ "$EXCEPTION_CODE" == "user_requested" ]] && exit 0

    SF="${STATE_BASE}/workflow-state-${RUN_ID}.json"
    if [[ -f "$SF" ]]; then
      HAS_EXCEPTION="$(jq '[.self_verifications[]? | select(.exception != "none")] | length > 0' "$SF" 2>/dev/null || echo "false")"
      [[ "$HAS_EXCEPTION" == "true" ]] && exit 0
    fi
    echo "[codex-orchestrate] BLOCKED: targeted re-review requires qualifying exception; default path is Coordinator self-verify." >&2
    exit 2
    ;;
esac

exit 0
