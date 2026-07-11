#!/usr/bin/env bash
# PostToolUse(commit):提交即记 step done
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/host.sh
. "$SCRIPT_DIR/../scripts/lib/host.sh"
LOOP="$SCRIPT_DIR/../scripts/loop.sh"

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"

# 只认命令位的 git commit——echo/文档文本里提到 "git commit ... Pack N.M" 不算,防误记进度
is_commit=0
segs="$(printf '%s\n' "$cmd" | tr ';|&()`' '\n')"
while IFS= read -r seg; do
  set -f
  # shellcheck disable=SC2086
  set -- $seg
  set +f
  while [ $# -gt 0 ]; do
    case "$1" in
      [A-Za-z_]*=*|sudo|env|command|nohup|time) shift ;;
      *) break ;;
    esac
  done
  if [ $# -ge 2 ] && [ "$1" = "git" ] && [ "$2" = "commit" ]; then is_commit=1; break; fi
done <<< "$segs"
[ "$is_commit" = "1" ] || exit 0

pack="$(printf '%s' "$cmd" | grep -oE 'Pack[[:space:]]+[0-9]+\.[0-9]+' | head -1 || true)"
[ -n "$pack" ] || exit 0
id="$(printf '%s' "$pack" | awk '{print $2}')"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_SUBDIR="$(mmw_resolve_state_subdir "$top")"
[ -f "$top/$STATE_SUBDIR/loop-state.json" ] || exit 0
sha="$(git -C "$top" rev-parse HEAD 2>/dev/null || echo "")"

if ! ( cd "$top" && bash "$LOOP" step done --id "$id" --commit "$sha" ) >/dev/null 2>&1; then
  echo "record-step: 提交含 $pack 但 step done 失败(id=$id);进度未记,请人核。" >&2
fi
exit 0
