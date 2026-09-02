#!/usr/bin/env bash
#
# Tests for dispatch.sh. One scenario per run:
#
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh worker|reviewer|seat|runtable|runchecks
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh idletimeout|notready|livesession|noherdr
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh wait|waittimeout|placeholder
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh advance|advanceconflict|advancedirty
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
if [ "$1 $2 ${3:-}" = "agent start --help" ]; then
  echo "      --kind <KIND>"
  echo "          Supported agent kind and canonical executable"
  echo
  echo "          [possible values: ${FAKE_HERDR_KINDS:-pi, claude, codex, gemini, cursor, grok}]"
  exit 0
fi
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
  "api snapshot")
    if [ -n "${FAKE_HERDR_AGENTS:-}" ]; then
      printf '%s\n' "$FAKE_HERDR_AGENTS" \
        | python3 -c 'import json,sys; print(json.dumps({"result":{"snapshot":{"agents":(json.load(sys.stdin).get("result") or {}).get("agents") or []}}}))'
    else
      echo '{"result":{"snapshot":{"agents":[]}}}'
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
    "blockedBy": {"nodes": [{"number": int(b.split(":")[0]), "state": b.split(":")[1]}
                            for b in blockers.split(",") if b]},
    "title": os.environ.get("FAKE_GH_TITLE",
                            "landing 7 of 15: a new skill called dispatch"),
}))
' ;;
  *"/sub_issues"*)
    python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
print(json.dumps([{"number": t["number"]} for t in rows]))
' ;;
  *"--json state,labels,assignees,blockedBy,comments"*)
    MMW_WANT="$3" python3 -c '
import json, os, sys
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t["number"] == want), {})
print(json.dumps({
    "state": found.get("state", "OPEN"),
    "labels": [{"name": n} for n in found.get("labels", ["ready-for-agent"])],
    "assignees": [{"login": n} for n in found.get("assignees", [])],
    "blockedBy": {"nodes": found.get("blockedBy", [])},
    "comments": [{"body": b} for b in found.get("comments", [])],
    "title": found.get("title", "a ticket"),
    "createdAt": found.get("createdAt", "2026-08-30T00:00:00Z"),
    "closedAt": found.get("closedAt", ""),
}))
' ;;
  *) echo '{}' ;;
esac
FAKE

chmod +x "$TMP/bin/herdr" "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_GH_COMMENT_CALLS="$TMP/comment-calls"

# These tests run inside Herdr as often as not, and dispatch.sh reads the workspace it
# was started in to build the names it hands out. Cleared here so the answer is the same
# wherever the suite runs; the cases that want a workspace pass one of their own.
unset HERDR_WORKSPACE_ID

# A fixture repository of its own, so the worktrees dispatch.sh opens land under $TMP
# and never touch the repository these tests live in.
export MMW_WORKTREES="$TMP/worktrees"
git init -q -b main "$TMP/repo"
git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture

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

run_dispatch() { (cd "$TMP/repo" && "$@") > "$TMP/out" 2> "$TMP/err"; echo "$?"; }

# The host and model of a `models.md` row, so the scenarios below assert what the table
# says today rather than what it said when they were written.
row_host() { awk -F'|' -v want="$1" 'function t(s){gsub(/^[ \t`]+|[ \t`]+$/,"",s);return s} /^[ \t]*\|/ && NF==7 && t($2)==want {print t($3); exit}' "$SKILL/models.md"; }
row_model() { awk -F'|' -v want="$1" 'function t(s){gsub(/^[ \t`]+|[ \t`]+$/,"",s);return s} /^[ \t]*\|/ && NF==7 && t($2)==want {print t($4); exit}' "$SKILL/models.md"; }
JUNIOR_HOST="$(row_host junior-worker)"; JUNIOR_MODEL="$(row_model junior-worker)"
SENIOR_MODEL="$(row_model senior-worker)"
one_line_reason() {
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "the reason should be one line: $(cat "$TMP/err")"
}

# ------------------------------------------------------------------ scenarios

