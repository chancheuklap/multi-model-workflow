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

# ===== A: new-design 全程空跑 + 中途甩支线 (design→plan→build→verify→closing) =====
WA="$(newtask new-design 2026-06-28-task-a)"
[ "$(mphase "$WA")" = "design" ] && ok "A 起于 design" || no "A 起于 design ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/design.md >/dev/null )
[ "$(mphase "$WA")" = "plan" ] && ok "design pass→plan" || no "design→plan ($(mphase "$WA"))"
[ "$(mfield "$WA" 'artifacts|length')" = "1" ] && ok "产出登记进 artifacts" || no "产出登记"

( cd "$WA" && bash "$FLOW" spinoff --tag bug --finding "中途挖到登录态丢失" >/dev/null )
[ "$(mfield "$WA" 'subtasks|length')" = "1" ] && ok "甩支线→子任务登记" || no "甩支线登记"
[ "$(mphase "$WA")" = "plan" ] && ok "甩支线后主流程不动" || no "甩支线后主流程不动"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # plan→build
( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # build→verify
[ "$(mphase "$WA")" = "verify" ] && ok "plan→build→verify" || no "推进到 verify ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # verify→closing
[ "$(mphase "$WA")" = "closing" ] && ok "→closing" || no "→closing"
OUT="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass)"        # closing→ready-to-close
echo "$OUT" | grep -q "STATUS=ready-to-close" && ok "末阶段 pass→ready-to-close" || no "ready-to-close"
echo "$OUT" | grep -q "NEXT_ACTION=done" && ok "末阶段 NEXT=done" || no "NEXT=done"
[ "$(mfield "$WA" 'history|length')" = "5" ] && ok "history 记满 5 步" || no "history 5 步 ($(mfield "$WA" 'history|length'))"

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
WC="$(newtask new-design 2026-06-28-task-c)"
( cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
[ "$(mfield "$WC" repair_count)" = "1" ] && ok "返工计数=1" || no "返工计数=1"
[ "$(mphase "$WC")" = "design" ] && ok "返工原地不挪阶段" || no "返工原地"
( cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
OUTC="$(cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair)"
echo "$OUTC" | grep -q "STATUS=blocked" && ok "返工超上限(>2)→blocked" || no "返工超上限"
WC2="$(newtask new-design 2026-06-28-task-c2)"
( cd "$WC2" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
( cd "$WC2" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(mfield "$WC2" repair_count)" = "0" ] && ok "进下一阶段返工计数清零" || no "返工清零"

# ===== D: needs-context 停下等用户 =====
WD="$(newtask new-design 2026-06-28-task-d)"
OUTD="$(cd "$WD" && bash "$FLOW" handoff --conclusion needs-context)"
echo "$OUTD" | grep -q "STATUS=waiting-user" && ok "缺输入→waiting-user" || no "waiting-user"
[ "$(mphase "$WD")" = "design" ] && ok "等用户时阶段不动" || no "等用户阶段不动"

# ===== E: fail-closed =====
WE="$(newtask new-design 2026-06-28-task-e)"
if ( cd "$WE" && bash "$FLOW" handoff >/dev/null 2>&1 ); then no "缺结论被拒"; else ok "缺结论被拒(fail-closed)"; fi
if ( cd "$WE" && bash "$FLOW" handoff --conclusion bogus >/dev/null 2>&1 ); then no "非法结论词被拒"; else ok "非法结论词被拒"; fi
if ( cd "$WE" && bash "$FLOW" spinoff --tag nope --finding x >/dev/null 2>&1 ); then no "非法 tag 被拒"; else ok "非法 tag 被拒"; fi

# ===== F: small-change 只走 build→verify→closing(验证预设开关) =====
WSC="$(newtask small-change 2026-06-28-task-sc)"
[ "$(mphase "$WSC")" = "build" ] && ok "small-change 起于 build(前置全关)" || no "small-change 起于 build ($(mphase "$WSC"))"
[ "$(mfield "$WSC" 'phases|length')" = "3" ] && ok "small-change 只 3 个阶段" || no "small-change 3 阶段"

# ===== G: 断点恢复 =====
WF="$(newtask new-design 2026-06-28-task-f)"
( cd "$WF" && bash "$FLOW" handoff --conclusion pass >/dev/null )  # design→plan
WHERE="$(cd "$WF" && bash "$FLOW" where)"
echo "$WHERE" | grep -q "phase=plan" && ok "where 报精确阶段" || no "where 精确阶段"
echo "$WHERE" | grep -q "phase_index=1" && ok "where 报精确下标" || no "where 下标"
RES="$(cd "$WF" && bash "$PREPARE" resume 2>/dev/null)"
echo "$RES" | head -1 | grep -q "MANAGED" && echo "$RES" | tail -n +2 | jq -e '.phase=="plan"' >/dev/null \
  && ok "resume 读到 plan(断点续传)" || no "resume 断点续传"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
