#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
INVESTIGATE="$PLUGIN/scripts/investigate.sh"
MMW="$PLUGIN/scripts/mmw.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

mkdir -p "$TMP/bin" "$TMP/markers"
export DROID_TEST_LOG="$TMP/droid.log"
export DROID_FAKE_MARKERS="$TMP/markers"
cat >"$TMP/bin/droid" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$DROID_TEST_LOG"
prompt=""
list_tools=0
model=""
while [ $# -gt 0 ]; do
  case "$1" in
    --file) prompt="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --list-tools) list_tools=1; shift ;;
    *) shift ;;
  esac
done
if [ "$list_tools" = 1 ]; then
  [ "${DROID_FAKE_LIST_FAIL:-0}" = 1 ] && exit 4
  [ -n "${DROID_FAKE_LIST_SLEEP:-}" ] && sleep "$DROID_FAKE_LIST_SLEEP"
  jq -cn '[
    {id:"create-cli"},{id:"edit-cli"},{id:"execute-cli"},{id:"task-cli"},
    {id:"web_search"},{id:"fetch_url"},{id:"read-cli"},{id:"grep_tool_cli"},
    {id:"glob-search-cli"},{id:"ls-cli"},{id:"apply-patch-cli"}
  ]'
  exit 0
fi
[ -f "$prompt" ] || exit 3
sleep 0.03

if grep -q '^证据：' "$prompt"; then
  if [ -n "${DROID_FAKE_SYNTH_FAIL_ONCE:-}" ] \
    && [ ! -f "$DROID_FAKE_MARKERS/synth-failed" ]; then
    touch "$DROID_FAKE_MARKERS/synth-failed"
    jq -cn '{type:"result",subtype:"success",is_error:false,result:"not-json",session_id:"synth-session"}'
    exit 0
  fi
  payload="$(jq -cn '{markdown:"# Investigation\n\nVerified evidence with `src/app.py:10`.",open_questions:["remaining gap"],spinoff_candidates:[{tag:"optimize",finding:"later cleanup"}]}')"
  jq -cn --arg result "$payload" \
    '{type:"result",subtype:"success",is_error:false,result:$result,session_id:"synth-session"}'
  exit 0
fi

angle="$(sed -n 's/^angle=//p' "$prompt" | head -1)"
mode="$(sed -n 's/^mode=//p' "$prompt" | head -1)"
if [ "$angle" = retry-topic ] && [ ! -f "$DROID_FAKE_MARKERS/retry-topic-failed" ]; then
  touch "$DROID_FAKE_MARKERS/retry-topic-failed"
  jq -cn '{type:"result",subtype:"success",is_error:false,result:"invalid topic",session_id:"topic-retry-session"}'
  exit 0
fi
if [ "$mode" = external ]; then
  locator="https://example.com/source"
  wrong_locator="src/app.py:10"
else
  locator="src/app.py:10"
  wrong_locator="https://example.com/wrong-mode"
fi
payload="$(jq -cn --arg angle "$angle" --arg locator "$locator" --arg wrong "$wrong_locator" \
  '{topic:$angle,findings:[
      {claim:"verified",locator:$locator,confidence:"high"},
      {claim:"weak",locator:$locator,confidence:"low"},
      {claim:"missing locator",locator:"",confidence:"medium"},
      {claim:"blank locator",locator:"   ",confidence:"high"},
      {claim:"wrong mode locator",locator:$wrong,confidence:"high"}
    ],summary:"current state; unrelated side issue remains a candidate",gaps:["one gap"]}')"
jq -cn --arg result "$payload" --arg session "topic-$angle" \
  '{type:"result",subtype:"success",is_error:false,result:$result,session_id:$session}'
FAKE
chmod +x "$TMP/bin/droid"
export PATH="$TMP/bin:$PATH"

git -C "$TMP" init -q
git -C "$TMP" config user.email test@example.com
git -C "$TMP" config user.name test
echo base >"$TMP/base.txt"
git -C "$TMP" add base.txt
git -C "$TMP" commit -qm base

