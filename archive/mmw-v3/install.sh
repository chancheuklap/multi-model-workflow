#!/usr/bin/env bash
# 把 MMW 装到本机，让每个 host 都读得到。十样东西，全部指向运行本脚本的这个 checkout 的 mmw-v3/：
#
#   技能              skills/ 下每个带 SKILL.md 的目录，软链进 ~/.agents/skills 与 ~/.claude/skills
#   hook              dispatch 的 tool-guard.py 与 turn-guard.py，写进各 host 自己的配置；mmw-mode 的
#                     mode-hook.py 挂在 Claude Code 与 Codex 的 SessionStart 上
#   提示词            prompt/shared.md：Claude Code 读软链，Codex、Grok 读 prompt/render.py 写出的
#                     AGENTS.md
#   launchd 任务      盯着 shared.md，改了就重写 Codex、Grok 的 AGENTS.md
#   task board        一个 com.mmw.board LaunchAgent，按 ~/.mmw/boards.json 为每个仓库守住本机服务
#   Paseo 侧配置      ~/.local/bin/paseo 软链；~/.paseo/config.json 里 grok/cursor 两条 provider、
#                     worktrees.root。不写 Agent profile。~/.mmw/models.json 缺席时写入默认值；
#                     已有 JSON 不覆盖，只给缺的角色补一行。
#   Orca 侧工作树     有 orca 时，安装把每个 setup 的 worktree-base-path 设为 .worktrees。没有 orca 则跳过。
#   Nowledge Mem 对象  strict 的 mmw-toolbox Space；mmw-worker、mmw-reviewer 两个 Identity，
#                     默认 Space 都是 mmw-toolbox。没有的才建。没有 nmem 时 --check 明说没查，但不因此失败。
#   Cursor 的 MCP     ~/.cursor/mcp.json 里 nowledge-mem 一条，内容问本机 nmem 要
#   shell 的 Space    ~/.zshrc 里加载 shell/nmem-space.zsh 的一段：终端进入一个仓库时，把 NMEM_SPACE
#                     设成这个仓库的 Nowledge Mem Space
#
# 装完把本 checkout 的 mmw-v3 目录记进 ~/.mmw/installed-root。
#
# 本机装的是哪一份，只由这一次显式的安装决定。每一样都指进运行本脚本的 checkout：hook 的命令
# 走 ~/.agents/skills 下的技能软链，看板和提示词的 launchd 任务写的是这个 checkout 的路径。所以
# 别的 checkout 里的代码怎么改、并进哪个分支，都碰不到正在运行的 host；装着的 checkout 移到新
# 的提交，host 下一次调用就是新的，看板自己重启。别的 checkout 跑 --check 只核对（见下面
# installed-root 一段），dispatch.sh check 也只跑 --check，把缺的报出来。
#
# 本仓库装过、这次不装的东西，install 摘掉，--check 报残留：指回 mmw-v2 的技能软链（skills/ 下
# 没有的那些）、~/.claude/rules/mmw-claude.md、Pi 的两个扩展文件与生成的 AGENTS.md、本仓库在
# host 配置里写过这次不装的 hook。mmw-v2 装过、这里同名再装的，原地换成指向本 checkout：所以
# 从 mmw-v2 换到这一份，就是在装着的 checkout 里跑一次本脚本。反过来，在同一个 checkout 里跑一次
# bash mmw-v2/install.sh 就退回 mmw-v2（ADR 0036）。
#
# 软链不是拷贝：host 读的就是仓库里那个文件。在用技能的当中直接改 mmw-v3/skills/ 下的
# SKILL.md，下一次调用就是新的，不用重装。（只有 frontmatter 的 description 是 host 启动时扫的，
# 改它要重开会话。）
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西或有 stale link 回 1。
#
# 两种模式在 hook 都齐了的时候都打印 HOOKS-INSTALLED。
#
# 技能装两处，不按 host 分。~/.agents/skills 不属于任何一个 host，Codex、Cursor、Grok
# 都原生扫它；Claude Code 不扫，只认 ~/.claude/skills，所以那一处再装一份。两处装的是
# 同一批软链，都直接指向 mmw-v3/skills/，彼此不串。
#
# 每个 host 都读 SKILL.md 的 disable-model-invocation，Codex 另读技能目录里的
# agents/openai.yaml。两者都在技能目录内，软链一并带过去，所以技能安装没有任何按 host
# 分支的逻辑。
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/skills"

