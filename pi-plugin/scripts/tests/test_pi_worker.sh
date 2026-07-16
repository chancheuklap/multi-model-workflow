#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKER="$SCRIPT_DIR/../worker.sh"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat >"$TMP/bin/pi" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf 'cwd=%q ' "$PWD" >>"$PI_TEST_LOG"
printf '%q ' "$@" >>"$PI_TEST_LOG"
printf '\n' >>"$PI_TEST_LOG"
session=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --session-id) session="$2"; shift 2 ;;
    --model|--thinking|--append-system-prompt|-t) shift 2 ;;
    *) shift ;;
  esac
done
[ -n "$session" ] || exit 3
sleep 0.05
if [ "${PI_FAKE_FAIL:-0}" = 1 ]; then
  echo 'fake failure' >&2
  exit 9
fi
printf '%s\n' 'fake complete'
SH
chmod +x "$TMP/bin/pi"
export PATH="$TMP/bin:$PATH"
export PI_TEST_LOG="$TMP/pi-invocations.log"

wait_status() {
  local wt="$1" plan="${2:-}" out i
  for i in $(seq 1 40); do
    if [ -n "$plan" ]; then
      out="$(bash "$WORKER" status --plan "$plan" --worktree "$wt" 2>/dev/null)" && {
        printf '%s\n' "$out"
        return 0
      }
    else
      out="$(bash "$WORKER" status --worktree "$wt" 2>/dev/null)" && {
        printf '%s\n' "$out"
        return 0
      }
    fi
    sleep 0.05
  done
  printf '%s\n' "$out"
  return 1
}

git -C "$TMP" init -q
git -C "$TMP" config user.email test@example.com
git -C "$TMP" config user.name Test
echo base > "$TMP/base.txt"
git -C "$TMP" add base.txt
git -C "$TMP" commit -qm base

mkdir -p "$TMP/docs/plans/demo" "$TMP/docs/issues/demo" "$TMP/docs/design"
PLAN="$TMP/docs/plans/demo/001.md"
ISSUE="$TMP/docs/issues/demo/001.md"
DESIGN="$TMP/docs/design/demo.md"
printf '# plan\n' > "$PLAN"
printf '# issue\n\n## Small issues\n<!-- PENDING -->\n' > "$ISSUE"
printf '# design\n' > "$DESIGN"
git -C "$TMP" add docs
git -C "$TMP" commit -qm docs

WT="$TMP/.pi/worktrees/demo-plan-001"
OUT="$(bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" 2>&1)"
META="$WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
ACTUAL_WT="$(jq -r .worktree "$META")"
[ "$(git -C "$ACTUAL_WT" branch --show-current)" = "worker/demo-plan-001" ] && ok "worker branch" || no "worker branch"
[ -f "$WT/.pi/multi-model-workflow/worker-dispatch/prompt.md" ] && ok "worker prompt package" || no "worker prompt"
[ "$(jq -r .agent "$META")" = pack-executor ] && ok "pack executor selected" || no "executor"
echo "$OUT" | grep -q 'WORKER_BACKEND=pi-exec' && ok "real pi exec backend" || no "pi exec backend"
STATUS="$(wait_status "$WT")"
echo "$STATUS" | grep -q 'WORKER_STATUS=COMPLETED' && ok "worker completes with durable status" || no "worker status"
SID="$(jq -r .session_id "$META")"
[ -n "$SID" ] && [ "$SID" != null ] && ok "session id captured" || no "session id"
grep -qF 'headless-agent prompt: placeholder, not injected' "$(jq -r .log_file "$META")" \
  && ok "GPT placeholder skip is logged" || no "placeholder skip log"
grep -Fq -- "cwd=$ACTUAL_WT" "$PI_TEST_LOG" \
  && ok "runtime executes inside worker worktree" || no "worker worktree cwd"
grep -Fq -- '--thinking high' "$PI_TEST_LOG" \
  && ok "worker reasoning effort reaches pi" || no "worker reasoning effort"
grep -Fq -- '-t read\,write\,edit\,bash\,grep\,find\,ls' "$PI_TEST_LOG" \
  && ok "worker runtime restricts tools by allowlist" || no "worker tool policy"
grep -Fq -- '--append-system-prompt' "$PI_TEST_LOG" \
  && ok "worker role system prompt connected" || no "worker role prompt"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" >/dev/null 2>&1; then
  no "completed worker must not be duplicated"
else
  ok "duplicate worker dispatch fails closed"
fi

