#!/usr/bin/env bash
# 编辑后诊断的共用核心。四个宿主的 hook 都调它，各自只写自己的返回通道。
#
# 这一层不决定退出码，也不打印任何东西给宿主：返回通道是宿主合同，四家互不相同，
# 混在一起写会让某一家静默失效。核心只回答两件事——这次改了哪些文件，诊断说了什么。
#
# 用法（在 adapter 里）：
#   . "<本文件>"
#   payload="$(mmw_hook_payload)"
#   mmw_hook_collect_files "$payload"   # 结果在数组 MMW_HOOK_FILES
#   mmw_hook_diagnose                   # 输出在 MMW_HOOK_OUTPUT，返回 0 表示干净
#
# jq 或 mmw 不在时 mmw_hook_diagnose 返回 0：诊断跑不起来不该挡住干活。

mmw_hook_payload() {
  cat
}

# 路径的取法取各宿主写法的并集，不按宿主分支：
#   tool_input / toolInput      两种拼写
#   path / filePath / file_path 三种别名
#   apply_patch                 路径写在 command 的补丁正文里
# 某个宿主不用某种写法时那一支自然取不到东西，不会误伤。
mmw_hook_collect_files() {
  local payload="$1"
  MMW_HOOK_FILES=()
  command -v jq >/dev/null 2>&1 || return 0
  # 不用 mapfile：macOS 自带的是 bash 3.2，没有这个内建。
  local line
  while IFS= read -r line; do
    [ -n "$line" ] && MMW_HOOK_FILES+=("$line")
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

# 会话结束那一类事件的 payload 里没有 tool_input，改用工作树里动过的文件。
mmw_hook_collect_worktree_files() {
  command -v git >/dev/null 2>&1 || return 0
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0
  local line
  while IFS= read -r line; do
    [ -n "$line" ] && MMW_HOOK_FILES+=("$line")
  done < <(
    git diff --name-only HEAD 2>/dev/null
    git ls-files --others --exclude-standard 2>/dev/null
  )
}

# 返回 0 表示没有要报的：干净、没有文件、或者工具链跑不起来。
# 返回 1 表示 MMW_HOOK_OUTPUT 里有诊断。
mmw_hook_diagnose() {
  MMW_HOOK_OUTPUT=""
  export MMW_HOOK_OUTPUT
  [ "${#MMW_HOOK_FILES[@]}" -gt 0 ] || return 0
  command -v mmw >/dev/null 2>&1 || return 0
  if MMW_HOOK_OUTPUT="$(mmw toolchain check --changed-only "${MMW_HOOK_FILES[@]}" 2>&1)"; then
    MMW_HOOK_OUTPUT=""
    return 0
  fi
  return 1
}
