#!/usr/bin/env bash
#
# turn-guard.py end to end: each host's turn-end payload on stdin, the way that host's
# registration calls it, and the three hook-collision cases.
#
#   bash mmw-v2/tests/liveness/test_guard.sh
#
# The seam is this machine's state directory plus the runner: MMW_HOME is a temporary
# directory holding one open night (a relay.json whose relay is not running) with a main
# agent registered under a fake runner, `fake`, whose adapter answers `self` with
# $FAKE_SELF. MMW_WATCHDOG_PY names a script that exits at once, so the hook's attempt
# to arm the watchdog fails and the night is left unwatched — the state in which a turn
# end must be kept. One case arms the real watchdog.py instead, against a fake `gh`. What
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
echo '[[]]'
FAKE
chmod +x "$TMP/bin/gh"

printf '{"runner": "fake", "session": "main-1"}\n' > "$STATE/recipient.json"
printf '{"watch": {"tickets": [61]}, "started": "2026-09-10T00:00:00Z"}\n' > "$STATE/relay.json"

# Run the hook: `hook <host> <payload> [VAR=value ...]`. Sets RC, OUT, ERR.
hook() {
  local host="$1" payload="$2"
  shift 2
  local out err
  out="$TMP/out"; err="$TMP/err"
  printf '%s' "$payload" | env -u GROK_AGENT -u GROK_HOOK_EVENT -u GROK_SESSION_ID \
      -u CURSOR_VERSION -u CURSOR_INVOKED_AS -u CURSOR_AGENT \
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
GROK='{"hookEventName":"stop","hook_event_name":"Stop","sessionId":"g1","cwd":"/repo","workspaceRoot":"/repo","stopHookActive":false,"reason":"end_turn"}'
CURSOR='{"conversation_id":"k1","generation_id":"g","hook_event_name":"stop","status":"completed","loop_count":0,"cursor_version":"2026.09.08-6caf4ff","workspace_roots":["/repo"]}'
PI='{"hook_event_name":"agent_settled","cwd":"/repo"}'

echo "### each host blocks, in its own terms, while tickets may be held and no watchdog runs"
hook claude "$CLAUDE";  check "claude Stop: exit 2 with the reason on stderr" 2 "MMW turn guard: the night on o/r"
hook codex "$CODEX";    check "codex Stop: exit 2 with the reason on stderr" 2 "watchdog is not healthy"
hook grok "$GROK" GROK_HOOK_EVENT=stop GROK_SESSION_ID=g1
                        check "grok Stop: its own registration blocks despite its own markers" 2 "MMW turn guard"
hook pi "$PI";          check "pi agent_settled: exit 2, the extension sends it as a follow-up" 2 "MMW turn guard"
hook cursor "$CURSOR"
if [ "$RC" = 0 ] && printf '%s' "$OUT" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert "MMW turn guard" in d["followup_message"]' 2>/dev/null; then
  pass=$((pass + 1)); echo "ok   cursor stop: exit 0 with one followup_message on stdout"
else
  failed=$((failed + 1)); echo "FAIL cursor stop: want exit 0 and {followup_message}; got rc=$RC out=${OUT:0:120}" >&2
fi
hook claude "$CLAUDE"
check "the block tells the agent how the arm failed and the one command to run" 2 "this watchdog does not start"
check "the block names the arm command" 2 "arm --repo o/r"

echo "### a stop that is already the forced continuation is let through"
hook claude "${CLAUDE/\"stop_hook_active\":false/\"stop_hook_active\":true}";  check_silent "claude stop_hook_active"
hook codex "${CODEX/\"stop_hook_active\":false/\"stop_hook_active\":true}";    check_silent "codex stop_hook_active"
hook grok "${GROK/\"stopHookActive\":false/\"stopHookActive\":true}" GROK_HOOK_EVENT=stop
check_silent "grok stopHookActive"
hook cursor "${CURSOR/\"loop_count\":0/\"loop_count\":1}";                     check_silent "cursor loop_count 1"
hook grok "${GROK/\"end_turn\"/\"shutdown\"}" GROK_HOOK_EVENT=stop
check_silent "grok's session-end Stop is not a turn"
if grep -q "claude allow held=None the continuation an earlier block forced" "$STATE/guard.log"; then
  pass=$((pass + 1)); echo "ok   a forced continuation is still recorded in guard.log"
else
  failed=$((failed + 1)); echo "FAIL guard.log has no line for the forced continuation" >&2
fi

echo "### collisions: the copy registered for another host stands down where it must, and only there"
before="$(log_lines)"
hook claude "$CLAUDE" GROK_AGENT=1
check_silent "claude copy under grok 0.2.73 (GROK_AGENT) stands down"
hook claude "$CLAUDE" GROK_HOOK_EVENT=stop
check_silent "claude copy under grok 1.0 (GROK_HOOK_EVENT) stands down"
[ "$(log_lines)" = "$before" ] && { pass=$((pass + 1)); echo "ok   a copy that stands down judges nothing and logs nothing"; } \
  || { failed=$((failed + 1)); echo "FAIL a copy that stood down wrote to guard.log" >&2; }
hook claude "$CLAUDE" GROK_SESSION_ID=inherited
check "GROK_SESSION_ID alone (inherited by a Claude session Grok started) does not stand it down" 2 "MMW turn guard"
hook claude "${CLAUDE/\"hook_event_name\"/\"cursor_version\":\"2026.09.08-6caf4ff\",\"hook_event_name\"}"
check_silent "claude copy delivered by cursor (payload cursor_version) stands down"
hook claude "$CLAUDE" CURSOR_VERSION=2026.09.08 CURSOR_INVOKED_AS=cursor-agent CURSOR_AGENT=1
check "cursor's environment alone (a Claude session started from a Cursor pane) does not stand it down" 2 "MMW turn guard"
hook cursor "$GROK" GROK_HOOK_EVENT=stop
check_silent "cursor copy loaded by grok (no cursor_version in the payload) stands down"

echo "### whose turn, and which night"
hook claude "$CLAUDE" FAKE_SELF=worker-9;  check_silent "a session that is not the registered main agent is let through"
hook claude "$CLAUDE" FAKE_SELF=;          check_silent "a process in no session of the main agent's runner is let through"
mv "$STATE/relay.json" "$TMP/relay.json.aside"
printf '{"at": null, "stopped": "2026-09-10T00:00:00Z"}\n' > "$STATE/beat.json"
hook claude "$CLAUDE";                     check_silent "no open night: nothing to guard"
mv "$TMP/relay.json.aside" "$STATE/relay.json"

echo "### the predicate: nothing held at the last round"
printf '{"pid": 1, "identity": "gone", "at": "2026-09-10T00:00:00Z", "poll": 60, "held": []}\n' > "$STATE/watchdog.json"
hook claude "$CLAUDE";                     check_silent "a dead watchdog whose last round held nothing lets the turn end"
printf '{"pid": 1, "identity": "gone", "at": "2026-09-10T00:00:00Z", "poll": 60, "held": [61]}\n' > "$STATE/watchdog.json"
hook claude "$CLAUDE";                     check "a dead watchdog whose last round held #61 blocks, naming it" 2 "(#61)"
grep -q "claude block held=\[61\]" "$STATE/guard.log" && { pass=$((pass + 1)); echo "ok   guard.log records the decision"; } \
  || { failed=$((failed + 1)); echo "FAIL guard.log has no block line for held=[61]" >&2; }

echo "### the hook re-arms the watchdog, and a healthy one lets the turn end"
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
hook codex "$CODEX" MMW_WATCHDOG_PY= PATH="$TMP/bin:$PATH"
check_silent "a second turn end finds it healthy and starts nothing"

echo
echo "passed $pass, failed $failed"
[ "$failed" -eq 0 ]
