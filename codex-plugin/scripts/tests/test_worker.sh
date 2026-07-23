#!/usr/bin/env bash
# Codex native worker contract: scripts prepare boundaries and prompts; native
# subagents do the reasoning and writing.
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
printf 'base\n' >"$TMP/base.txt"
git -C "$TMP" add base.txt
git -C "$TMP" commit -qm base

NOMAN="$TMP/no-manifest"
mkdir -p "$NOMAN/docs/plans/demo" "$NOMAN/docs/issues/demo" "$NOMAN/docs/design"
git -C "$NOMAN" init -q
git -C "$NOMAN" config user.email test@example.com
git -C "$NOMAN" config user.name Test
printf '# plan\n' >"$NOMAN/docs/plans/demo/001.md"
printf '# issue\n\n## Small issues\n<!-- PENDING -->\n' >"$NOMAN/docs/issues/demo/001.md"
printf '# design\n' >"$NOMAN/docs/design/demo.md"
git -C "$NOMAN" add docs
git -C "$NOMAN" commit -qm docs
NOMAN_WT_COUNT="$(git -C "$NOMAN" worktree list --porcelain | grep -c '^worktree ')"
if bash "$WORKER" dispatch \
  --plan "$NOMAN/docs/plans/demo/001.md" \
  --design "$NOMAN/docs/design/demo.md" \
  --issue "$NOMAN/docs/issues/demo/001.md" \
  --worktree "$NOMAN/.codex/worktrees/build" >/dev/null 2>&1; then
  no "build dispatch without task manifest must fail"
elif [ "$(git -C "$NOMAN" worktree list --porcelain | grep -c '^worktree ')" = "$NOMAN_WT_COUNT" ]; then
  ok "missing manifest blocks build before inner worktree creation"
else
  no "missing manifest build changed worktree state"
fi
if bash "$WORKER" plan-dispatch \
  --plan "$NOMAN/docs/plans/demo/002.md" \
  --worktree "$NOMAN" \
  --design "$NOMAN/docs/design/demo.md" \
  --issue "$NOMAN/docs/issues/demo/001.md" >/dev/null 2>&1; then
  no "plan dispatch without task manifest must fail"
elif [ "$(git -C "$NOMAN" worktree list --porcelain | grep -c '^worktree ')" = "$NOMAN_WT_COUNT" ]; then
  ok "missing manifest blocks plan before sandbox creation"
else
  no "missing manifest plan changed worktree state"
fi

mkdir -p "$TMP/docs/plans/demo" "$TMP/docs/issues/demo" "$TMP/docs/design/prototype"
PLAN="$TMP/docs/plans/demo/001.md"
ISSUE="$TMP/docs/issues/demo/001.md"
DESIGN="$TMP/docs/design/demo.md"
printf '# plan\n' >"$PLAN"
printf '# issue\n\n## Small issues\n<!-- PENDING -->\n' >"$ISSUE"
printf '# design\n' >"$DESIGN"
printf '# accepted iterations\n' >"$TMP/docs/design/prototype/README.md"
printf 'selected\n' >"$TMP/docs/design/prototype/selected.py"
printf 'rejected\n' >"$TMP/docs/design/prototype/rejected.py"
mkdir -p "$TMP/.codex/multi-model-workflow"
cat >"$TMP/.codex/multi-model-workflow/task.json" <<'JSON'
{"docs":{"design":"docs/design"},"prototype":{"status":"accepted","log":"docs/design/prototype/README.md","selected":["docs/design/prototype/selected.py"]},"approval":{"reports":["docs/design/prototype/README.md","docs/design/prototype/selected.py"],"fingerprint":"PENDING"}}
JSON
FP="$(cd "$TMP" && bash "$SCRIPT_DIR/../note.sh" fingerprint \
  --report docs/design/prototype/README.md \
  --report docs/design/prototype/selected.py)"
jq --arg fp "$FP" '.approval.fingerprint=$fp' \
  "$TMP/.codex/multi-model-workflow/task.json" >"$TMP/task.json.tmp"
mv "$TMP/task.json.tmp" "$TMP/.codex/multi-model-workflow/task.json"
git -C "$TMP" add docs
git -C "$TMP" commit -qm docs

