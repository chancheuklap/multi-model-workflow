#!/usr/bin/env bash
#
# End-to-end tests for relay.py. One scenario per run:
#
#   bash mmw-v2/tests/relay/test_relay.sh wake|worker|busy|retired|gone|reconcile|pollfail
#   bash mmw-v2/tests/relay/test_relay.sh singleton|norecipient|registerstopped|readonly
#   bash mmw-v2/tests/relay/test_relay.sh startstop|ackwake
#   bash mmw-v2/tests/relay/test_relay.sh all
#
# A fake `gh` and a fake `paseo` sit in front of the real ones on PATH and write every
# call they receive to a log, one call per line, fields joined by ` :: `. The board is a
# directory of JSON files, one per ticket, that the fake `gh` answers comment reads from
# (honouring `since`); Paseo is one JSON file of agents that the fake `paseo ls` answers
# from. The relay's deliveries go through the real `runners/paseo.sh` adapter, so what
# this proves is the relay and that adapter together, without a network or a daemon.
# The last line of a passing scenario is its EXPECT string.

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
RELAY="$(dirname "$(dirname "$HERE")")/skills/dispatch/scripts/relay.py"
REPO=o/r

rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
BG_PID=""
cleanup() {
  [ -n "$BG_PID" ] && kill "$BG_PID" 2>/dev/null
  # A relay `start` left running would outlive this file and poll a board that is gone.
  python3 "$RELAY" stop --repo "$REPO" >/dev/null 2>&1
  rm -rf "$TMP"
}
trap cleanup EXIT
mkdir -p "$TMP/bin"

cat > "$TMP/bin/gh" <<'FAKE'
#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

args = sys.argv[1:]
with open(os.environ["MMW_TEST_LOG"], "a", encoding="utf-8") as fh:
    fh.write("gh" + "".join(" :: " + a for a in args) + "\n")
board = Path(os.environ["FAKE_BOARD"])
url = args[-1] if args else ""
found = re.search(r"repos/[^/]+/[^/]+/issues/(\d+)/(comments|sub_issues)(?:\?(.*))?$", url)
if args[:1] != ["api"] or not found:
    sys.stderr.write(f"fake gh: no answer for {args}\n")
    sys.exit(1)
number, kind, query = found.group(1), found.group(2), found.group(3) or ""
if number in [n for n in os.environ.get("FAKE_GH_FAIL", "").split(",") if n]:
    sys.stderr.write("HTTP 502: Bad Gateway (https://api.github.com/)\n")
    sys.exit(1)
if kind == "sub_issues":
    rows = json.loads((board / f"sub-{number}.json").read_text()) if (board / f"sub-{number}.json").is_file() else []
    print(json.dumps([rows]))
    sys.exit(0)
params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
since = params.get("since")
path = board / f"{number}.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows = [c for c in rows if not since or c["updated_at"] >= since]
# `--paginate --slurp` answers with one list per page: two pages here, to prove they are joined.
half = len(rows) // 2
print(json.dumps([rows[:half], rows[half:]]))
FAKE

cat > "$TMP/bin/paseo" <<'FAKE'
#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

args = sys.argv[1:]
with open(os.environ["MMW_TEST_LOG"], "a", encoding="utf-8") as fh:
    fh.write("paseo" + "".join(" :: " + a for a in args) + "\n")
agents = Path(os.environ["FAKE_PASEO_AGENTS"])
if args[:3] == ["ls", "-g", "--json"]:
    print(agents.read_text() if agents.is_file() else "[]")
    sys.exit(0)
if args[:2] == ["send", "--no-wait"]:
    if os.environ.get("FAKE_PASEO_SEND_FAILS") == "1":
        sys.stderr.write("Error: agent is running a turn\n")
        sys.exit(1)
    sys.exit(0)
sys.stderr.write(f"fake paseo: no answer for {args}\n")
sys.exit(1)
FAKE

chmod +x "$TMP/bin/gh" "$TMP/bin/paseo"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_HOME="$TMP/mmw-home"
export FAKE_BOARD="$TMP/board"
export FAKE_PASEO_AGENTS="$TMP/agents.json"
STATE="$MMW_HOME/state/o__r"

