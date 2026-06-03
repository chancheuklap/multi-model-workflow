#!/usr/bin/env bash
# test_validate_multi_pr_dispatch.sh
# Pack 6.9: tests for validate-multi-pr-dispatch.sh hook.
# Covers: (a) merge-brief existence, (b) META stage vs repair_round,
#         (c) conflict_id in §4 with status ≠ resolved, (d) prompt references merge-brief path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../validate-multi-pr-dispatch.sh"
STATE_SH="$SCRIPT_DIR/../../scripts/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_DIR="$FIXTURE_DIR"

pass=0
fail=0

run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure but passed)"
    fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass + 1))
  fi
}

# Run hook with payload from temp file (avoids quoting issues in bash -c)
run_hook_with_payload() {
  local payload_file="$1"
  bash "$HOOK" < "$payload_file"
}

# Write payload to temp file and run hook
PAYLOAD_FILE="$FIXTURE_DIR/hook-payload.json"
write_payload_and_run_test() {
  local name="$1" expect_fail="$2" run_id="$3" phase="$4" repair_round="$5" conflict_id="${6:-}" include_brief_ref="${7:-yes}"
  make_prompt "$run_id" "$phase" "$repair_round" "$conflict_id" "$include_brief_ref" > "$PAYLOAD_FILE"
  if [[ "$expect_fail" == "yes" ]]; then
    run_test_expect_fail "$name" bash "$HOOK" < "$PAYLOAD_FILE"
  else
    run_test "$name" bash "$HOOK" < "$PAYLOAD_FILE"
  fi
}

# Helper: build a hook JSON payload (wrapping the Agent tool_input.prompt)
make_prompt() {
  local run_id="$1" phase="$2" repair_round="${3:-0}" conflict_id="${4:-}" include_brief_ref="${5:-yes}"
  local brief_ref=""
  if [[ "$include_brief_ref" == "yes" ]]; then
    # No backticks here to avoid jq string escaping issues; the hook checks for the file name string
    brief_ref="Read .claude/multi-model-workflow/merge-brief-${run_id}.md for context."
  fi

  local conflict_field=""
  if [[ -n "$conflict_id" ]]; then
    conflict_field=", \"conflict_id\": \"${conflict_id}\""
  fi

  # Build the prompt text string (avoid backticks in the string to prevent jq parse issues)
  local brief_ref_escaped="${brief_ref//\`/}"
  local prompt_text
  prompt_text=$(cat <<PTEOF
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "${run_id}",
  "phase": "${phase}",
  "agent_role": "pack-executor",
  "repair_round": ${repair_round},
  "idempotency_key": "${run_id}/test/r${repair_round}"${conflict_field}
}
-->

${brief_ref_escaped}
PTEOF
)

  # Wrap in hook JSON format: {"tool_input": {"prompt": "<..."}}
  jq -n --arg prompt "$prompt_text" '{"tool_input": {"prompt": $prompt}}'
}

# Helper: create a valid merge-brief file
make_merge_brief() {
  local run_id="$1" stage="${2:-init}" conflicts_section="${3:-}"
  local now; now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local path="$FIXTURE_DIR/merge-brief-${run_id}.md"
  cat > "$path" <<BRIEF
<!-- MERGE_BRIEF_META
{
  "schema_version": "1",
  "run_id": "${run_id}",
  "slug": "test-feature",
  "created_at": "${now}",
  "last_updated_at": "${now}",
  "current_stage": "${stage}",
  "integration_review_gate": null
}
-->

## 1. Meta
## 2. 参与 PR（Big Picture）
## 3. 合并后正确状态模型（Step 2 强制产出）
## 4. Conflict Findings（Steps 5-7 持续追加）
${conflicts_section}
## 5. Root Cause Analysis（Step 10 追加；仅 systemic conflict）
## 6. Resolution Log（Steps 13-15 追加）
## 7. Integration Review Pointers（Step 16 前补写）
## 8. Open Items / Out-of-scope
## 9. Verdict（Step 22 写入）
BRIEF
}

echo "=== test_validate_multi_pr_dispatch.sh ==="
echo ""
echo "--- non-multi-pr-merge phase: hook is no-op ---"

RUN_ID="no-merge-run"
write_payload_and_run_test "hook no-op for execution phase" "no" "$RUN_ID" "execution" 0
write_payload_and_run_test "hook no-op for plan-writing phase" "no" "$RUN_ID" "plan-writing" 0

echo ""
echo "--- check (a): merge-brief must exist ---"

RUN_A="run-a-test"
write_payload_and_run_test "fails when merge-brief missing" "yes" "$RUN_A" "multi-pr-merge" 0

# Create the merge-brief
make_merge_brief "$RUN_A" "init"
write_payload_and_run_test "passes when merge-brief exists (round=0, stage=init)" "no" "$RUN_A" "multi-pr-merge" 0

echo ""
echo "--- check (b): META stage vs repair_round consistency ---"

RUN_B="run-b-test"
make_merge_brief "$RUN_B" "complete"
write_payload_and_run_test "fails when repair_round=0 but stage=complete" "yes" "$RUN_B" "multi-pr-merge" 0