BASE_WT_COUNT="$(git -C "$TMP" worktree list --porcelain | grep -c '^worktree ')"
jq '.approval.fingerprint="stale"' "$TMP/.codex/multi-model-workflow/task.json" >"$TMP/task.json.tmp"
mv "$TMP/task.json.tmp" "$TMP/.codex/multi-model-workflow/task.json"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" \
  --worktree "$TMP/.codex/worktrees/stale" >/dev/null 2>&1; then
  no "stale approval must block build"
elif [ "$(git -C "$TMP" worktree list --porcelain | grep -c '^worktree ')" = "$BASE_WT_COUNT" ] \
  && [ ! -e "$TMP/.codex/worktrees/stale" ]; then
  ok "stale approval blocks before control and inner worktree creation"
else
  no "stale approval left build worktree residue"
fi
jq --arg fp "$FP" '.approval.fingerprint=$fp | .prototype.status="active"' \
  "$TMP/.codex/multi-model-workflow/task.json" >"$TMP/task.json.tmp"
mv "$TMP/task.json.tmp" "$TMP/.codex/multi-model-workflow/task.json"
if bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" \
  --worktree "$TMP/.codex/worktrees/active" >/dev/null 2>&1; then
  no "active prototype must block build"
elif [ "$(git -C "$TMP" worktree list --porcelain | grep -c '^worktree ')" = "$BASE_WT_COUNT" ] \
  && [ ! -e "$TMP/.codex/worktrees/active" ]; then
  ok "active prototype blocks before control and inner worktree creation"
else
  no "active prototype left build worktree residue"
fi
jq --arg fp "$FP" '.approval.fingerprint=$fp | .prototype.status="accepted"' \
  "$TMP/.codex/multi-model-workflow/task.json" >"$TMP/task.json.tmp"
mv "$TMP/task.json.tmp" "$TMP/.codex/multi-model-workflow/task.json"

CONTROL="$TMP/.codex/worktrees/build-001"
OUT="$(bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" --worktree "$CONTROL")"
META="$CONTROL/.codex/multi-model-workflow/worker-dispatch/meta.json"
RUN_WT="$(jq -r .worktree "$META")"
PROMPT="$CONTROL/.codex/multi-model-workflow/worker-dispatch/prompt.md"

echo "$OUT" | grep -q '^WORKER_BACKEND=codex-native-subagents$' \
  && ok "dispatch selects Codex native subagents" || no "native backend"
echo "$OUT" | grep -q 'spawn_agent' && echo "$OUT" | grep -q 'fork_turns="none"' \
  && ok "dispatch names the native spawn operation" || no "native spawn instruction"
echo "$OUT" | grep -q 'task_name="build_worker"' \
  && ok "build task name satisfies Codex native schema" || no "build task name"
if echo "$OUT" | grep -qiE 'run[_ -]?id|note-run-id|codex exec|claude|gemini'; then
  no "dispatch must not depend on external Codex or durable agent ids"
else
  ok "dispatch has no external Codex or durable agent id"
fi
[ "$(git -C "$RUN_WT" branch --show-current)" = "worker/build-001" ] \
  && ok "build worker receives an inner worktree" || no "build inner worktree"
CONTROL_B="$TMP/.codex/worktrees/build-002"
bash "$WORKER" dispatch --plan "$PLAN" --design "$DESIGN" --issue "$ISSUE" \
  --worktree "$CONTROL_B" >/dev/null
RUN_WT_B="$(jq -r .worktree "$CONTROL_B/.codex/multi-model-workflow/worker-dispatch/meta.json")"
[ "$RUN_WT" != "$RUN_WT_B" ] && [ -d "$RUN_WT_B" ] \
  && ok "parallel build workers receive separate inner worktrees" || no "parallel build isolation"
grep -q "$RUN_WT" "$PROMPT" && grep -q 'worktree-build/SKILL.md' "$PROMPT" \
  && ok "build prompt pins worktree and skill" || no "build prompt"
grep -q 'prototype/README.md' "$PROMPT" && grep -q 'prototype/selected.py' "$PROMPT" \
  && ! grep -q 'prototype/rejected.py' "$PROMPT" \
  && ok "build prompt only carries accepted prototype materials" || no "prototype handoff"

