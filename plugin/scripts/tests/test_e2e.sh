#!/usr/bin/env bash
# 端到端空跑:发真命令走一条完整 develop 任务,证明机器从入口到 ready-to-close
# 平稳推进——接力单逐阶段接得上、审闸该停就停、内外层命令不报错。
# 这是"端到端平稳"的命令级验收(内容级=真 subagent/Codex,不在单测范围)。
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
FLOW="$SCRIPT_DIR/../flow.sh"
LOOP="$SCRIPT_DIR/../loop.sh"
REVIEW="$SCRIPT_DIR/../review.sh"
PACKAGE="$SCRIPT_DIR/../package-phase.sh"
PACKAGE_FIXTURES="$SCRIPT_DIR/fixtures/package-phase"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
ph() { jq -r .phase "$WT/${STATE_SUBDIR}/task.json"; }
gate() { jq -r '.gate // "null"' "$WT/${STATE_SUBDIR}/task.json"; }
prevout() { (cd "$WT" && bash "$FLOW" where) | sed -n 's/^prev_outputs=//p'; }
mkf() { mkdir -p "$WT/$(dirname "$1")"; : > "$WT/$1"; }   # handoff 拒收幽灵产出:先真建
mkd() { mkdir -p "$WT/$1"; }
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

# 入口:建 develop 任务
WT="$(bash "$PREPARE" new --scenario develop --slug 2026-06-29-e2e --title "端到端" 2>/dev/null | sed -n 's/^worktree_path=//p')"
[ -n "$WT" ] && ok "入口:prepare 建 develop worktree" || { no "prepare 失败"; exit 1; }
[ "$(ph)" = "investigate" ] && ok "起于 investigate" || no "起点 ($(ph))"

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

# design → ①审闸(只产设计文档,①审只审它)
mkf docs/design/e2e.md
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/design/e2e.md)"
echo "$OUT" | grep -q "NEXT_ACTION=review" && ok "design 过→进①审闸(不直接 advance)" || no "①审闸"
[ "$(gate)" = "design" ] && ok "gate=design" || no "gate ($(gate))"
# G2:审闸里 where 报 review_source = 当前阶产物(审什么),裸路径直接喂 review start --source
RS="$(cd "$WT" && bash "$FLOW" where | sed -n 's/^review_source=//p')"
[ "$RS" = "docs/design/e2e.md" ] && ok "审闸报 review_source 裸路径(直接喂 --source,只设计文档)" || no "review_source ($RS)"
# 起审一条命令(init review loop + 出 brief)
( cd "$WT" && bash "$REVIEW" start --stage design --source docs/design/e2e.md >/dev/null 2>&1 ) && ok "review.sh start 起①审 loop" || no "review.sh start"
# 覆盖清单坐实(新契约:审闸 pass 前 loop 必须 exit-check==DONE,替代 SubagentStop 看守)
( cd "$WT" && bash "$LOOP" checklist add --item "设计意图" --source docs/design/e2e.md >/dev/null \
  && bash "$LOOP" checklist cover --item "设计意图" --evidence "docs/design/e2e.md:1" >/dev/null )
# 审过 → advance to-issue(审后再切片)
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(ph)" = "to-issue" ] && [ "$(gate)" = "null" ] && ok "①审过→to-issue(审后切片),gate 清空" || no "①审过→to-issue ($(ph)/$(gate))"
[ "$(prevout)" = '["docs/design/e2e.md"]' ] && ok "to-issue 照单读到 设计文档" || no "接力单 design→to-issue ($(prevout))"
# to-issue → plan(产出 issue 骨架,无审闸)
mkd docs/issues/e2e
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/e2e/ >/dev/null )
[ "$(ph)" = "plan" ] && [ "$(gate)" = "null" ] && ok "to-issue→plan(无审闸)" || no "to-issue→plan ($(ph)/$(gate))"
# G1:plan reads [design,to-issue] → 一单读全(设计文档 + issue 骨架)
[ "$(prevout)" = '["docs/design/e2e.md","docs/issues/e2e/"]' ] && ok "plan 照单读到 设计文档 + issue 骨架" || no "接力单 →plan ($(prevout))"

# plan → ②审闸(产出 plan 目录)
mkd docs/plans/e2e
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/e2e/)"
echo "$OUT" | grep -q "NEXT_ACTION=review" && ok "plan 过→进②审闸" || no "②审闸"
( cd "$WT" && bash "$REVIEW" start --stage plan --source docs/plans/e2e/ >/dev/null 2>&1 ) && ok "②审 loop 起得来" || no "②审 loop"
( cd "$WT" && bash "$LOOP" checklist add --item "计划覆盖" --source docs/plans/e2e/ >/dev/null \
  && bash "$LOOP" checklist cover --item "计划覆盖" --evidence "docs/plans/e2e:1" >/dev/null )
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )   # ②审过
[ "$(ph)" = "build" ] && ok "②审过→build" || no "②审过→build ($(ph))"
[ "$(prevout)" = '["docs/plans/e2e/"]' ] && ok "build 照单读到 plan 目录" || no "接力单 plan→build ($(prevout))"

# build:起落地 loop + 走一步 + ③合同门(命令级不报错)
( cd "$WT" && bash "$LOOP" init --kind execution >/dev/null && bash "$LOOP" step add --id 1.1 --desc "pack 1.1" >/dev/null \
  && bash "$LOOP" step done --id 1.1 >/dev/null ) && ok "build:起 execution loop + 步账走通" || no "build loop"
[ "$(cd "$WT" && bash "$LOOP" exit-check)" = "DONE" ] && ok "build:步账全 done→exit-check DONE" || no "build exit-check"
( cd "$WT" && bash "$REVIEW" start --stage plan-impl --source docs/plans/e2e/ >/dev/null 2>&1 ) && ok "build:③合同门起得来" || no "③合同门"
# build 产物过 → ④终审闸(build 也 gated:phase 不动,gate=build);产出=真提交范围(幽灵范围会被拒)
RANGE="$(cd "$WT" && git rev-parse HEAD)..HEAD"
OUTBG="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced "$RANGE")"
echo "$OUTBG" | grep -q "NEXT_ACTION=review" && ok "build 过→进④终审闸(引擎强制)" || no "build→④闸"
[ "$(ph)" = "build" ] && [ "$(gate)" = "build" ] && ok "build 审闸:phase 不动 gate=build" || no "build 闸 ($(ph)/$(gate))"
# where 在 build 闸吐确切 review_start --stage final(引擎给命令,不靠散文猜)
( cd "$WT" && bash "$FLOW" where | grep "review_start=" | grep -q -- "review start --stage final" ) && ok "build 闸 where 吐 review_start --stage final" || no "review_start final"

# ④终审 loop 起得来 → 审过钉终审报告 → package → closing
( cd "$WT" && bash "$REVIEW" start --stage final --source "$RANGE" >/dev/null 2>&1 ) && ok "④终审 loop 起得来" || no "④终审"
( cd "$WT" && bash "$LOOP" checklist add --item "意图逐条" --source "$RANGE" >/dev/null \
  && bash "$LOOP" checklist cover --item "意图逐条" --evidence "$RANGE" >/dev/null )
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

# history 完整:investigate,propose,design,①审,to-issue,plan,②审,build,④审,package,closing = 11 步
[ "$(jq -r '.history|length' "$WT/${STATE_SUBDIR}/task.json")" = "11" ] && ok "history 记满 11 步(package + 三审闸 ①②④ 全程留痕)" || no "history 11 ($(jq -r '.history|length' "$WT/${STATE_SUBDIR}/task.json"))"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
