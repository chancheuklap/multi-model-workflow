#!/usr/bin/env bash
# 把 cursor-plugin 复制到 Cursor 用户级原生加载面 + 引擎树。
# 落点：agents / skills / commands / rules / hooks / hooks.json / mcp.json /
#       ~/.cursor/multi-model-workflow-engine
# 组件一律复制（hooks.json / mcp.json 须合并）。
set -euo pipefail

PLUGIN_SRC="$(cd "$(dirname "$0")/.." && pwd)"
USER_AGENTS="${CURSOR_USER_AGENTS:-$HOME/.cursor/agents}"
USER_SKILLS="${CURSOR_USER_SKILLS:-$HOME/.cursor/skills}"
USER_COMMANDS="${CURSOR_USER_COMMANDS:-$HOME/.cursor/commands}"
USER_RULES="${CURSOR_USER_RULES:-$HOME/.cursor/rules}"
USER_HOOKS_DIR="${CURSOR_USER_HOOKS_DIR:-$HOME/.cursor/hooks}"
USER_HOOKS_JSON="${CURSOR_USER_HOOKS:-$HOME/.cursor/hooks.json}"
USER_MCP_JSON="${CURSOR_USER_MCP:-$HOME/.cursor/mcp.json}"
ENGINE_ROOT="${MMW_ENGINE_ROOT:-$HOME/.cursor/multi-model-workflow-engine}"

die() { echo "ERROR: $*" >&2; exit 1; }

[ -f "$PLUGIN_SRC/.cursor-plugin/plugin.json" ] \
  || die "不是 cursor-plugin 根:$PLUGIN_SRC(缺 .cursor-plugin/plugin.json)"

copy_file() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [ -L "$dest" ] || [ -e "$dest" ]; then
    rm -f "$dest"
  fi
  cp "$src" "$dest"
}

# --- agents ---
mkdir -p "$USER_AGENTS"
agent_n=0
for f in "$PLUGIN_SRC"/agents/*.md; do
  [ -f "$f" ] || continue
  copy_file "$f" "$USER_AGENTS/$(basename "$f")"
  agent_n=$((agent_n + 1))
done

# --- skills ---
mkdir -p "$USER_SKILLS"
skill_n=0
for d in "$PLUGIN_SRC"/skills/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  mkdir -p "$USER_SKILLS/$name"
  rsync -a --delete --exclude '.DS_Store' "$d" "$USER_SKILLS/$name/"
  skill_n=$((skill_n + 1))
done

# --- commands ---
mkdir -p "$USER_COMMANDS"
cmd_n=0
for f in "$PLUGIN_SRC"/commands/*.md; do
  [ -f "$f" ] || continue
  copy_file "$f" "$USER_COMMANDS/$(basename "$f")"
  cmd_n=$((cmd_n + 1))
done

# --- rules ---
mkdir -p "$USER_RULES"
rule_n=0
for f in "$PLUGIN_SRC"/rules/*.mdc; do
  [ -f "$f" ] || continue
  copy_file "$f" "$USER_RULES/$(basename "$f")"
  rule_n=$((rule_n + 1))
done

# --- hooks scripts ---
mkdir -p "$USER_HOOKS_DIR"
for f in session-triage.sh guard-redline.sh record-step.sh; do
  [ -f "$PLUGIN_SRC/hooks/$f" ] || die "缺 hooks/$f"
  copy_file "$PLUGIN_SRC/hooks/$f" "$USER_HOOKS_DIR/$f"
  chmod +x "$USER_HOOKS_DIR/$f"
done

# --- engine tree ---
mkdir -p "$ENGINE_ROOT"
rsync -a --delete --exclude '.DS_Store' --exclude 'scripts/tests/*.tmp' \
  "$PLUGIN_SRC/scripts/" "$ENGINE_ROOT/scripts/"
rsync -a --delete --exclude '.DS_Store' \
  "$PLUGIN_SRC/state-schema/" "$ENGINE_ROOT/state-schema/"
rsync -a --delete --exclude '.DS_Store' \
  "$PLUGIN_SRC/config/" "$ENGINE_ROOT/config/"
mkdir -p "$ENGINE_ROOT/skills"
rsync -a --delete --exclude '.DS_Store' \
  "$PLUGIN_SRC/skills/graphify/" "$ENGINE_ROOT/skills/graphify/"
mkdir -p "$ENGINE_ROOT/.cursor-plugin"
cp "$PLUGIN_SRC/.cursor-plugin/plugin.json" "$ENGINE_ROOT/.cursor-plugin/plugin.json"

# --- merge hooks.json ---
python3 - "$USER_HOOKS_JSON" "$USER_HOOKS_DIR" <<'PY'
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
    if "multi-model-workflow-cursor/hooks/" in c:
        return True
    if "/.cursor/hooks/" in c or c.endswith(
        tuple(f"/hooks/{name}" for name in (
            "session-triage.sh", "guard-redline.sh", "record-step.sh"
        ))
    ):
        # only claim known MMW script basenames
        return any(c.endswith(name) for name in (
            "session-triage.sh", "guard-redline.sh", "record-step.sh"
        ))
    return False

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

# --- merge mcp.json (MMW servers from source; keep user others) ---
python3 - "$USER_MCP_JSON" "$PLUGIN_SRC/mcp.json" <<'PY'
import json, sys
from pathlib import Path

user_path = Path(sys.argv[1])
src_path = Path(sys.argv[2])
src = json.loads(src_path.read_text())
mmw_servers = src.get("mcpServers") or {}
existing = {"mcpServers": {}}
if user_path.is_file():
    existing = json.loads(user_path.read_text())
    if not isinstance(existing, dict):
        raise SystemExit(f"ERROR: {user_path} is not a JSON object")
    existing.setdefault("mcpServers", {})

servers = dict(existing.get("mcpServers") or {})
for name, conf in mmw_servers.items():
    servers[name] = conf
out = dict(existing)
out["mcpServers"] = servers
user_path.parent.mkdir(parents=True, exist_ok=True)
user_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(f"merged MMW mcpServers -> {user_path} ({', '.join(sorted(mmw_servers))})")
PY

echo "synced agents ($agent_n) -> $USER_AGENTS"
echo "synced skills ($skill_n) -> $USER_SKILLS"
echo "synced commands ($cmd_n) -> $USER_COMMANDS"
echo "synced rules ($rule_n) -> $USER_RULES"
echo "synced hooks -> $USER_HOOKS_DIR"
echo "synced engine -> $ENGINE_ROOT"

if command -v uv >/dev/null 2>&1 && [ "${MMW_INSTALL_SKIP_UV:-}" != "1" ]; then
  for pkg in serena-agent graphifyy; do
    if ! uv tool list 2>/dev/null | grep -q "^${pkg} "; then
      echo "installing uv tool $pkg ..."
      uv tool install "$pkg" || echo "WARN: uv tool install $pkg 失败，首次开 MCP 时会再试"
    fi
  done
elif [ "${MMW_INSTALL_SKIP_UV:-}" = "1" ]; then
  :
else
  echo "WARN: 未找到 uv；请先安装 uv，否则 Serena/Graphify MCP 无法拉取上游 CLI"
fi

echo "next: Reload Window 后 slash 命令、hooks、MCP 与 ~/.cursor/agents 花名册应生效。"
