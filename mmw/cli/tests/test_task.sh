#!/usr/bin/env bash
# 任务隔离。要验的核心是：从任何一棵树上跑，新 worktree 都落在主仓库的
# .worktrees/ 下——分支可以嵌套，目录不嵌套。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$HERE/../mmw"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
check() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       想要：$want" >&2
    echo "       得到：$got" >&2
    fail=$((fail + 1))
  fi
}

export MMW_HOST=claude-code
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

git -C "$WORK" init -q -b main repo
cp "$HERE/../mmw.default.json" "$WORK/repo/.mmw.json"
cd "$WORK/repo"
git add -A && git commit -q -m "init"
MAIN="$(pwd -P)"

echo "task new"

got="$("$MMW" task new feat-one "用户说要做第一件事" 2>/dev/null)"
check "落在主仓库的 .worktrees/ 下" "$MAIN/.worktrees/feat-one" "$got"

check "记住用户原话的空提交" "用户说要做第一件事" \
  "$(git -C .worktrees/feat-one log -1 --format='%b' | head -1)"
check "空提交的标题是 slug" "feat-one" \
  "$(git -C .worktrees/feat-one log -1 --format='%s')"

got="$("$MMW" task enter feat-one)"
check "enter 给出同一个路径" "$MAIN/.worktrees/feat-one" "$got"

set +e
"$MMW" task new feat-one "重复" > /dev/null 2>&1
rc=$?
set -e
check "同名已存在时失败" "非零" "$([ "$rc" -ne 0 ] && echo 非零 || echo 零)"

echo
echo "从 worktree 里再建一棵"

cd "$MAIN/.worktrees/feat-one"
got="$("$MMW" task new feat-two "从第一棵分叉" 2>/dev/null)"
check "仍落在主仓库的 .worktrees/ 下，不嵌套" "$MAIN/.worktrees/feat-two" "$got"

check "从当前分支分叉" "feat-one" \
  "$(git -C "$MAIN/.worktrees/feat-two" log --format='%s' | sed -n '2p')"

echo
echo "挂回已有分支"

cd "$MAIN"
git worktree remove .worktrees/feat-two
got="$("$MMW" task new feat-two 2>/dev/null)"
check "分支还在时挂回去" "$MAIN/.worktrees/feat-two" "$got"
check "挂回去不再打空提交" "feat-two" \
  "$(git -C .worktrees/feat-two log -1 --format='%s')"

echo
echo "task cleanup"

nonzero() { [ "$1" -ne 0 ] && echo 非零 || echo 零; }

set +e
printf 'dirty\n' > .worktrees/feat-one/x.txt
"$MMW" task cleanup feat-one > /dev/null 2>&1
rc=$?
set -e
check "工作区不干净时拒绝清理" "非零" "$(nonzero $rc)"
check "拒绝之后 worktree 还在" "yes" \
  "$([ -d .worktrees/feat-one ] && echo yes || echo no)"

rm .worktrees/feat-one/x.txt
set +e
"$MMW" task cleanup feat-one > /dev/null 2>&1
rc=$?
set -e
check "分支没合并进来时也拒绝" "非零" "$(nonzero $rc)"
check "被拒之后 worktree 还在，不是半完成" "yes" \
  "$([ -d .worktrees/feat-one ] && echo yes || echo no)"

git merge --no-ff feat-one -m "merge feat-one" >/dev/null
set +e
out="$("$MMW" task cleanup feat-one 2>&1)"
rc=$?
set -e
[ "$rc" -eq 0 ] || echo "       cleanup 说：$out" >&2
check "干净且已合并才清得掉" "no" \
  "$([ -d .worktrees/feat-one ] && echo yes || echo no)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
