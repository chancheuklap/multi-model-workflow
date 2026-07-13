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
cat >"$TMP/bin/droid" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
printf '%q ' "$@" >>"$DROID_TEST_LOG"
printf '\n' >>"$DROID_TEST_LOG"
session=""
list_tools=0
native_branch=""
native_root=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --session-id) session="$2"; shift 2 ;;
    --list-tools) list_tools=1; shift ;;
    --worktree) native_branch="$2"; shift 2 ;;
    --worktree-dir) native_root="$2"; shift 2 ;;
    --cwd|--model|--reasoning-effort|--append-system-prompt-file|--file|--output-format|--auto|--disabled-tools) shift 2 ;;
    exec) shift ;;
    *) shift ;;
  esac
done
if [ "$list_tools" = 1 ]; then
  jq -cn '[
    {id:"read-cli"},{id:"create-cli"},{id:"edit-cli"},{id:"apply-patch-cli"},
    {id:"execute-cli"},{id:"grep_tool_cli"},{id:"glob-search-cli"},{id:"ls-cli"},
    {id:"skill"},{id:"task-cli"},{id:"web_search"},{id:"fetch_url"},{id:"start-mission-run"}
  ]'
  exit 0
fi
[ -z "$native_branch" ] || {
  actual="$native_root/$(basename "$PWD")-wt-${native_branch//\//-}"
  [ -d "$actual" ] || git worktree add -q "$actual" "$native_branch"
}
[ -n "$session" ] || session="session-test"
sleep 0.05
if [ "${DROID_FAKE_FAIL:-0}" = 1 ]; then
  printf '{"type":"result","subtype":"error","is_error":true,"result":"fake failure","session_id":"%s"}\n' "$session"
  exit 0
fi
printf '{"type":"result","subtype":"success","is_error":false,"result":"fake complete","session_id":"%s"}\n' "$session"
SH
chmod +x "$TMP/bin/droid"
export PATH="$TMP/bin:$PATH"
export DROID_TEST_LOG="$TMP/droid-invocations.log"

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

WT="$TMP/.factory/worktrees/demo-plan-001"
OUT="$(bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" 2>&1)"
META="$WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
ACTUAL_WT="$(jq -r .worktree "$META")"
[ "$(git -C "$ACTUAL_WT" branch --show-current)" = "worker/demo-plan-001" ] && ok "worker branch" || no "worker branch"
[ -f "$WT/.factory/multi-model-workflow/worker-dispatch/prompt.md" ] && ok "worker prompt package" || no "worker prompt"
[ "$(jq -r .droid "$META")" = pack-executor ] && ok "pack executor selected" || no "executor"
echo "$OUT" | grep -q 'WORKER_BACKEND=droid-exec' && ok "real Droid exec backend" || no "Droid exec backend"
STATUS="$(wait_status "$WT")"
echo "$STATUS" | grep -q 'WORKER_STATUS=COMPLETED' && ok "worker completes with durable status" || no "worker status"
[ "$(jq -r .session_id "$META")" = session-test ] && ok "session id captured" || no "session id"
grep -Fq -- "--worktree worker/demo-plan-001 --worktree-dir $WT" "$DROID_TEST_LOG" \
  && ok "runtime uses Droid native worktree" || no "native worker worktree"
if grep -F -- "--worktree worker/demo-plan-001" "$DROID_TEST_LOG" | grep -Fq -- '--auto medium'; then
  ok "worker uses development autonomy"
else
  no "worker autonomy"
fi
if grep -F -- "--worktree worker/demo-plan-001" "$DROID_TEST_LOG" | grep -Eq -- '--disabled-tools [^ ]*(task-cli|web_search)'; then
  ok "worker runtime restricts unrelated tools"
else
  no "worker tool policy"
fi
if grep -F -- "--worktree worker/demo-plan-001" "$DROID_TEST_LOG" | grep -F -- '--disabled-tools' | grep -Fq 'skill'; then
  no "worker disabled required Skill tool"
else
  ok "worker retains required Skill tool"