# Approval fingerprint is rechecked on every entry.
printf 'changed\n' >>"$TMP/docs/design/prototype/selected.py"
if bash "$WORKER" verify --worktree "$CONTROL" >/dev/null 2>&1; then
  no "changed prototype must block verify"
else
  ok "changed prototype blocks verify"
fi
NEW_FP="$(cd "$TMP" && bash "$SCRIPT_DIR/../note.sh" fingerprint \
  --report docs/design/prototype/README.md \
  --report docs/design/prototype/selected.py)"
jq --arg fp "$NEW_FP" '.approval.fingerprint=$fp' \
  "$TMP/.codex/multi-model-workflow/task.json" >"$TMP/task.json.tmp"
mv "$TMP/task.json.tmp" "$TMP/.codex/multi-model-workflow/task.json"
if bash "$WORKER" verify --worktree "$CONTROL" >/dev/null 2>&1; then
  no "reapproved but changed prototype must require redispatch"
else
  ok "reapproved prototype change requires redispatch"
fi
printf 'selected\n' >"$TMP/docs/design/prototype/selected.py"
jq --arg fp "$FP" '.approval.fingerprint=$fp' \
  "$TMP/.codex/multi-model-workflow/task.json" >"$TMP/task.json.tmp"
mv "$TMP/task.json.tmp" "$TMP/.codex/multi-model-workflow/task.json"

bash "$WORKER" verify --worktree "$CONTROL" >/dev/null \
  && ok "clean build boundary verifies" || no "build verify"
printf 'repair\n' >"$TMP/repair.md"
RESUME="$(bash "$WORKER" resume --worktree "$CONTROL" --instructions "$TMP/repair.md")"
echo "$RESUME" | grep -q 'followup_task' && echo "$RESUME" | grep -q 'spawn_agent' \
  && ok "resume offers live follow-up or clean respawn" || no "native resume instruction"
if jq -e 'has("run_id") or has("agent_id")' "$META" >/dev/null; then
  no "worker ledger must not store native agent identity"
else
  ok "worker ledger stores no native agent identity"
fi

mkdir -p "$RUN_WT/docs"
printf 'bad\n' >"$RUN_WT/docs/bad.md"
if bash "$WORKER" verify --worktree "$CONTROL" >/dev/null 2>&1; then
  no "build worker docs write must fail"
else
  ok "build worker docs write fails closed"
fi
rm "$RUN_WT/docs/bad.md"
bash "$WORKER" verify --worktree "$CONTROL" >/dev/null

# Two plan writers are isolated, and only their assigned plan plus Small issues
# section are published back to the App task worktree.
TASK_WT="$TMP/task-wt"
git -C "$TMP" worktree add -q -b codex/demo "$TASK_WT" HEAD
mkdir -p "$TASK_WT/.codex/multi-model-workflow"
cp "$TMP/.codex/multi-model-workflow/task.json" "$TASK_WT/.codex/multi-model-workflow/task.json"
printf 'task branch only\n' >"$TASK_WT/task-branch.txt"
git -C "$TASK_WT" add task-branch.txt
git -C "$TASK_WT" commit -qm "task branch"
TASK_BUILD_CONTROL="$TASK_WT/.codex/worktrees/task-base"
bash "$WORKER" dispatch \
  --plan "$TASK_WT/docs/plans/demo/001.md" \
  --design "$TASK_WT/docs/design/demo.md" \
  --issue "$TASK_WT/docs/issues/demo/001.md" \
  --worktree "$TASK_BUILD_CONTROL" >/dev/null
TASK_BUILD_WT="$(jq -r .worktree "$TASK_BUILD_CONTROL/.codex/multi-model-workflow/worker-dispatch/meta.json")"
[ -f "$TASK_BUILD_WT/task-branch.txt" ] \
  && ok "build worker starts from App task branch HEAD" || no "build base must be task branch HEAD"
PLAN2="$TASK_WT/docs/plans/demo/002.md"
PLAN3="$TASK_WT/docs/plans/demo/003.md"
ISSUE2="$TASK_WT/docs/issues/demo/001.md"
ISSUE3="$TASK_WT/docs/issues/demo/003.md"
printf '# issue 3\n\n## Small issues\n<!-- PENDING -->\n' >"$ISSUE3"