# ------------------------------------------------------------------ fixtures

reset() {
  rm -rf "$MMW_HOME" "$FAKE_BOARD"
  mkdir -p "$MMW_HOME" "$FAKE_BOARD"
  : > "$MMW_TEST_LOG"
  agents main-a
  unset FAKE_GH_FAIL FAKE_PASEO_SEND_FAILS
}

# agents <id>...: the sessions `paseo ls` lists, all idle.
agents() {
  python3 - "$@" > "$FAKE_PASEO_AGENTS" <<'PY'
import json, sys
print(json.dumps([{"id": a, "status": "idle"} for a in sys.argv[1:]]))
PY
}

# event <ticket> <comment-id> <event> [updated_at] [key=value...]: a comment lands on the ticket.
event() {
  python3 - "$FAKE_BOARD" "$@" <<'PY'
import json, sys
from pathlib import Path
board, ticket, cid, name = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rest = sys.argv[5:]
updated = rest.pop(0) if rest and "=" not in rest[0] else "2026-09-10T01:00:00Z"
block = {"v": 1, "event": name, "ticket": ticket, **dict(r.split("=", 1) for r in rest)}
# What an event must carry to be one (`events.py`'s table), when the scenario does not care.
block = {**{"ticket.refused": {"reason": "blocked"},
            "worker.started": {"machine": "mac-1", "host": "grok", "model": "grok-4.6", "effort": "high",
                               "grade": "junior-worker", "worktree": "/repo/.worktrees/issue-61",
                               "branch": "issue-61", "base": "0" * 40}}.get(name, {}), **block}
path = board / f"{ticket}.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({"id": cid, "created_at": updated, "updated_at": updated,
             "body": f"a line for people\n\n<!-- mmw {json.dumps(block)} -->"})
path.write_text(json.dumps(rows))
PY
}

# set_beat <time>: the relay's last good poll was at <time>.
set_beat() {
  python3 - "$STATE/beat.json" "$1" <<'PY'
import json, sys
path, at = sys.argv[1], sys.argv[2]
beat = json.load(open(path))
beat["at"] = at
json.dump(beat, open(path, "w"))
PY
}

relay_() { python3 "$RELAY" "$@" > "$TMP/out" 2> "$TMP/err"; echo "$?"; }

# rows: one `seq ticket event session delivered?` line per queued row.
rows() {
  python3 "$RELAY" queue --repo "$REPO" 2>/dev/null | python3 -c '
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    print(r["seq"], r["ticket"], r["event"], r["session"], "delivered" if r["delivered"] else "undelivered")
'
}

has() { grep -qF -- "$1" "$MMW_TEST_LOG" || fail "no call matching: $1"; }
hasnt() { grep -qF -- "$1" "$MMW_TEST_LOG" && fail "should not have called: $1"; return 0; }
count_of() { grep -cF -- "$1" "$MMW_TEST_LOG" | tr -d ' '; }
expect_rows() {
  local got
  got="$(rows)"
  [ "$got" = "$1" ] || fail "queue should read
$1
but reads
$got"
}

register_main() {
  local code
  code="$(relay_ register --repo "$REPO" --runner paseo --session "${1:-main-a}")"
  [ "$code" = 0 ] || fail "register ${1:-main-a} expected 0, got $code: $(cat "$TMP/err")"
}

# ------------------------------------------------------------------ scenarios

scenario_wake() {
  local code
  echo "--- a landed ticket wakes the main agent through the runner, and stays until acked"
  reset
  register_main
  event 61 101 ticket.passed
  event 62 102 ticket.claimed
  event 62 103 ticket.returned
  code="$(relay_ run --repo "$REPO" --tickets 61,62 --once)"
  [ "$code" = 0 ] || fail "run --once expected 0, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: main-a :: #61 ticket.passed"
  has "paseo :: send :: --no-wait :: main-a :: #62 ticket.returned"
  hasnt "ticket.claimed"
  expect_rows "1 61 ticket.passed main-a delivered
2 62 ticket.returned main-a delivered"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --through 1)"
  [ "$code" = 0 ] || fail "ack expected 0, got $code: $(cat "$TMP/err")"
  expect_rows "2 62 ticket.returned main-a delivered"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --through 9)"
  [ "$code" = 1 ] || fail "ack past the last seq expected 1, got $code"
  grep -q "the last one is 2" "$TMP/err" || fail "the refusal should name the last seq: $(cat "$TMP/err")"
  expect_rows "2 62 ticket.returned main-a delivered"
}

