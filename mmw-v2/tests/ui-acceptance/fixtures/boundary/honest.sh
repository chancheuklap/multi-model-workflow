#!/usr/bin/env bash
# Passes unless MMW_NEGATIVE=1: a test that actually depends on its interaction.
set -euo pipefail
if [ "${MMW_NEGATIVE:-}" = "1" ]; then
  echo "interaction skipped"
  exit 1
fi
echo "interaction ran"
exit 0
