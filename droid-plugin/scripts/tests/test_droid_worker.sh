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
while [ "$#" -gt 0 ]; do
  case "$1" in
    --session-id) session="$2"; shift 2 ;;
    --cwd|--model|--reasoning-effort|--append-system-prompt-file|--file|--output-format|--auto) shift 2 ;;
    exec) shift ;;
    *) shift ;;
  esac
done
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

mkdir -p "$TMP/docs/plans/demo" "$TMP/docs/issues/demo"
PLAN="$TMP/docs/plans/demo/001.md"
ISSUE="$TMP/docs/issues/demo/001.md"
printf '# plan\n' > "$PLAN"
printf '# issue\n' > "$ISSUE"
git -C "$TMP" add docs
git -C "$TMP" commit -qm docs

WT="$TMP/.factory/worktrees/demo-plan-001"
OUT="$(bash "$WORKER" dispatch --plan "$PLAN" --issue "$ISSUE" --worktree "$WT" 2>&1)"
[ "$(git -C "$WT" branch --show-current)" = "worker/demo-plan-001" ] && ok "worker branch" || no "worker branch"
[ -f "$WT/.factory/multi-model-workflow/worker-dispatch/prompt.md" ] && ok "worker prompt package" || no "worker prompt"
[ "$(jq -r .droid "$WT/.factory/multi-model-workflow/worker-dispatch/meta.json")" = pack-executor ] && ok "pack executor selected" || no "executor"
echo "$OUT" | grep -q 'WORKER_BACKEND=droid-exec' && ok "real Droid exec backend" || no "Droid exec backend"
STATUS="$(wait_status "$WT")"
echo "$STATUS" | grep -q 'WORKER_STATUS=COMPLETED' && ok "worker completes with durable status" || no "worker status"
[ "$(jq -r .session_id "$WT/.factory/multi-model-workflow/worker-dispatch/meta.json")" = session-test ] && ok "session id captured" || no "session id"
grep -Fq -- "--cwd $WT" "$DROID_TEST_LOG" && ok "runtime cwd bound to worker worktree" || no "worker cwd"
if bash "$WORKER" dispatch --plan "$PLAN" --issue "$ISSUE" --worktree "$WT" >/dev/null 2>&1; then
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

mkdir -p "$WT/docs"
echo bad > "$WT/docs/bad.md"
if bash "$WORKER" check-docs --worktree "$WT" >/dev/null 2>&1; then
  no "docs boundary must fail"
else
  ok "docs boundary fails closed"
fi
rm "$WT/docs/bad.md"

TASK_WT="$TMP/task-wt"
git -C "$TMP" worktree add -q -b task-wt "$TASK_WT" HEAD
PLAN2="$TASK_WT/docs/plans/demo/002.md"
OUT2="$(bash "$WORKER" plan-dispatch --plan "$PLAN2" --worktree "$TASK_WT" --issue "$TASK_WT/docs/issues/demo/001.md")"
echo "$OUT2" | grep -q 'WORKER_STARTED' && ok "plan writer starts" || no "plan dispatch"
META="$TASK_WT/.factory/multi-model-workflow/plan-workers/002/dispatch/meta.json"
[ "$(jq -r .droid "$META")" = plan-writer ] && ok "plan writer selected" || no "plan writer"

mkdir -p "$(dirname "$PLAN2")"
printf '# generated\n' > "$PLAN2"
PLAN_STATUS="$(wait_status "$TASK_WT" "$PLAN2")"
echo "$PLAN_STATUS" | grep -q 'WORKER_STATUS=COMPLETED' && ok "plan writer status" || no "plan writer status"
bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null &&
  ok "plan boundary accepts plan file" || no "plan boundary"
echo bad > "$TASK_WT/source.txt"
if bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "plan boundary must reject source"
else
  ok "plan boundary rejects source"
fi

CAPABLE_PLAN="$TMP/docs/plans/demo/003.md"
printf '# Plan\nComplexity: capable\n' >"$CAPABLE_PLAN"
CAPABLE_WT="$TMP/.factory/worktrees/demo-plan-003"
CAPABLE_OUT="$(bash "$WORKER" dispatch --plan "$CAPABLE_PLAN" --worktree "$CAPABLE_WT")"
CAPABLE_META="$CAPABLE_WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .droid "$CAPABLE_META")" = pack-executor-capable ] \
  && [ "$(jq -r .model "$CAPABLE_META")" = gemini-3.1-pro-preview ] \
  && ok "capable plan selects higher executor" || no "capable executor routing"
wait_status "$CAPABLE_WT" >/dev/null
grep -Fq -- '--model gemini-3.1-pro-preview' "$DROID_TEST_LOG" \
  && ok "capable model reaches Droid exec" || no "capable runtime model"

OVERRIDE_WT="$TMP/.factory/worktrees/demo-plan-override"
bash "$WORKER" dispatch --plan "$PLAN" --worktree "$OVERRIDE_WT" --model gpt-5.6-sol --effort high >/dev/null
OVERRIDE_META="$OVERRIDE_WT/.factory/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .model "$OVERRIDE_META")" = gpt-5.6-sol ] \
  && [ "$(jq -r .reasoning_effort "$OVERRIDE_META")" = high ] \
  && ok "explicit model override reaches runtime" || no "model override"
wait_status "$OVERRIDE_WT" >/dev/null
grep -Fq -- '--model gpt-5.6-sol --reasoning-effort high' "$DROID_TEST_LOG" \
  && ok "override reaches Droid exec arguments" || no "runtime model override"

FAIL_WT="$TMP/.factory/worktrees/demo-plan-fail"
DROID_FAKE_FAIL=1 bash "$WORKER" dispatch --plan "$PLAN" --worktree "$FAIL_WT" >/dev/null
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