poll_completed() {
  local run="$1" i output
  for i in $(seq 1 80); do
    output="$(cd "$TMP" && bash "$INVESTIGATE" status --run "$run" 2>&1)" || true
    case "$output" in
      *INVESTIGATE_STATUS=COMPLETED*) printf '%s\n' "$output"; return 0 ;;
      *INVESTIGATE_STATUS=FAILED*) printf '%s\n' "$output"; return 1 ;;
    esac
    sleep 0.03
  done
  return 1
}

poll_failed() {
  local run="$1" i output
  for i in $(seq 1 80); do
    output="$(cd "$TMP" && bash "$INVESTIGATE" status --run "$run" 2>&1)" || true
    case "$output" in
      *INVESTIGATE_STATUS=FAILED*) printf '%s\n' "$output"; return 0 ;;
      *INVESTIGATE_STATUS=COMPLETED*) return 1 ;;
    esac
    sleep 0.03
  done
  return 1
}

cat >"$TMP/topics.json" <<'JSON'
[
  {"angle":"module-boundary","question":"Where is the seam?","skill":"codebase-design"},
  {"angle":"data-flow","question":"How does data move?","skill":""}
]
JSON

START="$(cd "$TMP" && bash "$MMW" investigate start --direction internal --topics "$TMP/topics.json" --run internal-a)"
printf '%s\n' "$START" | grep -q 'INVESTIGATE_STARTED.*topics=2' \
  && ok "parallel topic run starts" || no "investigate start"
poll_completed internal-a >/dev/null \
  && ok "topics validate and synthesize" || no "investigate completion"

ROOT="$TMP/.factory/multi-model-workflow/investigate-runs/internal-a"
[ "$(jq 'length' "$ROOT/synthesis/evidence.json")" = 2 ] \
  && ok "all topic evidence reaches synthesis" || no "evidence fan-in"
[ "$(jq '.findings|length' "$ROOT/topics/000/validated.json")" = 1 ] \
  && [ "$(jq '.dropped|length' "$ROOT/topics/000/validated.json")" = 4 ] \
  && ok "weak, blank, and mode-mismatched evidence filtered" || no "evidence filtering"
RESULT="$(cd "$TMP" && bash "$INVESTIGATE" result --run internal-a)"
printf '%s\n' "$RESULT" | grep -q '^# Investigation' \
  && ok "completed report is readable" || no "report output"
jq '.status="synthesizing" | .report_file=null' "$ROOT/run.json" >"$ROOT/run.json.tmp"
mv "$ROOT/run.json.tmp" "$ROOT/run.json"
cd "$TMP" && bash "$INVESTIGATE" status --run internal-a >/dev/null
[ "$(jq -r .status "$ROOT/run.json")" = completed ] \
  && [ "$(basename "$(jq -r .report_file "$ROOT/run.json")")" = result.json ] \
  && ok "completed result reconciles run ledger" || no "run ledger reconciliation"
printf '%s\n' "$$" >"$ROOT/.run-lock"
if cd "$TMP" && bash "$INVESTIGATE" status --run internal-a >/dev/null 2>&1; then
  no "concurrent status must fail"
else
  ok "run ledger update is locked"
fi
rm -f "$ROOT/.run-lock"
printf '99999999\n' >"$ROOT/.run-lock"
if cd "$TMP" && bash "$INVESTIGATE" status --run internal-a >/dev/null 2>&1; then
  no "stale lock must fail closed"
elif [ -e "$ROOT/.run-lock" ]; then
  rm -f "$ROOT/.run-lock"
  if cd "$TMP" && bash "$INVESTIGATE" status --run internal-a >/dev/null; then
    ok "stale run lock requires explicit verified removal"
  else
    no "status failed after explicit stale-lock removal"
  fi
else
  no "stale lock was removed unsafely"