PLAN_OUT="$(bash "$WORKER" plan-dispatch --plan "$PLAN2" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$ISSUE2")"
bash "$WORKER" plan-dispatch --plan "$PLAN3" --worktree "$TASK_WT" \
  --design "$TASK_WT/docs/design/demo.md" --issue "$ISSUE3" >/dev/null
echo "$PLAN_OUT" | grep -q 'spawn_agent' && echo "$PLAN_OUT" | grep -q '互不依赖' \
  && ok "plan dispatch supports parallel native writers" || no "parallel plan dispatch"
echo "$PLAN_OUT" | grep -q 'task_name="plan_writer_002"' \
  && ok "plan task name satisfies Codex native schema" || no "plan task name"

META2="$TASK_WT/.codex/multi-model-workflow/plan-workers/002/dispatch/meta.json"
META3="$TASK_WT/.codex/multi-model-workflow/plan-workers/003/dispatch/meta.json"
SANDBOX2="$(jq -r .worktree "$META2")"
SANDBOX3="$(jq -r .worktree "$META3")"
[ "$SANDBOX2" != "$SANDBOX3" ] && [ -d "$SANDBOX2" ] && [ -d "$SANDBOX3" ] \
  && ok "plan writers have separate inner worktrees" || no "plan isolation"
PLAN_PROMPT="$(jq -r .prompt_file "$META2")"
grep -q 'prototype/README.md' "$PLAN_PROMPT" && grep -q 'prototype/selected.py' "$PLAN_PROMPT" \
  && ! grep -q 'prototype/rejected.py' "$PLAN_PROMPT" \
  && ok "plan prompt only carries accepted prototype materials" || no "plan prototype handoff"

printf '# generated 2\n' >"$(jq -r .plan "$META2")"
printf '# issue\n\n## Small issues\n- child 2\n' >"$(jq -r .issue "$META2")"
printf '# generated 3\n' >"$(jq -r .plan "$META3")"
printf '# issue 3\n\n## Small issues\n- child 3\n' >"$(jq -r .issue "$META3")"

bash "$WORKER" verify --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null \
  && bash "$WORKER" verify --plan "$PLAN3" --worktree "$TASK_WT" >/dev/null \
  && ok "isolated plan results publish" || no "plan publish"
grep -q '^# generated 2$' "$PLAN2" && grep -q '^# generated 3$' "$PLAN3" \
  && grep -q 'child 2' "$ISSUE2" && grep -q 'child 3' "$ISSUE3" \
  && ok "assigned plan and issue sections are published" || no "published results"
[ ! -d "$SANDBOX2" ] && [ ! -d "$SANDBOX3" ] \
  && ok "verified plan sandboxes are cleaned" || no "plan sandbox cleanup"

printf 'tighten acceptance\n' >"$TMP/plan-repair.md"
PLAN_RESUME="$(bash "$WORKER" plan-resume --plan "$PLAN2" --worktree "$TASK_WT" \
  --instructions "$TMP/plan-repair.md")"
REPAIR_SANDBOX="$(jq -r .worktree "$META2")"
echo "$PLAN_RESUME" | grep -q 'spawn_agent' && [ -d "$REPAIR_SANDBOX" ] \
  && grep -q 'prototype/selected.py' "$(jq -r .prompt_file "$META2")" \
  && ok "published plan repair rebuilds isolated native context" || no "plan repair recreation"
printf '# generated 2 repaired\n' >"$(jq -r .plan "$META2")"
printf '# issue\n\n## Small issues\n- child 2 repaired\n' >"$(jq -r .issue "$META2")"
bash "$WORKER" verify --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null
[ ! -d "$REPAIR_SANDBOX" ] && grep -q 'generated 2 repaired' "$PLAN2" \
  && ok "plan repair republishes and cleans" || no "plan repair publish"

printf '# altered issue\n\n## Small issues\n- child 2\n' >"$ISSUE2"
if bash "$WORKER" plan-check --plan "$PLAN2" --worktree "$TASK_WT" >/dev/null 2>&1; then
  no "published issue drift must fail"
else
  ok "published issue drift fails closed"
fi

exit "$fail"