# 一条软链是不是本仓库装的：目标落在本仓库任一 checkout（主 checkout 或某个 worktree）
# 的 mmw-v3/skills/ 里，或 mmw-v2 装技能用的三个目录里，按路径段认。ADR 0006 说的「指回本
# 仓库」是仓库，不是某一个 checkout：从哪个 checkout 运行本脚本，哪个 checkout 的 mmw-v3/skills/
# 就接管这批软链，mmw-v2 装的也一样接管。
ours_skill_target() {
  case "$1" in
    */mmw-v3/skills/* | */mmw-v2/upstream/skills/* | */mmw-v2/skills/* | */mmw-v2/upstream-diagram-design/skills/*) return 0 ;;
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
# 就再也没人认领。ui-qa 从技能清单拿掉之后八处软链留了一整天，就是这么来的。
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

# MMW_INSTALL_HOME 只给测试用：把安装位置整体搬到一个一次性目录下，不碰真的家目录。
HOME_DIR="${MMW_INSTALL_HOME:-$HOME}"

# 不属于任何一个 host，所以无条件建。
NEUTRAL_DIR="$HOME_DIR/.agents/skills"
# Claude Code 专用。它不扫 ~/.agents/skills。host 没装就跳过。
CLAUDE_DIR="$HOME_DIR/.claude/skills"

HOST_DIRS=(
  "$NEUTRAL_DIR"
  "$CLAUDE_DIR"
)

die() {
  echo "mmw-v3 install: $1" >&2
  exit "${2:-1}"
}

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) die "用法：install.sh [--check]" 2 ;;
esac

# 装过之后记下是从哪个 checkout 装的（它的 mmw-v3 目录；mmw-v2 装的记的是 mmw-v2 目录）。
# --check 从另一个 checkout 跑时，交给记下的那个目录自己的 install.sh 核对，只核对、不接管：一个冻结的 checkout 装给各 host 用，
# 改造这套工具箱的那一夜就在别的 checkout 上进行，advance 并进去多少都不会动到正在运行的
# host。核对用的是装着的那一份自己的脚本：拿这个 checkout 的核对逻辑去读另一个版本的
# 文件，两边的函数对不上时核对本身就会出错。
INSTALLED_ROOT_FILE="$HOME_DIR/.mmw/installed-root"
if [ "$mode" = check ] && [ -f "$INSTALLED_ROOT_FILE" ]; then
  installed_root="$(cat "$INSTALLED_ROOT_FILE")"
  if [ -n "$installed_root" ] && [ -d "$installed_root" ] && [ "$installed_root" != "$ROOT" ]; then
    echo "装自  ${installed_root}（本 checkout ${ROOT} 只核对，不接管）"
    [ -f "$installed_root/install.sh" ] || die "装着的 checkout 里没有 install.sh：$installed_root"
    exec bash "$installed_root/install.sh" --check
  fi
fi

[ -d "$SKILLS_SRC" ] || die "缺技能目录：$SKILLS_SRC"


# 装哪些技能：skills/ 下每个带 SKILL.md 的目录。
wanted_dirs=()
wanted_names=()
for skill_md in "$SKILLS_SRC"/*/SKILL.md; do
  [ -f "$skill_md" ] || continue
  wanted_dirs+=("$(dirname "$skill_md")")
  wanted_names+=("$(basename "$(dirname "$skill_md")")")
done
[ "${#wanted_names[@]}" -gt 0 ] || die "$SKILLS_SRC 下没有带 SKILL.md 的目录"

rc=0
installed_dests=0
# hook 一段的成败。跑过且齐了才打印 HOOKS-INSTALLED。
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
      echo "残留  $stale 指回本仓库，skills/ 下却没有它，跑一次 install.sh 摘掉" >&2
      rc=1
    done < <(stale_links "$dest" ours_skill_target "${wanted_names[@]}")
    continue
  fi

  mkdir -p "$dest"

  # 先清理：这个目录里指回本仓库、skills/ 下却没有的软链，摘掉。
  # 目标不指回本仓库的一律不碰，宁可留着也不误删。
  while IFS= read -r stale; do
    [ -n "$stale" ] || continue
    rm "$stale"; echo "摘掉  $stale"
  done < <(stale_links "$dest" ours_skill_target "${wanted_names[@]}")

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

# ---------------- hook ----------------

# 技能是 host 去读的，hook 是 host 来调的，所以它要在每个 host 的配置里各有一条。
# mmw-mode 的 mode-hook.py 挂在 claude 与 codex 的 SessionStart 上：会话所在的仓库有 .mmw/ 时，
# 让它先读 mmw-mode 的 SKILL.md。只这两家，因为只有这两家的 SessionStart 能往会话里加话；
# 读 ~/.claude/settings.json 的 Grok 被下面的环境变量守卫挡掉，Cursor 由脚本读它 payload 里的
# cursor_version 自己退出。另外三样：dispatch 的 tool-guard.py 的 pretool gate（四个 host）与 question gate（起 session
# 的三个 host），同一技能的 turn-guard.py 挂在四个 host 的回合结束事件上（claude、codex、grok
# 的 Stop，cursor 的 stop）。每一处都写进 host 的 JSON 配置，指向 ~/.agents/skills 下的脚本——那已经是指回仓库的软链，所以改脚本不用重装。
#
# Cursor 与 Grok 都读 ~/.claude/settings.json，Grok 还读 ~/.cursor/hooks.json，所以写给 claude
# 的每一条命令前面都带同一个环境变量守卫：GROK_AGENT 或 GROK_HOOK_EVENT 有值就退出——两个都判，
# Grok 0.2.73 只设前一个、1.0 只设后一个；GROK_SESSION_ID 不能判，Grok 把它传进每个子进程，
# 会一路带进 Grok 起的 Claude 会话，把那个会话自己的 hook 也关掉。Cursor 那一侧由脚本读它 payload
# 里的 cursor_version 分辨，不读环境变量（turn-guard.py 头部有全文）。
#
# 合并而不是覆盖：这几处别人也各装了自己的东西。只认 command 里带本脚本名与 gate 名的
# 那一条，认得出就换成新的，认不出就在后面添一条，别人的条目一个字不动。

HOOK_SRC="$SKILLS_SRC/dispatch/scripts/tool-guard.py"

if [ -f "$HOOK_SRC" ]; then
  hooks_ran=1
  MMW_MODE="$mode" \
  MMW_HOOK="$NEUTRAL_DIR/dispatch/scripts/tool-guard.py" \
  MMW_GUARD="$NEUTRAL_DIR/dispatch/scripts/turn-guard.py" \
  MMW_MODE_HOOK="$NEUTRAL_DIR/mmw-mode/scripts/mode-hook.py" \
  MMW_NEUTRAL="$NEUTRAL_DIR" \
  MMW_HOOK_HOME="$HOME_DIR" \
  MMW_CODEX="${CODEX_HOME:-$HOME_DIR/.codex}" \
  python3 - <<'PY' || { rc=1; hooks_rc=1; }
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

mode = os.environ["MMW_MODE"]
hook = os.environ["MMW_HOOK"]
neutral = os.environ["MMW_NEUTRAL"]
home = Path(os.environ["MMW_HOOK_HOME"])
codex_home = Path(os.environ["MMW_CODEX"])

# tool-guard.py 只比对命令文本，不跑任何东西，所以给它 host 默认之下的一个短超时就够。
TIMEOUT = 10

COMMAND = f"python3 '{hook}' pretool "
QUESTION = f"python3 '{hook}' question "

guard = os.environ["MMW_GUARD"]
# turn-guard.py 在回合结束时可能要拉起 watchdog 并等它最多 5 秒，再问 runner 一次 self，
# 所以给它比 tool-guard.py 长的超时。
GUARD_TIMEOUT = 30
STOP = f"python3 '{guard}' stop "
# 写给 claude 的每一条命令前面都带它（见本段开头）。
GROK_GUARD = '[ -z "${GROK_AGENT:-}${GROK_HOOK_EVENT:-}" ] || exit 0; exec '
# Cursor 自己的回合上限：turn-guard.py 只在 loop_count 为 0 时要一次 follow-up，这个数是
# 脚本失灵时 Cursor 那一侧仍然成立的外层边界。
CURSOR_LOOP_LIMIT = 3


def for_host(host, command):
    return GROK_GUARD + command + host if host == "claude" else command + host


# The tool each host calls to put a question on the screen: the matcher of its
# question gate. Only hosts that expose a supported question tool carry one.
QUESTION_TOOLS = {"claude": "AskUserQuestion", "grok": "ask_user_question",
                  "codex": "request_user_input"}


def load(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def backup_latest(path):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = path.with_name(path.name + ".bak-" + stamp)
    shutil.copy2(path, backup)
    for old in path.parent.glob(path.name + ".bak-*"):
        if old != backup and (old.is_file() or old.is_symlink()):
            old.unlink()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.is_file():
        old = path.read_text(encoding="utf-8")
        if old != text:
            backup_latest(path)
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(text, encoding="utf-8")
    scratch.replace(path)


def marker_of(command):
    """What identifies one of ours across paths: the script's basename and its gate."""
    head, _, tail = command.rpartition("' ")
    return os.path.basename(head.split("'")[-1]) + "' " + tail


def ours(handler, command):
    return isinstance(handler, dict) and marker_of(command) in str(handler.get("command", ""))


def grouped(path, event, matcher, command, timeout=TIMEOUT):
    """Claude Code、Codex、Grok Build 都把处理器按 matcher 分组。

    `command` 是完整的一条：脚本路径、gate 与 host。同一个文件里的同一个事件可以带两条我们
    的处理器（pretool 与 question），靠脚本名加 gate 名认出各自的那条。
    """

    def install():
        data = load(path)
        hooks = data.setdefault("hooks", {})
        handler = {"type": "command", "command": command, "timeout": timeout}
        for group in hooks.setdefault(event, []):
            inner = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(inner, list):
                continue
            for index, existing in enumerate(inner):
                if ours(existing, command):
                    inner[index] = handler
                    if matcher is None:
                        group.pop("matcher", None)
                    else:
                        group["matcher"] = matcher
                    save(path, data)
                    return
        entry = {"hooks": [handler]}
        if matcher is not None:
            entry["matcher"] = matcher
        hooks[event].append(entry)
        save(path, data)

    def installed():
        hooks = load(path).get("hooks") or {}
        for group in hooks.get(event) or []:
            inner = group.get("hooks") if isinstance(group, dict) else None
            for existing in inner or []:
                if isinstance(existing, dict) and existing.get("command") == command \
                        and (matcher is None or group.get("matcher") == matcher):
                    return True
        return False

    return install, installed


def cursor(path, event, command, timeout=TIMEOUT, extra=None):
    """Cursor 把处理器直接列在事件下面。`extra` 是这一条另带的字段（stop 的 loop_limit）。"""

    def install():
        data = load(path)
        data.setdefault("version", 1)
        entries = data.setdefault("hooks", {}).setdefault(event, [])
        handler = {"command": command, "timeout": timeout, **(extra or {})}
        for index, existing in enumerate(entries):
            if ours(existing, command):
                entries[index] = handler
                break
        else:
            entries.append(handler)
        save(path, data)

    def installed():
        entries = (load(path).get("hooks") or {}).get(event) or []
        return any(isinstance(e, dict) and e.get("command") == command
                   and all(e.get(k) == v for k, v in (extra or {}).items())
                   for e in entries)

    return install, installed


# ---- 本仓库装过、这次不再装的 hook ----
#
# 技能软链那一段靠扫目录认领本仓库的残留（stale_links）；hook 这一侧是同一个机制。
# 一条登记指着一个不再存在的脚本，host 每次触发那个事件都会调用失败，有的 host 因此
# 挡住每一次输入；所以本仓库写进 host 配置的处理器，这次不装的就摘掉，--check 报残留。
#
# 认领判据与软链那边同构：命令里的脚本落在 ~/.agents/skills 下，就是本仓库装的。别人
# （Herdr、Paseo、Nowledge Mem）的处理器指向自己的目录，一条都不碰。
#
# 扫哪几个文件是下面这份显式清单：「这次装什么」认不出本仓库曾写在哪个文件里，只有人手
# 记着。不再往某个文件写的时候，把它留在清单里。
MARK = f"'{neutral}/"

# 一行一处：文件、它的格式、整个文件是不是只有本仓库写。
# 只有本仓库写的那种，条目清空之后连文件一起删——grok 把 hooks/*.json 全部合并读入，
# 空壳留着不报错也不提示。
SWEPT = [
    (home / ".claude/settings.json", "grouped", False),
    (codex_home / "hooks.json", "grouped", False),
    (home / ".cursor/hooks.json", "cursor", False),
    (home / ".grok/hooks/mmw-verify-ticket.json", "grouped", True),
    (home / ".grok/hooks/mmw-turn-guard.json", "grouped", True),
]

# mmw-v2 给 Pi 写的两个扩展文件。v3 不装 Pi 的 hook；文件头带 installed by mmw- 的才是本仓库写的。
PI_HOME = Path(os.environ.get("PI_CODING_AGENT_DIR")
               or Path(os.environ.get("PI_HOME") or home / ".pi") / "agent")
RETIRED_PI = [PI_HOME / "extensions/mmw-verify-ticket.ts", PI_HOME / "extensions/mmw-turn-guard.ts"]


def sweep(path, fmt, keep):
    """这个文件里本仓库装的、keep 之外的处理器。返回 (摘掉了什么, 摘完的 data)。"""
    data = load(path)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return [], data
    dropped = []

    def survivors(handlers, event):
        left = []
        for handler in handlers:
            command = str(handler.get("command", "")) if isinstance(handler, dict) else ""
            if MARK in command and command not in keep:
                dropped.append((event, command))
            else:
                left.append(handler)
        return left

    for event in list(hooks):
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        if fmt == "cursor":
            left = survivors(entries, event)
        else:
            left = []
            for group in entries:
                inner = group.get("hooks") if isinstance(group, dict) else None
                if not isinstance(inner, list):
                    left.append(group)
                    continue
                kept = survivors(inner, event)
                # 组里本来就有别人的处理器就留着；清空了的组连壳一起去掉。
                if kept:
                    group["hooks"] = kept
                    left.append(group)
        if left:
            hooks[event] = left
        else:
            del hooks[event]
    return dropped, data


# 一行一个安装点：host 根、配置文件、事件名（只出现在输出里）、装与查两个动作。
# grok 把 hooks/*.json 全部合并读入，所以 tool-guard.py 独占一个文件；claude 与 codex 只有一份
# 配置，几条都写进去。
grouped_hosts = [
    ("claude", home / ".claude", home / ".claude/settings.json"),
    ("grok", home / ".grok", home / ".grok/hooks/mmw-verify-ticket.json"),
    ("codex", codex_home, codex_home / "hooks.json"),
]
points = []
# 这次装的每一条完整命令，按文件收着：sweep 摘的就是这个集合之外的。
keep = {}


def point(host_home, path, label, actions, command=None):
    points.append((host_home, path, label, actions))
    if command is not None:
        keep.setdefault(path, set()).add(command)


for host, host_home, path in grouped_hosts:
    point(host_home, path, "PreToolUse Bash",
          grouped(path, "PreToolUse", "Bash", for_host(host, COMMAND)), for_host(host, COMMAND))
    point(host_home, path, "PreToolUse " + QUESTION_TOOLS[host],
          grouped(path, "PreToolUse", QUESTION_TOOLS[host], for_host(host, QUESTION)),
          for_host(host, QUESTION))
point(home / ".cursor", home / ".cursor/hooks.json", "beforeShellExecution",
      cursor(home / ".cursor/hooks.json", "beforeShellExecution", COMMAND + "cursor"),
      COMMAND + "cursor")

# turn-guard.py 挂在主 agent 的回合结束事件上。grok 那一条独占一个文件，理由同上。
stop_hosts = [
    ("claude", home / ".claude", home / ".claude/settings.json"),
    ("grok", home / ".grok", home / ".grok/hooks/mmw-turn-guard.json"),
    ("codex", codex_home, codex_home / "hooks.json"),
]
for host, host_home, path in stop_hosts:
    point(host_home, path, "Stop",
          grouped(path, "Stop", None, for_host(host, STOP), GUARD_TIMEOUT), for_host(host, STOP))
point(home / ".cursor", home / ".cursor/hooks.json", "stop",
      cursor(home / ".cursor/hooks.json", "stop", STOP + "cursor", GUARD_TIMEOUT,
             {"loop_limit": CURSOR_LOOP_LIMIT}),
      STOP + "cursor")

# mode-hook.py 在 claude 与 codex 的 SessionStart 上，见本段开头。
MODE_HOOK = os.environ["MMW_MODE_HOOK"]
MODE_START = f"python3 '{MODE_HOOK}' session-start "
for host, host_home, path in (("claude", home / ".claude", home / ".claude/settings.json"),
                              ("codex", codex_home, codex_home / "hooks.json")):
    point(host_home, path, "SessionStart",
          grouped(path, "SessionStart", None, for_host(host, MODE_START)), for_host(host, MODE_START))

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

# 装完再扫：一条只是换了路径的注册，上面已经原地更新过，它的新命令就在 keep 里；
# 剩下认领得出、却没人再装的，才是上一代的残留。
for path, fmt, mmw_owned in SWEPT:
    if not path.exists():
        continue
    dropped, data = sweep(path, fmt, keep.get(path, set()))
    if not dropped:
        continue
    if mode == "check":
        for event, command in dropped:
            sys.stderr.write(f"残留  {path}  {event}  {command}"
                             f" 指向 ~/.agents/skills，这次却不装它，跑一次 install.sh 摘掉\n")
        failed = True
        continue
    if mmw_owned and not (data.get("hooks") or {}):
        path.unlink()
        print(f"摘掉  {path}（本仓库写的最后一条 hook 也不装了）")
    else:
        save(path, data)
        for event, command in dropped:
            print(f"摘掉  {path}  {event}  {command}")

for path in RETIRED_PI:
    try:
        if not path.read_text(encoding="utf-8").startswith("// installed by mmw-"):
            continue
    except OSError:
        continue
    if mode == "check":
        sys.stderr.write(f"残留  {path} 是本仓库给 Pi 写的扩展，这次不装，跑一次 install.sh 摘掉\n")
        failed = True
    else:
        path.unlink()
        print(f"摘掉  {path}")

# ---- codex 的 hook 信任 ----
#
# 2026-08-29 实测：写进 hooks.json 还不够。Codex 开场先弹「N hooks need review」，按一次 t
# 之前这条 hook 是 Installed 而 Active 为 0。按下去记的是 config.toml 里的一张表
# [hooks.state."<hooks.json 路径>:<事件>:<组号>:<处理器号>"]，trusted_hash 一行。这个哈希由
# codex-rs 的 hooks/src/engine/discovery.rs（hook_hash）与 config/src/fingerprint.rs
# （version_for_toml）算：规范化之后的 {event_name, matcher, hooks: [这一条处理器]} 按键排序、
# 紧凑 JSON 的 sha256。所以本段替本仓库写进 hooks.json 的那几条处理器照同一算法算出哈希，
# 写进这张表，不用再按 t；别的处理器一条不碰。2026-09-10 拿本机 ~/.codex/hooks.json 的 16 条
# 处理器核对过这个算法：14 条与 config.toml 已记的哈希一致，另 2 条是信任之后又改过的。
# Codex 换了算法，这里写的哈希就对不上，Codex 照旧弹「need review」，--check 不会知道。
CODEX_LABELS = {"PreToolUse": "pre_tool_use", "PermissionRequest": "permission_request",
                "PostToolUse": "post_tool_use", "PreCompact": "pre_compact",
                "PostCompact": "post_compact", "SessionStart": "session_start",
                "SessionEnd": "session_end", "UserPromptSubmit": "user_prompt_submit",
                "SubagentStart": "subagent_start", "SubagentStop": "subagent_stop",
                "Stop": "stop", "Interrupt": "interrupt"}
CODEX_CONTEXT_EVENTS = {"PreToolUse", "PostToolUse", "SessionStart", "UserPromptSubmit",
                        "SubagentStart"}


def codex_trust_hash(event, matcher, handler):
    import hashlib

    timeout = handler.get("timeout")
    if event in ("SessionEnd", "Interrupt"):
        timeout = max(1, min(timeout if timeout is not None else 1, 3))
    else:
        timeout = max(1, timeout if timeout is not None else 600)
    normal = {"type": "command", "command": handler["command"], "timeout": timeout,
              "async": bool(handler.get("async", False))}
    if handler.get("statusMessage") is not None:
        normal["statusMessage"] = handler["statusMessage"]
    limit = handler.get("additionalContextLimit")
    if event in CODEX_CONTEXT_EVENTS and limit is not None and limit != 2500:
        normal["additionalContextLimit"] = limit
    identity = {"event_name": CODEX_LABELS[event], "hooks": [normal]}
    if matcher is not None:
        identity["matcher"] = matcher
    text = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def codex_trust_wanted():
    """{hooks.state 表名: 哈希}，本仓库写进 codex hooks.json 的每一条处理器一行。"""
    path = codex_home / "hooks.json"
    ours_there = keep.get(path, set())
    wanted = {}
    for event, groups in (load(path).get("hooks") or {}).items():
        if event not in CODEX_LABELS or not isinstance(groups, list):
            continue
        for gi, group in enumerate(groups):
            for hi, handler in enumerate((group or {}).get("hooks") or []):
                if isinstance(handler, dict) and handler.get("command") in ours_there:
                    name = f"{path}:{CODEX_LABELS[event]}:{gi}:{hi}"
                    wanted[name] = codex_trust_hash(event, group.get("matcher"), handler)
    return wanted


def codex_trust_recorded():
    import tomllib

    try:
        data = tomllib.loads((codex_home / "config.toml").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as exc:
        sys.stderr.write(f"读不懂  {codex_home / 'config.toml'}：{exc}\n")
        return None
    state = (data.get("hooks") or {}).get("state") or {}
    return {k: (v or {}).get("trusted_hash") for k, v in state.items() if isinstance(v, dict)}


def toml_key(name):
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


def codex_trust_write(wanted):
    """把 wanted 里对不上的每一条写进 config.toml：表已在就换它的 trusted_hash 行，不在就追加。"""
    import re

    path = codex_home / "config.toml"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    recorded = codex_trust_recorded() or {}
    changed = False
    for name, digest in wanted.items():
        if recorded.get(name) == digest:
            continue
        header = f"[hooks.state.{toml_key(name)}]"
        line = f'trusted_hash = "{digest}"'
        at = text.find(header + "\n")
        if at >= 0:
            start = at + len(header) + 1
            nxt = re.search(r"^\[", text[start:], re.M)
            end = start + nxt.start() if nxt else len(text)
            body = re.sub(r"^trusted_hash\s*=.*$", line, text[start:end], flags=re.M)
            if line not in body:
                body = line + "\n" + body
            text = text[:start] + body + text[end:]
        else:
            text = text.rstrip("\n") + ("\n\n" if text.strip() else "") + header + "\n" + line + "\n"
        changed = True
    if changed:
        import tomllib

        # 写坏的 config.toml 会让 codex 起不来：写之前先读一遍自己要写的东西。
        try:
            tomllib.loads(text)
        except Exception as exc:
            sys.stderr.write(f"没写  {path}：改完读不回来（{exc}），原文件没动\n")
            return False
        if path.is_file():
            backup_latest(path)
        scratch = path.with_name(path.name + ".mmw-tmp")
        scratch.write_text(text, encoding="utf-8")
        scratch.replace(path)
    return changed


if codex_home.is_dir():
    wanted = codex_trust_wanted()
    if mode != "check" and wanted and codex_trust_recorded() is not None:
        codex_trust_write(wanted)
    recorded = codex_trust_recorded()
    for name, digest in wanted.items():
        if recorded is not None and recorded.get(name) == digest:
            print(f"信任  {codex_home / 'config.toml'}  {name}")
        else:
            sys.stderr.write(f"缺    {codex_home / 'config.toml'}  hooks.state {name} 的 trusted_hash"
                             f"（codex 会弹「hooks need review」）\n")
            failed = True

if mode != "check":
    print(f"已装  {count} 条 hook")
sys.exit(1 if failed else 0)
PY
fi

if [ "$hooks_ran" -eq 1 ] && [ "$hooks_rc" -eq 0 ]; then
  echo "HOOKS-INSTALLED"
fi

# ---------------- 提示词 ----------------

# 源在 prompt/shared.md，三家共用。Claude Code 认软链，所以 ~/.claude/CLAUDE.md 直接指 shared.md，
# 改源即生效。Codex、Grok 没有引入语法，只能由 render.py 把它写成各自的 AGENTS.md；生成物带
# 哈希，被人直接改过 render.py 就拒绝覆盖。launchd 任务监视 shared.md，改动即重写；Claude Code 那条
# 软链不需要它。MMW_INSTALL_HOME 之下（测试）不装 launchd。
#
# ~/.claude/rules/mmw-claude.md 是 mmw-v2 装的、只给 Claude Code 的那一份；v3 没有只给一家的提示词，
# 指回本仓库的这条软链摘掉。mmw-v2 给 Pi 生成的 AGENTS.md 也摘掉：v3 不装 Pi。

PROMPT_SRC="$ROOT/prompt"

# 一条软链该指哪里就指哪里；原位已有别的文件就是冲突。
link_prompt() {
  local link="$1" want="$2"
  if [ -L "$link" ]; then
    if [ "$(readlink "$link")" = "$want" ]; then return 0; fi
    case "$(readlink "$link")" in
      */mmw-v3/prompt/* | */mmw-v2/prompt/*) [ "$mode" = check ] || ln -sfn "$want" "$link"
        [ "$mode" != check ] || { echo "缺    $link 指向别的 checkout，跑一次 install.sh" >&2; return 1; }
        return 0 ;;
      *) echo "冲突  $link 是软链但不指回本仓库，跳过" >&2; return 1 ;;
    esac
  fi
  if [ -e "$link" ]; then
    echo "冲突  $link 已存在且不是软链；把它的内容搬进 $want 再删掉它" >&2
    return 1
  fi
  if [ "$mode" = check ]; then echo "缺    $link" >&2; return 1; fi
  mkdir -p "$(dirname "$link")"
  ln -sfn "$want" "$link"
}

# 一条本仓库装过、这次不装的提示词软链：指回本仓库就摘掉，别的不碰。
retire_prompt() {
  local link="$1"
  [ -L "$link" ] || return 0
  case "$(readlink "$link")" in
    */mmw-v3/prompt/* | */mmw-v2/prompt/*) ;;
    *) return 0 ;;
  esac
  if [ "$mode" = check ]; then
    echo "残留  $link 指回本仓库，这次却不装它，跑一次 install.sh 摘掉" >&2
    return 1
  fi
  rm "$link"; echo "摘掉  $link"
}

launch_agent() {
  local label="$1" plist="$2" want="$3" installed="$4" status=0
  if [ "$mode" = check ]; then
    if [ ! -f "$plist" ] || [ "$(cat "$plist")" != "$want" ]; then
      echo "缺    $plist 不存在或指向别的 checkout，跑一次 install.sh" >&2
      return 1
    fi
    if [ "$HOME_DIR" = "$HOME" ] && [ "$(uname)" = Darwin ] \
       && ! launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then
      echo "缺    launchd 任务 $label 没在跑，跑一次 install.sh" >&2
      return 1
    fi
    return 0
  fi
  if [ ! -f "$plist" ] || [ "$(cat "$plist")" != "$want" ]; then
    mkdir -p "$(dirname "$plist")"
    if [ "$HOME_DIR" = "$HOME" ] && [ "$(uname)" = Darwin ]; then
      launchctl bootout "gui/$(id -u)/$label" >/dev/null 2>&1 || true
      # bootout 返回时，有进程在跑的任务还在退出，launchctl print 仍找得到它；下面据此跳过
      # bootstrap，任务就停着没人起。等它真的不在了（最多 10 秒）再往下走。
      for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
        launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1 || break
        sleep 0.5
      done
    fi
    printf '%s\n' "$want" > "$plist"
  fi
  if [ "$HOME_DIR" = "$HOME" ] && [ "$(uname)" = Darwin ] \
     && ! launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then
    launchctl bootstrap "gui/$(id -u)" "$plist" \
      || { echo "缺    launchd 任务装不上：$plist" >&2; status=1; }
  fi
  echo "$installed"
  return "$status"
}

if [ -f "$PROMPT_SRC/shared.md" ]; then
  prompt_rc=0
  if [ -d "$HOME_DIR/.claude" ]; then
    link_prompt "$HOME_DIR/.claude/CLAUDE.md" "$PROMPT_SRC/shared.md" || prompt_rc=1
    retire_prompt "$HOME_DIR/.claude/rules/mmw-claude.md" || prompt_rc=1
  fi
  pi_agents="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}/AGENTS.md"
  if [ -f "$pi_agents" ] && head -n 1 "$pi_agents" | grep -q "mmw prompt-sync"; then
    if [ "$mode" = check ]; then
      echo "残留  $pi_agents 是本仓库给 Pi 生成的，这次不装，跑一次 install.sh 摘掉" >&2; prompt_rc=1
    else
      rm "$pi_agents"; echo "摘掉  $pi_agents"
    fi
  fi

  if [ "$mode" = check ]; then
    MMW_INSTALL_HOME="$HOME_DIR" python3 "$PROMPT_SRC/render.py" --check || prompt_rc=1
  else
    MMW_INSTALL_HOME="$HOME_DIR" python3 "$PROMPT_SRC/render.py" || {
      prompt_rc=1
      echo "注意  首次装或生成物被改过时，跑：python3 $PROMPT_SRC/render.py --adopt" >&2
    }
  fi

  # launchd：只在真家目录装。WatchPaths 里的路径是本 checkout 的源文件，换 checkout 跑一次本脚本就重写。
  if [ "$HOME_DIR" = "$HOME" ] && [ "$(uname)" = Darwin ]; then
    PLIST="$HOME/Library/LaunchAgents/com.mmw.prompt-sync.plist"
    want_plist="$(cat <<XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.mmw.prompt-sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>$(command -v python3)</string>
    <string>$PROMPT_SRC/render.py</string>
  </array>
  <key>WatchPaths</key>
  <array>
    <string>$PROMPT_SRC/shared.md</string>
  </array>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/mmw-prompt-sync.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/mmw-prompt-sync.log</string>
</dict>
</plist>
XML
)"
    launch_agent com.mmw.prompt-sync "$PLIST" "$want_plist" \
      "已装  launchd 任务 com.mmw.prompt-sync 盯着 $PROMPT_SRC/shared.md" || prompt_rc=1
  fi
  if [ "$mode" != check ] && [ "$prompt_rc" -eq 0 ]; then
    echo "已装  提示词：~/.claude/CLAUDE.md 一条软链，Codex、Grok 各一份生成的 AGENTS.md"
  fi
  [ "$prompt_rc" -eq 0 ] || rc=1
fi

# ---------------- shell 里的 Nowledge Mem Space ----------------
#
# 会话写 Memory 用的是 NMEM_SPACE 指的那个 Space；没设、或指的 Space 不存在，nmem 不报错，
# 静默写进 Default。shell/nmem-space.zsh 在终端进入一个仓库时，按 origin 把它设成这个仓库的
# Space。~/.zshrc 只放加载它的一段，两行标记夹着，指向本 checkout，所以改 nmem-space.zsh 不用重装。
# 这一段每台机器装一次，对所有仓库都一样；仓库自己的 Space 由 setup-mmw 建。
#
# 同样的代码以前手写在 ~/.zshrc 里：从「# Nowledge Mem Space per repository: in a git checkout
# whose origin has a Space」那一行，到其后第一个顶格的 fi，中间有 _nmem_space_sync。认得出整段，
# 就原地换成加载的那一段，--check 报残留；认不全，就报冲突，不动文件。

MMW_MODE="$mode" MMW_ZSHRC="$HOME_DIR/.zshrc" MMW_NMEM_SHELL="$ROOT/shell/nmem-space.zsh" \
python3 - <<'PY' || rc=1
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

mode = os.environ["MMW_MODE"]
zshrc = Path(os.environ["MMW_ZSHRC"])
source = os.environ["MMW_NMEM_SHELL"]
BEGIN = "# >>> mmw: Nowledge Mem Space per repository (mmw-v3/install.sh) >>>"
END = "# <<< mmw: Nowledge Mem Space per repository <<<"
BLOCK = [BEGIN, f"[ -f '{source}' ] && source '{source}'", END]
LEGACY = "# Nowledge Mem Space per repository: in a git checkout whose origin has a Space"

lines = zshrc.read_text(encoding="utf-8").split("\n") if zshrc.is_file() else []


def span(first, last, needle=None):
    """(start, end) of the lines from `first` to the next line equal to `last`, both kept;
    (start, None) when `last` never follows, or `needle` is not between them; None without `first`."""
    if first not in lines:
        return None
    start = lines.index(first)
    end = next((i for i in range(start + 1, len(lines)) if lines[i] == last), None)
    if end is not None and needle is not None and not any(needle in l for l in lines[start:end]):
        end = None
    return start, end


ours = span(BEGIN, END)
legacy = span(LEGACY, "fi", "_nmem_space_sync")
conflicts = []
if ours and ours[1] is None:
    conflicts.append(f"冲突  {zshrc} 有「{BEGIN}」却没有「{END}」；补上或删掉那一行再跑")
if legacy and legacy[1] is None:
    conflicts.append(f"冲突  {zshrc} 第 {legacy[0] + 1} 行起手写的 NMEM_SPACE 一段认不全；"
                     "删掉它再跑，本段会装上同样的东西")
if conflicts:
    sys.stderr.write("\n".join(conflicts) + "\n")
    sys.exit(1)

if mode == "check":
    failed = False
    if not ours or lines[ours[0]:ours[1] + 1] != BLOCK:
        sys.stderr.write(f"缺    {zshrc} 里加载 {source} 的一段，跑一次 install.sh\n")
        failed = True
    if legacy:
        sys.stderr.write(f"残留  {zshrc} 第 {legacy[0] + 1} 行起手写的 NMEM_SPACE 一段，"
                         "跑一次 install.sh 换成加载 shell/nmem-space.zsh\n")
        failed = True
    if not failed:
        print(f"shell {zshrc} 加载 {source}")
    sys.exit(1 if failed else 0)

dropped = set()
for found in (ours, legacy):
    if found:
        dropped.update(range(found[0], found[1] + 1))
if dropped:
    at = min(dropped)
    new = lines[:at] + BLOCK + [l for i, l in enumerate(lines) if i > at and i not in dropped]
else:
    body = lines[:-1] if lines and lines[-1] == "" else lines
    new = body + ([""] if body else []) + BLOCK + [""]
if new != lines:
    if zshrc.is_file():
        backup = zshrc.with_name(zshrc.name + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S"))
        shutil.copy2(zshrc, backup)
        for old in zshrc.parent.glob(zshrc.name + ".bak-*"):
            if old != backup and old.is_file():
                old.unlink()
    scratch = zshrc.with_name(zshrc.name + ".mmw-tmp")
    scratch.write_text("\n".join(new), encoding="utf-8")
    scratch.replace(zshrc)
    if legacy:
        print(f"换掉  {zshrc} 里手写的 NMEM_SPACE 一段")
print(f"已装  {zshrc} 加载 {source}")
PY

# ---------------- task board LaunchAgent ----------------
#
# MMW_INSTALL_HOME 下只写或核 plist，绝不调用 launchctl；这让测试能验证同一份定义而不改变本机服务。
# 真家目录下由 launchd 守住 supervisor.py，后者再按 MMW_HOME/boards.json 守住各仓库的 board。

BOARD_PLIST="$HOME_DIR/Library/LaunchAgents/com.mmw.board.plist"
BOARD_SUPERVISOR="$ROOT/board/supervisor.py"
BOARD_PATH="$HOME_DIR/.local/bin:$HOME_DIR/.grok/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
board_gh="$(command -v gh 2>/dev/null || true)"
if [ -n "$board_gh" ]; then
  board_gh_dir="$(dirname "$board_gh")"
  case ":$BOARD_PATH:" in
    *":$board_gh_dir:"*) ;;
    *) BOARD_PATH="$board_gh_dir:$BOARD_PATH" ;;
  esac
fi
board_plist="$(cat <<XML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.mmw.board</string>
  <key>ProgramArguments</key>
  <array>
    <string>$(command -v python3)</string>
    <string>$BOARD_SUPERVISOR</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$BOARD_PATH</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME_DIR/Library/Logs/mmw-board.log</string>
  <key>StandardErrorPath</key><string>$HOME_DIR/Library/Logs/mmw-board.log</string>
</dict>
</plist>
XML
)"

launch_agent com.mmw.board "$BOARD_PLIST" "$board_plist" \
  "已装  launchd 任务 com.mmw.board 守住 $BOARD_SUPERVISOR" || rc=1

# ---------------- Paseo 侧配置 ----------------
#
# 源在仓库（hosts.json 里两条 provider 的字面量），host 侧只放生成物：CLI 软链、
# ~/.paseo/config.json 里的 provider、worktrees.root。models.json 在 ~/.mmw/：第一次
# install 从 hosts.json 的 defaults 写入，之后不覆盖。不写 Agent profile。
# MMW_INSTALL_HOME 之下不跑 paseo reload（与 launchd 同构）。

PASEO_BIN_SRC="/Applications/Paseo.app/Contents/Resources/bin/paseo"
PASEO_BIN_LINK="$HOME_DIR/.local/bin/paseo"
PASEO_CONFIG="$HOME_DIR/.paseo/config.json"
PASEO_WORKTREES_ROOT="$HOME_DIR/paseo-worktrees"

if [ "$mode" = check ]; then
  if [ ! -L "$PASEO_BIN_LINK" ] || [ "$(readlink "$PASEO_BIN_LINK")" != "$PASEO_BIN_SRC" ]; then
    echo "缺    $PASEO_BIN_LINK" >&2
    rc=1
  fi
  if ! PATH="$HOME_DIR/.local/bin:$PATH" command -v paseo >/dev/null 2>&1; then
    echo "缺    command -v paseo" >&2
    rc=1
  fi
else
  mkdir -p "$HOME_DIR/.local/bin"
  ln -sfn "$PASEO_BIN_SRC" "$PASEO_BIN_LINK"
  echo "已装  $PASEO_BIN_LINK"
fi

MMW_MODE="$mode" \
MMW_PASEO_CONFIG="$PASEO_CONFIG" \
MMW_MODELS_PY="$SKILLS_SRC/dispatch/scripts/models.py" \
MMW_PASEO_WORKTREES="$PASEO_WORKTREES_ROOT" \
MMW_HOME_DIR="$HOME_DIR" \
MMW_HOME="${MMW_HOME:-$HOME_DIR/.mmw}" \
python3 - <<'PY' || rc=1
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

mode = os.environ["MMW_MODE"]
config_path = Path(os.environ["MMW_PASEO_CONFIG"])
models_py = Path(os.environ["MMW_MODELS_PY"])
worktrees_root = os.environ["MMW_PASEO_WORKTREES"]

_spec = importlib.util.spec_from_file_location("mmw_models", models_py)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

GROK_PROVIDER = {
    "extends": "acp",
    "label": "Grok",
    "command": ["grok", "agent", "stdio"],
    "params": {"clientCapabilities": {"terminal": False}},
}
CURSOR_PROVIDER = {
    "extends": "acp",
    "label": "Cursor",
    "command": ["cursor-agent", "acp"],
}


def die(msg):
    sys.stderr.write(f"缺    {msg}\n")
    sys.exit(1)


def load(path):
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"{path} 不是合法 JSON：{exc}")
    return value if isinstance(value, dict) else {}


def backup_latest(path):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = path.with_name(path.name + ".bak-" + stamp)
    shutil.copy2(path, backup)
    for old in path.parent.glob(path.name + ".bak-*"):
        if old != backup and (old.is_file() or old.is_symlink()):
            old.unlink()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.is_file():
        old = path.read_text(encoding="utf-8")
        if old != text:
            backup_latest(path)
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(text, encoding="utf-8")
    scratch.replace(path)


def merge_providers(data):
    agents = data.setdefault("agents", {})
    providers = agents.setdefault("providers", {})
    providers["grok"] = dict(GROK_PROVIDER)
    providers["cursor"] = dict(CURSOR_PROVIDER)
    worktrees = data.setdefault("worktrees", {})
    worktrees["root"] = worktrees_root
    data.setdefault("version", 1)
    return data


failed = False
try:
    config_file = models.models_json_path()
    if mode != "check":
        installed = models.install_local_config()
        config = installed.config
        if installed.created:
            print(f"已装  {config_file}")
    else:
        config = models.read_local_config()
    config, scan, errors = models.check_local_config(config)
    if errors:
        for item in errors:
            sys.stderr.write(f"缺    {config_file} {item['cell']}: {item['reason']}\n")
        sys.exit(1)
except ValueError as exc:
    die(str(exc))

if mode == "check":
    data = load(config_path)
    providers = ((data.get("agents") or {}).get("providers") or {})
    for name, want in (("grok", GROK_PROVIDER), ("cursor", CURSOR_PROVIDER)):
        have = providers.get(name)
        if have != want:
            sys.stderr.write(f"缺    agents.providers.{name} 与 install.sh 不一致\n")
            failed = True
    have_root = ((data.get("worktrees") or {}).get("root"))
    if have_root != worktrees_root:
        sys.stderr.write(f"缺    worktrees.root 应为 {worktrees_root} 实为 {have_root}\n")
        failed = True
    sys.exit(1 if failed else 0)

data = merge_providers(load(config_path))
save(config_path, data)
print(f"已装  {config_path}")
sys.exit(1 if failed else 0)
PY

# `paseo reload` 落地本段刚写的两条 provider。`worktrees.root` 不在——Paseo 只在启动时读它一次——所以改了它要重启
# daemon，否则新工作区还是建到 daemon 启动时的那个根目录去。哪些设置卡在这上面，只有
# `--json` 的 restartRequiredPaths 按名字说得出来。它比对的是 daemon 启动时的配置，所以
# 列出来的不限于这一次安装改的。
if [ "$mode" != check ] && [ "$HOME_DIR" = "$HOME" ]; then
  if reload_out="$(PATH="$HOME_DIR/.local/bin:$PATH" paseo reload --json 2>&1)"; then
    printf '%s' "$reload_out" | python3 -c '
import json, sys

try:
    paths = (json.load(sys.stdin) or {}).get("restartRequiredPaths") or []
except Exception:
    sys.exit(0)
if paths:
    print("注意  这些设置要等 daemon 重启才生效，跑 paseo daemon restart：")
    for path in paths:
        print("        " + str(path))
'
  else
    echo "注意  paseo reload 没跑成：${reload_out:-exit $?}"
  fi
fi

# ---------------- Orca 侧工作树配置 ----------------
#
# 协议自己用 git 切工作树，落点是每个仓库的 `.worktrees/`。这一条让 Orca 自己建的树也落在
# 同一处，只关系到 Orca 的界面，所以只在安装时写，--check 不查。没有 orca 的机器跳过。

if [ "$mode" != check ] && command -v orca >/dev/null 2>&1; then
  python3 - <<'PY' || rc=1
import json
import subprocess
import sys


def orca(*args):
    return subprocess.run(["orca", *args], check=False, capture_output=True, text=True)


proc = orca("project", "setups", "--json")
try:
    setups = json.loads(proc.stdout)["result"]["setups"]
except Exception:
    sys.stderr.write(f"缺    读不出 orca project setups --json（退出 {proc.returncode}），worktree-base-path 没写\n")
    sys.exit(1)
failed = False
for row in setups:
    ident = str((row or {}).get("id") or "")
    if not ident:
        continue
    if orca("project", "setup-update", "--setup", ident, "--worktree-base-path", ".worktrees",
            "--json").returncode:
        sys.stderr.write(f"缺    orca setup {ident} 的 worktree-base-path 没写上：手动跑 "
                         f"orca project setup-update --setup {ident} --worktree-base-path .worktrees\n")
        failed = True
    else:
        print(f"已装  orca setup {ident} worktree-base-path .worktrees")
sys.exit(1 if failed else 0)
PY
fi

# Nowledge Mem 的共享对象。Identity 只写来源角色，default Space 固定为 mmw-toolbox，
# 避免一次漏传 repository Space 时退回个人 Default。repository Space 由 dispatch.sh open 建立。
# 有就不动，没有才建；--check 只看在不在。
MMW_MODE="$mode" python3 - <<'PY' || rc=1
import os
import shutil
import subprocess
import sys

mode = os.environ["MMW_MODE"]

if shutil.which("nmem") is None:
    if mode == "check":
        sys.stderr.write("没查  Nowledge Mem objects（本机没有 nmem）\n")
    raise SystemExit(0)


def nmem(*args):
    return subprocess.run(["nmem", "--json", *args], text=True, capture_output=True)


failed = False
wanted = [("Space mmw-toolbox", ("spaces", "show", "mmw-toolbox"),
           ("spaces", "create", "MMW Toolbox", "--id", "mmw-toolbox", "--retrieval-mode", "strict"))]
for ident, name, role in (("mmw-worker", "MMW Worker", "worker"),
                          ("mmw-reviewer", "MMW Reviewer", "reviewer")):
    wanted.append((f"Identity {ident}", ("agents", "show", ident),
                   ("agents", "enroll", ident, "--name", name, "--role", role,
                    "--default-space", "mmw-toolbox")))
for label, show, create in wanted:
    if nmem(*show).returncode == 0:
        continue
    if mode == "check":
        sys.stderr.write(f"缺    Nowledge Mem {label}：跑一次 install.sh\n")
        failed = True
        continue
    made = nmem(*create)
    if made.returncode:
        detail = (made.stderr or made.stdout).strip().replace("\n", "; ")
        sys.stderr.write(f"缺    Nowledge Mem {label} 建不起来：{detail}\n")
        failed = True
    else:
        print(f"已装  Nowledge Mem {label}")
sys.exit(1 if failed else 0)
PY

# Cursor 的 Nowledge Mem MCP 一条：~/.cursor/mcp.json 里 mcpServers.nowledge-mem。
# 条目内容问本机的 nmem 要（`nmem config mcp show --host cursor`),因为 URL 与 header 跟着
# 这台机器的 nmem client 配置走，本地 server 与 remote Mem 两样。唯一的改动是去掉它给的
# type 字段：cursor-agent 只认 url 与 headers，带上 type 它把整条 server 跳过，症状是
# `cursor-agent mcp list` 报 No MCP servers configured、worker 静默地没有 memory 工具。
# 同一份文件里别的 server 一字不动。没有可用 nmem 的机器跳过这一样。

CURSOR_MCP="$HOME_DIR/.cursor/mcp.json"

if [ ! -d "$HOME_DIR/.cursor" ]; then
  echo "跳过  ${CURSOR_MCP}（host 没装）"
elif command -v nmem >/dev/null 2>&1 && nmem_mcp="$(nmem --json config mcp show --host cursor 2>/dev/null)"; then
  MMW_MODE="$mode" \
  MMW_CURSOR_MCP="$CURSOR_MCP" \
  MMW_NMEM_MCP="$nmem_mcp" \
  python3 - <<'PY' || rc=1
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

mode = os.environ["MMW_MODE"]
path = Path(os.environ["MMW_CURSOR_MCP"])
NAME = "nowledge-mem"

try:
    want = json.loads(os.environ["MMW_NMEM_MCP"])["config"]["mcpServers"][NAME]
except Exception as exc:
    sys.stderr.write(f"缺    nmem config mcp show --host cursor 没给出 {NAME}：{exc}\n")
    sys.exit(1)
if not isinstance(want, dict):
    sys.stderr.write(f"缺    nmem 给的 {NAME} 不是一个 object\n")
    sys.exit(1)
want.pop("type", None)


def load(p):
    if not p.is_file():
        return {}
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        sys.stderr.write(f"缺    {p} 不是合法 JSON：{exc}\n")
        sys.exit(1)
    return value if isinstance(value, dict) else {}


def backup_latest(p):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = p.with_name(p.name + ".bak-" + stamp)
    shutil.copy2(p, backup)
    for old in p.parent.glob(p.name + ".bak-*"):
        if old != backup and (old.is_file() or old.is_symlink()):
            old.unlink()


data = load(path)
have = (data.get("mcpServers") or {}).get(NAME)

if mode == "check":
    if have != want:
        sys.stderr.write(f"缺    {path} 里 mcpServers.{NAME} 与 nmem 给的不一致\n")
        sys.exit(1)
    sys.exit(0)

if have != want:
    data.setdefault("mcpServers", {})[NAME] = want
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.is_file():
        backup_latest(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(text, encoding="utf-8")
    scratch.replace(path)
print(f"已装  {path}")
PY
else
  echo "跳过  ${CURSOR_MCP}（本机没有可用的 nmem）"
fi

if [ "$mode" = check ]; then
  if [ "$rc" -eq 0 ]; then
    echo "齐了：技能 ${installed_dests} 处 × ${#wanted_names[@]} 个，hook 见上"
  fi
else
  mkdir -p "$(dirname "$INSTALLED_ROOT_FILE")"
  printf '%s\n' "$ROOT" > "$INSTALLED_ROOT_FILE"
  echo
  echo "技能目录：${SKILLS_SRC}"
  echo "改技能直接改这个目录里的文件，host 下次调用就是新的。"
  echo "装自  ${ROOT}（记在 ${INSTALLED_ROOT_FILE}；别的 checkout 跑 --check 时按它核对）"
fi

exit "$rc"
