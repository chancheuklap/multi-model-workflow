#!/usr/bin/env bash
# 把四样东西装到本机，让每个 host 都读得到：
#
#   技能              skills.txt 列出的，软链进 ~/.agents/skills 与 ~/.claude/skills
#   subagent          agents/<名>/out/ 的 assembled subagent file，软链进各 host 的 agent 目录
#   hook              verify-ticket 的 hook.py pretool（五个 host）与 Claude Code 的
#                     rule-at-moment.py（三个事件），写进各 host 自己的配置
#   agent detection rule   dispatch 技能带的覆盖（有才装），拷进 ~/.config/herdr/agent-detection/
#
# 技能有三个来源：mattpocock/skills 的在 upstream/skills/，我们自己写的在 skills/（skills.txt
# 里前缀 self/），cathrynlavery/diagram-design 的在 upstream-diagram-design/skills/（前缀 dd/）。三者
# 装法完全一样。
#
# 软链不是拷贝：host 读的就是仓库里那个文件。在用技能的当中直接改 source directory 下的
# SKILL.md，下一次调用就是新的，不用重装。（只有 frontmatter 的 description 是 host 启动时扫的，
# 改它要重开会话。）
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西或有 stale link 回 1
#
# 两种模式在 hook 都齐了的时候都打印 HOOKS-INSTALLED。
#
# 技能装两处，不按 host 分。~/.agents/skills 不属于任何一个 host，Codex、Cursor、Grok、Pi
# 都原生扫它；Claude Code 不扫，只认 ~/.claude/skills，所以那一处再装一份。两处装的是
# 同一批软链，都直接指向 source directory，彼此不串。
#
# 每个 host 都读 SKILL.md 的 disable-model-invocation，Codex 另读技能目录里的
# agents/openai.yaml。两者都在技能目录内，软链一并带过去，所以技能安装没有任何按 host
# 分支的逻辑。
#
# subagent 跟技能不同：model 字段各家写法不一样，同一份正文必须按 host 换 per-host shell。
# per-host shell 由 agents/assemble.py 从 body.md + agent.json assemble 进 agents/<名>/out/，
# 这里只把 assembled subagent file 软链到各 host 的 agent 目录。软链仍指回仓库：改了 body.md
# 跑一次 assemble.py（或本脚本），host 下一次调用就是新的。
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/upstream/skills"
SELF_SRC="$ROOT/skills"
DD_SRC="$ROOT/upstream-diagram-design/skills"
LIST="$ROOT/skills.txt"

