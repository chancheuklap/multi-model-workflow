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
[ ! -d "$PLUGIN/workflows" ] && ok "no foreign workflow artifact directory" || no "unexpected workflows directory"

[ "$(jq -r .name "$PLUGIN/.factory-plugin/plugin.json")" = multi-model-workflow-droid ] &&
  ok "dedicated plugin identity" || no "plugin identity"
jq -e '.hooks.PreToolUse[].matcher == "Execute" and .hooks.PostToolUse[].matcher == "Execute"' \
  "$PLUGIN/hooks/hooks.json" >/dev/null && ok "Droid hook matchers" || no "hook matchers"

for d in investigate-topic investigate-synthesizer code-explorer decision-advisor plan-writer pack-executor pack-executor-capable reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b; do
  file="$PLUGIN/droids/$d.md"
  [ -f "$file" ] || { no "missing droid $d"; continue; }
  grep -q '^description: ' "$file" || no "missing description $d"
  grep -q '^model: ' "$file" || no "missing model $d"
  grep -q '^tools: ' "$file" || no "missing tools $d"
  if [ "$d" = investigate-synthesizer ]; then
    grep -q '^mcpServers: \[\]$' "$file" || no "synthesizer 不得获得 MCP"
  else
    grep -q '^mcpServers: \["serena", "graphify"\]$' "$file" || no "missing serena/graphify grant $d"
  fi
done
[ "$fail" -eq 0 ] && ok "all role droids present"

MARKETPLACE="$PLUGIN/../.factory-plugin/marketplace.json"
[ "$(jq '.plugins | length' "$MARKETPLACE")" = 1 ] \
  && [ "$(jq -r '.plugins[0].source' "$MARKETPLACE")" = "./droid-plugin" ] \
  && ok "marketplace only publishes standalone Droid plugin" || no "marketplace contains legacy plugin"
[ "$(jq -r .version "$PLUGIN/.factory-plugin/plugin.json")" = "$(jq -r '.plugins[0].version' "$MARKETPLACE")" ] \
  && ok "plugin and marketplace versions match" || no "plugin version drift"

grep -q '/approve-design' "$PLUGIN/skills/orchestrate/references/design/design-self-check.md" \
  && ok "design self-check routes through the human gate" || no "design self-check bypasses human gate"
grep -q '任意消息即恢复 attended' "$PLUGIN/commands/unattended.md" \
  && ok "unattended exit semantics are explicit" || no "unattended semantics drift"
grep -q '执行者 agent 在任务中途咨询的更强审查者' "$PLUGIN/droids/decision-advisor.md" \
  && grep -q '对你自己判断的最强反方论点' "$PLUGIN/droids/decision-advisor.md" \
  && ok "advisor prompt preserves judgment contract" || no "advisor prompt contract"
for d in reviewer-final-a reviewer-final-b; do
  grep -q 'stage 和视角完全由 dispatch prompt 指定' "$PLUGIN/droids/$d.md" \
    || no "$d hardcodes final baseline"
  grep -q '"Execute"' "$PLUGIN/droids/$d.md" || no "$d lacks verification tool"
done

exit "$fail"
