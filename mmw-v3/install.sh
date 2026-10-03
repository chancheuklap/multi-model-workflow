#!/usr/bin/env bash
# 把 MMW v3 装到本机，让每个 host 都读得到。装六样东西：
#
#   技能              skills.txt 列出的每个技能，在 ~/.agents/skills 与 ~/.claude/skills 各一条
#                     软链，指向本 checkout 的 mmw-v3/skills/<名>
#   hook              只有 mmw-mode 技能的 mode-hook.py 一样，依据 U-2 只登记在 Claude Code 与
#                     Codex 的 SessionStart、SubagentStart、UserPromptSubmit 三个事件上。登记的
#                     命令调复制来的 ~/.mmw/bin/hook-launcher（普通文件，不是软链；源文件是
#                     mmw-v3/hook-launcher.py），由它按 installed-root 找到 mode-hook.py。Codex 的
#                     每一条另在 ~/.codex/config.toml 写下 trusted_hash。
#   提示词            prompt/shared.md 与 prompt/hosts/<host>.md：Claude Code 读软链，Codex、Pi、Grok
#                     读 prompt/render.py 拼出的 AGENTS.md
#   launchd 任务      com.mmw.prompt-sync，盯着提示词源文件，改了就重拼 Codex、Pi、Grok 的 AGENTS.md
#   Paseo 侧配置      ~/.local/bin/paseo 软链；~/.paseo/config.json 里 grok/cursor 两条 provider、
#                     worktrees.root。不写 Agent profile。~/.mmw/models.json 缺席时写入默认值，
#                     或把同目录遗留的 models.md 一次性导入后删除；已有 JSON 不覆盖。
#   Orca 侧工作树     有 orca 时：每个 setup 的 worktree-base-path 为 .worktrees；
#                     Git repo 的 externalWorktreeVisibility 为 show。没有 orca 则跳过。
#
# 装完把本 checkout 的 mmw-v3 目录记进 ~/.mmw/installed-root。
#
# 本仓库装过、这里不装的东西，install 摘掉，--check 报残留：指向 mmw-v2 各技能来源目录的软链，
# ~/.mmw/skill-copies/ 安装副本目录及指进它的软链，subagent 定义文件的软链，tool-guard 与
# turn-guard 在 Claude Code、Codex、Cursor、Grok、Pi 的登记，以及本仓库在这些 host 配置里写过、
# 这次不装的其他 hook。task board 的 com.mmw.board LaunchAgent、Nowledge Mem 对象、Cursor 的 MCP
# 条目不归本脚本管：不装、不核，本机上有什么都不动。
#
# 技能软链不是拷贝：host 读的就是 mmw-v3/skills/ 的文件，改动下一次调用生效。description 由
# host 启动时扫描，改它另要重开会话。
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西、有残留或有 stale link 回 1。
#                         installed-root 记的是另一个 checkout 的 mmw-v3 目录时，交给那个目录自己的
#                         install.sh --check；记的是别的目录（比如一个 mmw-v2 checkout）时就地核对，
#                         并把 installed-root 报成残留或缺。
#                         另读 locations.py 的 MODE_SCRIPTS 下 runners/*.sh 的 MMW_USES，问 PATH 上的二进制还认不认；
#                         读不到帮助页报「没查」，flag 对不上报「不一致」，两句话分开。
#                         核对复制的 .mmw/bin/hook-launcher 与 mmw-v3/hook-launcher.py 逐字节相同
#                         且不是软链，并核对 Claude Code、Codex 的 hook 都经 hook-launcher；不同报
#                         「不一致」，这一项改退出码。
#                         跑 writing-skill-sets 技能的 check_skill_text.py 核对整套技能的文本：
#                         FAIL 时打印它点名的每个问题并回 1；跑不起来报「没查」并回 1。
#
# 两种模式在 hook 都齐了的时候都打印 HOOKS-INSTALLED。
#
# 技能装两处，不按 host 分。~/.agents/skills 不属于任何一个 host，Codex、Cursor、Grok、Pi
# 都原生扫它；Claude Code 不扫，只认 ~/.claude/skills，所以那一处再装一份。两处装的是
# 同一批软链。
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/skills"
LIST="$ROOT/skills.txt"

