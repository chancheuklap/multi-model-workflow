#!/usr/bin/env bash
# 在合并 Codex 后台任务结果前，验证报告里的分支、SHA 和分叉基点。
set -euo pipefail

usage() {
  echo '用法: verify-worker-result.sh <结果分支> <报告的 HEAD SHA> <派发前基点 SHA>' >&2
  exit 2
}

branch="${1:-}"
reported="${2:-}"
base="${3:-}"
[ $# -eq 3 ] || usage
case "$branch" in
  codex/*) ;;
  *) echo "MMW verify: 结果分支必须以 codex/ 开头：$branch" >&2; exit 1 ;;
esac

root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "MMW verify: 当前目录不在 Git worktree" >&2
  exit 1
}
status="$(git -C "$root" status --porcelain)" || {
  echo "MMW verify: 无法读取目标分支工作区状态" >&2
  exit 1
}
[ -z "$status" ] || {
  echo "MMW verify: 目标分支工作区不干净，拒绝合并" >&2
  git -C "$root" status --short >&2
  exit 1
}
git -C "$root" check-ref-format --branch "$branch" >/dev/null 2>&1 || {
  echo "MMW verify: 结果分支名非法：$branch" >&2
  exit 1
}
git -C "$root" show-ref --verify --quiet "refs/heads/$branch" || {
  echo "MMW verify: 本地结果分支不存在：$branch" >&2
  exit 1
}
reported="$(git -C "$root" rev-parse --verify "${reported}^{commit}" 2>/dev/null)" || {
  echo "MMW verify: 报告的 SHA 不是 commit" >&2
  exit 1
}
base="$(git -C "$root" rev-parse --verify "${base}^{commit}" 2>/dev/null)" || {
  echo "MMW verify: 派发前基点不是 commit" >&2
  exit 1
}
tip="$(git -C "$root" rev-parse "refs/heads/$branch")"
[ "$tip" = "$reported" ] || {
  echo "MMW verify: 分支 tip 与报告 SHA 不一致" >&2
  printf 'branch-tip: %s\nreported: %s\n' "$tip" "$reported" >&2
  exit 1
}
[ "$reported" != "$base" ] || {
  echo "MMW verify: 结果分支没有新增提交" >&2
  exit 1
}
git -C "$root" merge-base --is-ancestor "$base" "$reported" || {
  echo "MMW verify: 结果分支不是从派发基点继续出来的" >&2
  exit 1
}
current="$(git -C "$root" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
[ "$current" != "$branch" ] || {
  echo "MMW verify: 当前 checkout 就是结果分支，不能在自身上合并" >&2
  exit 1
}

printf 'verified-branch: %s\n' "$branch"
printf 'verified-head: %s\n' "$reported"
printf 'verified-base: %s\n' "$base"
