#!/usr/bin/env bash
# 把 skills.txt 列出的技能和 agents/ 下的 subagent 装到本机，让每个宿主都读得到。就这两件事。
#
# 技能有三个来源：mattpocock 上游的在 upstream/skills/，我们自己写的在 skills/（名单里
# 前缀 self/），diagram-design 上游的在 upstream-diagram-design/skills/（前缀 dd/）。三者
# 装法完全一样。
#
# 软链不是拷贝：宿主读的就是仓库里那个文件。在用技能的当中直接改源目录下的 SKILL.md，
# 下一次调用就是新的，不用重装。（只有 frontmatter 的 description 是宿主启动时扫的，
# 改它要重开会话。）
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西或有残留回 1
#
# 技能装两处，不按宿主分。~/.agents/skills 是各家通用的位置，Codex、Cursor、Grok、Pi
# 都原生扫它；Claude Code 不扫，只认 ~/.claude/skills，所以那一处再装一份。两处装的是
# 同一批软链，都直接指向仓库源目录，彼此不串。
#
# 宿主的用户触发开关都读 SKILL.md 的 disable-model-invocation，Codex 另读技能目录里的
# agents/openai.yaml。两者都在技能目录内，软链一并带过去，所以技能安装没有任何按宿主
# 分支的逻辑。
#
# subagent 跟技能不同：模型字段各家写法不一样，同一份正文必须按宿主换壳。壳由
# agents/assemble.py 从 body.md + agent.json 装配到 agents/<名>/out/，这里只把成品
# 软链到各宿主的 agent 目录。软链仍指回仓库：改了 body.md 跑一次装配（或本脚本），
# 宿主下一次调用就是新的。
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/upstream/skills"
SELF_SRC="$ROOT/skills"
DD_SRC="$ROOT/upstream-diagram-design/skills"
LIST="$ROOT/skills.txt"
MANIFEST_NAME=".mmw-skills"

# MMW_V2_HOME 只给测试用：把安装位置整体搬到一个一次性目录下，不碰真的家目录。
HOME_DIR="${MMW_V2_HOME:-$HOME}"

# 通用位置。不属于任何一个宿主，所以无条件建。
NEUTRAL_DIR="$HOME_DIR/.agents/skills"
# Claude Code 专用。它不扫通用位置。宿主没装就跳过。
CLAUDE_DIR="$HOME_DIR/.claude/skills"

