#!/usr/bin/env bash
# Real-host measurements for #611, never an acceptance CHECK.
set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
exec python3 -B "$HERE/run_probes.py" "$@"
