#!/usr/bin/env bash
# Tests redline-check.sh advisory 红线探测器:
#   - 含 billing/auth/migration/endpoint 的输入 → exit 0 + 命中类别
#   - 纯文案输入 → exit 1
#   - args 与 stdin 两种入口都生效
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REDLINE_SH="$SCRIPT_DIR/../redline-check.sh"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }

echo "=== test_redline_check.sh ==="

# --- 命中红线 → exit 0 ---
run_test "billing path → exit 0" \
  bash -c "bash '$REDLINE_SH' 'src/billing/charge.py'"
run_test "billing path prints 'billing' category" \
  bash -c "bash '$REDLINE_SH' 'src/billing/charge.py' | grep -qx billing"

run_test "auth keyword → exit 0" \
  bash -c "bash '$REDLINE_SH' 'src/middleware/permission_check.py'"
run_test "auth prints 'auth' category" \
  bash -c "bash '$REDLINE_SH' 'modified permission acl' | grep -qx auth"

run_test "migration keyword → exit 0 (data-authority)" \
  bash -c "bash '$REDLINE_SH' 'alembic/versions/0042_add.py migration'"
run_test "migration prints 'data-authority' category" \
  bash -c "bash '$REDLINE_SH' 'migration schema change' | grep -qx data-authority"

run_test "endpoint keyword → exit 0 (user-contract)" \
  bash -c "bash '$REDLINE_SH' 'added new endpoint /v2/orders'"
run_test "endpoint prints 'user-contract' category" \
  bash -c "bash '$REDLINE_SH' 'new public endpoint' | grep -qx user-contract"

# --- 纯文案输入 → exit 1 ---
run_test "pure copy change → exit 1" \
  bash -c "! bash '$REDLINE_SH' 'docs/copy.md 改文案'"
run_test "plain prose → exit 1" \
  bash -c "! bash '$REDLINE_SH' 'fix typo in README and adjust button color'"

# --- stdin 入口 ---
run_test "billing via stdin → exit 0" \
  bash -c "echo 'src/billing/charge.py' | bash '$REDLINE_SH'"
run_test "pure copy via stdin → exit 1" \
  bash -c "! (echo 'just a wording tweak' | bash '$REDLINE_SH')"

# --- 多类别命中（输出多行）---
run_test "multi-category billing+auth+migration+endpoint → exit 0" \
  bash -c "bash '$REDLINE_SH' 'billing auth migration endpoint'"
run_test "multi-category prints 4 lines" \
  bash -c "[[ \$(bash '$REDLINE_SH' 'billing auth migration endpoint' | wc -l | tr -d ' ') -eq 4 ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
