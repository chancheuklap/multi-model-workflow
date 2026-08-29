#!/usr/bin/env bash
#
# Tests for dispatch.sh. One scenario per run:
#
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh worker|reviewer|badrole
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh idletimeout|notready|noherdr
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh wait|waittimeout|placeholder
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh all
#
# A fake `herdr` and a fake `gh` sit in front of the real ones on PATH and write every
# call they receive to a log, one call per line, fields joined by ` :: `. What the
# script does to Herdr and to the tracker is therefore checkable without a terminal
# multiplexer, a network, or a ticket. The last line of a passing run is the scenario's
# EXPECT string; everything before it says what was checked.

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname "$HERE")"
DISPATCH="$SKILL/scripts/dispatch.sh"

rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

cat > "$TMP/bin/herdr" <<'FAKE'
#!/usr/bin/env bash
line=herdr
for a in "$@"; do line="$line :: $a"; done
echo "$line" >> "$MMW_TEST_LOG"
case "$1 $2" in
  "tab create")
    echo '{"result":{"tab":{"tab_id":"w1:t9"},"root_pane":{"pane_id":"w1:p9"}}}' ;;
  "pane layout")
    echo "{\"result\":{\"layout\":{\"area\":{\"width\":${FAKE_HERDR_WIDTH:-210},\"height\":48}}}}" ;;
  "pane split")
    echo '{"result":{"pane":{"pane_id":"w1:p10"}}}' ;;
  "agent list")
    if [ -n "${FAKE_HERDR_AGENTS:-}" ]; then
      printf '%s\n' "$FAKE_HERDR_AGENTS"
    else
      echo '{"result":{"agents":[]}}'
    fi ;;
  "agent wait")
    if [ "${FAKE_HERDR_WAIT_FAIL:-0}" = 1 ]; then
      echo '{"error":{"code":"timeout"}}' >&2
      exit 1
    fi
    echo '{"result":{"agent":{"agent_status":"idle"}}}' ;;
  "agent start")
    echo '{"result":{"agent":{"agent_status":"idle"}}}' ;;
  *)
    echo '{"result":{}}' ;;
esac
FAKE

cat > "$TMP/bin/gh" <<'FAKE'
#!/usr/bin/env bash
line=gh
for a in "$@"; do line="$line :: $a"; done
echo "$line" >> "$MMW_TEST_LOG"
case "$*" in
  *"--json comments"*)
    seen=$(( $(cat "$MMW_GH_COMMENT_CALLS" 2>/dev/null || echo 0) + 1 ))
    echo "$seen" > "$MMW_GH_COMMENT_CALLS"
    MMW_SEEN="$seen" python3 -c '
import json, os

seen = int(os.environ["MMW_SEEN"])
match_on = int(os.environ.get("FAKE_GH_MATCH_ON", "1"))
if match_on and seen >= match_on:
    body = "REVIEW clean\nNo findings inside the ticket."
else:
    body = "self-run\n3 met, 1 unmet"
print(json.dumps({"comments": [{"body": body}]}))
' ;;
  *"--json state,labels,blockedBy,title"*)
    python3 -c '
import json, os

labels = os.environ.get("FAKE_GH_LABELS", "ready-for-agent")
blockers = os.environ.get("FAKE_GH_BLOCKERS", "")
print(json.dumps({
    "state": os.environ.get("FAKE_GH_STATE", "OPEN"),
    "labels": [{"name": n} for n in labels.split(",") if n],
    "blockedBy": [{"number": int(b.split(":")[0]), "state": b.split(":")[1]}
                  for b in blockers.split(",") if b],
    "title": os.environ.get("FAKE_GH_TITLE",
                            "landing 7 of 15: a new skill called dispatch"),
}))
' ;;
  *) echo '{}' ;;
esac
FAKE

chmod +x "$TMP/bin/herdr" "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_GH_COMMENT_CALLS="$TMP/comment-calls"

# ------------------------------------------------------------------ log reading

reset_log() { : > "$MMW_TEST_LOG"; : > "$MMW_GH_COMMENT_CALLS"; }
has() { grep -qF -- "$1" "$MMW_TEST_LOG" || fail "no call matching: $1"; }
hasnt() { grep -qF -- "$1" "$MMW_TEST_LOG" && fail "should not have called: $1"; return 0; }
count_of() { grep -cF -- "$1" "$MMW_TEST_LOG" | tr -d ' '; }
# Line number of the first matching call, or 0 when there is none, so that a
# comparison against it stays an integer comparison.
line_of() { grep -n -- "$1" "$MMW_TEST_LOG" | head -1 | cut -d: -f1 | grep . || echo 0; }