# 一条软链是不是本仓库装的：目标落在本仓库任一 checkout（主 checkout 或某个 worktree）
# 的 mmw-v3/skills/ 里，或 mmw-v2 的四个技能来源目录（skills/、upstream/skills/、
# upstream-diagram-design/skills/、upstream-pstack/skills/）里，或安装目标家目录的
# skill-copies 下，按路径段认。ADR 0006 说的「指回本仓库」是仓库，不是某一个
# checkout：从哪个 checkout 运行本脚本，哪个 checkout 的 mmw-v3/skills/ 就接管这批软链。
ours_skill_target() {
  case "$1" in
    "$SKILL_COPIES/"* | */mmw-v3/skills/* | */mmw-v2/skills/* | */mmw-v2/upstream/skills/* | */mmw-v2/upstream-diagram-design/skills/* | */mmw-v2/upstream-pstack/skills/*) return 0 ;;
  esac
  return 1
}

# 本仓库不再装 subagent 定义文件，所以这个判据只用来认领残留：见下面 RETIRED_AGENT_DIRS。
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

# MMW_V3_HOME 只给测试用：把安装位置整体搬到一个一次性目录下，不碰真的家目录。
HOME_DIR="${MMW_V3_HOME:-$HOME}"
SKILL_COPIES="$HOME_DIR/.mmw/skill-copies"
# 隔离安装只可调用显式给出的 launchctl 替身；真安装不读这个测试入口。
LAUNCHCTL=launchctl
if [ -n "${MMW_V3_HOME+x}" ]; then
  LAUNCHCTL="${MMW_V3_LAUNCHCTL:-}"
fi
[ "$(uname)" = Darwin ] || LAUNCHCTL=""

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

# 装过之后记下是从哪个 checkout 装的。--check 从另一个 checkout 跑、记下的是一个 mmw-v3 目录时，
# 交给那个目录自己的 install.sh 核对，只核对、不接管：一个冻结的 checkout 装给各 host 用，
# 改造这套工具箱的那一夜就在别的 checkout 上进行，advance 并进去多少都不会动到正在运行的
# host。核对用的是装着的那一份自己的脚本：拿这个 checkout 的核对逻辑去读另一个版本的
# 文件，两边的函数对不上时核对本身就会出错。
# 记下的不是 mmw-v3 目录（比如一个 mmw-v2 checkout）时不交出去：那份脚本核对的是它自己装的
# 那一套，答不了 v3 装没装；就地核对，下面把 installed-root 报出来。
INSTALLED_ROOT_FILE="$HOME_DIR/.mmw/installed-root"
if [ "$mode" = check ] && [ -f "$INSTALLED_ROOT_FILE" ]; then
  installed_root="$(cat "$INSTALLED_ROOT_FILE")"
  if [ -n "$installed_root" ] && [ -d "$installed_root" ] && [ "$installed_root" != "$ROOT" ] \
     && [ "$(basename "$installed_root")" = mmw-v3 ]; then
    echo "装自  ${installed_root}（本 checkout ${ROOT} 只核对，不接管）"
    [ -f "$installed_root/install.sh" ] || die "装着的 checkout 里没有 install.sh：$installed_root"
    exec bash "$installed_root/install.sh" --check
  fi
fi

[ -f "$LIST" ] || die "缺 skills.txt：$LIST"
[ -d "$SKILLS_SRC" ] || die "缺技能目录：$SKILLS_SRC"

# 读 skills.txt。一行是一个技能名，即 $SKILLS_SRC/<名>。名字后面另有记号、名字里带 /，
# 在这里停下：这时还没有建任何 host 目录。每个技能都要真的存在——写错要在动 host 之前就停。
wanted_dirs=()
wanted_names=()
while IFS= read -r line; do
  line="${line%%#*}"
  tokens=()
  read -r -a tokens <<< "$line"
  [ "${#tokens[@]}" -gt 0 ] || continue
  name="${tokens[0]}"
  if [ "${#tokens[@]}" -ne 1 ]; then
    die "skills.txt 的这一行有不认识的记号：${tokens[*]}。一行只写一个技能名；删掉名字后面的记号"
  fi
  case "$name" in
    */* | . | ..) die "skills.txt 的这一行不是技能名：${name}。写 $SKILLS_SRC 下的目录名，不带前缀与 /" ;;
  esac
  dir="$SKILLS_SRC/$name"
  [ -f "$dir/SKILL.md" ] || die "skills.txt 里的技能不存在：${name}（没有 $dir/SKILL.md）"
  wanted_dirs+=("$dir")
  wanted_names+=("$name")
done < "$LIST"

[ "${#wanted_names[@]}" -gt 0 ] || die "skills.txt 是空的：$LIST"

# 名字撞车要在装之前发现：两个技能软链成同一个名字，后装的会盖掉先装的。
dupes="$(printf '%s\n' "${wanted_names[@]}" | sort | uniq -d)"
[ -z "$dupes" ] || die "skills.txt 里有重名技能：$(echo "$dupes" | tr '\n' ' ')"

rc=0
installed_dests=0
# hook 一段齐了才打印 HOOKS-INSTALLED。
hooks_rc=0

# 记的是另一个存在的 mmw-v3 目录时，上面已经交出去了；走到这里的 --check，installed-root
# 记的是本 checkout、别的目录、一个已不存在的目录，或什么都没记。记的不是本 checkout 时，
# hook-launcher 会去记下的那个目录里找 mode-hook.py。
if [ "$mode" = check ]; then
  recorded_root="$(cat "$INSTALLED_ROOT_FILE" 2>/dev/null || true)"
  if [ "$recorded_root" != "$ROOT" ]; then
    if [ -n "$recorded_root" ] && [ "$(basename "$recorded_root")" != mmw-v3 ]; then
      echo "残留  ${INSTALLED_ROOT_FILE} 记的是 ${recorded_root}，不是 mmw-v3 目录；hook-launcher 会去那里找脚本：跑一次 install.sh 改记本 checkout" >&2
    else
      echo "缺    ${INSTALLED_ROOT_FILE} 记的不是本 checkout ${ROOT}（记的是 ${recorded_root:-空，或文件不在}）：跑一次 install.sh" >&2
    fi
    rc=1
  fi
