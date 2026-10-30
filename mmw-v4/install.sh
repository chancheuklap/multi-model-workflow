#!/usr/bin/env bash
# 把 MMW v4 装到本机，让每个 host 都读得到。下面几样，全部指向运行本脚本的这个 checkout 的 mmw-v4/：
#
#   技能              skills/ 下每个带 SKILL.md 的目录，软链进 ~/.agents/skills 与 ~/.claude/skills
#   提示词            prompt/shared.md：Claude Code 与 Codex 的用户级入口都用软链读取
#   Paseo 侧配置      ~/.local/bin/paseo 软链；~/.paseo/config.json 里的 worktrees.root，并摘掉
#                     从前写进去的 grok、cursor 两条 provider。~/.mmw/models.json 缺席时写入默认值；已有的只动角色行：
#                     roles.json 没有的角色行摘掉（先留一份 .bak- 副本），缺的角色补默认值
#   Orca 侧工作树     有 orca 时，把每个 setup 的 worktree-base-path 设为 .worktrees；--check 报不是的
#   基础工具          一样不装，两种模式都查：gh 已登录，git、python3、uv、node 在 PATH 上，
#                     paseo、herdr、orca 至少一个在 PATH 上。缺的报一行，说怎么装
#   子代理层数        Claude Code、Codex 的子代理层数上限都设为 2
#   task board        一个 com.mmw.board LaunchAgent，按 ~/.mmw/boards.json 为每个仓库守住本机服务
#
# 装完把本 checkout 的 mmw-v4 目录记进 ~/.mmw/installed-root。
#
# 不碰的：Nowledge Mem 的 Space 与 Identity、~/.cursor/mcp.json、
# ~/.zshrc 里加载 nmem-space.zsh 的一段。它们留在 mmw-v3/install.sh 装的样子，指着同一个
# checkout 的 mmw-v3/。
#
# 本机装的是哪一份，只由这一次显式的安装决定。别的 checkout 跑 --check 只核对（见下面
# installed-root 一段），dispatch.sh check 也只跑 --check，把缺的报出来。
#
# 软链不是拷贝：host 读的就是仓库里那个文件。改 mmw-v4/skills/ 下的 SKILL.md，下一次调用就是
# 新的，不用重装。（只有 frontmatter 的 description 是 host 启动时扫的，改它要重开会话。）
#
#   install.sh            装
#   install.sh --check    只看装没装，不动磁盘。齐了回 0，缺东西或有残留回 1。
#   install.sh --back     退回 v3：摘掉本脚本装的、v3 认不出的几样，再跑同一 checkout 的
#                         mmw-v3/install.sh，退出码是它的
#
# 两种模式在 hook 都齐了的时候都打印 HOOKS-INSTALLED。
#
# 技能装两处，不按 host 分。~/.agents/skills 不属于任何一个 host，Codex 原生扫它；
# Claude Code 不扫，只认 ~/.claude/skills，所以那一处再装一份。

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$ROOT/skills"

