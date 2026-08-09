#!/usr/bin/env bash
# 从 MMW 源码仓库构建一次 runtime，并安装到本机已有的各个宿主。

set -euo pipefail

# 安装期间跑的 Python 不写 .pyc：物化和体检都在 runtime 里执行，写出来的
# __pycache__ 就留在发布产物里了，而清理发生在它们之前，删不掉。
export PYTHONDONTWRITEBYTECODE=1

SOURCE_MMW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SOURCE_MMW/.." && pwd)"
RUNTIME_HOME="${MMW_RUNTIME_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/mmw}"
RUNTIME_ROOT="$RUNTIME_HOME/runtime"
BIN_DIR="${MMW_BIN_DIR:-$HOME/.local/bin}"
FORWARD_HEADER="# Managed by MMW source installer."

die() {
  echo "mmw install: $1" >&2
  exit "${2:-1}"
}

require_source_repo() {
  [ -f "$SOURCE_REPO/.agents/plugins/marketplace.json" ] \
    || die "找不到 Codex marketplace：$SOURCE_REPO/.agents/plugins/marketplace.json"
  [ -f "$SOURCE_REPO/.claude-plugin/marketplace.json" ] \
    || die "找不到 Claude Code marketplace：$SOURCE_REPO/.claude-plugin/marketplace.json"
  [ -f "$SOURCE_MMW/.codex-plugin/plugin.json" ] \
    || die "当前目录不是完整的 MMW 源码仓库：$SOURCE_MMW"
}

verify_source() {
  "$SOURCE_MMW/cli/mmw" skills materialize --host all --check
  "$SOURCE_MMW/cli/mmw" agents materialize --host pi --check
  python3 "$SOURCE_MMW/codex/runtime.py" materialize --check
}

build_runtime() {
  local stage previous
  mkdir -p "$RUNTIME_HOME"
  stage="$(mktemp -d "$RUNTIME_HOME/.runtime.XXXXXX")"
  mkdir -p "$stage/.agents/plugins" "$stage/.claude-plugin"
  cp "$SOURCE_REPO/.agents/plugins/marketplace.json" "$stage/.agents/plugins/marketplace.json"
  cp "$SOURCE_REPO/.claude-plugin/marketplace.json" "$stage/.claude-plugin/marketplace.json"
  cp -R "$SOURCE_MMW" "$stage/mmw"
  printf '%s\n' "$SOURCE_REPO" > "$stage/.mmw-source-root"

  # 测试只在源码仓库跑，不跟着发到各宿主：它们要 uv、要建一次性 git 仓库，
  # 装到用户机器上既用不到，又把 plugin 撑大。Python 缓存同理。
  # -prune 不能省：不剪枝的话 find 会走进刚被 rm 掉的目录，报错退非零，
  # 而那个错误正好被 2>/dev/null 吞掉，看起来像删干净了。
  rm -f "$stage/mmw/test.sh" "$stage/mmw/mcp/test_graphify_ensure.py"
  find "$stage/mmw" -type d \( -name tests -o -name __pycache__ -o -name .pytest_cache \) \
    -prune -exec rm -rf {} +

  if [ -d "$stage/mmw/skill-rebuilds" ]; then
    find "$stage/mmw/skill-rebuilds" -depth -delete
  fi
  if [ -d "$stage/mmw/wayfinder-rebuild" ]; then
    find "$stage/mmw/wayfinder-rebuild" -depth -delete
  fi

  previous="$RUNTIME_HOME/runtime.previous"
  if [ -e "$previous" ]; then
    find "$previous" -depth -delete
  fi
  if [ -e "$RUNTIME_ROOT" ]; then
    mv "$RUNTIME_ROOT" "$previous"
  fi
  mv "$stage" "$RUNTIME_ROOT"
  echo "runtime  : $RUNTIME_ROOT"
}