# 一条软链是不是本仓库装的：目标落在本仓库任一 checkout（主 checkout 或某个 worktree）
# 的对应 source directory 里，按路径段认。ADR 0006 说的「指回本仓库」是仓库，不是某一个
# checkout：从哪个 checkout 运行本脚本，哪个 checkout 的 source directory 就接管这批软链。
ours_skill_target() {
  case "$1" in
    */mmw-v2/upstream/skills/* | */mmw-v2/skills/* | */mmw-v2/upstream-diagram-design/skills/*) return 0 ;;
  esac
  return 1
}

ours_agent_target() {
  case "$1" in
    */mmw-v2/agents/*) return 0 ;;
  esac
  return 1
}

# 一个安装目录里所有指回本仓库的软链。别人放在同一个目录里的东西不在其中。
repo_links() {
  local dest="$1" pred="$2" link
  [ -d "$dest" ] || return 0
  for link in "$dest"/*; do
    [ -L "$link" ] || continue
    if "$pred" "$(readlink "$link")"; then printf '%s\n' "$link"; fi
  done
  return 0
}

# 其中这次不该有的：指回本仓库，名字却不在这一批要装的里面。
# 扫目录而不是读「上一次装了什么」的记录：记录会被下一次安装重写，被漏掉的那条
# 就再也没人认领。ui-qa 从 skills.txt 拿掉之后八处软链留了一整天，就是这么来的。
stale_links() {
  local dest="$1" pred="$2"; shift 2
  local keep=("$@") link name
  while IFS= read -r link; do
    [ -n "$link" ] || continue
    name="$(basename "$link")"
    if [ "${#keep[@]}" -gt 0 ] && printf '%s\n' "${keep[@]}" | grep -qx "$name"; then
      continue
    fi
    printf '%s\n' "$link"
  done < <(repo_links "$dest" "$pred")
  return 0
}

# MMW_V2_HOME 只给测试用：把安装位置整体搬到一个一次性目录下，不碰真的家目录。
HOME_DIR="${MMW_V2_HOME:-$HOME}"

# 不属于任何一个 host，所以无条件建。
NEUTRAL_DIR="$HOME_DIR/.agents/skills"
# Claude Code 专用。它不扫 ~/.agents/skills。host 没装就跳过。
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

[ -f "$LIST" ] || die "缺 skills.txt：$LIST"
[ -d "$SKILLS_SRC" ] || die "缺 upstream 技能目录：$SKILLS_SRC"

# 读 skills.txt。顺便当场验证每个都真的存在——写错要在动 host 之前就停。
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
  [ -f "$dir/SKILL.md" ] || die "skills.txt 里的技能不存在：$line"
  wanted_dirs+=("$dir")
  wanted_names+=("$(basename "$line")")
done < "$LIST"

[ "${#wanted_names[@]}" -gt 0 ] || die "skills.txt 是空的：$LIST"

# 名字撞车要在装之前发现：两个技能软链成同一个名字，后装的会盖掉先装的。
dupes="$(printf '%s\n' "${wanted_names[@]}" | sort | uniq -d)"
[ -z "$dupes" ] || die "skills.txt 里有重名技能：$(echo "$dupes" | tr '\n' ' ')"

rc=0
installed_dests=0
# hook 两段各自的成败。两段都跑过且都齐了才打印 HOOKS-INSTALLED。
hooks_ran=0
hooks_rc=0

for dest in "${HOST_DIRS[@]}"; do
  host_home="$(dirname "$dest")"
  if [ "$dest" != "$NEUTRAL_DIR" ] && [ ! -d "$host_home" ]; then
    echo "跳过  ${dest}（host 没装）"
    continue
  fi
  installed_dests=$((installed_dests + 1))

  if [ "$mode" = check ]; then
    for i in "${!wanted_names[@]}"; do
      link="$dest/${wanted_names[$i]}"
      want="${wanted_dirs[$i]}"
      if [ ! -L "$link" ] || [ "$(readlink "$link")" != "$want" ]; then
        echo "缺    $link" >&2
        rc=1
      fi
    done
    while IFS= read -r stale; do
      [ -n "$stale" ] || continue
      echo "残留  $stale 指回本仓库，skills.txt 里却没有它，跑一次 install.sh 摘掉" >&2
      rc=1
    done < <(stale_links "$dest" ours_skill_target "${wanted_names[@]}")
    continue
  fi

  mkdir -p "$dest"

  # 先清理：这个目录里指回本仓库、skills.txt 里却没有的软链，摘掉。
  # 目标不指回本仓库的一律不碰，宁可留着也不误删。
  while IFS= read -r stale; do
    [ -n "$stale" ] || continue
    rm "$stale"; echo "摘掉  $stale"
  done < <(stale_links "$dest" ours_skill_target "${wanted_names[@]}")

  # .mmw-skills 没有读者：装了什么由扫目录认，见到这份记账文件就删。
  [ -f "$dest/.mmw-skills" ] && rm "$dest/.mmw-skills"

  linked=()
  for i in "${!wanted_names[@]}"; do
    name="${wanted_names[$i]}"
    link="$dest/$name"
    want="${wanted_dirs[$i]}"

    if [ -e "$link" ] || [ -L "$link" ]; then
      # 已经是我们指向本仓库的软链，直接重指（换 checkout 时也走这条）。
      if [ -L "$link" ] && ours_skill_target "$(readlink "$link")"; then
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

  echo "已装  ${#linked[@]} 个技能 -> $dest"
done

# ---------------- retired 的技能位置 ----------------

# 下面四处是 retired 的安装位置：主循环不装它们，各自的 host 却仍在扫。留在那里的软链是
# 上一轮 skills.txt 的旧版本，跟 ~/.agents/skills 那份撞名；实测里 Grok 取 ~/.grok/skills
# 那份，把 ~/.agents/skills 的盖住，不报错也不提示。所以每次安装都摘一遍。
RETIRED_DIRS=(
  "${CODEX_HOME:-$HOME_DIR/.codex}/skills"
  "${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}/skills"
  "$HOME_DIR/.cursor/skills"
  "$HOME_DIR/.grok/skills"
)

for dest in "${RETIRED_DIRS[@]}"; do
  [ -d "$dest" ] || continue

  # 这四处整个 retired，所以指回本仓库的软链一条不留。别人放在同一个目录里的东西一律不碰。
  retired=()
  while IFS= read -r stale; do
    [ -n "$stale" ] || continue
    retired+=("$stale")
  done < <(repo_links "$dest" ours_skill_target)

  if [ "$mode" = check ]; then
    if [ "${#retired[@]}" -gt 0 ]; then
      echo "残留  ${dest} 是 retired 的位置，还有 ${#retired[@]} 条技能软链指回本仓库，跑一次 install.sh 摘掉" >&2
      rc=1
    fi
    continue
  fi

  [ -f "$dest/.mmw-skills" ] && rm "$dest/.mmw-skills"
  [ "${#retired[@]}" -gt 0 ] || continue
  for stale in "${retired[@]}"; do
    rm "$stale"
  done
  echo "退役  摘掉 ${#retired[@]} 个技能 <- ${dest}"
done

# ---------------- subagent ----------------

AGENTS_SRC="$ROOT/agents"

if [ -d "$AGENTS_SRC" ]; then
  # assembled subagent file 必须与源一致：装的时候先 assemble，查的时候只验不写。
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

  # 一行一个安装点：host 根|目标目录|assembled subagent file 名|落地后缀。
  # grok 一家两处：agents/ 放定义与 model，roles/ 放只读能力与 effort。
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

    if [ "$mode" = check ]; then
      for name in "${agent_names[@]}"; do
        link="$dest/$name$suffix"
        want="$AGENTS_SRC/$name/out/$src_name"
        if [ ! -L "$link" ] || [ "$(readlink "$link")" != "$want" ]; then
          echo "缺    $link" >&2
          rc=1
        fi
      done
      while IFS= read -r stale; do
        [ -n "$stale" ] || continue
        echo "残留  $stale 指回本仓库，agents/ 下却没有它，跑一次 install.sh 摘掉" >&2
        rc=1
      done < <(stale_links "$dest" ours_agent_target "${agent_names[@]/%/$suffix}")
      continue
    fi

    mkdir -p "$dest"

    # 清理：这个目录里指回本仓库 agents/、这次却不装的软链，摘掉。
    while IFS= read -r stale; do
      [ -n "$stale" ] || continue
      rm "$stale"; echo "摘掉  $stale"
    done < <(stale_links "$dest" ours_agent_target "${agent_names[@]/%/$suffix}")

    [ -f "$dest/.mmw-agents" ] && rm "$dest/.mmw-agents"

    linked=()
    for name in "${agent_names[@]}"; do
      link="$dest/$name$suffix"
      want="$AGENTS_SRC/$name/out/$src_name"
      if [ -e "$link" ] || [ -L "$link" ]; then
        if [ -L "$link" ] && ours_agent_target "$(readlink "$link")"; then
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

    echo "已装  ${#linked[@]} 个 agent -> $dest"
  done
fi

# ---------------- Herdr agent detection rule ----------------

# Herdr 认一个 pane 里的 agent 是 idle 还是 blocked，靠的是每家一份 agent detection rule。
# 某家规则不准时，修法是放一份本地覆盖进这个目录——本地覆盖优先于远端，改完要让
# 服务端重读一遍才生效。dispatch 技能带了覆盖才有东西可装，目录不在就整段跳过。

DETECT_SRC="$SELF_SRC/dispatch/herdr/agent-detection"
DETECT_DEST="$HOME_DIR/.config/herdr/agent-detection"

if [ -d "$DETECT_SRC" ]; then
  for src in "$DETECT_SRC"/*.toml; do
    [ -f "$src" ] || continue
    name="$(basename "$src")"
    dest="$DETECT_DEST/$name"

    if [ "$mode" = check ]; then
      if [ ! -f "$dest" ] || ! cmp -s "$src" "$dest"; then
        echo "缺    ${dest}（与 ${src} 不一致）" >&2
        rc=1
      fi
      continue
    fi

    # 这里是拷贝不是软链：Herdr 自己会往这个目录里写远端拉下来的那一份，
    # 软链进去等于把仓库交给它写。
    mkdir -p "$DETECT_DEST"
    cp "$src" "$dest"
    echo "已装  $dest"
  done

  if [ "$mode" != check ] && [ "$HOME_DIR" = "$HOME" ] && command -v herdr >/dev/null 2>&1; then
    herdr server reload-agent-manifests >/dev/null 2>&1 \
      && echo "已重读 Herdr agent detection rule" \
      || echo "注意  Herdr 没在跑，agent detection rule 下次起服务时才生效"
  fi
fi

# ---------------- hook ----------------

# 技能和 subagent 是 host 去读的，hook 是 host 来调的，所以它要在每个 host 的配置里各有一条。
# 四家写 JSON，pi 写一个扩展文件；五处都指向 ~/.agents/skills 下的 hook.py——
# 那已经是指回仓库的软链，所以改 hook.py 不用重装。
#
# 合并而不是覆盖：这五处 Herdr 也各装了自己的东西。只认 command 里带 hook.py 的那一条，
# 认得出就换成新的，认不出就在后面添一条，别人的条目一个字不动。

HOOK_SRC="$SELF_SRC/verify-ticket/scripts/hook.py"

if [ -f "$HOOK_SRC" ]; then
  hooks_ran=1
  MMW_MODE="$mode" \
  MMW_HOOK="$NEUTRAL_DIR/verify-ticket/scripts/hook.py" \
  MMW_HOME="$HOME_DIR" \
  MMW_CODEX="${CODEX_HOME:-$HOME_DIR/.codex}" \
  MMW_PI="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}" \
  python3 - <<'PY' || { rc=1; hooks_rc=1; }
import json
import os
import sys
from pathlib import Path

mode = os.environ["MMW_MODE"]
hook = os.environ["MMW_HOOK"]
home = Path(os.environ["MMW_HOME"])
codex_home = Path(os.environ["MMW_CODEX"])
pi_home = Path(os.environ["MMW_PI"])

# hook.py 只比对命令文本，不跑任何东西，所以给它 host 默认之下的一个短超时就够。
TIMEOUT = 10

PI_EXTENSION = """// installed by mmw-v2/install.sh
// hook.py 在 pi 这一侧的形状：pi 不读 JSON 配置，所以由这个扩展在 tool_call 上调
// 同一个 hook.py，再把它的答案翻回 pi 的说法。
// @ts-nocheck

import { spawnSync } from "node:child_process";

const HOOK = "%(hook)s";

export default function (pi) {
  // 没有 dispatch.sh 塞的 MMW_TICKET 就不必调 hook.py，也就不必为每条命令付一个进程。
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


# 一行一个安装点：host 根、配置文件、事件名（只出现在输出里）、装与查两个动作。
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
        print(f"跳过  {host_home}（host 没装）")
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
    # 写完当场回读：认得出自己刚写的那一条，这个安装点才算数。
    if not installed():
        sys.stderr.write(f"缺    {path}  {event}\n")
        failed = True
        continue
    count += 1

if mode != "check":
    print(f"已装  {count} 处 hook -> {count} 个 host")
    if codex_home.is_dir():
        # 2026-08-29 实测：写进 hooks.json 还不够。Codex 开场先弹「N hooks need review」，
        # 按一次 t 之前这条 hook 是 Installed 而 Active 为 0。按下去记的是这条 hook 的哈希
        # （config.toml 的 [hooks.state]），所以 hook.py 的路径一变要再按一次。
        print("注意  codex 里这条 hook 要按一次 t 才生效：下次开 codex 会看到"
              "「hooks need review」，按 t 信任")
sys.exit(1 if failed else 0)
PY
fi

# ---------------- Claude Code 的 rule-at-moment.py ----------------

# hooks/rule-at-moment.py 只给 Claude Code 用：在每次读、写、派子代理、结果被 host 截断
# 这几个时刻，把 ~/.claude/CLAUDE.md 里对应的那一条原文送到模型眼前。软链放在
# ~/.claude/hooks/（Herdr 的几个 hook 也在那），settings.json 里三条都指向它；改脚本不用
# 重装。合并法与上面一样：只认 command 里带脚本名的条目。
#
#   install_claude_hook <源脚本> <软链> '<事件与 matcher 的 JSON 列表>'

install_claude_hook() {
  local src="$1" link="$2" wanted="$3"
  [ -f "$src" ] && [ -d "$HOME_DIR/.claude" ] || return 0
  hooks_ran=1
  if [ "$mode" = check ]; then
    if [ ! -L "$link" ] || [ "$(readlink "$link")" != "$src" ]; then
      echo "缺    $link" >&2
      rc=1
      hooks_rc=1
    fi
  else
    mkdir -p "$(dirname "$link")"
    if [ -e "$link" ] && [ ! -L "$link" ]; then
      echo "冲突  $link 已存在且不是软链，跳过" >&2
      rc=1
      hooks_rc=1
    else
      ln -sfn "$src" "$link"
      echo "已装  $link"
    fi
  fi

  MMW_MODE="$mode" \
  MMW_SETTINGS="$HOME_DIR/.claude/settings.json" \
  MMW_HOOK_LINK="$link" \
  MMW_WANTED="$wanted" \
  python3 - <<'PY' || { rc=1; hooks_rc=1; }
import json
import os
import sys
from pathlib import Path

mode = os.environ["MMW_MODE"]
path = Path(os.environ["MMW_SETTINGS"])
link = os.environ["MMW_HOOK_LINK"]
command = f"python3 '{link}'"
MARK = os.path.basename(link)
TIMEOUT = 10
wanted = [tuple(item) for item in json.loads(os.environ["MMW_WANTED"])]


def load():
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def save(data):
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    scratch.replace(path)


def ours(handler):
    return isinstance(handler, dict) and MARK in str(handler.get("command", ""))


def find(hooks, event):
    for group in hooks.get(event) or []:
        inner = group.get("hooks") if isinstance(group, dict) else None
        for existing in inner or []:
            if ours(existing):
                return group, existing
    return None, None


data = load()
hooks = data.setdefault("hooks", {})
failed = False
for event, matcher in wanted:
    group, existing = find(hooks, event)
    if mode == "check":
        ok = existing is not None and existing.get("command") == command \
            and (matcher is None or group.get("matcher") == matcher)
        if ok:
            print(f"hook  {path}  {event}  {MARK}")
        else:
            sys.stderr.write(f"缺    {path}  {event}  {MARK}\n")
            failed = True
        continue
    handler = {"type": "command", "command": command, "timeout": TIMEOUT}
    if group is not None:
        inner = group["hooks"]
        inner[inner.index(existing)] = handler
        if matcher is not None:
            group["matcher"] = matcher
        else:
            group.pop("matcher", None)
    else:
        entry = {"hooks": [handler]}
        if matcher is not None:
            entry["matcher"] = matcher
        hooks.setdefault(event, []).append(entry)
if mode != "check":
    save(data)
    # 写完当场回读：每个事件都在文件里认得出来，才算装上。
    written = load().get("hooks") or {}
    for event, matcher in wanted:
        group, existing = find(written, event)
        if existing is not None and existing.get("command") == command \
                and (matcher is None or group.get("matcher") == matcher):
            continue
        sys.stderr.write(f"缺    {path}  {event}  {MARK}\n")
        failed = True
    if not failed:
        print(f"已装  {len(wanted)} 条 {MARK} hook -> {path}")
sys.exit(1 if failed else 0)
PY
}

# PreToolUse 一条 matcher 管八个工具；其余两个事件不带 matcher。
install_claude_hook "$ROOT/hooks/rule-at-moment.py" "$HOME_DIR/.claude/hooks/rule-at-moment.py" \
  '[["PreToolUse", "Read|Grep|WebFetch|Bash|Write|Edit|NotebookEdit|Agent"], ["PostToolUse", null], ["PostToolUseFailure", null]]'

if [ "$hooks_ran" -eq 1 ] && [ "$hooks_rc" -eq 0 ]; then
  echo "HOOKS-INSTALLED"
fi

if [ "$mode" = check ]; then
  if [ "$rc" -eq 0 ]; then
    echo "齐了：技能 ${installed_dests} 处 × ${#wanted_names[@]} 个，subagent 与 hook 见上"
  fi
else
  echo
  echo "source directory：${SKILLS_SRC}（mattpocock/skills）、${SELF_SRC}（自研）、${DD_SRC}（cathrynlavery/diagram-design）"
  echo "改技能直接改 source directory 里的文件，host 下次调用就是新的。"
fi

exit "$rc"
