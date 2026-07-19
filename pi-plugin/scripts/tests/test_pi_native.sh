#!/usr/bin/env bash
# pi-plugin 单宿主 surface 合同。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }

echo '=== test_pi_native.sh ==='
jq -e '.version=="9.1.0" and (.keywords|index("pi-package")) and .pi.extensions==["./extensions"] and .pi.skills==["./skills"] and .pi.prompts==["./prompts"]' "$PLUGIN/package.json" >/dev/null \
  && ok 'package.json pi manifest/version' || no 'pi manifest'
[ -f "$PLUGIN/extensions/mmw-hooks.ts" ] && ok 'mmw extension exists' || no 'extension missing'
[ ! -f "$PLUGIN/scripts/lib/pi-exec.sh" ] && [ ! -f "$PLUGIN/scripts/lib/droid-exec.sh" ] \
  && grep -q "mmw_worker_backend() { printf 'pi-subagents'; }" "$PLUGIN/scripts/lib/runtime.sh" \
  && ok 'pi-subagents is sole worker backend(无无头层)' || no 'worker backend surface'
[ -d "$PLUGIN/prompts" ] && [ "$(find "$PLUGIN/prompts" -name '*.md' | wc -l | tr -d ' ')" = 11 ] \
  && ok '11 prompt templates' || no 'prompt templates'
[ ! -d "$PLUGIN/commands" ] && ok 'no legacy commands directory' || no 'legacy commands remains'

roles='investigate-topic investigate-synthesizer code-explorer plan-writer pack-executor pack-executor-capable reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b'
for role in $roles; do
  file="$PLUGIN/agents-roster/$role.md"
  [ -f "$file" ] && grep -q '^model: \(openai-codex\|claude-provider\)/' "$file" \
    && grep -q '^thinking: ' "$file" && ! grep -q '^reasoningEffort:' "$file" \
    && ok "role:$role" || no "role missing/invalid:$role"
done
[ ! -f "$PLUGIN/agents-roster/decision-advisor.md" ] \
  && ok 'decision-advisor 已裁(咨询走 advisor 工具)' || no 'decision-advisor 残留'
for role in $roles; do
  reg="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/agents/$role.md"
  [ -e "$reg" ] || { no "role 未注册为 pi agent:$role"; continue; }
done
ok 'roster 全员已注册为 pi agent'

grep -q 'PLAN_AGENT.*plan-writer' "$PLUGIN/scripts/worker.sh" \
  && grep -q 'CAPABLE_EXECUTOR_AGENT.*pack-executor-capable' "$PLUGIN/scripts/worker.sh" \
  && grep -q 'EXECUTOR_AGENT.*pack-executor' "$PLUGIN/scripts/worker.sh" \
  && ok 'worker routes all writer roles' || no 'worker role routes'
grep -q 'agent=reviewer-final-a' "$PLUGIN/scripts/review.sh" \
  && ! grep -q 'roster_model' "$PLUGIN/scripts/review.sh" \
  && ok 'review 按名字派 reviewer(无 roster_model 间接层)' || no 'review role routes'

[ -f "$PLUGIN/workflows/investigate-internal.workflow.js" ] \
  && [ -f "$PLUGIN/workflows/investigate-external.workflow.js" ] \
  && [ -x "$PLUGIN/workflows/install-workflows.sh" ] \
  && ok 'dynamic workflow sources+installer' || no 'workflow surface'
[ ! -f "$PLUGIN/prompts-runtime/headless-agent.md" ] \
  && ok '无头提示词层已随 pi-exec 一并移除' || no 'headless prompt 残留'

residue="$(grep -RInE 'DROID_PLUGIN_ROOT|\.factory/|\.factory-plugin|\.claude/|codex exec|droid-exec' "$PLUGIN" \
  --exclude='test_pi_native.sh' --exclude='*.pyc' --exclude-dir='__pycache__' || true)"
[ -z "$residue" ] && ok 'single-host residue check' || { no 'foreign-host residue'; printf '%s\n' "$residue"; }

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
