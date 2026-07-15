#!/usr/bin/env bash
# 端到端空跑:发真命令走一条完整 develop 任务,证明机器从入口到 ready-to-close
# 平稳推进——接力单逐阶段接得上、design 人闸(approve)过门、审闸留痕收口、内外层命令不报错。
# 这是"端到端平稳"的命令级验收(内容级=真 subagent/Codex,不在单测范围)。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
FLOW="$SCRIPT_DIR/../flow.sh"
LOOP="$SCRIPT_DIR/../loop.sh"
NOTE="$SCRIPT_DIR/../note.sh"
REVIEW="$SCRIPT_DIR/../review.sh"
PACKAGE="$SCRIPT_DIR/../package-phase.sh"
PACKAGE_FIXTURES="$SCRIPT_DIR/fixtures/package-phase"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
ph() { jq -r .phase "$WT/${STATE_SUBDIR}/task.json"; }
gate() { jq -r '.gate // "null"' "$WT/${STATE_SUBDIR}/task.json"; }
att() { jq -r .attendance "$WT/${STATE_SUBDIR}/task.json"; }
prevout() { (cd "$WT" && bash "$FLOW" where) | sed -n 's/^prev_outputs=//p'; }
mkf() { mkdir -p "$WT/$(dirname "$1")"; : > "$WT/$1"; }   # 接力单只收真实路径:先真建
mkd() { mkdir -p "$WT/$1"; }
trace() { # $1=stage:落审查留痕(收口硬核=文件在且含 verdict)
  mkdir -p "$WT/docs/reviews"
  printf '# findings\n\n## verdict\npass\n' > "$WT/docs/reviews/2026-06-29-e2e-$1.md"
}
init_empty_package() {
  mkdir -p "$WT/fixtures"
  cp -R "$PACKAGE_FIXTURES/." "$WT/fixtures/"
  ( cd "$WT" && bash "$PACKAGE" init --scope fixtures/generic.release-package-scope.json )
}

echo "=== test_e2e.sh — 一条 develop 端到端空跑 ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export UV_CACHE_DIR="${UV_CACHE_DIR:-$TMP/uv-cache}"
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo seed>seed; git add -A; git commit -qm seed

# 入口:建 develop 任务(讨论态生来 attended)
WT="$(bash "$PREPARE" new --scenario develop --slug 2026-06-29-e2e --title "端到端" 2>/dev/null | sed -n 's/^worktree_path=//p')"
[ -n "$WT" ] && ok "入口:prepare 建 develop worktree" || { no "prepare 失败"; exit 1; }
[ "$(ph)" = "investigate" ] && ok "起于 investigate" || no "起点 ($(ph))"
[ "$(att)" = "attended" ] && ok "讨论态生来 attended(HITL 集中在 propose/design)" || no "attended 起步 ($(att))"

# investigate → propose(产出现状报告,钉接力单)
mkf docs/investigating/e2e.md
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/e2e.md >/dev/null )
[ "$(ph)" = "propose" ] && ok "investigate→propose" || no "→propose ($(ph))"
[ "$(prevout)" = '["docs/investigating/e2e.md"]' ] && ok "propose 照单读到 investigate 报告" || no "接力单 investigate→propose ($(prevout))"

# propose → design(给方案选定方向,钉接力单)
mkf docs/design/e2e-direction.md
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/design/e2e-direction.md >/dev/null )
[ "$(ph)" = "design" ] && ok "propose→design(方向选定)" || no "→design ($(ph))"
# design 跨两阶 reads:现状报告 + 方向都进 prev_outputs(照单读全,不自己找)
[ "$(prevout)" = '["docs/investigating/e2e.md","docs/design/e2e-direction.md"]' ] \
  && ok "design 照单读到 现状报告 + 选定方向" || no "接力单 propose→design ($(prevout))"

# design 阶段:讨论中随手记书签(断点续传三源之一)
( cd "$WT" && bash "$NOTE" note set --text "边界:计费口径按自然月" >/dev/null ) && ok "design 讨论中 note 书签可记" || no "note 书签"
# 设计成文(含空 Cross-Plan Contract Anchors 节,供 ③合同门机器核)
mkdir -p "$WT/docs/design"
printf '# e2e 设计\n\n方案主体。\n\n## Cross-Plan Contract Anchors\n<!-- 由 plan 阶段回填 -->\n' > "$WT/docs/design/e2e.md"
# 设计预审(结果给用户参考,不是闸):命令级起得来即可
( cd "$WT" && bash "$REVIEW" start --stage design --source docs/design/e2e.md >/dev/null 2>&1 ) && ok "设计预审 review start 起得来(参考,非闸)" || no "设计预审"
# design 出口 = 唯一人闸:用户 /approve-design → mmw approve(盖指纹+过门+放权)
APR="$(cd "$WT" && bash "$NOTE" approve --report docs/design/e2e.md)"
echo "$APR" | grep -q "^APPROVED fingerprint=" && ok "approve 过门:盖承重指纹" || no "approve 指纹"
[ "$(ph)" = "to-issue" ] && [ "$(gate)" = "null" ] && ok "过门→to-issue(不走 handoff pass)" || no "过门→to-issue ($(ph)/$(gate))"
[ "$(att)" = "afk" ] && ok "过门自动切 afk(流水线态放权自主跑)" || no "过门切 afk ($(att))"
[ "$(prevout)" = '["docs/design/e2e.md"]' ] && ok "to-issue 照单读到 设计文档(approve 钉的)" || no "接力单 design→to-issue ($(prevout))"

