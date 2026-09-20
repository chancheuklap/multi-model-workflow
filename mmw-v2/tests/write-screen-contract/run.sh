#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/write-screen-contract/run.sh [-k <pattern>]
#
# unittest over fixed contracts and a temporary handoff package; no browser, no tracker.
# `lint_screen_contract.py` imports pyyaml, so the tests run through `uv` with it.
#
# A skip count other than 0, or a run count of 0, exits non-zero and does not
# print `all passed`.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v2/tests/lib/parse_k.sh

if ! command -v uv >/dev/null 2>&1; then
  echo "write-screen-contract failed: uv is not on PATH" >&2
  exit 1
fi

if uv run --quiet --with pyyaml python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
