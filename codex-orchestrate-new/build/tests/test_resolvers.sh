#!/usr/bin/env bash
# Tests for the inlined resolve_anchor logic in build.sh.
# Resolvers are no longer separate .sh files; this test validates
# each case branch produces correct output via build.sh --apply on fixtures.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$(cd "$BUILD_DIR/.." && pwd)"
BUILD_SH="$BUILD_DIR/build.sh"

pass=0
fail=0

echo "=== test_resolvers.sh ==="

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

# Helper: source resolve_anchor from build.sh into current shell.
# build.sh calls `usage` (exit 1) without args; we just need the function defined.
# We source with MODE and TEMPLATE_DIR set so set -e / usage guard is bypassed.
_source_resolve_anchor() {
  local tmpl_dir="$1"
  # Extract only the VOICE_FOOTER and resolve_anchor function from build.sh,
  # then eval it so we can call resolve_anchor directly.
  eval "$(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")"
  TEMPLATE_DIR="$tmpl_dir"
}

REAL_TMPL="$PLUGIN_DIR/build/templates"

# ── Type 2: worker-loop (file-level variant: codex, no base) ────────────────
run_test "worker-loop: codex variant matches template" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor worker-loop codex)
  expected=\$(cat '$REAL_TMPL/worker-loop.codex.md.tmpl')
  [[ \"\$out\" == \"\$expected\" ]]
"

run_test "worker-loop: codex variant contains Codex-native dispatch terms" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor worker-loop codex)
  grep -q 'send_input' <<<\"\$out\" && grep -q 'spawn_agent' <<<\"\$out\"
"

run_test "worker-loop: codex variant rejects old worker carriers" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor worker-loop codex)
  ! grep -qE 'SendMessage|CLAUDE_PLUGIN_ROOT|execution-worker-dispatch|plan-executor' <<<\"\$out\"
"

# ── Type 2: control-envelope (file-level variant + cat) ─────────────────────
run_test "control-envelope: no-variant falls back to .md.tmpl" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor control-envelope '')
  expected=\$(cat '$REAL_TMPL/control-envelope.md.tmpl')
  [[ \"\$out\" == \"\$expected\" ]]
"

# ── Type 3: preamble (inline sed variant) ───────────────────────────────────
# preamble uses variants; extract one and verify output is non-empty
if ls "$REAL_TMPL"/preamble.md.tmpl >/dev/null 2>&1; then
  FIRST_PREAMBLE_VARIANT=$(grep -m1 '^\[variant=' "$REAL_TMPL/preamble.md.tmpl" | sed 's/\[variant=\(.*\)\]/\1/' || true)
  if [[ -n "$FIRST_PREAMBLE_VARIANT" ]]; then
    run_test "preamble: variant '$FIRST_PREAMBLE_VARIANT' extracts non-empty" bash -c "
      $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
      TEMPLATE_DIR='$REAL_TMPL'
      out=\$(resolve_anchor preamble '$FIRST_PREAMBLE_VARIANT')
      [[ -n \"\$out\" ]]
    "
  fi
fi

# ── Type 3: signpost (inline sed variant, uses \${anchor_name}.md.tmpl) ─────
if ls "$REAL_TMPL"/signpost.md.tmpl >/dev/null 2>&1; then
  FIRST_SIGNPOST_VARIANT=$(grep -m1 '^\[variant=' "$REAL_TMPL/signpost.md.tmpl" | sed 's/\[variant=\(.*\)\]/\1/' || true)
  if [[ -n "$FIRST_SIGNPOST_VARIANT" ]]; then
    run_test "signpost: variant '$FIRST_SIGNPOST_VARIANT' extracts non-empty" bash -c "
      $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
      TEMPLATE_DIR='$REAL_TMPL'
      out=\$(resolve_anchor signpost '$FIRST_SIGNPOST_VARIANT')
      [[ -n \"\$out\" ]]
    "
  fi
fi

# ── Type 3 (voice): voice-directive with footer single-source ───────────────
VOICE_FOOTER_LINE="禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal."

run_test "voice-directive: pack_executor contains body text" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor voice-directive pack_executor)
  echo \"\$out\" | grep -q '执行者'
"

run_test "voice-directive: pack_executor output ends with footer" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor voice-directive pack_executor)
  last=\$(echo \"\$out\" | tail -1)
  [[ \"\$last\" == '$VOICE_FOOTER_LINE' ]]
"

run_test "voice-directive: workflow contains Coordinator + footer" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor voice-directive workflow)
  echo \"\$out\" | grep -q 'Coordinator' && echo \"\$out\" | grep -q 'delve'
"

run_test "voice-directive: code_explorer contains body + footer" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor voice-directive code_explorer)
  echo \"\$out\" | grep -q '只读调查员' && echo \"\$out\" | grep -q 'delve'
"

run_test "voice-directive: footer appears exactly once in pack_executor output" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor voice-directive pack_executor)
  count=\$(echo \"\$out\" | grep -c 'delve, robust')
  [[ \"\$count\" -eq 1 ]]
"

# ── codex_reviewer dead variant: must NOT be resolvable ────────────────────
run_test "voice-directive: codex_reviewer dead variant returns empty (not in template)" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  out=\$(resolve_anchor voice-directive codex_reviewer 2>/dev/null || true)
  # sed finds no matching block → empty output; footer still appended but no body
  # The important thing: no 独立审查者 content
  ! echo \"\$out\" | grep -q '独立审查者'
"

# ── Unknown anchor: must return 1 ──────────────────────────────────────────
run_test "unknown anchor returns 1" bash -c "
  $(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$REAL_TMPL'
  resolve_anchor nonexistent-anchor '' 2>/dev/null; [[ \$? -ne 0 ]]
"

# ── Resolver files are gone ─────────────────────────────────────────────────
run_test "resolvers directory is empty (no .sh files)" bash -c "
  count=\$(ls '$BUILD_DIR/resolvers/'*.sh 2>/dev/null | wc -l | tr -d ' ')
  [[ \"\$count\" -eq 0 ]]
"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
