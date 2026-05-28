#!/usr/bin/env bash
# Plan 005 Pack 5.15: doc-patch-apply.sh unit tests.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPLY_LIB="$(cd "$SCRIPT_DIR/.." && pwd)/lib/doc-patch-apply.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0
fail=0

assert_eq() {
  local name="$1" actual="$2" expected="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name — expected '$expected', got '$actual'"
    fail=$((fail + 1))
  fi
}

# Setup fresh git repo in fixture
cd "$FIXTURE_DIR"
git init -q
git config user.email "test@test"
git config user.name "test"

mkdir -p docs/orchestrate/plans/slug
cat > docs/orchestrate/plans/slug/005-foo.md <<'EOF'
# Plan 005

## Acceptance criteria

- [ ] item A
- [ ] item B
- [ ] item C
EOF

git add -A
git commit -q -m "init"

echo "=== test_doc_patch_apply.sh ==="

# Lib sources
( source "$APPLY_LIB" && type apply_doc_patch >/dev/null )
assert_eq "lib is sourceable" "$?" "0"

# Happy path: tick items A + B
# Generate a real patch by ticking 2 items in place, then `git diff` and undo.
sed -i.bak 's/- \[ \] item A/- [x] item A/' docs/orchestrate/plans/slug/005-foo.md
sed -i.bak 's/- \[ \] item B/- [x] item B/' docs/orchestrate/plans/slug/005-foo.md
rm -f docs/orchestrate/plans/slug/005-foo.md.bak
git diff > /tmp/patch.diff
git checkout -q -- docs/orchestrate/plans/slug/005-foo.md

(
  source "$APPLY_LIB"
  apply_doc_patch /tmp/patch.diff
) >/dev/null 2>&1
RC=$?
assert_eq "happy path apply returns 0" "$RC" "0"

# Verify file was actually updated
TICKED=$(grep -c '\- \[x\]' docs/orchestrate/plans/slug/005-foo.md)
assert_eq "2 items now ticked" "$TICKED" "2"

# File should be staged
STAGED=$(git diff --cached --name-only | grep -c "005-foo.md")
assert_eq "file is staged for commit" "$STAGED" "1"

# Reset for next case
git reset --hard -q HEAD

# Conflict case: patch references base content that no longer exists
cat > /tmp/conflict.diff <<'EOF'
diff --git a/docs/orchestrate/plans/slug/005-foo.md b/docs/orchestrate/plans/slug/005-foo.md
index 0000000..1111111 100644
--- a/docs/orchestrate/plans/slug/005-foo.md
+++ b/docs/orchestrate/plans/slug/005-foo.md
@@ -1,3 +1,3 @@
-# DIFFERENT TITLE THAT DOES NOT MATCH
+# New title

 ## Acceptance criteria
EOF

(
  source "$APPLY_LIB"
  apply_doc_patch /tmp/conflict.diff
) >/dev/null 2>&1
RC=$?
assert_eq "conflict apply returns 2" "$RC" "2"

# Working tree should remain clean (no partial apply)
STATUS=$(git status --porcelain)
assert_eq "working tree clean after conflict" "$STATUS" ""

# Missing patch
( source "$APPLY_LIB" && apply_doc_patch /tmp/nonexistent.diff ) >/dev/null 2>&1
RC=$?
assert_eq "missing patch returns 2" "$RC" "2"

# Empty patch
: > /tmp/empty.diff
( source "$APPLY_LIB" && apply_doc_patch /tmp/empty.diff ) >/dev/null 2>&1
RC=$?
assert_eq "empty patch is no-op (returns 0)" "$RC" "0"

rm -f /tmp/patch.diff /tmp/conflict.diff /tmp/empty.diff

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
