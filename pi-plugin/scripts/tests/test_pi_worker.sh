#!/usr/bin/env bash
# worker.sh(pi-subagents 原生)合同:dispatch 只准备不启动、verify 过边界门、
# plan 工人隔离沙箱 + 原子发布、resume 重置账本。测试自己扮演工人写产物。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKER="$SCRIPT_DIR/../worker.sh"
fail=0
ok() { echo "ok - $1"; }
no() { echo "not ok - $1"; fail=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 注册目录仿真:preflight 只认 $PI_CODING_AGENT_DIR/agents/<role>.md 存在
export PI_CODING_AGENT_DIR="$TMP/agentdir"
mkdir -p "$PI_CODING_AGENT_DIR/agents"

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
mkdir -p "$TMP/docs/design/prototype" "$TMP/docs/design/mockup" "$TMP/.pi/multi-model-workflow"
printf '# prototype log\n' >"$TMP/docs/design/prototype/README.md"
printf 'selected\n' >"$TMP/docs/design/prototype/selected.py"
printf 'rejected\n' >"$TMP/docs/design/prototype/rejected.py"
printf '<html>loser</html>\n' >"$TMP/docs/design/mockup/loser.html"
cat >"$TMP/.pi/multi-model-workflow/task.json" <<'JSON'
{"docs":{"design":"docs/design"},"prototype":{"status":"accepted","log":"docs/design/prototype/README.md","selected":["docs/design/prototype/selected.py"]},"approval":{"reports":["docs/design/prototype/README.md","docs/design/prototype/selected.py"],"fingerprint":"88b87bf4f460b9ff95c2a557d0ae73586a84bbe5"}}
JSON
git -C "$TMP" add docs
git -C "$TMP" commit -qm docs

WT="$TMP/.pi/worktrees/demo-plan-001"

# 未注册角色 fail-closed
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" >/dev/null 2>&1; then
  no "unregistered agent must fail dispatch"
else
  ok "unregistered agent fails dispatch closed"
fi
for role in pack-executor pack-executor-capable plan-writer; do
  : >"$PI_CODING_AGENT_DIR/agents/$role.md"
done

OUT="$(bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" 2>&1)"
META="$WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
ACTUAL_WT="$(jq -r .worktree "$META")"
[ "$(git -C "$ACTUAL_WT" branch --show-current)" = "worker/demo-plan-001" ] && ok "worker branch" || no "worker branch"
[ -f "$WT/.pi/multi-model-workflow/worker-dispatch/prompt.md" ] && ok "worker prompt package" || no "worker prompt"
[ "$(jq -r .agent "$META")" = pack-executor ] && ok "pack executor selected" || no "executor"
[ "$(jq -r .status "$META")" = dispatched ] && ok "meta status dispatched" || no "meta status"
echo "$OUT" | grep -q 'WORKER_BACKEND=pi-subagents' && ok "pi-subagents backend" || no "backend banner"
echo "$OUT" | grep -q 'agent:"pack-executor"' && ok "dispatch instruction names agent" || no "dispatch instruction"
echo "$OUT" | grep -q 'async:true' && ok "dispatch instruction runs in background" || no "dispatch background"
echo "$OUT" | grep -q 'note-run-id' && ok "dispatch requires run id ledger" || no "run id ledger pointer"
echo "$OUT" | grep -q 'mmw worker verify' && ok "dispatch points to verify gate" || no "verify pointer"
grep -q "$ACTUAL_WT" "$WT/.pi/multi-model-workflow/worker-dispatch/prompt.md" \
  && ok "prompt pins absolute worktree path" || no "prompt worktree pin"
BUILD_PROMPT="$WT/.pi/multi-model-workflow/worker-dispatch/prompt.md"
grep -q 'prototype/README.md' "$BUILD_PROMPT" && grep -q 'prototype/selected.py' "$BUILD_PROMPT" \
  && ! grep -q 'prototype/rejected.py' "$BUILD_PROMPT" && ! grep -q 'mockup/loser.html' "$BUILD_PROMPT" \
  && ok "build worker 只收到 accepted log + selected" || no "build worker prototype 选中材料"

