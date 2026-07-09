#!/usr/bin/env bash
# host.sh —— 宿主检测与路径/工具约定(Claude Code / Droid 双宿主完整面)
# 被 prepare/flow/loop/review/worker/hooks 统一 source,禁止各脚本再硬编码状态路径。
#
# 检测优先级:
#   1. MMW_HOST=droid|claude 显式覆盖
#   2. DROID_PLUGIN_ROOT 已设 → droid(仅 hook 运行时有;主线程 Execute 里没有)
#   3. 路径自检:本脚本装在 .../.factory/plugins/ → droid;.../.claude/plugins/ → claude
#      (不依赖 env,主线程直接跑 mmw 也判得对,plugin update 冲不掉)
#   4. 默认 claude
#
# 路径:
#   claude → .claude/multi-model-workflow + .claude/worktrees
#   droid  → .factory/multi-model-workflow + .factory/worktrees
#
# 续跑/列队跨宿主:
#   新建任务只写当前宿主平面;读已有任务时 mmw_resolve_state_subdir 会落到真实有 task.json 的平面。
#   列在飞 / team / cleanup 会扫两个 worktree 根。

mmw_host() {
  if [ -n "${MMW_HOST:-}" ]; then
    case "$MMW_HOST" in
      droid|claude) printf '%s' "$MMW_HOST"; return 0 ;;
      *)
        echo "ERROR: MMW_HOST must be droid|claude (got: $MMW_HOST)" >&2
        return 2
        ;;
    esac
  fi
  if [ -n "${DROID_PLUGIN_ROOT:-}" ]; then
    printf 'droid'; return 0
  fi
  # 路径自检:脚本被装进哪个宿主的插件目录就是谁(不依赖 env,更新冲不掉)
  local self
  self="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || self=""
  case "$self" in
    */.factory/plugins/*) printf 'droid'; return 0 ;;
    */.claude/plugins/*)  printf 'claude'; return 0 ;;
  esac
  printf 'claude'
}

# 写码工人 worktree 分支前缀
mmw_worker_branch_prefix() {
  case "$(mmw_host)" in
    droid) printf 'worker' ;;
    *)     printf 'codex' ;;
  esac
}

mmw_state_parent() {
  case "$(mmw_host)" in
    droid) printf '.factory' ;;
    *)     printf '.claude' ;;
  esac
}

mmw_peer_state_parent() {
  case "$(mmw_host)" in
    droid) printf '.claude' ;;
    *)     printf '.factory' ;;
  esac
}

mmw_state_subdir() {
  printf '%s/multi-model-workflow' "$(mmw_state_parent)"
}

mmw_peer_state_subdir() {
  printf '%s/multi-model-workflow' "$(mmw_peer_state_parent)"
}

mmw_worktrees_rel() {
  printf '%s/worktrees' "$(mmw_state_parent)"
}

mmw_peer_worktrees_rel() {
  printf '%s/worktrees' "$(mmw_peer_state_parent)"
}

# 当前宿主优先,再对端(列队/扫盘用)
mmw_all_worktrees_rel() {
  printf '%s\n%s\n' "$(mmw_worktrees_rel)" "$(mmw_peer_worktrees_rel)"
}

# 在仓库/worktree 根下解析真实状态平面:
# 优先当前宿主平面(有 task.json 或 loop-state.json);否则对端;都没有则回当前宿主(给新建写路径)。
# $1=可选 top;缺省 git toplevel。
mmw_resolve_state_subdir() {
  local top="${1:-}" pref peer
  pref="$(mmw_state_subdir)"
  peer="$(mmw_peer_state_subdir)"
  if [ -z "$top" ]; then
    top="$(git rev-parse --show-toplevel 2>/dev/null)" || { printf '%s' "$pref"; return 0; }
  fi
  if [ -f "$top/$pref/task.json" ] || [ -f "$top/$pref/loop-state.json" ]; then
    printf '%s' "$pref"
  elif [ -f "$top/$peer/task.json" ] || [ -f "$top/$peer/loop-state.json" ]; then
    printf '%s' "$peer"
  else
    printf '%s' "$pref"
  fi
}

# 按 slug 在两个 worktree 根里找路径;找到打印绝对路径并 return 0。
mmw_find_worktree() {
  local top="$1" slug="$2" rel
  [ -n "$top" ] && [ -n "$slug" ] || return 1
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    if [ -d "$top/$rel/$slug" ]; then
      printf '%s' "$top/$rel/$slug"
      return 0
    fi
  done < <(mmw_all_worktrees_rel)
  return 1
}

# 打印所有在飞 task.json 绝对路径(两个宿主平面)。
mmw_foreach_flying_manifest() {
  local top="$1" parent root d man
  [ -n "$top" ] || return 0
  for parent in .claude .factory; do
    root="$top/$parent/worktrees"
    [ -d "$root" ] || continue
    for d in "$root"/*/; do
      [ -d "$d" ] || continue
      man="${d}${parent}/multi-model-workflow/task.json"
      [ -f "$man" ] && printf '%s\n' "$man"
    done
  done
}

# 主仓库状态平面 gitignore(幂等)。$1=git toplevel
mmw_ensure_state_ignore() {
  local top="$1"
  local parent; parent="$(mmw_state_parent)"
  local g="$top/$parent/.gitignore" line
  mkdir -p "$top/$parent"
  if [ -f "$g" ] && grep -qxF '*' "$g" 2>/dev/null; then return 0; fi
  for line in 'worktrees/' 'multi-model-workflow/' '.gitignore'; do
    { [ -f "$g" ] && grep -qxF "$line" "$g"; } || printf '%s\n' "$line" >> "$g"
  done
}

# worktree 内状态平面全遮蔽
mmw_ensure_wt_state_ignore() {
  local wt="$1"
  local parent; parent="$(mmw_state_parent)"
  mkdir -p "$wt/$parent"
  [ -f "$wt/$parent/.gitignore" ] || printf '*\n' > "$wt/$parent/.gitignore"
}

# 续跑提示(宿主中立,不提 Claude 专属 EnterWorktree)
mmw_enter_worktree_hint() {
  local path="$1"
  case "$(mmw_host)" in
    droid)
      printf '在 worktree 路径继续本任务: cd %s 后跑 mmw where(或新开 droid 会话于该目录)' "$path"
      ;;
    *)
      printf 'EnterWorktree({ path: "%s" }) 然后 mmw where' "$path"
      ;;
  esac
}

# 问人工具名(文案用)
mmw_ask_user_tool() {
  case "$(mmw_host)" in
    droid) printf 'AskUser' ;;
    *)     printf 'AskUserQuestion' ;;
  esac
}

# 写码工人后端
mmw_worker_backend() {
  case "$(mmw_host)" in
    droid) printf 'droid-task' ;;
    *)     printf 'codex-cli' ;;
  esac
}

# 壳命令工具名(hooks matcher / 文案)
mmw_shell_tool() {
  case "$(mmw_host)" in
    droid) printf 'Execute' ;;
    *)     printf 'Bash' ;;
  esac
}

# 插件根(双宿主;脚本相对回退)
mmw_plugin_root() {
  if [ -n "${DROID_PLUGIN_ROOT:-}" ]; then
    printf '%s' "$DROID_PLUGIN_ROOT"
  elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
    printf '%s' "$CLAUDE_PLUGIN_ROOT"
  else
    # 脚本相对回退: .../plugin/scripts/lib → plugin
    local here; here="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    printf '%s' "$here"
  fi
}
