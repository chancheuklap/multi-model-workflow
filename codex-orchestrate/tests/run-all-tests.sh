#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
failed=()
count=0

for test_file in "$TEST_DIR"/test_*.sh; do
  [[ -f "$test_file" ]] || continue
  count=$((count + 1))
  echo "== $(basename "$test_file") =="
  if bash "$test_file"; then
    echo "PASS $(basename "$test_file")"
  else
    failed+=("$(basename "$test_file")")
    echo "FAIL $(basename "$test_file")"
  fi
done

if [[ ${#failed[@]} -gt 0 ]]; then
  printf 'Failed tests:\n' >&2
  printf ' - %s\n' "${failed[@]}" >&2
  exit 1
fi

echo "All $count test suites passed"