# Prints the field after <flag> on the first logged call carrying that flag.
arg_after() {
  MMW_FLAG="$1" python3 -c '
import os

flag = os.environ["MMW_FLAG"]
for line in open(os.environ["MMW_TEST_LOG"], encoding="utf-8"):
    fields = line.rstrip("\n").split(" :: ")
    if flag in fields:
        index = fields.index(flag)
        if index + 1 < len(fields):
            print(fields[index + 1])
        break
'
}

run_dispatch() { "$@" > "$TMP/out" 2> "$TMP/err"; echo "$?"; }
one_line_reason() {
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "the reason should be one line: $(cat "$TMP/err")"
}

# ------------------------------------------------------------------ scenarios

scenario_worker() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  echo "--- the ticket is read before anything is started"
  has "gh :: issue :: view :: 61 :: --json :: state,labels,blockedBy,title"
  local first_gh first_herdr
  first_gh="$(line_of '^gh ')"
  first_herdr="$(line_of '^herdr ')"
  { [ -n "$first_gh" ] && [ -n "$first_herdr" ] && [ "$first_gh" -lt "$first_herdr" ]; } \
    || fail "the tracker should be asked before the first herdr call"

  echo "--- one tab per ticket, carrying the ticket number into the pane"
  has "herdr :: tab :: create"
  has ":: --workspace :: w1"
  has ":: --env :: MMW_TICKET=61"
  has ":: --no-focus"
  [ "$(arg_after --cwd)" = "$(git rev-parse --show-toplevel)" ] \
    || fail "--cwd should be the repository root, got $(arg_after --cwd)"
  MMW_LABEL="$(arg_after --label)" python3 -c '
import os, sys

label = os.environ["MMW_LABEL"]
if not label.startswith("#61 "):
    sys.exit("label does not name the ticket: " + label)
if len(label) != 24:
    sys.exit("label should be #61 plus 20 title characters, got %d: %s" % (len(label), label))
' || fail "the tab label is wrong"

  echo "--- the agent starts in the tab's own pane, and nothing is split"
  has "herdr :: agent :: start :: issue-61 :: --kind :: cursor :: --pane :: w1:p9 :: --"
  has ":: -w :: issue-61 :: --worktree-base :: main :: --force :: --trust :: --model :: cursor-grok-4.6-high"
  hasnt "herdr :: pane :: split"

  echo "--- it is told what to work on only after it is ready"
  has "herdr :: agent :: wait :: issue-61 :: --until :: idle :: --until :: done :: --timeout :: 120000"
  has "herdr :: agent :: prompt :: issue-61 :: implement #61"
  [ "$(line_of 'agent :: wait')" -lt "$(line_of 'agent :: prompt')" ] \
    || fail "prompted before waiting for readiness"

  echo "--- the pane says who it is, to a person and to a machine"
  has "herdr :: pane :: rename :: w1:p9 :: #61 worker"
  has "herdr :: pane :: report-metadata :: w1:p9 :: --source :: mmw :: --token :: model=cursor-grok-4.6-high :: --ttl-ms :: 86400000"
}

scenario_reviewer() {
  local code
  echo "--- a wide pane splits sideways"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_HERDR_WIDTH=210 \
          bash "$DISPATCH" 61 reviewer abc1234)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: pane :: layout :: --pane :: w1:p1"
  has "herdr :: pane :: split :: --pane :: w1:p1 :: --direction :: right"
  hasnt "herdr :: tab :: create"
  [ "$(line_of 'pane :: layout')" -lt "$(line_of 'pane :: split')" ] \
    || fail "split without measuring the pane first"

  echo "--- the reviewer is a claude session named apart from the worker"
  has "herdr :: agent :: start :: issue-61-review :: --kind :: claude :: --pane :: w1:p10 :: --"
  has ":: --permission-mode :: bypassPermissions :: --model :: opus :: -n :: issue-61-review"
  has "herdr :: agent :: prompt :: issue-61-review :: code-review abc1234 #61"
  has "herdr :: pane :: rename :: w1:p10 :: #61 reviewer"
  has "herdr :: pane :: report-metadata :: w1:p10 :: --source :: mmw :: --token :: model=opus"

  echo "--- a narrow pane splits downwards"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_HERDR_WIDTH=120 \
          bash "$DISPATCH" 61 reviewer abc1234)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: pane :: split :: --pane :: w1:p1 :: --direction :: down"
  hasnt "herdr :: tab :: create"
}