TASK_JSON="$TMP/.pi/multi-model-workflow/task.json"; cp "$TASK_JSON" "$TMP/task-backup.json"
mv "$TMP/docs/design/prototype/selected.py" "$TMP/docs/design/prototype/selected.tmp"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-missing" >/dev/null 2>&1; then no "missing selected"; else ok "missing selected fails closed"; fi
mv "$TMP/docs/design/prototype/selected.tmp" "$TMP/docs/design/prototype/selected.py"
mkdir -p "$TMP/outside-evidence"; ln -s "$TMP/outside-evidence" "$TMP/docs/design/evidence"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-symlink" >/dev/null 2>&1; then no "symlink evidence"; else ok "symlink evidence fails closed"; fi
rm "$TMP/docs/design/evidence"
mv "$TMP/docs/design/prototype" "$TMP/docs/design/prototype.saved"; mv "$TMP/docs/design/mockup" "$TMP/docs/design/mockup.saved"
jq '.scenario="develop" | .prototype=null' "$TMP/task-backup.json" >"$TASK_JSON"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-empty" >/dev/null 2>&1; then no "develop empty prototype"; else ok "develop empty prototype fails closed"; fi
mv "$TMP/docs/design/prototype.saved" "$TMP/docs/design/prototype"; mv "$TMP/docs/design/mockup.saved" "$TMP/docs/design/mockup"
jq '.prototype=null' "$TMP/task-backup.json" >"$TASK_JSON"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-old" >/dev/null 2>&1; then no "old untracked prototype"; else ok "old untracked prototype fails closed"; fi
cp "$TMP/task-backup.json" "$TASK_JSON"
jq '.approval=null' "$TMP/task-backup.json" >"$TASK_JSON"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-unapproved" >/dev/null 2>&1; then no "unapproved accepted"; else ok "unapproved accepted fails closed"; fi
printf B >"$TMP/docs/design/prototype/b.py"; jq '.prototype.selected=["docs/design/prototype/b.py"]' "$TMP/task-backup.json" >"$TASK_JSON"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-unapproved-selected" >/dev/null 2>&1; then no "unapproved selected"; else ok "unapproved selected fails closed"; fi
rm "$TMP/docs/design/prototype/b.py"; cp "$TMP/task-backup.json" "$TASK_JSON"
jq '.approval={reports:["docs/design/prototype/README.md","docs/design/prototype/selected.py"],fingerprint:"stale"}' "$TMP/task-backup.json" >"$TASK_JSON"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$TMP/.pi/worktrees/guard-stale" >/dev/null 2>&1; then no "stale approval"; else ok "stale approval fails closed"; fi
cp "$TMP/task-backup.json" "$TASK_JSON"

# 未验收(可能在飞)禁止重派
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" >/dev/null 2>&1; then
  no "pending worker must not be duplicated"
else
  ok "duplicate dispatch while pending fails closed"
fi

# 首派后 selected 改动时，resume 与最终 verify 都必须回源任务 fail-closed。
GUARD_INSTR="$TMP/guard-instructions.md"; printf 'guard\n' >"$GUARD_INSTR"
printf 'changed\n' >>"$TMP/docs/design/prototype/selected.py"
if bash "$WORKER" resume --worktree "$WT" --instructions "$GUARD_INSTR" >/dev/null 2>&1; then no "stale resume"; else ok "stale resume checks task origin"; fi
if bash "$WORKER" verify --worktree "$WT" >/dev/null 2>&1; then no "stale verify"; else ok "stale verify checks task origin"; fi
printf 'selected\n' >"$TMP/docs/design/prototype/selected.py"

# 工人干净收工 → verify 过门并记 verified
V="$(bash "$WORKER" verify --worktree "$WT")"
echo "$V" | grep -q 'WORKER_VERIFY=pass' && ok "verify passes clean docs boundary" || no "verify pass"
[ "$(jq -r .status "$META")" = verified ] && ok "verify marks ledger" || no "verify ledger"

# verified 后再 dispatch 仍 fail-closed(补改走 resume)
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$WT" >/dev/null 2>&1; then
  no "verified worker must not be redispatched"
else
  ok "redispatch after verify fails closed"
fi

