#!/usr/bin/env bash
# 把无头劳动力要读的方法论软链进它自己的技能目录。
# 用软链不拷贝:插件里改一次方法论,下一轮派出去的立刻读到新的。
#
#   install-agent-skills.sh          装
#   install-agent-skills.sh --check  只看装没装。装齐回 0,缺东西回 1

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="${MMW_AGENT_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"

# 审者读审查方法论,写计划工人读写计划方法论,两边都要读测试那一份:
# 审者按它核这次新增和改动的测试,写计划工人按它写测试规划。
WANTED=(mmw-reviewer mmw-planner mmw-tdd)

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-agent-skills.sh [--check]" >&2; exit 2 ;;
esac

rc=0
[ "$mode" = check ] || mkdir -p "$SKILLS_DIR"

for sk in "${WANTED[@]}"; do
  src="$PLUGIN_ROOT/skills/$sk"
  dst="$SKILLS_DIR/$sk"

  if [ ! -d "$src" ]; then
    echo "ERROR: 插件里没有这份技能: $src" >&2
    exit 2
  fi

  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "已装  $sk"
  elif [ -e "$dst" ]; then
    # 同名的东西已经在那儿了,而且不是我们装的。宁可停下让人看一眼,也不覆盖。
    echo "冲突  $sk → $dst 已被别的东西占着,先处理它再装" >&2
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