# 一条软链是不是本仓库装的，按目标的路径段认：落在本仓库任一 checkout 的 mmw-v4/skills/、
# mmw-v3/skills/，或 mmw-v2 装技能用的三个目录里。从哪个 checkout 运行本脚本，同名的就由哪个
# checkout 的 mmw-v4/skills/ 接管。
ours_skill_target() {
  case "$1" in
    */mmw-v4/skills/* | */mmw-v3/skills/* | */mmw-v2/upstream/skills/* | */mmw-v2/skills/* | */mmw-v2/upstream-diagram-design/skills/*) return 0 ;;
  esac
  return 1
}

# skills/ 下没有、该摘掉的：指回本仓库任何一版的技能软链。只有 v3 有的也摘，两版不混装；
# 退回 v3 时 mmw-v3/install.sh 会把它们装回来。
retired_skill_target() {
  ours_skill_target "$1"
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
  echo "mmw-v4 install: $1" >&2
  exit "${2:-1}"
}

mode=install
case "${1:-}" in
  --check) mode=check ;;
  --back) mode=back ;;
  "") ;;
  *) die "用法：install.sh [--check|--back]" 2 ;;
esac

# 装过之后记下是从哪个 checkout 装的（它的 mmw-v4 目录；v3、v2 装的记的是 mmw-v3、mmw-v2 目录）。
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

# ---------------- --back：退回 v3 ----------------
#
# mmw-v3/install.sh 只认指向 mmw-v3、mmw-v2 的软链；指向 mmw-v4 的同名技能软链与 CLAUDE.md 它当作
# 别人的东西，报冲突、跳过。models.json 里 v4 的 candidate 行 v3 的 models.py 不认，v3 的
# explainer、synthesizer 行 v4 装的时候摘掉了。所以先把这几样还原成 v3 认得的样子，再交给同一
# checkout 的 mmw-v3/install.sh 装。hook 的命令两版写的是同一条路径，v3 原地接管。
# 两家的 v4 提示词软链都先摘掉，防止 v3 的生成器沿 Codex 软链写进 v4 的源。

if [ "$mode" = back ]; then
  V3_ROOT="$(dirname "$ROOT")/mmw-v3"
  [ -f "$V3_ROOT/install.sh" ] || die "同一 checkout 里没有 mmw-v3/install.sh：$V3_ROOT"
  for dest in "${HOST_DIRS[@]}"; do
    [ -d "$dest" ] || continue
    for link in "$dest"/*; do
      [ -L "$link" ] || continue
      case "$(readlink "$link")" in
        */mmw-v4/skills/*) rm "$link"; echo "摘掉  $link" ;;
      esac
    done
  done
  for prompt in "$HOME_DIR/.claude/CLAUDE.md" "${CODEX_HOME:-$HOME_DIR/.codex}/AGENTS.md"; do
    if [ -L "$prompt" ]; then
      case "$(readlink "$prompt")" in
        */mmw-v4/prompt/*) rm "$prompt"; echo "摘掉  $prompt" ;;
      esac
    fi
  done
  # models.json：v3 不认的行摘掉；v3 要、这里没有的行，从 v4 安装时留的 .bak- 副本拿回来。
  # 副本里也没有的，交给 v3 的 install.sh 补默认值。
  MMW_HOME="${MMW_HOME:-$HOME_DIR/.mmw}" MMW_V3_ROLES="$V3_ROOT/skills/dispatch/roles.json" \
  python3 - <<'PY' || die "models.json 没还原成 v3 认得的样子，mmw-v3/install.sh 没跑"
import json
import os
from pathlib import Path

path = Path(os.environ["MMW_HOME"]) / "models.json"
if not path.is_file():
    raise SystemExit(0)
roles = json.loads(Path(os.environ["MMW_V3_ROLES"]).read_text(encoding="utf-8"))["roles"]
v3 = [r["name"] for r in roles if r.get("kind") == "session"]
config = json.loads(path.read_text(encoding="utf-8"))
rows = config.get("rows") or {}
backups = sorted(path.parent.glob(path.name + ".bak-*"))
saved = (json.loads(backups[-1].read_text(encoding="utf-8")).get("rows") or {}) if backups else {}
changed = False
for role in [r for r in rows if r not in v3]:
    del rows[role]
    print(f"摘掉  {path} 的 {role} 行（v3 没有这个角色）")
    changed = True
for role in v3:
    if role not in rows and role in saved:
        rows[role] = saved[role]
        print(f"拿回  {path} 的 {role} 行，从 {backups[-1].name}")
        changed = True
if changed:
    config["rows"] = rows
    config["version"] = int(config.get("version") or 0) + 1
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    scratch.replace(path)
PY
  echo "交给  $V3_ROOT/install.sh"
  exec bash "$V3_ROOT/install.sh"
fi

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
    done < <(stale_links "$dest" retired_skill_target "${wanted_names[@]}")
    continue
  fi

  mkdir -p "$dest"

  # 先清理：这个目录里指回本仓库（mmw-v4、mmw-v3、mmw-v2），skills/ 下却没有的软链，摘掉。
  # 目标不指回本仓库的一律不碰，宁可留着也不误删。
  while IFS= read -r stale; do
    [ -n "$stale" ] || continue
    rm "$stale"; echo "摘掉  $stale"
  done < <(stale_links "$dest" retired_skill_target "${wanted_names[@]}")

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

# 合并而不是覆盖：这几处别人也各装了自己的东西。只认 command 里带本脚本名与 gate 名的
# 那一条，认得出就换成新的，认不出就在后面添一条，别人的条目一个字不动。

HOOK_SRC="$SKILLS_SRC/dispatch/scripts/tool-guard.py"

if [ -f "$HOOK_SRC" ]; then
  hooks_ran=1
  MMW_MODE="$mode" \
  MMW_HOOK="$NEUTRAL_DIR/dispatch/scripts/tool-guard.py" \
  MMW_GUARD="$NEUTRAL_DIR/dispatch/scripts/turn-guard.py" \
  MMW_SESSION_START="$NEUTRAL_DIR/mmw-mode/scripts/session-start.py" \
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
SESSION_START = f"python3 '{os.environ['MMW_SESSION_START']}' "


def for_host(host, command):
    return command + host


# The tool each host calls to put a question on the screen: the matcher of its
# question gate.
QUESTION_TOOLS = {"claude": "AskUserQuestion", "codex": "request_user_input"}


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
    """Claude Code、Codex 都把处理器按 matcher 分组。

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
                if not ours(existing, command):
                    continue
                if len(inner) == 1 or group.get("matcher") == matcher:
                    inner[index] = handler
                    if matcher is None:
                        group.pop("matcher", None)
                    else:
                        group["matcher"] = matcher
                    save(path, data)
                    return
                inner.pop(index)
                break
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
                if existing == {"type": "command", "command": command, "timeout": timeout} \
                        and group.get("matcher") == matcher:
                    return True
        return False

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
# 记着。不再往某个文件写的时候，把它留在清单里：~/.cursor 与 ~/.grok 的三行就是这样留下的，
# v4 不再给这两个 host 装 hook，留着它们是为了把从前装的那几条摘干净。
MARK = f"'{neutral}/"

# 一行一处：文件、它的格式、整个文件是不是只有本仓库写。
# 只有本仓库写的那种，条目清空之后连文件一起删——grok 把 hooks/*.json 全部合并读入，
# 空壳留着不报错也不提示。cursor 格式的文件把处理器直接列在事件下面，不按 matcher 分组。
SWEPT = [
    (home / ".claude/settings.json", "grouped", False),
    (codex_home / "hooks.json", "grouped", False),
    (home / ".cursor/hooks.json", "cursor", False),
    (home / ".grok/hooks/mmw-verify-ticket.json", "grouped", True),
    (home / ".grok/hooks/mmw-turn-guard.json", "grouped", True),
]


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
# claude 与 codex 各只有一份配置，几条都写进去。
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


for host, host_home, path in grouped_hosts:
    command = for_host(host, SESSION_START)
    for event in ("SessionStart", "UserPromptSubmit"):
        point(host_home, path, event + " session-start.py",
              grouped(path, event, None, command, 2), command)
    point(host_home, path, "PreToolUse Bash",
          grouped(path, "PreToolUse", "Bash", for_host(host, COMMAND)), for_host(host, COMMAND))
    point(host_home, path, "PreToolUse " + QUESTION_TOOLS[host],
          grouped(path, "PreToolUse", QUESTION_TOOLS[host], for_host(host, QUESTION)),
          for_host(host, QUESTION))

for host, host_home, path in grouped_hosts:
    command = for_host(host, STOP)
    point(host_home, path, "Stop turn-guard.py",
          grouped(path, "Stop", None, command, GUARD_TIMEOUT), command)

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

# 两家的用户级入口都指向本次安装的 shared.md。安装前先停旧生成任务，避免它沿新软链写进源。

PROMPT_SRC="$ROOT/prompt"

# 一条软链该指哪里就指哪里；原位已有别的文件就是冲突。
link_prompt() {
  local link="$1" want="$2" generated="${3:-false}"
  if [ -L "$link" ]; then
    if [ "$(readlink "$link")" = "$want" ]; then return 0; fi
    case "$(readlink "$link")" in
      */mmw-v4/prompt/* | */mmw-v3/prompt/* | */mmw-v2/prompt/*) [ "$mode" = check ] || ln -sfn "$want" "$link"
        [ "$mode" != check ] || { echo "缺    $link 指向别的 checkout，跑一次 install.sh" >&2; return 1; }
        return 0 ;;
      *) echo "冲突  $link 是软链，指的不是本仓库，跳过" >&2; return 1 ;;
    esac
  fi
  if [ -e "$link" ]; then
    if [ "$generated" = true ] && [ -f "$link" ] && python3 - "$link" <<'PY'
import hashlib
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_bytes()
header = re.match(rb"^<!-- mmw prompt-sync: .* body-sha256=([0-9a-f]{64}) -->\n", text)
sys.exit(0 if header and hashlib.sha256(text[header.end():]).hexdigest().encode() == header[1] else 1)
PY
    then
      if [ "$mode" = check ]; then
        echo "缺    $link 还是生成文件，跑一次 install.sh 换成软链" >&2
        return 1
      fi
      ln -sfn "$want" "$link"
      return 0
    fi
    echo "冲突  $link 已存在且不是软链；把它的内容搬进 $want 再删掉它" >&2
    return 1
  fi
  if [ "$mode" = check ]; then echo "缺    $link" >&2; return 1; fi
  mkdir -p "$(dirname "$link")"
  ln -sfn "$want" "$link"
}

remove_prompt_sync() {
  local plist="$HOME_DIR/Library/LaunchAgents/com.mmw.prompt-sync.plist" job="gui/$(id -u)/com.mmw.prompt-sync" loaded=false
  if [ "$HOME_DIR" = "$HOME" ] && [ "$(uname)" = Darwin ] && launchctl print "$job" >/dev/null 2>&1; then
    loaded=true
  fi
  if [ "$mode" = check ]; then
    if [ -e "$plist" ] || [ -L "$plist" ] || [ "$loaded" = true ]; then
      echo "残留  com.mmw.prompt-sync（${plist}），跑一次 install.sh 摘掉" >&2
      return 1
    fi
    return 0
  fi
  if [ "$loaded" = true ]; then
    launchctl bootout "$job" >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
      launchctl print "$job" >/dev/null 2>&1 || break
      sleep 0.5
    done
    if launchctl print "$job" >/dev/null 2>&1; then
      echo "冲突  com.mmw.prompt-sync 仍在运行，提示词没迁移；先用 launchctl bootout $job 停掉它，再跑 install.sh" >&2
      return 1
    fi
  fi
  if [ -e "$plist" ] || [ -L "$plist" ]; then
    rm "$plist"
    echo "摘掉  $plist"
  fi
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
  remove_prompt_sync || prompt_rc=1
  if [ "$mode" = check ] || [ "$prompt_rc" -eq 0 ]; then
    if [ -d "$HOME_DIR/.claude" ]; then
      link_prompt "$HOME_DIR/.claude/CLAUDE.md" "$PROMPT_SRC/shared.md" || prompt_rc=1
    fi
    codex_home="${CODEX_HOME:-$HOME_DIR/.codex}"
    if [ -d "$codex_home" ]; then
      link_prompt "$codex_home/AGENTS.md" "$PROMPT_SRC/shared.md" true || prompt_rc=1
    fi
  fi
  if [ "$mode" != check ] && [ "$prompt_rc" -eq 0 ]; then
    echo "已装  提示词：Claude Code 与 Codex 的用户级入口都用软链读取 $PROMPT_SRC/shared.md"
  fi
  [ "$prompt_rc" -eq 0 ] || rc=1
else
  echo "缺    $PROMPT_SRC/shared.md" >&2
  rc=1
fi

# ---------------- task board LaunchAgent ----------------
#
# MMW_INSTALL_HOME 下只写或核 plist，绝不调用 launchctl；这让测试能验证同一份定义而不改变本机服务。
# 真家目录下由 launchd 守住 supervisor.py，后者再按 MMW_HOME/boards.json 守住各仓库的 board。

BOARD_PLIST="$HOME_DIR/Library/LaunchAgents/com.mmw.board.plist"
BOARD_SUPERVISOR="$ROOT/board/supervisor.py"
BOARD_PATH="$HOME_DIR/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
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
# host 侧只放生成物：CLI 软链、~/.paseo/config.json 里的 worktrees.root。本脚本从前往那份
# config.json 写过 grok、cursor 两条 provider；v4 不再服务这两个 host，所以装的时候摘掉它们，
# --check 见到就报残留。models.json 在 ~/.mmw/：第一次
# install 从 roles.json 每个角色的 default 写入，之后只动角色行。v3 的 explainer、synthesizer 行
# roles.json 没有，models.py 拒绝整份文件，所以摘掉，摘之前留一份 .bak- 副本（--back 从它拿回）；
# 缺的 candidate 行由 models.py 补默认值。别的行一字不动。不写 Agent profile。
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

RETIRED_PROVIDERS = ("grok", "cursor")


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


def retired_providers(data):
    providers = (data.get("agents") or {}).get("providers") or {}
    return [name for name in RETIRED_PROVIDERS if name in providers]


def merge(data):
    for name in retired_providers(data):
        del data["agents"]["providers"][name]
        print(f"摘掉  agents.providers.{name}（v4 不再服务这个 host）")
    worktrees = data.setdefault("worktrees", {})
    worktrees["root"] = worktrees_root
    data.setdefault("version", 1)
    return data


def drop_unknown_rows(path):
    """roles.json 没有的角色行摘掉，摘之前留一份 .bak- 副本。"""
    if not path.is_file():
        return
    with models.config_lock(purpose="drop rows of roles v4 does not have"):
        config = models.read_local_config()
        rows = config.get("rows")
        extra = [r for r in rows if r not in models.ALLOWED_AGENTS] if isinstance(rows, dict) else []
        if not extra:
            return
        backup_latest(path)
        for role in extra:
            del rows[role]
        config["version"] = int(config.get("version") or 0) + 1
        scratch = path.with_name(path.name + ".mmw-tmp")
        scratch.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        scratch.replace(path)
        print(f"摘掉  {path} 的 {', '.join(extra)} 行（v4 没有这些角色；原文件留在 .bak- 副本里）")


failed = False
try:
    config_file = models.models_json_path()
    if mode != "check":
        drop_unknown_rows(config_file)
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
    for name in retired_providers(data):
        sys.stderr.write(f"残留  {config_path} agents.providers.{name}：v4 不再服务这个 host，"
                         f"跑一次 install.sh 摘掉\n")
        failed = True
    have_root = ((data.get("worktrees") or {}).get("root"))
    if have_root != worktrees_root:
        sys.stderr.write(f"缺    worktrees.root 应为 {worktrees_root} 实为 {have_root}\n")
        failed = True
    sys.exit(1 if failed else 0)

data = merge(load(config_path))
save(config_path, data)
print(f"已装  {config_path}")
sys.exit(1 if failed else 0)
PY

# `paseo reload` 让 Paseo 读到本段摘掉的 provider。`worktrees.root` 不在——Paseo 只在启动时读它一次——所以改了它要重启
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

# ---------------- 子代理层数 ----------------
#
# 被派的 agent 该不该再派人，由开场提示末尾那一句管（It is your whole task …）；这里给两家
# host 的子代理层数定同一个上限 2，作兜底：主会话的子代理还能再派一层，再往下派不出来。
# dispatch 起的会话在它的 host 上也是主会话。两家默认不同：Claude Code 3（官方文档），
# Codex 1（codex-rs core/src/config/mod.rs 的 DEFAULT_AGENT_MAX_DEPTH）。
# host 没装（目录不在）就跳过。--back 不还原它。

MMW_DEPTH_MODE="$mode" \
MMW_DEPTH_HOME="$HOME_DIR" \
MMW_DEPTH_CODEX="${CODEX_HOME:-$HOME_DIR/.codex}" \
python3 - <<'PY' || rc=1
import json
import os
import re
import shutil
import sys
import tomllib
from datetime import datetime
from pathlib import Path

DEPTH = 2
mode = os.environ["MMW_DEPTH_MODE"]
home = Path(os.environ["MMW_DEPTH_HOME"])
codex_home = Path(os.environ["MMW_DEPTH_CODEX"])
failed = False


def backup_latest(path):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = path.with_name(path.name + ".bak-" + stamp)
    shutil.copy2(path, backup)
    for old in path.parent.glob(path.name + ".bak-*"):
        if old != backup and (old.is_file() or old.is_symlink()):
            old.unlink()


def replace_file(path, text):
    if path.is_file():
        if path.read_text(encoding="utf-8") == text:
            return
        backup_latest(path)
    scratch = path.with_name(path.name + ".mmw-tmp")
    scratch.write_text(text, encoding="utf-8")
    scratch.replace(path)


def claude(path):
    """settings.json 的 env 里 CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH。返回现在的值，装的时候先写上。"""
    key = "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except Exception as exc:
        sys.stderr.write(f"读不懂  {path}：{exc}\n")
        return None
    if mode != "check" and (data.get("env") or {}).get(key) != str(DEPTH):
        data.setdefault("env", {})[key] = str(DEPTH)
        replace_file(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return (data.get("env") or {}).get(key)


def toml_value(text, table, key):
    return (tomllib.loads(text).get(table) or {}).get(key)


def toml(path, table, key):
    """config.toml 的 [table] 里 key。别的行一个字不动；写坏了 host 起不来，所以写前先读回一遍。"""
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        now = toml_value(text, table, key)
    except Exception as exc:
        sys.stderr.write(f"读不懂  {path}：{exc}\n")
        return None
    if mode == "check" or now == DEPTH:
        return now
    line = f"{key} = {DEPTH}"
    header = re.search(rf"^\[{re.escape(table)}\][ \t]*$", text, re.M)
    if header and header.end() == len(text):
        text += "\n"
    if header:
        start = header.end() + 1
        nxt = re.search(r"^\[", text[start:], re.M)
        end = start + nxt.start() if nxt else len(text)
        body, n = re.subn(rf"^{re.escape(key)}\s*=.*$", line, text[start:end], flags=re.M)
        text = text[:start] + (body if n else line + "\n" + body) + text[end:]
    else:
        text = text.rstrip("\n") + ("\n\n" if text.strip() else "") + f"[{table}]\n{line}\n"
    try:
        written = toml_value(text, table, key)
    except Exception as exc:
        sys.stderr.write(f"没写  {path}：改完读不回来（{exc}），原文件没动\n")
        return now
    if written != DEPTH:
        sys.stderr.write(f"没写  {path}：[{table}] {key} 别处另有写法，改完仍是 {written}，原文件没动\n")
        return now
    path.parent.mkdir(parents=True, exist_ok=True)
    replace_file(path, text)
    return written


for host, where, got in (
    ("claude", home / ".claude", lambda: claude(home / ".claude/settings.json")),
    ("codex", codex_home, lambda: toml(codex_home / "config.toml", "agents", "max_depth")),
):
    if not where.is_dir():
        continue
    value = got()
    if str(value) == str(DEPTH):
        print(f"已装  {host} 子代理层数 {DEPTH}")
    else:
        sys.stderr.write(f"缺    {host} 子代理层数是 {value if value is not None else '默认'}，要 {DEPTH}：跑一次 install.sh\n")
        failed = True
sys.exit(1 if failed else 0)
PY

# ---------------- 本机基础工具 ----------------
#
# 夜里的脚本要调的几样：gh（且已登录）、git、python3、uv、node，以及起会话用的 runner，
# paseo、herdr、orca 至少一个。本脚本一样都不装，两种模式都只查：缺的报一行，说怎么装。
# 本机只在这一处查，setup-mmw 的 check.py 经 --check 读到它。

base_tool_hint() {
  case "$1" in
    gh) echo "brew install gh，再 gh auth login" ;;
    git) echo "xcode-select --install，或 brew install git" ;;
    python3) echo "brew install python" ;;
    uv) echo "brew install uv" ;;
    node) echo "brew install node" ;;
  esac
}

base_rc=0
for tool in gh git python3 uv node; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "缺    $tool 不在 PATH 上：$(base_tool_hint "$tool")" >&2
    base_rc=1
  fi
done
if command -v gh >/dev/null 2>&1; then
  if ! gh_out="$(gh auth status 2>&1)"; then
    gh_why="$(printf '%s\n' "$gh_out" | grep -v '^[[:space:]]*$' | head -n 1 | sed 's/^[[:space:]]*//' || true)"
    echo "缺    gh 没登录（${gh_why:-gh auth status 退出非 0}）：跑 gh auth login" >&2
    base_rc=1
  fi
fi
base_runners=()
for runner in paseo herdr orca; do
  if PATH="$HOME_DIR/.local/bin:$PATH" command -v "$runner" >/dev/null 2>&1; then
    base_runners+=("$runner")
  fi
done
if [ "${#base_runners[@]}" -eq 0 ]; then
  echo "缺    runner：paseo、herdr、orca 都不在 PATH 上，夜里的会话靠其中一个起。装 Orca、Herdr 或" \
       "Paseo 的应用，把它的命令行放上 PATH；Paseo.app 装好后再跑一次 install.sh，它把 paseo 链进 ~/.local/bin" >&2
  base_rc=1
fi
if [ "$base_rc" -eq 0 ]; then
  echo "已装  基础工具：gh 已登录，git、python3、uv、node 在 PATH 上，runner ${base_runners[*]}"
else
  rc=1
fi

# ---------------- Orca 侧工作树配置 ----------------
#
# 协议自己用 git 切工作树，落点是每个仓库的 `.worktrees/`。这一条让 Orca 自己建的树也落在
# 同一处。读的是 Orca 此刻的每个 setup：装完之后才加进 Orca 的仓库，下一次 install 补上，
# 每一次 --check 都报出来。没有 orca 的机器跳过。

if command -v orca >/dev/null 2>&1; then
  MMW_MODE="$mode" python3 - <<'PY' || rc=1
import json
import os
import subprocess
import sys

BASE = ".worktrees"
mode = os.environ["MMW_MODE"]


def orca(*args):
    return subprocess.run(["orca", *args], check=False, capture_output=True, text=True)


proc = orca("project", "setups", "--json")
try:
    setups = json.loads(proc.stdout)["result"]["setups"]
except Exception:
    sys.stderr.write(f"缺    读不出 orca project setups --json（退出 {proc.returncode}），"
                     f"worktree-base-path 没{'查' if mode == 'check' else '写'}\n")
    sys.exit(1)
rows = [row for row in setups if isinstance(row, dict) and row.get("id")]
wrong = [row for row in rows if row.get("worktreeBasePath") != BASE]


def where(row):
    path = row.get("path") or row.get("displayName")
    return f"orca setup {row['id']}" + (f"（{path}）" if path else "")


if mode == "check":
    for row in wrong:
        sys.stderr.write(f"缺    {where(row)}的 worktree-base-path 是 {row.get('worktreeBasePath')!r}，"
                         f"要 {BASE}：跑一次 install.sh\n")
    if not wrong:
        print(f"已装  orca 的 {len(rows)} 个 setup，worktree-base-path 都是 {BASE}")
    sys.exit(1 if wrong else 0)

failed = False
for row in wrong:
    ident = str(row["id"])
    if orca("project", "setup-update", "--setup", ident, "--worktree-base-path", BASE,
            "--json").returncode:
        sys.stderr.write(f"缺    {where(row)}的 worktree-base-path 没写上：手动跑 "
                         f"orca project setup-update --setup {ident} --worktree-base-path {BASE}\n")
        failed = True
    else:
        print(f"已装  {where(row)} worktree-base-path {BASE}")
sys.exit(1 if failed else 0)
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
  echo "技能目录：${SKILLS_SRC}"
  echo "改技能直接改这个目录里的文件，host 下次调用就是新的。"
  echo "装自  ${ROOT}（记在 ${INSTALLED_ROOT_FILE}；别的 checkout 跑 --check 时按它核对）"
fi

exit "$rc"
