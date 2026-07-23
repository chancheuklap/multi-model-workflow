#!/usr/bin/env bash
# prototype design 内层循环的共用状态/路径合同。调用者先 source lib/runtime.sh。

mmw_prototype_state_subdir() {
  if declare -F mmw_resolve_state_subdir >/dev/null 2>&1; then
    mmw_resolve_state_subdir "$1"
  elif [ -n "${MMW_STATE_SUBDIR:-}" ]; then
    printf '%s' "$MMW_STATE_SUBDIR"
  else
    return 1
  fi
}

mmw_prototype_manifest_from_top() {
  local top="$1" sd
  sd="$(mmw_prototype_state_subdir "$top")" || return 1
  printf '%s/%s/task.json' "$top" "$sd"
}

mmw_prototype_design_rel() {
  jq -r '.docs.design // empty' "$1"
}

mmw_prototype_log_rel() {
  local design
  design="$(mmw_prototype_design_rel "$1")" || return 1
  [ -n "$design" ] || return 1
  printf '%s/prototype/README.md' "$design"
}

mmw_prototype_has_newline() {
  case "$1" in *$'\n'*|*$'\r'*) return 0 ;; *) return 1 ;; esac
}

mmw_prototype_relpath_syntax_ok() {
  local rel="$1"
  [ -n "$rel" ] || return 1
  case "$rel" in /*) return 1 ;; esac
  mmw_prototype_has_newline "$rel" && return 1
  case "/$rel/" in */../*) return 1 ;; esac
  return 0
}

mmw_prototype_allowed_artifact_rel() {
  local man="$1" rel="$2" design
  mmw_prototype_relpath_syntax_ok "$rel" || return 1
  design="$(mmw_prototype_design_rel "$man")" || return 1
  case "$rel" in
    "$design/prototype/"*|"$design/mockup/"*) return 0 ;;
    *) return 1 ;;
  esac
}

mmw_prototype_path_has_symlink() {
  local top="$1" rel="$2" current="$1" part
  local -a parts=()
  IFS='/' read -r -a parts <<<"$rel"
  for part in "${parts[@]}"; do
    [ -n "$part" ] || continue
    current="$current/$part"
    [ -L "$current" ] && return 0
  done
  if [ -d "$current" ]; then
    [ -n "$(find "$current" -type l -print -quit 2>/dev/null)" ] && return 0
  fi
  return 1
}

mmw_prototype_validate_artifact() {
  local top="$1" man="$2" rel="$3"
  mmw_prototype_allowed_artifact_rel "$man" "$rel" || {
    echo "ERROR: prototype 产物必须是设计目录 prototype/ 或 mockup/ 下的相对路径:$rel" >&2
    return 1
  }
  [ -e "$top/$rel" ] || {
    echo "ERROR: prototype 产物不存在:$rel" >&2
    return 1
  }
  mmw_prototype_path_has_symlink "$top" "$rel" && {
    echo "ERROR: prototype 产物是软链或目录内含软链:$rel" >&2
    return 1
  }
  return 0
}

mmw_prototype_validate_evidence() {
  local top="$1" man="$2" rel="$3" iteration="$4" design round
  mmw_prototype_relpath_syntax_ok "$rel" || {
    echo "ERROR: prototype 证据路径非法:$rel" >&2
    return 1
  }
  design="$(mmw_prototype_design_rel "$man")" || return 1
  round="$(printf '%03d' "$iteration")"
  case "$rel" in "$design/prototype/runs/$round/"*) ;; *)
    echo "ERROR: 第 $iteration 轮证据必须放 $design/prototype/runs/$round/:$rel" >&2
    return 1 ;;
  esac
  [ -e "$top/$rel" ] || { echo "ERROR: prototype 证据不存在:$rel" >&2; return 1; }
  mmw_prototype_path_has_symlink "$top" "$rel" && {
    echo "ERROR: prototype 证据是软链或目录内含软链:$rel" >&2
    return 1
  }
  return 0
}

# prototype 状态为空但磁盘已有正式产物时列出相对路径。README 是命令账本，不算未登记实现。
mmw_prototype_untracked_paths() {
  local top="$1" man="$2" design root abs
  design="$(mmw_prototype_design_rel "$man")" || return 1
  for root in "$design/prototype" "$design/mockup"; do
    abs="$top/$root"
    [ -d "$abs" ] || continue
    find "$abs" \( -type f -o -type l \) -print 2>/dev/null
  done | while IFS= read -r abs; do
    [ "$abs" = "$top/$design/prototype/README.md" ] && continue
    printf '%s\n' "${abs#"$top/"}"
  done | LC_ALL=C sort -u
}

# plan/build 只读取 accepted 的账本与 selected。输出 worktree 相对路径。
mmw_prototype_selected_relpaths() {
  local man="$1" status rel
  status="$(jq -r '.prototype.status // empty' "$man")"
  [ "$status" = accepted ] || return 0
  rel="$(jq -r '.prototype.log // empty' "$man")"
  [ -n "$rel" ] || { echo "ERROR: accepted prototype 缺 log" >&2; return 1; }
  printf '%s\n' "$rel"
  jq -r '.prototype.selected[]?' "$man"
}