# resume 重置账本并给出续接指令
INSTR="$TMP/instructions.md"
printf 'continue\n' > "$INSTR"
R="$(bash "$WORKER" resume --worktree "$WT" --instructions "$INSTR")"
echo "$R" | grep -q '账本无 run id' && ok "resume without ledger run id falls back to redispatch" || no "resume fallback"
echo "$R" | grep -q 'agent:"pack-executor"' && ok "resume redispatch names agent" || no "resume redispatch"
bash "$WORKER" note-run-id --worktree "$WT" --id run-123 >/dev/null
[ "$(jq -r .run_id "$META")" = run-123 ] && ok "note-run-id writes ledger" || no "note-run-id ledger"
R2="$(bash "$WORKER" resume --worktree "$WT" --instructions "$INSTR")"
echo "$R2" | grep -q 'action:"resume", id:"run-123"' && ok "resume offers durable continuation" || no "resume instruction"
[ "$(jq -r .status "$META")" = dispatched ] && ok "resume resets ledger to dispatched" || no "resume ledger"
[ -f "$WT/.pi/multi-model-workflow/worker-dispatch/resume-prompt.md" ] && ok "resume prompt package" || no "resume prompt"

# docs 红线 fail-closed
mkdir -p "$ACTUAL_WT/docs"
echo bad > "$ACTUAL_WT/docs/bad.md"
if bash "$WORKER" verify --worktree "$WT" >/dev/null 2>&1; then
  no "docs boundary must fail verify"
else
  ok "docs boundary fails verify closed"
fi
if bash "$WORKER" check-docs --worktree "$WT" >/dev/null 2>&1; then
  no "docs boundary must fail"
else
  ok "docs boundary fails closed"
fi
rm "$ACTUAL_WT/docs/bad.md"
bash "$WORKER" verify --worktree "$WT" >/dev/null

TASK_WT="$TMP/task-wt"
git -C "$TMP" worktree add -q -b task-wt "$TASK_WT" HEAD
mkdir -p "$TASK_WT/.pi/multi-model-workflow"
cat >"$TASK_WT/.pi/multi-model-workflow/task.json" <<'JSON'
{"docs":{"design":"docs/design"},"prototype":{"status":"accepted","log":"docs/design/prototype/README.md","selected":["docs/design/prototype/selected.py"]},"approval":{"reports":["docs/design/prototype/README.md","docs/design/prototype/selected.py"],"fingerprint":"88b87bf4f460b9ff95c2a557d0ae73586a84bbe5"}}
JSON
PLAN2="$TASK_WT/docs/plans/new-demo/002.md"
printf '\n## Cross-Plan Contract Anchors\n- shared contract\n' >>"$TASK_WT/docs/design/demo.md"
OUT2="$(bash "$WORKER" plan-dispatch --plan "$PLAN2" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$TASK_WT/docs/issues/demo/001.md")"
echo "$OUT2" | grep -q 'agent:"plan-writer"' && ok "plan writer dispatch instruction" || no "plan dispatch"
META="$TASK_WT/.pi/multi-model-workflow/plan-workers/002/dispatch/meta.json"
[ "$(jq -r .agent "$META")" = plan-writer ] && ok "plan writer selected" || no "plan writer"
[ -d "$(dirname "$(jq -r .plan "$META")")" ] \
  && ok "plan writer target directory exists before launch" || no "plan writer target directory"
PLAN_PROMPT="$TASK_WT/.pi/multi-model-workflow/plan-workers/002/dispatch/prompt.md"
grep -q 'prototype/README.md' "$PLAN_PROMPT" && grep -q 'prototype/selected.py' "$PLAN_PROMPT" \
  && ! grep -q 'prototype/rejected.py' "$PLAN_PROMPT" && ! grep -q 'mockup/loser.html' "$PLAN_PROMPT" \
  && ok "plan writer 只收到 accepted log + selected" || no "plan writer prototype 选中材料"

PLAN3="$TASK_WT/docs/plans/demo/003.md"
ISSUE3="$TASK_WT/docs/issues/demo/003.md"
printf '# issue 3\n\n## Small issues\n<!-- PENDING -->\n' >"$ISSUE3"
bash "$WORKER" plan-dispatch --plan "$PLAN3" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$ISSUE3" >/dev/null

SANDBOX2="$(jq -r .worktree "$META")"
META3="$TASK_WT/.pi/multi-model-workflow/plan-workers/003/dispatch/meta.json"
SANDBOX3="$(jq -r .worktree "$META3")"
# 测试扮演两个 plan writer:各自在隔离沙箱写 plan + issue 小节
printf '# generated\n' >"$(jq -r .plan "$META")"
printf '# issue\n\n## Small issues\n- child issue\n' >"$(jq -r .issue "$META")"
printf '# generated 3\n' >"$(jq -r .plan "$META3")"
printf '# issue 3\n\n## Small issues\n- child 3\n' >"$(jq -r .issue "$META3")"
SANDBOX_PLAN2="$(jq -r .plan "$META")"
if bash "$WORKER" verify --plan "$SANDBOX_PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "plan verify must reject sandbox target path"
else
  ok "plan verify rejects sandbox target path"
