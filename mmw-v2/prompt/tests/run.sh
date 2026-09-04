#!/usr/bin/env bash
# Run the prompt renderer's tests. Run after any change to render.py.
#
#   bash mmw-v2/prompt/tests/run.sh
#
#   test_render.py   render.py against a throwaway home under MMW_V2_HOME
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
