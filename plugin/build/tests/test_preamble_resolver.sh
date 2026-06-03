#!/usr/bin/env bash
# Tests for the inlined preamble resolve logic (previously in resolvers/preamble.sh).
# Preamble resolver is now inlined into build.sh as a case branch.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_SH="$BUILD_DIR/build.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0
fail=0

echo "=== test_preamble_resolver.sh ==="

# --- Test 1: inlined resolve_anchor outputs template content ---
mkdir -p "$FIXTURE_DIR/build/templates"
cat > "$FIXTURE_DIR/build/templates/preamble.md.tmpl" <<'TMPL'
**Hard Gate**: 每个 phase 开始前必须确认 scope 和 state。

**Only stop for:**
- BLOCKED
- 用户确认
TMPL

output=$(bash -c "
$(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
TEMPLATE_DIR='$FIXTURE_DIR/build/templates'
resolve_anchor preamble ''
" 2>&1)

if echo "$output" | grep -q "Hard Gate"; then
  echo "  PASS: inlined resolve_anchor outputs template content"
  pass=$((pass + 1))
else
  echo "  FAIL: resolve_anchor output missing expected content"
  fail=$((fail + 1))
fi

# --- Test 2: resolve_anchor fails on missing template ---
if bash -c "
$(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
TEMPLATE_DIR='/nonexistent/path'
resolve_anchor preamble ''
" >/dev/null 2>&1; then
  echo "  FAIL: resolve_anchor should fail on missing template"
  fail=$((fail + 1))
else
  echo "  PASS: resolve_anchor fails on missing template"
  pass=$((pass + 1))
fi

# --- Test 3: resolve_anchor output matches template exactly ---
expected=$(cat "$FIXTURE_DIR/build/templates/preamble.md.tmpl")
if [[ "$output" == "$expected" ]]; then
  echo "  PASS: resolve_anchor output matches template exactly"
  pass=$((pass + 1))
else
  echo "  FAIL: resolve_anchor output differs from template"
  diff <(echo "$expected") <(echo "$output") || true
  fail=$((fail + 1))
fi

# --- Test 4: preamble.sh resolver file no longer exists ---
if [[ ! -f "$BUILD_DIR/resolvers/preamble.sh" ]]; then
  echo "  PASS: preamble.sh resolver file correctly removed (inlined into build.sh)"
  pass=$((pass + 1))
else
  echo "  FAIL: preamble.sh resolver still exists (should have been removed)"
  fail=$((fail + 1))
fi

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