RUN_B2="run-b2-test"
make_merge_brief "$RUN_B2" "init"
write_payload_and_run_test "fails when repair_round=1 but stage=init" "yes" "$RUN_B2" "multi-pr-merge" 1

RUN_B3="run-b3-test"
make_merge_brief "$RUN_B3" "repair"
write_payload_and_run_test "passes when repair_round=1 and stage=repair" "no" "$RUN_B3" "multi-pr-merge" 1

RUN_B4="run-b4-test"
make_merge_brief "$RUN_B4" "conflict_discovery"
write_payload_and_run_test "passes when repair_round=0 and stage=conflict_discovery" "no" "$RUN_B4" "multi-pr-merge" 0

echo ""
echo "--- check (c): conflict_id validation ---"

CONFLICT_SECTION='
- conflict_id: C-001
- status: open
- type: code
- involved_prs: [#101]
- description: test conflict
- severity: medium

- conflict_id: C-002
- status: resolved
- type: function
- involved_prs: [#101, #102]
- description: another conflict
- severity: high
'

RUN_C="run-c-test"
make_merge_brief "$RUN_C" "conflict_discovery" "$CONFLICT_SECTION"

write_payload_and_run_test "passes with valid open conflict_id C-001" "no" "$RUN_C" "multi-pr-merge" 0 "C-001"
write_payload_and_run_test "fails with conflict_id C-002 (status=resolved)" "yes" "$RUN_C" "multi-pr-merge" 0 "C-002"
write_payload_and_run_test "fails with conflict_id C-999 (not found in §4)" "yes" "$RUN_C" "multi-pr-merge" 0 "C-999"

echo ""
echo "--- check (d): prompt must reference merge-brief path ---"

RUN_D="run-d-test"
make_merge_brief "$RUN_D" "conflict_discovery"

write_payload_and_run_test "fails when prompt does not reference merge-brief" "yes" "$RUN_D" "multi-pr-merge" 0 "" "no"
write_payload_and_run_test "passes when prompt references merge-brief-<run_id>.md" "no" "$RUN_D" "multi-pr-merge" 0 "" "yes"

echo ""
echo "--- hook is silent for non-Agent calls ---"
run_test "no-op when prompt is empty" \
  bash -c "echo '{}' | bash '$HOOK'"

echo ""
echo "--- routes fail-open: manifest unreadable → fall back to literal PHASE comparison ---"

RUN_FO="run-fo-test"
make_merge_brief "$RUN_FO" "init"

# With a poisoned ROUTES_MANIFEST env or by temporarily pointing the lib at /dev/null,
# simulate unreadable manifest by overriding the manifest path via a wrapper script.
FAILOPEN_HOOK="$FIXTURE_DIR/validate-multi-pr-dispatch-failopen-wrapper.sh"
cat > "$FAILOPEN_HOOK" <<WRAPPER
#!/usr/bin/env bash
# Wrapper: replaces routes.sh with a stub that always returns empty (simulates unreadable manifest)
# so the hook exercises the literal-fallback path.
set -euo pipefail
INPUT=\$(cat)
ORIG_HOOK="$HOOK"
STUB_LIB="$FIXTURE_DIR/stub-routes.sh"

# Create stub that mimics routes_dispatch_shape returning empty
cat > "\$STUB_LIB" <<'STUBEOF'
routes_manifest_readable() { return 1; }
routes_dispatch_shape() { echo ""; return 0; }
STUBEOF

# Patch: source stub instead of real lib by prepending to PATH and wrapping bash source
# We use env var to tell the hook to use our stub — but hook sources from fixed path.
# Simpler approach: run hook with the state-schema routes file temporarily absent.
ROUTES_FILE="$SCRIPT_DIR/../../state-schema/routes-v1.json"
BACKUP="\${ROUTES_FILE}.failopen-backup"
mv "\$ROUTES_FILE" "\$BACKUP"
trap 'mv "\$BACKUP" "\$ROUTES_FILE"' EXIT
echo "\$INPUT" | bash "\$ORIG_HOOK"
WRAPPER
chmod +x "$FAILOPEN_HOOK"

# Test 1: multi-pr-merge phase with manifest absent → fail-open to literal → activates → gate checks run → merge-brief found → PASS
PAYLOAD_FO="$FIXTURE_DIR/payload-fo.json"
make_prompt "$RUN_FO" "multi-pr-merge" 0 "" "yes" > "$PAYLOAD_FO"
run_test "fail-open: multi-pr-merge phase activates gate (literal fallback)" \
  bash -c "bash '$FAILOPEN_HOOK' < '$PAYLOAD_FO'"

# Test 2: non-multi-pr phase with manifest absent → fail-open to literal → exits 0 silently
PAYLOAD_FO2="$FIXTURE_DIR/payload-fo2.json"
make_prompt "$RUN_FO" "execution" 0 "" "yes" > "$PAYLOAD_FO2"
run_test "fail-open: non-multi-pr phase is no-op when manifest unreadable (literal fallback)" \
  bash -c "bash '$FAILOPEN_HOOK' < '$PAYLOAD_FO2'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
