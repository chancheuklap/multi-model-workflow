#!/usr/bin/env bash
# 跑完这个技能的五份测试。改了 scripts/ 下任何东西之后跑一次。
#
#   bash mmw-v2/skills/exe-release/tests/run.sh
#
# 生成出来的 PowerShell 语法对不对，这里验不了——Mac 上没有 PowerShell 解析器。
# 手上有构建机时跑 check-generated-powershell.sh，它把脚本送到构建机上让 PowerShell 自己解析。
#
# 两份 Python 测试要 uv（引擎自己也要，manifest 校验走 uv run）。没装 uv 就说清楚
# 少跑了哪两份，不静默跳过。

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
rc=0

run() {
  local label="$1"
  shift
  echo
  echo "### $label"
  if "$@"; then
    echo "### $label 通过"
  else
    echo "### $label 失败" >&2
    rc=1
  fi
}

run "引擎状态机" bash "$HERE/test_release_flow.sh"
run "失败分级" bash "$HERE/test_release_classify.sh"
run "修复派发与路径闸" bash "$HERE/test_release_dispatch.sh"

if command -v uv >/dev/null 2>&1; then
  run "合同与出包脚本装配" \
    uv run --quiet --with pytest --with 'pydantic>=2' python -m pytest \
      "$HERE/test_release_contracts.py" "$HERE/test_release_script_assembler.py" \
      "$HERE/test_release_script_assembler_v2.py" -q
else
  echo
  echo "没装 uv：合同与出包脚本装配这几份没跑。引擎本身也要 uv 才能校验 manifest。" >&2
  rc=1
fi

echo
[ "$rc" -eq 0 ] && echo "五份全过" || echo "有失败，看上面" >&2
exit "$rc"
