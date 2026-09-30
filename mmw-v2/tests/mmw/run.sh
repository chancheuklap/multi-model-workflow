#!/usr/bin/env bash
# Tests the pstack importer and mode scripts against disposable fixtures.
# Usage: bash mmw-v2/tests/mmw/run.sh [-k <pattern>]
# Needs uv (supplies pyyaml), python3 and git. Empty or skipped selections fail.

set -euo pipefail
bash "$(dirname -- "${BASH_SOURCE[0]}")/../lib/run_shared_lints.sh" || exit 1
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
unset MMW_TICKET MMW_BASE_REF MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)
# shellcheck source-path=SCRIPTDIR
# shellcheck source=../lib/parse_k.sh
. "$HERE/../lib/parse_k.sh"
if uv run --quiet --with pyyaml python -u "$HERE/../lib/run_unittests.py" "$HERE" "$pattern"; then
  echo "all passed"
else
  exit 1
fi
