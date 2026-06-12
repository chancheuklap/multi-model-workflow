#!/usr/bin/env bash
# PreToolUse hook for Edit and Write tools — B2/B3 四规则路径守卫。
#
# 背景：PreToolUse hook 输入不含调用者 agent 身份，守卫无法按 Worker 区分各自
# worktree，因此设计为对所有调用者都安全的全局规则（与「Coordinator 在 formal
# 流程中不直接写生产代码」hard gate 自洽，Coordinator 不被误伤）。
#
# Marker 协议（B3，per-plan）：Coordinator 派发 Worker 前创建
#   .codex/multi-model-workflow/worker-active-<plan_id>
# 文件内容 = 该 Plan 的 worktree 绝对路径（串行模式 = Coordinator 工作树路径）。
# Worker 终态后由 Coordinator 删除对应 marker；marker 互不影响（一个 Worker
# 收尾不会误清其他在跑 Worker 的保护）。
#
# 飞行期间（存在任一 marker）的四规则，按序判定：
#   ① docs/ 一律拦（设计/计划文档只有 Coordinator 可改，且只在无 Worker 飞行时）
#   ② 状态目录 .codex/multi-model-workflow/ 放行（plan-returns / open-items /
#      pack-returns 等控制面是 Worker 的合法写入通道）
#   ③ 已登记 worktree 内放行（Worker 在自己工作树干活）
#   ④ 主工作树其余路径拦（飞行期间主树 = 只读源码区；源码改动只能发生在
#      隔离 worktree 里，经 B6 回收合并进来）
# 无 marker（无 Worker 飞行）→ 全放行，Coordinator 自由。
#
# 注意：本守卫覆盖 Codex 文件工具层（Edit/Write/apply_patch）的写入。shell
# 命令自身仍由 sandbox 和回收前 diff 检查兜底，因此 worker prompt 也必须声明
# worktree_path 与 docs/ 禁写边界。
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/payload.sh
source "$SCRIPT_DIR/lib/payload.sh"

# Extract file_path from tool_input (works for both Edit and Write)
FILE_PATH="$(mmw_payload_file_path "$INPUT")"
[[ -z "$FILE_PATH" ]] && exit 0

WORKFLOW_DIR=".codex/multi-model-workflow"
if [[ ! -d "$WORKFLOW_DIR" ]]; then
  exit 0
fi

# Collect per-plan markers + registered worktrees
ANY_MARKER="false"
WORKTREES=()
for marker in "$WORKFLOW_DIR"/worker-active-*; do
  [[ -f "$marker" ]] || continue
  ANY_MARKER="true"
  wt=$(head -1 "$marker" 2>/dev/null | tr -d '[:space:]')
  [[ -n "$wt" ]] && WORKTREES+=("$wt")
done

# No worker in flight → Coordinator context → allow everything
if [[ "$ANY_MARKER" != "true" ]]; then
  exit 0
fi

# Resolve to absolute path (without requiring the file to exist)
MAIN_TREE="$(pwd)"
ABS_PATH="$FILE_PATH"
[[ "$ABS_PATH" != /* ]] && ABS_PATH="${MAIN_TREE}/${ABS_PATH}"

# Rule ①: docs/ blocked anywhere (main tree or worktree — plan/design docs are
# Coordinator-only, and only outside worker flight)
if echo "$ABS_PATH" | grep -qE '(^|/)docs/'; then
  echo "[multi-model-workflow] BLOCKED: Worker 飞行期间不可修改 docs/ 下的设计与计划文档（任何工作树）。checkbox 勾选由 Coordinator 在 Plan Implementation Review 通过后执行。" >&2
  exit 2
fi

# Rule ②: control plane (.codex/multi-model-workflow/) allowed — legitimate
# Worker write channel (plan-returns / open-items / pack-returns / locks)
case "$ABS_PATH" in
  */.codex/multi-model-workflow/*) exit 0 ;;
esac

# Rule ③: inside a registered worktree → allow
for wt in ${WORKTREES[@]+"${WORKTREES[@]}"}; do
  case "$ABS_PATH" in
    "$wt"/*|"$wt") exit 0 ;;
  esac
done

# Rule ④: main tree source area is read-only during parallel flight
case "$ABS_PATH" in
  "$MAIN_TREE"/*)
    echo "[multi-model-workflow] BLOCKED: Worker 飞行期间主工作树为只读源码区。源码改动必须发生在分配的隔离 worktree 内（envelope.worktree_path），完成后经依赖序合并回收。" >&2
    exit 2
    ;;
esac

# Outside main tree and not a registered worktree (e.g. /tmp) → allow
exit 0
