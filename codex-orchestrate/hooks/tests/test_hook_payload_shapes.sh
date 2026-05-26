#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

TRACK_EXEC="$PLUGIN_DIR/hooks/track-execution-state.sh"
CLEANUP="$PLUGIN_DIR/scripts/cleanup-before-push.sh"
GUARD_PUSH="$PLUGIN_DIR/scripts/guard-premature-push.sh"
ENFORCE_COMMIT="$PLUGIN_DIR/hooks/enforce-pack-commit.sh"
GUARD_DOC="$PLUGIN_DIR/hooks/guard-doc-edit.sh"
TRACK_EFFORT="$PLUGIN_DIR/hooks/track-effort-budget.sh"
AGENT_RETURN="$PLUGIN_DIR/hooks/agent-return-handler.sh"

WORKSPACE=$(mktemp -d)
trap 'rm -rf "$WORKSPACE"' EXIT

pass=0
fail=0

run_test() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

run_test_expect_code() {
  local name="$1"
  local expected="$2"
  shift 2
  local code=0
  "$@" >/dev/null 2>&1 || code=$?
  if [[ "$code" -eq "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected $expected, got $code)"
    fail=$((fail + 1))
  fi
}

echo "=== test_hook_payload_shapes.sh ==="

POST_STRING_RESPONSE='{"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"git status --short --branch"},"tool_response":"## main"}'
PRE_STRING_INPUT='{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":"git status --short --branch"}'
MERGE_SQUASH_STRING='{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":"git merge --squash feature"}'
BAD_PACK_STRING='{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":"git commit -m '\''Pack 1.1 bad'\''"}'
PATCH_DOCS='{"hook_event_name":"PreToolUse","tool_name":"apply_patch","tool_input":"*** Begin Patch\n*** Update File: docs/example.md\n@@\n-old\n+new\n*** End Patch"}'
MALFORMED='{not json'

POST_STRING_RESPONSE_FILE="$WORKSPACE/post-string-response.json"
PRE_STRING_INPUT_FILE="$WORKSPACE/pre-string-input.json"
MERGE_SQUASH_FILE="$WORKSPACE/merge-squash.json"
BAD_PACK_FILE="$WORKSPACE/bad-pack.json"
PATCH_DOCS_FILE="$WORKSPACE/patch-docs.json"
MALFORMED_FILE="$WORKSPACE/malformed.json"

printf '%s' "$POST_STRING_RESPONSE" > "$POST_STRING_RESPONSE_FILE"
printf '%s' "$PRE_STRING_INPUT" > "$PRE_STRING_INPUT_FILE"
printf '%s' "$MERGE_SQUASH_STRING" > "$MERGE_SQUASH_FILE"
printf '%s' "$BAD_PACK_STRING" > "$BAD_PACK_FILE"
printf '%s' "$PATCH_DOCS" > "$PATCH_DOCS_FILE"
printf '%s' "$MALFORMED" > "$MALFORMED_FILE"

write_push_payload() {
  local output_file="$1"
  local workdir="$2"
  jq -n --arg workdir "$workdir" \
    '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"cmd":"git push origin test","workdir":$workdir}}' \
    > "$output_file"
}

run_test "track-execution-state tolerates string tool_response" \
  bash -c "cd '$WORKSPACE' && bash '$TRACK_EXEC' < '$POST_STRING_RESPONSE_FILE'"

run_test "cleanup-before-push tolerates string tool_response" \
  bash -c "cd '$WORKSPACE' && bash '$CLEANUP' < '$POST_STRING_RESPONSE_FILE'"

run_test "guard-premature-push tolerates string tool_input" \
  bash -c "cd '$WORKSPACE' && bash '$GUARD_PUSH' < '$PRE_STRING_INPUT_FILE'"

run_test_expect_code "guard-premature-push blocks squash from string tool_input" 2 \
  bash -c "cd '$WORKSPACE' && bash '$GUARD_PUSH' < '$MERGE_SQUASH_FILE'"

SCOPED_PASS_WORKSPACE="$WORKSPACE/scoped-pass"
SCOPED_PASS_PAYLOAD="$WORKSPACE/scoped-pass-push.json"
mkdir -p "$SCOPED_PASS_WORKSPACE/.codex/multi-model-workflow"
mkdir -p "$SCOPED_PASS_WORKSPACE/docs/orchestrate/plans/active-plan"
mkdir -p "$SCOPED_PASS_WORKSPACE/docs/orchestrate/plans/other-plan"
printf '%s\n' "run-1" > "$SCOPED_PASS_WORKSPACE/.codex/multi-model-workflow/active-run-id"
printf '%s\n' '{"slug":"active-plan"}' > "$SCOPED_PASS_WORKSPACE/.codex/multi-model-workflow/workflow-state-run-1.json"
printf '%s\n' "- [x] active task complete" > "$SCOPED_PASS_WORKSPACE/docs/orchestrate/plans/active-plan/plan.md"
printf '%s\n' "- [ ] unrelated task pending" > "$SCOPED_PASS_WORKSPACE/docs/orchestrate/plans/other-plan/plan.md"
write_push_payload "$SCOPED_PASS_PAYLOAD" "$SCOPED_PASS_WORKSPACE"

run_test "guard-premature-push ignores unchecked tasks outside active run plan" \
  bash -c "bash '$GUARD_PUSH' < '$SCOPED_PASS_PAYLOAD'"

SCOPED_BLOCK_WORKSPACE="$WORKSPACE/scoped-block"
SCOPED_BLOCK_PAYLOAD="$WORKSPACE/scoped-block-push.json"
mkdir -p "$SCOPED_BLOCK_WORKSPACE/.codex/multi-model-workflow"
mkdir -p "$SCOPED_BLOCK_WORKSPACE/docs/orchestrate/plans/active-plan"
printf '%s\n' "run-1" > "$SCOPED_BLOCK_WORKSPACE/.codex/multi-model-workflow/active-run-id"
printf '%s\n' '{"slug":"active-plan"}' > "$SCOPED_BLOCK_WORKSPACE/.codex/multi-model-workflow/workflow-state-run-1.json"
printf '%s\n' "- [ ] active task pending" > "$SCOPED_BLOCK_WORKSPACE/docs/orchestrate/plans/active-plan/plan.md"
write_push_payload "$SCOPED_BLOCK_PAYLOAD" "$SCOPED_BLOCK_WORKSPACE"

run_test_expect_code "guard-premature-push blocks unchecked tasks inside active run plan" 2 \
  bash -c "bash '$GUARD_PUSH' < '$SCOPED_BLOCK_PAYLOAD'"

FALLBACK_PASS_WORKSPACE="$WORKSPACE/fallback-pass"
FALLBACK_PASS_PAYLOAD="$WORKSPACE/fallback-pass-push.json"
mkdir -p "$FALLBACK_PASS_WORKSPACE"
git -C "$FALLBACK_PASS_WORKSPACE" -c init.defaultBranch=main init >/dev/null
git -C "$FALLBACK_PASS_WORKSPACE" config user.email test@example.com
git -C "$FALLBACK_PASS_WORKSPACE" config user.name "Hook Test"
mkdir -p "$FALLBACK_PASS_WORKSPACE/docs/orchestrate/plans/other-plan"
printf '%s\n' "- [ ] unrelated baseline task pending" > "$FALLBACK_PASS_WORKSPACE/docs/orchestrate/plans/other-plan/plan.md"
git -C "$FALLBACK_PASS_WORKSPACE" add docs
git -C "$FALLBACK_PASS_WORKSPACE" commit -m baseline >/dev/null
git -C "$FALLBACK_PASS_WORKSPACE" update-ref refs/remotes/origin/main HEAD
mkdir -p "$FALLBACK_PASS_WORKSPACE/docs/orchestrate/plans/current-plan"
printf '%s\n' "- [x] current task complete" > "$FALLBACK_PASS_WORKSPACE/docs/orchestrate/plans/current-plan/plan.md"
git -C "$FALLBACK_PASS_WORKSPACE" add docs
git -C "$FALLBACK_PASS_WORKSPACE" commit -m current-plan >/dev/null
write_push_payload "$FALLBACK_PASS_PAYLOAD" "$FALLBACK_PASS_WORKSPACE"

run_test "guard-premature-push falls back to changed plan dirs after cleanup" \
  bash -c "bash '$GUARD_PUSH' < '$FALLBACK_PASS_PAYLOAD'"

FALLBACK_BLOCK_WORKSPACE="$WORKSPACE/fallback-block"
FALLBACK_BLOCK_PAYLOAD="$WORKSPACE/fallback-block-push.json"
mkdir -p "$FALLBACK_BLOCK_WORKSPACE"
git -C "$FALLBACK_BLOCK_WORKSPACE" -c init.defaultBranch=main init >/dev/null
git -C "$FALLBACK_BLOCK_WORKSPACE" config user.email test@example.com
git -C "$FALLBACK_BLOCK_WORKSPACE" config user.name "Hook Test"
mkdir -p "$FALLBACK_BLOCK_WORKSPACE/docs/orchestrate/plans/other-plan"
printf '%s\n' "- [ ] unrelated baseline task pending" > "$FALLBACK_BLOCK_WORKSPACE/docs/orchestrate/plans/other-plan/plan.md"
git -C "$FALLBACK_BLOCK_WORKSPACE" add docs
git -C "$FALLBACK_BLOCK_WORKSPACE" commit -m baseline >/dev/null
git -C "$FALLBACK_BLOCK_WORKSPACE" update-ref refs/remotes/origin/main HEAD
mkdir -p "$FALLBACK_BLOCK_WORKSPACE/docs/orchestrate/plans/current-plan"
printf '%s\n' "- [ ] current task pending" > "$FALLBACK_BLOCK_WORKSPACE/docs/orchestrate/plans/current-plan/plan.md"
git -C "$FALLBACK_BLOCK_WORKSPACE" add docs
git -C "$FALLBACK_BLOCK_WORKSPACE" commit -m current-plan >/dev/null
write_push_payload "$FALLBACK_BLOCK_PAYLOAD" "$FALLBACK_BLOCK_WORKSPACE"

run_test_expect_code "guard-premature-push blocks unchecked changed plan dirs after cleanup" 2 \
  bash -c "bash '$GUARD_PUSH' < '$FALLBACK_BLOCK_PAYLOAD'"

mkdir -p "$WORKSPACE/.codex/multi-model-workflow"
echo "shape-test" > "$WORKSPACE/.codex/multi-model-workflow/active-run-id"
printf '{}' > "$WORKSPACE/.codex/multi-model-workflow/workflow-state-shape-test.json"

run_test_expect_code "enforce-pack-commit validates string command input" 2 \
  bash -c "cd '$WORKSPACE' && bash '$ENFORCE_COMMIT' < '$BAD_PACK_FILE'"

touch "$WORKSPACE/.codex/multi-model-workflow/worker-active"
run_test_expect_code "guard-doc-edit blocks docs patch string input for worker" 2 \
  bash -c "cd '$WORKSPACE' && bash '$GUARD_DOC' < '$PATCH_DOCS_FILE'"

run_test "track-effort-budget tolerates malformed JSON" \
  bash -c "cd '$WORKSPACE' && bash '$TRACK_EFFORT' < '$MALFORMED_FILE'"

run_test "agent-return-handler tolerates malformed JSON" \
  bash -c "cd '$WORKSPACE' && bash '$AGENT_RETURN' < '$MALFORMED_FILE'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