fi
if grep 'topics/00[01]/prompt.md' "$DROID_TEST_LOG" | grep -q -- '--disabled-tools .*web_search.*fetch_url'; then
  ok "internal topics disable external search"
else
  no "internal tool restriction"
fi
if grep 'topics/00[01]/prompt.md' "$DROID_TEST_LOG" | grep -- '--disabled-tools' | grep -q 'execute-cli'; then
  no "internal bug investigation lost Execute"
else
  ok "internal topics retain diagnostic Execute"
fi
if grep 'synthesis/prompt.md' "$DROID_TEST_LOG" | grep -q -- '--disabled-tools .*apply-patch-cli'; then
  ok "synthesis uses its own model tool inventory"
else
  no "synthesis model tool restriction"
fi
if cd "$TMP" && bash "$INVESTIGATE" start --direction internal --topics "$TMP/topics.json" --run internal-a >/dev/null 2>&1; then
  no "duplicate run must fail"
else
  ok "duplicate run fails closed"
fi
mkdir "$TMP/inherited-staging-victim"
if cd "$TMP" && MMW_INVESTIGATE_STAGING="$TMP/inherited-staging-victim" \
  bash "$INVESTIGATE" start --direction internal --topics "$TMP/topics.json" \
  --run internal-a >/dev/null 2>&1; then
  no "duplicate run with inherited staging must fail"
elif [ -d "$TMP/inherited-staging-victim" ]; then
  ok "inherited cleanup path is ignored"
else
  no "inherited staging path was deleted"
fi
set +e
(cd "$TMP" && DROID_FAKE_LIST_SLEEP=0.05 bash "$INVESTIGATE" start \
  --direction internal --topics "$TMP/topics.json" --run concurrent-a >/dev/null 2>&1) &
p1=$!
(cd "$TMP" && DROID_FAKE_LIST_SLEEP=0.05 bash "$INVESTIGATE" start \
  --direction internal --topics "$TMP/topics.json" --run concurrent-a >/dev/null 2>&1) &
p2=$!
wait "$p1"; r1=$?
wait "$p2"; r2=$?
set -e
successes=0
if [ "$r1" -eq 0 ]; then successes=$((successes+1)); fi
if [ "$r2" -eq 0 ]; then successes=$((successes+1)); fi
if [ "$successes" -eq 1 ]; then
  ok "concurrent duplicate start is atomic"
else
  no "concurrent start expected exactly one success"
fi
poll_completed concurrent-a >/dev/null || no "concurrent winner completion"
set +e
DROID_FAKE_LIST_SLEEP=0.5 bash -c \
  'cd "$1"; exec bash "$2" start --direction internal --topics "$3" --run interrupted-a' \
  _ "$TMP" "$INVESTIGATE" "$TMP/topics.json" >/dev/null 2>&1 &
interrupted_pid=$!
sleep 0.05
kill "$interrupted_pid" 2>/dev/null
wait "$interrupted_pid" 2>/dev/null
sleep 0.05
set -e
INTERRUPTED_PARENT="$TMP/.factory/multi-model-workflow/investigate-runs"
if [ ! -e "$INTERRUPTED_PARENT/interrupted-a" ] \
  && ! compgen -G "$INTERRUPTED_PARENT/.interrupted-a.start.*" >/dev/null; then
  ok "interrupted start publishes no partial run"
else
  no "interrupted start left partial state"
fi
cd "$TMP" && bash "$INVESTIGATE" start \
  --direction internal --topics "$TMP/topics.json" --run interrupted-a >/dev/null
poll_completed interrupted-a >/dev/null \
  && ok "interrupted run id can restart cleanly" || no "interrupted start recovery"

cat >"$TMP/external.json" <<'JSON'
[{"angle":"library-practice","question":"What is established externally?"}]
JSON
cd "$TMP" && bash "$INVESTIGATE" start --direction external --topics "$TMP/external.json" --run external-a >/dev/null
poll_completed external-a >/dev/null \
  && ok "external topic completes" || no "external completion"