HOST_DIRS=(
  "$NEUTRAL_DIR"
  "$CLAUDE_DIR"
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
wanted_dirs=()
wanted_names=()
while IFS= read -r line; do
  line="${line%%#*}"
  line="$(echo "$line" | tr -d '[:space:]')"
  [ -n "$line" ] || continue
  case "$line" in
    self/*) dir="$SELF_SRC/${line#self/}" ;;
    dd/*) dir="$DD_SRC/${line#dd/}" ;;
    *) dir="$SKILLS_SRC/$line" ;;
  esac
  [ -f "$dir/SKILL.md" ] || die "名单里的技能不存在：$line"
  wanted_dirs+=("$dir")
  wanted_names+=("$(basename "$line")")
done < "$LIST"

[ "${#wanted_names[@]}" -gt 0 ] || die "名单是空的：$LIST"

# 名字撞车要在装之前发现：两个技能软链成同一个名字，后装的会盖掉先装的。
dupes="$(printf '%s\n' "${wanted_names[@]}" | sort | uniq -d)"
[ -z "$dupes" ] || die "名单里有重名技能：$(echo "$dupes" | tr '\n' ' ')"

rc=0
installed_dests=0

for dest in "${HOST_DIRS[@]}"; do
  host_home="$(dirname "$dest")"
  if [ "$dest" != "$NEUTRAL_DIR" ] && [ ! -d "$host_home" ]; then
    echo "跳过  ${dest}（宿主没装）"
    continue
  fi
  installed_dests=$((installed_dests + 1))

  manifest="$dest/$MANIFEST_NAME"

  if [ "$mode" = check ]; then
    for i in "${!wanted_names[@]}"; do
      link="$dest/${wanted_names[$i]}"
      want="${wanted_dirs[$i]}"
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
        "$SKILLS_SRC"/* | "$SELF_SRC"/* | "$DD_SRC"/*) rm "$stale"; echo "摘掉  $stale" ;;
      esac
    done < "$manifest"
  fi

  # 清单只记真正装上的。装不上的写进去，下一轮清理就会去找一个我们没装过的东西。
  linked=()
  for i in "${!wanted_names[@]}"; do
    name="${wanted_names[$i]}"
    link="$dest/$name"
    want="${wanted_dirs[$i]}"

    if [ -e "$link" ] || [ -L "$link" ]; then
      # 已经是我们指向本仓库的软链，直接重指（升级路径时也走这条）。
      if [ -L "$link" ] && { [[ "$(readlink "$link")" == "$SKILLS_SRC"/* ]] || [[ "$(readlink "$link")" == "$SELF_SRC"/* ]] || [[ "$(readlink "$link")" == "$DD_SRC"/* ]]; }; then
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

# ---------------- 退役的技能位置 ----------------

# 技能以前按宿主各装一份。下面四处不再是安装目标，主循环也不会再走到它们，残留的软链
# 就会一直留着——而各自的宿主仍在扫它们。残留是上一轮名单里的旧版本，跟通用位置的那份
# 撞名；实测里 Grok 取 ~/.grok/skills 那份，把通用位置的盖住，不报错也不提示。
# 所以每次安装都摘一遍。
RETIRED_DIRS=(
  "${CODEX_HOME:-$HOME_DIR/.codex}/skills"
  "${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}/skills"
  "$HOME_DIR/.cursor/skills"
  "$HOME_DIR/.grok/skills"
)

for dest in "${RETIRED_DIRS[@]}"; do
  manifest="$dest/$MANIFEST_NAME"
  [ -f "$manifest" ] || continue

  # 只摘指回本仓库的软链。别人放在同一个目录里的东西一律不碰。
  stale_links=()
  while IFS= read -r old; do
    [ -n "$old" ] || continue
    stale="$dest/$old"
    [ -L "$stale" ] || continue
    case "$(readlink "$stale")" in
      "$SKILLS_SRC"/* | "$SELF_SRC"/* | "$DD_SRC"/*) stale_links+=("$stale") ;;
    esac
  done < "$manifest"

  if [ "$mode" = check ]; then
    if [ "${#stale_links[@]}" -gt 0 ]; then
      echo "残留  ${dest} 还有 ${#stale_links[@]} 条上一代的技能软链，跑一次 install.sh 摘掉" >&2
      rc=1
    fi
    continue
  fi

  if [ "${#stale_links[@]}" -gt 0 ]; then
    for stale in "${stale_links[@]}"; do
      rm "$stale"
    done
  fi
  rm "$manifest"
  echo "退役  摘掉 ${#stale_links[@]} 个技能 <- ${dest}"
done

# ---------------- subagent ----------------

AGENTS_SRC="$ROOT/agents"
AGENT_MANIFEST_NAME=".mmw-agents"

if [ -d "$AGENTS_SRC" ]; then
  # 成品必须与源一致：装的时候先装配，查的时候只验不写。
  if [ "$mode" = check ]; then
    python3 "$AGENTS_SRC/assemble.py" --check || rc=1
  else
    python3 "$AGENTS_SRC/assemble.py"
  fi

  agent_names=()
  for d in "$AGENTS_SRC"/*/; do
    [ -f "${d}agent.json" ] || continue
    agent_names+=("$(basename "$d")")
  done
  [ "${#agent_names[@]}" -gt 0 ] || die "agents/ 目录在，里面却一个 agent 都没有"

  # 一行一个安装点：宿主根|目标目录|成品文件名|落地后缀。
  # grok 一家两处：agents/ 放定义与模型，roles/ 放只读能力与推理力度。
  agent_dests=(
    "$HOME_DIR/.claude|$HOME_DIR/.claude/agents|claude.md|.md"
    "${CODEX_HOME:-$HOME_DIR/.codex}|${CODEX_HOME:-$HOME_DIR/.codex}/agents|codex.toml|.toml"
    "${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}|${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}/agents|pi.md|.md"
    "$HOME_DIR/.cursor|$HOME_DIR/.cursor/agents|cursor.md|.md"
    "$HOME_DIR/.grok|$HOME_DIR/.grok/agents|grok.md|.md"
    "$HOME_DIR/.grok|$HOME_DIR/.grok/roles|grok.role.toml|.toml"
  )

  for row in "${agent_dests[@]}"; do
    IFS='|' read -r host_home dest src_name suffix <<<"$row"
    [ -d "$host_home" ] || continue

    manifest="$dest/$AGENT_MANIFEST_NAME"

    if [ "$mode" = check ]; then
      for name in "${agent_names[@]}"; do
        link="$dest/$name$suffix"
        want="$AGENTS_SRC/$name/out/$src_name"
        if [ ! -L "$link" ] || [ "$(readlink "$link")" != "$want" ]; then
          echo "缺    $link" >&2
          rc=1
        fi
      done
      continue
    fi

    mkdir -p "$dest"

    # 清理上次装了、这次没有的。只摘指回本仓库 agents/ 的软链。
    if [ -f "$manifest" ]; then
      while IFS= read -r old; do
        [ -n "$old" ] || continue
        printf '%s\n' "${agent_names[@]/%/$suffix}" | grep -qx "$old" && continue
        stale="$dest/$old"
        [ -L "$stale" ] || continue
        case "$(readlink "$stale")" in
          "$AGENTS_SRC"/*) rm "$stale"; echo "摘掉  $stale" ;;
        esac
      done < "$manifest"
    fi

    linked=()
    for name in "${agent_names[@]}"; do
      link="$dest/$name$suffix"
      want="$AGENTS_SRC/$name/out/$src_name"
      if [ -e "$link" ] || [ -L "$link" ]; then
        if [ -L "$link" ] && [[ "$(readlink "$link")" == "$AGENTS_SRC"/* ]]; then
          :
        else
          echo "冲突  $link 已存在且不是本仓库装的，跳过" >&2
          rc=1
          continue
        fi
      fi
      ln -sfn "$want" "$link"
      linked+=("$name$suffix")
    done

    if [ "${#linked[@]}" -gt 0 ]; then
      printf '%s\n' "${linked[@]}" > "$manifest"
    else
      : > "$manifest"
    fi
    echo "已装  ${#linked[@]} 个 agent -> $dest"
  done
fi

if [ "$mode" = check ]; then
  [ "$rc" -eq 0 ] && echo "齐了：${installed_dests} 处 × ${#wanted_names[@]} 个技能"
else
  echo
  echo "源目录：${SKILLS_SRC}（上游）、${SELF_SRC}（自研）、${DD_SRC}（diagram-design 上游）"
  echo "改技能直接改源目录里的文件，宿主下次调用就是新的。"
fi

exit "$rc"
