#!/usr/bin/env bash
# 派发参数是宿主会话真正执行 subagent 的合同。MMW 的 subagent 一律后台运行；
# 这个行为由 adapter 明写，不能依赖用户级默认配置。

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

params() {
  sed -n 's/^params: //p' | jq -c .
}

git -C "$WORK" init -q repo
cp "$HERE/../mmw.default.json" "$WORK/repo/.mmw.json"
printf '只读烟雾测试。\n' > "$WORK/repo/brief.md"
cd "$WORK/repo"

printf 'Pi 后台派发\n'
pi_params="$(MMW_HOST=pi "$MMW" dispatch investigator --brief "$WORK/repo/brief.md" | params)"
check "adapter 显式要求 async，不吃用户默认值" "true" "$(jq -r '.async' <<<"$pi_params")"
check "上下文仍然隔离" "fresh" "$(jq -r '.context' <<<"$pi_params")"

printf '\nClaude Code 后台派发\n'
claude_params="$(MMW_HOST=claude-code "$MMW" dispatch reviewer-claude --brief "$WORK/repo/brief.md" | params)"
check "Agent 工具显式在后台运行" "true" "$(jq -r '.run_in_background' <<<"$claude_params")"

printf '\n过 %s，失败 %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
