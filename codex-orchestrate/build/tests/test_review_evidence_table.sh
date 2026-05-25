#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0

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

echo "=== test_review_evidence_table.sh ==="

TEMPLATE="$PLUGIN_DIR/build/templates/review-dispatch.md.tmpl"
ADHOC="$PLUGIN_DIR/skills/codex-review/SKILL.md"
EXECUTION_SKILL="$PLUGIN_DIR/skills/orchestrate-execution/SKILL.md"

run_test "review-dispatch template requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$TEMPLATE"

run_test "review-dispatch template requires unverified items" \
  grep -q "未验证项" "$TEMPLATE"

while IFS= read -r ref; do
  run_test "$(basename "$ref") includes evidence table contract" \
    grep -q "证据表 (REQUIRED)" "$ref"
  run_test "$(basename "$ref") requires unverified items" \
    grep -q "未验证项" "$ref"
done < <(grep -rl "BEGIN: review-dispatch" "$PLUGIN_DIR/skills" | sort)

run_test "ad-hoc codex-review requires evidence table" \
  grep -q "证据表 (REQUIRED)" "$ADHOC"

run_test "ad-hoc codex-review requires source evidence row" \
  grep -q "已读设计 / mockup / plan 来源" "$ADHOC"

run_test "ad-hoc codex-review requires unverified items" \
  grep -q "未验证项" "$ADHOC"

run_test "Plan Implementation Review inline prompt requires evidence table" bash -c \
  "awk '/Review prompt 写入 .*plan-impl-review-N\\.md/{flag=1} flag{print} /Plan Implementation Review finding 必须标注/{flag=0}' '$EXECUTION_SKILL' | grep -q '证据表 (REQUIRED)'"

run_test "Plan Implementation Review inline prompt requires unverified items" bash -c \
  "awk '/Review prompt 写入 .*plan-impl-review-N\\.md/{flag=1} flag{print} /Plan Implementation Review finding 必须标注/{flag=0}' '$EXECUTION_SKILL' | grep -q '未验证项'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
