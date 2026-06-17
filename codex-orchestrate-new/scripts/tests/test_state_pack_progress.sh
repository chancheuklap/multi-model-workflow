#!/usr/bin/env bash
# Plan 005 Pack 5.7: state.sh pack-progress + execution-plan complete + plan-returns ingest.
# Naming aligned with design 9 enforcement #5.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="pp-test"
pass=0
fail=0

assert_eq() {
  local name="$1" actual="$2" expected="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name — expected '$expected', got '$actual'"
    fail=$((fail + 1))
  fi
}

echo "=== test_state_pack_progress.sh ==="

# Build a fixture execution-state with 3 packs in plan 005
ESF="$FIXTURE_DIR/execution-state-$RUN_ID.json"
cat > "$ESF" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"},"5.3":{"status":"pending"}}}}}
EOF

# --- pack-progress ---
bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "005" --pack-id "5.1" \
  --status committed --commit-sha "abc123" 2>/dev/null
S=$(jq -r '.plans["005"].packs["5.1"].status' "$ESF")
SHA=$(jq -r '.plans["005"].packs["5.1"].commit_sha' "$ESF")
assert_eq "pack-progress writes status committed" "$S" "committed"
assert_eq "pack-progress writes commit_sha" "$SHA" "abc123"

# pack-progress with status=blocked
bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "005" --pack-id "5.2" \
  --status blocked 2>/dev/null
S=$(jq -r '.plans["005"].packs["5.2"].status' "$ESF")
assert_eq "pack-progress writes status blocked" "$S" "blocked"

# Invalid status rejected
if bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "005" --pack-id "5.3" \
   --status garbage 2>/dev/null; then
  echo "  FAIL: invalid status should be rejected"
  fail=$((fail + 1))
else
  echo "  PASS: invalid status correctly rejected"
  pass=$((pass + 1))
fi

# Unknown pack_id rejected
if bash "$STATE_SH" pack-progress --run-id "$RUN_ID" --plan-id "005" --pack-id "5.99" \
   --status committed 2>/dev/null; then
  echo "  FAIL: unknown pack_id should be rejected"
  fail=$((fail + 1))
else
  echo "  PASS: unknown pack_id correctly rejected"
  pass=$((pass + 1))
fi

# --- execution-plan complete ---
bash "$STATE_SH" execution-plan complete --run-id "$RUN_ID" --plan-id "005" \
  --verdict pass 2>/dev/null
PVERDICT=$(jq -r '.plans["005"].worker_verdict' "$ESF")
PFINISHED=$(jq -r '.plans["005"].finished_at' "$ESF")
assert_eq "execution-plan complete writes worker_verdict" "$PVERDICT" "pass"
if [[ "$PFINISHED" == "null" ]] || [[ -z "$PFINISHED" ]]; then
  echo "  FAIL: execution-plan complete should write finished_at (got null)"
  fail=$((fail + 1))
else
  echo "  PASS: execution-plan complete writes finished_at ($PFINISHED)"
  pass=$((pass + 1))
fi

# Verdict enum validation
if bash "$STATE_SH" execution-plan complete --run-id "$RUN_ID" --plan-id "005" \
   --verdict invalid-verdict 2>/dev/null; then
  echo "  FAIL: invalid verdict should be rejected"
  fail=$((fail + 1))
else
  echo "  PASS: invalid verdict correctly rejected"
  pass=$((pass + 1))
fi

# All 6 verdicts accepted
for v in pass partial-pass blocked need-fresh-worker needs-context needs-plan-revision; do
  if bash "$STATE_SH" execution-plan complete --run-id "$RUN_ID" --plan-id "005" \
     --verdict "$v" 2>/dev/null; then
    echo "  PASS: verdict '$v' accepted"
    pass=$((pass + 1))
  else
    echo "  FAIL: verdict '$v' should be accepted"
    fail=$((fail + 1))
  fi
done

# --- plan-returns ingest ---
# Setup: write a plan-return.json fixture
PR_DIR="$FIXTURE_DIR/plan-returns/$RUN_ID/005"
mkdir -p "$PR_DIR"
cat > "$PR_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"005","verdict":"partial-pass","per_pack":{"5.1":{"status":"committed","commit_sha":"abc"},"5.2":{"status":"committed","commit_sha":"def"},"5.3":{"status":"blocked","reason":"failed verification"}}}
EOF

