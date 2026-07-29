#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

SKILL="$PLUGIN/skills/orchestrate/SKILL.md"
FRAG="$PLUGIN/build/fragments/locate-mmw.md"
[ -f "$FRAG" ] || { echo "missing locate fragment"; exit 1; }
grep -q 'CURSOR_PLUGIN_ROOT\|plugins/local/multi-model-workflow-cursor\|cursor-plugin' "$FRAG" \
  && ok "locate mentions Cursor install" || no "locate Cursor"
! grep -qE '\.pi/agent/settings|pi-plugin/\?\$|\.factory/plugins' "$FRAG" \
  && ok "locate does not probe foreign hosts" || no "foreign probe"

# commands exist + Cursor frontmatter
n=$(ls "$PLUGIN/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = 11 ] && ok "11 commands" || no "commands count=$n"

expected='approve-design attended force-validate gather-context progress reassess replan-remaining rescope side-finding skip-current unattended'
for name in $expected; do
  f="$PLUGIN/commands/$name.md"
  [ -f "$f" ] || { no "missing $name.md"; continue; }
  awk '
    BEGIN { in_fm=0; name=""; desc="" }
    /^---[[:space:]]*$/ { if (++in_fm == 1) next; exit }
    in_fm == 1 && $1 ~ /^name:/ { sub(/^name:[[:space:]]*/, ""); name=$0 }
    in_fm == 1 && $1 ~ /^description:/ { sub(/^description:[[:space:]]*/, ""); desc=$0 }
    END {
      if (name == "'"$name"'" && length(desc) > 0) exit 0
      exit 1
    }
  ' "$f" && ok "frontmatter $name" || no "frontmatter $name (need name+description)"
done

[ -x "$PLUGIN/scripts/install-local-surface.sh" ] \
  && ok "install-local-surface.sh present" || no "missing install-local-surface.sh"

# 本地试装：插件本体与 commands 均为软链（沙箱跑一遍，不碰真实 ~/.cursor）
INSTALL="$PLUGIN/scripts/install-local-surface.sh"
SANDBOX="$(mktemp -d)"
# 注意：本文件末尾 exit 前清沙箱；不用 EXIT trap，避免覆盖其他清理
mkdir -p "$SANDBOX/local" "$SANDBOX/commands"
# 先放一个实体假拷贝，确认脚本会拆掉并改成软链
mkdir -p "$SANDBOX/local/multi-model-workflow-cursor"
echo stale > "$SANDBOX/local/multi-model-workflow-cursor/stale.txt"
# 再放一个实体命令文件，确认会被换成软链
echo stale-cmd > "$SANDBOX/commands/approve-design.md"
HOOKS_JSON="$SANDBOX/hooks.json"
printf '%s\n' '{"version":1,"hooks":{}}' > "$HOOKS_JSON"
if CURSOR_LOCAL_PLUGIN="$SANDBOX/local/multi-model-workflow-cursor" \
   CURSOR_USER_COMMANDS="$SANDBOX/commands" \
   CURSOR_USER_HOOKS="$HOOKS_JSON" \
   bash "$INSTALL" >/dev/null; then
  plugin_real="$(python3 -c "import os; print(os.path.realpath(r'''$SANDBOX/local/multi-model-workflow-cursor'''))")"
  src_real="$(python3 -c "import os; print(os.path.realpath(r'''$PLUGIN'''))")"
  if [ -L "$SANDBOX/local/multi-model-workflow-cursor" ] \
    && [ "$plugin_real" = "$src_real" ] \
    && [ ! -e "$SANDBOX/local/multi-model-workflow-cursor/stale.txt" ]; then
    ok "install links plugin (replaces entity copy)"
  else
    no "install did not symlink plugin to source"
  fi
  cmd_real="$(python3 -c "import os; print(os.path.realpath(r'''$SANDBOX/commands/approve-design.md'''))")"
  cmd_expect="$(python3 -c "import os; print(os.path.realpath(r'''$PLUGIN/commands/approve-design.md'''))")"
  if [ -L "$SANDBOX/commands/approve-design.md" ] && [ "$cmd_real" = "$cmd_expect" ]; then
    ok "install symlinks slash commands"
  else
    no "install command symlink broken"
  fi
  # 幂等：再跑一次仍指向同一源
  CURSOR_LOCAL_PLUGIN="$SANDBOX/local/multi-model-workflow-cursor" \
    CURSOR_USER_COMMANDS="$SANDBOX/commands" \
    CURSOR_USER_HOOKS="$HOOKS_JSON" \
    bash "$INSTALL" >/dev/null
  plugin_real2="$(python3 -c "import os; print(os.path.realpath(r'''$SANDBOX/local/multi-model-workflow-cursor'''))")"
  [ -L "$SANDBOX/local/multi-model-workflow-cursor" ] && [ "$plugin_real2" = "$src_real" ] \
    && ok "install symlink idempotent" || no "install not idempotent"
else
  no "install-local-surface failed in sandbox"
fi
rm -rf "$SANDBOX"

jq -e '.commands == "./commands/"' "$PLUGIN/.cursor-plugin/plugin.json" >/dev/null \
  && ok "plugin.json declares commands" || no "plugin.json commands"

# Cursor 生效面纪律：禁止调用 enter_worktree({...})；investigate 必须 run_in_background
! rg -n 'enter_worktree\(\{' "$PLUGIN" --glob '!**/scripts/tests/**' >/dev/null \
  && ok "no enter_worktree({...}) calls" || no "enter_worktree({...}) still present"
! rg -n '(^|[^_])background:true' "$PLUGIN/scripts/investigate.sh" >/dev/null \
  && rg -n 'run_in_background:true' "$PLUGIN/scripts/investigate.sh" >/dev/null \
  && ok "investigate DISPATCH uses run_in_background" || no "investigate DISPATCH param"
! rg -n 'advisor\(\)|零参数' "$PLUGIN/agents/advisor.md" "$PLUGIN/skills/orchestrate" >/dev/null \
  && ok "no advisor() zero-arg lies" || no "advisor zero-arg residue"

exit "$fail"
