#!/usr/bin/env bash
set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
unset MMW_TICKET MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)
MMW_HOME="$(mktemp -d)"
export MMW_HOME
trap 'rm -rf "$MMW_HOME"' EXIT
# A cached Playwright is a complete test dependency. uv may otherwise refresh
# PyPI for each test file even when the installed package is already usable.
# A fresh machine with no cache still takes the normal online path.
if uv run --offline --quiet --with playwright python -c 'import playwright' >/dev/null 2>&1; then
  export UV_OFFLINE=1
fi
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
