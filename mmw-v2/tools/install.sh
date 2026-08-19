#!/usr/bin/env bash
# 装齐这台机器上的语言工具，装进 mmw-v2/tools/，每次装最新稳定版。
#
# 一份安装，两个消费者：编辑后诊断跑这些检查器，serena 用这些语言服务器。pyright
# 这一条同时是两者——同一个包的两个入口。所以清单只有一张（tools.json），装出来的
# 也只有一份，不会出现同一个引擎两个版本。
#
# 装在自己的目录里，不碰机器的全局环境：这些是 agent 的工具，不是用户敲的命令。
# ~/dev-environment 管的是后者（brew、shell 启动、你自己用的 CLI），跟这里互不影响。
# 例外是 shellcheck：编译好的二进制，没有私有目录装法，走 Homebrew。
#
# 不锁版本。uv 与 pnpm 每次拉最新稳定版，brew 每次试着升。锁住换来的一致只保证两个
# 陈旧副本相同。
#
#   install.sh          装，并把 serena 指过来
#   install.sh --check  只看齐没齐，不动磁盘

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS="$HERE/tools.json"
BIN="$HERE/bin"
NODE_DIR="$HERE/node"
NODE_BIN="$NODE_DIR/node_modules/.bin"
SERENA_CONFIG="${MMW_SERENA_HOME:-$HOME/.serena}/serena_config.yml"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install.sh [--check]" >&2; exit 2 ;;
esac

[ -f "$TOOLS" ] || { echo "ERROR: 缺工具清单 ${TOOLS}" >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: 需要 jq" >&2; exit 2; }

packages_for() {
  jq -r --arg m "$1" '
    .tools[]
    | select(.install.manager == $m)
    | [.install.package] + (.install.companions // [])
    | .[]
  ' "$TOOLS" | sort -u
}

rc=0

# Python 那几个。UV_TOOL_DIR 与 UV_TOOL_BIN_DIR 让 uv 装进这里而不是 ~/.local，
# 实测这两个变量生效（uv tool dir 会把它们打出来）。
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
    if UV_TOOL_DIR="$HERE/uv" UV_TOOL_BIN_DIR="$BIN" \
        uv tool install --upgrade "$pkg" >/dev/null 2>&1; then
      echo "装好  ${pkg} → ${BIN}"
    else
      echo "ERROR: 装 ${pkg} 失败" >&2
      return 1
    fi
  done
}

# Node 那几个。用一个私有的包目录，不用 pnpm 的全局安装。
#
# 不往别处软链：pnpm 的 .bin 项是按 $0 算相对路径的脚本外壳，链到别的目录之后它会
# 去那个目录的上一级找自己的包，找不到就崩（实测 oxlint 会去 tools/.pnpm 找）。
# check.py 与 serena 都直接用 node_modules/.bin 里的原件。
install_pnpm() {
  local pkgs pkg spec=()
  pkgs="$(packages_for pnpm)"
  [ -n "$pkgs" ] || return 0
  if ! command -v pnpm >/dev/null 2>&1; then
    echo "ERROR: 缺 pnpm，装不了 $(echo "$pkgs" | tr '\n' ' ')" >&2
    return 1
  fi
  mkdir -p "$NODE_DIR"
  [ -f "$NODE_DIR/package.json" ] || printf '{"private":true}\n' > "$NODE_DIR/package.json"
  for pkg in $pkgs; do spec+=("${pkg}@latest"); done
  if ! (cd "$NODE_DIR" && pnpm add --silent "${spec[@]}" >/dev/null 2>&1); then
    echo "ERROR: 装 $(echo "$pkgs" | tr '\n' ' ') 失败" >&2
    return 1
  fi
  echo "装好  $(echo "$pkgs" | tr '\n' ' ')→ ${NODE_BIN}"
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

# 把 serena 的语言服务器指到上面装的这一份。yaml 用 uv 临时带：系统 python3 没有它，
# 而 uv 已经是这个安装器的硬依赖。
wire_serena() {
  local args=(--tools "$TOOLS" --bin-dir "$BIN" --node-bin-dir "$NODE_BIN" --config "$SERENA_CONFIG")
  [ "$mode" = check ] && args+=(--check)
  uv run --quiet --with pyyaml python3 "$HERE/serena-language-servers.py" "${args[@]}"
}

if [ "$mode" = check ]; then
  python3 "$HERE/../diagnostics/check.py" --doctor || rc=1
  wire_serena || rc=1
else
  install_uv || rc=1
  install_pnpm || rc=1
  install_brew || rc=1
  echo
  python3 "$HERE/../diagnostics/check.py" --doctor || rc=1
  wire_serena || rc=1
fi

exit "$rc"