scenario_worker() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  echo "--- the ticket is read before anything is started"
  has "gh :: issue :: view :: 61 :: --json :: state,labels,blockedBy,title"
  local first_gh first_herdr
  first_gh="$(line_of '^gh ')"
  first_herdr="$(line_of '^herdr ')"
  { [ -n "$first_gh" ] && [ -n "$first_herdr" ] && [ "$first_gh" -lt "$first_herdr" ]; } \
    || fail "the tracker should be asked before the first herdr call"

  echo "--- one tab per ticket, opened inside the worktree dispatch itself made"
  has "herdr :: tab :: create"
  has ":: --workspace :: w1"
  has ":: --env :: MMW_TICKET=61"
  has ":: --env :: MMW_AUTONOMOUS=1"
  has ":: --no-focus"
  [ "$(arg_after --cwd)" = "$MMW_WORKTREES/repo/issue-61" ] \
    || fail "--cwd should be the ticket's worktree, got $(arg_after --cwd)"
  [ "$(git -C "$MMW_WORKTREES/repo/issue-61" rev-parse --abbrev-ref HEAD)" = "issue-61" ] \
    || fail "the worktree is not on branch issue-61"
  MMW_LABEL="$(arg_after --label)" python3 -c '
import os, sys

label = os.environ["MMW_LABEL"]
if not label.startswith("#61 "):
    sys.exit("label does not name the ticket: " + label)
if len(label) != 24:
    sys.exit("label should be #61 plus 20 title characters, got %d: %s" % (len(label), label))
' || fail "the tab label is wrong"

  echo "--- the agent starts in the tab's own pane, and nothing is split"
  has "herdr :: agent :: start :: w1-issue-61 :: --kind :: $JUNIOR_HOST :: --pane :: w1:p9 :: --"
  has ":: -m :: $JUNIOR_MODEL"
  hasnt "herdr :: pane :: split"

  echo "--- it is told what to work on only after it is ready"
  has "herdr :: agent :: wait :: w1-issue-61 :: --until :: idle :: --until :: done :: --timeout :: 120000"
  has "herdr :: agent :: prompt :: w1-issue-61 :: Use the implement skill to work ticket #61. You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work."
  [ "$(line_of 'agent :: wait')" -lt "$(line_of 'agent :: prompt')" ] \
    || fail "prompted before waiting for readiness"

  echo "--- and the prompt is confirmed to have landed, not just sent"
  has "herdr :: agent :: wait :: w1-issue-61 :: --until :: working :: --until :: blocked :: --timeout :: 15000"

  echo "--- the pane says who it is, to a person and to a machine"
  has "herdr :: pane :: rename :: w1:p9 :: #61 worker"
  has "herdr :: pane :: report-metadata :: w1:p9 :: --source :: mmw :: --token :: ticket=61 :: --token :: kind=worker :: --token :: model=$JUNIOR_MODEL :: --ttl-ms :: 86400000"
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
  has ":: --env :: MMW_AUTONOMOUS=1 :: --no-focus"
  hasnt "herdr :: tab :: create"
  [ "$(line_of 'pane :: layout')" -lt "$(line_of 'pane :: split')" ] \
    || fail "split without measuring the pane first"

  echo "--- the reviewer is a claude session named apart from the worker"
  has "herdr :: agent :: start :: w1-issue-61-review :: --kind :: claude :: --pane :: w1:p10 :: --"
  # `-n` is Claude Code's own session name, out of `models.md`, not the Herdr name
  # this script hands out: two namespaces, and only the Herdr one collides.
  has ":: --permission-mode :: bypassPermissions :: --model :: opus :: --effort :: high :: -n :: issue-61-review"
  has "herdr :: agent :: prompt :: w1-issue-61-review :: Use the code-review skill to review ticket #61 from base commit abc1234. You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work."
  has "herdr :: pane :: rename :: w1:p10 :: #61 reviewer"
  has "herdr :: pane :: report-metadata :: w1:p10 :: --source :: mmw :: --token :: ticket=61 :: --token :: kind=reviewer :: --token :: model=opus"

  echo "--- a narrow pane splits downwards"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_HERDR_WIDTH=120 \
          bash "$DISPATCH" 61 reviewer abc1234)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: pane :: split :: --pane :: w1:p1 :: --direction :: down"
  hasnt "herdr :: tab :: create"
}

