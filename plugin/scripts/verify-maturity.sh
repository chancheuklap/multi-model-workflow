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
check "≥7 resolvers" bash -c "[ \$(ls -1 '$PLUGIN_DIR/build/resolvers/'*.sh | wc -l) -ge 7 ]"
check "≥7 templates" bash -c "[ \$(ls -1 '$PLUGIN_DIR/build/templates/'*.tmpl | wc -l) -ge 7 ]"

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
check "validate-plan-dispatch.sh exists" test -x "$PLUGIN_DIR/hooks/validate-plan-dispatch.sh"
check "complete-review-dispatch.sh exists" test -x "$PLUGIN_DIR/scripts/complete-review-dispatch.sh"
check "record-review-disposition.sh exists" test -x "$PLUGIN_DIR/scripts/record-review-disposition.sh"

echo ""
echo "## Fallback Removal"
check "no '或新建' in skills/" bash -c "! grep -rq '或新建' '$PLUGIN_DIR/skills/'"
check "no '新建同类' in agents/" bash -c "! grep -rq '新建同类' '$PLUGIN_DIR/agents/'"

echo ""
echo "## Anchors + Canonical References (D1)"
check "canonical review-dispatch exists" test -f "$PLUGIN_DIR/skills/_shared/review-dispatch.md"
check "canonical repair-routing exists" test -f "$PLUGIN_DIR/skills/_shared/repair-routing.md"
check "canonical disposition-table exists" test -f "$PLUGIN_DIR/skills/_shared/disposition-table.md"
check "no stale review-dispatch standard anchor" bash -c "[ \$(grep -rln '<!-- BEGIN: review-dispatch -->' '$PLUGIN_DIR/skills/' | grep -v 'codex-review' | wc -l) -eq 0 ]"
check "no stale repair-routing anchor" bash -c "[ \$(grep -rln '<!-- BEGIN: repair-routing -->' '$PLUGIN_DIR/skills/' | wc -l) -eq 0 ]"
check "no stale disposition-table anchor" bash -c "[ \$(grep -rln '<!-- BEGIN: disposition-table -->' '$PLUGIN_DIR/skills/' | wc -l) -eq 0 ]"
check "no relative _shared/ references" bash -c "[ \$(grep -rn '\.\./\_shared/\|^_shared/' '$PLUGIN_DIR/skills/' | wc -l) -eq 0 ]"
check "≥1 preamble anchor" bash -c "[ \$(grep -rl 'BEGIN: preamble' '$PLUGIN_DIR/skills/' | wc -l) -ge 1 ]"

echo ""
echo "## Persona + Observability"
check "persona.md exists" test -f "$PLUGIN_DIR/agents/persona.md"
check "run-summary.sh exists" test -x "$PLUGIN_DIR/scripts/run-summary.sh"

echo ""
echo "## Defense"
check "poison detection function inlined in learnings-jsonl.sh" bash -c "grep -q 'detect_learning_poison' '$PLUGIN_DIR/scripts/learnings-jsonl.sh'"
check "pack-count-validator.sh removed (D24)" test ! -f "$PLUGIN_DIR/scripts/pack-count-validator.sh"

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

check "gate-codex-review hard-fails on missing envelope" bash -c "
  echo '{\"tool_input\":{\"command\":\"node x/codex-companion.mjs task --prompt-file /nonexistent\"}}' \
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

check "agent_id guard in validate-plan-dispatch" bash -c "
  grep -q 'already in_progress with worker' '$PLUGIN_DIR/hooks/validate-plan-dispatch.sh'
"

check "targeted-re-review removed from gate-codex-review" bash -c "
  ! grep -q 'targeted-re-review' '$PLUGIN_DIR/hooks/gate-codex-review.sh'
"

check "worker spec no review finding in mode 2b" bash -c "
  ! grep -A2 '模式 2b' '$PLUGIN_DIR/agents/pack-executor.md' | grep -q 'review finding'
"

check "Path B uses SendMessage not Agent()" bash -c "
  ! grep -A3 '路径 B' '$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-repair.md' | grep -q 'Agent({'
"

echo ""
echo "## Missing Files"
check "state-lock.sh exists" test -f "$PLUGIN_DIR/scripts/lib/state-lock.sh"
check "learnings-jsonl.sh executable" test -x "$PLUGIN_DIR/scripts/learnings-jsonl.sh"
check "execution-state-v1.json valid" python3 -m json.tool "$PLUGIN_DIR/state-schema/execution-state-v1.json"
check "pack-returns-v1.json exists and valid" python3 -m json.tool "$PLUGIN_DIR/state-schema/pack-returns-v1.json"
check "direction-check.md exists" test -f "$PLUGIN_DIR/skills/orchestrate-workflow/references/direction-check.md"

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
echo "## Behavioral Checks (R2)"

# C1: agent-return-handler uses || pattern, not dead-code if $?
check "C1: agent-return-handler no dead-code pattern" bash -c \
  "! grep -q 'if \[ \$? -ne 0 \]' '$PLUGIN_DIR/hooks/agent-return-handler.sh'"