INSTR="$TMP/instructions.md"
printf 'continue\n' > "$INSTR"
R="$(bash "$WORKER" resume --worktree "$WT" --instructions "$INSTR")"
echo "$R" | grep -q 'WORKER_STARTED' && ok "resume starts continuation" || no "resume start"
STATUS="$(wait_status "$WT")"
echo "$STATUS" | grep -q "SESSION_ID=$SID" && ok "resume preserves pi session" || no "resume session"
grep -Fq -- "--session-id $SID" "$PI_TEST_LOG" && ok "resume passes session id to pi" || no "runtime resume id"
grep -qF 'headless-agent prompt: placeholder, not injected' "$(jq -r .log_file "$META")" \
  && ok "resume preserves placeholder skip audit" || no "resume placeholder audit"

mkdir -p "$ACTUAL_WT/docs"
echo bad > "$ACTUAL_WT/docs/bad.md"
if bash "$WORKER" check-docs --worktree "$WT" >/dev/null 2>&1; then
  no "docs boundary must fail"
else
  ok "docs boundary fails closed"
fi
rm "$ACTUAL_WT/docs/bad.md"

TASK_WT="$TMP/task-wt"
git -C "$TMP" worktree add -q -b task-wt "$TASK_WT" HEAD
PLAN2="$TASK_WT/docs/plans/demo/002.md"
printf '\n## Cross-Plan Contract Anchors\n- shared contract\n' >>"$TASK_WT/docs/design/demo.md"
OUT2="$(bash "$WORKER" plan-dispatch --plan "$PLAN2" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$TASK_WT/docs/issues/demo/001.md")"
echo "$OUT2" | grep -q 'WORKER_STARTED' && ok "plan writer starts" || no "plan dispatch"
META="$TASK_WT/.pi/multi-model-workflow/plan-workers/002/dispatch/meta.json"
[ "$(jq -r .agent "$META")" = plan-writer ] && ok "plan writer selected" || no "plan writer"

PLAN3="$TASK_WT/docs/plans/demo/003.md"
ISSUE3="$TASK_WT/docs/issues/demo/003.md"
printf '# issue 3\n\n## Small issues\n<!-- PENDING -->\n' >"$ISSUE3"
bash "$WORKER" plan-dispatch --plan "$PLAN3" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$ISSUE3" >/dev/null

SANDBOX2="$(jq -r .worktree "$META")"
META3="$TASK_WT/.pi/multi-model-workflow/plan-workers/003/dispatch/meta.json"
SANDBOX3="$(jq -r .worktree "$META3")"
printf '# generated\n' >"$(jq -r .plan "$META")"
printf '# issue\n\n## Small issues\n- child issue\n' >"$(jq -r .issue "$META")"
printf '# generated 3\n' >"$(jq -r .plan "$META3")"
printf '# issue 3\n\n## Small issues\n- child 3\n' >"$(jq -r .issue "$META3")"
printf '# cross-writer overwrite\n' >"$SANDBOX2/docs/plans/demo/003.md"
if bash "$WORKER" status --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "isolated writer must not touch another plan target"
else
  ok "isolated writer cannot modify another plan target"
fi
rm "$SANDBOX2/docs/plans/demo/003.md"
printf '\ncoordinator concurrent change\n' >>"$TASK_WT/docs/issues/demo/001.md"
if bash "$WORKER" status --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "plan publish must not overwrite concurrent coordinator target changes"
else
  ok "plan publish conflict fails closed"
fi
git -C "$TASK_WT" checkout -- docs/issues/demo/001.md

PLAN_STATUS="$(wait_status "$TASK_WT" "$PLAN2")"
echo "$PLAN_STATUS" | grep -q 'WORKER_STATUS=COMPLETED' && ok "plan writer status" || no "plan writer status"
wait_status "$TASK_WT" "$PLAN3" >/dev/null \
  && ok "parallel plan writers publish from isolated worktrees" || no "parallel plan boundary"
[ ! -d "$SANDBOX2" ] && [ ! -d "$SANDBOX3" ] \
  && ok "plan writer sandboxes cleaned after publish" || no "plan sandbox cleanup"
grep -q '^# generated$' "$PLAN2" && grep -q '^# generated 3$' "$PLAN3" \
  && ok "isolated plans published to assigned targets" || no "plan publish"
grep -q 'child issue' "$TASK_WT/docs/issues/demo/001.md" \
  && grep -q 'child 3' "$ISSUE3" \
  && ok "only assigned issue results published" || no "issue publish"
