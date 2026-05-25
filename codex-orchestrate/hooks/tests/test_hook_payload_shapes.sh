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

run_test "track-execution-state tolerates string tool_response" \
  bash -c "cd '$WORKSPACE' && bash '$TRACK_EXEC' < '$POST_STRING_RESPONSE_FILE'"

run_test "cleanup-before-push tolerates string tool_response" \
  bash -c "cd '$WORKSPACE' && bash '$CLEANUP' < '$POST_STRING_RESPONSE_FILE'"

run_test "guard-premature-push tolerates string tool_input" \
  bash -c "cd '$WORKSPACE' && bash '$GUARD_PUSH' < '$PRE_STRING_INPUT_FILE'"

run_test_expect_code "guard-premature-push blocks squash from string tool_input" 2 \
  bash -c "cd '$WORKSPACE' && bash '$GUARD_PUSH' < '$MERGE_SQUASH_FILE'"

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
