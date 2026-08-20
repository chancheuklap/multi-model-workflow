#!/usr/bin/env bash
# 跑完这个技能的测试。改了 scripts/ 下任何东西之后跑一次。
#
#   bash mmw-v2/skills/exe-release/tests/run.sh
#
# PowerShell 那两条这里都验不了——Mac 上没有 PowerShell。手上有构建机时跑：
#
#   bash tests/check-generated-powershell.sh <构建机> <release.ps1>   # 语法
#   bash tests/check-template-behaviour.sh <构建机>                    # 那几个守卫函数判得对不对
#
# 语法过了不代表判得对：源码泄漏扫描误报过两次，每次都挡下了一个本来没问题的发布。
#
# 两份 Python 测试要 uv（引擎自己也要，manifest 校验走 uv run）。没装 uv 就说清楚
# 少跑了哪两份，不静默跳过。

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

run "引擎状态机" bash "$HERE/test_release_flow.sh"
run "失败分级" bash "$HERE/test_release_classify.sh"
run "修复派发与路径闸" bash "$HERE/test_release_dispatch.sh"

if command -v uv >/dev/null 2>&1; then
  run "合同、装配、诊断、派修与最小钥匙" \
    uv run --quiet --with pytest --with 'pydantic>=2' python -m pytest \
      "$HERE/test_release_contracts.py" \
      "$HERE/test_release_script_assembler.py" "$HERE/test_diagnose_core.py" \
      "$HERE/test_fix_dispatch.py" "$HERE/test_minimal_key.py" \
      "$HERE/test_verify_key.py" -q
else
  echo
  echo "没装 uv：Python 那几份没跑。引擎本身也要 uv 才能校验 manifest。" >&2
  rc=1
fi

echo
[ "$rc" -eq 0 ] && echo "全过" || echo "有失败，看上面" >&2
exit "$rc"