scenario_worker() {
  local code
  echo "--- a reviewer's report wakes the ticket's worker, and each recipient acks only its own rows"
  reset
  agents main-a wk-61
  register_main
  event 61 100 worker.started runner=paseo session=wk-61
  event 61 101 reviewer.reported
  event 61 102 ticket.passed
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 0 ] || fail "run --once expected 0, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: wk-61 :: #61 reviewer.reported"
  has "paseo :: send :: --no-wait :: main-a :: #61 ticket.passed"
  hasnt "main-a :: #61 reviewer.reported"
  expect_rows "1 61 reviewer.reported wk-61 delivered
2 61 ticket.passed main-a delivered"
  python3 "$RELAY" queue --repo "$REPO" --runner paseo --session wk-61 > "$TMP/out" 2>/dev/null
  [ "$(wc -l < "$TMP/out" | tr -d ' ')" = 1 ] && grep -q '"session": "wk-61"' "$TMP/out" \
    || fail "queue --runner paseo --session wk-61 should print the worker's one row: $(cat "$TMP/out")"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session wk-61 --through 2)"
  [ "$code" = 0 ] || fail "the worker's ack expected 0, got $code: $(cat "$TMP/err")"
  grep -q "acked paseo wk-61 through 2: removed 1, 0 left for it" "$TMP/out" || fail "ack should say what it removed: $(cat "$TMP/out")"
  expect_rows "2 61 ticket.passed main-a delivered"
}

scenario_busy() {
  local code
  echo "--- a wake that arrives while the main agent is in a turn stays and is sent on the next pass"
  reset
  register_main
  event 61 101 ticket.passed
  code="$(FAKE_PASEO_SEND_FAILS=1 relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 0 ] || fail "run --once expected 0, got $code: $(cat "$TMP/err")"
  grep -q "kept 1 #61 ticket.passed: main-a is in a turn" "$TMP/out" || fail "should say it kept row 1: $(cat "$TMP/out")"
  expect_rows "1 61 ticket.passed main-a undelivered"
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 0 ] || fail "second run expected 0, got $code: $(cat "$TMP/err")"
  [ "$(count_of 'paseo :: send :: --no-wait :: main-a :: #61 ticket.passed')" = 2 ] \
    || fail "the kept row should have been sent a second time"
  expect_rows "1 61 ticket.passed main-a delivered"
}

scenario_retired() {
  local code
  echo "--- rows for a session that is no longer the registered main agent are dropped unsent"
  reset
  register_main main-a
  event 61 101 ticket.passed
  FAKE_PASEO_SEND_FAILS=1 relay_ run --repo "$REPO" --tickets 61 --once >/dev/null
  agents main-b
  register_main main-b
  : > "$MMW_TEST_LOG"
  event 61 102 ticket.refused 2026-09-10T01:05:00Z
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 0 ] || fail "run --once expected 0, got $code: $(cat "$TMP/err")"
  hasnt "main-a :: #61"
  has "paseo :: send :: --no-wait :: main-b :: #61 ticket.refused"
  grep -q "dropped row 1 (#61 ticket.passed for main main-a): it is addressed to paseo session main-a, and the registered main agent is now paseo session main-b" "$TMP/err" \
    || fail "the drop should be reported: $(cat "$TMP/err")"
  expect_rows "2 61 ticket.refused main-b delivered"
}

scenario_gone() {
  local code
  echo "--- a send the runner answers with 'no such session' drops the row"
  reset
  register_main main-a
  agents
  event 61 101 ticket.passed
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 0 ] || fail "run --once expected 0, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"
  grep -q "dropped row 1 (#61 ticket.passed for main main-a): paseo has no session main-a" "$TMP/err" \
    || fail "the drop should name the session: $(cat "$TMP/err")"
  expect_rows ""
}

