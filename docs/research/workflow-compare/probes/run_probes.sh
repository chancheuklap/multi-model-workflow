#!/usr/bin/env bash
# Real-host measurements, never an acceptance CHECK.
set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [ "${1:-}" = --u7 ]; then
  shift
  exec python3 -B "$HERE/run_u7.py" "$@"
fi
exec python3 -B "$HERE/run_probes.py" "$@"
