#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$(cd "$BUILD_DIR/.." && pwd)"
BUILD_SH="$BUILD_DIR/build.sh"

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

run_test_expect_fail() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure but got success)"
    fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass + 1))
  fi
}

echo "=== test_build_check.sh ==="

# --- Test 1: build.sh exists and is executable ---
run_test "build.sh exists" test -x "$BUILD_SH"

# --- Test 2: --check on a SKILL.md with up-to-date anchors exits 0 ---
# Create a fixture SKILL.md with a preamble anchor containing expected content
mkdir -p "$FIXTURE_DIR/skills/test-skill"
mkdir -p "$FIXTURE_DIR/build/templates"

cat > "$FIXTURE_DIR/skills/test-skill/SKILL.md" <<'FIXTURE'
---
name: test-skill
description: "test"
---

# Test Skill

<!-- BEGIN: preamble -->
This is the preamble content.
<!-- END: preamble -->

## Step 1
Do something.
FIXTURE

cat > "$FIXTURE_DIR/build/templates/preamble.md.tmpl" <<'TMPL'
This is the preamble content.
TMPL

run_test "--check exits 0 when content matches" \
  bash "$BUILD_SH" --check --plugin-dir "$FIXTURE_DIR"

# --- Test 3: --check exits 1 when template differs from anchor content ---
cat > "$FIXTURE_DIR/build/templates/preamble.md.tmpl" <<'TMPL'
This is MODIFIED preamble content.
TMPL

run_test_expect_fail "--check exits non-0 when content mismatches" \
  bash "$BUILD_SH" --check --plugin-dir "$FIXTURE_DIR"

# --- Test 4: --apply updates the SKILL.md to match template ---
bash "$BUILD_SH" --apply --plugin-dir "$FIXTURE_DIR" 2>/dev/null || true
run_test "--apply updates SKILL.md" \
  grep -q "MODIFIED preamble" "$FIXTURE_DIR/skills/test-skill/SKILL.md"

# --- Test 5: --check exits 0 after --apply ---
run_test "--check exits 0 after --apply" \
  bash "$BUILD_SH" --check --plugin-dir "$FIXTURE_DIR"

# --- Test 6: idempotency — two consecutive --apply produce identical output ---
sha1=$(shasum "$FIXTURE_DIR/skills/test-skill/SKILL.md" | cut -d' ' -f1)
bash "$BUILD_SH" --apply --plugin-dir "$FIXTURE_DIR" 2>/dev/null || true
sha2=$(shasum "$FIXTURE_DIR/skills/test-skill/SKILL.md" | cut -d' ' -f1)
if [[ "$sha1" == "$sha2" ]]; then
  echo "  PASS: idempotency (sha match after second --apply)"
  pass=$((pass + 1))
else
  echo "  FAIL: idempotency (sha mismatch: $sha1 vs $sha2)"
  fail=$((fail + 1))
fi

# --- Test 7: SKILL.md without anchors is left unchanged ---
cat > "$FIXTURE_DIR/skills/test-skill/SKILL.md" <<'NOANCHOR'
---
name: no-anchor
description: "no anchors here"
---

# No Anchors
Just plain content.
NOANCHOR

sha_before=$(shasum "$FIXTURE_DIR/skills/test-skill/SKILL.md" | cut -d' ' -f1)
bash "$BUILD_SH" --apply --plugin-dir "$FIXTURE_DIR" 2>/dev/null || true
sha_after=$(shasum "$FIXTURE_DIR/skills/test-skill/SKILL.md" | cut -d' ' -f1)
if [[ "$sha_before" == "$sha_after" ]]; then
  echo "  PASS: SKILL.md without anchors unchanged"
  pass=$((pass + 1))
else
  echo "  FAIL: SKILL.md without anchors was modified"
  fail=$((fail + 1))
fi

# --- Test 8: TOML agent anchors are checked and applied ---
mkdir -p "$FIXTURE_DIR/agents"
cat > "$FIXTURE_DIR/build/templates/voice-directive.md.tmpl" <<'TMPL'
[variant=pack_executor]
Original TOML voice.
[/variant]
TMPL
cat > "$FIXTURE_DIR/agents/pack_executor.toml" <<'TOML'
name = "pack_executor"
developer_instructions = '''
<!-- BEGIN: voice-directive [variant=pack_executor] -->
Original TOML voice.
禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal.
<!-- END: voice-directive -->
'''
TOML

run_test "--check scans TOML anchors" \
  bash "$BUILD_SH" --check --plugin-dir "$FIXTURE_DIR"

cat > "$FIXTURE_DIR/build/templates/voice-directive.md.tmpl" <<'TMPL'
[variant=pack_executor]
Modified TOML voice.
[/variant]
TMPL

run_test_expect_fail "--check fails on TOML generated drift" \
  bash "$BUILD_SH" --check --plugin-dir "$FIXTURE_DIR"

bash "$BUILD_SH" --apply --plugin-dir "$FIXTURE_DIR" 2>/dev/null
run_test "--apply updates TOML anchors" \
  grep -q "Modified TOML voice" "$FIXTURE_DIR/agents/pack_executor.toml"

# --- Test 9: unresolved anchors fail instead of being silently skipped ---
mkdir -p "$FIXTURE_DIR/skills/bad-skill"
cat > "$FIXTURE_DIR/skills/bad-skill/SKILL.md" <<'BAD'
# Bad Skill

<!-- BEGIN: missing-anchor -->
stale content
<!-- END: missing-anchor -->
BAD

run_test_expect_fail "unresolved anchor fails build check" \
  bash "$BUILD_SH" --check --plugin-dir "$FIXTURE_DIR"
rm -rf "$FIXTURE_DIR/skills/bad-skill"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
