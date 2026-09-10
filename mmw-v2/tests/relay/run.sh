#!/usr/bin/env bash
# Run the relay's tests. Run after any change to relay.py, statedir.py or runners/paseo.sh.
#
#   bash mmw-v2/tests/relay/run.sh
#
# Two engines, two test files:
#
#   test_relay.py   unittest: relay.py against a fake board and a fake send verb, and
#                   statedir.py's directory and lock against real processes
#   test_relay.sh   relay.py end to end: a fake `gh` and a fake `paseo` on PATH, deliveries
#                   through the real runners/paseo.sh adapter
#
# Neither needs the tracker, a runner daemon or the network, and neither touches
# ~/.mmw: both point MMW_HOME at a temporary directory.

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
echo "### relay.py end to end"
if bash "$HERE/test_relay.sh" all; then
  echo "### relay.py end to end passed"
else
  echo "### relay.py end to end failed" >&2
  rc=1
fi

echo
if [ "$rc" -eq 0 ]; then
  echo "all passed"
else
  echo "failures above" >&2
fi
exit "$rc"
