#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/align-screens/run.sh
#
# unittest over fixed contracts and a temporary handoff package; no browser, no tracker.
# `lint_contract.py` imports pyyaml, so the tests run through `uv` with it.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if uv run --with pyyaml python -m unittest discover -s "$HERE" -p 'test_*.py'; then
  echo "all passed"
else
  echo "failures above" >&2
  exit 1
fi
