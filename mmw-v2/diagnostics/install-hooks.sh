#!/usr/bin/env bash
# 把编辑后诊断注册进五个宿主。
#
# 每家挂在哪、诊断怎么回到 agent，是 2026-08-19 在本机各自实测出来的：
#   Claude Code  ~/.claude/settings.json 的 .hooks.PostToolUse   退出码 2 加 stderr
#   Codex        ~/.codex/hooks.json 的 .hooks.PostToolUse       同上
#   Cursor       ~/.cursor/hooks.json 的 .hooks.postToolUse      stdout 的 additional_context
#   Grok         ~/.grok/hooks/ 下单独一份 json，Stop 与 SubagentStop
#   pi           ~/.pi/agent/extensions/ 下一个扩展
#
# Grok 为什么不挂 PostToolUse：实测它会触发，但写到 stdout 的 additionalContext 到
# 不了模型。同一个探针挂到 Stop 上，模型逐字读到了。
#
# pi 为什么是扩展不是 hook：0.84.2 的代码里没有 hookEventName 也没有 PostToolUse，
# 它至今没有 hook 这一层。
#
# 注册的是路径，不是副本。写进宿主配置的是指向这个 checkout 的绝对路径，技能软链和
# MCP 配置也是这么做的：改一个字，下次调用就是新的，不用重装。所以要从主检出装，
# 不要从任务 worktree 装——worktree 合并后会删掉，路径就断了。
#
# 只加不删：别人的 hook 原样保留，只换掉我们自己那一条。认自己那一条靠命令里出现
# mmw-v2/diagnostics/hooks，改安装位置也认得出来。
#
#   install-hooks.sh          装
#   install-hooks.sh --check  只看装没装，不动磁盘。齐了回 0，缺东西回 1

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS="$HERE/hooks"
MARKER="mmw-v2/diagnostics/hooks"

PI_AGENT_DIR="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME/.pi}/agent}"
CLAUDE_SETTINGS="${MMW_CLAUDE_SETTINGS_FILE:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json}"
CODEX_HOOKS="${MMW_CODEX_HOOKS_FILE:-${CODEX_HOME:-$HOME/.codex}/hooks.json}"
CURSOR_HOOKS="${MMW_CURSOR_HOOKS_FILE:-$HOME/.cursor/hooks.json}"
GROK_HOOK_DIR="${MMW_GROK_HOOK_DIR:-$HOME/.grok/hooks}"
PI_EXT_DIR="${MMW_PI_EXT_DIR:-$PI_AGENT_DIR/extensions}"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-hooks.sh [--check]" >&2; exit 2 ;;
esac

command -v jq >/dev/null 2>&1 || { echo "ERROR: 需要 jq" >&2; exit 2; }
[ -d "$HOOKS" ] || { echo "ERROR: 缺适配器目录 ${HOOKS}" >&2; exit 2; }

rc=0

# 这台机器有没有这个宿主。没有就跳过，那是正确结果，不是失败。
host_present() {
  local dir="$1"
  [ -d "$dir" ]
}

