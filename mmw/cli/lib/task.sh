#!/usr/bin/env bash
# 任务隔离：建 worktree、给出路径、清理。
#
# 切会话工作目录只有宿主工具做得到，脚本做不了。所以 new 与 enter 都只输出路
# 径，切目录那一步由技能用宿主自己的工具做。
#
# 落点一律在主仓库的 .worktrees/ 下，不管命令从哪棵树上跑起来——分支可以嵌
# 套，目录不嵌套。
#
# 清理一律用非强制形式：有未合并的改动时 git 自己会失败，那正是要的行为。

set -euo pipefail

mmw_task_dir() {
  local slug="$1"
  echo "$(mmw_main_root)/$(mmw_path_field worktrees)/$slug"
}

# 建 worktree、建分支、打一个记住用户原话的空提交。
#
# 从哪里分叉由当前 HEAD 决定：在主仓库跑就从主线分叉，在某棵 worktree 里跑就
# 从那条分支分叉。同名分支已经存在时挂回它，不新建也不打空提交——map 的
# worktree 被清理过之后要建回来，走的就是这条。
mmw_task_new() {
  local slug="$1" note="${2:-}"
  local root dir
  root="$(mmw_main_root)"
  dir="$(mmw_task_dir "$slug")"

  if [ -e "$dir" ]; then
    echo "mmw: ${dir} 已经存在" >&2
    return 1
  fi

  if git show-ref --quiet --verify "refs/heads/$slug"; then
    git -C "$root" worktree add "$dir" "$slug" >&2
    echo "$dir"
    return 0
  fi

  git worktree add -b "$slug" "$dir" >&2
  if [ -n "$note" ]; then
    git -C "$dir" commit --allow-empty -q -m "$slug" -m "$note"
  fi
  echo "$dir"
}

mmw_task_enter() {
  local dir
  dir="$(mmw_task_dir "$1")"
  if [ ! -d "$dir" ]; then
    echo "mmw: ${dir} 不存在" >&2
    return 1
  fi
  echo "$dir"
}

mmw_task_cleanup() {
  local slug="$1"
  local root dir onto
  root="$(mmw_main_root)"
  dir="$(mmw_task_dir "$slug")"

  if ! git -C "$root" show-ref --quiet --verify "refs/heads/$slug"; then
    echo "mmw: 没有 ${slug} 这条分支" >&2
    return 1
  fi

  # 合没合并要在动 worktree 之前判。反过来会留下半完成状态：worktree 已经删
  # 掉、分支还在，而命令报的是失败——人看到失败，以为什么都没发生。
  onto="$(git -C "$root" rev-parse --abbrev-ref HEAD)"
  if ! git -C "$root" merge-base --is-ancestor "$slug" HEAD; then
    echo "mmw: ${slug} 还没合并进 ${onto}，不清理" >&2
    return 1
  fi

  # 这一条是非强制形式：worktree 里有未提交改动时 git 会拒绝，命令带着非零退
  # 出码停在这里，由人决定要不要真的丢掉。
  git -C "$root" worktree remove "$dir"
  git -C "$root" branch -d "$slug"
}
