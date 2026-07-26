#!/usr/bin/env bash
# 把 cursor-plugin 接到本机真正会生效的 Cursor 加载面。
# 1) ~/.cursor/plugins/local/multi-model-workflow-cursor  — 插件本体
# 2) ~/.cursor/commands/                                  — slash 命令可靠面
# 3) ~/.cursor/hooks.json                                 — 合并 MMW hooks（保留 herdr 等非 MMW 条目）
set -euo pipefail

PLUGIN_SRC="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_PLUGIN="${CURSOR_LOCAL_PLUGIN:-$HOME/.cursor/plugins/local/multi-model-workflow-cursor}"
USER_COMMANDS="${CURSOR_USER_COMMANDS:-$HOME/.cursor/commands}"
USER_HOOKS="${CURSOR_USER_HOOKS:-$HOME/.cursor/hooks.json}"
HOOK_DIR="$LOCAL_PLUGIN/hooks"

mkdir -p "$(dirname "$LOCAL_PLUGIN")" "$USER_COMMANDS"

rsync -a --delete \
  --exclude '.DS_Store' \
  --exclude 'scripts/tests/*.tmp' \
  "$PLUGIN_SRC/" "$LOCAL_PLUGIN/"

for f in "$PLUGIN_SRC"/commands/*.md; do
  cp "$f" "$USER_COMMANDS/$(basename "$f")"
done

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

echo "synced plugin -> $LOCAL_PLUGIN"
echo "synced $(ls "$PLUGIN_SRC"/commands/*.md | wc -l | tr -d ' ') commands -> $USER_COMMANDS"
echo "next: Settings 确认「Include third-party Plugins, Skills, and other configs」按需开启；Reload Window 后 /approve-design 与红线应可用。"
