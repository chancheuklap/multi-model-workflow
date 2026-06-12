#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"
PARSER="$PLUGIN_DIR/hooks/lib/parse-envelope.sh"
SCHEMA="$PLUGIN_DIR/state-schema/dispatch-envelope-v1.json"

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

echo "=== test_dispatch_envelope_contract.sh ==="

run_test "schema includes all route-worker phases" \
  jq -e '(.properties.phase.enum | index("bug-investigation")) and (.properties.phase.enum | index("direct-repair")) and (.properties.phase.enum | index("multi-pr-merge"))' "$SCHEMA"

run_test "schema allows ad-hoc review intent" \
  jq -e '.properties.review_intent.oneOf[0].enum | index("ad-hoc")' "$SCHEMA"

run_test "generator builds direct-repair envelope" \
  bash -c "bash '$STATE_SH' envelope build --run-id route-contract --phase direct-repair --agent-role pack_executor | bash '$PARSER' | jq -e '.phase == \"direct-repair\"'"

run_test "generator builds ad-hoc reviewer envelope" \
  bash -c "bash '$STATE_SH' envelope build --run-id adhoc-123 --phase execution --agent-role codex_reviewer --review-intent ad-hoc | bash '$PARSER' | jq -e '.review_intent == \"ad-hoc\"'"

run_test_expect_fail "ad-hoc reviewer envelope requires adhoc run id" \
  bash "$STATE_SH" envelope build --run-id formal-123 --phase execution --agent-role codex_reviewer --review-intent ad-hoc

run_test_expect_fail "parser rejects unknown phase" \
  bash -c "echo '<!-- DISPATCH_ENVELOPE {\"protocol_version\":\"1\",\"run_id\":\"r1\",\"phase\":\"unknown\",\"agent_role\":\"pack_executor\",\"repair_round\":0,\"idempotency_key\":\"k\"} -->' | bash '$PARSER'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
