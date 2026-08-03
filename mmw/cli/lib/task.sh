#!/usr/bin/env bash
# 任务隔离：建 worktree、给出路径、清理。
#
# 切会话工作目录只有宿主工具做得到，脚本做不了。所以 enter 只输出路径，切目录
# 那一步由技能用宿主自己的工具做。
#
# 清理一律用非强制形式：有未合并的改动时 git 自己会失败，那正是要的行为。

set -euo pipefail

mmw_task_dir() {
  local slug="$1"
  echo "$(mmw_repo_root)/$(mmw_path_field worktrees)/$slug"
}

# 建 worktree、建分支、打一个记住用户原话的空提交。
mmw_task_new() {
  local slug="$1" note="${2:-}"
  local root dir branch
  root="$(mmw_repo_root)"
  dir="$(mmw_task_dir "$slug")"
  branch="$slug"

  if [ -e "$dir" ]; then
    echo "mmw: $dir 已经存在" >&2
    return 1
  fi

  git -C "$root" worktree add -b "$branch" "$dir" >&2
  if [ -n "$note" ]; then
    git -C "$dir" commit --allow-empty -q -m "task($slug): $note"
  fi
  echo "$dir"
}

mmw_task_enter() {
  local dir
  dir="$(mmw_task_dir "$1")"
  if [ ! -d "$dir" ]; then
    echo "mmw: $dir 不存在" >&2
    return 1
  fi
  echo "$dir"
}

mmw_task_cleanup() {
  local slug="$1"
  local root dir
  root="$(mmw_repo_root)"
  dir="$(mmw_task_dir "$slug")"
  # 两条都是非强制形式：worktree 里有未提交改动、分支没合并进来，git 会拒绝，
  # 命令带着非零退出码停在这里，由人决定要不要真的丢掉。
  git -C "$root" worktree remove "$dir"
  git -C "$root" branch -d "$slug"
}
