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
  echo ready > "$FIXTURE_STATE/alpha-ready"
  read -r ready < "$FIXTURE_STATE/overlap"
  touch "$FIXTURE_STATE/alpha-done"
  echo 'alpha saw overlap'
}
scenario_beta() {
  echo 'beta output starts'
  read -r ready < "$FIXTURE_STATE/alpha-ready"
  echo ready > "$FIXTURE_STATE/overlap"
  echo 'beta saw overlap'
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
run_fixture() {
  python3 - "$TMP/scenarios.sh" "$@" <<'PYFIXTURE'
import os
import signal
import subprocess
import sys

process = subprocess.Popen(["bash", *sys.argv[1:]], start_new_session=True)
try:
    sys.exit(process.wait(timeout=10))
except subprocess.TimeoutExpired:
    os.killpg(process.pid, signal.SIGKILL)
    process.wait()
    print("fixture scenarios did not complete their overlap handshake within 10 seconds", file=sys.stderr)
    sys.exit(2)
PYFIXTURE
}
mkfifo "$TMP/alpha-ready" "$TMP/overlap"
code=0
MMW_TEST_JOBS=2 run_fixture alpha beta broken omega > "$TMP/out" 2>&1 || code=$?
[ "$code" -eq 1 ] || { cat "$TMP/out"; echo "expected exit 1, got $code" >&2; exit 1; }
[ -f "$MMW_TEST_BOARD_LOCK" ] || { cat "$TMP/out"; echo "runner ignored fixture port lock $MMW_TEST_BOARD_LOCK" >&2; exit 1; }
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
mkfifo "$TMP/alpha-ready" "$TMP/overlap"
MMW_TEST_JOBS=2 run_fixture all > "$TMP/all" 2>&1 && { echo 'all hid a failure' >&2; exit 1; }
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
python3 - "$TMP" <<'PYKILL'
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(sys.argv[1])
fixture = root / "killed.sh"
pids = root / "killed-pids"
fixture.write_text("""#!/usr/bin/env bash
set -uo pipefail
work() {
  echo "$$" >> "$FIXTURE_STATE/killed-pids"
  sleep 60 &
  echo "$!" >> "$FIXTURE_STATE/killed-pids"
  wait
}
scenario_a() { work; }
scenario_b() { work; }
source "$RUNNER_UNDER_TEST"
run_scenarios "$0" "$@"
""")
def running(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True)
    return result.returncode == 0 and not result.stdout.lstrip().startswith("Z")

process = subprocess.Popen(["bash", str(fixture), "all"], env=dict(os.environ, MMW_TEST_JOBS="2"),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
owned = []
try:
    deadline = time.monotonic() + 5
    while not pids.exists() or len(pids.read_text().splitlines()) < 4:
        assert time.monotonic() < deadline, "forced-timeout scenarios never started"
        time.sleep(.01)
    owned = [int(pid) for pid in pids.read_text().splitlines()]
    os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=3)
    deadline = time.monotonic() + 3
    while any(running(pid) for pid in owned) and time.monotonic() < deadline:
        time.sleep(.02)
    assert not any(running(pid) for pid in owned), f"forced timeout left scenario processes alive: {owned}"
finally:
    if pids.exists():
        owned = [int(pid) for pid in pids.read_text().splitlines()]
    for pid in owned:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
PYKILL
echo 'parallel runner reports failures'
