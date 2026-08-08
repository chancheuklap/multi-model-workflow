#!/usr/bin/env bash
# 配置里的产物基础路径合不合法。路径本身写死在技能里，这里只挡住 .mmw.json 配出
# 仓库外或者带 .. 的值。

set -euo pipefail

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

