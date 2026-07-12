#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKER="$SCRIPT_DIR/../worker.sh"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
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
echo "$OUT" | grep -q 'run_in_background=true' && ok "background Task guidance" || no "background guidance"
echo "$OUT" | grep -q 'task-record' && ok "task id recording guidance" || no "task record guidance"

bash "$WORKER" task-record --worktree "$WT" --task-id task-123 >/dev/null
[ "$(jq -r .task_id "$WT/.factory/multi-model-workflow/worker-dispatch/meta.json")" = task-123 ] && ok "task id recorded" || no "task id"

INSTR="$TMP/instructions.md"
printf 'continue\n' > "$INSTR"
R="$(bash "$WORKER" resume --worktree "$WT" --instructions "$INSTR")"
echo "$R" | grep -q 'resume=task-123' && ok "resume uses task id" || no "resume id"

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
echo "$OUT2" | grep -q 'Droid 写计划派发' && ok "plan dispatch guidance" || no "plan dispatch"
META="$TASK_WT/.factory/multi-model-workflow/plan-workers/002/dispatch/meta.json"
[ "$(jq -r .droid "$META")" = plan-writer ] && ok "plan writer selected" || no "plan writer"
bash "$WORKER" task-record --worktree "$TASK_WT" --plan "$PLAN2" --task-id plan-456 >/dev/null
[ "$(jq -r .task_id "$META")" = plan-456 ] && ok "plan task id recorded" || no "plan task id"

mkdir -p "$(dirname "$PLAN2")"
printf '# generated\n' > "$PLAN2"
bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null &&
  ok "plan boundary accepts plan file" || no "plan boundary"
echo bad > "$TASK_WT/source.txt"
if bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "plan boundary must reject source"
else
  ok "plan boundary rejects source"
fi

exit "$fail"
