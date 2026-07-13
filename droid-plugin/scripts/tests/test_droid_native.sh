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

for d in investigate-topic investigate-synthesizer code-explorer decision-advisor plan-writer pack-executor pack-executor-capable reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b; do
  file="$PLUGIN/droids/$d.md"
  [ -f "$file" ] || { no "missing droid $d"; continue; }
  grep -q '^description: ' "$file" || no "missing description $d"
  grep -q '^model: ' "$file" || no "missing model $d"
  grep -q '^tools: ' "$file" || no "missing tools $d"
  grep -q '^mcpServers: \[\]' "$file" || no "unbounded MCP access $d"
  [ "$(awk 'BEGIN{n=0} /^---$/{n++;next} n>=2{c+=length($0)} END{print c+0}' "$file")" -ge 120 ] \
    || no "thin prompt $d"
done
[ "$fail" -eq 0 ] && ok "all role droids present"

MARKETPLACE="$PLUGIN/../.factory-plugin/marketplace.json"
[ "$(jq '.plugins | length' "$MARKETPLACE")" = 1 ] \
  && [ "$(jq -r '.plugins[0].source' "$MARKETPLACE")" = "./droid-plugin" ] \
  && ok "marketplace only publishes standalone Droid plugin" || no "marketplace contains legacy plugin"
[ "$(jq -r .version "$PLUGIN/.factory-plugin/plugin.json")" = "$(jq -r '.plugins[0].version' "$MARKETPLACE")" ] \
  && ok "plugin and marketplace versions match" || no "plugin version drift"

grep -q 'checkpoint prepare' "$PLUGIN/skills/orchestrate/references/design/design-self-check.md" \
  && ok "design self-check routes through checkpoint" || no "design self-check bypasses checkpoint"
grep -q '普通用户消息不改变该模式' "$PLUGIN/commands/unattended.md" \
  && ok "unattended exit semantics are explicit" || no "unattended semantics drift"
if grep -Eq 'run_in_background|task-record|Task 的 resume=' "$PLUGIN/scripts/worker.sh"; then
  no "worker still emits unsupported Task lifecycle"
else
  ok "worker uses supported Droid exec lifecycle"
fi
[ -x "$PLUGIN/scripts/investigate.sh" ] \
  && grep -q 'investigate) exec bash' "$PLUGIN/scripts/mmw.sh" \
  && ok "native investigate orchestrator exposed" || no "investigate orchestrator missing"
grep -q '执行者 agent 在任务中途咨询的更强审查者' "$PLUGIN/droids/decision-advisor.md" \
  && grep -q '对你自己判断的最强反方论点' "$PLUGIN/droids/decision-advisor.md" \
  && grep -q '^model: claude-opus-4-8$' "$PLUGIN/droids/decision-advisor.md" \
  && ok "advisor prompt preserves judgment contract" || no "advisor prompt contract"
for d in reviewer-final-a reviewer-final-b; do
  grep -q 'stage 和视角完全由 dispatch prompt 指定' "$PLUGIN/droids/$d.md" \
    || no "$d hardcodes final baseline"
  grep -q '"Execute"' "$PLUGIN/droids/$d.md" || no "$d lacks verification tool"
done
grep -q 'subagent_type:"code-explorer"' "$PLUGIN/skills/orchestrate/references/investigate.md" \
  && grep -q 'subagent_type: "decision-advisor"' "$PLUGIN/skills/orchestrate/references/propose.md" \
  && grep -q 'subagent_type: "decision-advisor"' "$PLUGIN/skills/orchestrate/references/closing.md" \
  && grep -q 'investigate-topic.md' "$PLUGIN/scripts/investigate.sh" \
  && grep -q 'investigate-synthesizer.md' "$PLUGIN/scripts/investigate.sh" \
  && grep -q 'PLAN_DROID.*plan-writer' "$PLUGIN/scripts/worker.sh" \
  && grep -q 'CAPABLE_EXECUTOR_DROID.*pack-executor-capable' "$PLUGIN/scripts/worker.sh" \
  && grep -q 'reviewer-design-a' "$PLUGIN/scripts/review.sh" \
  && grep -q 'reviewer-plan-a' "$PLUGIN/scripts/review.sh" \
  && grep -q 'reviewer-final-a' "$PLUGIN/scripts/review.sh" \
  && ok "all custom droids have runtime routes" || no "custom droid route coverage"
[ "$fail" -eq 0 ] && ok "custom droid routing contracts" || true

exit "$fail"
