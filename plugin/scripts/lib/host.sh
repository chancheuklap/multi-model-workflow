#!/usr/bin/env bash
# host.sh —— 宿主检测与路径/工具约定(Claude Code / Droid 双宿主完整面)
# 被 prepare/flow/loop/review/worker/hooks 统一 source,禁止各脚本再硬编码状态路径。
#
# 检测优先级:
#   1. MMW_HOST=droid|claude 显式覆盖
#   2. DROID_PLUGIN_ROOT 已设 → droid(Droid 会同时设 CLAUDE_PLUGIN_ROOT 别名,以 DROID 为准)
#   3. 默认 claude
#
# 路径:
#   claude → .claude/multi-model-workflow + .claude/worktrees
#   droid  → .factory/multi-model-workflow + .factory/worktrees

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
    printf 'droid'
  else
    printf 'claude'
  fi
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

mmw_state_subdir() {
  printf '%s/multi-model-workflow' "$(mmw_state_parent)"
}

mmw_worktrees_rel() {
  printf '%s/worktrees' "$(mmw_state_parent)"
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

# 插件根(双宿主)
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
