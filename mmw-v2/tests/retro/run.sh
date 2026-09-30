#!/usr/bin/env bash
# Isolated command-level retro suite: temporary Git checkout, fake gh and nmem.
# Needs bash, python3 and git. No live tracker, Space, install or product.
# Run one path: bash mmw-v2/tests/retro/run.sh complete-none|partial-evidence|proposal-threshold|prompt-and-record-contract|retry-finalize|large-evidence|parent-without-map|all
set -euo pipefail
bash "$(dirname -- "${BASH_SOURCE[0]}")/../lib/run_shared_lints.sh" || exit 1
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
unset MMW_TICKET MMW_CATALOG_MODE MMW_SPEC MMW_TASK_SCOPE MMW_KIND MMW_EVENTS_PY
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)
export MMW_HOME="$(mktemp -d)"
trap 'rm -rf "$MMW_HOME"' EXIT
python3 "$HERE/test_retro.py" "${1:-all}"
