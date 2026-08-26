#!/usr/bin/env bash
# 从 MMW 源码仓库构建一次 runtime，并安装到本机已有的各个宿主。

set -euo pipefail

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

install_pi() {
  command -v pi >/dev/null 2>&1 || { echo "Pi       : 未安装，跳过"; return; }
  local runtime_package
  runtime_package="$(cd "$RUNTIME_ROOT/mmw" && pwd -P)"
  remove_old_pi_mmw
  pi install "$runtime_package" >/dev/null
  echo "Pi       : 已安装 $runtime_package"
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
