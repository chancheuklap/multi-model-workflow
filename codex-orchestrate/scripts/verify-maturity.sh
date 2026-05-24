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
check "hooks.json valid JSON" python3 -m json.tool "$PLUGIN_DIR/hooks.json"
check "gate-codex-review.sh exists" test -x "$PLUGIN_DIR/hooks/gate-codex-review.sh"
check "track-review-budget.sh exists" test -x "$PLUGIN_DIR/hooks/track-review-budget.sh"
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
echo "## State Machine Contracts"
check "state.sh transition matrix enforced" bash -c "
  export STATE_BASE=\$(mktemp -d)
  bash '$PLUGIN_DIR/scripts/state.sh' init --run-id mtest --slug s --route formal >/dev/null
  ! bash '$PLUGIN_DIR/scripts/state.sh' transition --run-id mtest --actor evil --from x --to y 2>/dev/null
"

check "state.sh init formal defers budget" bash -c "
  export STATE_BASE=\$(mktemp -d)
  bash '$PLUGIN_DIR/scripts/state.sh' init --run-id mtest --slug s --route formal >/dev/null
  [ \"\$(jq -r '.budget.budget_status' \$STATE_BASE/workflow-state-mtest.json)\" = 'pending_plan_count' ]
"

check "state.sh budget initialize computes correctly" bash -c "
  export STATE_BASE=\$(mktemp -d)
  bash '$PLUGIN_DIR/scripts/state.sh' init --run-id mtest --slug s --route formal >/dev/null
  bash '$PLUGIN_DIR/scripts/state.sh' budget initialize --run-id mtest --plan-count 2 >/dev/null
  [ \"\$(jq '.budget.effort_total' \$STATE_BASE/workflow-state-mtest.json)\" = '36' ]
"

check "no regex Pack ID in agent-return-handler" bash -c "
  ! grep -qE 'sed -n.*Pack:' '$PLUGIN_DIR/hooks/agent-return-handler.sh'
"

check "gate-codex-review hard-fails on missing reviewer envelope" bash -c "
  echo '{\"hook_event_name\":\"SubagentStart\",\"agent_type\":\"codex_reviewer\",\"prompt\":\"no envelope\"}' \
    | bash '$PLUGIN_DIR/hooks/gate-codex-review.sh' 2>/dev/null; [ \$? -eq 2 ]
"

check "disposition append injected" bash -c "
  grep -q 'state\.sh.*disposition append' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'
"

check "run_in_background in dispatch" bash -c "
  grep -q 'run_in_background' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'
"

check "DISPATCH_ENVELOPE in worker dispatch" bash -c "
  grep -q 'DISPATCH_ENVELOPE' '$PLUGIN_DIR/skills/orchestrate-execution/references/execution-worker-dispatch.md'
"

check "agent_id guard in validate-pack-dispatch" bash -c "
  grep -q 'already has agent_id\|agent_id.*BLOCKED' '$PLUGIN_DIR/hooks/validate-pack-dispatch.sh'
"

check "targeted-re-review requires send_input continuity" bash -c "
  grep -q 'targeted re-review must use send_input' '$PLUGIN_DIR/hooks/gate-codex-review.sh'
"

check "worker spec no review finding in mode 2b" bash -c "
  ! grep -A2 '模式 2b' '$PLUGIN_DIR/agents/pack-executor.md' | grep -q 'review finding'
"

check "Path B uses send_input not spawn_agent" bash -c "
  ! grep -A3 '路径 B' '$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md' | grep -q 'Agent({'
"

echo ""
echo "## Missing Files"
check "state-lock.sh exists" test -f "$PLUGIN_DIR/scripts/lib/state-lock.sh"
check "learnings-jsonl.sh executable" test -x "$PLUGIN_DIR/scripts/learnings-jsonl.sh"
check "execution-state-v1.json valid" python3 -m json.tool "$PLUGIN_DIR/state-schema/execution-state-v1.json"
check "trust-boundary.md.tmpl exists" test -f "$PLUGIN_DIR/build/templates/trust-boundary.md.tmpl"
check "path-a-re-review.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-execution/references/path-a-re-review.md"
check "direction-check.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-workflow/references/direction-check.md"

echo ""
echo "## Version Sync"
PLUGIN_V=$(jq -r '.version' "$PLUGIN_DIR/.codex-plugin/plugin.json" 2>/dev/null || echo "MISSING")
MARKET_V=$(jq -r '.plugins[] | select(.name == "multi-model-workflow") | .version // empty' "$(cd "$PLUGIN_DIR/.." && pwd)/.agents/plugins/marketplace.json" 2>/dev/null || echo "")
if [[ -z "$MARKET_V" ]]; then
  MARKET_V="$PLUGIN_V"
fi
if [[ "$PLUGIN_V" == "$MARKET_V" ]]; then
  echo "  ✓ version sync ($PLUGIN_V)"
  pass=$((pass + 1))
else
  echo "  ✗ version mismatch: plugin=$PLUGIN_V marketplace=$MARKET_V"
  fail=$((fail + 1))
fi

echo ""
echo "## Behavioral Checks (R2)"

# C1: agent-return-handler uses || pattern, not dead-code if $?
check "C1: agent-return-handler no dead-code pattern" bash -c \
  "! grep -q 'if \[ \$? -ne 0 \]' '$PLUGIN_DIR/hooks/agent-return-handler.sh'"

# C2: track-review-budget uses state lock for concurrent safety
check "C2: track-review-budget uses state lock" \
  grep -q 'state_lock_acquire' "$PLUGIN_DIR/hooks/track-review-budget.sh"
check "C2: track-review-budget tracks native reviewer start" bash -c \
  "grep -q 'SubagentStart' '$PLUGIN_DIR/hooks/track-review-budget.sh' && grep -q 'codex_reviewer' '$PLUGIN_DIR/hooks/track-review-budget.sh'"

# C3: track-effort-budget uses state lock for concurrent safety
check "C3: track-effort-budget uses state lock" \
  grep -q 'state_lock_acquire' "$PLUGIN_DIR/hooks/track-effort-budget.sh"

# C4: agent-return-handler uses lock for execution-state write
check "C4: agent-return-handler uses state lock" \
  grep -q 'state_lock_acquire' "$PLUGIN_DIR/hooks/agent-return-handler.sh"

# I1: all active resolvers have at least one consuming anchor
for resolver in forbidden-shortcuts sendmessage-resume signpost state-write trust-boundary; do
  check "I1: resolver $resolver has consuming anchor" bash -c \
    "grep -rl 'BEGIN: $resolver' '$PLUGIN_DIR/skills/' '$PLUGIN_DIR/agents/' 2>/dev/null | grep -q ."
done

# I2: plan-writer-dispatch has DISPATCH_ENVELOPE protocol
check "I2: plan-writer-dispatch has DISPATCH_ENVELOPE" \
  grep -q 'DISPATCH_ENVELOPE' "$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-writer-dispatch.md"

# I3: plan-writing and workflow SKILL.md have build-system anchors
check "I3: plan-writing SKILL.md has anchors" bash -c \
  "[ \$(grep -c 'BEGIN:' '$PLUGIN_DIR/skills/orchestrate-plan-writing/SKILL.md') -ge 1 ]"
check "I3: workflow SKILL.md has anchors" bash -c \
  "[ \$(grep -c 'BEGIN:' '$PLUGIN_DIR/skills/orchestrate-workflow/SKILL.md') -ge 1 ]"

# I4: validate-pack-dispatch Step 7 implemented (not deferred)
check "I4: validate-pack-dispatch Step 7 pack status check" \
  grep -q 'PACK_STATUS' "$PLUGIN_DIR/hooks/validate-pack-dispatch.sh"

# I5: state.sh supports plans subcommand
check "I5: state.sh has plans subcommand" bash -c \
  "bash '$PLUGIN_DIR/scripts/state.sh' 2>&1 | grep -q 'plans'"

# I7: no macOS-only date -j in learnings (cross-platform)
check "I7: learnings-jsonl no macOS-only date" bash -c \
  "! grep -q 'date -j' '$PLUGIN_DIR/scripts/learnings-jsonl.sh'"

# M3: state.sh disposition enum validation
check "M3: state.sh has disposition enum validation" bash -c \
  "grep -q 'case.*disposition' '$PLUGIN_DIR/scripts/state.sh'"

# D2: BLOCKED template has dual layers (business + technical)
check "D2: execution SKILL.md has BLOCKED dual-layer template" \
  grep -q '业务影响层' "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"
check "D2: execution SKILL.md has technical detail layer" \
  grep -q '技术详情层' "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"

# D8: Entry Gate checks Codex subagent messaging availability
check "D8: workflow SKILL.md has send_input availability check" bash -c \
  "grep -q 'send_input.*可用\|send_input' '$PLUGIN_DIR/skills/orchestrate-workflow/SKILL.md'"

# route-extension dead code deleted
check "route-extension template deleted" bash -c \
  "test ! -f '$PLUGIN_DIR/build/templates/route-extension.md.tmpl'"
check "route-extension resolver deleted" bash -c \
  "test ! -f '$PLUGIN_DIR/build/resolvers/route-extension.sh'"

# set -e anti-pattern: detect $(...); if [ $? -ne 0 ] in all hooks
check "no set -e anti-pattern in hooks" bash -c \
  "! grep -rq 'if \[ \$? -ne 0 \]' '$PLUGIN_DIR/hooks/'"

echo ""
echo "## R3 Gap Coverage"

# Route 4-7 keywords in workflow SKILL.md Entry Gate
check "R3-05: Route 4 hotfix in workflow Entry Gate" \
  grep -q "hotfix" "$PLUGIN_DIR/skills/orchestrate-workflow/SKILL.md"
check "R3-05: Route 6 spike in workflow Entry Gate" \
  grep -q "spike" "$PLUGIN_DIR/skills/orchestrate-workflow/SKILL.md"
check "R3-05: Route 7 maintenance in workflow Entry Gate" \
  grep -q "maintenance" "$PLUGIN_DIR/skills/orchestrate-workflow/SKILL.md"

# NEEDS_ISSUE_SPLIT in plan-writing SKILL.md
check "R3-06: NEEDS_ISSUE_SPLIT in plan-writing SKILL.md" \
  grep -q "NEEDS_ISSUE_SPLIT" "$PLUGIN_DIR/skills/orchestrate-plan-writing/SKILL.md"

# Forbidden words in voice-directive template
check "R3-01: forbidden words in voice-directive template" \
  grep -q "delve" "$PLUGIN_DIR/build/templates/voice-directive.md.tmpl"

# Review segmentation in execution SKILL.md
check "R3-07: review segmentation in execution SKILL.md" bash -c \
  "grep -qE '分段|split.*review|Cross-Pack.*Coherence' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'"

# Neighbor interface in execution SKILL.md
check "R3-08: neighbor interface in execution SKILL.md" bash -c \
  "grep -qE 'Neighbor.*interface|邻居接口' '$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md'"

# Re-run behavior in execution + plan-writing SKILL.md
check "R3-09: Re-run behavior in execution SKILL.md" \
  grep -q "Re-run behavior" "$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"
check "R3-09: Re-run behavior in plan-writing SKILL.md" \
  grep -q "Re-run behavior" "$PLUGIN_DIR/skills/orchestrate-plan-writing/SKILL.md"

# correlation_id in dispatch-envelope schema
check "R3-04: correlation_id in dispatch-envelope schema" \
  grep -q "correlation_id" "$PLUGIN_DIR/state-schema/dispatch-envelope-v1.json"

# mutations field in state.sh
check "R3-12: mutations field in state.sh" \
  grep -q "mutations" "$PLUGIN_DIR/scripts/state.sh"

# claude --version check in session-start.sh
check "R3-13: claude version check in session-start.sh" bash -c \
  "grep -qE 'claude.*version|2\\.1\\.147' '$PLUGIN_DIR/hooks/session-start.sh'"

# R3-18: repair reference doc contradiction fixed
check "R3-18: no '默认只做 targeted re-review' in execution repair" bash -c \
  "! grep -q '默认只做 targeted re-review' '$PLUGIN_DIR/skills/orchestrate-execution/references/execution-repair-truncation.md'"
check "R3-18: no '默认只做 targeted re-review' in final-review repair" bash -c \
  "! grep -q '默认只做 targeted re-review' '$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md'"

# R3-19: exit signposts in reference files
check "R3-19: direction-check has exit signpost" bash -c \
  "tail -3 '$PLUGIN_DIR/skills/orchestrate-workflow/references/direction-check.md' | grep -qE '下一步|回到'"
check "R3-19: plan-gates has exit signpost" bash -c \
  "tail -3 '$PLUGIN_DIR/skills/orchestrate-plan-writing/references/plan-gates.md' | grep -qE '下一步|回到'"
check "R3-19: merge-preparation has exit signpost" bash -c \
  "tail -3 '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-preparation.md' | grep -qE '下一步|回到'"

# R3-20: architecture-draft sync
check "R3-20: no budget-*.json refs in architecture-draft" bash -c \
  "! grep -q 'budget-.*\.json' '$PLUGIN_DIR/architecture-draft.md'"
check "R3-20: Ruling 1 in architecture-draft" \
  grep -q "Ruling 1" "$PLUGIN_DIR/architecture-draft.md"
check "R3-20: Ruling 2 in architecture-draft" \
  grep -q "Ruling 2" "$PLUGIN_DIR/architecture-draft.md"
check "R3-20: Ruling 3 in architecture-draft" \
  grep -q "Ruling 3" "$PLUGIN_DIR/architecture-draft.md"

# R3-21: design doc rulings
check "R3-21: Ruling 2 in design doc" \
  grep -q "Ruling 2" "docs/orchestrate/design/2025-05-22-plugin-maturity.md"
check "R3-21: Ruling 3 in design doc" \
  grep -q "Ruling 3" "docs/orchestrate/design/2025-05-22-plugin-maturity.md"

echo ""
echo "=== Results: $pass passed, $fail failed ==="
[[ $fail -eq 0 ]]
