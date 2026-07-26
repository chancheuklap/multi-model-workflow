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

# commands exist
n=$(ls "$PLUGIN/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$n" = 11 ] && ok "11 commands" || no "commands count=$n"

exit "$fail"
