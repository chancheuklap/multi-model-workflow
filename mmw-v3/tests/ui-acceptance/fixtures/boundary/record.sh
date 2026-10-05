#!/usr/bin/env bash
# Honest exit codes, plus a line per pass so a test can see cwd and MMW_NEGATIVE.
set -euo pipefail
printf 'cwd=%s negative=%s\n' "$(pwd)" "${MMW_NEGATIVE-}" >> "${MMW_BOUNDARY_LOG:?}"
if [ "${MMW_NEGATIVE:-}" = "1" ]; then
  exit 1
fi
exit 0
