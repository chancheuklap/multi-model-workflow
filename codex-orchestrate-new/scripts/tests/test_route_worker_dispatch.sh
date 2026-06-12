#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"
DISPATCH="$PLUGIN_DIR/scripts/dispatch-route-worker.sh"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

RUN_ID="multi-pr-route-gate"

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
    echo "  FAIL: $name"
    fail=$((fail + 1))
  else
    echo "  PASS: $name"
    pass=$((pass + 1))
  fi
}

echo "=== test_route_worker_dispatch.sh ==="

STATE_BASE="$TMP_DIR" bash "$STATE_SH" init --run-id "$RUN_ID" --slug route-gate --route multi-pr-merge >/dev/null
STATE_BASE="$TMP_DIR" bash "$STATE_SH" merge-brief init --run-id "$RUN_ID" --slug route-gate >/dev/null

GOOD_PROMPT="$TMP_DIR/good.md"
BAD_PROMPT="$TMP_DIR/bad.md"

{
  STATE_BASE="$TMP_DIR" bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase multi-pr-merge --agent-role pack_executor
  printf '\nRead `.codex/multi-model-workflow/merge-brief-%s.md` before editing.\n' "$RUN_ID"
} > "$GOOD_PROMPT"

STATE_BASE="$TMP_DIR" bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase multi-pr-merge --agent-role pack_executor > "$BAD_PROMPT"

run_test "multi-pr route-worker validate accepts prompt with merge brief reference" \
  env STATE_BASE="$TMP_DIR" bash "$DISPATCH" validate --prompt-file "$GOOD_PROMPT" --transport subagent

run_test_expect_fail "multi-pr route-worker validate calls dedicated merge-brief gate" \
  env STATE_BASE="$TMP_DIR" bash "$DISPATCH" validate --prompt-file "$BAD_PROMPT" --transport subagent

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
