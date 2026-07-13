#!/usr/bin/env bash
# PostToolUse(commit):提交即记 step done。
# 真值链:命令位确认是 git commit(含 -C/-c 等全局选项)→ Pack 号和 sha 从 HEAD 提交信息取——
# 命令文本里的 Pack 字样不作数(echo/后续段里的不算),commit 失败 HEAD 没动就不记。
# Hook 的 if 前筛认 `git commit`/`git -C` 打头;env 赋值前缀(FOO=1 git commit)不会唤醒。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/runtime.sh
. "$SCRIPT_DIR/../scripts/lib/runtime.sh"
LOOP="$SCRIPT_DIR/../scripts/loop.sh"

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"

# 只认命令位的 git commit;剥 git 全局选项,-C 的目标目录记下来当仓库根
is_commit=0; cdir=""
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
  [ $# -gt 0 ] && [ "$1" = "git" ] || continue
  shift
  d=""
  while [ $# -gt 0 ]; do
    case "$1" in
      -C) shift; [ $# -gt 0 ] && { d="$1"; shift; } ;;
      -c|--git-dir|--work-tree|--namespace) shift; [ $# -gt 0 ] && shift ;;
      -*) shift ;;
      *) break ;;
    esac
  done
  if [ $# -gt 0 ] && [ "$1" = "commit" ]; then is_commit=1; cdir="$d"; break; fi
done <<< "$segs"
[ "$is_commit" = "1" ] || exit 0

if [ -n "$cdir" ]; then
  top="$(git -C "$cdir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
else
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
fi

# Pack 号从 HEAD 提交信息取(盘上真相):commit 失败 HEAD 没动 → 信息里没有新 Pack → 不记
msg="$(git -C "$top" log -1 --format=%B 2>/dev/null || true)"
pack="$(printf '%s' "$msg" | grep -oE 'Pack[[:space:]]+[0-9]+\.[0-9]+' | head -1 || true)"
[ -n "$pack" ] || exit 0
id="$(printf '%s' "$pack" | awk '{print $2}')"

STATE_SUBDIR="$MMW_STATE_SUBDIR"
[ -f "$top/$STATE_SUBDIR/loop-state.json" ] || exit 0
sha="$(git -C "$top" rev-parse HEAD 2>/dev/null || echo "")"

if ! ( cd "$top" && bash "$LOOP" step done --id "$id" --commit "$sha" ) >/dev/null 2>&1; then
  echo "record-step: HEAD 含 $pack 但 step done 失败(id=$id);进度未记,请人核。" >&2
fi
exit 0
