#!/usr/bin/env bash
# Pack 6.6: Multi-PR Merge end-to-end integration test.
#
# Simulates the full merge-brief lifecycle:
#   1. state.sh merge-brief init → creates file with 9 sections + MERGE_BRIEF_META
#   2. state.sh merge-brief stage → META stage transitions correctly
#   3. validate-multi-pr-dispatch.sh gates:
#      (a) missing merge-brief → BLOCKED
#      (b) repair_round=1 but stage=init → BLOCKED
#      (c) conflict_id not in §4 → BLOCKED
#      (d) prompt missing merge-brief path reference → BLOCKED
#      (e) valid dispatch (with conflict in §4 + correct stage + path ref) → PASS
#   4. Coordinator appends conflict to §4 → verify passes
#   5. state.sh merge-brief verify → full self-consistency check
#
# Verifies the complete "Coordinator creates merge-brief → dispatches agent"
# flow documented in orchestrate-multi-pr-merge SKILL.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$(cd "$HOOKS_DIR/.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"
HOOK="$PLUGIN_DIR/hooks/validate-multi-pr-dispatch.sh"

WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT
export STATE_BASE="$WORKSPACE"
# validate-multi-pr-dispatch.sh uses STATE_DIR
export STATE_DIR="$WORKSPACE"

pass=0
fail=0

check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

check_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure but passed)"
    fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass + 1))
  fi
}

# Build a hook dispatch payload (multi-line DISPATCH_ENVELOPE in prompt)
make_dispatch_payload() {
  local run_id="$1" phase="$2" repair_round="${3:-0}" conflict_id="${4:-}" include_brief_ref="${5:-yes}"

  local conflict_field=""
  if [[ -n "$conflict_id" ]]; then
    conflict_field=", \"conflict_id\": \"${conflict_id}\""
  fi

  local brief_ref=""
  if [[ "$include_brief_ref" == "yes" ]]; then
    brief_ref="Read .codex/multi-model-workflow/merge-brief-${run_id}.md for context."
  fi

  local prompt_text
  prompt_text=$(cat <<PTEOF
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "${run_id}",
  "phase": "${phase}",
  "agent_role": "pack_executor",
  "repair_round": ${repair_round},
  "idempotency_key": "${run_id}/e2e/r${repair_round}"${conflict_field}
}
-->

${brief_ref}
PTEOF
)
  jq -n --arg prompt "$prompt_text" '{"tool_input": {"prompt": $prompt}}'
}

echo "=== test_multi_pr_merge_e2e.sh ==="
echo ""
echo "## Phase 1: state.sh merge-brief init"

RUN_ID="e2e-merge-run-001"

# Hook dispatch before merge-brief exists
PAYLOAD_FILE="$WORKSPACE/payload.json"
make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "" "yes" > "$PAYLOAD_FILE"
check_fail "hook BLOCKS dispatch before merge-brief exists" \
  bash "$HOOK" < "$PAYLOAD_FILE"

# Init merge-brief
check "merge-brief init succeeds" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID" --slug "feature-auth-refactor"

BRIEF_PATH="$WORKSPACE/merge-brief-${RUN_ID}.md"
check "merge-brief file created at STATE_BASE path" test -f "$BRIEF_PATH"

check "merge-brief has MERGE_BRIEF_META block" \
  grep -q 'MERGE_BRIEF_META' "$BRIEF_PATH"

check "merge-brief has ≥9 section headings" bash -c "
  [ \$(grep -c '^## [0-9]' '$BRIEF_PATH') -ge 9 ]
"

check "merge-brief META has current_stage=init" \
  python3 -c "
import sys, re, json
content = open('$BRIEF_PATH').read()
m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', content, re.DOTALL)
meta = json.loads(m.group(1))
assert meta['current_stage'] == 'init', f'stage={meta[\"current_stage\"]}'
"

check "merge-brief init is idempotent (second init does not fail)" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID" --slug "feature-auth-refactor"

echo ""
echo "## Phase 2: Hook gate checks with initial stage"

# Now merge-brief exists (stage=init, repair_round=0) → should PASS
make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "" "yes" > "$PAYLOAD_FILE"
check "hook PASSES initial dispatch (round=0, stage=init, with path ref)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

# repair_round=1 but stage=init → BLOCKED (check b)
make_dispatch_payload "$RUN_ID" "multi-pr-merge" 1 "" "yes" > "$PAYLOAD_FILE"
check_fail "hook BLOCKS repair_round=1 when stage=init (check b)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

# Missing merge-brief path reference (check d)
make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "" "no" > "$PAYLOAD_FILE"
check_fail "hook BLOCKS dispatch when prompt missing merge-brief path ref (check d)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

