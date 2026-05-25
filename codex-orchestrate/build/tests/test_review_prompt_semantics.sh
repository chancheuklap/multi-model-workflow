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

echo "=== test_review_prompt_semantics.sh ==="

DESIGN_REVIEW="$PLUGIN_DIR/skills/orchestrate-discovery/references/design-review-angles.md"
FINAL_REVIEW="$PLUGIN_DIR/skills/orchestrate-final-review/references/final-review-angles.md"

run_test "design review treats mockup as visual design authority" \
  grep -q "Mockup 是可视化设计文档" "$DESIGN_REVIEW"

run_test "design review requires visual specs from mockup" \
  grep -q "布局/颜色/字体/间距/组件结构" "$DESIGN_REVIEW"

run_test "final review requires reading mockup files" \
  grep -q "Reviewer 必须 Read mockup 目录中的文件" "$FINAL_REVIEW"

run_test "final review extracts intent from mockup files" \
  grep -q "Read mockup 文件，不只看文字描述" "$FINAL_REVIEW"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
