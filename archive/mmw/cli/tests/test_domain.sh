#!/usr/bin/env bash
# domain 只答两个机械问题：这个仓库是哪种形态、下一个 ADR 编号是几。
# 「这次要碰哪几个上下文」不在这里测，因为它不该在这里实现。

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
# macOS 的 /var 是 /private/var 的软链，git 给的是物理路径。
REPO="$(pwd -P)"

echo "domain path"

check "两个都没有时报 none" "none" "$("$MMW" domain path | cut -f1)"

printf 'glossary\n' > CONTEXT.md
check "只有根 CONTEXT.md 时报 single" "single" "$("$MMW" domain path | cut -f1)"
check "single 给出根 CONTEXT.md 的路径" "$REPO/CONTEXT.md" "$("$MMW" domain path | cut -f2)"

printf 'index\n' > CONTEXT-MAP.md
check "有索引时报 map，索引优先" "map" "$("$MMW" domain path | cut -f1)"
check "map 给出索引本身的路径" "$REPO/CONTEXT-MAP.md" "$("$MMW" domain path | cut -f2)"

echo
echo "domain adr-next"

check "没有 adr 目录时是 0001" "0001" "$("$MMW" domain adr-next)"

mkdir -p docs/adr
check "adr 目录空着时是 0001" "0001" "$("$MMW" domain adr-next)"

touch docs/adr/0001-first.md docs/adr/0002-second.md
check "有 0001 与 0002 时是 0003" "0003" "$("$MMW" domain adr-next)"

touch docs/adr/draft-42-pending.md
check "draft- 的不占号" "0003" "$("$MMW" domain adr-next)"

touch docs/adr/0010-tenth.md
check "取最大号加一，不是数个数" "0011" "$("$MMW" domain adr-next)"

touch docs/adr/0009-ninth.md
check "补上中间缺的号之后仍取最大号" "0011" "$("$MMW" domain adr-next)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
