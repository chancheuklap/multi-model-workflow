#!/usr/bin/env bash
# runtime.sh —— Claude Code 状态平面与 worktree 公共操作。

MMW_STATE_SUBDIR=".claude/multi-model-workflow"
MMW_WORKTREES_REL=".claude/worktrees"

mmw_ensure_state_ignore() {
  local top="$1"
  local g="$top/.claude/.gitignore" line
  mkdir -p "$top/.claude"
  if [ -f "$g" ] && grep -qxF '*' "$g" 2>/dev/null; then return 0; fi
  for line in 'worktrees/' 'multi-model-workflow/' '.gitignore'; do
    { [ -f "$g" ] && grep -qxF "$line" "$g"; } || printf '%s\n' "$line" >> "$g"
  done
}

mmw_ensure_worktree_state_ignore() {
  local wt="$1"
  mkdir -p "$wt/.claude"
  [ -f "$wt/.claude/.gitignore" ] || printf '*\n' > "$wt/.claude/.gitignore"
}
