#!/usr/bin/env bash
# Plan 005 Pack 5.11: enforce-plan-commit.sh (renamed from enforce-pack-commit.sh).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/enforce-plan-commit.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
cd "$FIXTURE_DIR"

mkdir -p .codex/multi-model-workflow
echo "test-run" > .codex/multi-model-workflow/active-run-id
echo '{"run_id":"test-run"}' > .codex/multi-model-workflow/workflow-state-test-run.json

pass=0
fail=0

invoke() {
  local cmd="$1"
  local input
  input=$(jq -n --arg c "$cmd" '{tool_input: {command: $c}}')
  echo "$input" | bash "$HOOK"
}

run_test_pass() {
  local name="$1" cmd="$2"
  if invoke "$cmd" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected pass but hook returned non-zero)"
    fail=$((fail + 1))
  fi
}

run_test_block() {
  local name="$1" cmd="$2"
  if ! invoke "$cmd" >/dev/null 2>&1; then
    echo "  PASS: $name (correctly blocked)"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected block but hook returned zero)"
    fail=$((fail + 1))
  fi
}

echo "=== test_enforce_plan_commit.sh ==="

# File exists and old one is gone (Pack 5.14 deletes old hook, but file at new path required now)
if [[ ! -x "$HOOK" ]]; then
  echo "  FAIL: enforce-plan-commit.sh missing or not executable"
  fail=$((fail + 1))
else
  echo "  PASS: enforce-plan-commit.sh exists and is executable"
  pass=$((pass + 1))
fi

run_test_pass "valid Pack N.M commit" \
  'git commit -m "Pack 5.1: worker-loop template — added"'

run_test_pass "valid repair-mode commit" \
  'git commit -m "Pack 5.9: agent-return-handler — repair: handle blocked verdict"'

run_test_block "invalid Pack format (missing colon)" \
  'git commit -m "Pack 5.1 something"'

run_test_block "invalid Pack format (no dot)" \
  'git commit -m "Pack 5: title — summary"'

run_test_pass "non-Pack commit passes through (Coordinator commit)" \
  'git commit -m "chore: bump version"'

run_test_pass "merge commit passes through" \
  'git commit -m "Merge branch foo"'

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
