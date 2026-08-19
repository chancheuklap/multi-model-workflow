#!/usr/bin/env bash
# 装两样东西进本机的每个宿主：skills.txt 列出的上游技能（软链），以及 .mcp.json
# 声明的检索服务器（写进宿主自己的配置，由 mcp/install-mcp.sh 完成）。
#
# 软链不是拷贝：宿主读的就是仓库里那个文件。在用技能的当中直接改
# mmw-v2/upstream/skills/<桶>/<名>/SKILL.md，下一次调用就是新的，不用重装。
# （只有 frontmatter 的 description 是宿主启动时扫的，改它要重开会话。）
#
# MCP 那一侧写的是绝对路径，指向这个 checkout：要从主检出装，不要从任务 worktree 装。
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西回 1
#
# 五个宿主的用户触发开关都读 SKILL.md 的 disable-model-invocation，
# Codex 另读技能目录里的 agents/openai.yaml。两者都在技能目录内，软链一并带过去，
# 所以这里没有任何按宿主分支的逻辑。

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/upstream/skills"
LIST="$ROOT/skills.txt"
MANIFEST_NAME=".mmw-skills"

# 宿主的用户级技能目录。目录不存在就当这个宿主没装，跳过。
# MMW_V2_HOME 只给测试用：把五个宿主整体搬到一个一次性目录下，不碰真的家目录。
HOME_DIR="${MMW_V2_HOME:-$HOME}"
HOST_DIRS=(
  "$HOME_DIR/.claude/skills"
  "${CODEX_HOME:-$HOME_DIR/.codex}/skills"
  "${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}/skills"
  "$HOME_DIR/.cursor/skills"
  "$HOME_DIR/.grok/skills"
)

die() {
  echo "mmw-v2 install: $1" >&2
  exit "${2:-1}"
}

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) die "用法：install.sh [--check]" 2 ;;
esac

[ -f "$LIST" ] || die "缺技能名单：$LIST"
[ -d "$SKILLS_SRC" ] || die "缺上游技能目录：$SKILLS_SRC"

# 读名单。顺便当场验证每个都真的存在——名单写错要在动宿主之前就停。
wanted_paths=()
wanted_names=()
while IFS= read -r line; do
  line="${line%%#*}"
  line="$(echo "$line" | tr -d '[:space:]')"
  [ -n "$line" ] || continue
  [ -f "$SKILLS_SRC/$line/SKILL.md" ] || die "名单里的技能不存在：$line"
  wanted_paths+=("$line")
  wanted_names+=("$(basename "$line")")
done < "$LIST"

[ "${#wanted_names[@]}" -gt 0 ] || die "名单是空的：$LIST"

# 名字撞车要在装之前发现：两个技能软链成同一个名字，后装的会盖掉先装的。
dupes="$(printf '%s\n' "${wanted_names[@]}" | sort | uniq -d)"
[ -z "$dupes" ] || die "名单里有重名技能：$(echo "$dupes" | tr '\n' ' ')"

rc=0
installed_hosts=0

