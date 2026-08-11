#!/usr/bin/env bash
# 配置里的产物基础路径合不合法。路径本身写死在技能里，这里只挡住 .mmw.json 配出
# 仓库外或者带 .. 的值。

set -euo pipefail

mmw_path_safe_segment() {
  local value="${1:-}" label="${2:-路径段}" prefix="${3:-mmw:}"
  if [ -z "$value" ]; then
    echo "$prefix $label 不能有空路径段" >&2
    return 1
  fi
  if [ "$value" = "." ] || [ "$value" = ".." ]; then
    echo "$prefix $label 不能是 . 或 .." >&2
    return 1
  fi
  if [[ "$value" == *[[:upper:]]* ]]; then
    echo "$prefix $label 只能用小写字母" >&2
    return 1
  fi
  if [[ ! "$value" =~ ^[a-z0-9] ]]; then
    echo "$prefix $label 首字符必须是字母或数字" >&2
    return 1
  fi
  if [[ ! "$value" =~ ^[a-z0-9][a-z0-9._-]*$ ]]; then
    echo "$prefix $label 只能包含小写字母、数字、点、下划线和连字符" >&2
    return 1
  fi
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
