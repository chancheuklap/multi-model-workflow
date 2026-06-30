#!/usr/bin/env bash
# 端到端空跑:发真命令走一条完整 develop 任务,证明机器从入口到 ready-to-close
# 平稳推进——接力单逐阶段接得上、审闸该停就停、内外层命令不报错。
# 这是"端到端平稳"的命令级验收(内容级=真 subagent/Codex,不在单测范围)。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
FLOW="$SCRIPT_DIR/../flow.sh"
LOOP="$SCRIPT_DIR/../loop.sh"
REVIEW="$SCRIPT_DIR/../review.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
ph() { jq -r .phase "$WT/.claude/multi-model-workflow/task.json"; }
gate() { jq -r '.gate // "null"' "$WT/.claude/multi-model-workflow/task.json"; }
prevout() { (cd "$WT" && bash "$FLOW" where) | sed -n 's/^prev_outputs=//p'; }

echo "=== test_e2e.sh — 一条 develop 端到端空跑 ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo seed>seed; git add -A; git commit -qm seed

# 入口:建 develop 任务
WT="$(bash "$PREPARE" new --scenario develop --slug 2026-06-29-e2e --title "端到端" 2>/dev/null | sed -n 's/^worktree_path=//p')"
[ -n "$WT" ] && ok "入口:prepare 建 develop worktree" || { no "prepare 失败"; exit 1; }
[ "$(ph)" = "investigate" ] && ok "起于 investigate" || no "起点 ($(ph))"

# investigate → propose(产出现状报告,钉接力单)
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/e2e.md >/dev/null )
[ "$(ph)" = "propose" ] && ok "investigate→propose" || no "→propose ($(ph))"
[ "$(prevout)" = '["docs/investigating/e2e.md"]' ] && ok "propose 照单读到 investigate 报告" || no "接力单 investigate→propose ($(prevout))"

# propose → design(给方案选定方向,钉接力单)
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/design/e2e-direction.md >/dev/null )
[ "$(ph)" = "design" ] && ok "propose→design(方向选定)" || no "→design ($(ph))"
# design 跨两阶 reads:现状报告 + 方向都进 prev_outputs(照单读全,不自己找)
[ "$(prevout)" = '["docs/investigating/e2e.md","docs/design/e2e-direction.md"]' ] \
  && ok "design 照单读到 现状报告 + 选定方向" || no "接力单 propose→design ($(prevout))"

# design → ①审闸(只产设计文档,①审只审它)
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/design/e2e.md)"
echo "$OUT" | grep -q "NEXT_ACTION=review" && ok "design 过→进①审闸(不直接 advance)" || no "①审闸"
[ "$(gate)" = "design" ] && ok "gate=design" || no "gate ($(gate))"
# G2:审闸里 where 报 review_source = 当前阶产物(审什么),裸路径直接喂 review start --source
RS="$(cd "$WT" && bash "$FLOW" where | sed -n 's/^review_source=//p')"
[ "$RS" = "docs/design/e2e.md" ] && ok "审闸报 review_source 裸路径(直接喂 --source,只设计文档)" || no "review_source ($RS)"
# 起审一条命令(init review loop + 出 brief)
( cd "$WT" && bash "$REVIEW" start --stage design --source docs/design/e2e.md >/dev/null 2>&1 ) && ok "review.sh start 起①审 loop" || no "review.sh start"
# 审过 → advance to-issue(审后再切片)
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(ph)" = "to-issue" ] && [ "$(gate)" = "null" ] && ok "①审过→to-issue(审后切片),gate 清空" || no "①审过→to-issue ($(ph)/$(gate))"
[ "$(prevout)" = '["docs/design/e2e.md"]' ] && ok "to-issue 照单读到 设计文档" || no "接力单 design→to-issue ($(prevout))"
# to-issue → plan(产出 issue 骨架,无审闸)
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/e2e/ >/dev/null )
[ "$(ph)" = "plan" ] && [ "$(gate)" = "null" ] && ok "to-issue→plan(无审闸)" || no "to-issue→plan ($(ph)/$(gate))"
# G1:plan reads [design,to-issue] → 一单读全(设计文档 + issue 骨架)
[ "$(prevout)" = '["docs/design/e2e.md","docs/issues/e2e/"]' ] && ok "plan 照单读到 设计文档 + issue 骨架" || no "接力单 →plan ($(prevout))"

# plan → ②审闸(产出 plan 目录)
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/e2e/)"
echo "$OUT" | grep -q "NEXT_ACTION=review" && ok "plan 过→进②审闸" || no "②审闸"
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )   # ②审过
[ "$(ph)" = "build" ] && ok "②审过→build" || no "②审过→build ($(ph))"
[ "$(prevout)" = '["docs/plans/e2e/"]' ] && ok "build 照单读到 plan 目录" || no "接力单 plan→build ($(prevout))"

# build:起落地 loop + 走一步 + ③合同门(命令级不报错)
( cd "$WT" && bash "$LOOP" init --kind execution >/dev/null && bash "$LOOP" step add --id 1.1 --desc "pack 1.1" >/dev/null \
  && bash "$LOOP" step done --id 1.1 >/dev/null ) && ok "build:起 execution loop + 步账走通" || no "build loop"
[ "$(cd "$WT" && bash "$LOOP" exit-check)" = "DONE" ] && ok "build:步账全 done→exit-check DONE" || no "build exit-check"
( cd "$WT" && bash "$REVIEW" start --stage plan-impl --source docs/plans/e2e/ >/dev/null 2>&1 ) && ok "build:③合同门起得来" || no "③合同门"
# build → verify
( cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced "seed..HEAD" >/dev/null )
[ "$(ph)" = "verify" ] && ok "build→verify(无闸)" || no "build→verify ($(ph))"

# verify(④终审)→ closing
( cd "$WT" && bash "$REVIEW" start --stage final --source docs/design/e2e.md >/dev/null 2>&1 ) && ok "verify:④终审 loop 起得来" || no "④终审"
( cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(ph)" = "closing" ] && ok "verify→closing" || no "verify→closing ($(ph))"

# closing → ready-to-close
OUT="$(cd "$WT" && bash "$FLOW" handoff --conclusion pass)"
echo "$OUT" | grep -q "STATUS=ready-to-close" && ok "closing→ready-to-close(端到端贯通)" || no "ready-to-close"

# history 完整:investigate,propose,design,①审,to-issue,plan,②审,build,verify,closing = 10 步
[ "$(jq -r '.history|length' "$WT/.claude/multi-model-workflow/task.json")" = "10" ] && ok "history 记满 10 步(全程留痕)" || no "history 10 ($(jq -r '.history|length' "$WT/.claude/multi-model-workflow/task.json"))"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