# 同一个版本号下改了内容就停下。
#
# Codex 与 Claude Code 运行的都是 plugins/cache 里的副本，不是这份 runtime。
# Claude Code 的 plugin update 按版本号判定：版本号不动，它认定已是最新，副本
# 一个字都不换。于是「install.sh 报了已安装」和「宿主真的读到新内容」是两回事。
#
# 绕过去的办法是 uninstall 再 install 强行覆盖，但那等于把版本号这道机制废掉，
# 而且只有动手的人知道自己绕过了，下一个人照样踩。所以这里直接拦：内容变了就
# 升版本号，五处一起升（见 AGENTS.md）。
require_version_bump() {
  local version cache_dir
  version="$(jq -er '.version' "$RUNTIME_ROOT/mmw/.claude-plugin/plugin.json")" \
    || die "读不出 runtime 的插件版本"
  for cache_dir in \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/cache/multi-model-workflow/mmw/$version" \
    "${CODEX_HOME:-$HOME/.codex}/plugins/cache/mmw-codex/mmw/$version"; do
    [ -d "$cache_dir" ] || continue
    if ! diff -r -q -x '__pycache__' -x '*.pyc' \
        "$RUNTIME_ROOT/mmw" "$cache_dir" >/dev/null 2>&1; then
      echo "mmw install: 版本仍是 ${version}，但内容与已安装副本不同：" >&2
      diff -r -q -x '__pycache__' -x '*.pyc' "$RUNTIME_ROOT/mmw" "$cache_dir" 2>&1 \
        | sed 's/^/  /' >&2
      die "先把五处版本号一起升上去再装（见 AGENTS.md「版本号位置」）"
    fi
  done
}

install_forwarder() {
  local target current temp
  target="$BIN_DIR/mmw"
  mkdir -p "$BIN_DIR"
  if [ -e "$target" ]; then
    current="$(sed -n '2p' "$target" 2>/dev/null || true)"
    case "$current" in
      "$FORWARD_HEADER"|"# Managed by MMW Codex runtime.") ;;
      *)
        grep -q 'multi-model-workflow/mmw/cli/mmw' "$target" 2>/dev/null \
          || die "拒绝覆盖非 MMW 管理的命令：$target"
        ;;
    esac
  fi
  temp="$(mktemp "$BIN_DIR/.mmw.XXXXXX")"
  cat > "$temp" <<EOF
#!/usr/bin/env bash
$FORWARD_HEADER
set -euo pipefail
exec "$RUNTIME_ROOT/mmw/cli/mmw" "\$@"
EOF
  chmod 0755 "$temp"
  mv "$temp" "$target"
  echo "mmw CLI  : $target"
}

install_codex() {
  command -v codex >/dev/null 2>&1 || { echo "Codex    : 未安装，跳过"; return; }
  local marketplace_json marketplace
  marketplace_json="$(codex plugin marketplace add "$RUNTIME_ROOT" --json)"
  marketplace="$(jq -er '.marketplaceName' <<< "$marketplace_json")" \
    || die "Codex marketplace 安装结果缺少 marketplaceName"
  codex plugin add "mmw@$marketplace" --json >/dev/null
  python3 "$RUNTIME_ROOT/mmw/codex/runtime.py" install
  echo "Codex    : 已安装 mmw@$marketplace"
}

install_claude_code() {
  command -v claude >/dev/null 2>&1 || { echo "Claude   : 未安装，跳过"; return; }
  local name="multi-model-workflow" registered installed settings temp
  registered="$(claude plugin marketplace list --json \
    | jq -r --arg n "$name" '.[] | select(.name == $n) | (.path // .installLocation)')"
  if [ -n "$registered" ] && [ "$registered" != "$RUNTIME_ROOT" ]; then
    claude plugin marketplace remove "$name" >/dev/null
  fi
  if [ "$registered" != "$RUNTIME_ROOT" ]; then
    claude plugin marketplace add "$RUNTIME_ROOT" >/dev/null
  fi
  installed="$(claude plugin list --json \
    | jq -r --arg n "mmw@$name" '.[] | select((.id // .name // "") == $n or .name == "mmw") | (.id // .name)')"
  if [ -n "$installed" ]; then
    claude plugin update "mmw@$name" >/dev/null
  else
    claude plugin install "mmw@$name" --scope user >/dev/null
  fi
  MMW_AGENT_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills" \
    bash "$RUNTIME_ROOT/mmw/cli/lib/install-agent-skills.sh"
  settings="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
  mkdir -p "$(dirname "$settings")"
  if [ ! -f "$settings" ]; then
    printf '{}\n' > "$settings"
  fi
  jq -e . "$settings" >/dev/null 2>&1 \
    || die "Claude Code 配置不是合法 JSON：$settings"
  temp="$(mktemp "$(dirname "$settings")/.settings.XXXXXX")"
  jq '.permissions.allow = (((.permissions.allow // []) + ["Bash(mmw:*)"]) | unique)' \
    "$settings" > "$temp"
  mv "$temp" "$settings"
  echo "Claude   : 已安装 mmw@$name"
  install_claude_code_lsp
}

