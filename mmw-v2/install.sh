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

# ---------------- hook ----------------

# 技能和 subagent 是宿主去读的，hook 是宿主来调的，所以它要在每个宿主的配置里各有一条。
# 四家写 JSON，pi 写一个扩展文件；五处都指向通用位置 ~/.agents/skills 下的 hook.py——
# 那已经是指回仓库的软链，所以改 hook.py 不用重装。
#
# 合并而不是覆盖：这五处 Herdr 也各装了自己的东西。只认 command 里带 hook.py 的那一条，
# 认得出就换成新的，认不出就在后面添一条，别人的条目一个字不动。

HOOK_SRC="$SELF_SRC/verify-ticket/scripts/hook.py"

if [ -f "$HOOK_SRC" ]; then
  MMW_MODE="$mode" \
  MMW_HOOK="$NEUTRAL_DIR/verify-ticket/scripts/hook.py" \
  MMW_HOME="$HOME_DIR" \
  MMW_CODEX="${CODEX_HOME:-$HOME_DIR/.codex}" \
  MMW_PI="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}" \
  python3 - <<'PY' || rc=1
import json
import os
import sys
from pathlib import Path

mode = os.environ["MMW_MODE"]
hook = os.environ["MMW_HOOK"]
home = Path(os.environ["MMW_HOME"])
codex_home = Path(os.environ["MMW_CODEX"])
pi_home = Path(os.environ["MMW_PI"])

# 这道门只比对命令文本，不跑任何东西，所以给它宿主默认之下的一个短超时就够。
TIMEOUT = 10

PI_EXTENSION = """// installed by mmw-v2/install.sh
// 这道门在 pi 这一侧的形状：pi 不读 JSON 配置，所以由这个扩展在 tool_call 上调
// 同一个 hook.py，再把它的答案翻回 pi 的说法。
// @ts-nocheck

import { spawnSync } from "node:child_process";

const HOOK = "%(hook)s";

export default function (pi) {
  // 没有派发脚本塞的这个标记就没有这道门，不必为每条命令付一个进程。
  if (!process.env.MMW_TICKET) return;

  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return;
    const run = spawnSync("python3", [HOOK, "pretool", "pi"], {
      input: JSON.stringify({ tool_name: "bash", tool_input: event.input }),
      encoding: "utf8",
      timeout: %(timeout)d000,
    });
    const answer = (run.stdout || "").trim();
    if (!answer) return;
    try {
      const parsed = JSON.parse(answer);
      if (parsed.block) return { block: true, reason: parsed.reason };
    } catch {}
  });
}
""" % {"hook": hook, "timeout": TIMEOUT}

COMMAND = f"python3 '{hook}' pretool "


def load(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    scratch.replace(path)


def ours(handler):
    return isinstance(handler, dict) and "hook.py" in str(handler.get("command", ""))


def grouped(path, host, event, matcher):
    """Claude Code、Codex、Grok Build 都把处理器按 matcher 分组。"""

    def install():
        data = load(path)
        hooks = data.setdefault("hooks", {})
        handler = {"type": "command", "command": COMMAND + host, "timeout": TIMEOUT}
        for group in hooks.setdefault(event, []):
            inner = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(inner, list):
                continue
            for index, existing in enumerate(inner):
                if ours(existing):
                    inner[index] = handler
                    group["matcher"] = matcher
                    save(path, data)
                    return
        hooks[event].append({"matcher": matcher, "hooks": [handler]})
        save(path, data)

    def installed():
        hooks = load(path).get("hooks") or {}
        for group in hooks.get(event) or []:
            inner = group.get("hooks") if isinstance(group, dict) else None
            for existing in inner or []:
                if isinstance(existing, dict) and existing.get("command") == COMMAND + host:
                    return True
        return False

    return install, installed


def cursor(path, event):
    """Cursor 把处理器直接列在事件下面。"""

    def install():
        data = load(path)
        data.setdefault("version", 1)
        entries = data.setdefault("hooks", {}).setdefault(event, [])
        handler = {"command": COMMAND + "cursor", "timeout": TIMEOUT}
        for index, existing in enumerate(entries):
            if ours(existing):
                entries[index] = handler
                break
        else:
            entries.append(handler)
        save(path, data)

    def installed():
        entries = (load(path).get("hooks") or {}).get(event) or []
        return any(isinstance(e, dict) and e.get("command") == COMMAND + "cursor"
                   for e in entries)

    return install, installed


def extension(path):
    def install():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PI_EXTENSION, encoding="utf-8")

    def installed():
        try:
            return hook in path.read_text(encoding="utf-8")
        except Exception:
            return False

    return install, installed


# 一行一个安装点：宿主根、配置文件、事件名（给人看）、装与查两个动作。
points = [
    (home / ".claude", home / ".claude/settings.json", "PreToolUse",
     grouped(home / ".claude/settings.json", "claude", "PreToolUse", "Bash")),
    (home / ".grok", home / ".grok/hooks/mmw-verify-ticket.json", "PreToolUse",
     grouped(home / ".grok/hooks/mmw-verify-ticket.json", "grok", "PreToolUse", "Bash")),
    (codex_home, codex_home / "hooks.json", "PreToolUse",
     grouped(codex_home / "hooks.json", "codex", "PreToolUse", "Bash")),
    (home / ".cursor", home / ".cursor/hooks.json", "beforeShellExecution",
     cursor(home / ".cursor/hooks.json", "beforeShellExecution")),
    (pi_home, pi_home / "extensions/mmw-verify-ticket.ts", "tool_call",
     extension(pi_home / "extensions/mmw-verify-ticket.ts")),
]

failed = False
count = 0
for host_home, path, event, (install, installed) in points:
    if not host_home.is_dir():
        print(f"跳过  {host_home}（宿主没装）")
        continue
    if mode == "check":
        if installed():
            print(f"hook  {path}  {event}")
            count += 1
        else:
            sys.stderr.write(f"缺    {path}  {event}\n")
            failed = True
        continue
    install()
    count += 1

if mode != "check":
    print(f"已装  {count} 处 hook -> 五个宿主")
    if codex_home.is_dir():
        # 2026-08-29 实测：写进 hooks.json 还不够。Codex 开场先弹「N hooks need review」，
        # 人按一次 t 之前这道门是 Installed 而 Active 为 0。按下去记的是这条 hook 的哈希
        # （config.toml 的 [hooks.state]），所以 hook.py 的路径一变要再按一次。
        print("注意  codex 里这道门要人按一次 t 才生效：下次开 codex 会看到"
              "「hooks need review」，按 t 信任")
sys.exit(1 if failed else 0)
PY
fi

if [ "$mode" = check ]; then
  [ "$rc" -eq 0 ] && echo "齐了：${installed_dests} 处 × ${#wanted_names[@]} 个技能"
else
  echo
  echo "源目录：${SKILLS_SRC}（上游）、${SELF_SRC}（自研）、${DD_SRC}（diagram-design 上游）"
  echo "改技能直接改源目录里的文件，宿主下次调用就是新的。"
fi

exit "$rc"
