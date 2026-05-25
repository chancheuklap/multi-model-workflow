#!/usr/bin/env bash
# multi-model-workflow: Codex SessionStart hook.
# Prerequisites check + behavioral override injection + state recovery.
# Missing prerequisites = exit 2 (block session startup).

check_prerequisite() {
  local name="$1" check="$2"
  if ! eval "$check" >/dev/null 2>&1; then
    echo "[multi-model-workflow] BLOCKED: prerequisite missing — $name" >&2
    exit 2
  fi
}

check_prerequisite "jq in PATH" \
  'command -v jq'

check_prerequisite "python3 in PATH" \
  'command -v python3'

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
check_prerequisite "plugin.json readable" \
  "[ -f '$PLUGIN_ROOT/.codex-plugin/plugin.json' ]"

PLUGIN_VERSION=$(jq -r '.version // empty' "$PLUGIN_ROOT/.codex-plugin/plugin.json" 2>/dev/null)
check_prerequisite "plugin.json has version field" \
  '[ -n "$PLUGIN_VERSION" ]'

CONTEXT=$(cat <<RULES
[multi-model-workflow] Codex workflow override active (version ${PLUGIN_VERSION}):

# 1. Environment check
- Before running plugin helper scripts in Skill instructions, set:
  \`export MMW_PLUGIN_ROOT="${PLUGIN_ROOT}"\`

# 2. Entry routing
- User asks for ad-hoc Codex review (Codex review / 用 Codex 审 / Codex 看看 / second opinion / 独立审查 + 指定 commit/文件/分支/文档) → multi-model-workflow:codex-review
- User confirms direction → multi-model-workflow:orchestrate-discovery → multi-model-workflow:orchestrate-plan-writing
- Design doc exists / referenced → multi-model-workflow:orchestrate-workflow (entry gate)
- User asks to review / advance / execute / 推进 / 审查 / 落地 / 走流程 → multi-model-workflow:orchestrate-workflow

# 3. Skill namespace
- Plugin skills (multi-model-workflow: prefix): orchestrate-workflow, orchestrate-discovery, orchestrate-plan-writing, orchestrate-execution, orchestrate-final-review, orchestrate-multi-pr-merge, codex-review
- User-level skills (short name, NO prefix): diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs

# 4. Hard gates
- 没有验证证据，不得声称完成
- 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境
- 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker
- Design Review / Plan Review / Final Review 不可跳过（除非 Direct Repair mini-route）
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点
- 不自己写生产代码——调度 Codex worker
- 不用技术语言向用户汇报
- Review 派发步骤已内联到各 dispatch 模板中，Read 对应的 review dispatch reference 即可
- Task Pack 串行执行，Worker 直接在 Coordinator 分支上工作

# 5. Compaction recovery
- 进入任何 phase skill 前：re-read .codex/multi-model-workflow/scope-<run_id>.md 确认 Scope Contract
- git status --short --branch 验证 branch 和 dirty state
- Resume Gate: source artifacts 改过 → 重进该 gate
RULES
)

# === Workflow state recovery ===
BUDGET_DIR=".codex/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ -f "$RUN_ID_FILE" ]; then
  RUN_ID=$(cat "$RUN_ID_FILE")
  SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
  if [ -f "$SF" ] && jq empty "$SF" 2>/dev/null; then
    CUR_PHASE=$(jq -r '.cursor.phase // empty' "$SF")
    CUR_REF=$(jq -r '.cursor.reference // empty' "$SF")
    CUR_STEP=$(jq -r '.cursor.step // empty' "$SF")
    REVIEW_USED=$(jq -r '.budget.review_used // 0' "$SF")
    REVIEW_TOTAL=$(jq -r '.budget.review_total // 0' "$SF")

    CONTEXT="${CONTEXT}

# 6. Workflow state recovery
[multi-model-workflow] RESUME: phase=${CUR_PHASE}, reference=${CUR_REF:-none}, step=${CUR_STEP:-unknown}, budget=${REVIEW_USED}/${REVIEW_TOTAL}."
  fi
fi

jq -n --arg context "$CONTEXT" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $context}}'
exit 0
