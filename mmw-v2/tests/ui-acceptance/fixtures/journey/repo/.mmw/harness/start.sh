#!/bin/sh
# A product of one page and a write/read API, on this run's own port, recorded so
# `stop` can end what it started and nothing else. Its break switch belongs to the
# product process and fails only the method and route pattern MMW_BREAK names.
set -e
rm -f .mmw/stop-ran
python3 .mmw/harness/server.py >"$MMW_DATA_DIR/http.log" 2>&1 &
echo $! > "$MMW_DATA_DIR/pid"
# Return only once the product answers, not merely once it is alive.
i=0
while [ $i -lt 100 ]; do
  if curl -sf "http://127.0.0.1:$MMW_PORT_BASE/health" >/dev/null 2>&1; then
    if [ -n "${MMW_BREAK:-}" ]; then echo "BREAK ARMED $MMW_BREAK"; fi
    exit 0
  fi
  i=$((i + 1))
  sleep 0.1
done
echo "the fixture product did not come up on 127.0.0.1:$MMW_PORT_BASE" >&2
exit 1
