#!/usr/bin/env bash
# 把 skills.txt 列出的技能、agents/ 下的 subagent 和 hooks/ 下的纪律注入层装进本机的每个宿主。就这三件事。
#
# 技能有两个来源：上游的在 upstream/skills/，我们自己写的在 skills/，名单里用 self/ 前缀
# 区分。两者装法完全一样。
#
# 软链不是拷贝：宿主读的就是仓库里那个文件。在用技能的当中直接改源目录下的 SKILL.md，
# 下一次调用就是新的，不用重装。（只有 frontmatter 的 description 是宿主启动时扫的，
# 改它要重开会话。）
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西回 1
#
# 五个宿主的用户触发开关都读 SKILL.md 的 disable-model-invocation，
# Codex 另读技能目录里的 agents/openai.yaml。两者都在技能目录内，软链一并带过去，
# 所以技能安装没有任何按宿主分支的逻辑。
#
# subagent 跟技能不同：模型字段各家写法不一样，同一份正文必须按宿主换壳。壳由
# agents/assemble.py 从 body.md + agent.json 装配到 agents/<名>/out/，这里只把成品
# 软链到各宿主的 agent 目录。软链仍指回仓库：改了 body.md 跑一次装配（或本脚本），
# 宿主下一次调用就是新的。
#
# hook 层（hooks/）跟前两者又不同：Claude、Codex、Cursor、Grok 读的是各自的 hook 配置文件，
# 本脚本把 hooks/mmw-hooks.json 里的三条合并进去（保留别人的条目，只摘自己的），pi 装的是
# 扩展目录软链，Grok 另装一份规则文件做开场降级。每个宿主根留一份 .mmw-hooks 清单记录本脚本
# 动过哪些文件与链接。--check 顺带跑承重句校验（hooks/check-invariants.js）。

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/upstream/skills"
SELF_SRC="$ROOT/skills"
VENDOR_SRC="$ROOT/vendor"
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
wanted_dirs=()
wanted_names=()
while IFS= read -r line; do
  line="${line%%#*}"
  line="$(echo "$line" | tr -d '[:space:]')"
  [ -n "$line" ] || continue
  case "$line" in
    self/*) dir="$SELF_SRC/${line#self/}" ;;
    vendor/*) dir="$VENDOR_SRC/${line#vendor/}" ;;
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
        "$SKILLS_SRC"/* | "$SELF_SRC"/* | "$VENDOR_SRC"/*) rm "$stale"; echo "摘掉  $stale" ;;
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
      if [ -L "$link" ] && { [[ "$(readlink "$link")" == "$SKILLS_SRC"/* ]] || [[ "$(readlink "$link")" == "$SELF_SRC"/* ]] || [[ "$(readlink "$link")" == "$VENDOR_SRC"/* ]]; }; then
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

# ---------------- hook 层 ----------------

HOOKS_SRC="$ROOT/hooks"
HOOK_MANIFEST_NAME=".mmw-hooks"

if [ -d "$HOOKS_SRC" ]; then
  command -v node >/dev/null 2>&1 || die "hook 层要 node（三个注入脚本与承重句校验都是 Node）"
  CODEX_DIR="${CODEX_HOME:-$HOME_DIR/.codex}"
  PI_DIR="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}"

  # 一行一个安装点：宿主根|种类|目标|格式或来源。
  # json：把三条 hook 合并进该文件（格式给 hooks-config.py）；link：软链到本仓库的一个路径。
  # Grok 两行：hooks/ 下一份自己的 hook 文件（它对 Claude/Cursor 配置的兼容扫描本机已关），
  # rules/ 下一份规则文件——它的开场事件是被动的，纪律只能走常驻规则。
  hook_dests=(
    "$HOME_DIR/.claude|json|$HOME_DIR/.claude/settings.json|claude"
    "$CODEX_DIR|json|$CODEX_DIR/hooks.json|codex"
    "$HOME_DIR/.cursor|json|$HOME_DIR/.cursor/hooks.json|cursor"
    "$HOME_DIR/.grok|json|$HOME_DIR/.grok/hooks/mmw-discipline.json|grok"
    "$HOME_DIR/.grok|link|$HOME_DIR/.grok/rules/mmw-discipline.md|$HOOKS_SRC/discipline/worker.md"
    "$PI_DIR|link|$PI_DIR/extensions/mmw-discipline|$HOOKS_SRC/pi-extension"
  )

  # 装前按清单清理退役条目：上次记录了、这次安装点里没有的。json 只摘本仓库的条目，
  # link 只摘指回本仓库 hooks/ 的软链。
  if [ "$mode" != check ]; then
    for row in "${hook_dests[@]}"; do
      IFS='|' read -r host_home _ _ _ <<<"$row"
      manifest="$host_home/$HOOK_MANIFEST_NAME"
      [ -f "$manifest" ] || continue
      while IFS= read -r old; do
        [ -n "$old" ] || continue
        printf '%s\n' "${hook_dests[@]}" | cut -d'|' -f2,3 | grep -qxF "$old" && continue
        kind="${old%%|*}"
        target="${old#*|}"
        case "$kind" in
          json) python3 "$HOOKS_SRC/hooks-config.py" strip "$target" "$HOOKS_SRC" ;;
          link)
            [ -L "$target" ] || continue
            case "$(readlink "$target")" in
              "$HOOKS_SRC"/*) rm "$target"; echo "摘掉  $target" ;;
            esac ;;
        esac
      done < "$manifest"
      : > "$manifest"
    done
  fi

  hooks_installed=0
  for row in "${hook_dests[@]}"; do
    IFS='|' read -r host_home kind target spec <<<"$row"
    [ -d "$host_home" ] || continue
    manifest="$host_home/$HOOK_MANIFEST_NAME"

    if [ "$mode" = check ]; then
      case "$kind" in
        json) python3 "$HOOKS_SRC/hooks-config.py" check "$target" "$spec" "$HOOKS_SRC" "$spec" || rc=1 ;;
        link)
          if [ ! -L "$target" ] || [ "$(readlink "$target")" != "$spec" ]; then
            echo "缺    $target" >&2
            rc=1
          fi ;;
      esac
      continue
    fi

    case "$kind" in
      json)
        if python3 "$HOOKS_SRC/hooks-config.py" merge "$target" "$spec" "$HOOKS_SRC" "$spec" >/dev/null; then
          echo "json|$target" >> "$manifest"
          hooks_installed=$((hooks_installed + 1))
        else
          rc=1
        fi ;;
      link)
        if [ -e "$target" ] || [ -L "$target" ]; then
          if [ -L "$target" ] && [[ "$(readlink "$target")" == "$HOOKS_SRC"/* ]]; then
            :
          else
            echo "冲突  $target 已存在且不是本仓库装的，跳过" >&2
            rc=1
            continue
          fi
        fi
        mkdir -p "$(dirname "$target")"
        ln -sfn "$spec" "$target"
        echo "link|$target" >> "$manifest"
        hooks_installed=$((hooks_installed + 1)) ;;
    esac
  done
  [ "$mode" = check ] || echo "已装  $hooks_installed 处 hook -> 各宿主的 .mmw-hooks 清单"

  # 承重句：清单里的短语逐字存在于权威位置。只在 --check 跑，装的时候不拦。
  if [ "$mode" = check ]; then
    node "$HOOKS_SRC/check-invariants.js" || rc=1
  fi
fi

[ "$installed_hosts" -gt 0 ] || die "一个宿主都没找到，什么都没装"

if [ "$mode" = check ]; then
  [ "$rc" -eq 0 ] && echo "齐了：$installed_hosts 个宿主 × ${#wanted_names[@]} 个技能"
else
  echo
  echo "源目录：${SKILLS_SRC}（上游）、${SELF_SRC}（自研）、${VENDOR_SRC}（第三方）"
  echo "改技能直接改源目录里的文件，宿主下次调用就是新的。"
fi

exit "$rc"