# to-issue → plan(产出 issue 骨架,无审闸)
mkd docs/issues/e2e
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/e2e/ >/dev/null )
[ "$(ph)" = "plan" ] && [ "$(gate)" = "null" ] && ok "to-issue→plan(无审闸)" || no "to-issue→plan ($(ph)/$(gate))"
# plan reads [design,to-issue] → 一单读全(设计文档 + issue 骨架)
[ "$(prevout)" = '["docs/design/e2e.md","docs/issues/e2e/"]' ] && ok "plan 照单读到 设计文档 + issue 骨架" || no "接力单 →plan ($(prevout))"

# plan → ②审闸(产出 plan 目录)
mkd docs/plans/e2e
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/e2e/)"
echo "$OUT" | grep -q "NEXT_ACTION=review" && ok "plan 过→进②审闸" || no "②审闸"
RS="$(cd "$WT" && bash "$FLOW" where | sed -n 's/^review_source=//p')"
[ "$RS" = "docs/plans/e2e/" ] && ok "审闸报 review_source 裸路径(直接喂 --source)" || no "review_source ($RS)"
( cd "$WT" && bash "$REVIEW" start --stage plan --source docs/plans/e2e/ >/dev/null 2>&1 ) && ok "②审 brief 出得来" || no "②审 brief"
# 收口硬核:留痕没落盘 pass 被拒;落盘含 verdict 才放行
if ( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 ); then no "②审无留痕 pass 应被拒"; else ok "②审无留痕 pass 被拒(留痕=审真跑过)"; fi
trace plan
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )   # ②审过
[ "$(ph)" = "build" ] && ok "②审过→build" || no "②审过→build ($(ph))"
[ "$(prevout)" = '["docs/plans/e2e/"]' ] && ok "build 照单读到 plan 目录" || no "接力单 plan→build ($(prevout))"

# build:起执行账本 + 走一步 + status 报进度(账本只记录,不当闸)
( cd "$WT" && bash "$LOOP" init >/dev/null && bash "$LOOP" step add --id 1.1 --desc "pack 1.1" --plan docs/plans/e2e/001.md >/dev/null \
  && bash "$LOOP" step done --id 1.1 >/dev/null ) && ok "build:执行账本走通(init/step add/done)" || no "build 账本"
[ "$(cd "$WT" && bash "$LOOP" status)" = "steps=1/1 remaining=none" ] && ok "build:loop status 报完成度" || no "build status"
# ③合同门:anchors 节为空 → 机器核实直接放行(不派审者)
OUT3="$(cd "$WT" && bash "$REVIEW" start --stage plan-impl --source docs/design/e2e.md 2>/dev/null)"
echo "$OUT3" | grep -q "CONTRACT_GATE_EMPTY" && ok "build:③合同门机器核 anchors 空→直接放行" || no "③合同门 ($OUT3)"
# build 产物过 → ④终审闸(引擎强制;产出=真提交范围)
RANGE="$(cd "$WT" && git rev-parse HEAD)..HEAD"
OUTBG="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced "$RANGE")"
echo "$OUTBG" | grep -q "NEXT_ACTION=review" && ok "build 过→进④终审闸(引擎强制)" || no "build→④闸"
[ "$(ph)" = "build" ] && [ "$(gate)" = "build" ] && ok "build 审闸:phase 不动 gate=build" || no "build 闸 ($(ph)/$(gate))"
( cd "$WT" && bash "$FLOW" where | grep "review_start=" | grep -q -- "review start --stage final" ) && ok "build 闸 where 吐 review_start --stage final" || no "review_start final"
( cd "$WT" && bash "$FLOW" where | grep -q "review_trace=docs/reviews/2026-06-29-e2e-final.md" ) && ok "build 闸 where 吐 review_trace 落点" || no "review_trace"

# ④终审:brief 出得来 → 留痕落盘 → 钉终审报告过闸 → package
( cd "$WT" && bash "$REVIEW" start --stage final --source "$RANGE" >/dev/null 2>&1 ) && ok "④终审 brief 出得来" || no "④终审"
trace final
mkf docs/e2e-final-review.md
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/e2e-final-review.md >/dev/null )
[ "$(ph)" = "package" ] && [ "$(gate)" = "null" ] && ok "④审过→package(gate 清空)" || no "④审过→package ($(ph)/$(gate))"
# 终审报告钉进 build 接力单,package 照单读得到
echo "$(prevout)" | grep -q "docs/e2e-final-review.md" && ok "终审报告进接力单(package 读 build 产物)" || no "终审报告接力单 ($(prevout))"
if ( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 ); then no "无 package state 不可进 closing"; else ok "无 package state 拒绝 closing"; fi
init_empty_package >/dev/null
[ "$(cd "$WT" && bash "$PACKAGE" exit-check)" = "DONE" ] && ok "空 package 初始化后 exit-check DONE" || no "空 package exit-check"
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(ph)" = "closing" ] && ok "空 package 后→closing" || no "package→closing ($(ph))"

# closing → ready-to-close
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass)"
echo "$OUT" | grep -q "STATUS=ready-to-close" && ok "closing→ready-to-close(端到端贯通)" || no "ready-to-close"

# history:investigate,propose,to-issue,plan,②审,build,④审,package,closing = 9 笔 handoff(approve 过门不占 handoff 账)
[ "$(jq -r '.history|length' "$WT/${STATE_SUBDIR}/task.json")" = "9" ] && ok "history 记 9 笔 handoff(全程留痕)" || no "history 9 ($(jq -r '.history|length' "$WT/${STATE_SUBDIR}/task.json"))"
# approve 指纹全程未失效(设计过门后没改过)
( cd "$WT" && bash "$FLOW" where ) | grep -q "approval_stale" && no "设计未改不该报 stale" || ok "设计指纹全程有效(执行的就是确认的)"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
