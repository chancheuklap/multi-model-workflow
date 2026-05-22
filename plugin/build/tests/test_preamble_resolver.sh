#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RESOLVER="$BUILD_DIR/resolvers/preamble.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0
fail=0

echo "=== test_preamble_resolver.sh ==="

# --- Test 1: resolver outputs template content ---
mkdir -p "$FIXTURE_DIR/build/templates"
cat > "$FIXTURE_DIR/build/templates/preamble.md.tmpl" <<'TMPL'
**Hard Gate**: 每个 phase 开始前必须确认 scope 和 state。

**Only stop for:**
- BLOCKED
- 用户确认
TMPL

output=$(bash "$RESOLVER" "$FIXTURE_DIR/build/templates" "preamble" "" 2>&1)
if echo "$output" | grep -q "Hard Gate"; then
  echo "  PASS: resolver outputs template content"
  pass=$((pass + 1))
else
  echo "  FAIL: resolver output missing expected content"
  fail=$((fail + 1))
fi

# --- Test 2: resolver fails on missing template ---
if bash "$RESOLVER" "/nonexistent/path" "preamble" "" >/dev/null 2>&1; then
  echo "  FAIL: resolver should fail on missing template"
  fail=$((fail + 1))
else
  echo "  PASS: resolver fails on missing template"
  pass=$((pass + 1))
fi

# --- Test 3: resolver output matches template exactly ---
expected=$(cat "$FIXTURE_DIR/build/templates/preamble.md.tmpl")
if [[ "$output" == "$expected" ]]; then
  echo "  PASS: resolver output matches template exactly"
  pass=$((pass + 1))
else
  echo "  FAIL: resolver output differs from template"
  diff <(echo "$expected") <(echo "$output") || true
  fail=$((fail + 1))
fi

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
