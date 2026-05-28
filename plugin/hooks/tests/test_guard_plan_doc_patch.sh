#!/usr/bin/env bash
# Plan 005 Pack 5.18: guard-plan-doc-patch.sh tests.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/guard-plan-doc-patch.sh"

pass=0
fail=0

assert_pass() {
  local name="$1" file_path="$2" content="$3"
  local input
  input=$(jq -n --arg fp "$file_path" --arg c "$content" \
    '{tool_input:{file_path:$fp,content:$c}}')
  if echo "$input" | bash "$HOOK" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected allow)"
    fail=$((fail + 1))
  fi
}

assert_block() {
  local name="$1" file_path="$2" content="$3"
  local input
  input=$(jq -n --arg fp "$file_path" --arg c "$content" \
    '{tool_input:{file_path:$fp,content:$c}}')
  if ! echo "$input" | bash "$HOOK" >/dev/null 2>&1; then
    echo "  PASS: $name (correctly blocked)"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected block)"
    fail=$((fail + 1))
  fi
}

echo "=== test_guard_plan_doc_patch.sh ==="

# 1. Non doc-patch.diff path → pass through (hook ignores)
assert_pass "non doc-patch.diff path passes through" \
  "/tmp/foo.txt" "any content"

# 2. Empty patch → allow (no-op)
assert_pass "empty patch is no-op" \
  ".claude/multi-model-workflow/plan-returns/r/005/doc-patch.diff" ""

# 3. Valid checkbox toggle → allow
VALID='diff --git a/docs/orchestrate/plans/foo/005-bar.md b/docs/orchestrate/plans/foo/005-bar.md
--- a/docs/orchestrate/plans/foo/005-bar.md
+++ b/docs/orchestrate/plans/foo/005-bar.md
@@ -1,3 +1,3 @@
-- [ ] item A
+- [x] item A
-- [ ] item B
+- [x] item B'
assert_pass "valid checkbox toggle" \
  ".claude/multi-model-workflow/plan-returns/r/005/doc-patch.diff" "$VALID"

# 4. Target not a plan doc → block
WRONG_TARGET='diff --git a/docs/orchestrate/design/foo.md b/docs/orchestrate/design/foo.md
--- a/docs/orchestrate/design/foo.md
+++ b/docs/orchestrate/design/foo.md
@@ -1,1 +1,1 @@
-- [ ] item A
+- [x] item A'
assert_block "target is design doc not plan doc" \
  ".claude/multi-model-workflow/plan-returns/r/005/doc-patch.diff" "$WRONG_TARGET"

# 5. Non-checkbox line in patch → block
NON_CB='diff --git a/docs/orchestrate/plans/foo/005-bar.md b/docs/orchestrate/plans/foo/005-bar.md
--- a/docs/orchestrate/plans/foo/005-bar.md
+++ b/docs/orchestrate/plans/foo/005-bar.md
@@ -1,2 +1,2 @@
-some random text
+different random text'
assert_block "non-checkbox change line" \
  ".claude/multi-model-workflow/plan-returns/r/005/doc-patch.diff" "$NON_CB"

# 6. Checkbox text changed (not pure toggle) → block
TEXT_CHANGED='diff --git a/docs/orchestrate/plans/foo/005-bar.md b/docs/orchestrate/plans/foo/005-bar.md
--- a/docs/orchestrate/plans/foo/005-bar.md
+++ b/docs/orchestrate/plans/foo/005-bar.md
@@ -1,1 +1,1 @@
-- [ ] item A
+- [x] item A renamed'
assert_block "checkbox text changed" \
  ".claude/multi-model-workflow/plan-returns/r/005/doc-patch.diff" "$TEXT_CHANGED"

# 7. Mix of plan doc + non-plan doc target → block
MIXED='diff --git a/docs/orchestrate/plans/foo/005-bar.md b/docs/orchestrate/plans/foo/005-bar.md
--- a/docs/orchestrate/plans/foo/005-bar.md
+++ b/docs/orchestrate/plans/foo/005-bar.md
@@ -1,1 +1,1 @@
-- [ ] item A
+- [x] item A
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,1 +1,1 @@
-- [ ] item B
+- [x] item B'
assert_block "mixed plan + non-plan targets" \
  ".claude/multi-model-workflow/plan-returns/r/005/doc-patch.diff" "$MIXED"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
