#!/usr/bin/env bash
# 结果树：Pi / Claude Code 从当前 HEAD 长出隔离 worktree，以及结果核对与合入。
#
# 任务工作树由用户和宿主创建。这里不认领、不绑定、不写 git 配置、不打空提交。

set -euo pipefail

mmw_current_name_segment() {
  local prefix="${1:-mmw artifact:}" branch slug git_dir common_dir
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "$prefix 当前目录不在 git 仓库里" >&2
    return 1
  }
  git_dir="$(git rev-parse --path-format=absolute --git-dir)"
  common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
  if [ "$git_dir" = "$common_dir" ]; then
    echo "$prefix 当前在仓库主检出里。请用户用当前宿主开一棵工作树再开会话。" >&2
    return 1
  fi
  branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  [ -n "$branch" ] || {
    echo "$prefix 当前没有任务分支。先 git switch -c <任务分支名>" >&2
    return 1
  }
  slug="${branch##*/}"
  mmw_path_safe_segment "$slug" "当前任务分支的名字段" "$prefix" || return 1
  printf '%s\n' "$slug"
}

mmw_worktree_dir() {
  local slug="$1"
  echo "$(mmw_main_root)/$(mmw_path_field worktrees)/$slug"
}

mmw_worktree_host_owns_trees() {
  case "$(mmw_host)" in
    codex)
      echo "mmw: Codex App 负责创建和回收 worktree" >&2
      return 1
      ;;
    cursor)
      echo "mmw: Cursor 负责创建和回收 ~/.cursor/worktrees 下的树" >&2
      return 1
      ;;
    grok)
      echo "mmw: Grok 负责创建和回收 managed worktree" >&2
      return 1
      ;;
  esac
  return 0
}

# 用法：mmw_worktree_add <结果分支>
mmw_worktree_add() {
  local branch="${1:-}"
  [ -n "$branch" ] || {
    echo "mmw: worktree add 要一个结果分支名" >&2
    return 1
  }
  [ $# -eq 1 ] || {
    echo "mmw: worktree add 只收结果分支名" >&2
    return 1
  }
  git check-ref-format --branch "$branch" >/dev/null 2>&1 || {
    echo "mmw: ${branch} 不是合法分支名" >&2
    return 1
  }
  mmw_path_safe_segment "$branch" "结果分支名" "mmw:" || return 1

  local root dir base
  root="$(mmw_main_root)"
  dir="$(mmw_worktree_dir "$branch")"

  if [ -e "$dir" ]; then
    echo "mmw: ${dir} 已经存在" >&2
    return 1
  fi
  if git show-ref --quiet --verify "refs/heads/$branch"; then
    echo "mmw: ${branch} 已存在" >&2
    return 1
  fi

  base="$(git rev-parse HEAD)"
  git -C "$root" worktree add -b "$branch" "$dir" "$base" >&2
  echo "$dir"
}

# 用法：mmw_worktree_remove <结果分支>
mmw_worktree_remove() {
  local slug="$1"
  [ -n "$slug" ] || {
    echo "mmw: worktree remove 要一个结果分支名" >&2
    return 1
  }
  local root dir onto here
  root="$(mmw_main_root)"
  dir="$(mmw_worktree_dir "$slug")"

  if ! git -C "$root" show-ref --quiet --verify "refs/heads/$slug"; then
    echo "mmw: 没有 ${slug} 这条分支" >&2
    return 1
  fi

  here="$(git rev-parse --show-toplevel)"
  if [ "$here" = "$dir" ]; then
    echo "mmw: 现在就在 ${slug} 这棵 worktree 里，先切到别处再清理" >&2
    return 1
  fi

  onto="$(git rev-parse --abbrev-ref HEAD)"
  if ! mmw_git_contains "$slug"; then
    echo "mmw: ${slug} 还没合并进 ${onto}，不清理" >&2
    return 1
  fi

  git worktree remove "$dir"
  git branch -d "$slug"
}

mmw_result_verify() {
  local branch="${1:-}" reported_head="${2:-}" base="${3:-}"
  [ -n "$branch" ] && [ -n "$reported_head" ] && [ -n "$base" ] || {
    echo "mmw: 结果核对要 <结果分支> <HEAD SHA> <基点 SHA>" >&2
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
    echo "mmw: result integrate 要求当前 checkout 已有任务分支" >&2
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
