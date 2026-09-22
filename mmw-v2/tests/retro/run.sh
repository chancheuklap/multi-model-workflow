#!/usr/bin/env bash
# Isolated command-level retro suite: temporary Git checkout, fake gh and nmem.
# Needs bash, python3 and git. No live tracker, Space, install or product.
# Run one path: bash mmw-v2/tests/retro/run.sh complete-none|partial-evidence|proposal-threshold|prompt-and-record-contract|retry-finalize|large-evidence|all
set -euo pipefail
python3 "$(dirname -- "${BASH_SOURCE[0]}")/../lib/check_module_paths.py" || { echo "a toolbox script names a module file that does not exist (above); fix it before running this suite" >&2; exit 1; }
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
unset MMW_TICKET MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)
export MMW_HOME="$(mktemp -d)"
trap 'rm -rf "$MMW_HOME"' EXIT
python3 "$HERE/test_retro.py" "${1:-all}"