scenario_badrole() {
  local code
  echo "--- a role that is not in the table"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$DISPATCH" 61 planner)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  one_line_reason
  grep -q 'planner' "$TMP/err" || fail "the reason does not name the role: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for an unknown role"

  echo "--- a role whose launch command is a dash, meaning it is a subagent"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$DISPATCH" 61 verifier)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  one_line_reason
  grep -q 'verifier' "$TMP/err" || fail "the reason does not name the role: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a subagent role"
}

scenario_idletimeout() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_HERDR_WAIT_FAIL=1 \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"
  echo "--- readiness is waited for at most 120 seconds"
  has "herdr :: agent :: wait :: issue-61 :: --until :: idle :: --until :: done :: --timeout :: 120000"
  echo "--- and nothing is said to an agent that never became ready"
  hasnt "herdr :: agent :: prompt"
  grep -q '120s' "$TMP/err" || fail "the reason does not say how long it waited: $(cat "$TMP/err")"
}

scenario_notready() {
  local code
  echo "--- a closed ticket"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_STATE=CLOSED \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 2 ] || fail "expected exit 2 for a closed ticket, got $code"
  one_line_reason
  grep -q 'closed' "$TMP/err" || fail "the reason does not say the ticket is closed: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a closed ticket"

  echo "--- a ticket that is not in the agent lane"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_LABELS=needs-triage \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 2 ] || fail "expected exit 2 for a ticket without the label, got $code"
  one_line_reason
  grep -q 'ready-for-agent' "$TMP/err" || fail "the reason does not name the missing label: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a ticket without the label"

  echo "--- a ticket whose blocker is still open"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_BLOCKERS=60:OPEN \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 2 ] || fail "expected exit 2 for a blocked ticket, got $code"
  one_line_reason
  grep -q '#60' "$TMP/err" || fail "the reason does not name the blocker: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a blocked ticket"

  echo "--- a blocker that is already closed is no obstacle"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_BLOCKERS=60:CLOSED \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 0 ] || fail "a closed blocker should not stop a dispatch, got $code: $(cat "$TMP/err")"
}

scenario_noherdr() {
  local code
  echo "--- dispatching from outside Herdr refuses and starts nothing"
  reset_log
  code="$(run_dispatch env -u HERDR_ENV -u HERDR_PANE_ID -u HERDR_WORKSPACE_ID \
          bash "$DISPATCH" 61 junior-worker)"
  [ "$code" = 2 ] || fail "expected exit 2 outside Herdr, got $code"
  one_line_reason
  grep -qi 'herdr' "$TMP/err" || fail "the reason does not say why: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called from outside Herdr"

  echo "--- waiting from outside Herdr still works, on the tracker alone"
  reset_log
  code="$(run_dispatch env -u HERDR_ENV -u HERDR_PANE_ID -u HERDR_WORKSPACE_ID FAKE_GH_MATCH_ON=1 \
          bash "$DISPATCH" wait 61 '^REVIEW' 30)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q '^REVIEW clean' "$TMP/out" || fail "the matched comment was not printed: $(cat "$TMP/out")"
  grep -q 'No findings inside the ticket' "$TMP/out" || fail "only the first line was printed"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called from outside Herdr"
}

scenario_wait() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_PANE_ID=w1:p1 FAKE_GH_MATCH_ON=3 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"issue-61-review","pane_id":"w1:p10"},{"name":"issue-61","pane_id":"w1:p1"}]}}' \
          bash "$DISPATCH" wait 61 '^REVIEW' 120)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  echo "--- the session waited on is the reviewer, not the caller's own"
  has "herdr :: agent :: list"
  has "herdr :: agent :: wait :: issue-61-review :: --timeout"
  hasnt "herdr :: agent :: wait :: issue-61 :: --timeout"

  echo "--- three rounds, each held open by Herdr before the tracker is asked"
  [ "$(count_of 'gh :: issue :: view :: 61 :: --json :: comments')" = 3 ] \
    || fail "expected the tracker to be asked three times, got $(count_of 'gh :: issue :: view :: 61 :: --json :: comments')"
  [ "$(count_of 'herdr :: agent :: wait')" = 3 ] \
    || fail "expected three lifecycle waits, got $(count_of 'herdr :: agent :: wait')"
  python3 -c '
import os, sys

