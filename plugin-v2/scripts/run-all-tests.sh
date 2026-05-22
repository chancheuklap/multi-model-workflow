#!/usr/bin/env bash
# Runs all test suites for plugin-v2.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

total_pass=0
total_fail=0
suites=0
failed_suites=()

run_suite() {
  local path="$1"
  local name
  name="$(basename "$path")"

  if [[ ! -x "$path" ]]; then
    chmod +x "$path"
  fi

  echo ""
  echo "=== $name ==="
  suites=$((suites + 1))

  if bash "$path" 2>/dev/null; then
    true
  else
    failed_suites+=("$name")
  fi
}

echo "======================================="
echo " Plugin V2 Test Runner"
echo "======================================="

# Scripts tests
for f in "$PLUGIN_DIR"/scripts/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

# Hook tests
for f in "$PLUGIN_DIR"/hooks/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

# Build tests
for f in "$PLUGIN_DIR"/build/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

echo ""
echo "======================================="
echo " Summary: $suites suites"
if [[ ${#failed_suites[@]} -eq 0 ]]; then
  echo " All suites passed"
  exit 0
else
  echo " ${#failed_suites[@]} suite(s) failed:"
  for s in "${failed_suites[@]}"; do
    echo "   - $s"
  done
  exit 1
fi
