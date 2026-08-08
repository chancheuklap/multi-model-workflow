#!/usr/bin/env bash
# spec、prototype、research、evidence、scratch 与 review 的仓库内路径。

set -euo pipefail

mmw_path_safe_segment() {
  local segment="${1:-}" label="${2:-路径段}"
  case "$segment" in
    ""|.|..|[!A-Za-z0-9]*|*[!A-Za-z0-9._-]*)
      echo "mmw: ${label}必须是单个安全路径段：${segment:-<空>}" >&2
      return 1
      ;;
  esac
}

mmw_path_issue_segment() {
  local segment="${1:-}" number
  mmw_path_safe_segment "$segment" "issue 子目录" || return 1
  case "$segment" in
    issue-*) number="${segment#issue-}" ;;
    *)
      echo "mmw: issue 子目录必须是 issue-<编号>：$segment" >&2
      return 1
      ;;
  esac
  case "$number" in
    ""|*[!0-9]*)
      echo "mmw: issue 子目录必须是 issue-<编号>：$segment" >&2
      return 1
      ;;
  esac
}

mmw_path_scratch_segment() {
  local segment="${1:-}" task_slug
  case "$segment" in
    issue-*) mmw_path_issue_segment "$segment" ;;
    task-*)
      mmw_path_safe_segment "$segment" "scratch 任务子目录" || return 1
      task_slug="${segment#task-}"
      if [ -z "$task_slug" ]; then
        echo "mmw: scratch 任务子目录必须是 task-<任务 slug>：$segment" >&2
        return 1
      fi
      ;;
    *)
      echo "mmw: scratch 子目录必须是 issue-<编号> 或 task-<任务 slug>：${segment:-<空>}" >&2
      return 1
      ;;
  esac
}

mmw_path_safe_base() {
  local base="${1:-}" segment
  local -a segments
  case "$base" in
    ""|/*|*/|*//* )
      echo "mmw: 产物基础路径必须是仓库内的规范相对路径：${base:-<空>}" >&2
      return 1
      ;;
  esac
  IFS='/' read -r -a segments <<< "$base"
  for segment in "${segments[@]}"; do
    case "$segment" in
      ""|.|..|*[!A-Za-z0-9._-]*)
        echo "mmw: 产物基础路径必须是仓库内的规范相对路径：$base" >&2
        return 1
        ;;
    esac
  done
}

mmw_path_root() {
  local kind="${1:-}" base
  case "$kind" in
    spec) base="$(mmw_path_field specs)" ;;
    prototype) base="$(mmw_path_field prototypes)" ;;
    research) base="$(mmw_path_field research)" ;;
    evidence) base="$(mmw_path_field evidence)" ;;
    scratch) base="$(mmw_path_field scratch)" ;;
    review) base="$(mmw_path_field reviews)" ;;
    *)
      echo "mmw: path 类型只能是 spec、prototype、research、evidence、scratch 或 review：${kind:-<空>}" >&2
      return 1
      ;;
  esac
  mmw_path_safe_base "$base" || return 1
  printf '%s\n' "$base"
}

mmw_path_spec() {
  local slug="${1:-}" base
  mmw_path_safe_segment "$slug" "任务 slug" || return 1
  base="$(mmw_path_root spec)" || return 1
  printf '%s/%s/%s.md\n' "${base%/}" "$slug" "$slug"
}

mmw_path_resolve() {
  local argument_count="$#" kind="${1:-}" output_dir="${2:-}" issue_dir="${3:-}" base
  case "$kind" in
    prototype|research|evidence|scratch) base="$(mmw_path_root "$kind")" ;;
    *)
      echo "mmw: path 类型只能是 prototype、research、evidence 或 scratch：${kind:-<空>}" >&2
      return 1
      ;;
  esac

  mmw_path_safe_base "$base" || return 1
  mmw_path_safe_segment "$output_dir" "产物目录" || return 1
  if [ "$argument_count" -eq 3 ]; then
    if [ "$kind" = "scratch" ]; then
      mmw_path_scratch_segment "$issue_dir" || return 1
    else
      mmw_path_issue_segment "$issue_dir" || return 1
    fi
    printf '%s/%s/%s\n' "${base%/}" "$output_dir" "$issue_dir"
  else
    printf '%s/%s\n' "${base%/}" "$output_dir"
  fi
}
