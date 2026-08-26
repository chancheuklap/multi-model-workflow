#!/usr/bin/env bash
# Git 事实：几条谓词，每条只回答一个可验证的问题。
#
# 护栏散在各处时，同一个问题会被写好几遍，写法还各不相同。「工作区干净」曾经
# 有三份实现，其中两份写成 `[ -z "$(git status --porcelain)" ]`——git 一旦报
# 错，命令替换返回空串，判定就成了「干净」。这一层把每个问题收到一处。
#
# 谓词只回答事实，不做流程判断。要说「所以这次不派任务」还是「所以不集成结
# 果」，由调用方在自己的上下文里说。

set -euo pipefail

# 工作树是不是干净的。
# 用法：mmw_git_clean <目录> <不干净时接着说的那半句>
# 读不到状态时同样非零：git 报错不算干净。
mmw_git_clean() {
  local dir="${1:-}" why="${2:-}" st shown
  # 调用方常传 "."。报错里写一个裸点，读的人不知道说的是哪棵树。
  shown="$(cd "$dir" 2>/dev/null && pwd -P)" || shown="$dir"
  if ! st="$(git -C "$dir" status --porcelain 2>&1)"; then
    echo "mmw: 读不到 ${shown} 的 git 状态，${why}" >&2
    printf '%s\n' "$st" | sed 's/^/  /' >&2
    return 1
  fi
  [ -z "$st" ] && return 0
  echo "mmw: ${shown} 工作区不干净，${why}" >&2
  git -C "$dir" status --short >&2
  return 1
}

# 把一个 ref 解析成提交 SHA，解析得到就打到 stdout。
# 用法：mmw_git_commit <ref> [目录]
# 分支不存在、SHA 不是提交、写错了，都走这一条，不用在调用点各判一次。
mmw_git_commit() {
  local ref="${1:-}" dir="${2:-.}" sha
  sha="$(git -C "$dir" rev-parse --verify --quiet "${ref}^{commit}" 2>/dev/null)" || {
    echo "mmw: 不是这个仓库里的提交：${ref}" >&2
    return 1
  }
  printf '%s\n' "$sha"
}

# head 是不是严格从 base 长出来的：base 在 head 的历史里，而且确实长出了新提交。
# 用法：mmw_git_descends_from <head SHA> <base SHA> <这条线怎么称呼> [目录]
# 两种不成立的情况诊断不同，所以分开报。名字要带上：只给 SHA，读的人认不出是谁。
mmw_git_descends_from() {
  local head="${1:-}" base="${2:-}" name="${3:-}" dir="${4:-.}"
  if [ "$head" = "$base" ]; then
    echo "mmw: ${name} 停在基点上，没有产生新提交" >&2
    return 1
  fi
  git -C "$dir" merge-base --is-ancestor "$base" "$head" || {
    echo "mmw: ${name} 不是从基点 ${base} 开始的" >&2
    return 1
  }
}

# 这个 ref 是不是已经在当前 HEAD 的历史里（相等也算在内）。
# 用法：mmw_git_contains <ref> [目录]
# 与 mmw_git_descends_from 的区别只在相等这一种情况：那里要求真的往前走了，
# 这里问的是「已经收进来了没有」。
mmw_git_contains() {
  local ref="${1:-}" dir="${2:-.}"
  git -C "$dir" merge-base --is-ancestor "$ref" HEAD
}

# 这条分支挂在哪棵 worktree 上，挂着就打出那棵树的路径。
# 用法：mmw_git_worktree_of <分支名>
mmw_git_worktree_of() {
  git worktree list --porcelain | awk -v wanted="refs/heads/$1" '
    /^worktree / { path = substr($0, 10) }
    /^branch / && substr($0, 8) == wanted { print path; found = 1; exit }
    END { if (!found) exit 1 }
  '
}
