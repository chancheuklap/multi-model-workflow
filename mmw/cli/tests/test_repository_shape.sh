#!/usr/bin/env bash
# 仓库只发布 mmw。旧宿主源码和 release manifest 必须留在 archive，不能重新出现在根目录。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"

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

printf '唯一活跃发布面\n'
for path in plugin droid-plugin pi-plugin cursor-plugin .factory-plugin .cursor-plugin advisor docs; do
  if [ -e "$ROOT/$path" ]; then
    check "根目录没有 $path" "不存在" "存在"
  else
    check "根目录没有 $path" "不存在" "不存在"
  fi
done

marketplace="$ROOT/.claude-plugin/marketplace.json"
check "Claude marketplace 只发布一个插件" "1" "$(jq '.plugins | length' "$marketplace")"
check "唯一插件名是 mmw" "mmw" "$(jq -r '.plugins[0].name' "$marketplace")"
check "唯一插件从 mmw 目录发布" "./mmw" "$(jq -r '.plugins[0].source' "$marketplace")"

printf '\n版本同步\n'
market_version="$(jq -r '.plugins[0].version' "$marketplace")"
check "Claude manifest 与 marketplace 同版" "$market_version" \
  "$(jq -r '.version' "$ROOT/mmw/.claude-plugin/plugin.json")"
check "Pi package 与 marketplace 同版" "$market_version" \
  "$(jq -r '.version' "$ROOT/mmw/package.json")"
check "marketplace 顶层版本同步" "$market_version" "$(jq -r '.version' "$marketplace")"
# 版本号具体是多少由发布决定，这里不锁字面值。锁了的话每次升版都要同步改这一行，
# 0.4.0 升 0.5.0 那次就漏了——测试红了，而产品没坏。上面三条已经守住四处同版，
# 这里只再守形状：发布出去的必须是一个合法的语义化版本。
check "版本号是语义化版本" "合法" \
  "$(printf '%s' "$market_version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' && echo 合法 || echo "不合法：$market_version")"

printf '\n归档完整\n'
archive="$ROOT/archive/legacy-host-plugins"
for path in plugin droid-plugin pi-plugin cursor-plugin .factory-plugin .cursor-plugin advisor docs .claude-plugin/marketplace.json; do
  if [ -e "$archive/$path" ]; then
    check "归档包含 $path" "存在" "存在"
  else
    check "归档包含 $path" "存在" "不存在"
  fi
done
if [ -e "$ROOT/archive/mmw-rebuild-completed/MMW-REBUILD.md" ]; then
  check "重建记录进入归档" "存在" "存在"
else
  check "重建记录进入归档" "存在" "不存在"
fi
if [ -e "$ROOT/mmw-skill-map.html" ]; then
  check "当前架构 HTML 保留在根目录" "存在" "存在"
else
  check "当前架构 HTML 保留在根目录" "存在" "不存在"
fi

printf '\n过 %s，失败 %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
