#!/usr/bin/env bash
# 编辑后诊断的共用核心。各宿主的适配器都调它，各自只写自己的返回通道。
#
# 这一层不决定退出码，也不打印任何东西给宿主：返回通道是宿主合同，五家互不相同，
# 混在一起写会让某一家静默失效。核心只回答两件事——这次改了哪些文件，检查器说了什么。
#
# 用法（在适配器里）：
#   . "<本文件>"
#   payload="$(cat)"
#   mmw_collect_files "$payload"    # 结果在数组 MMW_FILES
#   mmw_diagnose                    # 输出在 MMW_OUTPUT，返回 0 表示没有要报的
#
# jq 不在时 mmw_diagnose 返回 0：诊断跑不起来不该挡住干活。

MMW_CORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
MMW_CHECK="$MMW_CORE_DIR/../check.py"

# 路径的取法取各宿主写法的并集，不按宿主分支：
#   tool_input / toolInput      两种拼写
#   path / filePath / file_path 三种别名
#   apply_patch                 路径写在 command 的补丁正文里
# 某个宿主不用某种写法时那一支自然取不到东西，不会误伤。
mmw_collect_files() {
  local payload="$1"
  MMW_FILES=()
  command -v jq >/dev/null 2>&1 || return 0
  local base
  base="$(mmw_payload_cwd "$payload")"
  # 不用 mapfile：macOS 自带的是 bash 3.2，没有这个内建。
  local line
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    # 相对路径按载荷里的 cwd 补全，不按进程的工作目录——见 mmw_payload_cwd。
    case "$line" in
      /*) MMW_FILES+=("$line") ;;
      *) MMW_FILES+=("$base/$line") ;;
    esac
  done < <(
    printf '%s' "$payload" | jq -r '
      ((.tool_input // .toolInput // {}) as $i
      | [
          ($i.path // empty),
          ($i.filePath // empty),
          ($i.file_path // empty)
        ]
        + (
          ($i.command // "")
          | if type == "string" then
              [scan("\\*\\*\\* (?:Add|Update|Move) File: (.+)")[]?[0]]
            else [] end
        )
      | map(select(. != null and . != ""))
      | unique
      | .[])
    ' 2>/dev/null
  )
}

# agent 在哪个目录干活。取载荷里的字段，不取进程的工作目录。
#
# 进程的工作目录由宿主决定，五家没有一家承诺过它是什么。实测 Grok 用的是工作区，
# 但它的 hook 命令按目录约定写成相对名 ./mmw-diagnostics.sh，那个写法本身就允许它
# 从别处启动。真在别处启动时，git diff 什么都看不到，诊断一条不报——而 hook 明明
# 触发了，看起来跟「代码干净」一模一样。载荷里的 cwd 是宿主明说的，用它。
mmw_payload_cwd() {
  local payload="$1" dir=""
  if command -v jq >/dev/null 2>&1; then
    dir="$(printf '%s' "$payload" | jq -r '.cwd // .workspaceRoot // .workspace_root // empty' 2>/dev/null || true)"
  fi
  [ -n "$dir" ] && [ -d "$dir" ] || dir="$PWD"
  printf '%s' "$dir"
}

# 会话结束那一类事件的载荷里没有工具输入，改用工作树里动过的文件。
# 输出绝对路径：调用方拿到的路径要能脱离任何工作目录使用。
mmw_collect_worktree_files() {
  local dir="${1:-$PWD}" root line
  command -v git >/dev/null 2>&1 || return 0
  root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || return 0
  [ -n "$root" ] || return 0
  while IFS= read -r line; do
    [ -n "$line" ] && MMW_FILES+=("$root/$line")
  done < <(
    git -C "$root" diff --name-only HEAD 2>/dev/null
    git -C "$root" ls-files --others --exclude-standard 2>/dev/null
  )
}

# 探针：这次触发到底发生了没有，收到了哪些文件。
#
# 只在 MMW_DIAG_TRACE 指着一个文件时写，平时一行都不产生。留着是因为「subagent
# 改文件时这个 hook 会不会触发」这类问题没有一家宿主在文档里说过，只能实测，而且
# 宿主升级之后要能重测。诊断本身到没到模型是另一个问题，那个要看会话记录；这里
# 回答的是更前面那一问：hook 触发了吗，它看见了哪个文件。
#
# 写失败不影响主流程：探针坏掉不该挡住干活。
# 用法：mmw_trace <适配器名> <载荷>
mmw_trace() {
  [ -n "${MMW_DIAG_TRACE:-}" ] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  local event=""
  if [ -n "${2:-}" ]; then
    event="$(printf '%s' "$2" | jq -r '.hookEventName // .hook_event_name // empty' 2>/dev/null || true)"
  fi
  jq -nc \
    --arg adapter "${1:-未知}" \
    --arg event "$event" \
    --argjson files "$(printf '%s\n' ${MMW_FILES[@]+"${MMW_FILES[@]}"} | jq -R . | jq -sc 'map(select(. != ""))')" \
    '{adapter: $adapter, event: $event, files: $files}' \
    >> "$MMW_DIAG_TRACE" 2>/dev/null || true
}

# 返回 0 表示没有要报的：干净、没有文件、或者检查器跑不起来。
# 返回 1 表示 MMW_OUTPUT 里有诊断。
mmw_diagnose() {
  # 导出不是为了子进程，是为了让「这个变量给别的文件读」这件事在本文件里就成立。
  MMW_OUTPUT=""
  export MMW_OUTPUT
  [ "${#MMW_FILES[@]}" -gt 0 ] || return 0
  [ -f "$MMW_CHECK" ] || return 0

  # 仓库根按第一个文件所在位置算。宿主给的 cwd 不一定是仓库根，而 check.py 要用
  # 仓库根来算相对路径和改动行。
  local first="${MMW_FILES[0]}" dir root changed=(--changed-only)
  dir="$(dirname "$first")"
  [ -d "$dir" ] || dir="$PWD"
  root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null || true)"

  # 不是 git 仓库也要检查，只是没有「改动行」这个概念，所以整份文件都报。
  # 早先这里直接 return 0，于是在一个还没 git init 的目录里改文件，一条诊断都不报，
  # 而那跟「代码干净」长得一模一样。
  if [ -z "$root" ]; then
    root="$dir"
    changed=()
  fi

  if MMW_OUTPUT="$(python3 "$MMW_CHECK" --repo "$root" "${changed[@]+"${changed[@]}"}" "${MMW_FILES[@]}" 2>&1)"; then
    MMW_OUTPUT=""
    return 0
  fi
  return 1
}
