#!/usr/bin/env bash
# pi-plugin 单宿主 surface 合同。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }

echo '=== test_pi_native.sh ==='
jq -e '.version=="9.5.0" and (.keywords|index("pi-package")) and .pi.extensions==["./extensions"] and .pi.skills==["./skills"] and .pi.prompts==["./prompts"]' "$PLUGIN/package.json" >/dev/null \
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

# tools 行必须是逗号格式(nicobailon 不解析 YAML 数组,方括号会生成垃圾工具名)
! grep -l '^tools: \[' "$PLUGIN"/agents-roster/*.md >/dev/null \
  && ok 'roster tools 全逗号格式' || no 'roster tools 存在方括号'
# Fable 系 reviewer 配同厂商 fallback(fable-5 限流时换 opus-4-8:xhigh,不跨厂商)
for role in reviewer-design-b reviewer-plan-b reviewer-final-b; do
  grep -q '^fallbackModels: claude-provider/claude-opus-4-8:xhigh$' "$PLUGIN/agents-roster/$role.md" \
    && ok "fallback 同厂商:$role" || no "fallback 缺失:$role"
done
[ ! -f "$PLUGIN/agents-roster/decision-advisor.md" ] \
  && ok 'decision-advisor 已裁(咨询走 advisor 工具)' || no 'decision-advisor 残留'

# supervisor 举手通道:仅三个重角色有 contact_supervisor 工具 + 协议片段;reviewer/只读角色不絡
for role in plan-writer pack-executor pack-executor-capable; do
  file="$PLUGIN/agents-roster/$role.md"
  grep -q 'contact_supervisor' "$file" && grep -q '向上举手' "$file" \
    && ok "supervisor 通道:$role" || no "supervisor 通道缺失:$role"
done
for role in reviewer-design-a reviewer-plan-a reviewer-final-a code-explorer; do
  file="$PLUGIN/agents-roster/$role.md"
  grep -q 'contact_supervisor' "$file" && no "supervisor 越界:$role" || ok "无 supervisor(只读):$role"
done
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
