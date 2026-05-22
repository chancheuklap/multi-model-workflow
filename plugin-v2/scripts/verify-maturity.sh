#!/usr/bin/env bash
# End-to-end verification harness for plugin maturity.
# Runs all verification commands from the design doc §8.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

pass=0
fail=0

check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  ✓ $name"
    pass=$((pass + 1))
  else
    echo "  ✗ $name"
    fail=$((fail + 1))
  fi
}

echo "=== Plugin Maturity Verification ==="
echo ""

echo "## Build System"
check "build.sh exists and executable" test -x "$PLUGIN_DIR/build/build.sh"
check "build.sh --check passes" bash "$PLUGIN_DIR/build/build.sh" --check --plugin-dir "$PLUGIN_DIR"
check "≥9 resolvers" bash -c "[ \$(ls -1 '$PLUGIN_DIR/build/resolvers/'*.sh | wc -l) -ge 9 ]"
check "≥9 templates" bash -c "[ \$(ls -1 '$PLUGIN_DIR/build/templates/'*.tmpl | wc -l) -ge 9 ]"

echo ""
echo "## State Machine"
check "state.sh exists and executable" test -x "$PLUGIN_DIR/scripts/state.sh"
check "workflow-state-v1.json valid JSON" python3 -m json.tool "$PLUGIN_DIR/state-schema/workflow-state-v1.json"
check "dispatch-envelope-v1.json valid JSON" python3 -m json.tool "$PLUGIN_DIR/state-schema/dispatch-envelope-v1.json"

echo ""
echo "## Hooks"
check "hooks.json valid JSON" python3 -m json.tool "$PLUGIN_DIR/hooks/hooks.json"
check "gate-codex-review.sh exists" test -x "$PLUGIN_DIR/hooks/gate-codex-review.sh"
check "parse-envelope.sh exists" test -x "$PLUGIN_DIR/hooks/lib/parse-envelope.sh"
check "validate-pack-dispatch.sh exists" test -x "$PLUGIN_DIR/hooks/validate-pack-dispatch.sh"

echo ""
echo "## Fallback Removal"
check "no '或新建' in skills/" bash -c "! grep -rq '或新建' '$PLUGIN_DIR/skills/'"
check "no '新建同类' in agents/" bash -c "! grep -rq '新建同类' '$PLUGIN_DIR/agents/'"

echo ""
echo "## Anchors"
check "≥10 review-dispatch anchors" bash -c "[ \$(grep -rl 'BEGIN: review-dispatch' '$PLUGIN_DIR/skills/' | wc -l) -ge 10 ]"
check "≥1 disposition-table anchor" bash -c "[ \$(grep -rl 'BEGIN: disposition-table' '$PLUGIN_DIR/skills/' | wc -l) -ge 1 ]"
check "≥1 preamble anchor" bash -c "[ \$(grep -rl 'BEGIN: preamble' '$PLUGIN_DIR/skills/' | wc -l) -ge 1 ]"

echo ""
echo "## Route Extensions"
check "route-4-hotfix.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-execution/references/route-extensions/route-4-hotfix.md"
check "route-5-quickfix.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-execution/references/route-extensions/route-5-quickfix.md"
check "route-6-spike.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-execution/references/route-extensions/route-6-spike.md"
check "route-7-maintenance.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-execution/references/route-extensions/route-7-maintenance.md"

echo ""
echo "## Persona + Observability"
check "persona.md exists" test -f "$PLUGIN_DIR/agents/persona.md"
check "run-summary.sh exists" test -x "$PLUGIN_DIR/scripts/run-summary.sh"
check "review-effectiveness.sh exists" test -x "$PLUGIN_DIR/scripts/lib/review-effectiveness.sh"

echo ""
echo "## Defense"
check "learnings-poison-detector.sh exists" test -x "$PLUGIN_DIR/scripts/lib/learnings-poison-detector.sh"
check "pack-count-validator.sh exists" test -x "$PLUGIN_DIR/scripts/pack-count-validator.sh"

echo ""
echo "## Version Sync"
PLUGIN_V=$(jq -r '.version' "$PLUGIN_DIR/.claude-plugin/plugin.json" 2>/dev/null || echo "MISSING")
MARKET_V=$(jq -r '.plugins[0].version' "$(cd "$PLUGIN_DIR/.." && pwd)/.claude-plugin/marketplace.json" 2>/dev/null || echo "MISSING")
if [[ "$PLUGIN_V" == "$MARKET_V" ]]; then
  echo "  ✓ version sync ($PLUGIN_V)"
  pass=$((pass + 1))
else
  echo "  ✗ version mismatch: plugin=$PLUGIN_V marketplace=$MARKET_V"
  fail=$((fail + 1))
fi

echo ""
echo "=== Results: $pass passed, $fail failed ==="
[[ $fail -eq 0 ]]
