#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

[ -f "$PLUGIN/.cursor-plugin/plugin.json" ] && ok "Cursor manifest exists" || no "Cursor manifest"
[ ! -d "$PLUGIN/extensions" ] && ok "no Pi extensions" || no "unexpected extensions"
[ ! -d "$PLUGIN/workflows" ] && ok "no workflows dir" || no "unexpected workflows"
[ ! -f "$PLUGIN/scripts/render_agent_prompts.py" ] && ok "no render_agent_prompts" || no "render script leaked"
[ ! -f "$PLUGIN/scripts/lib/droid-exec.sh" ] && ok "no droid-exec" || no "droid-exec leaked"
[ ! -f "$PLUGIN/agents/decision-advisor.md" ] && ok "no decision-advisor" || no "decision-advisor leaked"

[ "$(jq -r .name "$PLUGIN/.cursor-plugin/plugin.json")" = multi-model-workflow-cursor ] &&
  ok "dedicated plugin identity" || no "plugin identity"

jq -e '.hooks.sessionStart and .hooks.beforeShellExecution and .hooks.afterShellExecution' \
  "$PLUGIN/hooks/hooks.json" >/dev/null && ok "Cursor hook events" || no "hook events"

for d in investigate-topic investigate-synthesizer code-explorer plan-writer pack-executor pack-executor-capable \
  reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b advisor; do
  file="$PLUGIN/agents/$d.md"
  [ -f "$file" ] || { no "missing agent $d"; continue; }
  grep -q '^description: ' "$file" || no "missing description $d"
  grep -q '^model: ' "$file" || no "missing model $d"
  ! grep -q 'contact_supervisor' "$file" || no "contact_supervisor in $d"
  ! grep -q 'mmw:fragments BEGIN' "$file" || no "fragment block in $d"
done
[ "$fail" -eq 0 ] && ok "all role agents present"

grep -q 'advisor-strategy pattern' "$PLUGIN/agents/advisor.md" \
  && ok "advisor system prompt present" || no "advisor prompt"

grep -q 'AskQuestion' "$PLUGIN/scripts/lib/runtime.sh" \
  && grep -q 'cursor-task' "$PLUGIN/scripts/lib/runtime.sh" \
  && ok "runtime Cursor constants" || no "runtime constants"

grep -q 'cmd_adopt' "$PLUGIN/scripts/prepare.sh" \
  && ok "task adopt exists" || no "task adopt"

grep -q 'investigate)' "$PLUGIN/scripts/mmw.sh" \
  && ok "mmw investigate wired" || no "investigate wire"

# locate must not probe foreign hosts
! grep -qE '\.pi/agent/settings|\.factory/plugins|claude-plugin' \
  "$PLUGIN/build/fragments/locate-mmw.md" \
  && ok "locate is Cursor-only" || no "locate probes foreign hosts"

exit "$fail"