# Claude Code 原生的语言服务器插件，装到用户级。
#
# 装用户级不装项目级：项目级 enabledPlugins 指向内建 marketplace 的插件时，Claude Code
# 不会自动安装也不提示（anthropics/claude-code#41669），等于每台新电脑、每个新仓库都要
# 人手动装一次。用户级一次装好，之后每个仓库都有。
#
# 这些插件只在仓库里有对应语言的文件时才起语言服务器，没有 Python 的仓库装了也不耗资源。
install_claude_code_lsp() {
  local plugin installed
  installed="$(claude plugin list --json 2>/dev/null | jq -r '.[] | (.id // .name // "")')"
  for plugin in pyright-lsp typescript-lsp; do
    case "$installed" in
      *"$plugin"*) echo "Claude   : $plugin 已在" ; continue ;;
    esac
    if claude plugin install "$plugin@claude-plugins-official" --scope user >/dev/null 2>&1; then
      echo "Claude   : 已装 $plugin（用户级）"
    else
      echo "Claude   : 装不上 $plugin，自己跑 claude plugin install $plugin@claude-plugins-official 看报什么"
    fi
  done
}

remove_old_pi_mmw() {
  local settings source resolved resolved_parent package_name
  settings="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME/.pi}/agent}/settings.json"
  [ -f "$settings" ] || return 0
  while IFS= read -r source; do
    [ -n "$source" ] || continue
    case "$source" in
      /*) resolved="$source" ;;
      npm:*|git:*|http:*|https:*|ssh:*) continue ;;
      *)
        resolved_parent="$(cd "$(dirname "$settings")" \
          && cd "$(dirname "$source")" 2>/dev/null && pwd -P || true)"
        [ -n "$resolved_parent" ] || continue
        resolved="$resolved_parent/$(basename "$source")"
        ;;
    esac
    [ -f "$resolved/package.json" ] || continue
    package_name="$(jq -r '.name // empty' "$resolved/package.json")"
    [ "$package_name" = "@cheuklapchan/mmw" ] || continue
    pi remove "$resolved" >/dev/null
  done < <(jq -r '.packages[]? | if type == "string" then . else .source // empty end' "$settings")
}

# 编辑后诊断在 Pi 那一侧靠扩展，不靠 hook——Pi 没有 hooks.json 那一层。扩展要落到
# Pi 自己的 extensions 目录才会被自动发现，所以这一步是拷贝，不是登记路径。
# Codex 那一侧同一件事走 plugin.json 的 hooks 字段，跟着插件走，不用单独拷。
install_pi_toolchain_extension() {
  local source target dir
  source="$RUNTIME_ROOT/mmw/toolchain/extensions-pi/toolchain-diagnostics.ts"
  [ -f "$source" ] || { echo "Pi       : 缺 toolchain 扩展源，跳过"; return; }
  dir="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME/.pi}/agent}/extensions"
  mkdir -p "$dir"
  target="$dir/mmw-toolchain-diagnostics.ts"
  if cp "$source" "$target"; then
    echo "Pi       : 已装编辑后诊断扩展 $target"
  else
    echo "Pi       : 装编辑后诊断扩展失败 $target" >&2
  fi
}

install_pi() {
  command -v pi >/dev/null 2>&1 || { echo "Pi       : 未安装，跳过"; return; }
  local runtime_package
  runtime_package="$(cd "$RUNTIME_ROOT/mmw" && pwd -P)"
  remove_old_pi_mmw
  pi install "$runtime_package" >/dev/null
  echo "Pi       : 已安装 $runtime_package"
  install_pi_toolchain_extension
}

install_cursor_agents() {
  if [ -d "$HOME/.cursor" ]; then
    "$RUNTIME_ROOT/mmw/cli/mmw" agents materialize --host cursor
  else
    echo "Cursor   : 未安装，跳过原生 subagent"
  fi
}

install_mcp() {
  bash "$RUNTIME_ROOT/mmw/mcp/install-mcp.sh"
}

require_source_repo
verify_source
build_runtime
require_version_bump
install_forwarder
install_codex
install_claude_code
install_pi
install_cursor_agents
install_mcp

if [ -e "$RUNTIME_HOME/runtime.previous" ]; then
  find "$RUNTIME_HOME/runtime.previous" -depth -delete
fi

echo "完成     : 重新启动宿主，或开始一个新会话后使用 MMW。"
