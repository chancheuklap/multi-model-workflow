#!/usr/bin/env bash
# mmw 统一 CLI 空跑:每个动词路由到对的底层脚本、行为与直调一致。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MMW="$SCRIPT_DIR/../mmw.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_mmw.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo seed>seed; git add -A; git commit -qm seed

# task new → prepare.sh
WT="$(bash "$MMW" task new --scenario develop --slug 2026-06-29-mmw --title t 2>/dev/null | sed -n 's/^worktree_path=//p')"
[ -n "$WT" ] && [ -d "$WT" ] && ok "mmw task new → prepare.sh 建 worktree" || no "mmw task new"

# where / handoff / spinoff → flow.sh
( cd "$WT" && bash "$MMW" where | grep -q "phase=investigate" ) && ok "mmw where → flow.sh where" || no "mmw where"
mkdir -p "$WT/docs"; : > "$WT/docs/x.md"   # handoff 拒收幽灵产出:先真建
( cd "$WT" && bash "$MMW" handoff --conclusion pass --produced docs/x.md >/dev/null ) && \
  [ "$(jq -r .phase "$WT/.claude/multi-model-workflow/task.json")" = "propose" ] && ok "mmw handoff → flow.sh handoff" || no "mmw handoff"
( cd "$WT" && bash "$MMW" spinoff --tag bug --finding "x" >/dev/null ) && \
  [ "$(jq -r '.subtasks|length' "$WT/.claude/multi-model-workflow/task.json")" = "1" ] && ok "mmw spinoff → flow.sh spinoff" || no "mmw spinoff"

# loop → loop.sh
( cd "$WT" && bash "$MMW" loop init --kind execution >/dev/null && bash "$MMW" loop step add --id 1.1 --desc p >/dev/null ) && \
  [ "$(jq -r '.steps|length' "$WT/.claude/multi-model-workflow/loop-state.json")" = "1" ] && ok "mmw loop → loop.sh" || no "mmw loop"

# progress → progress.sh(渲染板并落盘)
( cd "$WT" && bash "$MMW" progress render >/dev/null ) && \
  [ -f "$WT/.claude/multi-model-workflow/progress-board.md" ] && ok "mmw progress → progress.sh 落板" || no "mmw progress"

# review → review.sh(捕获到变量再 grep,避免 grep -q 早关管道触发 SIGPIPE+pipefail)
# 上面留了个未收束 execution loop(step 1.1 pending)→ 起审必须被拒(防落地步账被静默清)
if ( cd "$WT" && bash "$MMW" review start --stage design --source x >/dev/null 2>&1 ); then
  no "未收束 execution loop 起审应拒"
else
  ok "未收束 execution loop → review start 拒(fail-closed)"
fi
( cd "$WT" && bash "$MMW" loop close >/dev/null )   # 显式收束后再起审
RV="$(cd "$WT" && bash "$MMW" review start --stage design --source x 2>/dev/null)"
echo "$RV" | grep -q "REVIEW_STARTED" && ok "mmw review → review.sh" || no "mmw review"

# codex → codex-worker.sh(缺参数应被底层拒,证明路由到位)
if ( cd "$WT" && bash "$MMW" codex dispatch >/dev/null 2>&1 ); then no "mmw codex 路由(缺参数应拒)"; else ok "mmw codex → codex-worker.sh(缺参被拒)"; fi

# help / 未知
bash "$MMW" help 2>/dev/null | grep -q "mmw handoff" && ok "mmw help 列命令" || no "mmw help"
if bash "$MMW" bogus >/dev/null 2>&1; then no "未知命令被拒"; else ok "未知命令被拒"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