# Claude Code 与 Codex 的 hook 合同一样，注册位置不一样，所以是同一段代码两个宿主。
#
# 事件名与适配器都由调用方给：Codex 除了 PostToolUse 还要挂一个 SubagentStop，
# 因为它的子 agent 改文件时 PostToolUse 不触发（实测）。
#   merge_event <配置文件> <显示名> <事件名> <适配器文件名>
merge_event() {
  local file="$1" label="$2" event="$3" adapter="$4" cmd tmp dir
  dir="$(dirname "$file")"
  cmd="bash \"$HOOKS/$adapter\""

  if ! host_present "$dir"; then
    echo "跳过  这台机器没有 ${label}"
    return 0
  fi

  if [ "$mode" = check ]; then
    if [ -f "$file" ] && jq -e --arg m "$adapter" --arg e "$event" '
        [.hooks[$e] // [] | .[].hooks // [] | .[].command // ""]
        | any(contains($m))' "$file" >/dev/null 2>&1; then
      echo "已装  ${label} 的 ${event}"
      return 0
    fi
    echo "未装  ${label} 的 ${file} 里没有 ${event}" >&2
    return 1
  fi

  mkdir -p "$dir"
  [ -f "$file" ] || printf '{}\n' > "$file"
  jq -e . "$file" >/dev/null 2>&1 || { echo "ERROR: ${label} 的 ${file} 不是合法 JSON" >&2; return 2; }

  # 只认自己那一条：按适配器文件名匹配，不按目录名。同一个宿主的两个事件挂的是两个
  # 不同的适配器，用目录名做标记会让后装的那个把先装的删掉。
  tmp="$(mktemp "$dir/.mmw-hooks.XXXXXX")"
  jq --arg cmd "$cmd" --arg m "$adapter" --arg e "$event" '
    .hooks = (.hooks // {})
    | .hooks[$e] = (
        ((.hooks[$e] // [])
          | map(.hooks = ((.hooks // [])
              | map(select((.command // "") | tostring | contains($m) | not))))
          | map(select((.hooks | length) > 0)))
        + [{hooks: [{type: "command", command: $cmd, timeout: 120}]}]
      )
  ' "$file" > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    echo "ERROR: 合并 ${label} 的 hook 失败，${file} 保留原样" >&2
    return 1
  fi
  mv "$tmp" "$file"
  echo "装好  ${label} 的 ${event} → ${file}"
}

# Cursor 的形状不一样：hooks.postToolUse 是一个只有 command 的对象数组，而且它的
# 退出码 2 等同 permission deny，所以适配器一律退 0、走 additional_context。
install_cursor() {
  local file="$CURSOR_HOOKS" cmd tmp dir
  dir="$(dirname "$file")"
  cmd="bash \"$HOOKS/cursor.sh\""

  if ! host_present "$dir"; then
    echo "跳过  这台机器没有 Cursor"
    return 0
  fi

  if [ "$mode" = check ]; then
    if [ -f "$file" ] && jq -e --arg m "$MARKER" '
        [.hooks.postToolUse // [] | .[].command // ""] | any(contains($m))' \
        "$file" >/dev/null 2>&1; then
      echo "已装  Cursor 编辑后诊断"
      return 0
    fi
    echo "未装  Cursor 的 ${file} 里没有编辑后诊断" >&2
    return 1
  fi

  mkdir -p "$dir"
  [ -f "$file" ] || printf '{"version":1,"hooks":{}}\n' > "$file"
  jq -e . "$file" >/dev/null 2>&1 || { echo "ERROR: Cursor 的 ${file} 不是合法 JSON" >&2; return 2; }

  tmp="$(mktemp "$dir/.mmw-hooks.XXXXXX")"
  jq --arg cmd "$cmd" --arg m "$MARKER" '
    .version = (.version // 1)
    | .hooks = (.hooks // {})
    | .hooks.postToolUse = (
        ((.hooks.postToolUse // [])
          | map(select((.command // "") | tostring | contains($m) | not)))
        + [{command: $cmd}]
      )
  ' "$file" > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    echo "ERROR: 合并 Cursor 的 hook 失败，${file} 保留原样" >&2
    return 1
  fi
  mv "$tmp" "$file"
  echo "装好  Cursor 编辑后诊断 → ${file}"
}

# Grok 读 hooks 目录下的每一份 json，所以我们单独放一份，不去动别人那份。
#
# 命令写成 bash "绝对路径"，跟另外三家一模一样。原来写的是相对名 ./mmw-diagnostics.sh
# 加一条软链，路径确实解得开，但 Grok 是把命令当可执行文件直接 spawn 的，而适配器当时
# 没有执行位，于是每次都是 `failed to spawn command: Permission denied (os error 13)`。
# Grok 对 hook 失败 fail-open，只在 --debug-file 的日志里留一行 WARN——**从外面看跟
# 「代码干净」一模一样**，这个洞是 probe-subagent.sh 撞出来的。
#
# 走 bash 就跟执行位无关了。适配器的执行位也补上了，两道都不指望对方。
install_grok() {
  local spec="$GROK_HOOK_DIR/mmw-diagnostics.json"
  local stale="$GROK_HOOK_DIR/mmw-diagnostics.sh"
  local cmd="bash \"$HOOKS/grok.sh\""

  if ! host_present "$(dirname "$GROK_HOOK_DIR")"; then
    echo "跳过  这台机器没有 Grok"
    return 0
  fi

  if [ "$mode" = check ]; then
    if [ -f "$spec" ] && jq -e --arg m "$MARKER" '
        [.hooks | to_entries[] | .value[] | .hooks[] | .command // ""] | any(contains($m))' \
        "$spec" >/dev/null 2>&1; then
      echo "已装  Grok 编辑后诊断"
      return 0
    fi
    echo "未装  Grok 的 ${GROK_HOOK_DIR} 里没有编辑后诊断" >&2
    return 1
  fi

  mkdir -p "$GROK_HOOK_DIR"
  # 上一版留下的软链。命令不再走它，留着只会让人以为它还有用。
  [ -L "$stale" ] && rm -f "$stale"
  jq -n --arg cmd "$cmd" '{hooks: {
    Stop: [{hooks: [{type: "command", command: $cmd, timeout: 120}]}],
    SubagentStop: [{hooks: [{type: "command", command: $cmd, timeout: 120}]}]
  }}' > "$spec"
  echo "装好  Grok 编辑后诊断 → ${spec}"
}

# pi 是扩展。软链而不是拷贝：扩展要靠自己的位置算出 check.py 在哪，拷到别处就算不
# 出来了。
#
# 扩展那一侧要自己解软链。这里原来写着「Node 解析模块默认走 realpath，所以
# import.meta.url 拿到的是仓库里的真实路径」——那句话对 Pi 的加载器不成立，实测它
# 拿到的是软链自己的路径。diagnostics.ts 现在显式 realpathSync 一次。
install_pi() {
  local link="$PI_EXT_DIR/mmw-diagnostics.ts"
  local source="$HERE/extension-pi/diagnostics.ts"

  if ! host_present "$(dirname "$PI_EXT_DIR")"; then
    echo "跳过  这台机器没有 pi"
    return 0
  fi
  [ -f "$source" ] || { echo "ERROR: 缺 pi 扩展源 ${source}" >&2; return 2; }

  if [ "$mode" = check ]; then
    if [ -L "$link" ] && [ "$(readlink "$link")" = "$source" ]; then
      echo "已装  pi 编辑后诊断"
      return 0
    fi
    echo "未装  ${link} 不在或不指向本仓库" >&2
    return 1
  fi

  mkdir -p "$PI_EXT_DIR"
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    echo "冲突  ${link} 已存在且不是软链，跳过" >&2
    return 1
  fi
  ln -sfn "$source" "$link"
  echo "装好  pi 编辑后诊断 → ${link}"
}

# Claude Code 官方的两个 LSP 插件。关掉它们，让五家走同一条路。
#
# 那两个插件的全部内容是一句声明：命令 pyright-langserver --stdio，加一个扩展名映射。
# 它写死走 PATH，所以永远拿全局版本；而 check.py 是仓库自带的优先。同一台机器上
# 全局 pyright 与仓库 .venv 里的版本不同时，编辑时看到的类型错误和门禁判定的不是
# 同一套——2026-08-10 实测过一次（全局 1.1.411、仓库 1.1.409）。
#
# 关掉丢的是 Claude Code 那个 LSP 工具的服务器。逐条对过：跳转定义、找引用、找实现、
# 列文件符号、看类型签名，serena 全有而且五家都有；只有调用层级 serena 没有，那类
# 问题归 graphify，同样五家都有。丢掉的东西没有一样是别的宿主本来有的。
#
# 设成 false 而不是删掉这两个键：留着才看得见它被关了，也才好改回去。
disable_claude_lsp_plugins() {
  local file="$CLAUDE_SETTINGS" tmp dir
  dir="$(dirname "$file")"
  local names='["pyright-lsp@claude-plugins-official","typescript-lsp@claude-plugins-official"]'

  host_present "$dir" || return 0
  [ -f "$file" ] || return 0
  jq -e . "$file" >/dev/null 2>&1 || return 0

  local on
  on="$(jq -r --argjson n "$names" \
    '[(.enabledPlugins // {}) | to_entries[] | select((.key as $k | $n | index($k)) and .value == true) | .key] | length' \
    "$file")"

  if [ "$mode" = check ]; then
    [ "$on" -eq 0 ] && { echo "已关  Claude Code 的两个 LSP 插件"; return 0; }
    echo "未关  Claude Code 还开着 ${on} 个 LSP 插件，诊断会来自两条不同的路" >&2
    return 1
  fi

  [ "$on" -gt 0 ] || return 0
  tmp="$(mktemp "$dir/.mmw-plugins.XXXXXX")"
  jq --argjson n "$names" '
    .enabledPlugins = ((.enabledPlugins // {})
      | with_entries(if (.key as $k | $n | index($k)) then .value = false else . end))
  ' "$file" > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    echo "ERROR: 关 Claude Code 的 LSP 插件失败，${file} 保留原样" >&2
    return 1
  fi
  mv "$tmp" "$file"
  echo "关掉  Claude Code 的 ${on} 个 LSP 插件，诊断统一由编辑后诊断供给"
}

# 提交前门禁。装法是全局 core.hooksPath，一处设置覆盖这台机器上所有仓库。
#
# 这一条跟上面五个宿主不是一回事：它们补的是「agent 用编辑工具改了文件」，这一条
# 补的是那一层够不到的所有改法——shell 命令改的、你自己在编辑器里改的、别的电脑
# 改的。旧 mmw 靠 CI 挡这一块，CI 已经砍了。
#
# 别人已经设过 core.hooksPath 就不覆盖：那是一个全局开关，覆盖掉等于悄悄卸了对方
# 整套 hook。报出来让人自己定。
install_git_hooks() {
  local dir="$HERE/git-hooks" current
  command -v git >/dev/null 2>&1 || { echo "跳过  这台机器没有 git"; return 0; }
  current="$(git config --global --get core.hooksPath 2>/dev/null || true)"

  if [ "$mode" = check ]; then
    if [ "$current" = "$dir" ] && [ -x "$dir/pre-commit" ]; then
      echo "已装  提交前门禁"
      return 0
    fi
    echo "未装  git 的 core.hooksPath 是「${current:-空}」，不是 ${dir}" >&2
    return 1
  fi

  [ -x "$dir/pre-commit" ] || { echo "ERROR: 缺 ${dir}/pre-commit 或它没有执行权限" >&2; return 2; }
  if [ -n "$current" ] && [ "$current" != "$dir" ]; then
    echo "冲突  git 的 core.hooksPath 已经指向 ${current}，没有覆盖它" >&2
    return 1
  fi
  git config --global core.hooksPath "$dir"
  echo "装好  提交前门禁 → git config --global core.hooksPath ${dir}"
}

merge_event "$CLAUDE_SETTINGS" "Claude Code" PostToolUse claude-codex.sh || rc=$?
merge_event "$CODEX_HOOKS" "Codex" PostToolUse claude-codex.sh || rc=$?
merge_event "$CODEX_HOOKS" "Codex" SubagentStop codex-subagent.sh || rc=$?
install_cursor || rc=$?
install_grok || rc=$?
install_pi || rc=$?
disable_claude_lsp_plugins || rc=$?
install_git_hooks || rc=$?

exit "$rc"
