#!/usr/bin/env bash
# 跑这个仓库的全部测试。跑法：bash mmw/test.sh
#
# 收的是行为测试：命令在真仓库上做了什么、护栏拒绝了什么、拒绝之后破坏有没有
# 发生、纯函数给定输入返回什么。不收「版本号五处互相相等」这类断言——它只证明
# 复制粘贴没出错，不证明任何行为，而且改内容忘了改版本号时它照样绿。
#
# Python 部分是 PEP 723 内联脚本，依赖写在被测文件头部，由 uv 装。

set -uo pipefail

MMW_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED=()

run() {
  local label="$1"; shift
  printf '\n======== %s ========\n' "$label"
  if "$@"; then
    return 0
  fi
  FAILED+=("$label")
}

run "CLI 护栏" bash "$MMW_DIR/cli/tests/guardrails.sh"
run "release 引擎" bash "$MMW_DIR/release/tests/test_release_flow.sh"
run "release 分级" bash "$MMW_DIR/release/tests/test_release_classify.sh"
run "release 修复派发与路径闸" bash "$MMW_DIR/release/tests/test_release_dispatch.sh"
run "图谱构建准入" python3 "$MMW_DIR/mcp/test_graphify_ensure.py"

if command -v uv >/dev/null 2>&1; then
  run "release 合同与出包脚本装配" \
    uv run --quiet --with pytest --with 'pydantic>=2' python -m pytest \
      "$MMW_DIR/release/tests/test_release_contracts.py" \
      "$MMW_DIR/release/tests/test_release_script_assembler.py" -q
  run "跨语言边与配置解析" \
    uv run --quiet --with pytest python -m pytest "$MMW_DIR/graph/tests/test_graph.py" -q
else
  # 装不了就明说，不要静默跳过：跳过和通过在输出里必须长得不一样。
  printf '\n======== 要 uv 的那几份 ========\n'
  echo "没装 uv，release 合同、出包脚本装配、跨语言边这三份没跑。"
  echo "release-flow.sh 本身也要 uv，装了再跑一次。"
  FAILED+=("要 uv 的那几份（没装 uv）")
fi

printf '\n========================================\n'
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "全部通过"
  exit 0
fi
printf '有没通过的：\n'
printf '  %s\n' "${FAILED[@]}"
exit 1
