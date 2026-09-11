#!/usr/bin/env bash
set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
rc=0

for test_file in "$HERE"/test_*.py; do
  name="$(basename "$test_file")"
  if [[ "$name" == "test_story_page.py" || "$name" == "test_interact.py" ]]; then
    uv run --quiet --with playwright python -m unittest discover -s "$HERE" -p "$name" || rc=1
  else
    python3 -m unittest discover -s "$HERE" -p "$name" || rc=1
  fi
done

shopt -s nullglob
for test_file in "$HERE"/*.test.mjs; do
  node --test "$test_file" || rc=1
done

if [[ "$rc" -eq 0 ]]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
