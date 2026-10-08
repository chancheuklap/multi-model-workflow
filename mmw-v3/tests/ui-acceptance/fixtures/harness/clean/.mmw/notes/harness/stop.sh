#!/bin/sh
# Ends only what this run recorded as its own, and exits 0 with nothing of its own to end.
if [ -f "$MMW_DATA_DIR/pid" ]; then
  kill "$(cat "$MMW_DATA_DIR/pid")" 2>/dev/null || true
  rm -f "$MMW_DATA_DIR/pid"
fi
echo stop-ran > .mmw/stop-ran
