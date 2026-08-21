#!/usr/bin/env bash
# 跑完这个技能的测试。改了 scripts/ 下任何东西之后跑一次。
#
#   bash mmw-v2/skills/ui-qa/tests/run.sh
#
# 这里只覆盖机器能独自判对错的两件事：接线文件判得对不对，依赖齐没齐报得对不对。
# 九种检查判得准不准、一条 warning 该不该接受、报告怎么写——那些是技能与主 agent
# 的判断，不在这里断言。
#
# Python 那份要 uv。没装就说清楚少跑了什么，不静默跳过。

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
rc=0

# bash 自己的运行时错误出现在 $( ) 里时只杀掉子 shell，外面拿到空串照常往下走，
# 测试还是绿的而脚本已经走进了另一条分支。这些字样一出现就算失败。
FAULTS=': unbound variable|: integer expression expected|: command not found|syntax error near'

run() {
  local label="$1"
  shift
  echo
  echo "### $label"
  local out ok=0
  out="$(mktemp)"
  "$@" >"$out" 2>&1 || ok=1
  cat "$out"
  if [ "$ok" -eq 0 ]; then
    if grep -qE "$FAULTS" "$out"; then
      echo "### $label 失败：输出里有 bash 运行时错误" >&2
      grep -nE "$FAULTS" "$out" | sed 's/^/    /' >&2
      rc=1
    else
      echo "### $label 通过"
    fi
  else
    echo "### $label 失败" >&2
    rc=1
  fi
  rm -f "$out"
}

run "依赖检查" bash "$HERE/test_install_deps.sh"

if command -v uv >/dev/null 2>&1; then
  run "接线文件校验" \
    uv run --quiet --with pytest python -m pytest "$HERE/test_wiring_lint.py" -q
else
  echo
  echo "没装 uv：接线文件校验那份没跑。" >&2
  rc=1
fi

echo
[ "$rc" -eq 0 ] && echo "全过" || echo "有失败，看上面" >&2
exit "$rc"
