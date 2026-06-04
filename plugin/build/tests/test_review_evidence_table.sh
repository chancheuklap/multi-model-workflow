#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CANONICAL="$PLUGIN_DIR/skills/_shared/review-dispatch.md"
QUARTET="$PLUGIN_DIR/skills/_shared/review-prompt-quartet.md"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.content-only.md.tmpl"
ADHOC="$PLUGIN_DIR/skills/codex-review/SKILL.md"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_evidence_table.sh ==="

# Evidence table moved to review-prompt-quartet.md (§1: auto-injected into每个 review prompt
# by dispatch-review.sh validate, out of the Coordinator's dispatch read path)
run_test "review-prompt-quartet requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$QUARTET"

run_test "review-prompt-quartet requires unverified items" \
  grep -q "未验证项" "$QUARTET"

# dispatch-review.sh auto-injects the quartet into the prompt
run_test "dispatch-review.sh injects review-prompt-quartet" \
  grep -q "review-prompt-quartet" "$PLUGIN_DIR/scripts/dispatch-review.sh"

# Canonical review-dispatch points at the quartet (single source, not inlined)
run_test "canonical review-dispatch references quartet" \
  grep -q "review-prompt-quartet" "$CANONICAL"

# Content-only template source (codex-review ad-hoc variant)
run_test "review-dispatch content-only template requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$TEMPLATE"

run_test "review-dispatch content-only template requires unverified items" \
  grep -q "未验证项" "$TEMPLATE"

# Codex-review ad-hoc (content-only variant still injected via build)
run_test "ad-hoc codex-review requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$ADHOC"

# Files referencing canonical via Read directive
while IFS= read -r ref; do
  run_test "$(basename "$ref") references canonical review-dispatch" \
    grep -q "plugin/skills/_shared/review-dispatch.md" "$ref"
done < <(grep -rl "plugin/skills/_shared/review-dispatch.md" "$PLUGIN_DIR/skills" | grep -v '_shared' | sort)

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
