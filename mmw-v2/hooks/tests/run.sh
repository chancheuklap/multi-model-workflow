#!/usr/bin/env bash
# Run the hook's tests. Run after any change to rule-at-moment.py.
#
#   bash mmw-v2/hooks/tests/run.sh
#
#   test_rule_at_moment.py   rule-at-moment.py against fixed stdin and a fixed CLAUDE.md
#
# It needs no host.

set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if python3 -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