rounds = []
for line in open(os.environ["MMW_TEST_LOG"], encoding="utf-8"):
    if "agent :: wait" in line:
        rounds.append("wait")
    elif "--json :: comments" in line:
        rounds.append("ask")
if rounds != ["wait", "ask"] * 3:
    sys.exit("rounds were " + " ".join(rounds) + ", not one wait before each ask")
' || fail "the tracker was not asked once per lifecycle change"

  echo "--- the whole matching comment reaches stdout"
  grep -q '^REVIEW clean' "$TMP/out" || fail "the matched comment was not printed"
  grep -q 'No findings inside the ticket' "$TMP/out" || fail "only the first line was printed"

  echo "--- nothing is written on the ticket when the wait succeeds"
  hasnt "gh :: issue :: comment"
}

scenario_waittimeout() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_PANE_ID=w1:p1 FAKE_GH_MATCH_ON=0 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"issue-61-review","pane_id":"w1:p10"}]}}' \
          bash "$DISPATCH" wait 61 '^REVIEW' 1)"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"

  echo "--- the ticket is told who did not finish"
  has "gh :: issue :: comment :: 61 :: --body"
  grep -q 'issue-61-review' "$TMP/err" || fail "the reason does not name the agent: $(cat "$TMP/err")"

  echo "--- and that comment is the last thing done before giving up"
  local last_gh
  last_gh="$(grep '^gh ' "$MMW_TEST_LOG" | tail -1)"
  case "$last_gh" in
    "gh :: issue :: comment"*) ;;
    *) fail "the last tracker call was not the comment: $last_gh" ;;
  esac
}

scenario_placeholder() {
  echo "--- a copy of the skill, so the table can be edited without touching the source"
  local copy="$TMP/skill"
  rm -rf "$copy"
  mkdir -p "$copy"
  cp -R "$SKILL/models.md" "$SKILL/scripts" "$copy/"

  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$copy/scripts/dispatch.sh" 61 senior-worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  echo "--- model, thinking level and ticket number all reach the launch command"
  has "herdr :: agent :: start :: issue-61 :: --kind :: grok :: --"
  has ":: --worktree=issue-61 :: --worktree-ref :: main :: --permission-mode :: bypassPermissions :: -m :: grok-4.6 :: --reasoning-effort :: xhigh"
  hasnt "{model}"
  hasnt "{effort}"
  hasnt "{n}"

  echo "--- editing the model column changes the next dispatch, with nothing reinstalled"
  MMW_TABLE="$copy/models.md" python3 -c '
import os

path = os.environ["MMW_TABLE"]
lines = open(path, encoding="utf-8").read().splitlines(True)
out = [line.replace("grok-4.6", "grok-4.7-under-test")
       if line.startswith("| senior-worker ") else line
       for line in lines]
open(path, "w", encoding="utf-8").writelines(out)
'
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$copy/scripts/dispatch.sh" 61 senior-worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: -m :: grok-4.7-under-test"
  has "herdr :: pane :: report-metadata :: w1:p9 :: --source :: mmw :: --token :: model=grok-4.7-under-test"
  hasnt ":: -m :: grok-4.6 ::"
}

# ------------------------------------------------------------------ entry

ALL="worker reviewer badrole idletimeout notready noherdr wait waittimeout placeholder"

case "${1:-}" in
  worker|reviewer|badrole|idletimeout|notready|noherdr|wait|waittimeout|placeholder)
    wanted="$1" ;;
  all)
    wanted="$ALL" ;;
  *)
    echo "usage: test_dispatch.sh $(echo "$ALL" | tr ' ' '|')|all" >&2
    exit 2 ;;
esac

banner_for() {
  case "$1" in
    worker) echo DISPATCH-WORKER-OK ;;
    reviewer) echo DISPATCH-REVIEWER-OK ;;
    badrole) echo DISPATCH-BADROLE-OK ;;
    idletimeout) echo DISPATCH-IDLE-TIMEOUT-OK ;;
    notready) echo DISPATCH-NOTREADY-OK ;;
    noherdr) echo DISPATCH-NOHERDR-OK ;;
    wait) echo DISPATCH-WAIT-OK ;;
    waittimeout) echo DISPATCH-WAITTIMEOUT-OK ;;
    placeholder) echo DISPATCH-PLACEHOLDER-OK ;;
  esac
}

for name in $wanted; do
  echo "=== $name"
  "scenario_$name"
  if [ "$rc" -eq 0 ]; then
    banner_for "$name"
  else
    echo "$name failed" >&2
    exit 1
  fi
done
