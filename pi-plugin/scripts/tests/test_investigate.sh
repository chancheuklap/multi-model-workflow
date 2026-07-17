#!/usr/bin/env bash
# investigate.sh(pi-subagents 原生)合同:start 只准备并打印派发指令,工人回执经
# submit 交回过 schema 闸,status 备 synthesis / 汇编 result,resume 重派失败 job。
# 测试自己扮演工人生成回执 JSON。
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

git -C "$TMP" init -q
git -C "$TMP" config user.email test@example.com
git -C "$TMP" config user.name test
echo base >"$TMP/base.txt"
git -C "$TMP" add base.txt
git -C "$TMP" commit -qm base

# 扮演 topic 工人:带各种该被过滤的 finding
topic_payload() {  # $1=angle $2=mode
  local locator wrong_locator
  if [ "$2" = external ]; then
    locator="https://example.com/source"; wrong_locator="src/app.py:10"
  else
    locator="src/app.py:10"; wrong_locator="https://example.com/wrong-mode"
  fi
  jq -cn --arg angle "$1" --arg locator "$locator" --arg wrong "$wrong_locator" \
    '{topic:$angle,findings:[
        {claim:"verified",locator:$locator,confidence:"high"},
        {claim:"weak",locator:$locator,confidence:"low"},
        {claim:"missing locator",locator:"",confidence:"medium"},
        {claim:"blank locator",locator:"   ",confidence:"high"},
        {claim:"wrong mode locator",locator:$wrong,confidence:"high"}
      ],summary:"current state",gaps:["one gap"]}'
}
synth_payload() {
  jq -cn '{markdown:"# Investigation\n\nVerified evidence with `src/app.py:10`.",open_questions:["remaining gap"],spinoff_candidates:[{tag:"optimize",finding:"later cleanup"}]}'
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
printf '%s\n' "$START" | grep -q 'subagent_type=investigate-topic' \
  && ok "start prints dispatch instruction" || no "dispatch instruction"
printf '%s\n' "$START" | grep -q 'TOPIC=1 ANGLE=data-flow' \
  && ok "start lists per-topic prompt files" || no "topic listing"

ROOT="$TMP/.pi/multi-model-workflow/investigate-runs/internal-a"
[ -s "$ROOT/topics/000/prompt.md" ] && [ -s "$ROOT/topics/001/prompt.md" ] \
  && ok "topic prompts prepared" || no "topic prompts"
grep -q 'angle=module-boundary' "$ROOT/topics/000/prompt.md" \
  && ok "prompt carries topic angle" || no "prompt angle"

S="$(cd "$TMP" && bash "$INVESTIGATE" status --run internal-a)"
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=PENDING' \
  && ok "status pending before submits" || no "pending status"

topic_payload module-boundary internal >"$TMP/t0.json"
topic_payload data-flow internal >"$TMP/t1.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run internal-a --topic 0 --file "$TMP/t0.json" >/dev/null \
  && bash "$INVESTIGATE" submit --run internal-a --topic 1 --file "$TMP/t1.json" >/dev/null \
  && ok "topic submits validate" || no "topic submit"
[ "$(jq '.findings|length' "$ROOT/topics/000/validated.json")" = 1 ] \
  && [ "$(jq '.dropped|length' "$ROOT/topics/000/validated.json")" = 4 ] \
  && ok "weak, blank, and mode-mismatched evidence filtered" || no "evidence filtering"

S="$(cd "$TMP" && bash "$INVESTIGATE" status --run internal-a)"
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=SYNTHESIZING' \
  && printf '%s\n' "$S" | grep -q 'subagent_type=investigate-synthesizer' \
  && ok "all topics validated prepares synthesis dispatch" || no "synthesis prep"
[ "$(jq 'length' "$ROOT/synthesis/evidence.json")" = 2 ] \
  && ok "all topic evidence reaches synthesis" || no "evidence fan-in"
[ -s "$ROOT/synthesis/prompt.md" ] && ok "synthesis prompt prepared" || no "synthesis prompt"

synth_payload >"$TMP/synth.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run internal-a --synthesis --file "$TMP/synth.json" >/dev/null
S="$(cd "$TMP" && bash "$INVESTIGATE" status --run internal-a)"
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=COMPLETED' \
  && ok "synthesis submit completes run" || no "investigate completion"
RESULT="$(cd "$TMP" && bash "$INVESTIGATE" result --run internal-a)"
printf '%s\n' "$RESULT" | grep -q '^# Investigation' \
  && ok "completed report is readable" || no "report output"
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
(cd "$TMP" && bash "$INVESTIGATE" start \
  --direction internal --topics "$TMP/topics.json" --run concurrent-a >/dev/null 2>&1) &
p1=$!
(cd "$TMP" && bash "$INVESTIGATE" start \
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

cat >"$TMP/external.json" <<'JSON'
[{"angle":"library-practice","question":"What is established externally?"}]
JSON
cd "$TMP" && bash "$INVESTIGATE" start --direction external --topics "$TMP/external.json" --run external-a >/dev/null
topic_payload library-practice external >"$TMP/ext0.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run external-a --topic 0 --file "$TMP/ext0.json" >/dev/null
EXT_ROOT="$TMP/.pi/multi-model-workflow/investigate-runs/external-a"
[ "$(jq -r '.findings[0].locator' "$EXT_ROOT/topics/000/validated.json")" = "https://example.com/source" ] \
  && [ "$(jq '.dropped|length' "$EXT_ROOT/topics/000/validated.json")" = 4 ] \
  && ok "external locator must be URL" || no "external locator rule"

cat >"$TMP/both-invalid.json" <<'JSON'
[{"angle":"missing-mode","question":"Which direction?"}]
JSON
if cd "$TMP" && bash "$INVESTIGATE" start --direction both --topics "$TMP/both-invalid.json" --run both-invalid >/dev/null 2>&1; then
  no "both direction requires per-topic mode"
else
  ok "both direction validates topic mode"
fi

# 失败可见 + 选择性重派 + 审计留痕
cat >"$TMP/retry.json" <<'JSON'
[
  {"angle":"good-topic","question":"This succeeds."},
  {"angle":"retry-topic","question":"This returns malformed JSON once."}
]
JSON
cd "$TMP" && bash "$INVESTIGATE" start --direction internal --topics "$TMP/retry.json" --run retry-a >/dev/null
topic_payload good-topic internal >"$TMP/good.json"
printf 'not-json\n' >"$TMP/bad.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run retry-a --topic 0 --file "$TMP/good.json" >/dev/null
if cd "$TMP" && bash "$INVESTIGATE" submit --run retry-a --topic 1 --file "$TMP/bad.json" >/dev/null 2>&1; then
  no "malformed topic submit must fail"
else
  ok "malformed topic result fails visibly at submit"
fi
S="$(cd "$TMP" && bash "$INVESTIGATE" status --run retry-a 2>&1)" || true
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=FAILED' \
  && ok "failed topic keeps run failed" || no "schema failure visibility"
RETRY_ROOT="$TMP/.pi/multi-model-workflow/investigate-runs/retry-a"
[ -f "$RETRY_ROOT/topics/000/validated.json" ] && [ ! -f "$RETRY_ROOT/synthesis/meta.json" ] \
  && ok "partial success persists without premature synthesis" || no "partial failure state"
R="$(cd "$TMP" && bash "$INVESTIGATE" resume --run retry-a)"
printf '%s\n' "$R" | grep -q 'REDISPATCH=topic 1' \
  && ! printf '%s\n' "$R" | grep -q 'REDISPATCH=topic 0' \
  && ok "validated topic is not redispatched" || no "selective retry"
topic_payload retry-topic internal >"$TMP/retry-good.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run retry-a --topic 1 --file "$TMP/retry-good.json" >/dev/null
S="$(cd "$TMP" && bash "$INVESTIGATE" status --run retry-a)"
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=SYNTHESIZING' \
  && ok "resume + resubmit reaches synthesis" || no "topic retry"
[ -f "$RETRY_ROOT/topics/001/attempts/001/result.json" ] \
  && [ "$(jq -r .attempt "$RETRY_ROOT/topics/001/meta.json")" = 2 ] \
  && ok "failed topic attempt is preserved" || no "topic retry audit trail"

# synthesis 失败一次 → resume 重派 → 补交完成
printf 'not-json\n' >"$TMP/synth-bad.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run retry-a --synthesis --file "$TMP/synth-bad.json" >/dev/null
S="$(cd "$TMP" && bash "$INVESTIGATE" status --run retry-a 2>&1)" || true
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=FAILED synthesis' \
  && ok "malformed synthesis fails visibly" || no "synthesis failure visibility"
R="$(cd "$TMP" && bash "$INVESTIGATE" resume --run retry-a)"
printf '%s\n' "$R" | grep -q 'REDISPATCH=synthesis' \
  && ok "failed synthesis can be redispatched" || no "synthesis retry"
synth_payload >"$TMP/synth-good.json"
cd "$TMP" && bash "$INVESTIGATE" submit --run retry-a --synthesis --file "$TMP/synth-good.json" >/dev/null
S="$(cd "$TMP" && bash "$INVESTIGATE" status --run retry-a)"
printf '%s\n' "$S" | grep -q 'INVESTIGATE_STATUS=COMPLETED' \
  && ok "synthesis retry completes run" || no "synthesis retry completion"
SYNTH_ROOT="$RETRY_ROOT/synthesis"
[ -f "$SYNTH_ROOT/attempts/001/result.json" ] \
  && [ "$(jq -r .validation_error "$SYNTH_ROOT/attempts/001/meta.json")" = "report result schema invalid" ] \
  && ok "failed synthesis attempt is preserved" || no "synthesis retry audit trail"

exit "$fail"
