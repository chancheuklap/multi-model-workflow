#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GUARD="$SCRIPT_DIR/../guard-premature-push.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

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

payload() {
  jq -cn --arg command "$1" '{tool_input:{command:$command}}'
}

make_repo() {
  local root="$1"
  mkdir -p "$root"
  git -C "$root" init -q
  git -C "$root" config user.email "test@example.com"
  git -C "$root" config user.name "Test User"
  git -C "$root" checkout -q -b main
  mkdir -p "$root/docs/orchestrate/plans/historical"
  printf '# Historical plan\n\n- [ ] historical task\n' > "$root/docs/orchestrate/plans/historical/001-old.md"
  git -C "$root" add docs/orchestrate/plans/historical/001-old.md
  git -C "$root" commit -q -m "seed historical plan"
  git -C "$root" update-ref refs/remotes/origin/main HEAD
}

invoke_guard() {
  local root="$1"
  local command="$2"
  (cd "$root" && payload "$command" | bash "$GUARD")
}

expect_allow() {
  invoke_guard "$1" "$2"
}

expect_block() {
  local root="$1"
  local command="$2"
  if invoke_guard "$root" "$command"; then
    return 1
  fi
  return 0
}

echo "=== test_guard_premature_push.sh ==="

ROOT_NO_SCOPE="$FIXTURE_DIR/no-scope"
make_repo "$ROOT_NO_SCOPE"
run_test "historical unchecked tasks do not block unrelated push" \
  expect_allow "$ROOT_NO_SCOPE" "git push"
run_test "historical unchecked tasks do not block unrelated PR create" \
  expect_allow "$ROOT_NO_SCOPE" "gh pr create --fill"

ROOT_CHANGED="$FIXTURE_DIR/changed-plan"
make_repo "$ROOT_CHANGED"
mkdir -p "$ROOT_CHANGED/docs/orchestrate/plans/current"
printf '# Current plan\n\n- [ ] current task\n' > "$ROOT_CHANGED/docs/orchestrate/plans/current/001-current.md"
git -C "$ROOT_CHANGED" add docs/orchestrate/plans/current/001-current.md
git -C "$ROOT_CHANGED" commit -q -m "add current plan"
run_test "changed plan without active run does not block push" \
  expect_allow "$ROOT_CHANGED" "git push"

ROOT_ACTIVE="$FIXTURE_DIR/active-run"
make_repo "$ROOT_ACTIVE"
mkdir -p "$ROOT_ACTIVE/docs/orchestrate/plans/active"
printf '# Active plan\n\n- [ ] active task\n' > "$ROOT_ACTIVE/docs/orchestrate/plans/active/001-active.md"
mkdir -p "$ROOT_ACTIVE/.codex/multi-model-workflow"
printf 'run-active\n' > "$ROOT_ACTIVE/.codex/multi-model-workflow/active-run-id"
cat > "$ROOT_ACTIVE/.codex/multi-model-workflow/workflow-state-run-active.json" <<'JSON'
{"run_id":"run-active","slug":"active"}
JSON
run_test "active run plan with unchecked task blocks push" \
  expect_block "$ROOT_ACTIVE" "git push"

ROOT_MERGE="$FIXTURE_DIR/merge"
make_repo "$ROOT_MERGE"
run_test "git merge --squash remains blocked" \
  expect_block "$ROOT_MERGE" "git merge --squash feature/test"

ROOT_EXTERNAL="$FIXTURE_DIR/external-env"
make_repo "$ROOT_EXTERNAL"
mkdir -p "$ROOT_EXTERNAL/.codex/multi-model-workflow"
printf 'run-external\n' > "$ROOT_EXTERNAL/.codex/multi-model-workflow/active-run-id"
cat > "$ROOT_EXTERNAL/.codex/multi-model-workflow/workflow-state-run-external.json" <<'JSON'
{"run_id":"run-external","slug":"external"}
JSON
run_test "active run blocks VM start command" \
  expect_block "$ROOT_EXTERNAL" "vmrun start /Users/test/Windows.vmwarevm"
run_test "active run blocks opening VM bundle" \
  expect_block "$ROOT_EXTERNAL" "open /Users/test/Windows.vmwarevm"
run_test "active run blocks Win-PC ssh command" \
  expect_block "$ROOT_EXTERNAL" "ssh pc echo ok"
run_test "active run allows external command after explicit approval marker" \
  expect_allow "$ROOT_EXTERNAL" "MMW_EXTERNAL_ENV_APPROVED=1 vmrun start /Users/test/Windows.vmwarevm"
run_test "active run does not let unrelated approval text authorize later VM command" \
  expect_block "$ROOT_EXTERNAL" "MMW_EXTERNAL_ENV_APPROVED=1 echo approved; vmrun start /Users/test/Windows.vmwarevm"
run_test "active run does not block text search mentioning VM command" \
  expect_allow "$ROOT_EXTERNAL" "grep -R \"vmrun start\" docs"

ROOT_EXTERNAL_NO_SCOPE="$FIXTURE_DIR/external-env-no-scope"
make_repo "$ROOT_EXTERNAL_NO_SCOPE"
run_test "no active run allows VM status/control command guard scope" \
  expect_allow "$ROOT_EXTERNAL_NO_SCOPE" "vmrun start /Users/test/Windows.vmwarevm"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