fi
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
echo "$STATUS" | grep -q 'SESSION_ID=session-test' && ok "resume preserves Droid session" || no "resume session"
grep -Fq -- '--session-id session-test' "$DROID_TEST_LOG" && ok "resume passes session id to Droid" || no "runtime resume id"

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
META="$TASK_WT/.factory/multi-model-workflow/plan-workers/002/dispatch/meta.json"
[ "$(jq -r .droid "$META")" = plan-writer ] && ok "plan writer selected" || no "plan writer"

PLAN3="$TASK_WT/docs/plans/demo/003.md"
ISSUE3="$TASK_WT/docs/issues/demo/003.md"
printf '# issue 3\n\n## Small issues\n<!-- PENDING -->\n' >"$ISSUE3"
bash "$WORKER" plan-dispatch --plan "$PLAN3" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$ISSUE3" >/dev/null

SANDBOX2="$(jq -r .worktree "$META")"
META3="$TASK_WT/.factory/multi-model-workflow/plan-workers/003/dispatch/meta.json"
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
CAPABLE_WT="$TMP/.factory/worktrees/demo-plan-003"
CAPABLE_OUT="$(bash "$WORKER" dispatch --plan "$CAPABLE_PLAN" --worktree "$CAPABLE_WT" \
  --design "$DESIGN" --issue "$ISSUE")"
CAPABLE_META="$CAPABLE_WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .droid "$CAPABLE_META")" = pack-executor-capable ] \
  && ok "capable plan selects higher executor" || no "capable executor routing"
wait_status "$CAPABLE_WT" >/dev/null

OVERRIDE_WT="$TMP/.factory/worktrees/demo-plan-override"
bash "$WORKER" dispatch --plan "$PLAN" --worktree "$OVERRIDE_WT" --design "$DESIGN" --issue "$ISSUE" \
  --model test-model --effort high >/dev/null
OVERRIDE_META="$OVERRIDE_WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .model "$OVERRIDE_META")" = test-model ] \
  && [ "$(jq -r .reasoning_effort "$OVERRIDE_META")" = high ] \
  && ok "explicit model override reaches runtime" || no "model override"
wait_status "$OVERRIDE_WT" >/dev/null
grep -Fq -- '--model test-model --reasoning-effort high' "$DROID_TEST_LOG" \
  && ok "override reaches Droid exec arguments" || no "runtime model override"

MERGE_PLAN="$TMP/merge-mini.md"
MERGE_WT="$TMP/.factory/worktrees/merge-fix"
printf '# merge conflict mini-plan\n' >"$MERGE_PLAN"
MERGE_OUT="$(bash "$WORKER" dispatch --mode merge --plan "$MERGE_PLAN" --worktree "$MERGE_WT")"
MERGE_META="$MERGE_WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
echo "$MERGE_OUT" | grep -q 'WORKER_STARTED' \
  && [ "$(jq -r .mode "$MERGE_META")" = merge ] \
  && grep -q '合并冲突 mini-plan' "$MERGE_WT/.factory/multi-model-workflow/worker-dispatch/prompt.md" \
  && ok "merge mini-plan dispatch needs no design or issue" || no "merge worker mode"
wait_status "$MERGE_WT" >/dev/null

FAIL_WT="$TMP/.factory/worktrees/demo-plan-fail"
DROID_FAKE_FAIL=1 bash "$WORKER" dispatch --plan "$PLAN" --worktree "$FAIL_WT" \
  --design "$DESIGN" --issue "$ISSUE" >/dev/null
sleep 0.1
if FAIL_STATUS="$(bash "$WORKER" status --worktree "$FAIL_WT" 2>&1)"; then
  no "failed Droid result must fail status"
elif printf '%s\n' "$FAIL_STATUS" | grep -q 'WORKER_STATUS=FAILED'; then
  ok "failed Droid result remains visible"
else
  no "failed Droid result has no structured status"
fi
FAIL_META="$FAIL_WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r '.session_id // empty' "$FAIL_META")" = "" ] \
  && ok "failed execution session is not resumable" || no "failed session leaked into resume ledger"

exit "$fail"