scenario_seat() {
  local code
  echo "--- a ticket with no worker label starts on the default row"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_LABELS="ready-for-agent" bash "$DISPATCH" 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: --token :: model=$JUNIOR_MODEL"

  echo "--- a senior-worker label starts that row instead"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_LABELS="ready-for-agent,senior-worker" bash "$DISPATCH" 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: --token :: model=$SENIOR_MODEL"
  has ":: --reasoning-effort :: xhigh"

  echo "--- two worker labels are refused, and nothing is started"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_LABELS="ready-for-agent,junior-worker,senior-worker" \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  one_line_reason
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a ticket with two worker labels"

  echo "--- a worker label the table has no row for is refused, never quietly swapped"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_LABELS="ready-for-agent,principal-worker" bash "$DISPATCH" 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  one_line_reason
  grep -q 'principal-worker' "$TMP/err" || fail "the reason does not name the label: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for an unknown worker label"

  echo "--- the second argument is worker or reviewer"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$DISPATCH" 61 planner)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  one_line_reason
  grep -q 'planner' "$TMP/err" || fail "the reason does not name the argument: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for an unknown kind"
}

scenario_runtable() {
  local code
  echo "--- the night takes no role, because the tickets carry it"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$DISPATCH" run 76 --role senior-worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for an argument run does not take"

  echo "--- a worker row that starts no session is refused while somebody is still here"
  local copy="$TMP/runtable"
  rm -rf "$copy"
  mkdir -p "$copy"
  cp -R "$SKILL/models.md" "$SKILL/scripts" "$copy/"
  MMW_TABLE="$copy/models.md" python3 -c '
import os

path = os.environ["MMW_TABLE"]
lines = open(path, encoding="utf-8").read().splitlines(True)
out = ["| senior-worker | grok | `grok-4.6` | xhigh | — |\n"
       if line.startswith("| senior-worker ") else line
       for line in lines]
open(path, "w", encoding="utf-8").writelines(out)
'
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          bash "$copy/scripts/dispatch.sh" run 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  one_line_reason
  grep -q 'senior-worker' "$TMP/err" || fail "the reason does not name the row: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a row that starts nothing"
}

# A copy of the skill two directories under a fake install.sh, so `run` gets past the
# `install.sh --check` it insists on without asking about this machine's real install.
skill_copy_for_run() {
  local copy="$TMP/fake/skills/$1"
  rm -rf "$TMP/fake"
  mkdir -p "$copy"
  cp -R "$SKILL/models.md" "$SKILL/scripts" "$copy/"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$TMP/fake/install.sh"
  chmod +x "$TMP/fake/install.sh"
  printf '%s\n' "$copy"
}

scenario_runchecks() {
  local code copy
  copy="$(skill_copy_for_run runchecks)"
  fresh_repo

  echo "--- a ticket whose worker label names no row stops the night, and names the ticket"
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker"]},
  {"number": 62, "state": "OPEN", "labels": ["ready-for-agent", "principal-worker"],
   "blockedBy": [{"number": 61, "state": "OPEN"}]},
  {"number": 63, "state": "OPEN", "labels": ["needs-triage", "principal-worker"]},
  {"number": 64, "state": "CLOSED", "labels": ["principal-worker"]}
]
JSON
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" run 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  one_line_reason
  grep -q '#62' "$TMP/err" || fail "the reason does not name the ticket: $(cat "$TMP/err")"
  grep -q 'principal-worker' "$TMP/err" || fail "the reason does not name the label: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: rename"
  hasnt "herdr :: tab :: create"

  echo "--- a ticket with two worker labels stops the night the same way"
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker", "senior-worker"]}
]
JSON
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" run 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  one_line_reason
  grep -q '#61' "$TMP/err" || fail "the reason does not name the ticket: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: rename"
  hasnt "herdr :: tab :: create"

  echo "--- a row whose host herdr does not know stops the night"
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "senior-worker"]}
]
JSON
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_HERDR_KINDS="pi, claude, codex" \
          bash "$copy/scripts/dispatch.sh" run 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  one_line_reason
  grep -q "$JUNIOR_HOST" "$TMP/err" || fail "the reason does not name the host: $(cat "$TMP/err")"
  has "herdr :: agent :: start :: --help"
  hasnt "herdr :: agent :: rename"
  hasnt "herdr :: tab :: create"

  echo "--- and when the help carries no kind list, the night is refused rather than guessed"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_HERDR_KINDS=" " \
          bash "$copy/scripts/dispatch.sh" run 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: rename"

  echo "--- a batch whose labels and hosts all resolve opens the night"
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker"]},
  {"number": 62, "state": "OPEN", "labels": ["ready-for-agent", "senior-worker"],
   "blockedBy": [{"number": 61, "state": "OPEN"}]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" run 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: rename :: w1:p1 :: w1-mmw-main"
  has "herdr :: tab :: create :: --workspace :: w1"
  has "herdr :: pane :: run :: w1:p9"
  hasnt "herdr :: agent :: start :: w1-issue"
}

