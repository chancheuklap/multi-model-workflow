#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATOR="$SCRIPT_DIR/../pack-count-validator.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_pack_count_validator.sh ==="

# Create test plan under threshold
cat > "$FIXTURE_DIR/plan-ok.md" <<'EOF'
### Pack 1.1: First
### Pack 1.2: Second
### Pack 1.3: Third
EOF

# Create test plan over threshold
cat > "$FIXTURE_DIR/plan-over.md" <<'EOF'
### Pack 1.1: One
### Pack 1.2: Two
### Pack 1.3: Three
### Pack 1.4: Four
### Pack 1.5: Five
EOF

# Create bootstrap plan
cat > "$FIXTURE_DIR/plan-bootstrap.md" <<'EOF'
<!-- self-violation acknowledgment: bootstrap plan -->
### Pack 1.1: One
### Pack 1.2: Two
### Pack 1.3: Three
### Pack 1.4: Four
### Pack 1.5: Five
EOF

# 1. Under threshold
run_test "under threshold passes" \
  bash "$VALIDATOR" "$FIXTURE_DIR/plan-ok.md" 5

# 2. Over threshold
run_test_expect_fail "over threshold fails" \
  bash "$VALIDATOR" "$FIXTURE_DIR/plan-over.md" 4

# 3. Bootstrap exception
run_test "bootstrap exception passes" \
  bash "$VALIDATOR" "$FIXTURE_DIR/plan-bootstrap.md" 4

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
