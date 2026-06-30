#!/usr/bin/env bash
# flow.sh 骨架空跑:每阶段只回个结论词,验证引擎换阶段对、分叉掉头对、上限拦得住、断点能续。
# 流程模型:一条主干 + 预设开关。阶段词=投/想/拆/落/验/收(investigate/design/plan/build/verify/closing)。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
FLOW="$SCRIPT_DIR/../flow.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_flow.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q; git config user.email t@t; git config user.name t
echo seed > seed.txt; git add -A; git commit -qm seed

newtask() { # preset slug -> echoes worktree path
  bash "$PREPARE" new --scenario "$1" --slug "$2" --title "t-$2" 2>/dev/null \
    | grep '^worktree_path=' | cut -d= -f2-
}
mphase() { jq -r .phase "$1/.claude/multi-model-workflow/task.json"; }
mfield() { jq -r ".$2" "$1/.claude/multi-model-workflow/task.json"; }

# ===== A: develop 全程空跑 + 中途甩支线 (investigate→design→plan→build→verify→closing) =====
WA="$(newtask develop 2026-06-28-task-a)"
[ "$(mphase "$WA")" = "investigate" ] && ok "A 起于 investigate" || no "A 起于 investigate ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/ctx.md >/dev/null )  # investigate→propose
[ "$(mphase "$WA")" = "propose" ] && ok "investigate pass→propose" || no "investigate→propose ($(mphase "$WA"))"
[ "$(mfield "$WA" 'artifacts|length')" = "1" ] && ok "产出登记进 artifacts" || no "产出登记"
# 接力单:产出钉进 phase_outputs[investigate],下阶段 where 照单读
[ "$(mfield "$WA" 'phase_outputs.investigate[0]')" = "docs/ctx.md" ] && ok "产出钉进接力单 phase_outputs[investigate]" || no "接力单钉死"
WPO="$(cd "$WA" && bash "$FLOW" where)"
echo "$WPO" | grep -q 'prev_outputs=\["docs/ctx.md"\]' && ok "where 报上阶段产出(prev_outputs 照单读)" || no "prev_outputs 照单读"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/dir.md >/dev/null )  # propose→design(给方案选定→进设计)
[ "$(mphase "$WA")" = "design" ] && ok "propose pass→design" || no "propose→design ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" spinoff --tag bug --finding "中途挖到登录态丢失" >/dev/null )
[ "$(mfield "$WA" 'subtasks|length')" = "1" ] && ok "甩支线→子任务登记" || no "甩支线登记"
[ "$(mphase "$WA")" = "design" ] && ok "甩支线后主流程不动" || no "甩支线后主流程不动"

