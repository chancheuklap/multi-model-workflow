#!/usr/bin/env bash
# 把审者要读的技能软链进无头命令行那一家自己的技能目录。
#
# 为什么软链不拷贝:插件里改一次方法论,下一轮审者立刻读到新的。拷贝会漂移。
# 为什么不把方法论粘进提示词:提示词会变成几千字,主线程要读好几个文件自己拼,
# 拼漏了看不出来;而且已经派出去的那批读的还是旧的。
#
#   install-reviewer.sh          装
#   install-reviewer.sh --check  只看装没装。装齐回 0,缺东西回 1

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_DIR="${MMW_AGENT_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"

# 审者要读的两份:审查方法论本身,加测试进仓资格线——
# 独立终审那一路要按它核这次新增和改动的测试。
WANTED=(mmw-reviewer mmw-tdd)

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-reviewer.sh [--check]" >&2; exit 2 ;;
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
