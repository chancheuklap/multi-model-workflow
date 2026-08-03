#!/usr/bin/env bash
# 读仓库根的 .mmw.json，以及判定当前宿主。
#
# 这一层不做任何流程判断，只回答两类问题：这个仓库的参数是什么、我们跑在哪个
# 宿主里。判断留给技能，动作留给 adapter。

set -euo pipefail

# 仓库根。CLI 的每条命令都是（仓库，参数）的纯函数，仓库就是这里。
mmw_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || {
    echo "mmw: 当前目录不在 git 仓库里" >&2
    return 1
  }
}

mmw_config_path() {
  echo "$(mmw_repo_root)/.mmw.json"
}

# 配置缺失时立刻报错并给出补救命令，不用默认值兜过去。
mmw_require_config() {
  local path
  path="$(mmw_config_path)"
  if [ ! -f "$path" ]; then
    echo "mmw: 找不到 $path，先跑 mmw init" >&2
    return 1
  fi
  echo "$path"
}

# mmw_config <jq 表达式>
mmw_config() {
  local path
  path="$(mmw_require_config)" || return 1
  jq -er "$1" "$path" 2>/dev/null || {
    echo "mmw: .mmw.json 里没有 $1" >&2
    return 1
  }
}

# 当前宿主：claude-code | pi。两个变量都没有时报错，不猜。
mmw_host() {
  if [ -n "${MMW_HOST:-}" ]; then
    echo "$MMW_HOST"
  elif [ -n "${CLAUDECODE:-}" ]; then
    echo "claude-code"
  elif [ -n "${PI_CODING_AGENT:-}" ]; then
    echo "pi"
  else
    echo "mmw: 认不出当前宿主（CLAUDECODE 与 PI_CODING_AGENT 都没有设）" >&2
    echo "mmw: 要在别处跑，用 MMW_HOST=claude-code 或 MMW_HOST=pi 显式指定" >&2
    return 1
  fi
}

# mmw_model_field <角色> <字段>，字段是 family / id / effort。
mmw_model_field() {
  local role="$1" field="$2"
  mmw_config ".models[\"$role\"].$field"
}

mmw_path_field() {
  mmw_config ".paths[\"$1\"]"
}
