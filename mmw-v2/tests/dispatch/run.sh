#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/dispatch/run.sh
#
# Two engines, three test files:
#
#   test_status.py      unittest, status.py against a fixed paseo ls/inspect snapshot and ticket set
#   test_profiles.py    unittest, models.bypass_argv, catalog match, adopt, create_agent settings, CLI scan
#   test_dispatch.sh    dispatch.sh against a fake `paseo` and a fake `gh` on PATH
#
# None needs the tracker, a terminal or a browser.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

unset MMW_CATALOG_MODE

# The suite runs its own fixtures, so the session's own identity has to be off the
# environment first. `dispatch.sh` reads `MMW_SPEC`, `MMW_TICKET` and `MMW_KIND` to know
# which ticket the session it is running in belongs to; a worker session sets all three,
# and under one of those the fixtures get labelled with that session's spec instead of
# the fake parent the scenarios assert on, so `start-worker` fails on `spec label` while
# the same suite is green from a plain shell. A test that passes or fails by who ran it
# is not a test. Measured 2026-09-10 on #320. `MMW_EVENTS_PY` goes for the same reason:
# `dispatch.sh` exports it to every command it runs, pointing at its own checkout's
# events.py, and `status.py` and `relay.py` would load that one instead of this checkout's.
unset MMW_SPEC MMW_TICKET MMW_KIND MMW_EVENTS_PY

rc=0

echo "### unittest"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "### unittest passed"
else
  echo "### unittest failed" >&2
  rc=1
fi

echo
echo "### dispatch.sh"
# dispatch.sh asks git about the current checkout, so this one runs with the tests
# directory as its working directory rather than wherever run.sh was called from.
if (cd "$HERE" && bash ./test_dispatch.sh all); then
  echo "### dispatch.sh passed"
else
  echo "### dispatch.sh failed" >&2
  rc=1
fi

echo
if [ "$rc" -eq 0 ]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
