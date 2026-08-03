#!/usr/bin/env bash
# wiki nav 与 verify。不碰网络：Wiki 就是一个普通 git 仓库，本地造一个 bare
# 当远端就能把三条验证全走一遍。

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

git -C "$WORK" init -q repo
cp "$HERE/../mmw.default.json" "$WORK/repo/.mmw.json"
cd "$WORK/repo"

WIKI=".worktrees/.wiki"
mkdir -p "$WIKI"

page() {
  cat > "$WIKI/Spec-$1.md" <<EOF
<!-- mmw:spec
slug: $1
summary: $2
date: $3
pr: $4
-->

# $1
EOF
}

page feat-phone-login "手机号登录取代邮箱验证码" 2026-08-01 "https://github.com/o/r/pull/11"
page fix-refund-rounding "退款金额四舍五入错位" 2026-08-03 "https://github.com/o/r/pull/12"

echo "wiki nav"

"$MMW" wiki nav > /dev/null

got="$(grep -c '^| \[\[Spec-' "$WIKI/Home.md")"
check "Home 收录两份 spec" "2" "$got"

got="$(grep '^| \[\[Spec-' "$WIKI/Home.md" | head -1 | sed -E 's/^\| \[\[Spec-([a-z-]+)\\\|.*/\1/')"
check "Home 按落地日期倒序，最新的在前" "fix-refund-rounding" "$got"

got="$(grep -c 'pull/11' "$WIKI/Home.md")"
check "Home 带上 PR 链接" "1" "$got"

got="$(grep -c '^- \[\[Spec-' "$WIKI/_Sidebar.md")"
check "_Sidebar 列出两份" "2" "$got"

# 缺机器可读块的页面：不进导航，而且要报出来。
printf '# 手写的一页\n' > "$WIKI/Spec-legacy.md"
set +e
out="$("$MMW" wiki nav 2>&1)"
rc=$?
set -e
check "缺 mmw:spec 块时退出码非零" "1" "$rc"
got="$(grep -c 'Spec-legacy.md' <<<"$out" || true)"
check "缺块的页面被点名" "1" "$got"
got="$(grep -c 'Spec-legacy' "$WIKI/Home.md" || true)"
check "缺块的页面不进导航" "0" "$got"
rm "$WIKI/Spec-legacy.md"

echo
echo "wiki verify"

git init -q --bare "$WORK/wiki-remote.git"
git -C "$WIKI" init -q
git -C "$WIKI" remote add origin "$WORK/wiki-remote.git"
"$MMW" wiki nav > /dev/null
git -C "$WIKI" add -A
git -C "$WIKI" -c user.email=t@t -c user.name=t commit -q -m "wiki"

set +e
"$MMW" wiki verify feat-phone-login > /dev/null 2>&1
rc=$?
set -e
check "还没推上去，验证不过" "1" "$rc"

git -C "$WIKI" push -q -u origin HEAD:master
set +e
out="$("$MMW" wiki verify feat-phone-login 2>&1)"
rc=$?
set -e
check "推上去之后三条全过" "0" "$rc"

set +e
"$MMW" wiki verify no-such-slug > /dev/null 2>&1
rc=$?
set -e
check "页面不存在时验证不过" "1" "$rc"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