scenario_reconcile() {
  local code
  echo "--- a relay that was down reads everything on start and announces the stretch once"
  reset
  register_main
  event 61 101 ticket.passed
  relay_ run --repo "$REPO" --tickets 61,62 --once >/dev/null
  relay_ ack --repo "$REPO" --runner paseo --session main-a --through 1 >/dev/null
  # Down for an hour: the last good poll is an hour old, and two tickets landed meanwhile,
  # one of them stamped before the relay's own mark (a comment that became visible late).
  set_beat 2020-01-01T00:00:00Z
  event 62 102 ticket.returned 2020-01-01T00:00:00Z
  event 61 103 ticket.refused
  : > "$MMW_TEST_LOG"
  code="$(relay_ run --repo "$REPO" --tickets 61,62 --once)"
  [ "$code" = 0 ] || fail "run --once expected 0, got $code: $(cat "$TMP/err")"
  hasnt "since="
  expect_rows "2 None relay.recovered main-a delivered
3 62 ticket.returned main-a delivered
4 61 ticket.refused main-a delivered"
  has "paseo :: send :: --no-wait :: main-a :: relay.recovered since 2020-01-01T00:00:00Z"
  : > "$MMW_TEST_LOG"
  code="$(relay_ run --repo "$REPO" --tickets 61,62 --once)"
  [ "$code" = 0 ] || fail "third run expected 0, got $code: $(cat "$TMP/err")"
  [ "$(count_of 'relay.recovered')" = 1 ] || fail "the unacked announcement is sent once more on start, not queued again"
  [ "$(rows | grep -c relay.recovered)" = 1 ] || fail "the stretch should be announced once: $(rows)"
  # The announcement is acked, and then the same stretch comes round again: the good poll
  # that ended it never got its beat written (a crash in between). It is not announced twice.
  relay_ ack --repo "$REPO" --runner paseo --session main-a --through 4 >/dev/null
  set_beat 2020-01-01T00:00:00Z
  : > "$MMW_TEST_LOG"
  code="$(relay_ run --repo "$REPO" --tickets 61,62 --once)"
  [ "$code" = 0 ] || fail "fourth run expected 0, got $code: $(cat "$TMP/err")"
  hasnt "relay.recovered"
  expect_rows ""
}

scenario_pollfail() {
  local code
  echo "--- a read that could not be made is reported and is not a good poll"
  reset
  register_main
  event 61 101 ticket.passed
  event 62 102 ticket.passed
  code="$(FAKE_GH_FAIL=62 relay_ run --repo "$REPO" --tickets 61,62 --once)"
  [ "$code" = 3 ] || fail "run --once with an unreadable ticket expected 3, got $code"
  grep -q "could not read #62: gh exited 1: HTTP 502" "$TMP/err" || fail "stderr should name #62 and why: $(cat "$TMP/err")"
  expect_rows "1 61 ticket.passed main-a delivered"
  python3 -c 'import json,sys; b=json.load(open(sys.argv[1])); sys.exit(0 if b.get("at") is None and "#62" in b["failure"] else 1)' \
    "$STATE/beat.json" || fail "beat.json should hold no good poll and name the failure: $(cat "$STATE/beat.json")"
  code="$(relay_ run --repo "$REPO" --tickets 61,62 --once)"
  [ "$code" = 0 ] || fail "run once the read works expected 0, got $code: $(cat "$TMP/err")"
  expect_rows "1 61 ticket.passed main-a delivered
2 62 ticket.passed main-a delivered"
}