for dest in "${HOST_DIRS[@]}"; do
  host_home="$(dirname "$dest")"
  if [ ! -d "$host_home" ]; then
    echo "跳过  ${dest}（宿主没装）"
    continue
  fi
  installed_hosts=$((installed_hosts + 1))

  manifest="$dest/$MANIFEST_NAME"

  if [ "$mode" = check ]; then
    for i in "${!wanted_names[@]}"; do
      link="$dest/${wanted_names[$i]}"
      want="$SKILLS_SRC/${wanted_paths[$i]}"
      if [ ! -L "$link" ] || [ "$(readlink "$link")" != "$want" ]; then
        echo "缺    $link" >&2
        rc=1
      fi
    done
    continue
  fi

  mkdir -p "$dest"

  # 先按上一次的记录清理：那时装了、这次名单里没有的，摘掉。
  # 只摘我们自己装的软链——目标不指回本仓库的一律不碰，宁可留着也不误删。
  if [ -f "$manifest" ]; then
    while IFS= read -r old; do
      [ -n "$old" ] || continue
      printf '%s\n' "${wanted_names[@]}" | grep -qx "$old" && continue
      stale="$dest/$old"
      [ -L "$stale" ] || continue
      case "$(readlink "$stale")" in
        "$SKILLS_SRC"/*) rm "$stale"; echo "摘掉  $stale" ;;
      esac
    done < "$manifest"
  fi

  # 清单只记真正装上的。装不上的写进去，下一轮清理就会去找一个我们没装过的东西。
  linked=()
  for i in "${!wanted_names[@]}"; do
    name="${wanted_names[$i]}"
    link="$dest/$name"
    want="$SKILLS_SRC/${wanted_paths[$i]}"

    if [ -e "$link" ] || [ -L "$link" ]; then
      # 已经是我们指向本仓库的软链，直接重指（升级路径时也走这条）。
      if [ -L "$link" ] && [[ "$(readlink "$link")" == "$SKILLS_SRC"/* ]]; then
        :
      else
        echo "冲突  $dest/$name 已存在且不是本仓库装的，跳过" >&2
        rc=1
        continue
      fi
    fi
    ln -sfn "$want" "$link"
    linked+=("$name")
  done

  printf '%s\n' "${linked[@]}" > "$manifest"
  echo "已装  ${#linked[@]} 个技能 -> $dest"
done

[ "$installed_hosts" -gt 0 ] || die "一个宿主都没找到，什么都没装"

# 检索服务器。技能是软链、MCP 是写进各宿主自己的配置文件，两件事形状不同，
# 所以分两个脚本；这里只负责按同一个模式调用它，服务器定义在 .mcp.json。
echo
if [ "$mode" = check ]; then
  bash "$ROOT/mcp/install-mcp.sh" --check || rc=1
  bash "$ROOT/mcp/install-mcp.sh" --check-toml || rc=1
else
  bash "$ROOT/mcp/install-mcp.sh" || rc=$?
fi

# 语言工具与编辑后诊断。两步：先把语言工具装齐（装进 mmw-v2/tools/，每次最新稳定版，
# 并把 serena 的语言服务器指过来），再把诊断适配器注册进五个宿主。分两步是因为失败
# 原因完全不同——工具装不上是包管理器的事，注册不上是宿主配置的事，混在一条命令里
# 会让报错指不到地方。
echo
if [ "$mode" = check ]; then
  bash "$ROOT/tools/install.sh" --check || rc=1
  bash "$ROOT/diagnostics/install-hooks.sh" --check || rc=1
else
  bash "$ROOT/tools/install.sh" || rc=$?
  bash "$ROOT/diagnostics/install-hooks.sh" || rc=$?
fi

# 真起一次三台服务器，握手并列工具。写完配置不等于装好：配置写对了、而服务器因为
# 别的原因起不来，是这一层唯一能发现的失败。刚踩过一次——serena 的 context 里删掉一个
# 必填字段，配置文件看着完全正常，安装器一路报「装好」，服务器却根本起不来。
# 约半分钟，值这个钱。
echo
if ! python3 "$ROOT/mcp/probe.py"; then
  echo "检索服务器起不来，上面那行说了是哪一台。配置已经写完，修好再跑一次本脚本。" >&2
  rc=1
fi

if [ "$mode" = check ]; then
  [ "$rc" -eq 0 ] && echo "齐了：$installed_hosts 个宿主 × ${#wanted_names[@]} 个技能，加三台检索服务器与编辑后诊断"
else
  echo
  echo "源目录：$SKILLS_SRC"
  echo "改技能直接改源目录里的文件，宿主下次调用就是新的。"
  echo "MCP 写的是绝对路径，指向 ${ROOT}。换仓库位置要重跑本脚本。"
fi

exit "$rc"
