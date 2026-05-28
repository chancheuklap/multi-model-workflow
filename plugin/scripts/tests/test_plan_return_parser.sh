#!/usr/bin/env bash
# Plan 005 Pack 5.15: plan-return-parser.sh unit tests.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSER_LIB="$(cd "$SCRIPT_DIR/.." && pwd)/lib/plan-return-parser.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

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

echo "=== test_plan_return_parser.sh ==="

# Sanity: lib exists and source produces parse_plan_return function
( source "$PARSER_LIB" && type parse_plan_return >/dev/null )
assert_eq "lib is sourceable" "$?" "0"

# Happy path
GOOD="$FIXTURE_DIR/good.json"
cat > "$GOOD" <<EOF
{"schema_version":"1","run_id":"r-1","plan_id":"005","verdict":"pass","per_pack":{"5.1":{"status":"committed","commit_sha":"abc"},"5.2":{"status":"committed","commit_sha":"def"},"5.3":{"status":"blocked","reason":"x"}},"doc_patch_path":"plan-returns/r-1/005/doc-patch.diff","open_items_path":"plan-returns/r-1/005/open-items.json"}
EOF

# Run parser in a subshell so exports don't pollute next test
OUT=$(
  source "$PARSER_LIB"
  parse_plan_return "$GOOD" 2>&1
  echo "VERDICT=$PLAN_RETURN_VERDICT"
  echo "PLAN_ID=$PLAN_RETURN_PLAN_ID"
  echo "RUN_ID=$PLAN_RETURN_RUN_ID"
  echo "COMMITTED=$PLAN_RETURN_COMMITTED_COUNT"
  echo "BLOCKED=$PLAN_RETURN_BLOCKED_COUNT"
  echo "DOC_PATCH=$PLAN_RETURN_DOC_PATCH_PATH"
  echo "OPEN_ITEMS=$PLAN_RETURN_OPEN_ITEMS_PATH"
)

assert_eq "happy path: VERDICT" "$(echo "$OUT" | grep '^VERDICT=' | cut -d= -f2)" "pass"
assert_eq "happy path: PLAN_ID" "$(echo "$OUT" | grep '^PLAN_ID=' | cut -d= -f2)" "005"
assert_eq "happy path: RUN_ID" "$(echo "$OUT" | grep '^RUN_ID=' | cut -d= -f2)" "r-1"
assert_eq "happy path: COMMITTED_COUNT" "$(echo "$OUT" | grep '^COMMITTED=' | cut -d= -f2)" "2"
assert_eq "happy path: BLOCKED_COUNT" "$(echo "$OUT" | grep '^BLOCKED=' | cut -d= -f2)" "1"

# Missing file
MISSING="$FIXTURE_DIR/missing.json"
( source "$PARSER_LIB" && parse_plan_return "$MISSING" ) >/dev/null 2>&1
RC=$?
assert_eq "missing file → return 2" "$RC" "2"

# Invalid JSON
BAD="$FIXTURE_DIR/bad.json"
echo "not json" > "$BAD"
( source "$PARSER_LIB" && parse_plan_return "$BAD" ) >/dev/null 2>&1
RC=$?
assert_eq "invalid JSON → return 2" "$RC" "2"

# Wrong schema_version
WSV="$FIXTURE_DIR/wsv.json"
echo '{"schema_version":"2","run_id":"r","plan_id":"p","verdict":"pass","per_pack":{}}' > "$WSV"
( source "$PARSER_LIB" && parse_plan_return "$WSV" ) >/dev/null 2>&1
RC=$?
assert_eq "wrong schema_version → return 2" "$RC" "2"

# Invalid verdict
IV="$FIXTURE_DIR/iv.json"
echo '{"schema_version":"1","run_id":"r","plan_id":"p","verdict":"awesome","per_pack":{}}' > "$IV"
( source "$PARSER_LIB" && parse_plan_return "$IV" ) >/dev/null 2>&1
RC=$?
assert_eq "invalid verdict → return 2" "$RC" "2"

# Each verdict enum accepted
for v in pass partial-pass blocked need-fresh-worker needs-context needs-plan-revision; do
  TMP="$FIXTURE_DIR/$v.json"
  printf '{"schema_version":"1","run_id":"r","plan_id":"p","verdict":"%s","per_pack":{}}\n' "$v" > "$TMP"
  ( source "$PARSER_LIB" && parse_plan_return "$TMP" ) >/dev/null 2>&1
  RC=$?
  assert_eq "verdict '$v' accepted" "$RC" "0"
done

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
