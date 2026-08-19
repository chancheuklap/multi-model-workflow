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
merge_post_tool_use() {
  local file="$1" label="$2" cmd tmp dir
  dir="$(dirname "$file")"
  cmd="bash \"$HOOKS/claude-codex.sh\""

  if ! host_present "$dir"; then
    echo "跳过  这台机器没有 ${label}"
    return 0
  fi

  if [ "$mode" = check ]; then
    if [ -f "$file" ] && jq -e --arg m "$MARKER" '
        [.hooks.PostToolUse // [] | .[].hooks // [] | .[].command // ""]
        | any(contains($m))' "$file" >/dev/null 2>&1; then
      echo "已装  ${label} 编辑后诊断"
      return 0
    fi
    echo "未装  ${label} 的 ${file} 里没有编辑后诊断" >&2
    return 1
  fi

  mkdir -p "$dir"
  [ -f "$file" ] || printf '{}\n' > "$file"
  jq -e . "$file" >/dev/null 2>&1 || { echo "ERROR: ${label} 的 ${file} 不是合法 JSON" >&2; return 2; }

  tmp="$(mktemp "$dir/.mmw-hooks.XXXXXX")"
  jq --arg cmd "$cmd" --arg m "$MARKER" '
    .hooks = (.hooks // {})
    | .hooks.PostToolUse = (
        ((.hooks.PostToolUse // [])
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
  echo "装好  ${label} 编辑后诊断 → ${file}"
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
# 命令写相对名，跟 Grok 自己的目录约定一致（实测 ./name.sh 能跑起来）。
install_grok() {
  local link="$GROK_HOOK_DIR/mmw-diagnostics.sh"
  local spec="$GROK_HOOK_DIR/mmw-diagnostics.json"

  if ! host_present "$(dirname "$GROK_HOOK_DIR")"; then
    echo "跳过  这台机器没有 Grok"
    return 0
  fi

  if [ "$mode" = check ]; then
    if [ -L "$link" ] && [ "$(readlink "$link")" = "$HOOKS/grok.sh" ] && [ -f "$spec" ]; then
      echo "已装  Grok 编辑后诊断"
      return 0
    fi
    echo "未装  Grok 的 ${GROK_HOOK_DIR} 里没有编辑后诊断" >&2
    return 1
  fi

  mkdir -p "$GROK_HOOK_DIR"
  ln -sfn "$HOOKS/grok.sh" "$link"
  jq -n '{hooks: {
    Stop: [{hooks: [{type: "command", command: "./mmw-diagnostics.sh", timeout: 120}]}],
    SubagentStop: [{hooks: [{type: "command", command: "./mmw-diagnostics.sh", timeout: 120}]}]
  }}' > "$spec"
  echo "装好  Grok 编辑后诊断 → ${spec}"
}

# pi 是扩展。软链而不是拷贝：扩展要靠自己的位置算出 check.py 在哪，拷到别处就算不
# 出来了。Node 解析模块时默认走 realpath，所以软链过去 import.meta.url 拿到的是这个
# 仓库里的真实路径。
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

merge_post_tool_use "$CLAUDE_SETTINGS" "Claude Code" || rc=$?
merge_post_tool_use "$CODEX_HOOKS" "Codex" || rc=$?
install_cursor || rc=$?
install_grok || rc=$?
install_pi || rc=$?

exit "$rc"