fi

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
      if [ -L "$link" ] && [ "$(readlink "$link")" = "$want" ]; then
        continue
      fi
      have="$(readlink "$link" 2>/dev/null || true)"
      case "$have" in
        "$SKILL_COPIES/"*)
          echo "残留  $link 指进 ${SKILL_COPIES}，跑一次 install.sh 换成指向 $want" >&2 ;;
        */mmw-v2/*)
          echo "残留  $link 指向 mmw-v2 的 ${have}，跑一次 install.sh 换成指向 $want" >&2 ;;
        *)
          echo "缺    $link" >&2 ;;
      esac
      rc=1
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

# ---------------- retired 的安装位置 ----------------

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

# 下面六处是各 host 扫 subagent 定义文件的目录。本仓库不往里装任何东西：每个 host 都自带
# 通用 subagent，用哪个 model 由起它的那个会话决定，所以一份按 host 各写一遍的定义文件没有
# 读者。留在那里的软链指向本仓库已经删掉的文件，host 扫到一条断链就是一个起不来的 agent，
# 所以每次安装摘一遍，--check 报残留。判据与技能那边同构：只认指回本仓库的，别人放在同一个
# 目录里的东西一律不碰。
RETIRED_AGENT_DIRS=(
  "$HOME_DIR/.claude/agents"
  "${CODEX_HOME:-$HOME_DIR/.codex}/agents"
  "${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}/agents"
  "$HOME_DIR/.cursor/agents"
  "$HOME_DIR/.grok/agents"
  "$HOME_DIR/.grok/roles"
)

for dest in "${RETIRED_AGENT_DIRS[@]}"; do
  [ -d "$dest" ] || continue

  retired=()
  while IFS= read -r stale; do
    [ -n "$stale" ] || continue
    retired+=("$stale")
  done < <(repo_links "$dest" ours_agent_target)

  if [ "$mode" = check ]; then
    if [ "${#retired[@]}" -gt 0 ]; then
      echo "残留  ${dest} 里还有 ${#retired[@]} 条 subagent 软链指回本仓库，跑一次 install.sh 摘掉" >&2
      rc=1
    fi
    continue
  fi

  [ -f "$dest/.mmw-agents" ] && rm "$dest/.mmw-agents"
  [ "${#retired[@]}" -gt 0 ] || continue
  for stale in "${retired[@]}"; do
    rm "$stale"
  done
  echo "退役  摘掉 ${#retired[@]} 个 subagent <- ${dest}"
done

# ---------------- skill-copies ----------------
#
# ~/.mmw/skill-copies/ 是本仓库给一部分技能生成过的安装副本目录；这里不生成副本，技能一律
# 软链回 mmw-v3/skills/。上面两段已把指进它的软链换掉或摘掉；再没有软链指进它，就整个删掉。
# 还有软链指进它就留着，并点名那几条。--check 见到它还在就报残留。
copies_links() {
  local dest link
  for dest in "${HOST_DIRS[@]}" "${RETIRED_DIRS[@]}"; do
    [ -d "$dest" ] || continue
    for link in "$dest"/*; do
      [ -L "$link" ] || continue
      case "$(readlink "$link")" in
        "$SKILL_COPIES/"*) printf '%s\n' "$link" ;;
      esac
    done
  done
  return 0
}

if [ -e "$SKILL_COPIES" ] || [ -L "$SKILL_COPIES" ]; then
  if [ "$mode" = check ]; then
    echo "残留  $SKILL_COPIES 是安装副本目录，这里不装副本，跑一次 install.sh 删掉" >&2
    rc=1
  else
    copies_left="$(copies_links)"
    if [ -n "$copies_left" ]; then
      echo "留着  ${SKILL_COPIES}：还有软链指进它：$(printf '%s' "$copies_left" | tr '\n' ' ')" >&2
      rc=1
    else
      rm -rf -- "$SKILL_COPIES"
      echo "摘掉  $SKILL_COPIES"
    fi
  fi
fi

# ---------------- hook ----------------

# 技能是 host 去读的，hook 是 host 来调的，所以它要在 host 的配置里各有一条。这里只登记一样：
# mmw-mode 技能的 mode-hook.py，一条辅助提示，依据 U-2 只挂在 claude、codex 的 SessionStart、
# SubagentStart、UserPromptSubmit，任何失败都不拦截；其他 host 不登记。每一条都指向安装目标
# 家目录下复制的 ~/.mmw/bin/hook-launcher。启动器按 installed-root 找到脚本，脚本搬动不改变
# 登记命令；启动器源文件改动则需重新安装，--check 逐字节核对副本。
#
# Grok 也读 ~/.claude/settings.json，所以写给 claude 的每一条命令前面都带同一个环境变量守卫：
# GROK_AGENT 或 GROK_HOOK_EVENT 有值就退出——两个都判，Grok 0.2.73 只设前一个、1.0 只设后一个；
# GROK_SESSION_ID 不能判，Grok 把它传进每个子进程，会一路带进 Grok 起的 Claude 会话，把那个会话
# 自己的 hook 也关掉。
#
# 合并而不是覆盖：这几处别人也各装了自己的东西。只认 command 里带本脚本名与 gate 名的
# 那一条，认得出就换成新的，认不出就在后面添一条，别人的条目一个字不动。

HOOK_SRC="$SKILLS_SRC/mmw-mode/scripts/mode-hook.py"

if [ -f "$HOOK_SRC" ]; then
  MMW_MODE="$mode" \
  MMW_LAUNCHER="$HOME_DIR/.mmw/bin/hook-launcher" \
  MMW_LAUNCHER_SRC="$ROOT/hook-launcher.py" \
  MMW_NEUTRAL="$NEUTRAL_DIR" \
  MMW_HOOK_HOME="$HOME_DIR" \
  MMW_CODEX="${CODEX_HOME:-$HOME_DIR/.codex}" \
  MMW_PI="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME_DIR/.pi}/agent}" \
  python3 - <<'PY' || { rc=1; hooks_rc=1; }
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

mode = os.environ["MMW_MODE"]
launcher = Path(os.environ["MMW_LAUNCHER"])
launcher_source = Path(os.environ["MMW_LAUNCHER_SRC"])
neutral = os.environ["MMW_NEUTRAL"]
home = Path(os.environ["MMW_HOOK_HOME"])
codex_home = Path(os.environ["MMW_CODEX"])
pi_home = Path(os.environ["MMW_PI"])
failed = False

if mode == "check":
    try:
        same = (launcher.is_file() and not launcher.is_symlink()
                and launcher.read_bytes() == launcher_source.read_bytes())
    except OSError:
        same = False
    if not same:
        sys.stderr.write(f"不一致  {launcher} 与 {launcher_source} 不同或不是普通副本："
                         "run bash mmw-v3/install.sh\n")
        failed = True
else:
    launcher.parent.mkdir(parents=True, exist_ok=True)
    scratch = launcher.with_name(launcher.name + ".mmw-tmp")
    scratch.write_bytes(launcher_source.read_bytes())
    scratch.chmod(0o755)
    scratch.replace(launcher)

# mode-hook.py 只打印一行固定的话；这是宿主等它的上限。
TIMEOUT = 10
SESSION_START_TIMEOUT = 30
# 写给 claude 的每一条命令前面都带它（见本段开头）。
GROK_GUARD = '[ -z "${GROK_AGENT:-}${GROK_HOOK_EVENT:-}" ] || exit 0; '


def for_host(host, command):
    return GROK_GUARD + command + host if host == "claude" else command + host


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
    name = os.path.basename(head.split("'")[-1])
    return name + "' " + tail


def ours(handler, command):
    return isinstance(handler, dict) and marker_of(command) in str(handler.get("command", ""))


def grouped(path, event, matcher, command, timeout=TIMEOUT):
    """Claude Code 与 Codex 都把处理器按 matcher 分组。

    `command` 是完整的一条：脚本路径、gate 与 host。同一个文件里的同一个事件可以带几条我们
    的处理器，靠脚本名加 gate 名认出各自的那条。
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


# ---- 本仓库装过、这次不再装的 hook ----
#
# 技能软链那一段靠扫目录认领本仓库的残留（stale_links）；hook 这一侧是同一个机制。
# 一条登记指着一个不再存在的脚本，host 每次触发那个事件都会调用失败，有的 host 因此
# 挡住每一次输入；所以本仓库写进 host 配置的处理器，这次不装的就摘掉，--check 报残留。
#
# 认领判据：命令里的脚本落在 ~/.agents/skills 下，或指向本仓库复制的 hook-launcher。别人
# （Herdr、Paseo、Nowledge Mem）的处理器指向自己的目录，一条都不碰。
#
# 扫哪几个文件是下面这份显式清单，跟 RETIRED_DIRS 一个道理：「这次装什么」认不出本仓库
# 曾写在哪个文件里，只有人手记着。不再往某个文件写的时候，把它留在清单里。
#
# tool-guard 与 turn-guard 这里一条都不登记。它们的命令另带两个认领记号，指向哪个启动器路径都认，
# 所以在下面清单里的哪个文件里都会被摘掉。
MARKS = (f"'{neutral}/", f"'{launcher}' ", "hook-launcher' tool-guard ", "hook-launcher' turn-guard ")

# 一行一处：文件、它的格式、整个文件是不是只有本仓库写。
# 只有本仓库写的那种，条目清空之后连文件一起删——grok 把 hooks/*.json 全部合并读入，
# 空壳留着不报错也不提示。mmw-turn.json 是本仓库曾经独占的文件，这次一条都不往里写。
SWEPT = [
    (home / ".claude/settings.json", "grouped", False),
    (codex_home / "hooks.json", "grouped", False),
    (home / ".cursor/hooks.json", "cursor", False),
    (home / ".grok/hooks/mmw-verify-ticket.json", "grouped", True),
    (home / ".grok/hooks/mmw-turn.json", "grouped", True),
    (home / ".grok/hooks/mmw-discipline.json", "grouped", True),
    (home / ".grok/hooks/mmw-turn-guard.json", "grouped", True),
]

# pi 那一侧是整文件写入，不存在半条残留；这里不再写的扩展文件列在这里，每次安装删一遍：
# tool-guard 与 turn-guard 各一份。
RETIRED_PI = [pi_home / "extensions/mmw-verify-ticket.ts", pi_home / "extensions/mmw-turn-guard.ts"]


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
            if any(mark in command for mark in MARKS) and command not in keep:
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
grouped_hosts = [
    ("claude", home / ".claude", home / ".claude/settings.json"),
    ("codex", codex_home, codex_home / "hooks.json"),
]
points = []
# 这次装的每一条完整命令，按文件收着：sweep 摘的就是这个集合之外的。
keep = {}


def point(host_home, path, label, actions, command=None):
    points.append((host_home, path, label, actions))
    if command is not None:
        keep.setdefault(path, set()).add(command)


# U-2: Claude Code 2.1.285、Codex 0.159.2（2026-09-30；results.md 与 #613）
# 三个事件都能注入一行。
for host, host_home, path in grouped_hosts:
    for event, argument, timeout in (
        ("SessionStart", "session-start", SESSION_START_TIMEOUT),
        ("SubagentStart", "subagent-start", TIMEOUT),
        ("UserPromptSubmit", "prompt-submit", TIMEOUT),
    ):
        command = for_host(host, f"exec python3 '{launcher}' mode-hook {argument} ")
        point(host_home, path, event, grouped(path, event, None, command, timeout), command)

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
            sys.stderr.write(f"不一致  {path}  {event} 没有经 {launcher} 登记："
                             "run bash mmw-v3/install.sh\n")
            failed = True
        continue
    install()
    # 写完当场回读：认得出自己刚写的那一条，这个安装点才算数。
    if not installed():
        sys.stderr.write(f"缺    {path}  {event}\n")
        failed = True
        continue
    count += 1

# 装完再扫：当前命令在 keep 里；能认领、却不在 keep 里的登记全部摘掉。
for path, fmt, mmw_owned in SWEPT:
    if not path.exists():
        continue
    dropped, data = sweep(path, fmt, keep.get(path, set()))
    if not dropped:
        continue
    if mode == "check":
        for event, command in dropped:
            sys.stderr.write(f"残留  {path}  {event}  {command}"
                             " 指向本仓库的 hook，这次却不装它，跑一次 install.sh 摘掉\n")
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
    if not path.exists():
        continue
    if mode == "check":
        sys.stderr.write(f"残留  {path} 是 retired 的扩展，跑一次 install.sh 摘掉\n")
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
else
  die "缺    ${HOOK_SRC}：找不到 hook 源文件，无法安装或核对 hook；从本 checkout 的 git 历史恢复该文件后重跑 install.sh"
fi

if [ "$hooks_rc" -eq 0 ]; then
  echo "HOOKS-INSTALLED"
fi

# ---------------- 提示词 ----------------

# 源在 prompt/：shared.md 四家共用，hosts/<host>.md 只给那一家。Claude Code 认软链，所以
# ~/.claude/CLAUDE.md 直接指 shared.md，~/.claude/rules/mmw-claude.md 指 hosts/claude.md，改源即生效。
# 原位已是指向某个 mmw-v3/prompt/ 或 mmw-v2/prompt/ 的软链时，install 改指本 checkout；
# --check 认指向任一 mmw-v3/prompt/ 的，把指向 mmw-v2/prompt/ 的报残留。
# Codex、Pi、Grok 没有引入语法，只能由 render.py 把两份拼成各自的 AGENTS.md；生成物带哈希，
# 被人直接改过 render.py 就拒绝覆盖。launchd 任务监视五个源文件，改动即重拼——Claude Code 那两条
# 软链不需要它。MMW_V3_HOME 之下（测试）只在给了 MMW_V3_LAUNCHCTL 替身时装 launchd 任务。

PROMPT_SRC="$ROOT/prompt"

# 一条软链该指哪里就指哪里；原位是内容相同的普通文件就换成软链（首次迁移），内容不同就是冲突。
link_prompt() {
  local link="$1" want="$2"
  if [ -L "$link" ]; then
    if [ "$(readlink "$link")" = "$want" ]; then return 0; fi
    case "$(readlink "$link")" in
      */mmw-v3/prompt/*) [ "$mode" = check ] || ln -sfn "$want" "$link"; return 0 ;;
      */mmw-v2/prompt/*)
        if [ "$mode" = check ]; then
          echo "残留  $link 指向 mmw-v2 的 $(readlink "$link")，跑一次 install.sh 换成指向 $want" >&2
          return 1
        fi
        ln -sfn "$want" "$link"; return 0 ;;
      *) echo "冲突  $link 是软链但不指回本仓库，跳过" >&2; return 1 ;;
    esac
  fi
  if [ -e "$link" ]; then
    if cmp -s "$link" "$want"; then
      if [ "$mode" = check ]; then echo "缺    $link 还是普通文件，跑一次 install.sh 换成软链" >&2; return 1; fi
      ln -sfn "$want" "$link"; return 0
    fi
    echo "冲突  $link 已存在且内容与 $want 不同；把差异搬进源里再跑" >&2
    return 1
  fi
  if [ "$mode" = check ]; then echo "缺    $link" >&2; return 1; fi
  mkdir -p "$(dirname "$link")"
  ln -sfn "$want" "$link"
}

launch_agent() {
  local label="$1" plist="$2" want="$3" installed="$4" status=0
  if [ "$mode" = check ]; then
    if [ ! -f "$plist" ] || [ "$(cat "$plist")" != "$want" ]; then
      echo "缺    $plist 不存在或指向别的 checkout，跑一次 install.sh" >&2
      return 1
    fi
    if [ -n "$LAUNCHCTL" ] \
       && ! "$LAUNCHCTL" print "gui/$(id -u)/$label" >/dev/null 2>&1; then
      echo "缺    launchd 任务 $label 没在跑，跑一次 install.sh" >&2
      return 1
    fi
    return 0
  fi
  if [ ! -f "$plist" ] || [ "$(cat "$plist")" != "$want" ]; then
    mkdir -p "$(dirname "$plist")"
    if [ -n "$LAUNCHCTL" ]; then
      "$LAUNCHCTL" bootout "gui/$(id -u)/$label" >/dev/null 2>&1 || true
    fi
    printf '%s\n' "$want" > "$plist"
  fi
  if [ -n "$LAUNCHCTL" ] \
     && ! "$LAUNCHCTL" print "gui/$(id -u)/$label" >/dev/null 2>&1; then
    "$LAUNCHCTL" bootstrap "gui/$(id -u)" "$plist" \
      || { echo "缺    launchd 任务装不上：$plist" >&2; status=1; }
  fi
  echo "$installed"
  return "$status"
}

if [ -f "$PROMPT_SRC/shared.md" ]; then
  prompt_rc=0
  if [ -d "$HOME_DIR/.claude" ]; then
    link_prompt "$HOME_DIR/.claude/CLAUDE.md" "$PROMPT_SRC/shared.md" || prompt_rc=1
    link_prompt "$HOME_DIR/.claude/rules/mmw-claude.md" "$PROMPT_SRC/hosts/claude.md" || prompt_rc=1
  fi

  if [ "$mode" = check ]; then
    MMW_V3_HOME="$HOME_DIR" python3 "$PROMPT_SRC/render.py" --check || prompt_rc=1
  else
    MMW_V3_HOME="$HOME_DIR" python3 "$PROMPT_SRC/render.py" || {
      prompt_rc=1
      echo "注意  首次装或生成物被改过时，跑：python3 $PROMPT_SRC/render.py --adopt" >&2
    }
  fi

  # launchd 或显式指定的测试替身。plist 与日志都属于安装目标家目录。
  if [ -n "$LAUNCHCTL" ]; then
    PLIST="$HOME_DIR/Library/LaunchAgents/com.mmw.prompt-sync.plist"
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
    <string>$PROMPT_SRC/hosts/claude.md</string>
    <string>$PROMPT_SRC/hosts/codex.md</string>
    <string>$PROMPT_SRC/hosts/pi.md</string>
    <string>$PROMPT_SRC/hosts/grok.md</string>
  </array>
  <key>StandardOutPath</key><string>$HOME_DIR/Library/Logs/mmw-prompt-sync.log</string>
  <key>StandardErrorPath</key><string>$HOME_DIR/Library/Logs/mmw-prompt-sync.log</string>
</dict>
</plist>
XML
)"
    launch_agent com.mmw.prompt-sync "$PLIST" "$want_plist" \
      "已装  launchd 任务 com.mmw.prompt-sync 盯着 $PROMPT_SRC" || prompt_rc=1
  fi
  if [ "$mode" != check ] && [ "$prompt_rc" -eq 0 ]; then
    echo "已装  提示词：~/.claude 两条软链，Codex、Pi、Grok 各一份生成的 AGENTS.md"
  fi
  [ "$prompt_rc" -eq 0 ] || rc=1
fi

# ---------------- Paseo 侧配置 ----------------
#
# 源在仓库（hosts.json 里两条 provider 的字面量），host 侧只放生成物：CLI 软链、
# ~/.paseo/config.json 里的 provider、worktrees.root。models.json 在 ~/.mmw/：第一次
# install 从 hosts.json 的 defaults 写入，或从遗留 Markdown 导入，之后不覆盖。不写 Agent profile。笔记含
# `from models.md` 的生成 profile 安装时摘掉、--check 报残留；手写的不动。
# MMW_V3_HOME 之下不跑 paseo reload（与 launchd 同构）。

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
MMW_MODELS_PY="$SKILLS_SRC/mmw-mode/scripts/models.py" \
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
RETIRED_PROFILE_NOTE = "from models.md"

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


def is_generated(profile):
    notes = profile.get("notes") if isinstance(profile, dict) else None
    return isinstance(notes, str) and RETIRED_PROFILE_NOTE in notes


def drop_generated(data):
    daemon = data.setdefault("daemon", {})
    existing = list(daemon.get("agentProfiles") or [])
    kept = []
    dropped = []
    for profile in existing:
        if is_generated(profile):
            dropped.append(profile.get("id") if isinstance(profile, dict) else None)
        else:
            kept.append(profile)
    daemon["agentProfiles"] = kept
    return dropped


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
    legacy_file = config_file.with_name("models.md")
    if mode != "check":
        installed = models.install_local_config(legacy_file)
        config = installed.config
        if installed.created:
            print(f"已装  {config_file}")
        if installed.imported:
            print(f"迁移  {legacy_file} -> {config_file}，旧文件已删除")
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
    for profile in ((data.get("daemon") or {}).get("agentProfiles") or []):
        if is_generated(profile):
            sys.stderr.write(f"残留  profile {profile.get('id')}\n")
            failed = True
    have_root = ((data.get("worktrees") or {}).get("root"))
    if have_root != worktrees_root:
        sys.stderr.write(f"缺    worktrees.root 应为 {worktrees_root} 实为 {have_root}\n")
        failed = True
    sys.exit(1 if failed else 0)

data = merge_providers(load(config_path))
for pid in drop_generated(data):
    print(f"摘掉  profile {pid}")
save(config_path, data)
print(f"已装  {config_path}")
sys.exit(1 if failed else 0)
PY

# `paseo reload` 落地本段刚写的两条 provider。`worktrees.root` 不在——Paseo 只在启动时读它一次——所以改了它要重启
# daemon，否则新工作区还是建到 daemon 启动时的那个根目录去。哪些设置卡在这上面，只有
# `--json` 的 restartRequiredPaths 按名字说得出来。它比对的是 daemon 启动时的配置，所以
# 列出来的不限于这一次安装改的。
if [ "$mode" != check ] && [ -z "${MMW_V3_HOME+x}" ]; then
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
# 协议自己用 git 切工作树，落点是每个仓库的 `.worktrees/`。这两条只约束 runner 自己
# 建出来的树也落在同一处，以及外部工作树对人可见（只为人眼，寻址一律用绝对路径）。
# 没有 orca 的机器跳过。--check 只读：`orca project setups --json`（result.setups）与
# `orca repo list --json`（result.repos）。setup-update 只在安装时写，--check 不写。
# base path 的字段名是 `worktreeBasePath`，只在设过之后出现在 setup 行上；相对值挂在
# 仓库路径下（Orca 1.4.199 `shared/worktree/configured-worktree-base-path.js`）。所以
# 字段缺席就是没设，报缺；设了但解析出来不是 `<仓库>/.worktrees` 也报缺。
# 可见性只适用于 `kind: git`；Orca 也把 folder workspace 放进 repo list，那些没有 Git
# worktree，不检查。Git 仓库按 Orca 自己的判定链：仓库级 `externalWorktreeVisibility` 有值就是它；没值时
# 看全局 `worktreeVisibilityDefaults.external`，再按仓库加入日期兜底。Orca 的 CLI 读不出
# 全局默认，所以仓库级没值的那一行报「没查」，不猜。可见性没有 CLI 可写，只核对。
# 列表读不出、形状不对，报「没查」：一个空列表读起来和「全都对」一样。

if command -v orca >/dev/null 2>&1; then
  MMW_MODE="$mode" python3 - <<'PY' || rc=1
import json
import os
import subprocess
import sys

mode = os.environ["MMW_MODE"]


def orca(*args):
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    return subprocess.run(
        ["orca", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def rows_of(proc, key):
    """The list under result.<key>, or None when the answer has any other shape."""
    try:
        data = json.loads(proc.stdout or "")
    except Exception:
        return None
    value = data.get("result") if isinstance(data, dict) else None
    rows = value.get(key) if isinstance(value, dict) else None
    if not isinstance(rows, list):
        return None
    return [x for x in rows if isinstance(x, dict)]


def unread(what, proc):
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    why = f"退出 {proc.returncode}" if proc.returncode != 0 else "回答里没有这张列表"
    if detail:
        why += f"：{detail[0][:160]}"
    sys.stderr.write(
        f"没查  读不出 orca {what}（{why}）：确认 Orca 在运行，再跑一次 --check\n"
    )
    sys.exit(1)


def base_path_ok(value, repo_path):
    if value == ".worktrees":
        return True
    resolved = value if os.path.isabs(value) else os.path.join(repo_path, value)
    return os.path.normpath(resolved) == os.path.normpath(os.path.join(repo_path, ".worktrees"))


failed = False
setups_proc = orca("project", "setups", "--json")
setups = rows_of(setups_proc, "setups") if setups_proc.returncode == 0 else None
if setups is None:
    unread("project setups --json", setups_proc)

if mode != "check":
    for row in setups:
        ident = str(row.get("id") or "")
        if not ident:
            continue
        upd = orca(
            "project", "setup-update",
            "--setup", ident,
            "--worktree-base-path", ".worktrees",
            "--json",
        )
        if upd.returncode != 0:
            why = (upd.stderr or upd.stdout or "").strip().splitlines()
            sys.stderr.write(
                f"缺    orca setup {ident} 的 worktree-base-path 没写上"
                f"（{why[0][:160] if why else f'退出 {upd.returncode}'}）："
                f"手动跑 orca project setup-update --setup {ident} --worktree-base-path .worktrees\n"
            )
            failed = True
        else:
            print(f"已装  orca setup {ident} worktree-base-path .worktrees")

if mode == "check":
    for row in setups:
        ident = str(row.get("id") or "?")
        repo_path = str(row.get("path") or "")
        have = row.get("worktreeBasePath")
        fix = (
            f"跑 bash mmw-v3/install.sh 写上，或只改这一条："
            f"orca project setup-update --setup {ident} --worktree-base-path .worktrees"
        )
        if not isinstance(have, str) or not have.strip():
            sys.stderr.write(f"缺    orca worktree-base-path 没设（{repo_path or ident}）：{fix}\n")
            failed = True
        elif not base_path_ok(have.strip(), repo_path):
            sys.stderr.write(
                f"缺    orca worktree-base-path 应为 .worktrees 实为 {have}（{repo_path or ident}）：{fix}\n"
            )
            failed = True

repos_proc = orca("repo", "list", "--json")
repos = rows_of(repos_proc, "repos") if repos_proc.returncode == 0 else None
if repos is None:
    unread("repo list --json", repos_proc)
for row in repos:
    if row.get("kind") == "folder":
        continue
    vis = row.get("externalWorktreeVisibility")
    path = row.get("path") or row.get("id") or "?"
    if vis == "show":
        continue
    if vis in (None, ""):
        sys.stderr.write(
            f"没查  orca 没给 {path} 的 externalWorktreeVisibility，它落到全局默认上，"
            f"而全局默认 Orca 的 CLI 读不出：在 Orca 里给这个仓库的外部工作树明确选 Show\n"
        )
    else:
        sys.stderr.write(
            f"缺    orca externalWorktreeVisibility 应为 show 实为 {vis}（{path}）："
            f"在 Orca 里把这个仓库的外部工作树改成 Show，Orca 的 CLI 没有写这一项的命令\n"
        )
    failed = True

sys.exit(1 if failed else 0)
PY
else
  echo "跳过  orca 工作树配置（本机没有 orca）"
fi

# ---------------- 适配器 MMW_USES 自检 ----------------
#
# 只在 --check 里跑。读 runners/<name>.sh 文件头的 MMW_USES，去问 PATH 上的同名
# 二进制还认不认这些命令和 flag。Orca 走 `agent-context --json` 精确比对；Herdr
# 与 Paseo 退化成子命令帮助页上的文本核对。Herdr 的子命令帮助会静默掉回顶层用法
# 页（退出码 0），所以必须先确认读到的是这一页：首行不是顶层用法的首行，且
# Usage 行点名这个子命令。确认不了就报「没查」，不拿那一页去对 flag——掉回的
# 顶层页上，flag 名碰巧出现是假一致，碰巧不出现是假不一致。本机没有这个二进制
# 则跳过。没有东西可查——`runners/` 不在、里面没有适配器、一个适配器一条声明都
# 没有、一行声明没有命令名——也报「没查」：什么都没核的检查不许读起来像通过。
# 每一句「没查」「不一致」都带上唯一那条出路。只报，不禁止：不扫 skills.txt，
# 也不删任何技能。

if [ "$mode" = check ]; then
  PYTHONPATH="$SKILLS_SRC/mmw-mode/scripts${PYTHONPATH:+:$PYTHONPATH}" \
  MMW_ROOT="$ROOT" python3 - <<'PY' || rc=1
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import locations

root = Path(os.environ["MMW_ROOT"])
runners = root / "skills" / locations.MODE_SCRIPTS / "runners"
failed = False


def run_cmd(binary, argv):
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    return subprocess.run(
        [binary, *argv],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def first_line(text):
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def not_checked(line):
    global failed
    failed = True
    sys.stderr.write(f"没查    {line}\n")


def parse_uses(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("# MMW_USES:"):
            continue
        rest = line.split(":", 1)[1].strip()
        tokens = rest.split()
        cmd, flags = [], []
        for token in tokens:
            if token.startswith("-"):
                flags.append(token)
            else:
                cmd.append(token)
        if cmd:
            rows.append((cmd, flags, rest))
        else:
            not_checked(
                f"{path.name} 有一行 MMW_USES 没有命令名（{rest or '空'}）："
                f"写成「# MMW_USES: <子命令> --flag …」"
            )
    return rows


def flag_in_help(text, flag):
    return re.search(
        r"(^|[\s,\[\|/])" + re.escape(flag) + r"(?![A-Za-z0-9-])",
        text or "",
    ) is not None


def usage_names(text, binary, cmd):
    needle = " ".join([binary, *cmd])
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("usage:") and needle in stripped:
            return True
    return False


def help_text(binary, cmd):
    """The subcommand's own help page, or (None, why the last try was not it)."""
    top = run_cmd(binary, ["--help"])
    top_first = first_line(top.stdout or top.stderr)
    why = "没有输出"
    for _ in range(3):
        for flag in ("--help", "-h"):
            proc = run_cmd(binary, [*cmd, flag])
            text = proc.stdout or proc.stderr or ""
            if not text.strip():
                why = "没有输出"
                continue
            if first_line(text) == top_first:
                why = "掉回了顶层用法页"
                continue
            if not usage_names(text, binary, cmd):
                why = "Usage 行没点这个子命令的名"
                continue
            return text, ""
    return None, why


def unread(binary, cmd, why):
    named = " ".join([binary, *cmd])
    not_checked(
        f"读不到 {named} 的帮助页（{why}，--help 与 -h 各试三次）："
        f"手动跑 {named} --help，对着适配器的 MMW_USES 看一遍"
    )


def mismatch(binary, cmd, flag):
    global failed
    failed = True
    named = " ".join([*cmd, flag])
    key = flag.lstrip("-")
    sys.stderr.write(
        f"不一致  适配器说它要用 {named}，二进制的 flags 里没有 {key}："
        f"按 {binary} 现在的用法改 runners/{binary}.sh 里这条命令和它的 MMW_USES\n"
    )


def check_help(binary, rows):
    if shutil.which(binary) is None:
        return
    for cmd, flags, rest in rows:
        text, why = help_text(binary, cmd)
        if text is None:
            unread(binary, cmd, why)
            continue
        for flag in flags:
            if not flag_in_help(text, flag):
                mismatch(binary, cmd, flag)


def orca_catalog():
    proc = run_cmd("orca", ["agent-context", "--json"])
    try:
        data = json.loads(proc.stdout or "")
    except Exception:
        return None
    cmds = data.get("commands") if isinstance(data, dict) else None
    if not isinstance(cmds, list):
        return None
    by_name = {}
    for row in cmds:
        if isinstance(row, dict) and row.get("command"):
            by_name[str(row["command"])] = row
    return by_name


def check_orca(rows):
    global failed
    if shutil.which("orca") is None:
        return
    catalog = orca_catalog()
    if catalog is None:
        not_checked("读不到 orca agent-context --json 的命令表：确认 Orca 在运行，再跑一次 --check")
        return
    for cmd, flags, rest in rows:
        name = " ".join(cmd)
        row = catalog.get(name)
        if not isinstance(row, dict):
            sys.stderr.write(
                f"不一致  适配器说它要用 {rest}，二进制没有 {name}："
                f"按 orca 现在的命令表改 runners/orca.sh 里这条命令和它的 MMW_USES\n"
            )
            failed = True
            continue
        listed = row.get("flags")
        if not isinstance(listed, list):
            not_checked(
                f"orca agent-context 里 {name} 那一行读不出 flags 列表："
                f"手动跑 orca {name} --help，对着适配器的 MMW_USES 看一遍"
            )
            continue
        have = {str(item).lstrip("-") for item in listed}
        for flag in flags:
            key = flag.lstrip("-")
            if key not in have:
                mismatch("orca", cmd, flag)


adapters = sorted(runners.glob("*.sh")) if runners.is_dir() else []
if not adapters:
    not_checked(
        f"{runners} 下没有适配器，MMW_USES 一条都没核："
        f"从这个 checkout 的 git 历史里恢复 {runners}/"
    )
for path in adapters:
    binary = path.stem
    rows = parse_uses(path)
    if not rows:
        not_checked(
            f"{path.name} 一条 MMW_USES 声明都没有，它调 {binary} 的命令一条都没核："
            f"在文件头为它调用的每条命令写一行「# MMW_USES: <子命令> --flag …」"
        )
        continue
    if binary == "orca":
        check_orca(rows)
    else:
        check_help(binary, rows)

sys.exit(1 if failed else 0)
PY
fi

# ---------------- 技能文本检查 ----------------
#
# 只在 --check 里跑。writing-skill-sets 技能的 check_skill_text.py 核对整套技能的文本。
# 它的 FAIL 让 --check 回 1，并把它点名的每个问题打印出来；它的 NOT CHECKED 行不是问题，
# 不打印。它跑不起来，或回答的形状认不出，报「没查」并回 1。
if [ "$mode" = check ]; then
  MMW_SKILL_TEXT="$SKILLS_SRC/writing-skill-sets/scripts/check_skill_text.py" \
  python3 - <<'PY' || rc=1
import os
import subprocess
import sys
from pathlib import Path

checker = Path(os.environ['MMW_SKILL_TEXT'])


def unchecked(reason):
    detail = ' '.join(str(reason).splitlines())
    print(f'没查  技能文本检查 {checker}：{detail}；修正原因后再跑 install.sh --check', file=sys.stderr)
    raise SystemExit(1)


if not checker.is_file():
    unchecked('check_skill_text.py 不在')
try:
    result = subprocess.run([sys.executable, str(checker)],
                            capture_output=True, text=True, check=False)
except OSError as exc:
    unchecked(exc)
lines = result.stdout.splitlines()
summary = lines[-1] if lines else ''
if result.returncode == 0 and summary.startswith('OK '):
    print(f'技能文本  {summary}')
    raise SystemExit(0)
if result.returncode == 1 and summary.startswith('FAIL '):
    for line in lines[:-1]:
        if not line.startswith('NOT CHECKED '):
            print(line, file=sys.stderr)
    print(f'不一致  技能文本 {summary}：按上面每一行改正技能文本，再跑 install.sh --check',
          file=sys.stderr)
    raise SystemExit(1)
unchecked(f'退出 {result.returncode}：{result.stdout.strip()} {result.stderr.strip()}')
PY
fi

if [ "$mode" = check ]; then
  if [ "$rc" -eq 0 ]; then
    echo "齐了：技能 ${installed_dests} 处 × ${#wanted_names[@]} 个，hook 见上"
  fi
else
  mkdir -p "$(dirname "$INSTALLED_ROOT_FILE")"
  printf '%s\n' "$ROOT" > "$INSTALLED_ROOT_FILE"
  echo
  echo "source directory：${SKILLS_SRC}"
  echo "技能是软链：改 source directory，host 下次调用生效；description 另要重开会话。"
  echo "装自  ${ROOT}（记在 ${INSTALLED_ROOT_FILE}；别的 checkout 跑 --check 时按它核对）"
fi

exit "$rc"