scenario_idletimeout() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_HERDR_WAIT_FAIL=1 \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"
  echo "--- readiness is waited for at most 120 seconds"
  has "herdr :: agent :: wait :: w1-issue-61 :: --until :: idle :: --until :: done :: --timeout :: 120000"
  echo "--- and nothing is said to an agent that never became ready"
  hasnt "herdr :: agent :: prompt"
  grep -q '120s' "$TMP/err" || fail "the reason does not say how long it waited: $(cat "$TMP/err")"
}

scenario_notready() {
  local code
  echo "--- a closed ticket"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_STATE=CLOSED \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 for a closed ticket, got $code"
  one_line_reason
  grep -q 'closed' "$TMP/err" || fail "the reason does not say the ticket is closed: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a closed ticket"

  echo "--- a ticket that is not in the agent lane"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_LABELS=needs-triage \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 for a ticket without the label, got $code"
  one_line_reason
  grep -q 'ready-for-agent' "$TMP/err" || fail "the reason does not name the missing label: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a ticket without the label"

  echo "--- a ticket whose blocker is still open"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_BLOCKERS=60:OPEN \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 for a blocked ticket, got $code"
  one_line_reason
  grep -q '#60' "$TMP/err" || fail "the reason does not name the blocker: $(cat "$TMP/err")"
  [ "$(count_of 'herdr ::')" = 0 ] || fail "herdr was called for a blocked ticket"

  echo "--- a blocker that is already closed is no obstacle"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 FAKE_GH_BLOCKERS=60:CLOSED \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 0 ] || fail "a closed blocker should not stop a dispatch, got $code: $(cat "$TMP/err")"
}

scenario_livesession() {
  local code
  echo "--- a worker whose Herdr name is already live is refused before anything opens"
  reset_log
  fresh_repo
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"w1-issue-61","pane_id":"w1:p5"}]}}' \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  one_line_reason
  grep -q 'w1-issue-61' "$TMP/err" || fail "the reason does not name the session: $(cat "$TMP/err")"
  has "herdr :: agent :: list"
  hasnt "herdr :: tab :: create"
  hasnt "herdr :: pane :: split"
  hasnt "herdr :: agent :: start"
  [ ! -d "$MMW_WORKTREES/repo/issue-61" ] || fail "a worktree was opened for a ticket already live"

  echo "--- a reviewer whose name is already live is refused the same way"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"w1-issue-61-review","pane_id":"w1:p5"}]}}' \
          bash "$DISPATCH" 61 reviewer abc1234)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  one_line_reason
  grep -q 'w1-issue-61-review' "$TMP/err" || fail "the reason does not name the session: $(cat "$TMP/err")"
  hasnt "herdr :: pane :: layout"
  hasnt "herdr :: pane :: split"
  hasnt "herdr :: agent :: start"

  echo "--- the worker's name being live does not stop its reviewer, and the other way round"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"w1-issue-61","pane_id":"w1:p1"}]}}' \
          bash "$DISPATCH" 61 reviewer abc1234)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: start :: w1-issue-61-review"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"w1-issue-61-review","pane_id":"w1:p10"},{"name":"w2-issue-61","pane_id":"w2:p1"}]}}' \
          bash "$DISPATCH" 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: start :: w1-issue-61"
}

scenario_noherdr() {
  local code
  echo "--- dispatching from outside Herdr refuses and starts nothing"
  reset_log
  code="$(run_dispatch env -u HERDR_ENV -u HERDR_PANE_ID -u HERDR_WORKSPACE_ID \
          bash "$DISPATCH" 61 worker)"
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

  echo "--- a worker waits on its own reviewer"
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

  echo "--- whoever is not the worker waits on the worker instead"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_PANE_ID=w1:p99 FAKE_GH_MATCH_ON=1 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"issue-61-review","pane_id":"w1:p10"},{"name":"issue-61","pane_id":"w1:p1"}]}}' \
          bash "$DISPATCH" wait 61 '^REVIEW' 120)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: wait :: issue-61 :: --timeout"
  hasnt "herdr :: agent :: wait :: issue-61-review :: --timeout"
}

