#!/bin/sh
# A product of one page, on this run's own port, recorded so `stop` can end what it
# started and nothing else. `.mmw/target.json`'s `start` is the only way a run brings a
# product up, and it takes everything it needs from the lease in its environment.
set -e
rm -f .mmw/stop-ran
mkdir -p "$MMW_DATA_DIR/www"
echo ok > "$MMW_DATA_DIR/www/health"
cd "$MMW_DATA_DIR/www"
python3 -m http.server "$MMW_PORT_BASE" --bind 127.0.0.1 >"$MMW_DATA_DIR/http.log" 2>&1 &
echo $! > "$MMW_DATA_DIR/pid"
# Return only once the product answers, not merely once it is alive.
i=0
while [ $i -lt 100 ]; do
  if curl -sf "http://127.0.0.1:$MMW_PORT_BASE/health" >/dev/null 2>&1; then exit 0; fi
  i=$((i + 1))
  sleep 0.1
done
echo "the fixture product did not come up on 127.0.0.1:$MMW_PORT_BASE" >&2
exit 1