# Non-multi-pr-merge phase is no-op
make_dispatch_payload "$RUN_ID" "execution" 0 "" "no" > "$PAYLOAD_FILE"
check "hook is no-op for execution phase" \
  bash "$HOOK" < "$PAYLOAD_FILE"

echo ""
echo "## Phase 3: Stage transition"

check "merge-brief stage → conflict_discovery" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "conflict_discovery"

check "META stage updated to conflict_discovery" \
  python3 -c "
import sys, re, json
content = open('$BRIEF_PATH').read()
m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', content, re.DOTALL)
meta = json.loads(m.group(1))
assert meta['current_stage'] == 'conflict_discovery', f'stage={meta[\"current_stage\"]}'
"

# repair_round=1 with stage=conflict_discovery → hook PASSES
# (hook only blocks repair_round≥1 when stage is literally "init")
make_dispatch_payload "$RUN_ID" "multi-pr-merge" 1 "" "yes" > "$PAYLOAD_FILE"
check "hook PASSES repair_round=1 when stage=conflict_discovery (past init)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

echo ""
echo "## Phase 4: Coordinator appends conflict finding to §4"

# Simulate Coordinator Edit: append conflict to §4
python3 - "$BRIEF_PATH" <<'PYEOF'
import sys
path = sys.argv[1]
content = open(path).read()
conflict_entry = """
- conflict_id: C-001
- status: open
- type: semantic
- involved_prs: [#101, #102]
- description: Both PRs modify User.save() field list differently
- severity: high

- conflict_id: C-002
- status: resolved
- type: code
- involved_prs: [#101]
- description: Import path renamed
- severity: low
"""
# Insert into §4 (after the §4 heading, before §5)
marker = "## 4. Conflict"
end_marker = "## 5. Root Cause"
idx = content.find(marker)
end_idx = content.find(end_marker, idx)
new_content = content[:end_idx] + conflict_entry + "\n" + content[end_idx:]
open(path, 'w').write(new_content)
PYEOF
check "§4 now contains C-001" grep -q 'conflict_id: C-001' "$BRIEF_PATH"
check "§4 now contains C-002 (resolved)" grep -q 'conflict_id: C-002' "$BRIEF_PATH"

echo ""
echo "## Phase 5: Hook gates with conflict_id (check c)"

make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "C-001" "yes" > "$PAYLOAD_FILE"
check "hook PASSES valid conflict_id C-001 (status=open)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "C-002" "yes" > "$PAYLOAD_FILE"
check_fail "hook BLOCKS conflict_id C-002 (status=resolved, check c)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "C-999" "yes" > "$PAYLOAD_FILE"
check_fail "hook BLOCKS conflict_id C-999 (not in §4, check c)" \
  bash "$HOOK" < "$PAYLOAD_FILE"

echo ""
echo "## Phase 6: Stage → repair, repair_round=1 now passes"

check "merge-brief stage → repair" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "repair"

make_dispatch_payload "$RUN_ID" "multi-pr-merge" 1 "C-001" "yes" > "$PAYLOAD_FILE"
check "hook PASSES repair_round=1 with stage=repair and valid conflict" \
  bash "$HOOK" < "$PAYLOAD_FILE"

echo ""
echo "## Phase 7: state.sh merge-brief verify (with consistent §4)"

# C-001 is open (no §6 entry needed for open)
# C-002 is resolved → need §6 entry. Append a resolution log entry.
python3 - "$BRIEF_PATH" <<'PYEOF'
import sys
path = sys.argv[1]
content = open(path).read()
resolution_entry = "\n- conflict_id: C-002\n  resolution: Merged import path change from #101 into main.\n"
marker = "## 6. Resolution"
end_marker = "## 7. Integration"
idx = content.find(marker)
end_idx = content.find(end_marker, idx)
new_content = content[:end_idx] + resolution_entry + "\n" + content[end_idx:]
open(path, 'w').write(new_content)
PYEOF

check "merge-brief verify passes with self-consistent §4+§6" \
  bash "$STATE_SH" merge-brief verify --run-id "$RUN_ID"

echo ""
echo "## Phase 8: Invalid stage enum"

check_fail "merge-brief stage rejects invalid enum value" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "nonexistent_stage"

echo ""
echo "## Phase 9: complete stage and guard check"

check "merge-brief stage → complete" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "complete"

make_dispatch_payload "$RUN_ID" "multi-pr-merge" 0 "" "yes" > "$PAYLOAD_FILE"
check_fail "hook BLOCKS new dispatch (round=0) when stage=complete" \
  bash "$HOOK" < "$PAYLOAD_FILE"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
