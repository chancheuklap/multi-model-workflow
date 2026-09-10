#!/usr/bin/env bash
# Run the liveness tests. Run after any change to turn-guard.py, watchdog.py, statedir.py,
# or the way install.sh registers the turn guard.
#
#   bash mmw-v2/tests/liveness/run.sh
#
# Two engines, two test files:
#
#   test_liveness.py   unittest: the guard predicate, heartbeat freshness, the tolerance,
#                      the lock's identity against real processes (a recycled pid among
#                      them), and the third layer's three answers against a fake board
#                      and fake runner verbs
#   test_guard.sh      turn-guard.py end to end: each host's turn-end payload, the
#                      hook-collision cases, and one arm of the real watchdog.py
#
# Neither needs a host, the tracker, a runner or the network, and neither touches
# ~/.mmw: both point MMW_HOME at a temporary directory. Neither proves that a real host
# calls the hook with these payloads or honours its answer: that is checked by hand
# against each host, and recorded in turn-guard.py's header.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

rc=0

echo "### unittest"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "### unittest passed"
else
  echo "### unittest failed" >&2
  rc=1
fi

echo
echo "### turn-guard.py end to end"
if bash "$HERE/test_guard.sh"; then
  echo "### turn-guard.py end to end passed"
else
  echo "### turn-guard.py end to end failed" >&2
  rc=1
fi

echo
if [ "$rc" -eq 0 ]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