scenario_waittimeout() {
  reset_log
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_PANE_ID=w1:p1 FAKE_GH_MATCH_ON=0 \
          FAKE_HERDR_AGENTS='{"result":{"agents":[{"name":"issue-61","pane_id":"w1:p1"},{"name":"issue-61-review","pane_id":"w1:p10"}]}}' \
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
          FAKE_GH_LABELS="ready-for-agent,senior-worker" \
          bash "$copy/scripts/dispatch.sh" 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  echo "--- model, thinking level and ticket number all reach the launch arguments"
  has "herdr :: agent :: start :: w1-issue-61 :: --kind :: grok :: --"
  has ":: --permission-mode :: bypassPermissions :: -m :: grok-4.6 :: --reasoning-effort :: xhigh"
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
          FAKE_GH_LABELS="ready-for-agent,senior-worker" \
          bash "$copy/scripts/dispatch.sh" 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: -m :: grok-4.7-under-test"
  has "herdr :: pane :: report-metadata :: w1:p9 :: --source :: mmw :: --token :: ticket=61 :: --token :: kind=worker :: --token :: model=grok-4.7-under-test"
  hasnt ":: -m :: grok-4.6 ::"
}

# ------------------------------------------------------------------ entry

# ------------------------------------------------------------------ advance

# The scenarios before these ones dispatch tickets, and dispatching leaves branches and
# worktrees behind. Each advance scenario starts from a repository nobody has touched.
fresh_repo() {
  rm -rf "$TMP/repo" "$MMW_WORKTREES"
  git init -q -b main "$TMP/repo"
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture
}

# A branch off main with one file on it, the shape `worktree_for` leaves behind.
make_branch() {
  local name="$1" file="$2" text="$3"
  git -C "$TMP/repo" checkout -q -b "$name" main
  printf '%s\n' "$text" > "$TMP/repo/$file"
  git -C "$TMP/repo" add "$file"
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m "$name"
  git -C "$TMP/repo" checkout -q main
}

# The batch `board.py --advance-plan` reads. Closing order is what the merge order has
# to follow, so the two closed tickets close a minute apart.
write_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T01:00:00Z",
   "comments": ["self-run\\n3 met", "ALL MET\\nBranch: issue-61"]},
  {"number": 62, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T02:00:00Z",
   "comments": ["ALL MET\\nBranch: issue-62"]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
}

merge_subjects() {
  git -C "$TMP/repo" log --merges --first-parent --format='%s'
}

scenario_advance() {
  reset_log
  fresh_repo
  write_batch
  make_branch issue-61 one.txt "from 61"
  make_branch issue-62 two.txt "from 62"
  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76)"

  echo "--- both finished branches land on the main branch"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  [ -f "$TMP/repo/one.txt" ] || fail "issue-61 was not merged"
  [ -f "$TMP/repo/two.txt" ] || fail "issue-62 was not merged"

  echo "--- in the order the tickets closed, each keeping a merge commit of its own"
  [ "$(merge_subjects)" = "Merge branch 'issue-62'
Merge branch 'issue-61'" ] || fail "merge order is wrong: $(merge_subjects)"

  echo "--- and the frontier is started afterwards, never before"
  has "herdr :: agent :: start :: w1-issue-63"
  local merged started
  merged=$(git -C "$TMP/repo" rev-list --count HEAD)
  [ "$merged" -ge 3 ] || fail "expected the merges to be commits, got $merged"
  started="$(line_of 'agent :: start :: w1-issue-63')"
  [ "$started" -gt 0 ] || fail "the frontier ticket was never started"

  echo "--- a second run has nothing left to do and starts nothing new"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76)"
  [ "$code" = 0 ] || fail "exit $code on the second run: $(cat "$TMP/err")"
  [ "$(merge_subjects | wc -l | tr -d ' ')" = 2 ] || fail "it merged something twice"
  grep -q "merged 0" "$TMP/out" || fail "the second run should report nothing merged: $(cat "$TMP/out")"
}

