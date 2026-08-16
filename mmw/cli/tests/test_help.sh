#!/usr/bin/env bash
# --help 是旗标：查用法，不执行。缺必填旗标时给一条能复制的调用，不倒整段用法。

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

contains() {
  local name="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       没找到：$needle" >&2
    echo "       实际：$haystack" >&2
    fail=$((fail + 1))
  fi
}

absent() {
  local name="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  失败 $name" >&2
    echo "       不应出现：$needle" >&2
    echo "       实际：$haystack" >&2
    fail=$((fail + 1))
  else
    echo "  过  $name"
    pass=$((pass + 1))
  fi
}

capture() {
  local label="$1"
  shift
  LAST_OUT="$WORK/${label}.out"
  LAST_ERR="$WORK/${label}.err"
  if "$@" >"$LAST_OUT" 2>"$LAST_ERR"; then
    LAST_STATUS=0
  else
    LAST_STATUS=$?
  fi
}

capture "顶层 --version" "$MMW" --version
check "顶层 --version 退出码" "0" "$LAST_STATUS"
check "顶层 --version 标准输出" "$(jq -er .version "$HERE/../../package.json")" "$(cat "$LAST_OUT")"
check "顶层 --version 没有标准错误" "" "$(cat "$LAST_ERR")"

echo "--help 查用法"

capture "顶层无参" "$MMW"
check "顶层无参退出码" "2" "$LAST_STATUS"
check "顶层无参没有标准输出" "" "$(cat "$LAST_OUT")"

capture "顶层 --help" "$MMW" --help
check "顶层 --help 退出码" "0" "$LAST_STATUS"
check "顶层 --help 没有标准输出" "" "$(cat "$LAST_OUT")"
contains "顶层 --help 列出命令" "artifact" "$(cat "$LAST_ERR")"
contains "顶层 --help 有 Examples" "Examples:" "$(cat "$LAST_ERR")"

capture "artifact --help" "$MMW" artifact --help
check "artifact --help 退出码" "0" "$LAST_STATUS"
contains "artifact --help 有 path 签名" "mmw artifact path" "$(cat "$LAST_ERR")"
contains "artifact --help 有 Examples" "mmw artifact path spec" "$(cat "$LAST_ERR")"

capture "artifact path --help" "$MMW" artifact path --help
check "artifact path --help 退出码" "0" "$LAST_STATUS"
absent "artifact path --help 不当成类别" "认不出的类别" "$(cat "$LAST_ERR")"
contains "artifact path --help 仍是 artifact 用法" "mmw artifact path spec" "$(cat "$LAST_ERR")"

capture "doctor --help" "$MMW" doctor --help
check "doctor --help 退出码" "0" "$LAST_STATUS"
absent "doctor --help 不跑体检" "CLI      :" "$(cat "$LAST_OUT")$(cat "$LAST_ERR")"
contains "doctor --help 写出命令" "mmw doctor" "$(cat "$LAST_ERR")"

capture "init --help" "$MMW" init --help
check "init --help 退出码" "0" "$LAST_STATUS"
absent "init --help 不跑配置" "配置     :" "$(cat "$LAST_OUT")$(cat "$LAST_ERR")"
contains "init --help 写出命令" "mmw init" "$(cat "$LAST_ERR")"

capture "worktree --help" env MMW_HOST=cursor "$MMW" worktree --help
check "worktree --help 退出码" "0" "$LAST_STATUS"
absent "worktree --help 不因宿主失败" "Cursor 负责创建和回收" "$(cat "$LAST_ERR")"
contains "worktree --help 写出命令" "mmw worktree add" "$(cat "$LAST_ERR")"

capture "release --help" "$MMW" release --help
check "release --help 退出码" "0" "$LAST_STATUS"
contains "release --help 写出 where" "mmw release where" "$(cat "$LAST_ERR")"
contains "release --help 有 Examples" "Examples:" "$(cat "$LAST_ERR")"

echo "缺旗标给正确调用"

capture "issue create 缺 --title" "$MMW" issue create
check "issue create 缺 --title 退出码" "2" "$LAST_STATUS"
contains "issue create 缺 --title 点名旗标" "要 --title" "$(cat "$LAST_ERR")"
contains "issue create 缺 --title 给出调用" "mmw issue create --title <标题> --body-file <文件>" "$(cat "$LAST_ERR")"
absent "issue create 缺 --title 不倒整段用法" "以上七条" "$(cat "$LAST_ERR")"

capture "agents materialize 缺 --host" "$MMW" agents materialize
check "agents materialize 缺 --host 退出码" "2" "$LAST_STATUS"
contains "agents materialize 缺 --host 点名旗标" "要 --host" "$(cat "$LAST_ERR")"
contains "agents materialize 缺 --host 给出调用" "mmw agents materialize --host <pi|cursor|grok|all>" "$(cat "$LAST_ERR")"
absent "agents materialize 缺 --host 不倒整段用法" "Claude Code：仍用 mmw dispatch" "$(cat "$LAST_ERR")"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
