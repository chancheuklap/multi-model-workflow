#!/usr/bin/env bash
# PostToolUse(commit):提交即记 step done(机器记,不让帮手手写进度)。
# 从 commit message 抽 Pack id(已被提交格式保证),记进 loop-state。PostToolUse 撤不回,只记不拦。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/../scripts/loop.sh"

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"
printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+commit' || exit 0

# 抽 "Pack N.M"(commit 格式由提交纪律保证;Ruling 1 同理,格式输入用 grep 解析合法)
pack="$(printf '%s' "$cmd" | grep -oE 'Pack[[:space:]]+[0-9]+\.[0-9]+' | head -1 || true)"
[ -n "$pack" ] || exit 0
id="$(printf '%s' "$pack" | awk '{print $2}')"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
[ -f "$top/.claude/multi-model-workflow/loop-state.json" ] || exit 0
sha="$(git -C "$top" rev-parse HEAD 2>/dev/null || echo "")"

( cd "$top" && bash "$LOOP" step done --id "$id" --commit "$sha" ) >/dev/null 2>&1 || true
exit 0
