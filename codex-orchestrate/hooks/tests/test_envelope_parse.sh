#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE="$SCRIPT_DIR/../lib/parse-envelope.sh"

pass=0
fail=0

run_test() { local n="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $n"; pass=$((pass+1)); else echo "  FAIL: $n"; fail=$((fail+1)); fi; }
run_test_fail() { local n="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $n (expected failure)"; fail=$((fail+1)); else echo "  PASS: $n (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_envelope_parse.sh ==="

# Valid envelope
VALID='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"pack_executor","agent_id":null,"pack_id":"1.1","repair_round":0,"idempotency_key":"r1/1.1/r0","disposition_refs":null,"review_intent":null,"exception_code":null} -->'

run_test "valid envelope parses" bash -c "echo '$VALID' | bash '$PARSE'"

# Missing envelope
run_test_fail "missing envelope → exit 2" bash -c "echo 'no envelope here' | bash '$PARSE'"

# Malformed JSON
run_test_fail "malformed JSON → exit 2" bash -c "echo '<!-- DISPATCH_ENVELOPE {bad json} -->' | bash '$PARSE'"

# Missing required field
run_test_fail "missing run_id → exit 2" bash -c "echo '<!-- DISPATCH_ENVELOPE {\"protocol_version\":\"1\",\"phase\":\"execution\",\"agent_role\":\"pack_executor\",\"repair_round\":0,\"idempotency_key\":\"k\"} -->' | bash '$PARSE'"

# repair_round >= 1 without disposition_refs
REPAIR_NO_REFS='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"pack_executor","pack_id":"1.1","repair_round":2,"idempotency_key":"r1/1.1/r2","disposition_refs":null,"review_intent":null,"exception_code":null} -->'
run_test_fail "repair_round=2 + null disposition_refs → exit 2" bash -c "echo '$REPAIR_NO_REFS' | bash '$PARSE'"

# codex_reviewer without review_intent
CODEX_NO_INTENT='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"codex_reviewer","pack_id":null,"repair_round":0,"idempotency_key":"r1/review/r0","disposition_refs":null,"review_intent":null,"exception_code":null} -->'
run_test_fail "codex_reviewer + null review_intent → exit 2" bash -c "echo '$CODEX_NO_INTENT' | bash '$PARSE'"

# targeted-re-review without exception_code
TARGETED_NO_EX='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"codex_reviewer","pack_id":null,"repair_round":0,"idempotency_key":"r1/review/r0","disposition_refs":null,"review_intent":"targeted-re-review","exception_code":null} -->'
run_test_fail "targeted-re-review + null exception_code → exit 2" bash -c "echo '$TARGETED_NO_EX' | bash '$PARSE'"

# Legacy path-a-re-review intent must not parse. Path A uses targeted-re-review
# plus exception_code=path_a_self_fix on send_input to the baseline reviewer.
PATH_A_LEGACY='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"codex_reviewer","pack_id":null,"repair_round":0,"idempotency_key":"r1/review/r0","disposition_refs":null,"review_intent":"path-a-re-review","exception_code":null} -->'
run_test_fail "legacy path-a-re-review intent → exit 2" bash -c "echo '$PATH_A_LEGACY' | bash '$PARSE'"

# Valid codex_reviewer with baseline
BASELINE='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"codex_reviewer","pack_id":null,"repair_round":0,"idempotency_key":"r1/review/r0","disposition_refs":null,"review_intent":"baseline","exception_code":null} -->'
run_test "baseline review_intent valid" bash -c "echo '$BASELINE' | bash '$PARSE'"

# Valid repair with disposition_refs
REPAIR_OK='<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"pack_executor","pack_id":"1.1","repair_round":1,"idempotency_key":"r1/1.1/r1","disposition_refs":["F1","F3"],"review_intent":null,"exception_code":null} -->'
run_test "repair with disposition_refs valid" bash -c "echo '$REPAIR_OK' | bash '$PARSE'"

# Multi-line envelope (production format from control-envelope.md.tmpl)
MULTILINE='<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "r2",
  "phase": "execution",
  "agent_role": "pack_executor",
  "agent_id": null,
  "pack_id": "2.1",
  "repair_round": 0,
  "idempotency_key": "r2/2.1/r0",
  "disposition_refs": null,
  "review_intent": null,
  "exception_code": null
}
-->'
run_test "multi-line envelope parses" bash -c "printf '%s' '$MULTILINE' | bash '$PARSE'"

# Multi-line envelope with surrounding text
MULTILINE_CONTEXT="Some prompt text before.
<!-- DISPATCH_ENVELOPE
{\"protocol_version\":\"1\",\"run_id\":\"r3\",\"phase\":\"plan-writing\",\"agent_role\":\"plan_writer\",\"agent_id\":null,\"pack_id\":null,\"repair_round\":0,\"idempotency_key\":\"r3/plan/r0\",\"disposition_refs\":null,\"review_intent\":null,\"exception_code\":null}
-->
More prompt text after."
run_test "multi-line envelope with surrounding text" bash -c "printf '%s' '$MULTILINE_CONTEXT' | bash '$PARSE'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
