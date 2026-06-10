#!/usr/bin/env bash
# PreToolUse Bash hook (if: "Bash(*codex-companion.mjs task*)")
# Gates Codex review dispatch — validates review_intent and pack completion.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"
# shellcheck source=lib/routes.sh
source "$SCRIPT_DIR/lib/routes.sh"

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

BUDGET_DIR=".claude/multi-model-workflow"
SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
ROUTE=$(jq -r '.route // empty' "$SF" 2>/dev/null)

# Whether this review_intent triggers a review gate is declared per-route in
# routes-v1.json[route].review_required (the intent whitelist) — not hardcoded.
# execution-bearing routes (formal/light) list "baseline" → Plan Implementation
# Review pack-completion gate; route-worker routes list [] → no gate.
# Fail-open: if the manifest is unreadable or the route is unknown, fall back to
# the legacy literal (baseline = gated).
GATE_INTENT=false
if routes_manifest_readable && [[ -n "$ROUTE" ]]; then
  if routes_review_required "$ROUTE" | grep -qx "$REVIEW_INTENT"; then
    GATE_INTENT=true
  fi
else
  [[ "$REVIEW_INTENT" == "baseline" ]] && GATE_INTENT=true
fi

if [[ "$GATE_INTENT" == "true" && "$REVIEW_INTENT" == "baseline" ]]; then
  # For Plan Implementation Review: verify all packs in the plan are committed
  GATE_NAME=$(basename "$PROMPT_FILE" .md)
  PLAN_NUM=$(echo "$GATE_NAME" | sed -n 's/.*plan-impl-review-\([0-9]*\).*/\1/p')
  if [ -n "$PLAN_NUM" ]; then
    # Normalize to 3-digit zero-padded key (execution-state uses "001", "002", ...)
    PLAN_NUM=$(printf "%03d" "$PLAN_NUM")
    ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
    if [ -f "$ESF" ]; then
      # 这是安全门:无法核验 = 拒绝(fail-closed),不能让 jq 报错被 set -e 杀脚本后
      # PreToolUse 非 2 退出而把未核验的 review 放过去(fail-open)。
      if ! jq empty "$ESF" 2>/dev/null; then
        echo "[multi-model-workflow] BLOCKED: execution-state malformed, cannot verify pack completion." >&2
        exit 2
      fi
      PLAN_EXISTS=$(jq --arg pid "$PLAN_NUM" '.plans[$pid] != null' "$ESF" 2>/dev/null || echo "false")
      if [ "$PLAN_EXISTS" != "true" ]; then
        echo "[multi-model-workflow] BLOCKED: Plan ${PLAN_NUM} not found in execution-state. Cannot verify pack completion." >&2
        exit 2
      fi
      # packs 缺失/为 null 时 // {} 兜底为 0 未提交(无 pack 可提交);仍非数字则 fail-closed。
      UNCOMMITTED=$(jq --arg pid "$PLAN_NUM" '[(.plans[$pid].packs // {}) | to_entries[] | select(.value.status != "committed")] | length' "$ESF" 2>/dev/null || echo "")
      if ! [[ "$UNCOMMITTED" =~ ^[0-9]+$ ]]; then
        echo "[multi-model-workflow] BLOCKED: cannot determine pack completion for Plan ${PLAN_NUM}." >&2
        exit 2
      fi
      if [ "$UNCOMMITTED" -gt 0 ]; then
        echo "[multi-model-workflow] BLOCKED: Plan ${PLAN_NUM} has ${UNCOMMITTED} uncommitted packs. Complete all packs before dispatching Plan Implementation Review." >&2
        exit 2
      fi
    fi
  fi
fi

exit 0
