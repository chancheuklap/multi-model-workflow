#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CANONICAL="$PLUGIN_DIR/skills/_shared/review-dispatch.md"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.content-only.md.tmpl"
ADHOC="$PLUGIN_DIR/skills/codex-review/SKILL.md"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_evidence_table.sh ==="

# Canonical reference (D1)
run_test "canonical review-dispatch requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$CANONICAL"

run_test "canonical review-dispatch requires unverified items" \
  grep -q "未验证项" "$CANONICAL"

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
