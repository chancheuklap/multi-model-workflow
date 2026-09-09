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
