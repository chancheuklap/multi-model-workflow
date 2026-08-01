#!/usr/bin/env bash
# 把这套东西装到一家宿主上。它本来就是宿主通用的组件——技能、角色、钩子，
# 作为插件整体分发只是图省事，不是必须。
#
#   install.sh --host <宿主>              装
#   install.sh --host <宿主> --check      只看装没装好，不动手（装齐回 0，缺东西回 1）
#   install.sh --host <宿主> --uninstall  拆掉本插件装的那些，别人的不碰
#
# 宿主取值就是 adapters/ 下的目录名。它做四件事，全是机械动作：
#   1. 软链技能给主线程，含本宿主那一份 mmw-dispatch
#   2. 按 fields.json 的模型表分组：翻得出模型名的走原生，翻出 null 的划进无头
#   3. 有无头组的话，把那几个角色点名的技能软链到派发后端
#   4. 按 fields.json 生成本宿主格式的角色文件
#
# 技能一律软链，改了实时生效；角色文件是生成的，改了源角色文件要重装。
# 这个分界是有意的：角色文件头部只有四个参数、正文是薄壳，改动频率极低；技能天天在改。

set -euo pipefail

PLUGIN_ROOT="${MMW_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PENDING="待实测"

die() { echo "ERROR: $*" >&2; exit 2; }

host="" mode=install
while [ $# -gt 0 ]; do
  case "$1" in
    --host) host="${2:-}"; shift 2 ;;
    --check|--uninstall) mode="$1"; shift ;;
    *) die "未知参数: $1（用法: install.sh --host <宿主> [--check|--uninstall]）" ;;
  esac
done
[ -n "$host" ] || die "--host 必填。可选：$(cd "$PLUGIN_ROOT/adapters" && ls -d */ | tr -d / | paste -sd'、' -)"

ADAPTER="$PLUGIN_ROOT/adapters/$host"
FIELDS="$ADAPTER/fields.json"
[ -f "$FIELDS" ] || die "没有这家宿主的翻译表: $FIELDS"

fields_get() {  # $1=键名
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ""))' "$FIELDS" "$1"
}
expand() { printf '%s' "${1/#\~/$HOME}"; }

skill_dir="$(expand "$(fields_get skillDir)")"
agent_dir="$(expand "$(fields_get agentDir)")"
hook_dir="$(expand "$(fields_get hookDir)")"

rc=0

# 一条软链的三种模式。只认自己装的那一条，别人的同名目录一律不碰。
link() {  # $1=源 $2=目标 $3=显示名
  local src="$1" dst="$2" name="$3"
  case "$mode" in
    --uninstall)
      if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        rm "$dst"; echo "拆掉  $name"
      elif [ -e "$dst" ]; then
        echo "跳过  ${name}（不是本插件装的，留着）"
      fi ;;
    --check)
      if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        echo "已装  $name"
      elif [ -e "$dst" ]; then
        echo "冲突  $name → 已被别的东西占着" >&2; rc=1
      else
        echo "未装  $name" >&2; rc=1
      fi ;;
    *)
      [ -e "$src" ] || die "要装的东西不在插件里: $src"
      mkdir -p "$(dirname "$dst")"
      if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        echo "已装  $name"
      elif [ -e "$dst" ]; then
        # 同名的东西已经在那儿了，且不是我们装的。宁可停下让人看一眼，也不覆盖。
        die "$dst 已被别的东西占着，先处理它再装"
      else
        ln -s "$src" "$dst"; echo "装好  $name"
      fi ;;
  esac
}

# ---------- 一、主线程侧的技能 ----------
if [ "$skill_dir" = "$PENDING" ] || [ -z "$skill_dir" ]; then
  echo "跳过  主线程技能：${host} 的技能目录还没实测，填进 fields.json 再装" >&2
  rc=1
else
  for src in "$PLUGIN_ROOT"/skills/*/; do
    sk="$(basename "$src")"
    link "${src%/}" "$skill_dir/$sk" "$sk"
  done
  # 派发那一份住适配层，各家一份，装的是本宿主这一份。
  # 全角括号紧跟变量时 bash 会把它当成变量名的一部分，所以这里一律 ${...} 写全。
  link "$ADAPTER/mmw-dispatch" "$skill_dir/mmw-dispatch" "mmw-dispatch（${host}）"
fi

# ---------- 二、分组 ----------
headless="$(python3 "$PLUGIN_ROOT/scripts/render-roles.py" \
              --fields "$FIELDS" --roles-dir "$PLUGIN_ROOT/roles" --list headless)"

# ---------- 三、无头侧的技能 ----------
# 走无头的角色看不见宿主加载的技能，它们那一侧要单独装一份。名单不另写：
# 那几个角色的 skills 字段合起来就是它。注意 mmw-evidence 不在里面——scout 走原生。
if [ -n "$headless" ]; then
  agent_skills="${MMW_AGENT_SKILLS_DIR:-${CODEX_HOME:-$HOME/.codex}/skills}"
  wanted="$(
    for r in $headless; do
      sed -n '/^---$/,/^---$/p' "$PLUGIN_ROOT/roles/$r.md" | awk '
        $0 == "skills:" { grab=1; next }
        grab && /^[[:space:]]+-[[:space:]]/ { sub(/^[[:space:]]+-[[:space:]]*/, ""); print; next }
        grab { exit }'
    done | sort -u
  )"
  [ -n "$wanted" ] || die "走无头的角色一份技能都没点名，检查 $PLUGIN_ROOT/roles/"
  for sk in $wanted; do
    link "$PLUGIN_ROOT/skills/$sk" "$agent_skills/$sk" "${sk}（派发后端）"
  done
fi

# ---------- 四、角色文件 ----------
if [ "$agent_dir" = "$PENDING" ] || [ -z "$agent_dir" ]; then
  echo "跳过  角色文件：${host} 的角色目录还没实测，填进 fields.json 再装" >&2
  rc=1
elif [ "$mode" = --uninstall ]; then
  for r in $(python3 "$PLUGIN_ROOT/scripts/render-roles.py" \
               --fields "$FIELDS" --roles-dir "$PLUGIN_ROOT/roles" --list native); do
    [ -f "$agent_dir/$r.md" ] && { rm "$agent_dir/$r.md"; echo "拆掉  $r.md"; }
  done
else
  args=(--fields "$FIELDS" --roles-dir "$PLUGIN_ROOT/roles" --out-dir "$agent_dir")
  [ "$mode" = --check ] && args+=(--check)
  python3 "$PLUGIN_ROOT/scripts/render-roles.py" "${args[@]}" || rc=1
fi

# ---------- 五、钩子 ----------
# 钩子的注册格式各家不同，所以它跟 mmw-dispatch 一样住适配层。
# 这里只把文件放到位；怎么让宿主认它，各家不一样，装完自己核对一次。
if [ -d "$ADAPTER/hooks" ]; then
  if [ "$hook_dir" = "$PENDING" ] || [ -z "$hook_dir" ]; then
    echo "跳过  钩子：${host} 的钩子目录还没实测，填进 fields.json 再装" >&2
    rc=1
  else
    for f in "$ADAPTER"/hooks/*; do
      link "$f" "$hook_dir/$(basename "$f")" "$(basename "$f")"
    done
    [ "$mode" = install ] && echo "注意  钩子文件已就位。这一家怎么注册钩子请自己核对一次——有的宿主认目录，有的要写进设置文件。" >&2
  fi
fi

exit "$rc"