grep -q 'shared contract' "$TASK_WT/docs/design/demo.md" \
  && ok "preexisting coordinator design edit preserved" || no "coordinator edit preservation"
bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null &&
  ok "published plan boundary remains verifiable" || no "plan boundary"
PLAN_INSTR="$TMP/plan-instructions.md"
printf 'tighten the existing plan\n' >"$PLAN_INSTR"
PLAN_RESUME="$(bash "$WORKER" plan-resume --plan "$PLAN2" --worktree "$TASK_WT" --instructions "$PLAN_INSTR")"
RESUME_SANDBOX="$(jq -r .worktree "$META")"
echo "$PLAN_RESUME" | grep -q 'WORKER_STARTED' && [ -d "$RESUME_SANDBOX" ] \
  && ok "plan resume recreates isolated worktree" || no "plan resume isolation"
wait_status "$TASK_WT" "$PLAN2" >/dev/null
[ ! -d "$RESUME_SANDBOX" ] && ok "plan resume republishes and cleans sandbox" || no "plan resume cleanup"
printf '# altered issue\n\n## Small issues\n- child issue\n' >"$TASK_WT/docs/issues/demo/001.md"
if bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "published issue drift must be rejected"
else
  ok "published issue drift is rejected"
fi
printf '# issue\n\n## Small issues\n- child issue\n' >"$TASK_WT/docs/issues/demo/001.md"

CAPABLE_PLAN="$TMP/docs/plans/demo/003.md"
printf '# Plan\nComplexity: capable\n' >"$CAPABLE_PLAN"
CAPABLE_WT="$TMP/.pi/worktrees/demo-plan-003"
CAPABLE_OUT="$(bash "$WORKER" dispatch --plan "$CAPABLE_PLAN" --worktree "$CAPABLE_WT" \
  --design "$DESIGN" --issue "$ISSUE")"
CAPABLE_META="$CAPABLE_WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .agent "$CAPABLE_META")" = pack-executor-capable ] \
  && ok "capable plan selects higher executor" || no "capable executor routing"
wait_status "$CAPABLE_WT" >/dev/null

OVERRIDE_WT="$TMP/.pi/worktrees/demo-plan-override"
bash "$WORKER" dispatch --plan "$PLAN" --worktree "$OVERRIDE_WT" --design "$DESIGN" --issue "$ISSUE" \
  --model test-model --effort high >/dev/null
OVERRIDE_META="$OVERRIDE_WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .model "$OVERRIDE_META")" = test-model ] \
  && [ "$(jq -r .reasoning_effort "$OVERRIDE_META")" = high ] \
  && ok "explicit model override reaches runtime" || no "model override"
wait_status "$OVERRIDE_WT" >/dev/null
grep -Fq -- '--model test-model --thinking high' "$PI_TEST_LOG" \
  && ok "override reaches pi exec arguments" || no "runtime model override"

MERGE_PLAN="$TMP/merge-mini.md"
MERGE_WT="$TMP/.pi/worktrees/merge-fix"
printf '# merge conflict mini-plan\n' >"$MERGE_PLAN"
MERGE_OUT="$(bash "$WORKER" dispatch --mode merge --plan "$MERGE_PLAN" --worktree "$MERGE_WT")"
MERGE_META="$MERGE_WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
echo "$MERGE_OUT" | grep -q 'WORKER_STARTED' \
  && [ "$(jq -r .mode "$MERGE_META")" = merge ] \
  && grep -q '合并冲突 mini-plan' "$MERGE_WT/.pi/multi-model-workflow/worker-dispatch/prompt.md" \
  && ok "merge mini-plan dispatch needs no design or issue" || no "merge worker mode"
wait_status "$MERGE_WT" >/dev/null

FAIL_WT="$TMP/.pi/worktrees/demo-plan-fail"
PI_FAKE_FAIL=1 bash "$WORKER" dispatch --plan "$PLAN" --worktree "$FAIL_WT" \
  --design "$DESIGN" --issue "$ISSUE" >/dev/null
sleep 0.1
if FAIL_STATUS="$(bash "$WORKER" status --worktree "$FAIL_WT" 2>&1)"; then
  no "failed pi result must fail status"
elif printf '%s\n' "$FAIL_STATUS" | grep -q 'WORKER_STATUS=FAILED'; then
  ok "failed pi result remains visible"
else
  no "failed pi result has no structured status"
fi
FAIL_META="$FAIL_WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
[ -n "$(jq -r '.session_id // empty' "$FAIL_META")" ] \
  && ok "failed execution keeps session id for explicit resume" || no "failed session id missing"

exit "$fail"
