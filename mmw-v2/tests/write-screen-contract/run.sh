#!/usr/bin/env bash
# Run this skill's tests. Run after any change under scripts/.
#
#   bash mmw-v2/tests/write-screen-contract/run.sh [-k <pattern>]
#
# unittest over fixed contracts and a hand-written handoff package; no tracker.
# The skeleton cases render that package with real headless Chromium.
#
# A skip count other than 0, or a run count of 0, exits non-zero and does not
# print `all passed`.

set -euo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# A suite run from inside a worker session must not inherit that session's ticket
# or Memory boundary. These tests do not read the variables; stripping them is
# the runner convention in mmw-v2/tests/AGENTS.md.
unset MMW_TICKET MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"  # mmw-v2/tests/lib/parse_k.sh

if ! command -v uv >/dev/null 2>&1; then
  echo "write-screen-contract failed: uv is not on PATH" >&2
  exit 1
fi

if uv run --quiet --with pyyaml --with 'playwright>=1.58' \
  python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
