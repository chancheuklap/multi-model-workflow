#!/usr/bin/env bash
#
# turn-guard.py end to end: each host's turn-end payload on stdin, the way that host's
# registration calls it.
#
#   bash mmw-v4/tests/liveness/test_guard.sh
#
# The seam is this machine's state directory plus the runner: MMW_HOME is a temporary
# directory holding one open watch (a watches.json entry whose relay is not running) whose
# orchestrator is main-1 under a fake runner, `fake`, whose adapter answers `self` with
# $FAKE_SELF. MMW_WATCHDOG_PY names a script that exits at once, so the hook's attempt
# to arm the watchdog fails. The turn still ends. One case arms the real watchdog.py instead, against a fake `gh`. What
# is asserted is the exit code, stdout and stderr each host would read, and guard.log.
# Nothing here needs a host, the tracker or the network.

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPTS="$(dirname "$(dirname "$HERE")")/skills/dispatch/scripts"
GUARD="$SCRIPTS/turn-guard.py"

TMP="$(mktemp -d)"
pass=0
failed=0
cleanup() {
  # The one case that arms a real watchdog leaves it running; end it by its lock's pid.
  local pid
  pid="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("pid") or "")' \
         "$TMP/home/state/o__r/watchdog.lock" 2>/dev/null)"
  [ -n "$pid" ] && kill "$pid" 2>/dev/null
  rm -rf "$TMP"
}
trap cleanup EXIT

STATE="$TMP/home/state/o__r"
mkdir -p "$STATE" "$TMP/runners" "$TMP/bin"

cat > "$TMP/runners/fake.sh" <<'FAKE'
#!/usr/bin/env bash
case "$1" in
  self)
    [ -z "${FAKE_SELF_RC:-}" ] || exit "$FAKE_SELF_RC"
    [ -n "${FAKE_SELF:-}" ] || exit 3
    printf '%s\n' "$FAKE_SELF" ;;
  liveness) printf 'alive\n' ;;
  send) exit 3 ;;
esac
FAKE

cat > "$TMP/nodog.py" <<'FAKE'
import sys
sys.stderr.write("this watchdog does not start\n")
sys.exit(1)
FAKE

cat > "$TMP/bin/gh" <<'FAKE'
#!/usr/bin/env bash
if [ "${1:-}" = api ] && [ "${2:-}" = -i ]; then
  printf 'HTTP/2 200 OK\nETag: "empty"\n\n[]\n'
else
  echo '[[]]'
fi
FAKE
chmod +x "$TMP/bin/gh"

ONE_WATCH='{"tickets:61": {"tickets": [61], "runner": "fake", "session": "main-1"}}'
printf '%s\n' "$ONE_WATCH" > "$STATE/watches.json"

# Run the hook: `hook <host> <payload> [VAR=value ...]`. Sets RC, OUT, ERR.
hook() {
  local host="$1" payload="$2"
  shift 2
  local out err
  out="$TMP/out"; err="$TMP/err"
  printf '%s' "$payload" | env \
      MMW_HOME="$TMP/home" MMW_RUNNERS_DIR="$TMP/runners" MMW_WATCHDOG_PY="$TMP/nodog.py" \
      FAKE_SELF=main-1 "$@" python3 "$GUARD" stop "$host" >"$out" 2>"$err"
  RC=$?
  OUT="$(cat "$out")"
  ERR="$(cat "$err")"
}

check() {
  local name="$1" want_rc="$2" want="$3"
  local got="rc=$RC out=${OUT:0:80} err=${ERR:0:80}"
  if [ "$RC" = "$want_rc" ] && { [ -z "$want" ] || printf '%s\n%s' "$OUT" "$ERR" | grep -qF -- "$want"; }; then
    pass=$((pass + 1))
    echo "ok   $name"
  else
    failed=$((failed + 1))
    echo "FAIL $name: want rc=$want_rc containing '$want'; got $got" >&2
  fi
}

