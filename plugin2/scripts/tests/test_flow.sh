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

( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/design.md >/dev/null )  # investigate→design
[ "$(mphase "$WA")" = "design" ] && ok "investigate pass→design" || no "investigate→design ($(mphase "$WA"))"
[ "$(mfield "$WA" 'artifacts|length')" = "1" ] && ok "产出登记进 artifacts" || no "产出登记"
# 接力单:产出钉进 phase_outputs[investigate],下阶段 where 照单读
[ "$(mfield "$WA" 'phase_outputs.investigate[0]')" = "docs/design.md" ] && ok "产出钉进接力单 phase_outputs[investigate]" || no "接力单钉死"
WPO="$(cd "$WA" && bash "$FLOW" where)"
echo "$WPO" | grep -q 'prev_outputs=\["docs/design.md"\]' && ok "where 报上阶段产出(prev_outputs 照单读)" || no "prev_outputs 照单读"

( cd "$WA" && bash "$FLOW" spinoff --tag bug --finding "中途挖到登录态丢失" >/dev/null )
[ "$(mfield "$WA" 'subtasks|length')" = "1" ] && ok "甩支线→子任务登记" || no "甩支线登记"
[ "$(mphase "$WA")" = "design" ] && ok "甩支线后主流程不动" || no "甩支线后主流程不动"

# design 产物过 → 进 ①审闸(phase 不动,gate=design)
OUTG="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass)"       # design→gate:design
echo "$OUTG" | grep -q "NEXT_ACTION=review" && ok "design pass→进审闸(review)" || no "design→审闸"
echo "$OUTG" | grep -q "REVIEW_STAGE=design" && ok "审闸报阶段 design" || no "REVIEW_STAGE"
[ "$(mphase "$WA")" = "design" ] && ok "审闸里 phase 不动" || no "审闸 phase 不动 ($(mphase "$WA"))"
[ "$(mfield "$WA" gate)" = "design" ] && ok "gate=design" || no "gate=design ($(mfield "$WA" gate))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # ①审 verdict pass → plan
[ "$(mphase "$WA")" = "plan" ] && ok "①审过→进 plan" || no "①审过→plan ($(mphase "$WA"))"
[ "$(mfield "$WA" gate)" = "null" ] && ok "进下一阶段 gate 清空" || no "gate 清空 ($(mfield "$WA" gate))"

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
[ "$(mfield "$WA" 'history|length')" = "8" ] && ok "history 记满 8 步(含两审闸)" || no "history 8 步 ($(mfield "$WA" 'history|length'))"

# ===== A2: 审打回 → 清 gate 回该阶段返工 =====
WA2="$(newtask develop 2026-06-28-task-a2)"
( cd "$WA2" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # investigate→design
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

# ===== F: small-change 只走 build→verify→closing(验证预设开关) =====
WSC="$(newtask small-change 2026-06-28-task-sc)"
[ "$(mphase "$WSC")" = "build" ] && ok "small-change 起于 build(前置全关)" || no "small-change 起于 build ($(mphase "$WSC"))"
[ "$(mfield "$WSC" 'phases|length')" = "3" ] && ok "small-change 只 3 个阶段" || no "small-change 3 阶段"

# ===== G: 断点恢复 =====
WF="$(newtask develop 2026-06-28-task-f)"
( cd "$WF" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # investigate→design
WHERE="$(cd "$WF" && bash "$FLOW" where)"
echo "$WHERE" | grep -q "phase=design" && ok "where 报精确阶段" || no "where 精确阶段"
echo "$WHERE" | grep -q "phase_index=1" && ok "where 报精确下标" || no "where 下标"
RES="$(cd "$WF" && bash "$PREPARE" resume 2>/dev/null)"
echo "$RES" | head -1 | grep -q "MANAGED" && echo "$RES" | tail -n +2 | jq -e '.phase=="design"' >/dev/null \
  && ok "resume 读到 design(断点续传)" || no "resume 断点续传"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
