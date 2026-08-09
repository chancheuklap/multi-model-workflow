#!/usr/bin/env bash
# 任务隔离：查状态、建 worktree、绑定分支、给出路径、清理。
#
# 切会话工作目录只有宿主工具做得到，脚本做不了。所以 new 只输出路径，切目录
# 那一步由技能用宿主自己的工具做。
#
# 落点一律在主仓库的 .worktrees/ 下，不管命令在哪棵树上执行——分支可以嵌
# 套，目录不嵌套。
#
# 清理一律用非强制形式：有未合并的改动时 git 自己会失败，那正是要的行为。

set -euo pipefail

mmw_task_state() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "outside"
    return 0
  fi

  local git_dir common_dir branch head
  git_dir="$(git rev-parse --path-format=absolute --git-dir)"
  common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
  branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  head="$(git rev-parse HEAD)"

  if [ "$git_dir" = "$common_dir" ]; then
    echo "local ${branch:-detached} ${head}"
  elif [ -z "$branch" ]; then
    echo "detached ${head}"
  else
    echo "bound ${branch} ${head}"
  fi
}

# 把宿主已经创建的 detached linked worktree 绑到任务分支。
# 用法：mmw_task_bind <完整分支名> <用户原话或任务目标> [--from <预期基点>]
mmw_task_bind() {
  local branch="${1:-}" note="${2:-}" from=""
  shift 2 2>/dev/null || true
  while [ $# -gt 0 ]; do
    case "$1" in
      --from)
        from="${2:-}"
        [ -n "$from" ] || { echo "mmw: task bind 的 --from 要基点" >&2; return 1; }
        shift 2
        ;;
      *)
        echo "mmw: task bind 不认识 $1" >&2
        return 1
        ;;
    esac
  done
  [ -n "$branch" ] || { echo "mmw: task bind 要完整分支名" >&2; return 1; }
  [ -n "$note" ] || { echo "mmw: task bind 要用户原话或任务目标" >&2; return 1; }
  git check-ref-format --branch "$branch" >/dev/null 2>&1 || {
    echo "mmw: ${branch} 不是合法分支名" >&2
    return 1
  }
  [ "$(mmw_task_state | awk '{print $1}')" = "detached" ] || {
    echo "mmw: task bind 只能在 detached linked worktree 执行" >&2
    return 1
  }
  mmw_git_clean . "不绑定分支" || return 1
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    echo "mmw: ${branch} 已存在" >&2
    return 1
  fi
  if [ -n "$from" ]; then
    local from_sha
    from_sha="$(mmw_git_commit "$from")" || return 1
    if [ "$(git rev-parse HEAD)" != "$from_sha" ]; then
      echo "mmw: detached worktree 不在预期基点 ${from}" >&2
      return 1
    fi
  fi

  git switch -c "$branch"
  git commit --allow-empty -q -m "$branch" -m "$note"
  printf '%s\t%s\n' "$branch" "$(git rev-parse HEAD)"
}

mmw_result_verify() {
  local branch="${1:-}" reported_head="${2:-}" base="${3:-}"
  [ -n "$branch" ] && [ -n "$reported_head" ] && [ -n "$base" ] || {
    echo "mmw: result verify 要 <结果分支> <HEAD SHA> <基点 SHA>" >&2
    return 1
  }
  local actual_head reported_sha base_sha
  actual_head="$(mmw_git_commit "refs/heads/$branch")" || return 1
  reported_sha="$(mmw_git_commit "$reported_head")" || return 1
  base_sha="$(mmw_git_commit "$base")" || return 1

  [ "$actual_head" = "$reported_sha" ] || {
    echo "mmw: ${branch} 当前 HEAD ${actual_head} 与报告不一致" >&2
    return 1
  }
  mmw_git_descends_from "$actual_head" "$base_sha" "$branch" || return 1

  local worktree_path
  worktree_path="$(mmw_git_worktree_of "$branch")" || {
    echo "mmw: 找不到 ${branch} 对应的 worktree；先恢复拥有该分支的后台任务" >&2
    return 1
  }
  printf 'verified\t%s\t%s\t%s\t%s\n' \
    "$branch" "$actual_head" "$(git rev-list --count "${base_sha}..${actual_head}")" "$worktree_path"
}

mmw_result_integrate() {
  local branch="${1:-}" reported_head="${2:-}" base="${3:-}"
  mmw_result_verify "$branch" "$reported_head" "$base" >/dev/null || return 1
  local target
  target="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  [ -n "$target" ] || {
    echo "mmw: result integrate 要求当前 checkout 已绑定目标分支" >&2
    return 1
  }
  [ "$target" != "$branch" ] || {
    echo "mmw: 结果分支不能与当前目标分支相同：${branch}" >&2
    return 1
  }
  mmw_git_contains "$base" || {
    echo "mmw: 基点 ${base} 不在当前目标分支 ${target} 的历史中" >&2
    return 1
  }
  mmw_git_clean . "不集成结果" || return 1
  git merge --no-ff --no-edit "$branch"
  printf 'integrated\t%s\t%s\n' "$branch" "$(git rev-parse HEAD)"
}

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
    mmw_git_commit "$from" >/dev/null || return 1
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
  if ! mmw_git_contains "$slug" "$root"; then
    echo "mmw: ${slug} 还没合并进 ${onto}，不清理" >&2
    return 1
  fi

  # 这一条是非强制形式：worktree 里有未提交改动时 git 会拒绝，命令带着非零退
  # 出码停在这里，由人决定要不要真的丢掉。
  git -C "$root" worktree remove "$dir"
  git -C "$root" branch -d "$slug"
}