fi
[ ! -e "$PLAN2" ] && [ -d "$SANDBOX2" ] \
  && [ "$(jq -r .status "$META")" = dispatched ] && [ "$(jq -r '.published // false' "$META")" = false ] \
  && ok "rejected plan target preserves task and sandbox state" || no "rejected plan target state"
printf '# cross-writer overwrite\n' >"$SANDBOX2/docs/plans/demo/003.md"
if bash "$WORKER" verify --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "isolated writer must not touch another plan target"
else
  ok "isolated writer cannot modify another plan target"
fi
rm "$SANDBOX2/docs/plans/demo/003.md"
printf '\ncoordinator concurrent change\n' >>"$TASK_WT/docs/issues/demo/001.md"
if bash "$WORKER" verify --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "plan publish must not overwrite concurrent coordinator target changes"
else
  ok "plan publish conflict fails closed"
fi
git -C "$TASK_WT" checkout -- docs/issues/demo/001.md

bash "$WORKER" verify --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null \
  && ok "plan writer verify publishes" || no "plan writer verify"
bash "$WORKER" verify --plan "$PLAN3" --worktree "$TASK_WT" >/dev/null \
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
rm "$PLAN2"
PLAN_RESUME="$(bash "$WORKER" plan-resume --plan "$PLAN2" --worktree "$TASK_WT" --instructions "$PLAN_INSTR")"
RESUME_SANDBOX="$(jq -r .worktree "$META")"
echo "$PLAN_RESUME" | grep -q 'agent:"plan-writer"' && [ -d "$RESUME_SANDBOX" ] \
  && ok "plan resume recreates isolated worktree" || no "plan resume isolation"
[ -d "$(dirname "$(jq -r .plan "$META")")" ] \
  && ok "plan resume target directory exists before launch" || no "plan resume target directory"
printf '# generated\n' >"$(jq -r .plan "$META")"
printf '# issue\n\n## Small issues\n- child issue\n' >"$(jq -r .issue "$META")"
bash "$WORKER" verify --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null
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
bash "$WORKER" dispatch --plan "$CAPABLE_PLAN" --worktree "$CAPABLE_WT" \
  --design "$DESIGN" --issue "$ISSUE" >/dev/null
CAPABLE_META="$CAPABLE_WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
[ "$(jq -r .agent "$CAPABLE_META")" = pack-executor-capable ] \
  && ok "capable plan selects higher executor" || no "capable executor routing"

# 显式 --agent 覆盖(取代旧 --model/--effort:模型与档位由注册角色 frontmatter 决定)
OVERRIDE_WT="$TMP/.pi/worktrees/demo-plan-override"
if OVERRIDE_OUT="$(bash "$WORKER" dispatch --plan "$PLAN" --worktree "$OVERRIDE_WT" \
  --design "$DESIGN" --issue "$ISSUE" --agent pack-executor-capable)"; then
  echo "$OVERRIDE_OUT" | grep -q 'agent:"pack-executor-capable"' \
    && ok "explicit agent override reaches dispatch" || no "agent override"
else
  no "agent override dispatch"
fi

MERGE_PLAN="$TMP/merge-mini.md"
MERGE_WT="$TMP/.pi/worktrees/merge-fix"
printf '# merge conflict mini-plan\n' >"$MERGE_PLAN"
MERGE_OUT="$(bash "$WORKER" dispatch --mode merge --plan "$MERGE_PLAN" --worktree "$MERGE_WT")"
MERGE_META="$MERGE_WT/.pi/multi-model-workflow/worker-dispatch/meta.json"
echo "$MERGE_OUT" | grep -q 'agent:"pack-executor"' \
  && [ "$(jq -r .mode "$MERGE_META")" = merge ] \
  && grep -q '合并冲突 mini-plan' "$MERGE_WT/.pi/multi-model-workflow/worker-dispatch/prompt.md" \
  && ok "merge mini-plan dispatch needs no design or issue" || no "merge worker mode"

exit "$fail"
