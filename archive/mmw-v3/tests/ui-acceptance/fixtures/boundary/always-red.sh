#!/usr/bin/env bash
# Fails on both passes. Prints more than twenty lines so a MISS can be shown to
# keep only the last twenty.
set -euo pipefail
i=1
while [ "$i" -le 25 ]; do
  echo "red-line-$i"
  i=$((i + 1))
done
exit 1
