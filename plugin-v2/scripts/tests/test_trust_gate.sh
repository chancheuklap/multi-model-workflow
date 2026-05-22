#!/usr/bin/env bash
# Tests learnings-jsonl.sh trust gate: confidence < 4 filtered; decay-based filtering.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LEARNINGS_SH="$SCRIPT_DIR/../learnings-jsonl.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_trust_gate.sh ==="

# Append learnings with different confidence levels
bash "$LEARNINGS_SH" append --content "low confidence learning" --confidence 2 --source "test" --run-id "r1" >/dev/null
bash "$LEARNINGS_SH" append --content "medium confidence learning" --confidence 5 --source "test" --run-id "r1" >/dev/null
bash "$LEARNINGS_SH" append --content "high confidence learning" --confidence 8 --source "test" --run-id "r1" >/dev/null
bash "$LEARNINGS_SH" append --content "no source learning" --confidence 7 --run-id "r1" >/dev/null

# Test 1: read without trust gate returns all entries
run_test "read without gate returns all 4 entries" \
  bash -c "[[ \$(bash '$LEARNINGS_SH' read | jq length) -eq 4 ]]"

# Test 2: read with trust gate filters low confidence (< 4)
run_test "trust gate filters confidence < 4" \
  bash -c "! bash '$LEARNINGS_SH' read --with-trust-gate | jq -e '.[] | select(.content == \"low confidence learning\")'"

# Test 3: medium confidence passes trust gate
run_test "medium confidence (5) passes gate" \
  bash -c "bash '$LEARNINGS_SH' read --with-trust-gate | jq -e '.[] | select(.content == \"medium confidence learning\")'"

# Test 4: high confidence passes trust gate
run_test "high confidence (8) passes gate" \
  bash -c "bash '$LEARNINGS_SH' read --with-trust-gate | jq -e '.[] | select(.content == \"high confidence learning\")'"

# Test 5: missing source attribution is filtered
run_test "missing source attribution filtered" \
  bash -c "! bash '$LEARNINGS_SH' read --with-trust-gate | jq -e '.[] | select(.content == \"no source learning\")'"

# Test 6: create a stale entry (old timestamp) — should be filtered by decay
# Manually write a JSONL entry with a timestamp 1 year ago
OLD_TS=$(date -j -v-365d -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "365 days ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "2024-01-01T00:00:00Z")
echo "{\"schema_version\":1,\"timestamp\":\"$OLD_TS\",\"run_id\":\"r0\",\"source_project\":\"\",\"agent_role\":\"\",\"type\":\"pattern\",\"content\":\"very old learning\",\"tags\":[],\"files\":[],\"confidence\":5,\"source\":\"test\"}" >> "$FIXTURE_DIR/learnings.jsonl"

# confidence=5, decay after 365 days = 365/30 ≈ 12, effective = 5 - 12 = -7 < 1 -> filtered
run_test "stale entry (365 days old, conf 5) filtered by decay" \
  bash -c "! bash '$LEARNINGS_SH' read --with-trust-gate | jq -e '.[] | select(.content == \"very old learning\")'"

# --- R3-15: stale file reference filter ---
# Add a learning with a nonexistent file path
echo '{"schema_version":1,"timestamp":"2026-05-22T01:00:00Z","run_id":"r1","source_project":"","agent_role":"","type":"pattern","content":"stale file ref learning","tags":[],"files":["nonexistent/path/does-not-exist.py"],"confidence":8,"source":"test"}' >> "$FIXTURE_DIR/learnings.jsonl"

run_test "stale file reference filtered by trust gate" \
  bash -c "! bash '$LEARNINGS_SH' read --with-trust-gate | jq -e '.[] | select(.content == \"stale file ref learning\")'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
