#!/usr/bin/env bash
# 跑完 hook 层的测试。改了 mmw-v2/hooks/ 下任何东西之后跑一次。
#
#   bash mmw-v2/hooks/tests/run.sh
#
# 四份：注入脚本三家形状、完成拦截正反例、承重句校验自证、install.sh 在临时根装 hook。
# 只靠退出码说话；输出不要接管道，管道会把红跑成绿。

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
rc=0

# bash 自己的运行时错误（未绑定变量、参数为空导致的比较失败）出现在 $( ) 里时只杀掉子 shell：
# 外面拿到空串照常往下走，测试还是绿的，而引擎已经走进了另一条分支。所以这些字样一出现就算失败。
ENGINE_FAULTS=': unbound variable|: integer expression expected|: command not found|syntax error near'

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
    if grep -qE "$ENGINE_FAULTS" "$out"; then
      echo "### $label 失败：输出里有 bash 运行时错误" >&2
      grep -nE "$ENGINE_FAULTS" "$out" | sed 's/^/    /' >&2
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

if ! command -v node >/dev/null 2>&1; then
  echo "没装 node：hook 层全是 Node，一份都跑不了。" >&2
  exit 1
fi

run "注入脚本与分流形状" bash "$HERE/test_inject.sh"
run "完成拦截正反例" bash "$HERE/test_stop.sh"
run "承重句校验自证" bash "$HERE/test_invariants.sh"
run "install.sh 在临时根装 hook" bash "$HERE/test_install.sh"

echo
[ "$rc" -eq 0 ] && echo "全过" || echo "有失败，看上面" >&2
exit "$rc"