# C2: review budget increments through state.sh with lock, not in-hook
check "C2: state.sh review budget uses lock" bash -c \
  "grep -q 'cmd_budget_increment_review' '$PLUGIN_DIR/scripts/state.sh' && grep -q 'acquire_lock' '$PLUGIN_DIR/scripts/state.sh'"
check "C2: review budget auto-counted by PostToolUse hook (Claude-native)" bash -c \
  "grep -q 'review_used += 1' '$PLUGIN_DIR/hooks/track-review-budget.sh' && grep -q 'track-review-budget.sh' '$PLUGIN_DIR/hooks/hooks.json'"
check "C2: complete-review-dispatch is durability-only (no double-counting)" bash -c \
  "! grep -q 'budget increment-review' '$PLUGIN_DIR/scripts/complete-review-dispatch.sh' && grep -q 'status = \"completed\"' '$PLUGIN_DIR/scripts/complete-review-dispatch.sh'"
check "C2: review dispatch canonical marks disposition recovery" bash -c \
  "grep -q 'record-review-disposition.sh' '$PLUGIN_DIR/skills/_shared/review-dispatch.md' && grep -q 'disposition_started' '$PLUGIN_DIR/skills/_shared/review-dispatch.md'"
check "C2: review dispatch canonical completes through bookkeeping script" \
  grep -q 'complete-review-dispatch.sh' "$PLUGIN_DIR/skills/_shared/review-dispatch.md"
check "C2: review dispatch canonical records baseline reviewer agent" \
  grep -q 'dispatch-review.sh.*record' "$PLUGIN_DIR/skills/_shared/review-dispatch.md"
check "C2: state.sh supports budget unlimited subcommand" \
  bash -c "grep -q 'cmd_budget_unlimited' '$PLUGIN_DIR/scripts/state.sh'"
check "C2: direct-repair / multi-pr-merge / bug-investigation init as unlimited" bash -c \
  "grep -q 'direct-repair|multi-pr-merge|bug-investigation' '$PLUGIN_DIR/scripts/state.sh'"
check "C2: route worker dispatch used by merge-conflict-repair" \
  grep -q 'dispatch-route-worker.sh.*validate' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md"

# C3: track-effort-budget uses state lock for concurrent safety
check "C3: track-effort-budget uses state lock" \
  grep -q 'state_lock_acquire' "$PLUGIN_DIR/hooks/track-effort-budget.sh"

# C4: agent-return-handler's execution-state mutation is lock-protected. Plan-level
# handler delegates the write to `state.sh plan-returns ingest`, which acquires the
# state lock internally (cmd_plan_returns_ingest → acquire_lock).
check "C4: agent-return-handler state write is lock-protected via state.sh ingest" bash -c "
  grep -q 'plan-returns ingest' '$PLUGIN_DIR/hooks/agent-return-handler.sh' && \
  grep -q 'acquire_lock' '$PLUGIN_DIR/scripts/state.sh'
"

# I1: all active resolvers have at least one consuming anchor
for resolver in sendmessage-resume signpost; do
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

# I4: validate-plan-dispatch enforces plan-level execution (legacy pack-level path removed)
check "I4: validate-plan-dispatch blocks per-pack execution dispatch" \
  grep -q 'execution dispatch must be plan-level' "$PLUGIN_DIR/hooks/validate-plan-dispatch.sh"

# I5: state.sh plans subcommand removed (D7b)
check "I5: state.sh plans subcommand removed" bash -c \
  "! bash '$PLUGIN_DIR/scripts/state.sh' 2>&1 | grep -q '^  plans '"

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

# D8: Entry Gate checks SendMessage tool availability
check "D8: workflow SKILL.md has SendMessage availability check" bash -c \
  "grep -q 'SendMessage.*可用\|SendMessage tool' '$PLUGIN_DIR/skills/orchestrate-workflow/SKILL.md'"

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
echo "## Pack 6.x: merge-brief + Multi-PR Merge"

# 6.1: merge-brief-v1.json schema exists and has ≥10 top-level properties
check "6.1: merge-brief-v1.json exists and valid JSON" \
  python3 -m json.tool "$PLUGIN_DIR/state-schema/merge-brief-v1.json"
check "6.1: merge-brief-v1.json has ≥10 top-level properties" bash -c "
  [ \$(jq '.properties | length' '$PLUGIN_DIR/state-schema/merge-brief-v1.json') -ge 10 ]
"

# 6.2: merge-brief-template.md exists and has ≥9 sections
check "6.2: merge-brief-template.md exists" \
  test -f "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md"
check "6.2: merge-brief-template.md has ≥9 sections (## N.)" bash -c "
  [ \$(grep -c '^## [0-9]' '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md') -ge 9 ]
"
check "6.2: merge-brief-template.md has MERGE_BRIEF_META block" \
  grep -q 'MERGE_BRIEF_META' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md"