# design 产物过 → 进 ①审闸(phase 不动,gate=design)
OUTG="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass)"       # design→gate:design
echo "$OUTG" | grep -q "NEXT_ACTION=review" && ok "design pass→进审闸(review)" || no "design→审闸"
echo "$OUTG" | grep -q "REVIEW_STAGE=design" && ok "审闸报阶段 design" || no "REVIEW_STAGE"
[ "$(mphase "$WA")" = "design" ] && ok "审闸里 phase 不动" || no "审闸 phase 不动 ($(mphase "$WA"))"
[ "$(mfield "$WA" gate)" = "design" ] && ok "gate=design" || no "gate=design ($(mfield "$WA" gate))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # ①审 verdict pass → to-issue
[ "$(mphase "$WA")" = "to-issue" ] && ok "①审过→进 to-issue(审后切片)" || no "①审过→to-issue ($(mphase "$WA"))"
[ "$(mfield "$WA" gate)" = "null" ] && ok "进下一阶段 gate 清空" || no "gate 清空 ($(mfield "$WA" gate))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # to-issue→plan(无审闸)
[ "$(mphase "$WA")" = "plan" ] && ok "to-issue→进 plan(无审闸)" || no "to-issue→plan ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # plan→gate:plan
[ "$(mfield "$WA" gate)" = "plan" ] && ok "plan pass→进 ②审闸" || no "②审闸 ($(mfield "$WA" gate))"
( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # ②审 verdict→build
[ "$(mphase "$WA")" = "build" ] && ok "②审过→进 build" || no "②审过→build ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # build→verify(build 不 gated)
[ "$(mphase "$WA")" = "verify" ] && ok "build→verify(无闸)" || no "推进到 verify ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # verify→closing(verify=④,不 gated)
[ "$(mphase "$WA")" = "closing" ] && ok "verify→closing(无闸)" || no "→closing"
OUT="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass)"        # closing→ready-to-close
echo "$OUT" | grep -q "STATUS=ready-to-close" && ok "末阶段 pass→ready-to-close" || no "ready-to-close"
echo "$OUT" | grep -q "NEXT_ACTION=done" && ok "末阶段 NEXT=done" || no "NEXT=done"
[ "$(mfield "$WA" 'history|length')" = "10" ] && ok "history 记满 10 步(含 propose + to-issue + 两审闸)" || no "history 10 步 ($(mfield "$WA" 'history|length'))"

# ===== A2: 审打回 → 清 gate 回该阶段返工 =====
WA2="$(newtask develop 2026-06-28-task-a2)"
( cd "$WA2" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # investigate→propose
( cd "$WA2" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # propose→design
( cd "$WA2" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # design→gate:design
[ "$(mfield "$WA2" gate)" = "design" ] && ok "A2 进 ①审闸" || no "A2 ①审闸"
( cd "$WA2" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )  # 审打回
[ "$(mfield "$WA2" gate)" = "null" ] && ok "审打回→gate 清空" || no "审打回 gate 清空 ($(mfield "$WA2" gate))"
[ "$(mphase "$WA2")" = "design" ] && ok "审打回→停在 design 返工" || no "审打回停 design"
[ "$(mfield "$WA2" repair_count)" = "1" ] && ok "审打回计返工=1" || no "审打回返工计数"

# ===== B: bug 掉头 + 上限拦截 (investigate→build→verify→closing) =====
WB="$(newtask bug 2026-06-28-task-b)"
[ "$(mphase "$WB")" = "investigate" ] && ok "B 起于 investigate" || no "B 起于 investigate"
OUTB="$(cd "$WB" && bash "$FLOW" handoff --conclusion needs-redirection)"
echo "$OUTB" | grep -q "NEXT_ACTION=turn-around" && ok "掉头动作" || no "掉头动作"
[ "$(mphase "$WB")" = "investigate" ] && ok "掉头回首阶段" || no "掉头回首阶段"
[ "$(mfield "$WB" turnaround_count)" = "1" ] && ok "掉头计数=1" || no "掉头计数"
OUTB2="$(cd "$WB" && bash "$FLOW" handoff --conclusion needs-redirection)"
echo "$OUTB2" | grep -q "STATUS=blocked" && ok "掉头超上限→blocked" || no "掉头超上限"

# ===== B2: bug 系统性设计问题 → mmw task escalate --to develop(原地升级,投查成果留着) =====
WBE="$(newtask bug 2026-06-29-task-be)"
( cd "$WBE" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/be.md >/dev/null )  # bug investigate 查出根因
ESC="$(cd "$WBE" && bash "$PREPARE" escalate --to develop)"
echo "$ESC" | grep -q "ESCALATED from=bug to=develop" && ok "escalate bug→develop" || no "escalate 回执"
[ "$(mfield "$WBE" scenario)" = "develop" ] && ok "升级后 scenario=develop" || no "scenario 升级 ($(mfield "$WBE" scenario))"
[ "$(mfield "$WBE" 'phases|join(",")')" = "investigate,propose,design,to-issue,plan,build,verify,closing" ] && ok "升级后 phases=develop 八阶段" || no "phases 升级 ($(mfield "$WBE" 'phases|join(",")'))"
[ "$(mphase "$WBE")" = "investigate" ] && [ "$(mfield "$WBE" phase_index)" = "0" ] && ok "游标回 investigate" || no "游标回首阶段"
[ "$(mfield "$WBE" 'phase_outputs.investigate[0]')" = "docs/investigating/be.md" ] && ok "投查成果保留(phase_outputs 不丢)" || no "投查成果丢失"
[ "$(mfield "$WBE" 'history[-1].conclusion')" = "escalate→develop" ] && ok "history 记一笔升级" || no "history 升级留痕"
# 升级后真能按 develop 走到 propose(原 bug 走不到的阶段)
( cd "$WBE" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(mphase "$WBE")" = "propose" ] && ok "升级后 investigate→propose(develop 路打通)" || no "升级后走 develop ($(mphase "$WBE"))"
# 已是 develop 再 escalate 被拒;非法目标被拒
if ( cd "$WBE" && bash "$PREPARE" escalate --to develop >/dev/null 2>&1 ); then no "重复升级被拒"; else ok "已是 develop 再升级被拒"; fi
if ( cd "$WBE" && bash "$PREPARE" escalate --to bogus >/dev/null 2>&1 ); then no "非法目标被拒"; else ok "非法升级目标被拒"; fi

# ===== C: 返工 + 上限拦截 =====
WC="$(newtask develop 2026-06-28-task-c)"
( cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
[ "$(mfield "$WC" repair_count)" = "1" ] && ok "返工计数=1" || no "返工计数=1"
[ "$(mphase "$WC")" = "investigate" ] && ok "返工原地不挪阶段" || no "返工原地"
( cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
OUTC="$(cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair)"
echo "$OUTC" | grep -q "STATUS=blocked" && ok "返工超上限(>2)→blocked" || no "返工超上限"
WC2="$(newtask develop 2026-06-28-task-c2)"
( cd "$WC2" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
( cd "$WC2" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(mfield "$WC2" repair_count)" = "0" ] && ok "进下一阶段返工计数清零" || no "返工清零"

# ===== D: needs-context 停下等用户 =====
WD="$(newtask develop 2026-06-28-task-d)"
OUTD="$(cd "$WD" && bash "$FLOW" handoff --conclusion needs-context)"
echo "$OUTD" | grep -q "STATUS=waiting-user" && ok "缺输入→waiting-user" || no "waiting-user"
[ "$(mphase "$WD")" = "investigate" ] && ok "等用户时阶段不动" || no "等用户阶段不动"

# ===== E: fail-closed =====
WE="$(newtask develop 2026-06-28-task-e)"
if ( cd "$WE" && bash "$FLOW" handoff >/dev/null 2>&1 ); then no "缺结论被拒"; else ok "缺结论被拒(fail-closed)"; fi
if ( cd "$WE" && bash "$FLOW" handoff --conclusion bogus >/dev/null 2>&1 ); then no "非法结论词被拒"; else ok "非法结论词被拒"; fi
if ( cd "$WE" && bash "$FLOW" spinoff --tag nope --finding x >/dev/null 2>&1 ); then no "非法 tag 被拒"; else ok "非法 tag 被拒"; fi

# ===== D2: needs-redirection --to-phase 回上游任一指定阶段 =====
WD2="$(newtask develop 2026-06-28-task-d2)"
( cd "$WD2" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # investigate→propose
( cd "$WD2" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # propose→design
( cd "$WD2" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # design→①审闸
( cd "$WD2" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # ①审过→to-issue
( cd "$WD2" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # to-issue→plan
[ "$(mphase "$WD2")" = "plan" ] && ok "D2 到 plan" || no "D2 到 plan ($(mphase "$WD2"))"
( cd "$WD2" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase design >/dev/null )
[ "$(mphase "$WD2")" = "design" ] && ok "掉头 --to-phase design 回到 design(非首阶段)" || no "to-phase design ($(mphase "$WD2"))"
[ "$(mfield "$WD2" phase_index)" = "2" ] && ok "--to-phase 回到正确下标" || no "to-phase 下标"
# 不带 --to-phase 默认回首阶段
WD3="$(newtask develop 2026-06-28-task-d3)"
( cd "$WD3" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # →design
( cd "$WD3" && bash "$FLOW" handoff --conclusion needs-redirection >/dev/null )  # 无 to-phase
[ "$(mphase "$WD3")" = "investigate" ] && ok "无 --to-phase 默认回首阶段" || no "默认首阶段"
# --to-phase 非法(不在 phases / 往前跳)被拒
WD4="$(newtask develop 2026-06-28-task-d4)"
( cd "$WD4" && bash "$FLOW" handoff --conclusion pass >/dev/null )        # →design(idx1)
if ( cd "$WD4" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase nope >/dev/null 2>&1 ); then no "to-phase 不存在被拒"; else ok "to-phase 不存在被拒"; fi
if ( cd "$WD4" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase build >/dev/null 2>&1 ); then no "to-phase 往前跳被拒"; else ok "to-phase 往前跳被拒(只能上游)"; fi

# ===== F: small-change 只走 build→verify→closing(验证预设开关) =====
WSC="$(newtask small-change 2026-06-28-task-sc)"
[ "$(mphase "$WSC")" = "build" ] && ok "small-change 起于 build(前置全关)" || no "small-change 起于 build ($(mphase "$WSC"))"
[ "$(mfield "$WSC" 'phases|length')" = "3" ] && ok "small-change 只 3 个阶段" || no "small-change 3 阶段"

# ===== G: 断点恢复 =====
WF="$(newtask develop 2026-06-28-task-f)"
( cd "$WF" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # investigate→propose
WHERE="$(cd "$WF" && bash "$FLOW" where)"
echo "$WHERE" | grep -q "phase=propose" && ok "where 报精确阶段" || no "where 精确阶段"
echo "$WHERE" | grep -q "phase_index=1" && ok "where 报精确下标" || no "where 下标"
# then 的 produced 必须解析掉 <slug> 模板,直接可粘贴跑(不让 agent 手搓)
echo "$WHERE" | grep "^then=" | grep -q "<slug>" && no "then 仍含字面 <slug>" \
  || { echo "$WHERE" | grep "^then=" | grep -q "2026-06-28-task-f-direction.md" && ok "then 已解析真 slug" || no "then 未解析 slug"; }
RES="$(cd "$WF" && bash "$PREPARE" resume 2>/dev/null)"
echo "$RES" | head -1 | grep -q "MANAGED" && echo "$RES" | tail -n +2 | jq -e '.phase=="propose"' >/dev/null \
  && ok "resume 读到 propose(断点续传)" || no "resume 断点续传"

# ===== H: design 跨两阶接力单(reads = investigate + propose 都进 prev_outputs) =====
WH="$(newtask develop 2026-06-29-task-h)"
( cd "$WH" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/2026-06-29-task-h.md >/dev/null )  # investigate→propose
( cd "$WH" && bash "$FLOW" handoff --conclusion pass --produced docs/design/2026-06-29-task-h-direction.md >/dev/null )  # propose→design
WHD="$(cd "$WH" && bash "$FLOW" where)"
PREVH="$(echo "$WHD" | sed -n 's/^prev_outputs=//p')"
echo "$WHD" | grep -q "phase=design" || no "task-h 应在 design"
echo "$PREVH" | jq -e 'index("docs/investigating/2026-06-29-task-h.md")!=null and index("docs/design/2026-06-29-task-h-direction.md")!=null' >/dev/null \
  && ok "design prev_outputs 含 现状报告 + 方向(跨两阶接力)" || no "design prev_outputs 漏上游 ($PREVH)"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