scenario_singleton() {
  local code pid
  echo "--- one relay per repository, and the queue says when no relay feeds it"
  reset
  register_main
  python3 "$RELAY" run --repo "$REPO" --tickets 61 --interval 60 > "$TMP/bg.out" 2> "$TMP/bg.err" &
  BG_PID=$!
  for _ in $(seq 1 100); do
    [ -s "$STATE/beat.json" ] && grep -q '"at": "' "$STATE/beat.json" && break
    sleep 0.1
  done
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 1 ] || fail "a second relay expected refusal 1, got $code"
  grep -q "another relay is running for o/r: .* is held by pid $BG_PID" "$TMP/err" \
    || fail "the refusal should name the running relay's pid $BG_PID: $(cat "$TMP/err")"
  code="$(relay_ queue --repo "$REPO")"
  [ "$code" = 0 ] || fail "queue with a live relay expected 0, got $code: $(cat "$TMP/err")"
  pid="$BG_PID"
  kill -TERM "$pid"
  wait "$pid" 2>/dev/null
  BG_PID=""
  code="$(relay_ queue --repo "$REPO")"
  [ "$code" = 3 ] || fail "queue with no relay expected 3, got $code"
  grep -q "no relay is running for this repository" "$TMP/err" || fail "queue should say no relay runs: $(cat "$TMP/err")"
  # Killed without a chance to clean up: the record stays, names a dead pid, and blocks nobody.
  python3 "$RELAY" run --repo "$REPO" --tickets 61 --interval 60 > /dev/null 2>&1 &
  BG_PID=$!
  for _ in $(seq 1 100); do
    grep -q "\"pid\": $BG_PID" "$STATE/relay.lock" 2>/dev/null && break
    sleep 0.1
  done
  pid="$BG_PID"
  kill -KILL "$pid"
  wait "$pid" 2>/dev/null
  BG_PID=""
  grep -q "\"pid\": $pid," "$STATE/relay.lock" || fail "a killed relay leaves its record: $(cat "$STATE/relay.lock")"
  code="$(relay_ queue --repo "$REPO")"
  [ "$code" = 3 ] || fail "a record naming a dead pid is no relay, expected 3, got $code"
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 0 ] || fail "a relay after a killed one expected 0, got $code: $(cat "$TMP/err")"
}

scenario_norecipient() {
  local code
  echo "--- a relay with nobody registered to wake refuses to start"
  reset
  code="$(relay_ run --repo "$REPO" --tickets 61 --once)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code"
  grep -q "relay.py register --repo o/r" "$TMP/err" || fail "the refusal should give the register command: $(cat "$TMP/err")"
  hasnt "gh ::"
}

scenario_registerstopped() {
  local code
  echo "--- registering a session the runner says is stopped is refused"
  reset
  agents main-a
  code="$(relay_ register --repo "$REPO" --runner paseo --session main-z)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code"
  grep -q "session main-z is stopped" "$TMP/err" || fail "the refusal should name the session: $(cat "$TMP/err")"
  [ ! -f "$STATE/recipient.json" ] || fail "nothing should have been registered"
  code="$(relay_ register --repo "$REPO" --runner nosuch --session main-a)"
  [ "$code" = 1 ] || fail "an unknown runner expected refusal 1, got $code"
  grep -q "the adapters here are: .*paseo" "$TMP/err" || fail "the refusal should list the adapters: $(cat "$TMP/err")"
}

scenario_readonly() {
  echo "--- every call the relay makes to the tracker is a read"
  reset
  register_main
  event 61 101 ticket.passed
  echo '[{"number": 61}]' > "$FAKE_BOARD/sub-50.json"
  relay_ run --repo "$REPO" --spec 50 --once >/dev/null
  has "gh :: api :: --paginate :: --slurp :: repos/o/r/issues/50/sub_issues?per_page=100"
  has "gh :: api :: --paginate :: --slurp :: repos/o/r/issues/61/comments?per_page=100"
  python3 - "$MMW_TEST_LOG" <<'PY' || fail "a gh call that is not a plain read: $(grep '^gh' "$MMW_TEST_LOG")"
import sys
writes = ("-X", "--method", "-f", "-F", "--field", "--raw-field", "--input")
for line in open(sys.argv[1]):
    fields = line.rstrip("\n").split(" :: ")
    if fields[0] != "gh":
        continue
    if fields[1] != "api" or any(f in writes for f in fields):
        sys.exit(1)
PY
  expect_rows "1 61 ticket.passed main-a delivered"
}

