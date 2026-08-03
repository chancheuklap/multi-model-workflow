#!/usr/bin/env bash
# 任务隔离：建 worktree、给出路径、清理。
#
# 切会话工作目录只有宿主工具做得到，脚本做不了。所以 new 与 enter 都只输出路
# 径，切目录那一步由技能用宿主自己的工具做。
#
# 落点一律在主仓库的 .worktrees/ 下，不管命令在哪棵树上执行——分支可以嵌
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
# 用法：mmw_task_new <slug> [原话] [--from <基点>]
#
# 不给 --from 就从当前 HEAD 分叉：在主仓库跑从主线分叉，在某棵 worktree 里跑
# 从那条分支分叉。要从别的分支分叉必须显式给 --from——`/mmw-wayfinder` 走链时
# 会话还在主仓库，而那条链要从 map 分支分叉，光靠当前 HEAD 取不到；`git
# checkout` 也切不过去，map 分支正被 map 的 worktree 占着。
#
# 同名分支已经存在时挂回它，不新建也不打空提交，--from 一并忽略——map 的
# worktree 被清理过之后要建回来，走的就是这条。
mmw_task_new() {
  local slug="" note="" from=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --from)
        from="${2:-}"
        if [ -z "$from" ]; then
          echo "mmw: --from 要跟一个分支名或提交" >&2
          return 1
        fi
        shift 2
        ;;
      -*)
        echo "mmw: task new 不认识 $1" >&2
        return 1
        ;;
      *)
        if [ -z "$slug" ]; then slug="$1"; else note="$1"; fi
        shift
        ;;
    esac
  done

  if [ -z "$slug" ]; then
    echo "mmw: task new 要一个 slug" >&2
    return 1
  fi

  local root dir base
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

  if [ -n "$from" ]; then
    if ! git rev-parse --verify --quiet "$from^{commit}" > /dev/null; then
      echo "mmw: --from 给的 ${from} 不是这个仓库里的分支或提交" >&2
      return 1
    fi
    base="$from"
  else
    # 当前 HEAD 要在这里取出来再传给 git -C "$root"。不传的话 worktree add 用
    # 的是主仓库的 HEAD，在任务 worktree 里再开一棵就会错分叉到主线。
    base="$(git rev-parse HEAD)"
  fi

  git -C "$root" worktree add -b "$slug" "$dir" "$base" >&2
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
