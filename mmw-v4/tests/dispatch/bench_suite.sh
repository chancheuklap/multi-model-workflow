#!/usr/bin/env bash
# Times `test_dispatch.sh all` as run.sh runs it, from the tests directory, and counts its PASS lines
# against the scenario functions the file defines.
#
#   bash mmw-v4/tests/dispatch/bench_suite.sh [target seconds]
#
# Prints `SUITE <seconds>s <passed> passed of <defined> scenarios, exit <code>`, then
# `TARGET MET` only when every scenario passed, the suite exited 0 and the wall time is
# at most the target (default 180).
set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
target="${1:-180}"
defined="$(grep -cE '^scenario_[A-Za-z0-9_]+\(\)' "$HERE/test_dispatch.sh")"
start="$(date +%s)"
out="$(cd "$HERE" && env -u MMW_SPEC -u MMW_TICKET -u MMW_TASK_SCOPE -u MMW_KIND -u MMW_EVENTS_PY \
  -u PASEO_AGENT_ID -u ORCA_TERMINAL_HANDLE -u HERDR_PANE_ID \
  bash ./test_dispatch.sh all 2>&1)"
code=$?
seconds=$(( $(date +%s) - start ))
passed="$(grep -c '^PASS ' <<<"$out")"
echo "SUITE ${seconds}s ${passed} passed of ${defined} scenarios, exit ${code}"
if [ "$code" -eq 0 ] && [ "$passed" -eq "$defined" ] && [ "$seconds" -le "$target" ]; then
  echo "TARGET MET"
fi
