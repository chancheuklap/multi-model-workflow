#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"
MANIFEST="$PLUGIN_ROOT/.codex-plugin/plugin.json"

require() {
  local name="$1" cmd="$2"
  if ! eval "$cmd" >/dev/null 2>&1; then
    echo "[codex-orchestrate] BLOCKED: prerequisite missing: $name" >&2
    exit 2
  fi
}

require "jq" "command -v jq"
require "python3" "command -v python3"
require "codex" "command -v codex"
require ".codex-plugin/plugin.json" "[ -f '$MANIFEST' ]"
require "Codex features list" "codex features list"

VERSION="$(jq -r '.version // empty' "$MANIFEST")"
if [[ -z "$VERSION" || "$VERSION" == "null" ]]; then
  echo "[codex-orchestrate] BLOCKED: plugin manifest has no version." >&2
  exit 2
fi

CODEX_VERSION="$(codex --version 2>/dev/null || true)"
FEATURES="$(codex features list 2>/dev/null || true)"
for feature in plugins plugin_hooks hooks multi_agent unified_exec; do
  if ! awk -v f="$feature" '$1 == f && $3 == "true" { found=1 } END { exit(found ? 0 : 1) }' <<< "$FEATURES"; then
    echo "[codex-orchestrate] BLOCKED: required Codex feature disabled: $feature" >&2
    exit 2
  fi
done

MSG="$(cat <<RULES
[codex-orchestrate] Runtime active: version=$VERSION, cli=${CODEX_VERSION:-unknown}

# 1. Entry routing
- Ad-hoc Codex review request（Codex review / 用 Codex 审 / Codex 看看 / second opinion / 独立审查 + commit/文件/分支/文档）→ codex-review
- 新功能、改造、feedback、design/plan/issue/PRD、UI/UX 反馈、截图、测试失败、已实现 diff、要求实现/继续/review/验收/收尾 → orchestrate-workflow
- 缺可 review design → orchestrate-discovery
- 已有 reviewed design + issue hierarchy → orchestrate-plan-writing
- 已有 reviewed plan + Task Pack inventory → orchestrate-execution
- EXECUTION_PASSED → orchestrate-final-review
- 多 PR 合并审查 → orchestrate-multi-pr-merge

# 2. Skill namespace
- Plugin skills: orchestrate-workflow, orchestrate-discovery, orchestrate-plan-writing, orchestrate-execution, orchestrate-final-review, orchestrate-multi-pr-merge, codex-review
- External skills remain short-name skills: diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs

# 3. Hard gates
- 没有验证证据，不得声称完成。
- 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
- Design Review / Plan Review / Pack or Plan Implementation Review / Final Review 不可跳过，除非 route extension 明确拥有简化审查合同。
- Upstream skill 结论必须写回 design / issue / plan / bug brief，再继续当前节点。
- Coordinator 不写生产代码；生产代码由 worker 通过自足 dispatch 执行。
- 不用技术语言向用户汇报最终业务结果。
- 不存在非阻塞项：要么当前修复，要么记录为正式 issue / blocker。

# 4. Codex runtime contract
- Runtime state lives under .codex/multi-model-workflow.
- Dispatches must carry DISPATCH_ENVELOPE and go through dispatch-gateway.sh or worktree-exec.sh when they affect Task Packs.
- Write-heavy Task Packs use managed git worktrees and codex exec. Interactive subagents are for read-only or same-workspace coordination unless the coordinator records a clear exception.
- Repairs resume the original worker through send_input/resume_agent for interactive subagents, or worktree-resume.sh / codex exec resume <worker_thread_id> for worktree workers. Replacement dispatch requires an exception code and full prior context.
- All review uses native codex exec review through review-lane.sh and records thread_id. Targeted re-review must resume that thread_id; document reviews use gpt-5.5/xhigh; code, bug, integration, final, and release-risk reviews use gpt-5.4/xhigh. No Claude Review lane is part of this Codex runtime.

# 5. Compaction recovery
- Before entering any phase skill, read .codex/multi-model-workflow/scope-<run_id>.md when present.
- Read workflow-state-<run_id>.json cursor.phase / cursor.reference / cursor.step before continuing.
- Run git status --short --branch to verify branch and dirty state before dispatch or review.
- If source artifacts changed after their review gate, re-enter that gate before continuing downstream.
RULES
)"

RUN_ID_FILE="$STATE_BASE/active-run-id"
if [[ -f "$RUN_ID_FILE" ]]; then
  RUN_ID="$(cat "$RUN_ID_FILE" 2>/dev/null || true)"
  SF="$STATE_BASE/workflow-state-${RUN_ID}.json"
  if [[ -n "$RUN_ID" && -f "$SF" ]] && jq empty "$SF" >/dev/null 2>&1; then
    PHASE="$(jq -r '.cursor.phase // "unknown"' "$SF")"
    REF="$(jq -r '.cursor.reference // "none"' "$SF")"
    STEP="$(jq -r '.cursor.step // "unknown"' "$SF")"
    REVIEW_USED="$(jq -r '.budget.review_used // 0' "$SF")"
    REVIEW_TOTAL="$(jq -r '.budget.review_total // "unknown"' "$SF")"
    STATE_MSG="$(cat <<STATE

[codex-orchestrate] Resume state:
- run_id: $RUN_ID
- phase: $PHASE
- reference: $REF
- step: $STEP
- review budget: $REVIEW_USED/$REVIEW_TOTAL
STATE
)"
    MSG="${MSG}${STATE_MSG}"
  fi
fi

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$msg}}'

exit 0
