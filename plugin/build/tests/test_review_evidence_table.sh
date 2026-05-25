#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"
ADHOC="$PLUGIN_DIR/skills/codex-review/SKILL.md"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_review_evidence_table.sh ==="

run_test "review-dispatch template requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$TEMPLATE"

run_test "review-dispatch template requires unverified items" \
  grep -q "未验证项" "$TEMPLATE"

while IFS= read -r ref; do
  run_test "$(basename "$ref") includes evidence table contract" \
    grep -q "证据表 (REQUIRED)" "$ref"
done < <(grep -rl "BEGIN: review-dispatch" "$PLUGIN_DIR/skills" | sort)

run_test "ad-hoc codex-review requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$ADHOC"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
