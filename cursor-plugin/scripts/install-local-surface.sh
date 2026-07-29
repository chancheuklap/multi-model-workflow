#!/usr/bin/env bash
# 把 cursor-plugin 接到本机真正会生效的 Cursor 加载面。
# 1) ~/.cursor/plugins/local/multi-model-workflow-cursor  — 软链到本仓库 cursor-plugin/
# 2) ~/.cursor/commands/                                  — 各 slash 命令软链到插件 commands/
# 3) ~/.cursor/hooks.json                                 — 合并 MMW hooks（保留非 MMW 条目）
#
# 软链后改仓库源码即可；新装或换仓库路径时再跑本脚本。Reload Window 后生效。
set -euo pipefail

PLUGIN_SRC="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_PLUGIN="${CURSOR_LOCAL_PLUGIN:-$HOME/.cursor/plugins/local/multi-model-workflow-cursor}"
USER_COMMANDS="${CURSOR_USER_COMMANDS:-$HOME/.cursor/commands}"
USER_HOOKS="${CURSOR_USER_HOOKS:-$HOME/.cursor/hooks.json}"
HOOK_DIR="$LOCAL_PLUGIN/hooks"

die() { echo "ERROR: $*" >&2; exit 1; }

[ -f "$PLUGIN_SRC/.cursor-plugin/plugin.json" ] \
  || die "不是 cursor-plugin 根:$PLUGIN_SRC(缺 .cursor-plugin/plugin.json)"

mkdir -p "$(dirname "$LOCAL_PLUGIN")" "$USER_COMMANDS"

# 插件本体：软链到源码树。已有实体目录(旧 rsync 拷贝)先拆掉再链。
# rm 软链只删链接不碰目标；rm 实体目录只删旧拷贝。
if [ -e "$LOCAL_PLUGIN" ] || [ -L "$LOCAL_PLUGIN" ]; then
  if [ -L "$LOCAL_PLUGIN" ]; then
    cur="$(readlink "$LOCAL_PLUGIN")"
    case "$cur" in
      /*) ;;
      *) cur="$(cd "$(dirname "$LOCAL_PLUGIN")" && cd "$(dirname "$cur")" && pwd)/$(basename "$cur")" ;;
    esac
    if [ "$cur" = "$PLUGIN_SRC" ]; then
      : # 已指向本源，保持
    else
      rm -f "$LOCAL_PLUGIN"
      ln -s "$PLUGIN_SRC" "$LOCAL_PLUGIN"
    fi
  else
    rm -rf "$LOCAL_PLUGIN"
    ln -s "$PLUGIN_SRC" "$LOCAL_PLUGIN"
  fi
else
  ln -s "$PLUGIN_SRC" "$LOCAL_PLUGIN"
fi

[ -L "$LOCAL_PLUGIN" ] || die "本地插件位不是软链:$LOCAL_PLUGIN"
[ -f "$LOCAL_PLUGIN/.cursor-plugin/plugin.json" ] \
  || die "软链无法解析到插件:$LOCAL_PLUGIN → $PLUGIN_SRC"

# slash 命令：用户级目录各文件软链到插件 commands/（改命令文件即时可见）
shopt -s nullglob
for f in "$PLUGIN_SRC"/commands/*.md; do
  name="$(basename "$f")"
  dest="$USER_COMMANDS/$name"
  if [ -L "$dest" ] || [ -e "$dest" ]; then
    rm -f "$dest"
  fi
  ln -s "$f" "$dest"
  [ -L "$dest" ] || die "命令软链失败:$dest"
done
cmd_n=$(ls "$PLUGIN_SRC"/commands/*.md 2>/dev/null | wc -l | tr -d ' ')

python3 - "$USER_HOOKS" "$HOOK_DIR" <<'PY'
import json, sys
from pathlib import Path

hooks_path = Path(sys.argv[1])
hook_dir = Path(sys.argv[2])

def cmd(script: str) -> str:
    return f"bash '{hook_dir / script}'"

mmw = {
    "sessionStart": [{"command": cmd("session-triage.sh")}],
    "preCompact": [{"command": cmd("session-triage.sh")}],
    "beforeShellExecution": [{"command": cmd("guard-redline.sh"), "failClosed": True}],
    "afterShellExecution": [{"command": cmd("record-step.sh")}],
}

existing = {"version": 1, "hooks": {}}
if hooks_path.is_file():
    existing = json.loads(hooks_path.read_text())
    if not isinstance(existing, dict):
        raise SystemExit(f"ERROR: {hooks_path} is not a JSON object")
    existing.setdefault("version", 1)
    existing.setdefault("hooks", {})

def is_mmw(entry: dict) -> bool:
    c = str(entry.get("command", ""))
    return "multi-model-workflow-cursor/hooks/" in c or c.endswith(
        tuple(f"/hooks/{name}" for name in (
            "session-triage.sh", "guard-redline.sh", "record-step.sh"
        ))
    )

merged_hooks = {}
all_events = set(existing.get("hooks", {})) | set(mmw)
for event in sorted(all_events):
    kept = []
    for entry in existing.get("hooks", {}).get(event, []) or []:
        if isinstance(entry, dict) and not is_mmw(entry):
            kept.append(entry)
    kept.extend(mmw.get(event, []))
    if kept:
        merged_hooks[event] = kept

out = {"version": int(existing.get("version", 1)), "hooks": merged_hooks}
hooks_path.parent.mkdir(parents=True, exist_ok=True)
hooks_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(f"merged MMW hooks -> {hooks_path}")
for ev, arr in merged_hooks.items():
    print(f"  {ev}: {len(arr)} hook(s)")
PY

echo "linked plugin -> $LOCAL_PLUGIN"
echo "  target: $PLUGIN_SRC"
echo "linked $cmd_n commands -> $USER_COMMANDS (symlinks)"

# Cursor 本机上游 CLI：缺则安装。Serena/Graphify skill 与 MCP 包装器只活在本插件内，
# 不往 ~/.agents、~/.local/bin、其他 harness 目录做跨宿主软链。
if command -v uv >/dev/null 2>&1; then
  for pkg in serena-agent graphifyy; do
    if ! uv tool list 2>/dev/null | grep -q "^${pkg} "; then
      echo "installing uv tool $pkg ..."
      uv tool install "$pkg" || echo "WARN: uv tool install $pkg 失败，首次开 MCP 时会再试"
    fi
  done
else
  echo "WARN: 未找到 uv；请先安装 uv，否则 Serena/Graphify MCP 无法拉取上游 CLI"
fi

echo "next: Settings 确认「Include third-party Plugins, Skills, and other configs」按需开启；Reload Window 后 /approve-design、Serena/Graphify MCP 与红线应可用。"
