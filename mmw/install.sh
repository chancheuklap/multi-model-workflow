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
  [ -f "$SOURCE_MMW/cli/mmw" ] && [ -d "$SOURCE_MMW/skills-src" ] \
    && [ -f "$SOURCE_MMW/codex/runtime.py" ] \
    || die "当前目录不是完整的 MMW 源码仓库：$SOURCE_MMW"
}

verify_source() {
  "$SOURCE_MMW/cli/mmw" agents materialize --host pi --check
  python3 "$SOURCE_MMW/codex/runtime.py" materialize --check
}

build_runtime() {
  local stage previous
  mkdir -p "$RUNTIME_HOME"
  stage="$(mktemp -d "$RUNTIME_HOME/.runtime.XXXXXX")"
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

# 五个宿主的技能都从同一份 skills-src 软链过去：目标目录不同，动作相同。技能正文
# 对所有宿主是同一句，宿主差异由 cli/host-actions.json 在运行期回答。
install_skills_into() {
  bash "$RUNTIME_ROOT/mmw/cli/lib/install-skills.sh" --dest "$1" \
    || die "技能装不进 $1，按上面的冲突行处理后重跑"
}

# 上一版把 MMW 装成插件。装过的机器上那份插件还在，技能会出现两遍：一遍来自插件，
# 一遍来自用户级目录。这一步把它摘掉。摘的是 MMW 自己那两个 id
# （mmw@multi-model-workflow 与 mmw@mmw-codex），别人的插件一个都不碰。
remove_legacy_plugin() {
  # 摘 marketplace 与摘插件都直接执行，不拿 `plugin list` 当闸门。
  #
  # 上一版这里用 `plugin list` 当闸门，两个宿主上都没生效，各错各的：
  #
  #   Claude Code 的 JSON 里插件字段叫 id（"mmw@multi-model-workflow"），没有 name，
  #   select(.name == "mmw") 永远不匹配。
  #
  #   Codex 更糟：marketplace 的 source 指着 runtime 根，而那底下的清单已经随打包
  #   一起删了。清单读不到时 `codex plugin list` 整个非零退出——不只是查不到 mmw，
  #   是它的插件子系统全废。闸门自己先倒了，摘除永远轮不到。
  #
  # 摘之前先从磁盘上读一次「装没装过」。退出码当不了证据：两个宿主的
  # `marketplace remove` 对根本不存在的 marketplace 也返回 0，拿它判断的话
  # 每台机器每次安装都会报一遍「已摘掉上一版插件」，那句话就成了噪音。
  local claude_dir codex_dir had
  claude_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  codex_dir="${CODEX_HOME:-$HOME/.codex}"

  if command -v claude >/dev/null 2>&1; then
    had=""
    [ -d "$claude_dir/plugins/cache/multi-model-workflow" ] && had=yes
    jq -e '.plugins | has("mmw@multi-model-workflow")' \
      "$claude_dir/plugins/installed_plugins.json" >/dev/null 2>&1 && had=yes
    jq -e 'has("multi-model-workflow")' \
      "$claude_dir/plugins/known_marketplaces.json" >/dev/null 2>&1 && had=yes

    claude plugin uninstall "mmw@multi-model-workflow" >/dev/null 2>&1 || true
    claude plugin marketplace remove multi-model-workflow >/dev/null 2>&1 || true
    rm -rf "$claude_dir/plugins/cache/multi-model-workflow"
    [ -z "$had" ] || echo "Claude   : 已摘掉上一版的 mmw 插件"
  fi

  if command -v codex >/dev/null 2>&1; then
    had=""
    [ -d "$codex_dir/plugins/cache/mmw-codex" ] && had=yes
    grep -q 'mmw-codex' "$codex_dir/config.toml" 2>/dev/null && had=yes

    # marketplace 先摘：它的 source 指着 runtime 根，清单已随打包删掉，
    # 留着它 `codex plugin list` 会整个非零退出，插件也就摘不掉。
    codex plugin marketplace remove mmw-codex --json >/dev/null 2>&1 || true
    codex plugin remove "mmw@mmw-codex" --json >/dev/null 2>&1 || true
    rm -rf "$codex_dir/plugins/cache/mmw-codex"
    remove_legacy_codex_hook_state
    [ -z "$had" ] || echo "Codex    : 已摘掉上一版的 mmw 插件"
  fi
}

# `codex plugin remove` 不清 hooks.state 里那条信任记录。它指的 hooks.json 已经
# 随打包删掉，留着是个指向空处的哈希。整段删掉，其余内容一个字节不动。
remove_legacy_codex_hook_state() {
  local config
  config="${CODEX_HOME:-$HOME/.codex}/config.toml"
  [ -f "$config" ] || return 0
  grep -q 'hooks\.state\."mmw@mmw-codex' "$config" || return 0
  python3 - "$config" <<'CLEAN'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
block = re.compile(r'\n\[hooks\.state\."mmw@mmw-codex[^"]*"\]\n(?:(?!\[)[^\n]*\n)*', re.M)
cleaned, count = block.subn("\n", text)
if not count:
    sys.exit(0)
tmp = path.with_name(path.name + ".mmw-tmp")
tmp.write_text(cleaned, encoding="utf-8")
tmp.replace(path)
print(f"Codex    : 清掉 {count} 条指向已删 hooks.json 的信任记录")
CLEAN
}

install_codex() {
  command -v codex >/dev/null 2>&1 || { echo "Codex    : 未安装，跳过"; return; }
  python3 "$RUNTIME_ROOT/mmw/codex/runtime.py" install
  install_skills_into "${CODEX_HOME:-$HOME/.codex}/skills"
  merge_post_tool_use_hook "${CODEX_HOME:-$HOME/.codex}/hooks.json" "Codex   "
  echo "Codex    : 已装技能、原生 subagent、编辑后诊断 hook"
}

# Claude Code 的会话内 subagent。这个宿主只有一个：审查者。别的角色都是 GPT 族，
# 由 adapter 走 codex exec，不需要 agent 文件。
#
# 软链不拷贝，理由同技能。目标目录里同名的文件不是本脚本装的软链就不动它。
install_claude_code_agents() {
  local src dest manifest tmp name
  src="$RUNTIME_ROOT/mmw/agents"
  dest="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/agents"
  manifest="$dest/.mmw-agents"
  mkdir -p "$dest"
  if [ -f "$manifest" ]; then
    while IFS= read -r name; do
      [ -n "$name" ] || continue
      [ -f "$src/$name" ] && continue
      [ -L "$dest/$name" ] && rm -f "$dest/$name"
    done < "$manifest"
  fi
  tmp="$(mktemp "$dest/.mmw-agents.XXXXXX")"
  for name in "$src"/*.md; do
    [ -f "$name" ] || continue
    name="$(basename "$name")"
    if [ -e "$dest/$name" ] && [ ! -L "$dest/$name" ]; then
      die "Claude   : $dest/$name 已被非 MMW 内容占用，先处理它再装"
    fi
    ln -sfn "$src/$name" "$dest/$name"
    printf '%s\n' "$name" >> "$tmp"
  done
  mv "$tmp" "$manifest"
  echo "Claude   : 已装 agent 到 $dest"
}

install_claude_code() {
  command -v claude >/dev/null 2>&1 || { echo "Claude   : 未安装，跳过"; return; }
  local settings temp
  install_skills_into "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
  install_claude_code_agents
  merge_post_tool_use_hook "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" "Claude  "
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
  echo "Claude   : 已装技能、agent、权限与编辑后诊断 hook"
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
  local plugin id at_user
  for plugin in pyright-lsp typescript-lsp; do
    id="$plugin@claude-plugins-official"
    # 认 scope 不只认名字：同一个插件可能已经装成 project scope 绑在某个仓库上，
    # 那种装法换个仓库就没有，不算数。
    at_user="$(claude plugin list --json 2>/dev/null \
      | jq -r --arg i "$id" '[.[] | select((.id // "") == $i and .scope == "user")] | length')"
    if [ "${at_user:-0}" != "0" ]; then
      echo "Claude   : $plugin 已在（用户级）"
      continue
    fi
    if claude plugin install "$id" --scope user >/dev/null 2>&1; then
      echo "Claude   : 已装 ${plugin}（用户级）"
    else
      # 变量名必须用花括号界定：全角标点是多字节的，bash 会把 `$plugin，` 整个
      # 当成变量名，于是 set -u 直接崩，报的错跟真实原因（插件装不上）毫无关系。
      echo "Claude   : 装不上 ${plugin}，自己跑 claude plugin install ${id} --scope user 看报什么"
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
  install_skills_into "${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME/.pi}/agent}/skills"
  echo "Pi       : 已安装 $runtime_package"
  install_pi_toolchain_extension
}

# Cursor 的任务树与结果树都在 ~/.cursor/worktrees/。用户开任务树，agent 只在树上建分支。
# worker 结果树由 mmw-cursor-agent --worktree 创建，回收交给 Cursor 自己的 GC。
install_cursor_skills() {
  install_skills_into "$HOME/.cursor/skills"
  echo "Cursor   : 已装技能到 $HOME/.cursor/skills"
}

install_cursor_hooks() {
  local hooks_json="$HOME/.cursor/hooks.json"
  local hook_dir="$HOME/.cursor/hooks"
  local hook_script="$hook_dir/mmw-toolchain-check.sh"
  local source="$RUNTIME_ROOT/mmw/toolchain/hooks/cursor.sh"
  local tmp
  [ -f "$source" ] || die "缺 Cursor 诊断 hook 源：$source"
  mkdir -p "$hook_dir"
  ln -sfn "$source" "$hook_script"
  if [ ! -f "$hooks_json" ]; then
    printf '{"version":1,"hooks":{}}\n' > "$hooks_json"
  fi
  jq -e . "$hooks_json" >/dev/null 2>&1 \
    || die "Cursor hooks.json 不是合法 JSON：$hooks_json"
  tmp="$(mktemp "$HOME/.cursor/.hooks.XXXXXX")"
  jq --arg cmd "$hook_script" '
    .version = (.version // 1)
    | .hooks = (.hooks // {})
    | .hooks.postToolUse = (
        ((.hooks.postToolUse // [])
          | map(select((.command // "") | tostring | contains("mmw-toolchain-check") | not)))
        + [{command: $cmd, matcher: "Write|StrReplace|Delete"}]
      )
  ' "$hooks_json" > "$tmp"
  jq -e . "$tmp" >/dev/null 2>&1 || die "合并 Cursor hooks.json 失败"
  mv "$tmp" "$hooks_json"
  echo "Cursor   : 已合并 postToolUse 诊断 hook（保留已有 sessionStart）"
}

install_cursor_permissions() {
  local file="$HOME/.cursor/permissions.json"
  local tmp
  mkdir -p "$(dirname "$file")"
  if [ ! -f "$file" ]; then
    printf '{}\n' > "$file"
  fi
  jq -e . "$file" >/dev/null 2>&1 \
    || die "Cursor permissions.json 不是合法 JSON：$file"
  tmp="$(mktemp "$HOME/.cursor/.permissions.XXXXXX")"
  # File-based terminalAllowlist / mcpAllowlist lock Auto-review on current
  # Cursor desktop (forum 165722). Keep autoRun in this file; do not write
  # those two keys back.
  jq 'del(.terminalAllowlist, .mcpAllowlist)' "$file" > "$tmp"
  jq -e . "$tmp" >/dev/null 2>&1 || die "更新 Cursor permissions.json 失败"
  mv "$tmp" "$file"
  echo "Cursor   : 已去掉会锁死 Auto-review 的文件 allowlist；规则只放 autoRun"
}

install_cursor_wrapper() {
  local target current temp
  target="$BIN_DIR/mmw-cursor-agent"
  mkdir -p "$BIN_DIR"
  if [ -e "$target" ]; then
    current="$(sed -n '2p' "$target" 2>/dev/null || true)"
    case "$current" in
      "# Managed by MMW cursor isolate") ;;
      *)
        grep -q 'Managed by MMW cursor isolate' "$target" 2>/dev/null \
          || die "拒绝覆盖非 MMW 管理的命令：$target"
        ;;
    esac
  fi
  temp="$(mktemp "$BIN_DIR/.mmw-cursor-agent.XXXXXX")"
  cat > "$temp" <<EOF
#!/usr/bin/env bash
# Managed by MMW cursor isolate
set -euo pipefail
export MMW_HOST="\${MMW_HOST:-cursor}"
exec "$RUNTIME_ROOT/mmw/cli/bin/mmw-cursor-agent" "\$@"
EOF
  chmod 0755 "$temp"
  mv "$temp" "$target"
  echo "Cursor   : 已装隔离包装 $target"
}

install_cursor() {
  if [ ! -d "$HOME/.cursor" ]; then
    echo "Cursor   : 未安装，跳过"
    return
  fi
  "$RUNTIME_ROOT/mmw/cli/mmw" agents materialize --host cursor
  install_cursor_skills
  install_cursor_hooks
  install_cursor_permissions
  install_cursor_wrapper
}

install_grok() {
  command -v grok >/dev/null 2>&1 || [ -d "$HOME/.grok" ] || {
    echo "Grok     : 未安装，跳过"
    return
  }
  install_skills_into "$HOME/.grok/skills"
  "$RUNTIME_ROOT/mmw/cli/mmw" agents materialize --host grok
  install_grok_hooks
  echo "Grok     : 已装技能、角色、Stop hook"
}

# Grok 的诊断挂在 Stop 与 SubagentStop：它的 PostToolUse 忽略 stdout，诊断在那里
# 交不回模型。命令写相对名，与 Grok 自己的 hooks 目录约定一致。
install_grok_hooks() {
  local hook_dir="$HOME/.grok/hooks"
  mkdir -p "$hook_dir"
  ln -sfn "$RUNTIME_ROOT/mmw/toolchain/hooks/grok.sh" "$hook_dir/mmw-toolchain-check.sh"
  jq -n '
    {hooks: {
      Stop: [{hooks: [{type: "command", command: "./mmw-toolchain-check.sh", timeout: 60}]}],
      SubagentStop: [{hooks: [{type: "command", command: "./mmw-toolchain-check.sh", timeout: 60}]}]
    }}
  ' > "$hook_dir/mmw-toolchain.json"
}

# Claude Code 与 Codex 的 hook 合同一样，注册位置不一样：
#   Claude Code  ~/.claude/settings.json 的 .hooks
#   Codex        ~/.codex/hooks.json 的 .hooks
# 两边都是合并，不是覆盖：别人的 hook 留着，只换掉我们自己那一条。认自己那一条靠
# 命令里出现 mmw/toolchain/hooks，改安装位置也认得出来。
merge_post_tool_use_hook() {
  local file="$1" label="$2" cmd tmp
  cmd="bash \"$RUNTIME_ROOT/mmw/toolchain/hooks/claude-codex.sh\""
  mkdir -p "$(dirname "$file")"
  [ -f "$file" ] || printf '{}\n' > "$file"
  jq -e . "$file" >/dev/null 2>&1 || die "$label 的 $file 不是合法 JSON"
  tmp="$(mktemp "$(dirname "$file")/.mmw-hooks.XXXXXX")"
  jq --arg cmd "$cmd" '
    .hooks = (.hooks // {})
    | .hooks.PostToolUse = (
        ((.hooks.PostToolUse // [])
          | map(.hooks = ((.hooks // [])
              | map(select((.command // "") | tostring | contains("mmw/toolchain/hooks") | not))))
          | map(select((.hooks | length) > 0)))
        + [{hooks: [{type: "command", command: $cmd, timeout: 120}]}]
      )
  ' "$file" > "$tmp"
  jq -e . "$tmp" >/dev/null 2>&1 || die "合并 $label 的 hook 失败"
  mv "$tmp" "$file"
  echo "$label: 已合并编辑后诊断 hook 到 $file"
}

install_mcp() {
  bash "$RUNTIME_ROOT/mmw/mcp/install-mcp.sh"
}

# 界面 QA 的四个运行时依赖，以及技能定位它们用的那个转发器。
#
# 依赖本身装在 runtime 外面（理由见 install-ui-qa-deps.sh 开头）。转发器跟 mmw 一样
# 装进 BIN_DIR：技能正文只写命令名，路径由转发器当场算，因此 MMW_RUNTIME_HOME
# 换位置时技能不用改。
install_ui_qa() {
  local target current temp
  bash "$RUNTIME_ROOT/mmw/ui-qa/install-ui-qa-deps.sh"
  target="$BIN_DIR/mmw-ui-qa"
  mkdir -p "$BIN_DIR"
  if [ -e "$target" ]; then
    current="$(sed -n '2p' "$target" 2>/dev/null || true)"
    [ "$current" = "$FORWARD_HEADER" ] \
      || die "拒绝覆盖非 MMW 管理的命令：$target"
  fi
  temp="$(mktemp "$BIN_DIR/.mmw-ui-qa.XXXXXX")"
  cat > "$temp" <<EOF
#!/usr/bin/env bash
$FORWARD_HEADER
set -euo pipefail
exec "$RUNTIME_ROOT/mmw/ui-qa/mmw-ui-qa" "\$@"
EOF
  chmod 0755 "$temp"
  mv "$temp" "$target"
  echo "界面 QA  : $target"
}

require_source_repo
verify_source
build_runtime
install_forwarder
remove_legacy_plugin
install_codex
install_claude_code
install_pi
install_cursor
install_grok
install_mcp
install_ui_qa

if [ -e "$RUNTIME_HOME/runtime.previous" ]; then
  find "$RUNTIME_HOME/runtime.previous" -depth -delete
fi

echo "完成     : 重新启动宿主，或开始一个新会话后使用 MMW。"
