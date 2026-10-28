#!/usr/bin/env bash
set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export RUNNER_UNDER_TEST="$HERE/parallel.sh" FIXTURE_STATE="$TMP"
cat > "$TMP/scenarios.sh" <<'FIXTURE'
#!/usr/bin/env bash
set -uo pipefail
rc=0
scenario_alpha() {
  echo 'alpha output starts'
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
scenario_broken() {
  touch "$FIXTURE_STATE/overlap"
  echo 'broken diagnostic' >&2
  return 7
}
scenario_omega() {
  [ -f "$FIXTURE_STATE/alpha-done" ] || return 1
  echo 'omega output'
}
is_serial() { [ "$1" = omega ]; }
source "$RUNNER_UNDER_TEST"
run_scenarios "$0" "$@"
FIXTURE
code=0
MMW_TEST_JOBS=2 bash "$TMP/scenarios.sh" alpha broken omega > "$TMP/out" 2>&1 || code=$?
[ "$code" -eq 1 ] || { cat "$TMP/out"; echo "expected exit 1, got $code" >&2; exit 1; }
python3 - "$TMP/out" <<'PY'
from pathlib import Path
import sys
out = Path(sys.argv[1]).read_text()
for text in ('PASS alpha', 'PASS omega', 'FAIL broken', 'broken diagnostic', 'alpha saw overlap'):
    assert text in out, f'missing {text}:\n{out}'
assert 'alpha did not overlap' not in out, out
assert '=== alpha\nalpha output starts\nalpha saw overlap\nPASS alpha\n' in out, out
assert '=== omega\nomega output\nPASS omega\n' in out, out
assert out.index('FAIL broken') < out.rindex('broken diagnostic'), out
PY
rm "$TMP/overlap" "$TMP/alpha-done"
MMW_TEST_JOBS=2 bash "$TMP/scenarios.sh" all > "$TMP/all" 2>&1 && { echo 'all hid a failure' >&2; exit 1; }
grep -qx 'PASS omega' "$TMP/all"
code=0
bash "$TMP/scenarios.sh" nosuchscenario > "$TMP/unknown" 2>&1 || code=$?
[ "$code" -eq 2 ]
grep -q 'alpha' "$TMP/unknown"
code=0
MMW_TEST_JOBS=0 bash "$TMP/scenarios.sh" alpha omega > "$TMP/jobs" 2>&1 || code=$?
[ "$code" -eq 2 ]
echo 'parallel runner reports failures'
