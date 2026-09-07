#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/claude-design-blocks/run.sh
#
# unittest over a miniature handoff package; Node runs the page LOGIC, no browser.
# `node` has to be on PATH; without it the run fails rather than passing on
# half the tests.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# Node colours stack frames when FORCE_COLOR is set, even on captured stderr;
# the failed-scene test then sees a frame instead of the thrown error.
unset FORCE_COLOR

if ! command -v node >/dev/null 2>&1; then
  echo "claude-design-blocks failed: node is not on PATH" >&2
  exit 1
fi

if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