if grep 'external-a/topics/000/prompt.md' "$DROID_TEST_LOG" | grep -q -- '--disabled-tools .*read-cli.*grep_tool_cli'; then
  ok "external topics disable repository reads"
else
  no "external tool restriction"
fi

cat >"$TMP/both-invalid.json" <<'JSON'
[{"angle":"missing-mode","question":"Which direction?"}]
JSON
if cd "$TMP" && bash "$INVESTIGATE" start --direction both --topics "$TMP/both-invalid.json" --run both-invalid >/dev/null 2>&1; then
  no "both direction requires per-topic mode"
else
  ok "both direction validates topic mode"
fi
if cd "$TMP" && DROID_FAKE_LIST_FAIL=1 bash "$INVESTIGATE" start \
  --direction internal --topics "$TMP/external.json" --run inventory-fail >/dev/null 2>&1; then
  no "tool inventory failure must stop start"
elif [ ! -e "$TMP/.factory/multi-model-workflow/investigate-runs/inventory-fail" ]; then
  ok "tool inventory failure leaves no partial run"
else
  no "tool inventory failure left partial state"
fi

cat >"$TMP/retry.json" <<'JSON'
[
  {"angle":"good-topic","question":"This succeeds."},
  {"angle":"retry-topic","question":"This returns malformed JSON once."}
]
JSON
cd "$TMP" && bash "$INVESTIGATE" start --direction internal --topics "$TMP/retry.json" --run retry-a >/dev/null
poll_failed retry-a >/dev/null \
  && ok "malformed topic result fails visibly" || no "schema failure visibility"
RETRY_ROOT="$TMP/.factory/multi-model-workflow/investigate-runs/retry-a"
[ -f "$RETRY_ROOT/topics/000/validated.json" ] && [ ! -f "$RETRY_ROOT/synthesis/meta.json" ] \
  && ok "partial success persists without premature synthesis" || no "partial failure state"
rm -f "$RETRY_ROOT/topics/001/run.log"
cd "$TMP" && bash "$INVESTIGATE" resume --run retry-a >/dev/null
poll_completed retry-a >/dev/null \
  && ok "resume retries failed topic even when log is absent" || no "topic retry"
[ "$(grep -c 'retry-a/topics/000/prompt.md' "$DROID_TEST_LOG")" = 1 ] \
  && [ "$(grep -c 'retry-a/topics/001/prompt.md' "$DROID_TEST_LOG")" = 2 ] \
  && ok "validated topic is not rerun" || no "selective retry"
[ -f "$RETRY_ROOT/topics/001/attempts/001/result.json" ] \
  && [ "$(jq -r .attempt "$RETRY_ROOT/topics/001/meta.json")" = 2 ] \
  && ok "failed topic attempt is preserved" || no "topic retry audit trail"

cat >"$TMP/synth-retry.json" <<'JSON'
[{"angle":"synth-source","question":"Produce valid evidence."}]
JSON
export DROID_FAKE_SYNTH_FAIL_ONCE=1
cd "$TMP" && bash "$INVESTIGATE" start --direction internal --topics "$TMP/synth-retry.json" --run synth-retry >/dev/null
poll_failed synth-retry >/dev/null \
  && ok "malformed synthesis fails visibly" || no "synthesis failure visibility"
cd "$TMP" && bash "$INVESTIGATE" resume --run synth-retry >/dev/null
poll_completed synth-retry >/dev/null \
  && ok "failed synthesis can be rerun" || no "synthesis retry"
SYNTH_ROOT="$TMP/.factory/multi-model-workflow/investigate-runs/synth-retry/synthesis"
[ -f "$SYNTH_ROOT/attempts/001/result.json" ] \
  && [ "$(jq -r .validation_error "$SYNTH_ROOT/attempts/001/meta.json")" = "report result schema invalid" ] \
  && ok "failed synthesis attempt is preserved" || no "synthesis retry audit trail"
unset DROID_FAKE_SYNTH_FAIL_ONCE

exit "$fail"
