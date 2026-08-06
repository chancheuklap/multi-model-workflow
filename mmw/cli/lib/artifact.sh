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

mmw_artifact_path() {
  local argument_count="$#" kind="${1:-}" artifact_dir="${2:-}" issue_dir="${3:-}" base
  case "$kind" in
    prototype) base="$(mmw_path_field prototypes)" ;;
    evidence) base="$(mmw_path_field evidence)" ;;
    scratch) base="$(mmw_path_field scratch)" ;;
    *)
      echo "mmw: artifact path 类型只能是 prototype、evidence 或 scratch：${kind:-<空>}" >&2
      return 1
      ;;
  esac

  mmw_artifact_safe_segment "$artifact_dir" "产物目录" || return 1
  if [ "$argument_count" -eq 3 ]; then
    mmw_artifact_issue_segment "$issue_dir" || return 1
    printf '%s/%s/%s\n' "${base%/}" "$artifact_dir" "$issue_dir"
  else
    printf '%s/%s\n' "${base%/}" "$artifact_dir"
  fi
}
