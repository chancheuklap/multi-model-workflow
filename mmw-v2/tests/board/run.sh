#!/usr/bin/env bash
set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
rc=0
count=0
shopt -s nullglob

for test_file in "$HERE"/test_*.py; do
  name="$(basename "$test_file")"
  count=$((count + 1))
  uv run --quiet --with playwright python -m unittest discover -s "$HERE" -p "$name" || rc=1
done

for test_file in "$HERE"/*.test.mjs; do
  count=$((count + 1))
  node --test "$test_file" || rc=1
done

if [[ "$count" -eq 0 ]]; then
  echo "no board tests found" >&2
  exit 1
elif [[ "$rc" -eq 0 ]]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
