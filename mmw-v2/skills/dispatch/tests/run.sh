#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/skills/dispatch/tests/run.sh
#
# Two engines, two test runners:
#
#   test_status.py      unittest, status.py against a fixed paseo ls/inspect snapshot and ticket set
#   test_dispatch.sh    dispatch.sh against a fake `herdr` and a fake `gh` on PATH
#
# Neither needs the tracker, a terminal or a browser.

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
