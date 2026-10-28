#!/usr/bin/env bash
set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export RUNNER_UNDER_TEST="$HERE/parallel.sh" FIXTURE_STATE="$TMP"
export MMW_TEST_BOARD_LOCK="$TMP/ports.lock"
cat > "$TMP/scenarios.sh" <<'FIXTURE'
#!/usr/bin/env bash
set -uo pipefail
rc=0
scenario_alpha() {
  echo 'alpha output starts'
  touch "$FIXTURE_STATE/alpha-ready"
  for ((i=0; i<100; i++)); do
    if [ -f "$FIXTURE_STATE/overlap" ]; then
      touch "$FIXTURE_STATE/alpha-done"
      echo 'alpha saw overlap'
      return 0
    fi
    sleep .01
  done
  echo 'alpha did not overlap' >&2
  return 1
}
scenario_beta() {
  echo 'beta output starts'
  touch "$FIXTURE_STATE/overlap"
  for ((i=0; i<100; i++)); do
    if [ -f "$FIXTURE_STATE/alpha-ready" ]; then
      echo 'beta saw overlap'
      return 0
    fi
    sleep .01
  done
  echo 'beta did not overlap' >&2
  return 1
}
scenario_broken() {
  echo 'broken diagnostic' >&2
  return 7
}
scenario_omega() {
  [ -f "$FIXTURE_STATE/alpha-done" ] || return 1
  echo 'omega output'
}
needs_exclusive_ports() { [ "$1" = omega ]; }
source "$RUNNER_UNDER_TEST"
run_scenarios "$0" "$@"
FIXTURE
code=0
MMW_TEST_JOBS=2 bash "$TMP/scenarios.sh" alpha beta broken omega > "$TMP/out" 2>&1 || code=$?
[ -f "$MMW_TEST_BOARD_LOCK" ] || { cat "$TMP/out"; echo "runner ignored fixture port lock $MMW_TEST_BOARD_LOCK" >&2; exit 1; }
[ "$code" -eq 1 ] || { cat "$TMP/out"; echo "expected exit 1, got $code" >&2; exit 1; }
python3 - "$TMP/out" <<'PY'
from pathlib import Path
import sys
out = Path(sys.argv[1]).read_text()
for text in ('PASS alpha', 'PASS beta', 'PASS omega', 'FAIL broken', 'broken diagnostic', 'alpha saw overlap'):
    assert text in out, f'missing {text}:\n{out}'
assert 'alpha did not overlap' not in out, out
assert '=== alpha\nalpha output starts\nalpha saw overlap\nPASS alpha\n' in out, out
assert '=== beta\nbeta output starts\nbeta saw overlap\nPASS beta\n' in out, out
assert '=== omega\nomega output\nPASS omega\n' in out, out
assert out.index('FAIL broken') < out.rindex('broken diagnostic'), out
PY
rm "$TMP/overlap" "$TMP/alpha-done" "$TMP/alpha-ready"
MMW_TEST_JOBS=2 bash "$TMP/scenarios.sh" all > "$TMP/all" 2>&1 && { echo 'all hid a failure' >&2; exit 1; }
grep -qx 'PASS omega' "$TMP/all" || { cat "$TMP/all"; echo 'all did not report PASS omega' >&2; exit 1; }
for unknown in nosuchscenario 'alpha broken'; do
  code=0
  bash "$TMP/scenarios.sh" "$unknown" > "$TMP/unknown" 2>&1 || code=$?
  [ "$code" -eq 2 ] || { cat "$TMP/unknown"; echo "unknown name exited $code, expected 2" >&2; exit 1; }
  grep -q 'alpha' "$TMP/unknown" || { cat "$TMP/unknown"; echo 'unknown-name error omitted known scenario alpha' >&2; exit 1; }
done
code=0
MMW_TEST_JOBS=0 bash "$TMP/scenarios.sh" alpha omega > "$TMP/jobs" 2>&1 || code=$?
[ "$code" -eq 2 ] || { cat "$TMP/jobs"; echo "invalid MMW_TEST_JOBS exited $code, expected 2" >&2; exit 1; }
python3 - "$TMP" <<'PYLOCKTEST'
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(sys.argv[1])
fixture = root / "ports.sh"
log = root / "ports.log"
fixture.write_text("""#!/usr/bin/env bash
set -uo pipefail
port_user() {
  echo "start $$" >> "$FIXTURE_STATE/ports.log"
  sleep .2
  echo "end $$" >> "$FIXTURE_STATE/ports.log"
}
scenario_first() { port_user; }
scenario_second() { port_user; }
needs_exclusive_ports() { return 0; }
source "$RUNNER_UNDER_TEST"
run_scenarios "$0" "$@"
""")
first = subprocess.Popen(["bash", str(fixture), "first", "second"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
try:
    deadline = time.monotonic() + 3
    while not log.exists():
        assert time.monotonic() < deadline, "first port scenario never started"
        time.sleep(.01)
    second = subprocess.Popen(["bash", str(fixture), "first", "second"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        for process in (first, second):
            output, _ = process.communicate(timeout=5)
            assert process.returncode == 0, output.decode()
    finally:
        if second.poll() is None:
            second.kill()
            second.wait()
finally:
    if first.poll() is None:
        first.kill()
        first.wait()
lines = log.read_text().splitlines()
assert len(lines) == 8, lines
for start, end in zip(lines[::2], lines[1::2]):
    assert start.startswith("start ") and end == start.replace("start ", "end "), f"suite port users overlapped: {lines}"
PYLOCKTEST
python3 - "$TMP" <<'PYINTERRUPT'
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(sys.argv[1])
fixture = root / "interrupt.sh"
log = root / "started.log"
fixture.write_text("""#!/usr/bin/env bash
set -uo pipefail
work() { echo "$1" >> "$FIXTURE_STATE/started.log"; sleep .3; }
scenario_a() { work a; }
scenario_b() { work b; }
scenario_c() { work c; }
scenario_d() { work d; }
source "$RUNNER_UNDER_TEST"
run_scenarios "$0" "$@"
""")
process = subprocess.Popen(["bash", str(fixture), "all"], env=dict(os.environ, MMW_TEST_JOBS="1"),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
try:
    deadline = time.monotonic() + 3
    while not log.exists():
        assert time.monotonic() < deadline, "interrupt fixture never started"
        time.sleep(.01)
    os.killpg(process.pid, signal.SIGINT)
    output, _ = process.communicate(timeout=3)
    assert process.returncode != 0, output.decode()
    assert log.read_text().splitlines() == ["a"], f"interrupted run started queued scenarios: {log.read_text()}"
finally:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
PYINTERRUPT
echo 'parallel runner reports failures'
