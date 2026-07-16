#!/usr/bin/env bash
# pi-plugin 单宿主 surface 合同。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }

echo '=== test_pi_native.sh ==='
jq -e '.version=="8.0.0" and (.keywords|index("pi-package")) and .pi.extensions==["./extensions"] and .pi.skills==["./skills"] and .pi.prompts==["./prompts"]' "$PLUGIN/package.json" >/dev/null \
  && ok 'package.json pi manifest/version' || no 'pi manifest'
[ -f "$PLUGIN/extensions/mmw-hooks.ts" ] && ok 'mmw extension exists' || no 'extension missing'
[ -f "$PLUGIN/scripts/lib/pi-exec.sh" ] && [ ! -f "$PLUGIN/scripts/lib/droid-exec.sh" ] \
  && ok 'pi-exec is sole worker backend' || no 'worker backend surface'
[ -d "$PLUGIN/prompts" ] && [ "$(find "$PLUGIN/prompts" -name '*.md' | wc -l | tr -d ' ')" = 11 ] \
  && ok '11 prompt templates' || no 'prompt templates'
[ ! -d "$PLUGIN/commands" ] && ok 'no legacy commands directory' || no 'legacy commands remains'

roles='investigate-topic investigate-synthesizer code-explorer decision-advisor plan-writer pack-executor pack-executor-capable reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b'
for role in $roles; do
  file="$PLUGIN/agents-roster/$role.md"
  [ -f "$file" ] && grep -q '^model: \(openai-codex\|claude-provider\)/' "$file" \
    && ok "role:$role" || no "role missing/invalid:$role"
done

grep -q 'PLAN_AGENT.*plan-writer' "$PLUGIN/scripts/worker.sh" \
  && grep -q 'CAPABLE_EXECUTOR_AGENT.*pack-executor-capable' "$PLUGIN/scripts/worker.sh" \
  && grep -q 'EXECUTOR_AGENT.*pack-executor' "$PLUGIN/scripts/worker.sh" \
  && ok 'worker routes all writer roles' || no 'worker role routes'
grep -q 'reviewer-final-a' "$PLUGIN/scripts/review.sh" && grep -q 'Agent(pi-subagents' "$PLUGIN/scripts/review.sh" \
  && ok 'review routes pi-subagents reviewers' || no 'review role routes'

[ -f "$PLUGIN/workflows/investigate-internal.workflow.js" ] \
  && [ -f "$PLUGIN/workflows/investigate-external.workflow.js" ] \
  && [ -x "$PLUGIN/workflows/install-workflows.sh" ] \
  && ok 'dynamic workflow sources+installer' || no 'workflow surface'
python3 - "$PLUGIN/prompts-runtime/headless-agent.md" <<'PY'
import re,sys
s=open(sys.argv[1],encoding='utf8').read()
raise SystemExit(0 if not re.sub(r'<!--.*?-->','',s,flags=re.S).strip() else 1)
PY
[ "$?" = 0 ] && ok 'GPT headless prompt remains placeholder' || no 'headless prompt unexpectedly filled'

residue="$(grep -RInE 'DROID_PLUGIN_ROOT|\.factory/|\.factory-plugin|\.claude/|codex exec|droid-exec' "$PLUGIN" \
  --exclude='test_pi_native.sh' --exclude='*.pyc' --exclude-dir='__pycache__' || true)"
[ -z "$residue" ] && ok 'single-host residue check' || { no 'foreign-host residue'; printf '%s\n' "$residue"; }

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
