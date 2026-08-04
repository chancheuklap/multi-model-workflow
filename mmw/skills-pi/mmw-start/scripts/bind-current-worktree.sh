#!/usr/bin/env bash
# 把 Codex App 新建的干净 detached worktree 绑定为正式任务分支。
set -euo pipefail

usage() {
  echo '用法: bind-current-worktree.sh codex/<slug> "<用户原话>"' >&2
  exit 2
}

branch="${1:-}"
original="${2:-}"
[ $# -eq 2 ] || usage
case "$branch" in
  codex/*) ;;
  *) echo "MMW bind: 分支必须以 codex/ 开头：$branch" >&2; exit 1 ;;
esac
git check-ref-format --branch "$branch" >/dev/null 2>&1 || {
  echo "MMW bind: 分支名非法：$branch" >&2
  exit 1
}
[ -n "$original" ] || { echo "MMW bind: 用户原话不能为空" >&2; exit 1; }

root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "MMW bind: 当前目录不在 Git worktree" >&2
  exit 1
}
git_dir="$(git -C "$root" rev-parse --path-format=absolute --git-dir)"
common_dir="$(git -C "$root" rev-parse --path-format=absolute --git-common-dir)"
[ "$git_dir" != "$common_dir" ] || {
  echo "MMW bind: 当前 checkout 不是 linked worktree" >&2
  exit 1
}
if git -C "$root" symbolic-ref -q HEAD >/dev/null 2>&1; then
  echo "MMW bind: 当前 HEAD 已绑定分支；拒绝改绑" >&2
  exit 1
fi
status="$(git -C "$root" status --porcelain)" || {
  echo "MMW bind: 无法读取工作区状态" >&2
  exit 1
}
[ -z "$status" ] || {
  echo "MMW bind: 工作区不干净；确认任务前不能写入" >&2
  git -C "$root" status --short >&2
  exit 1
}
if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
  echo "MMW bind: 分支已存在：$branch" >&2
  exit 1
fi
git -C "$root" var GIT_AUTHOR_IDENT >/dev/null
git -C "$root" var GIT_COMMITTER_IDENT >/dev/null

base="$(git -C "$root" rev-parse HEAD)"
slug="${branch#codex/}"
git -C "$root" commit --allow-empty -m "chore(mmw): start $slug" -m "$original" >/dev/null
head="$(git -C "$root" rev-parse HEAD)"
git -C "$root" branch "$branch" "$head"
git -C "$root" switch "$branch" >/dev/null

printf 'branch: %s\n' "$branch"
printf 'base: %s\n' "$base"
printf 'head: %s\n' "$head"