# Reset execution-state for ingest test
cat > "$ESF" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"packs":{"5.1":{"status":"pending"},"5.2":{"status":"pending"},"5.3":{"status":"pending"}}}}}
EOF

bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "005" 2>/dev/null
RC=$?
assert_eq "plan-returns ingest returns 0" "$RC" "0"
S51=$(jq -r '.plans["005"].packs["5.1"].status' "$ESF")
S53=$(jq -r '.plans["005"].packs["5.3"].status' "$ESF")
VERDICT=$(jq -r '.plans["005"].worker_verdict' "$ESF")
assert_eq "ingest: 5.1 status committed" "$S51" "committed"
assert_eq "ingest: 5.3 status blocked" "$S53" "blocked"
assert_eq "ingest: worker_verdict mirrored" "$VERDICT" "partial-pass"
END_COMMIT=$(jq -r '.plans["005"].end_commit' "$ESF")
assert_eq "ingest: end_commit uses last committed pack sha" "$END_COMMIT" "def"

# Ingest missing plan-return.json → error
if bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "nonexistent" 2>/dev/null; then
  echo "  FAIL: ingest of missing plan-return should fail"
  fail=$((fail + 1))
else
  echo "  PASS: ingest of missing plan-return correctly fails"
  pass=$((pass + 1))
fi

# Invalid plan-return JSON → error
BAD_DIR="$FIXTURE_DIR/plan-returns/$RUN_ID/bad"
mkdir -p "$BAD_DIR"
echo "not json" > "$BAD_DIR/plan-return.json"
cat > "$ESF" <<EOF
{"run_id":"$RUN_ID","plans":{"bad":{"packs":{}}}}
EOF
if bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "bad" 2>/dev/null; then
  echo "  FAIL: ingest of bad JSON should fail"
  fail=$((fail + 1))
else
  echo "  PASS: ingest of bad JSON correctly fails"
  pass=$((pass + 1))
fi

# plan-return run_id mismatch → error
MISMATCH_DIR="$FIXTURE_DIR/plan-returns/$RUN_ID/005"
cat > "$MISMATCH_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"wrong-run","plan_id":"005","verdict":"pass","per_pack":{"5.1":{"status":"committed"}}}
EOF
cat > "$ESF" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"packs":{"5.1":{"status":"pending"}}}}}
EOF
if bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "005" 2>/dev/null; then
  echo "  FAIL: ingest with wrong run_id should fail"
  fail=$((fail + 1))
else
  echo "  PASS: ingest with wrong run_id correctly fails"
  pass=$((pass + 1))
fi

# plan-return plan_id mismatch → error
cat > "$MISMATCH_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"999","verdict":"pass","per_pack":{"5.1":{"status":"committed"}}}
EOF
if bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "005" 2>/dev/null; then
  echo "  FAIL: ingest with wrong plan_id should fail"
  fail=$((fail + 1))
else
  echo "  PASS: ingest with wrong plan_id correctly fails"
  pass=$((pass + 1))
fi

# plan-return illegal per_pack status → error
cat > "$MISMATCH_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"005","verdict":"pass","per_pack":{"5.1":{"status":"done"}}}
EOF
if bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "005" 2>/dev/null; then
  echo "  FAIL: ingest with illegal pack status should fail"
  fail=$((fail + 1))
else
  echo "  PASS: ingest with illegal pack status correctly fails"
  pass=$((pass + 1))
fi

# plan-return unknown pack_id → error
cat > "$MISMATCH_DIR/plan-return.json" <<EOF
{"schema_version":"1","run_id":"$RUN_ID","plan_id":"005","verdict":"pass","per_pack":{"5.99":{"status":"committed"}}}
EOF
if bash "$STATE_SH" plan-returns ingest --run-id "$RUN_ID" --plan-id "005" 2>/dev/null; then
  echo "  FAIL: ingest with unknown pack_id should fail"
  fail=$((fail + 1))
else
  echo "  PASS: ingest with unknown pack_id correctly fails"
  pass=$((pass + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