scenario_advanceconflict() {
  reset_log
  fresh_repo
  write_batch
  # Both branches rewrite the same line, so the second merge cannot be automatic.
  printf 'base\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m shared
  make_branch issue-61 shared.txt "from 61"
  make_branch issue-62 shared.txt "from 62"

  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76)"

  echo "--- a conflict stops the run with its own exit code"
  [ "$code" = 3 ] || fail "exit $code, not 3: $(cat "$TMP/err")"

  echo "--- the merge is left in the tree, never aborted"
  git -C "$TMP/repo" rev-parse -q --verify MERGE_HEAD >/dev/null \
    || fail "MERGE_HEAD is gone, so the merge was aborted"

  echo "--- and the report names both sides and the files"
  grep -q "CONFLICT merging issue-62" "$TMP/out" || fail "no CONFLICT line: $(cat "$TMP/out")"
  grep -q "MERGE_HEAD  issue-62" "$TMP/out" || fail "the incoming side is not named"
  grep -q "issue-61" "$TMP/out" || fail "the side already merged is not named"
  grep -q "shared.txt" "$TMP/out" || fail "the conflicted file is not named"

  echo "--- nothing is dispatched while the tree is half-merged"
  hasnt "agent :: start :: w1-issue-63"

  echo "--- running it again changes nothing and says the same thing"
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76)"
  [ "$code" = 3 ] || fail "exit $code on the second run, not 3"
  grep -q "CONFLICT merging issue-62" "$TMP/out" || fail "the second run lost the report"
  hasnt "agent :: start :: w1-issue-63"

  echo "--- once it is resolved and committed, the run carries on from there"
  printf 'resolved\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --no-edit
  reset_log
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76)"
  [ "$code" = 0 ] || fail "exit $code after the resolution: $(cat "$TMP/err")"
  grep -q "merged 0" "$TMP/out" || fail "it merged something already in: $(cat "$TMP/out")"
  has "herdr :: agent :: start :: w1-issue-63"
}

scenario_advancedirty() {
  reset_log
  fresh_repo
  write_batch
  make_branch issue-61 one.txt "from 61"
  printf 'unfinished\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m shared
  printf 'edited\n' > "$TMP/repo/shared.txt"

  local code
  code="$(run_dispatch env HERDR_ENV=1 HERDR_WORKSPACE_ID=w1 HERDR_PANE_ID=w1:p1 \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76)"

  echo "--- a tree with uncommitted work is refused before anything is merged"
  [ "$code" = 2 ] || fail "exit $code, not 2: $(cat "$TMP/err")"
  one_line_reason
  grep -q "uncommitted changes" "$TMP/err" || fail "the reason does not say why: $(cat "$TMP/err")"
  [ ! -f "$TMP/repo/one.txt" ] || fail "it merged despite the dirty tree"
  hasnt "agent :: start"
}

ALL="worker reviewer seat runtable runchecks idletimeout notready livesession noherdr wait waittimeout placeholder advance advanceconflict advancedirty"

case "${1:-}" in
  worker|reviewer|seat|runtable|runchecks|idletimeout|notready|livesession|noherdr|wait|waittimeout|placeholder|advance|advanceconflict|advancedirty)
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
    seat) echo DISPATCH-SEAT-OK ;;
    runtable) echo DISPATCH-RUNTABLE-OK ;;
    runchecks) echo DISPATCH-RUNCHECKS-OK ;;
    idletimeout) echo DISPATCH-IDLE-TIMEOUT-OK ;;
    notready) echo DISPATCH-NOTREADY-OK ;;
    livesession) echo DISPATCH-LIVESESSION-OK ;;
    noherdr) echo DISPATCH-NOHERDR-OK ;;
    wait) echo DISPATCH-WAIT-OK ;;
    waittimeout) echo DISPATCH-WAITTIMEOUT-OK ;;
    placeholder) echo DISPATCH-PLACEHOLDER-OK ;;
    advance) echo DISPATCH-ADVANCE-OK ;;
    advanceconflict) echo DISPATCH-ADVANCE-CONFLICT-OK ;;
    advancedirty) echo DISPATCH-ADVANCE-DIRTY-OK ;;
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
