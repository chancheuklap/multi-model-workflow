#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/design-pages/run.sh [-k <pattern>]
#
# unittest over miniature Claude Design projects. pull_design.py renders with real
# headless Chromium through `uv run --with playwright`. Missing uv or Chromium
# fails rather than passing half the suite.
#
# A skip count other than 0, or a run count of 0, exits non-zero and does not
# print `all passed`.

set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_upstream_em_dashes.py" >&2 || exit 1

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v2/tests/lib/parse_k.sh

if ! command -v uv >/dev/null 2>&1; then
  echo "design-pages failed: uv is not on PATH" >&2
  exit 1
fi

if uv run --quiet --with 'playwright>=1.58' python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
