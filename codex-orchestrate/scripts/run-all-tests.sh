#!/usr/bin/env bash
# Runs all Codex Orchestrate test suites, including ported plugin maturity tests.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

suites=0
failed_suites=()

run_suite() {
  local path="$1"
  local name
  name="$(basename "$path")"

  [[ -x "$path" ]] || chmod +x "$path"

  echo ""
  echo "=== $name ==="
  suites=$((suites + 1))

  if bash "$path"; then
    true
  else
    failed_suites+=("$name")
  fi
}

echo "======================================="
echo " Codex Orchestrate Test Runner"
echo "======================================="

for f in "$PLUGIN_DIR"/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

for f in "$PLUGIN_DIR"/scripts/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

for f in "$PLUGIN_DIR"/hooks/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

for f in "$PLUGIN_DIR"/build/tests/test_*.sh; do
  [[ -f "$f" ]] && run_suite "$f"
done

echo ""
echo "======================================="
echo " Summary: $suites suites"
if [[ ${#failed_suites[@]} -eq 0 ]]; then
  echo " All suites passed"
  exit 0
fi

echo " ${#failed_suites[@]} suite(s) failed:"
for s in "${failed_suites[@]}"; do
  echo "   - $s"
done
exit 1
