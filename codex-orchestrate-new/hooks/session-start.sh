#!/usr/bin/env bash
# multi-model-workflow: SessionStart hook
# Prerequisites check + behavioral override injection + state recovery.
# 守门改为告警、不阻断:SessionStart 钩子无法阻断会话——官方文档明确 exit 2 对
# SessionStart 只显示 stderr、不拦启动。而提前 exit 还会让脚本末尾的 workflow 断点恢复
# JSON 永远跑不到(守门没守住、反而废掉自己的核心功能)。故缺前置条件时只发一条可操作的
# 告警,放会话继续跑。

warn_prerequisite() {
  local name="$1" check="$2"
  if ! eval "$check" >/dev/null 2>&1; then
    echo "[multi-model-workflow] WARNING: prerequisite missing — $name. Plugin features may not work until resolved." >&2
  fi
}

# 读取 hook 触发源（startup / clear / compact）——决定续跑约束的注入强度。
# stdin 必须趁早一次性吃进变量，避免后续子进程争用。
HOOK_INPUT=$(cat 2>/dev/null || true)
HOOK_SOURCE=$(printf '%s' "$HOOK_INPUT" | jq -r '.source // empty' 2>/dev/null || true)

warn_prerequisite "jq in PATH" \
  'command -v jq'

warn_prerequisite "python3 in PATH" \
  'command -v python3'

PLUGIN_ROOT="${MMW_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
warn_prerequisite "plugin.json readable" \
  "[ -f '$PLUGIN_ROOT/.codex-plugin/plugin.json' ]"

PLUGIN_VERSION=$(jq -r '.version // empty' "$PLUGIN_ROOT/.codex-plugin/plugin.json" 2>/dev/null)
warn_prerequisite "plugin.json has version field" \
  '[ -n "$PLUGIN_VERSION" ]'

BASE_CONTEXT=$(cat <<RULES
[multi-model-workflow] Codex workflow plugin active (version ${PLUGIN_VERSION:-unknown}).

- Helper scripts live at: ${PLUGIN_ROOT}
- Before copying shell examples from skills, set: export MMW_PLUGIN_ROOT="${PLUGIN_ROOT}"
- State files live under: .codex/multi-model-workflow
- Dispatch must be Codex-native: spawn_agent, wait_agent, close_agent, resume_agent, send_input.
RULES
)

# 默认只注入轻量 runtime anchor；普通会话不主动续跑。
# 仅当存在进行中的 workflow（active-run-id）时，才注入断点恢复 + 续跑约束（见下方）。
# 入口路由由各 skill 的 description 承担；Hard Gates 由 orchestrate-workflow SKILL.md 的
# Global Constraints + PreToolUse guard 脚本强制——两者都不依赖本注入。
CONTEXT="$BASE_CONTEXT"

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
    if [ "$HOOK_SOURCE" = "compact" ]; then
      # compact：同一对话被压缩、任务连续——注入完整断点恢复，推动续跑。
      CONTEXT=$(cat <<RULES
[multi-model-workflow] Codex workflow plugin active (version ${PLUGIN_VERSION:-unknown}).

[multi-model-workflow] 检测到进行中的 workflow（version ${PLUGIN_VERSION}），续跑约束：

# 断点恢复
- RESUME: phase=${CUR_PHASE}, reference=${CUR_REF:-none}, step=${CUR_STEP:-unknown}, budget=${REVIEW_USED}/${REVIEW_TOTAL}
- 进入任何 phase skill 前 re-read ${BUDGET_DIR}/scope-${RUN_ID}.md 确认 Scope Contract
- git status --short --branch 验证 branch 和 dirty state
- Resume Gate: source artifacts 改过 → 重进该 gate
RULES
)
    else
      # clear / startup：用户大概率要开新局——只给一行被动备查，默认忽略，不施加续跑压力。
      CONTEXT="${BASE_CONTEXT}

[multi-model-workflow] 备查：存在未结束的 workflow（run ${RUN_ID}，停在 phase ${CUR_PHASE:-unknown}）。仅当用户本次明确要继续它时，才读 ${BUDGET_DIR}/scope-${RUN_ID}.md 恢复；否则忽略本行，正常处理当前请求，不主动续跑。"
    fi
  fi
fi

# jq 缺失时无法构造 JSON——告警已发出,会话仍需正常起步,故跳过注入而非崩溃。
if command -v jq >/dev/null 2>&1; then
  jq -n --arg context "$CONTEXT" \
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $context}}'
fi
exit 0
