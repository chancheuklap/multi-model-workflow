#!/bin/bash
# PreToolUse hook for Bash tool.
# Two responsibilities:
# 1. Block git push / gh pr create if unchecked tasks remain in the active plan.
# 2. Block git merge --squash — merge strategy rule enforcement.

if ! command -v jq >/dev/null 2>&1; then
  echo "[multi-model-workflow] jq not found — guard-premature-push requires jq. Skipping." >&2
  exit 0
fi

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../hooks/lib/payload.sh
source "$SCRIPT_DIR/../hooks/lib/payload.sh"
COMMAND="$(mmw_payload_command "$INPUT")"

# --- Rule 1: Merge strategy enforcement (always active, no plan check needed) ---
# 只在命令「真正执行」git merge --squash 时拦：匹配命令边界（行首 / ; & | && ||）后的
# 动词，不再裸扫整条命令文本。否则 `echo "别用 git merge --squash"`、grep 搜索这串
# 文字、写文档等无害命令都会被 exit 2 误杀（根因：旧版用 grep 扫全文当数据）。

if echo "$COMMAND" | grep -qE '(^|[;&|]|&&|\|\|)[[:space:]]*git[[:space:]]+merge[[:space:]][^;&|]*--squash'; then
  echo "[multi-model-workflow] BLOCKED: git merge --squash is forbidden. Use git merge --no-ff to preserve commit history." >&2
  exit 2
fi

# --- Rule 2: Block premature push/PR when plan has unchecked tasks ---
# 同样只在命令「真正执行」git push / gh pr create 时才进入未勾选检查：匹配命令边界后的
# 动词，不裸扫全文。否则 `grep "git push" docs/`、`echo "记得 gh pr create"` 等含这串
# 文字的无害命令会被误判为要推送而拦死（这正是本场反复卡死的根因）。

if ! echo "$COMMAND" | grep -qE '(^|[;&|]|&&|\|\|)[[:space:]]*(git[[:space:]]+push|gh[[:space:]]+pr[[:space:]]+create)([[:space:]]|$)'; then
  exit 0
fi

WORKSPACE_ROOT="$(pwd)"
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

# 无 active run、且本分支(BASE..HEAD)未改动任何 plan 文件 => 本次 push / PR 不挂在
# 任何具体计划上,直接放行。旧版在这里退回扫整个 docs/orchestrate/plans 目录,会把仓库里
# 无关的既有未勾选任务全算进来误拦(false positive：改个文案/修个无关 bug 也推不动)。
# 门禁只应锚定「当前在做的那个计划」——由 active run 或本分支改动的 plan 文件识别。
if [ "${#PLAN_ROOTS[@]}" -eq 0 ]; then
  exit 0
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
