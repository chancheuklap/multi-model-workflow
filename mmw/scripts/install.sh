#!/usr/bin/env bash
# 适配层。装在模型专用宿主上时，这套东西是两半：主线程那一半由宿主自己装（插件清单），
# 被派出去干活的那一半得装到派发后端里，否则被派者找不到自己的方法论。
#
# 这里只管后一半。名单不另写一份——六份角色的 skills 字段合起来就是它。
# 用软链不用拷贝：改了插件里的技能，两侧同时生效，不会出现一边新一边旧。
#
#   install.sh            装
#   install.sh --check    只看装没装好，不动手（装齐回 0，缺东西回 1）
#   install.sh --uninstall 拆掉本插件装的那些，别人的不碰
#
# 多模型宿主（Cursor、pi、Droid）不需要这个脚本：那边一次安装六个角色全是原生角色，
# 技能跟着插件一起加载，没有「另一侧」。

set -euo pipefail

PLUGIN_ROOT="${MMW_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
AGENT_SKILLS="${MMW_AGENT_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"

mode="${1:-install}"
case "$mode" in install|--check|--uninstall) ;; *) echo "用法: install.sh [--check|--uninstall]" >&2; exit 2 ;; esac

# 角色的 skills 字段：`skills:` 之后连续的 `  - 名字`
wanted="$(
  for rf in "$PLUGIN_ROOT"/roles/*.md; do
    sed -n '/^---$/,/^---$/p' "$rf" | awk '
      $0 == "skills:" { grab=1; next }
      grab && /^[[:space:]]+-[[:space:]]/ { sub(/^[[:space:]]+-[[:space:]]*/, ""); print; next }
      grab { exit }'
  done | sort -u
)"
[ -n "$wanted" ] || { echo "ERROR: 没有任何角色声明要读的技能，检查 $PLUGIN_ROOT/roles/" >&2; exit 2; }

rc=0
for sk in $wanted; do
  src="$PLUGIN_ROOT/skills/$sk"
  dst="$AGENT_SKILLS/$sk"

  case "$mode" in
    --uninstall)
      # 只拆自己装的软链。别人的同名目录或真目录一律不碰。
      if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        rm "$dst"; echo "拆掉  $sk"
      elif [ -e "$dst" ]; then
        echo "跳过  ${sk}（不是本插件装的，留着）"
      fi
      continue ;;

    --check)
      if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        echo "已装  $sk"
      elif [ -e "$dst" ]; then
        echo "冲突  $sk → 已被别的东西占着: $(readlink "$dst" 2>/dev/null || echo "$dst")" >&2; rc=1
      else
        echo "未装  $sk" >&2; rc=1
      fi
      continue ;;
  esac

  [ -f "$src/SKILL.md" ] || { echo "ERROR: 角色点名的技能不在插件里: $src/SKILL.md" >&2; exit 2; }
  mkdir -p "$AGENT_SKILLS"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "已装  $sk"
  elif [ -e "$dst" ]; then
    # 同名的东西已经在那儿了，且不是我们装的。宁可停下让人看一眼，也不覆盖。
    echo "ERROR: $dst 已被别的东西占着，先处理它再装" >&2; exit 2
  else
    ln -s "$src" "$dst"; echo "装好  $sk"
  fi
done

exit "$rc"
