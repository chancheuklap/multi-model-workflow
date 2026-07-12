#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

[ -f "$PLUGIN/.factory-plugin/plugin.json" ] && ok "Factory manifest exists" || no "Factory manifest"
legacy_manifest=".$(printf 'cl%s' 'aude')-plugin"
[ ! -d "$PLUGIN/$legacy_manifest" ] && ok "single native manifest" || no "unexpected compatibility manifest"
[ ! -d "$PLUGIN/agents" ] && ok "only droids directory" || no "unexpected agents directory"
[ ! -d "$PLUGIN/workflows" ] && ok "Task replaces workflow scripts" || no "unexpected workflows directory"

patterns='CLAUDE_''PLUGIN_ROOT|MMW_''HOST|AskUser''Question|Enter''Worktree|codex ''exec|codex-''session|codex-''logs|CODEX_''|Workflow''\(|\.claude''/'
if grep -RInE "$patterns" "$PLUGIN" --exclude='test_droid_native.sh' >/tmp/mmw-native-residue.$$; then
  cat /tmp/mmw-native-residue.$$
  no "native residue scan"
else
  ok "native residue scan"
fi
rm -f /tmp/mmw-native-residue.$$

[ "$(jq -r .name "$PLUGIN/.factory-plugin/plugin.json")" = multi-model-workflow-droid ] &&
  ok "dedicated plugin identity" || no "plugin identity"
jq -e '.hooks.PreToolUse[].matcher == "Execute" and .hooks.PostToolUse[].matcher == "Execute"' \
  "$PLUGIN/hooks/hooks.json" >/dev/null && ok "Droid hook matchers" || no "hook matchers"

for d in investigate-topic code-explorer decision-advisor plan-writer pack-executor reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b; do
  [ -f "$PLUGIN/droids/$d.md" ] || no "missing droid $d"
done
[ "$fail" -eq 0 ] && ok "all role droids present"

exit "$fail"