scenario_startstop() {
  local code pid got
  echo "--- start runs a relay of its own that polls and delivers, and stop ends it"
  reset
  code="$(relay_ start --repo "$REPO" --tickets 61 --interval 60)"
  [ "$code" = 1 ] || fail "start with nobody registered expected refusal 1, got $code"
  grep -q "relay.py register --repo o/r" "$TMP/err" || fail "the refusal should give the register command: $(cat "$TMP/err")"
  register_main
  event 61 101 ticket.passed
  code="$(relay_ start --repo "$REPO" --tickets 61 --interval 60)"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  grep -q "^relay started for o/r: pid [0-9]*, watching ticket #61, log $STATE/relay.log" "$TMP/out" \
    || fail "start should name the pid, the watch and the log: $(cat "$TMP/out")"
  pid="$(sed -n 's/^relay started for o\/r: pid \([0-9]*\),.*/\1/p' "$TMP/out")"
  for _ in $(seq 1 100); do
    grep -qF "paseo :: send :: --no-wait :: main-a :: #61 ticket.passed" "$MMW_TEST_LOG" && break
    sleep 0.1
  done
  has "paseo :: send :: --no-wait :: main-a :: #61 ticket.passed"
  python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if r["pid"] == int(sys.argv[2]) and r["watch"] == {"tickets": [61]} else 1)' \
    "$STATE/relay.json" "$pid" || fail "relay.json should name pid $pid and its watch: $(cat "$STATE/relay.json")"

  echo "--- a second start of the same watch finds it running; another watch is refused"
  code="$(relay_ start --repo "$REPO" --tickets 61 --interval 60)"
  [ "$code" = 0 ] || fail "a second start expected 0, got $code: $(cat "$TMP/err")"
  grep -q "relay already running for o/r: pid $pid, watching ticket #61" "$TMP/out" || fail "it should find pid $pid: $(cat "$TMP/out")"
  code="$(relay_ start --repo "$REPO" --spec 76)"
  [ "$code" = 1 ] || fail "a start on another watch expected 1, got $code"
  grep -q "already running for o/r (pid $pid), watching ticket #61, and one repository has one relay" "$TMP/err" \
    || fail "the refusal should name the running relay: $(cat "$TMP/err")"

  echo "--- watching answers for the ticket it watches and no other"
  code="$(relay_ watching --repo "$REPO" --ticket 61)"
  [ "$code" = 0 ] || fail "watching #61 expected 0, got $code: $(cat "$TMP/err")"
  code="$(relay_ watching --repo "$REPO" --ticket 62 --spec 76)"
  [ "$code" = 1 ] || fail "watching #62 expected 1, got $code"
  grep -q "watches ticket #61, and #62, a ticket of spec #76, is not among them" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"

  echo "--- stop leaves a relay watching something else running, and ends the one it names"
  code="$(relay_ stop --repo "$REPO" --spec 76)"
  [ "$code" = 3 ] || fail "stop on another watch expected 3, got $code"
  kill -0 "$pid" 2>/dev/null || fail "the relay should still run"
  code="$(relay_ stop --repo "$REPO" --tickets 61)"
  [ "$code" = 0 ] || fail "stop expected 0, got $code: $(cat "$TMP/err")"
  grep -q "stopped the relay for o/r: pid $pid, watching ticket #61" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"
  kill -0 "$pid" 2>/dev/null && fail "pid $pid should be gone"
  [ ! -f "$STATE/relay.json" ] || fail "a relay that stopped leaves no relay.json: $(cat "$STATE/relay.json")"
  code="$(relay_ watching --repo "$REPO" --ticket 61)"
  [ "$code" = 1 ] || fail "watching with no relay expected 1, got $code"

  echo "--- a relay stopped on purpose leaves no unattended stretch for the next one to announce"
  event 61 102 ticket.refused 2026-09-10T01:05:00Z
  code="$(relay_ run --repo "$REPO" --tickets 61 --once --grace 0)"
  [ "$code" = 0 ] || fail "the next relay expected 0, got $code: $(cat "$TMP/err")"
  got="$(rows)"
  case "$got" in *relay.recovered*) fail "a stop is not an unattended stretch: $got" ;; esac
  case "$got" in *"61 ticket.refused"*) ;; *) fail "the next relay should still read what landed meanwhile: $got" ;; esac

  code="$(relay_ stop --repo "$REPO")"
  [ "$code" = 0 ] || fail "stop with nothing running expected 0, got $code"
  grep -q "no relay is running for o/r" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"

  echo "--- stop with no relay alive still forgets the last good poll of the one that died"
  python3 "$RELAY" run --repo "$REPO" --tickets 61 --once >/dev/null 2>&1
  set_beat 2020-01-01T00:00:00Z
  code="$(relay_ stop --repo "$REPO")"
  [ "$code" = 0 ] || fail "stop expected 0, got $code"
  relay_ ack --repo "$REPO" --runner paseo --session main-a --through 2 >/dev/null
  code="$(relay_ run --repo "$REPO" --tickets 61 --once --grace 0)"
  [ "$code" = 0 ] || fail "the next relay expected 0, got $code: $(cat "$TMP/err")"
  got="$(rows)"
  case "$got" in *relay.recovered*) fail "a stop after a death is not an unattended stretch to announce: $got" ;; esac

  echo "--- start refuses, and runs nothing, when the registration cannot be read"
  echo "not json" > "$STATE/recipient.json"
  code="$(relay_ start --repo "$REPO" --tickets 61 --interval 60)"
  [ "$code" = 1 ] || fail "a start over an unreadable recipient expected 1, got $code"
  grep -q "recipient.json is not JSON" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  code="$(relay_ watching --repo "$REPO" --ticket 61)"
  [ "$code" = 1 ] || fail "nothing should be running, got $code"
}

