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
