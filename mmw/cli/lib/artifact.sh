#!/usr/bin/env bash
# prototype、evidence 与 scratch 的仓库内落点。

set -euo pipefail

mmw_artifact_safe_segment() {
  local segment="${1:-}" label="${2:-路径段}"
  case "$segment" in
    ""|.|..|[!A-Za-z0-9]*|*[!A-Za-z0-9._-]*)
      echo "mmw: ${label}必须是单个安全路径段：${segment:-<空>}" >&2
      return 1
      ;;
  esac
}

mmw_artifact_issue_segment() {
  local segment="${1:-}" number
  mmw_artifact_safe_segment "$segment" "issue 子目录" || return 1
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

mmw_artifact_scratch_segment() {
  local segment="${1:-}" task_slug
  case "$segment" in
    issue-*) mmw_artifact_issue_segment "$segment" ;;
    task-*)
      mmw_artifact_safe_segment "$segment" "scratch 任务子目录" || return 1
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

mmw_artifact_safe_base() {
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

mmw_artifact_root() {
  local kind="${1:-}" base
  case "$kind" in
    prototype) base="$(mmw_path_field prototypes)" ;;
    evidence) base="$(mmw_path_field evidence)" ;;
    scratch) base="$(mmw_path_field scratch)" ;;
    review) base="$(mmw_path_field reviews)" ;;
    *)
      echo "mmw: artifact root 类型只能是 prototype、evidence、scratch 或 review：${kind:-<空>}" >&2
      return 1
      ;;
  esac
  mmw_artifact_safe_base "$base" || return 1
  printf '%s\n' "$base"
}

mmw_artifact_path() {
  local argument_count="$#" kind="${1:-}" artifact_dir="${2:-}" issue_dir="${3:-}" base
  case "$kind" in
    prototype|evidence|scratch) base="$(mmw_artifact_root "$kind")" ;;
    *)
      echo "mmw: artifact path 类型只能是 prototype、evidence 或 scratch：${kind:-<空>}" >&2
      return 1
      ;;
  esac

  mmw_artifact_safe_base "$base" || return 1
  mmw_artifact_safe_segment "$artifact_dir" "产物目录" || return 1
  if [ "$argument_count" -eq 3 ]; then
    if [ "$kind" = "scratch" ]; then
      mmw_artifact_scratch_segment "$issue_dir" || return 1
    else
      mmw_artifact_issue_segment "$issue_dir" || return 1
    fi
    printf '%s/%s/%s\n' "${base%/}" "$artifact_dir" "$issue_dir"
  else
    printf '%s/%s\n' "${base%/}" "$artifact_dir"
  fi
}
