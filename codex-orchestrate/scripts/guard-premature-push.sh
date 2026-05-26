#!/bin/bash
# PreToolUse hook for shell commands.
# Two responsibilities:
# 1. Block git push / gh pr create if unchecked tasks remain in the active plan.
# 2. Block git merge --squash — merge strategy rule enforcement.

if ! command -v jq >/dev/null 2>&1; then
  echo "[multi-model-workflow] jq not found — guard-premature-push requires jq. Skipping." >&2
  exit 0
fi

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../hooks/lib/payload.sh"

COMMAND=$(payload_tool_command "$INPUT")

# --- Rule 1: Merge strategy enforcement (always active, no plan check needed) ---

if echo "$COMMAND" | grep -qE 'git merge\b.*--squash'; then
  echo "[multi-model-workflow] BLOCKED: git merge --squash is forbidden. Use git merge --no-ff to preserve commit history." >&2
  exit 2
fi

# --- Rule 2: Block premature push/PR when plan has unchecked tasks ---

if ! echo "$COMMAND" | grep -qE 'git push|gh pr create'; then
  exit 0
fi

TOOL_WORKDIR="$(payload_jq "$INPUT" 'if (.tool_input? | type) == "object" then (.tool_input.workdir // .tool_input.cwd // "") else "" end' "")"
WORKSPACE_ROOT="$(pwd)"
if [ -n "$TOOL_WORKDIR" ] && [ -d "$TOOL_WORKDIR" ]; then
  WORKSPACE_ROOT="$TOOL_WORKDIR"
fi
WORKSPACE_ROOT="$(git -C "$WORKSPACE_ROOT" rev-parse --show-toplevel 2>/dev/null || printf '%s\n' "$WORKSPACE_ROOT")"

DEFAULT_PLAN_ROOT="${WORKSPACE_ROOT}/docs/orchestrate/plans"
PLAN_ROOT="$DEFAULT_PLAN_ROOT"
ACTIVE_RUN_FILE="${WORKSPACE_ROOT}/.codex/multi-model-workflow/active-run-id"
PLAN_ROOTS=()

if [ -f "$ACTIVE_RUN_FILE" ]; then
  ACTIVE_RUN_ID="$(tr -d '[:space:]' < "$ACTIVE_RUN_FILE")"
  WORKFLOW_STATE="${WORKSPACE_ROOT}/.codex/multi-model-workflow/workflow-state-${ACTIVE_RUN_ID}.json"
  if [ -n "$ACTIVE_RUN_ID" ] && [ -f "$WORKFLOW_STATE" ]; then
    ACTIVE_SLUG="$(jq -r '.slug // empty' "$WORKFLOW_STATE" 2>/dev/null || true)"
    if [ -n "$ACTIVE_SLUG" ] && [ "$ACTIVE_SLUG" != "null" ] && [ -d "${PLAN_ROOT}/${ACTIVE_SLUG}" ]; then
      PLAN_ROOTS=("${PLAN_ROOT}/${ACTIVE_SLUG}")
    fi
  fi
fi

if [ "${#PLAN_ROOTS[@]}" -eq 0 ] && git -C "$WORKSPACE_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BASE_REF="$(git -C "$WORKSPACE_ROOT" merge-base HEAD origin/main 2>/dev/null || true)"
  if [ -n "$BASE_REF" ]; then
    while IFS= read -r changed_plan_root; do
      if [ -n "$changed_plan_root" ] && [ -d "$changed_plan_root" ]; then
        PLAN_ROOTS+=("$changed_plan_root")
      fi
    done < <(
      git -C "$WORKSPACE_ROOT" diff --name-only "${BASE_REF}..HEAD" -- docs/orchestrate/plans 2>/dev/null \
        | awk -F/ -v root="$WORKSPACE_ROOT" 'NF >= 4 {print root "/" $1 "/" $2 "/" $3 "/" $4}' \
        | sort -u
    )
  fi
fi

if [ "${#PLAN_ROOTS[@]}" -eq 0 ]; then
  PLAN_ROOTS=("$DEFAULT_PLAN_ROOT")
fi

UNCHECKED=0
for current_plan_root in "${PLAN_ROOTS[@]}"; do
  count=$(find "$current_plan_root" -name '*.md' -exec grep -c '^\s*- \[ \]' {} + 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')
  UNCHECKED=$((UNCHECKED + count))
done
if [ "${UNCHECKED}" -gt 0 ]; then
  printf -v PLAN_ROOT_LABEL '%s, ' "${PLAN_ROOTS[@]}"
  PLAN_ROOT_LABEL="${PLAN_ROOT_LABEL%, }"
  echo "[multi-model-workflow] BLOCKED: ${PLAN_ROOT_LABEL} has ${UNCHECKED} unchecked tasks. Complete execution and review before pushing." >&2
  exit 2
fi

exit 0