# 6.3: SKILL.md merge-brief section and dispatch rules present
check "6.3: orchestrate-multi-pr-merge SKILL.md has merge-brief 写作流程 section" \
  grep -q 'merge-brief 写作流程' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/SKILL.md"
check "6.3: orchestrate-multi-pr-merge SKILL.md has dispatch path-not-paste rule" bash -c "
  grep -q '路径.*不粘贴\|prompt 只携带.*路径\|path.*not.*paste\|路径而非粘贴' '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/SKILL.md'
"
check "6.3: merge-preparation.md has mandatory state.sh merge-brief init step" \
  grep -q 'state.sh.*merge-brief init\|merge-brief init' "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-preparation.md"

# 6.4: cursor.reference tests exist
check "6.4: test_state_cursor_reference.sh exists" \
  test -f "$PLUGIN_DIR/scripts/tests/test_state_cursor_reference.sh"

# 6.8: state.sh merge-brief subcommands (init/stage/verify)
check "6.8: state.sh has merge-brief init subcommand" \
  grep -q 'cmd_merge_brief_init\|merge-brief.*init' "$PLUGIN_DIR/scripts/state.sh"
check "6.8: state.sh has merge-brief stage subcommand" \
  grep -q 'cmd_merge_brief_stage\|merge-brief.*stage' "$PLUGIN_DIR/scripts/state.sh"
check "6.8: state.sh has merge-brief verify subcommand" \
  grep -q 'cmd_merge_brief_verify\|merge-brief.*verify' "$PLUGIN_DIR/scripts/state.sh"
check "6.8: state.sh merge-brief path uses STATE_BASE (not docs/)" bash -c "
  grep -A3 'merge_brief_default_path()' '$PLUGIN_DIR/scripts/state.sh' | grep -q 'STATE_BASE'
"
check "6.8: test_state_merge_brief.sh exists with ≥20 tests" bash -c "
  test -f '$PLUGIN_DIR/scripts/tests/test_state_merge_brief.sh' && \
  [ \$(grep -c 'run_test\|echo.*PASS\|echo.*FAIL' '$PLUGIN_DIR/scripts/tests/test_state_merge_brief.sh') -ge 20 ]
"

# 6.9: validate-multi-pr-dispatch.sh hook registered and executable
check "6.9: validate-multi-pr-dispatch.sh exists and executable" \
  test -x "$PLUGIN_DIR/hooks/validate-multi-pr-dispatch.sh"
check "6.9: validate-multi-pr-dispatch.sh registered in hooks.json" \
  grep -q 'validate-multi-pr-dispatch.sh' "$PLUGIN_DIR/hooks/hooks.json"
check "6.9: validate-multi-pr-dispatch.sh checks merge-brief existence" \
  grep -q 'merge-brief not found\|MERGE_BRIEF_PATH' "$PLUGIN_DIR/hooks/validate-multi-pr-dispatch.sh"
check "6.9: validate-multi-pr-dispatch.sh checks prompt references merge-brief" \
  grep -q 'EXPECTED_MERGE_BRIEF_REF\|does not reference merge-brief' "$PLUGIN_DIR/hooks/validate-multi-pr-dispatch.sh"

# 6.11: Multi-PR merge-brief + role references with Self-Read Protocol
check "6.11: merge-brief-template exists" \
  test -f "$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-brief-template.md"
check "6.11: merge-preparation has signpost" \
  bash -c "head -5 '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-preparation.md' | grep -qE '流程位置|使用场景|完成后回到|Self-Read Protocol'"
check "6.11: merge-conflict-discovery has signpost" \
  bash -c "head -5 '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-conflict-discovery.md' | grep -qE '流程位置|使用场景|完成后回到|Self-Read Protocol'"
check "6.11: merge-integration-review has signpost" \
  bash -c "head -5 '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md' | grep -qE '流程位置|使用场景|完成后回到|Self-Read Protocol'"
check "6.11: orchestrate-multi-pr-merge SKILL.md ≥100 lines" bash -c "
  [ \$(wc -l < '$PLUGIN_DIR/skills/orchestrate-multi-pr-merge/SKILL.md') -ge 100 ]
"

# 6.12: Reference signpost completeness (D12)
echo ""
echo "=== 6.12: Reference signpost completeness (D12) ==="
missing=$(for f in $(find "$PLUGIN_DIR/skills" -type f -name '*.md' -not -path '*/_shared/*' -path '*/references/*'); do head -5 "$f" | grep -qE '流程位置|使用场景|完成后回到' || echo "$f"; done)
if [[ -n "$missing" ]]; then
  echo "FAIL: missing signpost blockquote (top-5 lines) in:"
  echo "$missing"
  fail=$((fail+1))
else
  echo "PASS: all references have signpost blockquote"
  pass=$((pass+1))
fi

echo ""
echo "=== Results: $pass passed, $fail failed ==="
[[ $fail -eq 0 ]]
