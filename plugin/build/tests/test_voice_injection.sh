#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_voice_injection.sh ==="

# Verify voice-directive anchors in agent files
for agent in code-explorer complex-code-explorer complex-pack-executor docs-worker pack-executor plan-writer root-cause-analyst; do
  run_test "voice-directive anchor in $agent.md" \
    grep -q "BEGIN: voice-directive" "$PLUGIN_DIR/agents/${agent}.md"
done

# Verify voice-directive variants are extractable via inlined resolve_anchor
BUILD_SH="$PLUGIN_DIR/build/build.sh"
run_test "pack-executor variant extractable" \
  bash -c "$(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$PLUGIN_DIR/build/templates'
  resolve_anchor voice-directive pack-executor | grep -q '执行者'"

run_test "workflow variant extractable" \
  bash -c "$(sed -n '/^VOICE_FOOTER=/p; /^resolve_anchor()/,/^}/p' "$BUILD_SH")
  TEMPLATE_DIR='$PLUGIN_DIR/build/templates'
  resolve_anchor voice-directive workflow | grep -q 'Coordinator'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
