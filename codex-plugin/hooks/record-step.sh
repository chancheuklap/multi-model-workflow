#!/usr/bin/env bash
# Codex PostToolUse：真实 git commit 落地后，从 HEAD 提交信息读取 Pack 并完成 loop step。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/runtime.sh
. "$SCRIPT_DIR/../scripts/lib/runtime.sh"
LOOP="$SCRIPT_DIR/../scripts/loop.sh"

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[ -n "$cmd" ] || exit 0

is_commit=0
cdir=""
segs="$(printf '%s\n' "$cmd" | tr ';|&(){}`' '\n')"
while IFS= read -r seg; do
  set -f
  # shellcheck disable=SC2086
  set -- $seg
  set +f
  while [ $# -gt 0 ]; do
    case "$1" in
      [A-Za-z_]*=*|sudo|env|command|nohup|time|nice|stdbuf) shift ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] && [ "$1" = git ] || continue
  shift
  dir=""
  while [ $# -gt 0 ]; do
    case "$1" in
      -C)
        shift
        [ $# -gt 0 ] && { dir="$1"; shift; }
        ;;
      -c|--git-dir|--work-tree|--namespace)
        shift
        [ $# -gt 0 ] && shift
        ;;
      -*) shift ;;
      *) break ;;
    esac
  done
  if [ $# -gt 0 ] && [ "$1" = commit ]; then
    is_commit=1
    cdir="$dir"
    break
  fi
done <<<"$segs"
[ "$is_commit" = 1 ] || exit 0

if [ -n "$cdir" ]; then
  top="$(git -C "$cdir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
else
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
fi

message="$(git -C "$top" log -1 --format=%B 2>/dev/null || true)"
pack="$(printf '%s' "$message" | grep -oE 'Pack[[:space:]]+[0-9]+\.[0-9]+' | head -1 || true)"
[ -n "$pack" ] || exit 0
id="$(printf '%s' "$pack" | awk '{print $2}')"

state_subdir="$(mmw_resolve_state_subdir "$top")"
[ -f "$top/$state_subdir/loop-state.json" ] || exit 0
sha="$(git -C "$top" rev-parse HEAD 2>/dev/null || true)"

if ! (cd "$top" && bash "$LOOP" step "done" --id "$id" --commit "$sha") >/dev/null 2>&1; then
  echo "record-step: HEAD 含 $pack，但 step done 失败；进度未记，请核查。" >&2
fi
