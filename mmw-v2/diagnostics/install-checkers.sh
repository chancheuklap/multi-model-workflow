#!/usr/bin/env bash
# 把编辑后诊断要用的检查器装齐，装进 mmw-v2 自己的 tools/，每次都装最新稳定版。
#
# 为什么装进自己的目录，不装进机器的全局环境：这台机器的全局 Node CLI 由
# ~/dev-environment 那个控制平面管，往里塞东西要经过它。而检查器是 MMW 的实现细节，
# 不是用户要用的命令行工具。装在这里，删掉 tools/ 重跑一次就全回来，也不会跟别的
# 东西抢版本。
#
# 例外是 shellcheck：它是二进制，没有 uv 或 pnpm 那种私有目录装法，走 Homebrew。
#
# 不锁版本。uv 与 pnpm 每次都拉最新稳定版，brew 每次都试着升。锁住换来的"一致"
# 只保证两个陈旧副本相同，不是我们要的。
#
# 装什么、归哪个包管理器，唯一来源是 rules.json 的 install 字段。这里不另存一份清单。
#
#   install-checkers.sh          装
#   install-checkers.sh --check  只看齐没齐，不动磁盘

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES="$HERE/rules.json"
TOOLS="$HERE/tools"
BIN="$TOOLS/bin"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-checkers.sh [--check]" >&2; exit 2 ;;
esac

[ -f "$RULES" ] || { echo "ERROR: 缺检查器表 ${RULES}" >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: 需要 jq" >&2; exit 2; }

packages_for() {
  jq -r --arg m "$1" '
    .checkers[]
    | select(.install.manager == $m)
    | [.install.package] + (.install.companions // [])
    | .[]
  ' "$RULES" | sort -u
}

rc=0

# Python 的检查器。UV_TOOL_DIR 与 UV_TOOL_BIN_DIR 让 uv 装进我们这个目录而不是
# ~/.local，实测这两个变量生效（uv tool dir 会把它们打出来）。
install_uv() {
  local pkgs pkg
  pkgs="$(packages_for uv)"
  [ -n "$pkgs" ] || return 0
  if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 缺 uv，装不了 $(echo "$pkgs" | tr '\n' ' ')。brew install uv" >&2
    return 1
  fi
  mkdir -p "$BIN"
  for pkg in $pkgs; do
    if UV_TOOL_DIR="$TOOLS/uv" UV_TOOL_BIN_DIR="$BIN" \
        uv tool install --upgrade "$pkg" >/dev/null 2>&1; then
      echo "装好  ${pkg} → ${BIN}"
    else
      echo "ERROR: 装 ${pkg} 失败" >&2
      return 1
    fi
  done
}

# Node 的检查器。用一个私有的包目录，不用 pnpm 的全局安装：全局那份由
# ~/dev-environment 管，不该被这里写。装完把可执行文件软链进 tools/bin，让
# check.py 只认一个目录。
install_pnpm() {
  local pkgs pkg spec=()
  pkgs="$(packages_for pnpm)"
  [ -n "$pkgs" ] || return 0
  if ! command -v pnpm >/dev/null 2>&1; then
    echo "ERROR: 缺 pnpm，装不了 $(echo "$pkgs" | tr '\n' ' ')" >&2
    return 1
  fi
  mkdir -p "$TOOLS/node" "$BIN"
  [ -f "$TOOLS/node/package.json" ] || printf '{"private":true}\n' > "$TOOLS/node/package.json"
  for pkg in $pkgs; do spec+=("${pkg}@latest"); done
  if ! (cd "$TOOLS/node" && pnpm add --silent "${spec[@]}" >/dev/null 2>&1); then
    echo "ERROR: 装 $(echo "$pkgs" | tr '\n' ' ') 失败" >&2
    return 1
  fi
  # 不往 tools/bin 软链。pnpm 的 .bin 项是按 $0 算相对路径的脚本外壳，链到别的
  # 目录之后它会去那个目录的上一级找自己的包，找不到就崩。实测 oxlint 会去
  # tools/.pnpm 找。check.py 直接把 node_modules/.bin 也当成工具目录。
  echo "装好  $(echo "$pkgs" | tr '\n' ' ')→ ${TOOLS}/node/node_modules/.bin"
}

# Homebrew 的那一个。已经装了就试着升；升不动不算失败，可能只是已经最新。
install_brew() {
  local pkgs pkg
  pkgs="$(packages_for brew)"
  [ -n "$pkgs" ] || return 0
  if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: 缺 brew，装不了 $(echo "$pkgs" | tr '\n' ' ')" >&2
    return 1
  fi
  for pkg in $pkgs; do
    if brew list --formula "$pkg" >/dev/null 2>&1; then
      brew upgrade "$pkg" >/dev/null 2>&1 || true
      echo "已装  ${pkg}（Homebrew）"
    elif brew install "$pkg" >/dev/null 2>&1; then
      echo "装好  ${pkg}（Homebrew）"
    else
      echo "ERROR: 装 ${pkg} 失败" >&2
      return 1
    fi
  done
}

if [ "$mode" = check ]; then
  python3 "$HERE/check.py" --doctor || rc=1
else
  install_uv || rc=1
  install_pnpm || rc=1
  install_brew || rc=1
  echo
  python3 "$HERE/check.py" --doctor || rc=1
fi

exit "$rc"
