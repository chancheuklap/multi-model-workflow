#!/usr/bin/env bash
# 把 headless Codex 要读的方法论软链进它自己的技能目录。
# 本脚本从已安装 runtime 运行，所以链接不指向 MMW 源码仓库。
#
#   install-agent-skills.sh          装
#   install-agent-skills.sh --check  只看装没装。装齐回 0,缺东西回 1

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="${MMW_AGENT_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"

# 审查者读审查方法论，`planner` 读写计划方法论，两边都要读测试那一份：
# 审查者按它验证这次新增和改动的测试，`planner` 按它写测试规划。
# `investigator` 按 research task 指定的身份和方向读取 mmw-research 的对应 reference。
WANTED=(mmw-reviewer mmw-planner mmw-tdd mmw-research)

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-agent-skills.sh [--check]" >&2; exit 2 ;;
esac

rc=0
[ "$mode" = check ] || mkdir -p "$SKILLS_DIR"

for sk in "${WANTED[@]}"; do
  src="$PLUGIN_ROOT/skills-src/$sk"
  dst="$SKILLS_DIR/$sk"

  if [ ! -d "$src" ]; then
    echo "ERROR: 插件里没有这份技能: $src" >&2
    exit 2
  fi

  if [ -L "$dst" ]; then
    current="$(readlink "$dst")"
    case "$current" in
      /*) resolved="$current" ;;
      *)
        resolved_dir="$(cd "$(dirname "$dst")" \
          && cd "$(dirname "$current")" 2>/dev/null && pwd -P || true)"
        if [ -n "$resolved_dir" ]; then
          resolved="$resolved_dir/$(basename "$current")"
        else
          resolved="$current"
        fi
        ;;
    esac
    if [ "$resolved" = "$src" ]; then
      echo "已装  $sk"
    elif [ -f "$(dirname "$(dirname "$resolved")")/.codex-plugin/plugin.json" ] \
      || [ -f "$(dirname "$(dirname "$resolved")")/.claude-plugin/plugin.json" ]; then
      if [ "$mode" = check ]; then
        echo "旧链  $sk → $resolved" >&2
        rc=1
      else
        ln -sfn "$src" "$dst"
        echo "更新  $sk → $dst"
      fi
    else
      echo "冲突  $sk → $dst 指向非 MMW 内容，先处理它再装" >&2
      rc=1
    fi
  elif [ -e "$dst" ]; then
    echo "冲突  $sk → $dst 已被非 MMW 内容占用，先处理它再装" >&2
    rc=1
  elif [ "$mode" = check ]; then
    echo "未装  $sk" >&2
    rc=1
  else
    ln -s "$src" "$dst"
    echo "装好  $sk → $dst"
  fi
done

exit "$rc"