scenario_ackwake() {
  local code
  echo "--- a recipient acks the wake it read by ticket and event; a second ack of it is refused"
  reset
  agents main-a wk-61
  register_main
  event 61 100 worker.started runner=paseo session=wk-61
  event 61 101 ticket.passed
  event 61 102 reviewer.reported
  relay_ run --repo "$REPO" --tickets 61 --once >/dev/null
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --ticket 61 --event ticket.passed)"
  [ "$code" = 0 ] || fail "ack expected 0, got $code: $(cat "$TMP/err")"
  grep -q "acked paseo main-a \`#61 ticket.passed\` through 1: removed 1, 0 left for it" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"
  expect_rows "2 61 reviewer.reported wk-61 delivered"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --ticket 61 --event ticket.passed)"
  [ "$code" = 1 ] || fail "a second ack matches no row of main-a and is refused, got $code"
  grep -q "no wake \`#61 ticket.passed\` is queued for paseo session main-a" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  grep -q "Queued for this session: nothing" "$TMP/err" || fail "the refusal should say what main-a has queued: $(cat "$TMP/err")"

  echo "--- a session acking a wake that went to another session is refused, and removes nothing"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --ticket 61 --event reviewer.reported)"
  [ "$code" = 1 ] || fail "main-a acking the worker's wake expected 1, got $code"
  code="$(relay_ ack --repo "$REPO" --runner orca --session wk-61 --ticket 61 --event reviewer.reported)"
  [ "$code" = 1 ] || fail "the same session id on another runner is another session, expected 1, got $code"
  expect_rows "2 61 reviewer.reported wk-61 delivered"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --ticket 61 --event ticket.refused)"
  [ "$code" = 1 ] || fail "ack of a wake never queued expected 1, got $code"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --event ticket.passed)"
  [ "$code" = 1 ] || fail "ack of a ticket event with no ticket expected 1, got $code"
  code="$(relay_ ack --repo "$REPO" --runner paseo --session main-a --through 2 --ticket 61 --event ticket.passed)"
  [ "$code" = 1 ] || fail "ack with a seq and a wake expected 1, got $code"
  expect_rows "2 61 reviewer.reported wk-61 delivered"
}

ALL="wake worker busy retired gone reconcile pollfail singleton norecipient registerstopped readonly startstop ackwake"

case " $ALL all " in
  *" ${1:-} "*) ;;
  *)
    echo "usage: test_relay.sh $(echo "$ALL" | tr ' ' '|')|all" >&2
    exit 2 ;;
esac
if [ "$1" = all ]; then wanted="$ALL"; else wanted="$1"; fi

for name in $wanted; do
  echo "=== $name"
  "scenario_$name"
  if [ "$rc" -eq 0 ]; then
    echo "RELAY-$(echo "$name" | tr '[:lower:]' '[:upper:]')-OK"
  else
    echo "$name failed" >&2
    exit 1
  fi
done