check_silent() {
  local name="$1"
  if [ "$RC" = 0 ] && [ -z "$OUT" ] && [ -z "$ERR" ]; then
    pass=$((pass + 1))
    echo "ok   $name"
  else
    failed=$((failed + 1))
    echo "FAIL $name: want a silent exit 0; got rc=$RC out=${OUT:0:80} err=${ERR:0:80}" >&2
  fi
}

log_lines() { wc -l < "$STATE/guard.log" 2>/dev/null | tr -d ' ' || echo 0; }

CLAUDE='{"session_id":"c1","transcript_path":"/t","cwd":"/repo","hook_event_name":"Stop","stop_hook_active":false}'
CODEX='{"session_id":"x1","turn_id":"t1","cwd":"/repo","hook_event_name":"Stop","model":"gpt","stop_hook_active":false}'

echo "### each host ends its turn even when the watchdog cannot start"
hook claude "$CLAUDE"; check_silent "claude Stop"
hook codex "$CODEX"; check_silent "codex Stop"
hook grok "$CLAUDE"; check "an unknown host blocks nothing" 0 "usage: turn-guard.py stop <claude|codex>"
if grep -q "claude allow watchdog unhealthy" "$STATE/guard.log"; then
  pass=$((pass + 1)); echo "ok   guard.log records the failed arm"
else
  failed=$((failed + 1)); echo "FAIL guard.log has no failed arm" >&2
fi

echo "### any session arms an open watch"
hook claude "$CLAUDE" FAKE_SELF=worker-9; check_silent "a worker's turn ends"
hook claude "$CLAUDE" FAKE_SELF=; check_silent "a process with no session ends"
hook claude 'not json'; check_silent "an unreadable payload ends"
printf 'not json\n' > "$STATE/watches.json"
hook claude "$CLAUDE"; check_silent "unreadable watches still let the turn end"
rm -f "$STATE/watches.json"
before="$(log_lines)"
hook claude "$CLAUDE"; check_silent "no open watch"
if [ "$(log_lines)" = "$before" ]; then
  pass=$((pass + 1)); echo "ok   a closed watch is not armed"
else
  failed=$((failed + 1)); echo "FAIL a closed watch was armed" >&2
fi
printf '%s\n' "$ONE_WATCH" > "$STATE/watches.json"

echo "### the hook re-arms the watchdog, and a healthy one lets the turn end"
: > "$STATE/watchdog.log"   # the failed arms of the cases above are not this case's
hook claude "$CLAUDE" MMW_WATCHDOG_PY= PATH="$TMP/bin:$PATH"
check_silent "claude Stop with the real watchdog.py armed by the hook"
cat > "$TMP/owned.py" <<'PY'
import json, sys
from pathlib import Path
state = Path(sys.argv[1])
lock = json.loads((state / "watchdog.lock").read_text())
beat = json.loads((state / "watchdog.json").read_text())
assert lock["pid"] == beat["pid"] and lock["identity"] == beat["identity"], (lock, beat)
PY
if python3 "$TMP/owned.py" "$STATE"; then
  pass=$((pass + 1)); echo "ok   the armed watchdog holds its lock and wrote its own heartbeat"
else
  failed=$((failed + 1)); echo "FAIL the armed watchdog is not holding its lock with its own heartbeat" >&2
fi
first_pid="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pid"])' "$STATE/watchdog.lock")"
hook codex "$CODEX" MMW_WATCHDOG_PY= PATH="$TMP/bin:$PATH"
check_silent "a second turn end finds it healthy"
arms="$(grep -c "^--- " "$STATE/watchdog.log")"
now_pid="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pid"])' "$STATE/watchdog.lock")"
if [ "$arms" = 1 ] && [ "$now_pid" = "$first_pid" ]; then
  pass=$((pass + 1)); echo "ok   and starts no second watchdog: one arm in watchdog.log, the same pid holds the lock"
else
  failed=$((failed + 1)); echo "FAIL a healthy watchdog was armed again: $arms arms, lock pid $first_pid then $now_pid" >&2
fi

echo
echo "passed $pass, failed $failed"
[ "$failed" -eq 0 ]
