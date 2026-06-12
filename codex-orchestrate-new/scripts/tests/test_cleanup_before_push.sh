#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLEANUP="$SCRIPT_DIR/../cleanup-before-push.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_cleanup_before_push.sh ==="

make_state() {
  local root="$1" run_id="$2" commit_format="${3:-null}" pending="${4:-[]}"
  mkdir -p "$root/.codex/multi-model-workflow"
  echo "$run_id" > "$root/.codex/multi-model-workflow/active-run-id"
  cat > "$root/.codex/multi-model-workflow/workflow-state-${run_id}.json" <<EOF
{
  "run_id": "$run_id",
  "commit_format_override": $commit_format,
  "pending_post_push_reviews": $pending
}
EOF
  echo "artifact" > "$root/.codex/multi-model-workflow/artifact.txt"
}

payload() {
  local command="$1" exit_code="${2:-0}"
  jq -cn --arg command "$command" --argjson exit_code "$exit_code" \
    '{tool_input:{command:$command}, tool_response:{exit_code:$exit_code}}'
}

ROOT_PUSH="$FIXTURE_DIR/push"
make_state "$ROOT_PUSH" "run-push"
run_test "git push does not cleanup state before PR body/post-push checks" \
  bash -c "payload=\$(jq -cn '{tool_input:{command:\"git push -u origin branch\"}, tool_response:{exit_code:0}}'); cd '$ROOT_PUSH' && printf '%s' \"\$payload\" | bash '$CLEANUP' && [[ -d .codex/multi-model-workflow ]]"

ROOT_FAIL="$FIXTURE_DIR/fail"
make_state "$ROOT_FAIL" "run-fail"
run_test "failed gh pr create does not cleanup state" \
  bash -c "payload=\$(jq -cn '{tool_input:{command:\"gh pr create --fill\"}, tool_response:{exit_code:1}}'); cd '$ROOT_FAIL' && printf '%s' \"\$payload\" | bash '$CLEANUP' && [[ -d .codex/multi-model-workflow ]]"

ROOT_PR="$FIXTURE_DIR/pr"
make_state "$ROOT_PR" "run-pr"
run_test "successful gh pr create cleans state" \
  bash -c "payload=\$(jq -cn '{tool_input:{command:\"gh pr create --fill\"}, tool_response:{exit_code:0}}'); cd '$ROOT_PR' && printf '%s' \"\$payload\" | bash '$CLEANUP' && [[ ! -e .codex/multi-model-workflow ]]"

ROOT_EDIT="$FIXTURE_DIR/edit"
make_state "$ROOT_EDIT" "run-edit"
run_test "successful gh pr edit cleans state" \
  bash -c "payload=\$(jq -cn '{tool_input:{command:\"gh pr edit 12 --body-file /tmp/body.md\"}, tool_response:{exit_code:0}}'); cd '$ROOT_EDIT' && printf '%s' \"\$payload\" | bash '$CLEANUP' && [[ ! -e .codex/multi-model-workflow ]]"

ROOT_HOTFIX="$FIXTURE_DIR/hotfix"
make_state "$ROOT_HOTFIX" "run-hotfix" '"hotfix-unreviewed"' '[{"type":"post-push-regression","commit":"abc123"}]'
run_test "hotfix with pending post-push review defers cleanup" \
  bash -c "payload=\$(jq -cn '{tool_input:{command:\"gh pr create --fill\"}, tool_response:{exit_code:0}}'); cd '$ROOT_HOTFIX' && printf '%s' \"\$payload\" | bash '$CLEANUP' && [[ -d .codex/multi-model-workflow ]]"

jq '.pending_post_push_reviews = []' \
  "$ROOT_HOTFIX/.codex/multi-model-workflow/workflow-state-run-hotfix.json" \
  > "$ROOT_HOTFIX/.codex/multi-model-workflow/tmp.json"
mv "$ROOT_HOTFIX/.codex/multi-model-workflow/tmp.json" \
  "$ROOT_HOTFIX/.codex/multi-model-workflow/workflow-state-run-hotfix.json"
run_test "hotfix after post-push review cleanup proceeds" \
  bash -c "payload=\$(jq -cn '{tool_input:{command:\"gh pr edit 12 --body-file /tmp/body.md\"}, tool_response:{exit_code:0}}'); cd '$ROOT_HOTFIX' && printf '%s' \"\$payload\" | bash '$CLEANUP' && [[ ! -e .codex/multi-model-workflow ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
