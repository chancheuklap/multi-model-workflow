#!/usr/bin/env bash
# 把 MMW 技能软链进一个宿主的技能目录。
#
#   install-skills.sh --dest <目录>          装
#   install-skills.sh --dest <目录> --check  只看装没装。装齐回 0，缺东西回 1
#
# 软链不拷贝：升级 runtime 之后技能跟着变，不用重装。五个宿主用同一份 skills-src，
# 因为技能正文对所有宿主是同一句——宿主差异由 cli/host-actions.json 在运行期回答。
#
# 本脚本从已安装 runtime 运行，所以链接不指向 MMW 源码仓库。
#
# 目标目录里同名的东西不是本脚本装的软链时一律不动它，报冲突并非零退出。那个位置
# 可能是用户自己的技能，覆盖掉他不会知道。
#
# 卸载靠 <目标目录>/.mmw-skills 这份清单：装之前先读上一次装了哪些，这次不再有的
# 删掉。没有清单就当第一次装。清单只记本脚本装过的名字，别人的技能不进去。

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILLS_SRC="$PLUGIN_ROOT/skills-src"

# readlink -f 在 macOS 自带的 BSD coreutils 上没有，自己解一次：相对链接按它所在
# 目录算，绝对链接直接用。目标不存在时回空串，调用方按「指向非 MMW 内容」处理。
resolve_link() {
  local link="$1" target
  target="$(readlink "$link")"
  case "$target" in
    /*) ;;
    *) target="$(dirname "$link")/$target" ;;
  esac
  (cd "$target" 2>/dev/null && pwd -P) || true
}

# 上一版是整目录拷贝。判断某个目录是不是 MMW 自己拷过去的，两条判据任一成立即可：
#
#   1. 名字在 .mmw-skill-names 里。那是 Cursor 那一面上一版留下的记账文件。
#   2. 它的 SKILL.md 与技能源逐字节相同。Grok 那一面上一版不记账，只有这条判得出来。
#
# 第二条不会误伤：内容一模一样时换成软链没有任何损失；用户改过一个字，两边就不同，
# 这里立刻退回报冲突，不动它。
was_old_copy() {
  local name="$1"
  if [ -f "$dest/.mmw-skill-names" ] && grep -qx "$name" "$dest/.mmw-skill-names"; then
    return 0
  fi
  [ -f "$dest/$name/SKILL.md" ] && [ -f "$SKILLS_SRC/$name/SKILL.md" ] \
    && cmp -s "$dest/$name/SKILL.md" "$SKILLS_SRC/$name/SKILL.md"
}

dest=""
mode=install
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dest) dest="${2:-}"; shift 2 ;;
    --check) mode=check; shift ;;
    *) echo "用法: install-skills.sh --dest <目录> [--check]" >&2; exit 2 ;;
  esac
done
[ -n "$dest" ] || { echo "用法: install-skills.sh --dest <目录> [--check]" >&2; exit 2; }

[ -d "$SKILLS_SRC" ] || { echo "ERROR: 找不到技能源 $SKILLS_SRC" >&2; exit 2; }

# 技能是含 SKILL.md 的目录。别的目录不是技能，不装。
names=""
for dir in "$SKILLS_SRC"/*/; do
  [ -f "$dir/SKILL.md" ] || continue
  names="$names $(basename "$dir")"
done
[ -n "$names" ] || { echo "ERROR: $SKILLS_SRC 下没有技能" >&2; exit 2; }

manifest="$dest/.mmw-skills"
rc=0

# 先清理上一次装了、这次没有的。两份清单都读：.mmw-skills 是本脚本的，
# .mmw-skill-names 是上一版整目录拷贝留下的。check 模式只报，不删。
for old_manifest in "$manifest" "$dest/.mmw-skill-names"; do
  [ -f "$old_manifest" ] || continue
  while IFS= read -r old; do
    [ -n "$old" ] || continue
    case " $names " in *" $old "*) continue ;; esac
    [ -e "$dest/$old" ] || continue
    if [ "$mode" = check ]; then
      echo "多余  $dest/$old" >&2
      rc=1
    else
      rm -rf "${dest:?}/$old"
      echo "删掉  $old"
    fi
  done < "$old_manifest"
done

[ "$mode" = check ] || mkdir -p "$dest"

for name in $names; do
  src="$SKILLS_SRC/$name"
  dst="$dest/$name"

  if [ -L "$dst" ]; then
    current="$(resolve_link "$dst")"
    if [ "$current" = "$src" ]; then
      continue
    fi
    # 指向别的 MMW runtime 就改指。check 不报这一种：doctor 常常从源码仓库跑，而
    # 机器上装的是已安装 runtime，两个路径本来就不同——把它判成没装是误报。装没装
    # 看的是链接落在某个 MMW 技能源里，不是落在哪一份。
    if [ -f "$current/SKILL.md" ] && [ -d "$current/../../skills-src" ]; then
      if [ "$mode" != check ]; then
        ln -sfn "$src" "$dst"
      fi
    else
      echo "冲突  $dst 指向非 MMW 内容，先处理它再装" >&2
      rc=1
    fi
  elif [ -d "$dst" ] && was_old_copy "$name"; then
    # 旧安装方式把技能整个拷过来，留下 .mmw-skill-names 记账。那份清单点名的目录
    # 是 MMW 自己装的，换成软链；不在清单里的目录一律不动。
    if [ "$mode" = check ]; then
      echo "旧拷贝  $name 还是拷贝，不是软链" >&2
      rc=1
    else
      rm -rf "$dst"
      ln -s "$src" "$dst"
      echo "换链  $name"
    fi
  elif [ -d "$dst" ] && [ -f "$dst/SKILL.md" ]; then
    # 是个技能目录，但既不在记账文件里，内容也跟技能源对不上。两种可能：上一版
    # 拷过去之后技能源改过（那是 MMW 的旧内容，删掉即可），或者有人改过它。
    # 这里分不出来，也不该替人决定。
    echo "停下  $dst 是拷贝，内容与技能源不同" >&2
    echo "      没改过它就删掉再重跑；改过就先把改动挪走" >&2
    rc=1
  elif [ -e "$dst" ]; then
    echo "冲突  $dst 已被非 MMW 内容占用，先处理它再装" >&2
    rc=1
  elif [ "$mode" = check ]; then
    echo "未装  $name" >&2
    rc=1
  else
    ln -s "$src" "$dst"
  fi
done

if [ "$mode" != check ] && [ "$rc" = 0 ]; then
  tmp="$(mktemp "$dest/.mmw-skills.XXXXXX")"
  for name in $names; do printf '%s\n' "$name" >> "$tmp"; done
  mv "$tmp" "$manifest"
  # 迁移完成，上一版的记账文件不再需要。留着它下次会被当成还有拷贝要清理。
  rm -f "$dest/.mmw-skill-names"
fi

exit "$rc"
