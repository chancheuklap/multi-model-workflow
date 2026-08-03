#!/usr/bin/env bash
# mmw 统一 CLI 空跑:每个动词路由到对的底层脚本、行为与直调一致。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
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
WT="$(bash "$MMW" task new --scenario develop --slug 2026-06-29-mmw --title t --request t --entry-capability explicit-request --entry-evidence "测试夹具明确要求 MMW" 2>/dev/null | sed -n 's/^worktree_path=//p')"
[ -n "$WT" ] && [ -d "$WT" ] && ok "mmw task new → prepare.sh 建 worktree" || no "mmw task new"

# where / handoff / spinoff → flow.sh
( cd "$WT" && bash "$MMW" where | grep -q "phase=investigate" ) && ok "mmw where → flow.sh where" || no "mmw where"
mkdir -p "$WT/docs"; : > "$WT/docs/x.md"   # handoff 拒收幽灵产出:先真建
( cd "$WT" && bash "$MMW" handoff --conclusion pass --produced docs/x.md >/dev/null ) && \
  [ "$(jq -r .phase "$WT/${STATE_SUBDIR}/task.json")" = "propose" ] && ok "mmw handoff → flow.sh handoff" || no "mmw handoff"
( cd "$WT" && bash "$MMW" spinoff --tag bug --finding "x" >/dev/null ) && \
  [ "$(jq -r '.subtasks|length' "$WT/${STATE_SUBDIR}/task.json")" = "1" ] && ok "mmw spinoff → flow.sh spinoff" || no "mmw spinoff"

# pin → flow.sh(补钉产出,只登记不推进)
mkdir -p "$WT/docs"; : > "$WT/docs/pinme.md"
( cd "$WT" && bash "$MMW" pin --phase investigate --produced docs/pinme.md >/dev/null ) && \
  [ "$(jq -r '.phase_outputs.investigate | index("docs/pinme.md") != null' "$WT/${STATE_SUBDIR}/task.json")" = "true" ] && ok "mmw pin → flow.sh pin" || no "mmw pin"

# note / approve → note.sh(书签 + 唯一人闸)
( cd "$WT" && bash "$MMW" note set --text "书签" >/dev/null && bash "$MMW" note show | grep -q "书签" ) && ok "mmw note → note.sh" || no "mmw note"
if ( cd "$WT" && bash "$MMW" approve --report docs/nothing.md >/dev/null 2>&1 ); then no "mmw approve 幽灵报告应被底层拒"; else ok "mmw approve → note.sh(幽灵报告被拒,路由到位)"; fi

# loop → loop.sh(执行账本,init 无参)
( cd "$WT" && bash "$MMW" loop init >/dev/null && bash "$MMW" loop step add --id 1.1 --desc p >/dev/null ) && \
  [ "$(jq -r '.steps|length' "$WT/${STATE_SUBDIR}/loop-state.json")" = "1" ] && ok "mmw loop → loop.sh" || no "mmw loop"
( cd "$WT" && bash "$MMW" loop status | grep -q "steps=0/1" ) && ok "mmw loop status 报账本进度" || no "mmw loop status"
( cd "$WT" && bash "$MMW" loop close >/dev/null )

# progress → progress.sh(渲染板并落盘)
( cd "$WT" && bash "$MMW" progress render >/dev/null ) && \
  [ -f "$WT/.claude/multi-model-workflow/progress-board.md" ] && ok "mmw progress → progress.sh 落板" || no "mmw progress"

# review → review.sh(捕获到变量再 grep,避免 grep -q 早关管道触发 SIGPIPE+pipefail)
RV="$(cd "$WT" && bash "$MMW" review start --stage design --source x 2>/dev/null)"
echo "$RV" | grep -q "REVIEW_STARTED" && ok "mmw review → review.sh" || no "mmw review"

# codex 别名 → worker.sh(缺参数应被底层拒,证明路由到位)
if ( cd "$WT" && bash "$MMW" codex dispatch >/dev/null 2>&1 ); then no "mmw codex 路由(缺参数应拒)"; else ok "mmw codex → worker.sh(缺参被拒)"; fi

# help / 未知
HELP="$(bash "$MMW" help 2>/dev/null)"
echo "$HELP" | grep -q "mmw handoff" && echo "$HELP" | grep -q "mmw prototype" \
  && ok "mmw help 列主流程与 prototype 命令" || no "mmw help"
if bash "$MMW" bogus >/dev/null 2>&1; then no "未知命令被拒"; else ok "未知命令被拒"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
