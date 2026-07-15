#!/usr/bin/env bash
# flow.sh 骨架空跑:每阶段只回个结论词,验证引擎换阶段对、分叉掉头对、警告留痕、断点能续。
# 流程模型:一条主干 + 预设开关。阶段词=投/想/设计/切/拆/落/收(investigate/propose/design/to-issue/plan/build/closing)。
# 审闸 map(routes.review_gates):plan→②/build→④;design 出口是唯一人闸 mmw approve(/approve-design),不走 handoff pass。
# 机器否决权只认白名单:审闸留痕硬核、设计确认指纹、package exit-check;其余判断层问题一律 WARN 留痕不拒收。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.factory/multi-model-workflow}"
WT_REL="${WT_REL:-.factory/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
FLOW="$SCRIPT_DIR/../flow.sh"
LOOP="$SCRIPT_DIR/../loop.sh"
NOTE="$SCRIPT_DIR/../note.sh"
PACKAGE="$SCRIPT_DIR/../package-phase.sh"
PACKAGE_FIXTURES="$SCRIPT_DIR/fixtures/package-phase"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_flow.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export UV_CACHE_DIR="${UV_CACHE_DIR:-$TMP/uv-cache}"
cd "$TMP"
git init -q; git config user.email t@t; git config user.name t
echo seed > seed.txt; git add -A; git commit -qm seed

newtask() { # preset slug -> echoes worktree path
  bash "$PREPARE" new --scenario "$1" --slug "$2" --title "t-$2" --request "request-$2" 2>/dev/null \
    | grep '^worktree_path=' | cut -d= -f2-
}
mphase() { jq -r .phase "$1/${STATE_SUBDIR}/task.json"; }
mfield() { jq -r ".$2" "$1/${STATE_SUBDIR}/task.json"; }
mkf() { mkdir -p "$1/$(dirname "$2")"; : > "$1/$2"; }
mkd() { mkdir -p "$1/$2"; }
hrange() { (cd "$1" && echo "$(git rev-parse HEAD)..HEAD"); }
# 审闸收口硬核 = docs/reviews/<slug>-<stage>.md 存在且含 verdict(留痕即证据,报告在=审真跑过)。
# 空跑不经 review.sh,这里把留痕落盘再 pass。$2+ 透传给 handoff(如 --produced)。
gate_trace() { # $1=wt:按当前 gate 写审查留痕
  local wt="$1" gate stage slug
  gate="$(jq -r .gate "$wt/${STATE_SUBDIR}/task.json")"
  slug="$(jq -r .slug "$wt/${STATE_SUBDIR}/task.json")"
  case "$gate" in plan) stage=plan;; build) stage=final;; *) echo "gate_trace: 不在审闸($gate)" >&2; return 1;; esac
  mkdir -p "$wt/docs/reviews"
  printf '# review findings\n\n## verdict\npass\n' > "$wt/docs/reviews/$slug-$stage.md"
}
gate_verdict_pass() {
  local wt="$1"; shift
  gate_trace "$wt"
  ( cd "$wt" && bash "$FLOW" handoff --conclusion pass "$@" >/dev/null )
}
# design 过门:承重文档落盘(带内容)→ mmw approve(唯一人闸;空跑代用户敲)
approve_design() { # $1=wt $2=报告相对路径
  mkdir -p "$1/$(dirname "$2")"; printf '# design\nsettled design\n' > "$1/$2"
  ( cd "$1" && bash "$NOTE" approve --report "$2" >/dev/null )
}
init_empty_package() {
  mkdir -p "$1/fixtures"
  cp -R "$PACKAGE_FIXTURES/." "$1/fixtures/"
  (cd "$1" && bash "$PACKAGE" init --scope fixtures/generic.release-package-scope.json)
}

# ===== A: develop 全程空跑 + 中途甩支线 (investigate→propose→design(人闸)→to-issue→plan(②闸)→build(④闸)→package→closing) =====
WA="$(newtask develop 2026-06-28-task-a)"
[ "$(mphase "$WA")" = "investigate" ] && ok "A 起于 investigate" || no "A 起于 investigate ($(mphase "$WA"))"

mkf "$WA" docs/ctx.md
( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/ctx.md >/dev/null )  # investigate→propose
[ "$(mphase "$WA")" = "propose" ] && ok "investigate pass→propose" || no "investigate→propose ($(mphase "$WA"))"
[ "$(mfield "$WA" 'artifacts|length')" = "1" ] && ok "产出登记进 artifacts" || no "产出登记"
[ "$(mfield "$WA" 'phase_outputs.investigate[0]')" = "docs/ctx.md" ] && ok "产出钉进接力单 phase_outputs[investigate]" || no "接力单钉死"
WPO="$(cd "$WA" && bash "$FLOW" where)"
echo "$WPO" | grep -q 'prev_outputs=\["docs/ctx.md"\]' && ok "where 报上阶段产出(prev_outputs 照单读)" || no "prev_outputs 照单读"

mkf "$WA" docs/dir.md
( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/dir.md >/dev/null )  # propose→design(给方案选定→进设计)
[ "$(mphase "$WA")" = "design" ] && ok "propose pass→design" || no "propose→design ($(mphase "$WA"))"

( cd "$WA" && bash "$FLOW" spinoff --tag bug --finding "中途挖到登录态丢失" >/dev/null )
[ "$(mfield "$WA" 'subtasks|length')" = "1" ] && ok "甩支线→子任务登记" || no "甩支线登记"
[ "$(mphase "$WA")" = "design" ] && ok "甩支线后主流程不动" || no "甩支线后主流程不动"

# design 出口 = 唯一人闸 mmw approve:盖指纹 + 钉接力单 + attendance→afk + 推进 to-issue
[ "$(mfield "$WA" attendance)" = "attended" ] && ok "develop 讨论态 attended" || no "讨论态 attended ($(mfield "$WA" attendance))"
APR="$(mkdir -p "$WA/docs/design"; printf '# design\nsettled\n' > "$WA/docs/design/a.md"; cd "$WA" && bash "$NOTE" approve --report docs/design/a.md)"
echo "$APR" | grep -q "^APPROVED fingerprint=" && ok "approve 回执带指纹" || no "approve 指纹回执"
echo "$APR" | grep -q "NEXT_PHASE=to-issue" && ok "approve 过门→to-issue" || no "approve NEXT_PHASE"
[ "$(mphase "$WA")" = "to-issue" ] && ok "过门后 phase=to-issue" || no "过门 phase ($(mphase "$WA"))"
[ "$(mfield "$WA" attendance)" = "afk" ] && ok "过门自动切 afk(放权自主跑)" || no "过门切 afk ($(mfield "$WA" attendance))"
[ "$(mfield "$WA" 'approval.fingerprint')" != "null" ] && ok "approval 指纹落盘" || no "approval 落盘"
[ "$(mfield "$WA" 'phase_outputs.design[0]')" = "docs/design/a.md" ] && ok "承重文档钉进 design 接力单" || no "approve 钉接力单"

mkd "$WA" docs/issues/a
( cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/a/ >/dev/null )  # to-issue→plan(无审闸)
[ "$(mphase "$WA")" = "plan" ] && ok "to-issue→进 plan(无审闸)" || no "to-issue→plan ($(mphase "$WA"))"

mkd "$WA" docs/plans/a
OUTG="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/a/)"       # plan→gate:plan
echo "$OUTG" | grep -q "NEXT_ACTION=review" && ok "plan pass→进 ②审闸(review)" || no "plan→审闸"
echo "$OUTG" | grep -q "REVIEW_STAGE=plan" && ok "审闸报阶段 plan" || no "REVIEW_STAGE"
[ "$(mphase "$WA")" = "plan" ] && ok "审闸里 phase 不动" || no "审闸 phase 不动 ($(mphase "$WA"))"
[ "$(mfield "$WA" gate)" = "plan" ] && ok "gate=plan" || no "gate=plan ($(mfield "$WA" gate))"
# where 在审闸里吐 review_start + review_trace(收口硬核路径,引擎给命令不靠散文猜)
WPG="$(cd "$WA" && bash "$FLOW" where)"
echo "$WPG" | grep "review_start=" | grep -q -- "review start --stage plan" && ok "②闸 where 吐 review_start --stage plan" || no "review_start plan ($(echo "$WPG" | grep review_start))"
echo "$WPG" | grep -q "review_trace=docs/reviews/2026-06-28-task-a-plan.md" && ok "where 吐 review_trace 落点" || no "review_trace 行"
# 审闸收口硬核:无留痕 → pass 被拒;留痕无 verdict → 仍被拒;齐了才放行
if ( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 ); then no "无审查留痕 gate pass 该被拒"; else ok "无审查留痕 → gate pass 被拒(写者≠审者证据面)"; fi
mkdir -p "$WA/docs/reviews"; printf '# findings only\n' > "$WA/docs/reviews/2026-06-28-task-a-plan.md"
if ( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 ); then no "留痕无 verdict gate pass 该被拒"; else ok "留痕无 verdict → gate pass 被拒"; fi
printf '# findings\n\n## verdict\npass\n' > "$WA/docs/reviews/2026-06-28-task-a-plan.md"
( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )   # ②审过→build
[ "$(mphase "$WA")" = "build" ] && ok "②审过→进 build" || no "②审过→build ($(mphase "$WA"))"
[ "$(mfield "$WA" gate)" = "null" ] && ok "进下一阶段 gate 清空" || no "gate 清空 ($(mfield "$WA" gate))"

# build 产物过 → 进 ④终审闸
OUTBG="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass --produced "$(hrange "$WA")")"      # build→gate:build
echo "$OUTBG" | grep -q "NEXT_ACTION=review" && ok "build pass→进 ④终审闸(review)" || no "build→审闸"
echo "$OUTBG" | grep -q "REVIEW_STAGE=build" && ok "审闸报阶段 build" || no "build REVIEW_STAGE"
[ "$(mfield "$WA" gate)" = "build" ] && ok "gate=build" || no "gate=build ($(mfield "$WA" gate))"
WBG="$(cd "$WA" && bash "$FLOW" where)"
echo "$WBG" | grep "review_start=" | grep -q -- "review start --stage final" && ok "④闸 where 吐 review_start --stage final" || no "review_start final ($(echo "$WBG" | grep review_start))"

mkf "$WA" docs/2026-06-28-task-a-final-review.md
gate_verdict_pass "$WA" --produced docs/2026-06-28-task-a-final-review.md  # ④审过→package(④闸要钉终审报告)
[ "$(mphase "$WA")" = "package" ] && ok "④审过→package" || no "④审过→package ($(mphase "$WA"))"
echo "$(cd "$WA" && bash "$FLOW" where)" | grep -q 'load=references/package.md' && ok "package 阶段加载唯一操作指引" || no "package load"
if ( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 ); then no "package 无 state 时 pass 应被拒"; else ok "package 无 state 时 pass 被拒(release 子系统机器核)"; fi
init_empty_package "$WA" >/dev/null
[ "$(cd "$WA" && bash "$PACKAGE" exit-check)" = "DONE" ] && ok "空 package state 可交接" || no "空 package exit-check"
( cd "$WA" && bash "$FLOW" handoff --conclusion pass >/dev/null )
[ "$(mphase "$WA")" = "closing" ] && ok "完成 package 后→closing" || no "package→closing ($(mphase "$WA"))"
OUT="$(cd "$WA" && bash "$FLOW" handoff --conclusion pass)"        # closing→ready-to-close
echo "$OUT" | grep -q "STATUS=ready-to-close" && ok "末阶段 pass→ready-to-close" || no "ready-to-close"
echo "$OUT" | grep -q "NEXT_ACTION=done" && ok "末阶段 NEXT=done" || no "NEXT=done"
[ "$(mfield "$WA" 'history|length')" = "9" ] && ok "history 记 9 笔 handoff(approve 过门不占 handoff 账)" || no "history 笔数 ($(mfield "$WA" 'history|length'))"

# ===== W: 产出校验降警告(不拒收,缺口摆到明面) =====
WW="$(newtask develop 2026-06-28-task-w)"
OWW="$(cd "$WW" && bash "$FLOW" handoff --conclusion pass)"   # investigate 声明产出但空手 pass
echo "$OWW" | grep -q "WARN=.*没钉" && ok "空手 pass → WARN 留痕(不拒收)" || no "空手 WARN ($OWW)"
[ "$(mphase "$WW")" = "propose" ] && ok "空手 pass 仍推进(判断是 agent 的)" || no "空手仍推进 ($(mphase "$WW"))"
OWW2="$(cd "$WW" && bash "$FLOW" handoff --conclusion pass --produced docs/ghost.md)"   # 幽灵路径
echo "$OWW2" | grep -q "WARN=.*不存在" && ok "幽灵路径 → WARN 提示补钉" || no "幽灵 WARN ($OWW2)"
[ "$(mphase "$WW")" = "design" ] && ok "幽灵路径不拦推进" || no "幽灵仍推进 ($(mphase "$WW"))"
[ "$(mfield "$WW" 'phase_outputs.propose')" = "null" ] && ok "幽灵路径不进接力单(接力单必须真实)" || no "幽灵进了接力单"
# pin 补钉:产物就绪后补登记(不推进);幽灵 die
mkf "$WW" docs/design/w-dir.md
( cd "$WW" && bash "$FLOW" pin --phase propose --produced docs/design/w-dir.md >/dev/null )
[ "$(mfield "$WW" 'phase_outputs.propose[0]')" = "docs/design/w-dir.md" ] && ok "pin --phase 补钉指定阶段" || no "pin 补钉"
[ "$(mphase "$WW")" = "design" ] && ok "pin 只登记不推进" || no "pin 不该推进"
if ( cd "$WW" && bash "$FLOW" pin --produced docs/nothing.md >/dev/null 2>&1 ); then no "pin 幽灵路径该被拒"; else ok "pin 幽灵路径被拒(fail-closed)"; fi

# ===== AP: 设计确认指纹(白名单第 4 条:确认的是 A 就不许执行 B) =====
WAP="$(newtask develop 2026-06-28-task-ap)"
mkf "$WAP" docs/i.md; mkf "$WAP" docs/p.md
( cd "$WAP" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
( cd "$WAP" && bash "$FLOW" handoff --conclusion pass --produced docs/p.md >/dev/null )
approve_design "$WAP" docs/design/ap.md          # 过门→to-issue
[ "$(mphase "$WAP")" = "to-issue" ] || no "AP 过门失败"
( cd "$WAP" && bash "$FLOW" where ) | grep -q "approval_stale" && no "未改不该报 approval_stale" || ok "承重文档没改:where 不报 approval_stale"
echo "CHANGED after approval" >> "$WAP/docs/design/ap.md"       # 过门后改承重文档
( cd "$WAP" && bash "$FLOW" where ) | grep -q "approval_stale=" && ok "过门后改设计→where 提前亮 approval_stale" || no "approval_stale 未报"
mkd "$WAP" docs/issues/ap
if ( cd "$WAP" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/ap/ >/dev/null 2>&1 ); then no "指纹不符 pass 该硬停"; else ok "指纹不符 → pass 硬停(交用户重确认)"; fi
[ "$(mphase "$WAP")" = "to-issue" ] && ok "硬停后 phase 不动" || no "硬停 phase ($(mphase "$WAP"))"
# 用户重新确认(过门后重跑 approve = RE-APPROVED,只重盖指纹不动阶段/值守)
RAP="$(cd "$WAP" && bash "$NOTE" approve --report docs/design/ap.md)"
echo "$RAP" | grep -q "RE-APPROVED" && ok "修订后重 approve → RE-APPROVED" || no "RE-APPROVED ($RAP)"
[ "$(mphase "$WAP")" = "to-issue" ] && ok "RE-APPROVED 不动阶段" || no "RE-APPROVED 阶段 ($(mphase "$WAP"))"
( cd "$WAP" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/ap/ >/dev/null )
[ "$(mphase "$WAP")" = "plan" ] && ok "重盖指纹后 pass 放行" || no "重盖后放行 ($(mphase "$WAP"))"
# 目录形态承重文档:目录内文件改动同样触发 stale
WAD="$(newtask develop 2026-06-28-task-ad)"
mkf "$WAD" docs/i.md
( cd "$WAD" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
( cd "$WAD" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 )   # 空手到 design(WARN 已单测)
mkdir -p "$WAD/docs/design/ad"; printf 'main\n' > "$WAD/docs/design/ad/main.md"
( cd "$WAD" && bash "$NOTE" approve --report docs/design/ad >/dev/null )
echo 'more' >> "$WAD/docs/design/ad/main.md"
( cd "$WAD" && bash "$FLOW" where ) | grep -q "approval_stale=" && ok "目录承重:内文件改动也触发 stale" || no "目录指纹未覆盖"
# approve fail-closed:承重文档不存在/为空 → 拒;非 design 且从未确认 → 无门可过
if ( cd "$WAD" && bash "$NOTE" approve --report docs/design/none.md >/dev/null 2>&1 ); then no "approve 幽灵报告该被拒"; else ok "approve 承重文档不存在被拒"; fi
WBGT="$(newtask bug 2026-06-28-task-apx)"
mkf "$WBGT" docs/x.md
if ( cd "$WBGT" && bash "$NOTE" approve --report docs/x.md >/dev/null 2>&1 ); then no "非 design 未确认过 approve 该被拒"; else ok "非 design 且未确认过 → 无门可过被拒"; fi
# approve 缺 --report 回落 design 已钉产出
WAF="$(newtask develop 2026-06-28-task-af)"
mkf "$WAF" docs/i.md
( cd "$WAF" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
( cd "$WAF" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1 )   # →design
mkdir -p "$WAF/docs/design"; printf 'design body\n' > "$WAF/docs/design/af.md"
( cd "$WAF" && bash "$FLOW" pin --produced docs/design/af.md >/dev/null )
( cd "$WAF" && bash "$NOTE" approve >/dev/null )
[ "$(mphase "$WAF")" = "to-issue" ] && ok "approve 缺 --report 回落已钉设计产出" || no "approve 回落 ($(mphase "$WAF"))"

# ===== B: 掉头默认回上一阶段 + 无上限(警告不锁死) + 剪下游接力单 =====
WB="$(newtask bug 2026-06-28-task-b)"
OUTB="$(cd "$WB" && bash "$FLOW" handoff --conclusion needs-redirection)"
echo "$OUTB" | grep -q "NEXT_ACTION=turn-around" && ok "掉头动作" || no "掉头动作"
[ "$(mphase "$WB")" = "investigate" ] && ok "首阶段掉头原地(无更上游)" || no "首阶段掉头 ($(mphase "$WB"))"
[ "$(mfield "$WB" turnaround_count)" = "1" ] && ok "掉头计数=1" || no "掉头计数"
OUTB2="$(cd "$WB" && bash "$FLOW" handoff --conclusion needs-redirection)"
echo "$OUTB2" | grep -q "STATUS=blocked" && no "掉头不该锁死(讨论态自由往返)" || ok "第 2 次掉头不锁死"
echo "$OUTB2" | grep -q "WARN=.*掉头" && ok "第 2 次掉头带 WARN(先向用户讲清)" || no "掉头 WARN ($OUTB2)"
# 默认回上一阶段(不是首阶段)+ 剪下游 phase_outputs
WPR="$(newtask develop 2026-06-28-task-pr)"
mkf "$WPR" docs/i.md; mkf "$WPR" docs/p.md
( cd "$WPR" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )   # →propose
( cd "$WPR" && bash "$FLOW" handoff --conclusion pass --produced docs/p.md >/dev/null )   # →design
approve_design "$WPR" docs/design/pr.md                                                   # →to-issue
mkd "$WPR" docs/issues/pr
( cd "$WPR" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/pr/ >/dev/null )  # →plan
( cd "$WPR" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase design >/dev/null )  # plan 指定回 design
[ "$(mphase "$WPR")" = "design" ] && ok "--to-phase design 回指定上游" || no "to-phase design ($(mphase "$WPR"))"
[ "$(mfield "$WPR" phase_index)" = "2" ] && ok "--to-phase 回到正确下标" || no "to-phase 下标"
[ "$(mfield "$WPR" 'phase_outputs["to-issue"]')" = "null" ] && ok "掉头剪目标下游接力单(to-issue 产出已过期)" || no "剪下游 to-issue"
[ "$(mfield "$WPR" 'phase_outputs.design[0]')" = "docs/design/pr.md" ] && ok "掉头保留目标及上游接力单" || no "上游接力单误剪"
( cd "$WPR" && bash "$FLOW" handoff --conclusion needs-redirection >/dev/null )  # design 掉头,默认回上一阶段 propose
[ "$(mphase "$WPR")" = "propose" ] && ok "无 --to-phase 默认回上一阶段(不是首阶段)" || no "默认上一阶段 ($(mphase "$WPR"))"
[ "$(mfield "$WPR" 'phase_outputs.design')" = "null" ] && ok "默认掉头同样剪目标下游(design 产出剪掉)" || no "默认掉头剪 design"
# --to-phase 非法(不在 phases / 往前跳)被拒
if ( cd "$WPR" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase nope >/dev/null 2>&1 ); then no "to-phase 不存在被拒"; else ok "to-phase 不存在被拒"; fi
if ( cd "$WPR" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase build >/dev/null 2>&1 ); then no "to-phase 往前跳被拒"; else ok "to-phase 往前跳被拒(只能上游)"; fi

# package 的人工测试失败必须回 build,并删除旧 snapshot,避免新提交沿用旧目标列表。
WPKG="$(newtask develop 2026-07-11-package-redirection)"
jq '.phase="package" | .phase_index=6' "$WPKG/${STATE_SUBDIR}/task.json" > "$WPKG/task.json"
mv "$WPKG/task.json" "$WPKG/${STATE_SUBDIR}/task.json"
init_empty_package "$WPKG" >/dev/null
[ -f "$WPKG/${STATE_SUBDIR}/package-state.json" ] && ok "package 掉头前存在 snapshot" || no "package snapshot 未建"
( cd "$WPKG" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase build >/dev/null )
[ "$(mphase "$WPKG")" = "build" ] && ok "package needs-redirection→build" || no "package 掉头阶段 ($(mphase "$WPKG"))"
[ ! -e "$WPKG/${STATE_SUBDIR}/package-state.json" ] && ok "package→build 清除旧 snapshot" || no "package→build 应清除旧 snapshot"

# ===== B2: bug 系统性设计问题 → mmw task escalate --to develop(原地升级,投查成果留着) =====
WBE="$(newtask bug 2026-06-29-task-be)"
mkf "$WBE" docs/investigating/be.md
( cd "$WBE" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/be.md >/dev/null )
ESC="$(cd "$WBE" && bash "$PREPARE" escalate --to develop)"
echo "$ESC" | grep -q "ESCALATED from=bug to=develop" && ok "escalate bug→develop" || no "escalate 回执"
[ "$(mfield "$WBE" scenario)" = "develop" ] && ok "升级后 scenario=develop" || no "scenario 升级 ($(mfield "$WBE" scenario))"
[ "$(mfield "$WBE" 'phases|join(",")')" = "investigate,propose,design,to-issue,plan,build,package,closing" ] && ok "升级后 phases=develop 八阶段" || no "phases 升级"
[ "$(mphase "$WBE")" = "investigate" ] && [ "$(mfield "$WBE" phase_index)" = "0" ] && ok "游标回 investigate" || no "游标回首阶段"
[ "$(mfield "$WBE" 'phase_outputs.investigate[0]')" = "docs/investigating/be.md" ] && ok "投查成果保留(phase_outputs 不丢)" || no "投查成果丢失"
[ "$(mfield "$WBE" 'history[-1].conclusion')" = "escalate→develop" ] && ok "history 记一笔升级" || no "history 升级留痕"
mkf "$WBE" docs/investigating/be2.md
( cd "$WBE" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/be2.md >/dev/null )
[ "$(mphase "$WBE")" = "propose" ] && ok "升级后 investigate→propose(develop 路打通)" || no "升级后走 develop ($(mphase "$WBE"))"
if ( cd "$WBE" && bash "$PREPARE" escalate --to develop >/dev/null 2>&1 ); then no "重复升级被拒"; else ok "已是 develop 再升级被拒"; fi
if ( cd "$WBE" && bash "$PREPARE" escalate --to bogus >/dev/null 2>&1 ); then no "非法目标被拒"; else ok "非法升级目标被拒"; fi

# ===== C: 返工无上限(≥3 轮转汇报,不锁死) =====
WC="$(newtask develop 2026-06-28-task-c)"
( cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
[ "$(mfield "$WC" repair_count)" = "1" ] && ok "返工计数=1" || no "返工计数=1"
[ "$(mphase "$WC")" = "investigate" ] && ok "返工原地不挪阶段" || no "返工原地"
( cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
OUTC="$(cd "$WC" && bash "$FLOW" handoff --conclusion needs-repair)"
echo "$OUTC" | grep -q "STATUS=blocked" && no "返工不该锁死" || ok "第 3 轮返工不锁死"
echo "$OUTC" | grep -q "WARN=.*返工 3 轮" && ok "第 3 轮返工带 WARN(每轮向用户汇报)" || no "返工 WARN ($OUTC)"
[ "$(mfield "$WC" repair_count)" = "3" ] && ok "返工计数累到 3" || no "返工计数 3"
WC2="$(newtask develop 2026-06-28-task-c2)"
( cd "$WC2" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )
mkf "$WC2" docs/i.md
( cd "$WC2" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
[ "$(mfield "$WC2" repair_count)" = "0" ] && ok "进下一阶段返工计数清零" || no "返工清零"

# ===== D: needs-context 停下等用户(等什么必须落盘,冷启动靠它接上) =====
WD="$(newtask develop 2026-06-28-task-d)"
if ( cd "$WD" && bash "$FLOW" handoff --conclusion needs-context >/dev/null 2>&1 ); then
  no "needs-context 缺 --waiting-for 被拒"; else ok "needs-context 缺 --waiting-for 被拒(等什么必须落盘)"; fi
OUTD="$(cd "$WD" && bash "$FLOW" handoff --conclusion needs-context --waiting-for "线上库还是新库?")"
echo "$OUTD" | grep -q "STATUS=waiting-user" && ok "缺输入→waiting-user" || no "waiting-user"
[ "$(mphase "$WD")" = "investigate" ] && ok "等用户时阶段不动" || no "等用户阶段不动"
[ "$(mfield "$WD" waiting_for)" = "线上库还是新库?" ] && ok "waiting_for 落盘(跨会话可见)" || no "waiting_for 落盘"
WHD="$(cd "$WD" && bash "$FLOW" where)"
echo "$WHD" | grep -q "waiting_for=线上库还是新库?" && ok "where 报 waiting_for(冷启动先接问题)" || no "where 报 waiting_for"
echo "$WHD" | grep -q "是否回答了 waiting_for" && ok "where 的 do 指引先判用户是否已回答" || no "where do 指引"
( cd "$WD" && bash "$PREPARE" resume >/dev/null )
[ "$(mfield "$WD" waiting_for)" = "null" ] && ok "task resume 清 waiting_for" || no "resume 清 waiting_for"
if ( cd "$WD" && bash "$FLOW" handoff --conclusion pass --waiting-for x >/dev/null 2>&1 ); then
  no "--waiting-for 只许配 needs-context"; else ok "--waiting-for 配其他结论被拒"; fi

# ===== E: fail-closed(CLI 参数校验,不是判断审查) =====
WE="$(newtask develop 2026-06-28-task-e)"
if ( cd "$WE" && bash "$FLOW" handoff >/dev/null 2>&1 ); then no "缺结论被拒"; else ok "缺结论被拒(fail-closed)"; fi
if ( cd "$WE" && bash "$FLOW" handoff --conclusion bogus >/dev/null 2>&1 ); then no "非法结论词被拒"; else ok "非法结论词被拒"; fi
if ( cd "$WE" && bash "$FLOW" spinoff --tag nope --finding x >/dev/null 2>&1 ); then no "非法 tag 被拒"; else ok "非法 tag 被拒"; fi
if ( cd "$WE" && bash "$FLOW" step next >/dev/null 2>&1 ); then no "step 游标已拆,step next 该被拒"; else ok "step 游标已拆(方法顺序在 reference,不在引擎)"; fi

# ===== F: small-change 只走 build(④闸)→closing(验证预设开关) =====
WSC="$(newtask small-change 2026-06-28-task-sc)"
[ "$(mphase "$WSC")" = "build" ] && ok "small-change 起于 build(前置全关)" || no "small-change 起于 build ($(mphase "$WSC"))"
[ "$(mfield "$WSC" 'phases|length')" = "2" ] && ok "small-change 只 2 个阶段(build,closing)" || no "small-change 2 阶段"
( cd "$WSC" && bash "$FLOW" handoff --conclusion pass --produced "$(hrange "$WSC")" >/dev/null )  # build→gate:build
[ "$(mfield "$WSC" gate)" = "build" ] && ok "small-change build 也进 ④终审闸(放权不跳质量门)" || no "small-change build 闸 ($(mfield "$WSC" gate))"

# ===== G: 断点恢复 + 新鲜度戳 =====
WF="$(newtask develop 2026-06-28-task-f)"
mkf "$WF" docs/i.md
( cd "$WF" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
WHERE="$(cd "$WF" && bash "$FLOW" where)"
echo "$WHERE" | grep -q "phase=propose" && ok "where 报精确阶段" || no "where 精确阶段"
echo "$WHERE" | grep -q "phase_index=1" && ok "where 报精确下标" || no "where 下标"
echo "$WHERE" | grep "^then=" | grep -q "<slug>" && no "then 仍含字面 <slug>" \
  || { echo "$WHERE" | grep "^then=" | grep -q "2026-06-28-task-f-direction.md" && ok "then 已解析真 slug" || no "then 未解析 slug"; }
echo "$WHERE" | grep -q "stale_" && no "新任务不该报 stale" || ok "新任务 where 无新鲜度警告"
RES="$(cd "$WF" && bash "$PREPARE" resume 2>/dev/null)"
echo "$RES" | head -1 | grep -q "MANAGED" && echo "$RES" | tail -n +2 | jq -e '.phase=="propose"' >/dev/null \
  && ok "resume 读到 propose(断点续传)" || no "resume 断点续传"
# 白名单第 3 条:版本不符/超 7 天 → where 亮 stale(只提示 /reassess,不拒)
MF="$WF/${STATE_SUBDIR}/task.json"
jq '.plugin_version="0.0.1"' "$MF" > "$MF.tmp" && mv "$MF.tmp" "$MF"
WFS="$(cd "$WF" && bash "$FLOW" where)"
echo "$WFS" | grep -q "stale_version=0.0.1" && ok "版本不符 where 报 stale_version" || no "stale_version"
jq '.updated_at="2026-01-01T00:00:00Z"' "$MF" > "$MF.tmp" && mv "$MF.tmp" "$MF"
WFS2="$(cd "$WF" && bash "$FLOW" where)"
echo "$WFS2" | grep -q "stale_age=" && ok "超 7 天没动 where 报 stale_age" || no "stale_age"
echo "$WFS2" | grep -q "^phase=propose" && ok "stale 只警告,where 正常指路" || no "stale 不该拦 where"

# ===== H: design 跨两阶接力单(reads = investigate + propose 都进 prev_outputs) =====
WH="$(newtask develop 2026-06-29-task-h)"
mkf "$WH" docs/investigating/2026-06-29-task-h.md; mkf "$WH" docs/design/2026-06-29-task-h-direction.md
( cd "$WH" && bash "$FLOW" handoff --conclusion pass --produced docs/investigating/2026-06-29-task-h.md >/dev/null )
( cd "$WH" && bash "$FLOW" handoff --conclusion pass --produced docs/design/2026-06-29-task-h-direction.md >/dev/null )
WHD="$(cd "$WH" && bash "$FLOW" where)"
PREVH="$(echo "$WHD" | sed -n 's/^prev_outputs=//p')"
echo "$WHD" | grep -q "phase=design" || no "task-h 应在 design"
echo "$PREVH" | jq -e 'index("docs/investigating/2026-06-29-task-h.md")!=null and index("docs/design/2026-06-29-task-h-direction.md")!=null' >/dev/null \
  && ok "design prev_outputs 含 现状报告 + 方向(跨两阶接力)" || no "design prev_outputs 漏上游 ($PREVH)"
echo "$WHD" | grep -q "load=references/design/discussion.md" && ok "design load 讨论主指引(方法顺序在文内,无步游标)" || no "design load"
echo "$WHD" | grep -q "^step=" && no "where 不该再报 step 游标" || ok "where 无 step 游标行"

# ===== K: where 报执行账本(断点恢复)+ handoff 结论落定收束账本 =====
lf() { echo "$1/${STATE_SUBDIR}/loop-state.json"; }
WK="$(newtask small-change 2026-07-03-loopvis)"
( cd "$WK" && bash "$LOOP" init >/dev/null )
( cd "$WK" && bash "$LOOP" step add --id 1.1 --desc x >/dev/null )
WKW="$(cd "$WK" && bash "$FLOW" where)"
echo "$WKW" | grep -q "load=references/build-a.md" && ok "small-change build 阶段 load=build-a.md(脚本按 scenario 选模式)" || no "small-change load build-a"
echo "$WKW" | grep -q "inner_loop=execution" && ok "where 报 inner_loop=execution(账本可见)" || no "inner_loop ($(echo "$WKW"|grep inner_loop))"
echo "$WKW" | grep -q "inner_loop_state=steps=0/1 remaining=1.1" && ok "where 借 loop status 报账本进度(只报不当闸)" || no "inner_loop_state ($(echo "$WKW"|grep inner_loop_state))"
# 结论落定 = 账本收束(账本是记录不是闸,pass 不再被步账拦)
( cd "$WK" && bash "$FLOW" handoff --conclusion pass --produced "$(hrange "$WK")" >/dev/null )
[ ! -f "$(lf "$WK")" ] && ok "pass → loop close 收束账本(不当完工闸)" || no "loop-state 未清(残留)"
echo "$(cd "$WK" && bash "$FLOW" where)" | grep -q "inner_loop=" && no "清后 where 仍报 inner_loop(残留污染)" || ok "清后 where 无 inner_loop(无残留)"
# needs-context 是原地等 resume:保留账本现场,不清
WK2="$(newtask small-change 2026-07-03-loopkeep)"
( cd "$WK2" && bash "$LOOP" init >/dev/null )
( cd "$WK2" && bash "$FLOW" handoff --conclusion needs-context --waiting-for q >/dev/null )
[ -f "$(lf "$WK2")" ] && ok "needs-context 保留 loop-state(resume 续现场)" || no "needs-context 误清 loop"
[ "$(mfield "$WK2" status)" = "waiting-user" ] && ok "needs-context → status=waiting-user" || no "waiting-user 状态"
( cd "$WK2" && bash "$PREPARE" resume >/dev/null )
[ "$(mfield "$WK2" status)" = "active" ] && ok "task resume → 翻回 active" || no "resume 未翻 active ($(mfield "$WK2" status))"

# develop 到 build → 脚本给 build-b.md(派 Codex 模式),不与 small-change 同份
WBB="$(newtask develop 2026-07-03-modeb)"
mkf "$WBB" docs/i.md; mkf "$WBB" docs/p.md; mkd "$WBB" docs/issues/x; mkd "$WBB" docs/plans/x
( cd "$WBB" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )       # investigate→propose
( cd "$WBB" && bash "$FLOW" handoff --conclusion pass --produced docs/p.md >/dev/null )       # propose→design
approve_design "$WBB" docs/design/bb.md                                                       # design 人闸→to-issue
( cd "$WBB" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/x/ >/dev/null )  # to-issue→plan
( cd "$WBB" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/x/ >/dev/null )   # plan→②审闸
gate_verdict_pass "$WBB"                            # ②审过→build
[ "$(mphase "$WBB")" = "build" ] && ok "develop 一路到 build(人闸+②闸)" || no "develop 到 build ($(mphase "$WBB"))"
echo "$(cd "$WBB" && bash "$FLOW" where)" | grep -q "load=references/build-b.md" && ok "develop build 阶段 load=build-b.md(脚本按 scenario 选模式)" || no "develop load build-b"

# ===== 返修去重 + 审闸 review_start 多产物 =====
# plan 过闸→打回→再 pass 同一产出:phase_outputs 不重复累积(否则 review_start 参数炸)
WDD="$(newtask develop 2026-07-05-dedup)"
mkf "$WDD" docs/i.md; mkf "$WDD" docs/p.md; mkd "$WDD" docs/issues/dd; mkd "$WDD" docs/plans/dd
( cd "$WDD" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
( cd "$WDD" && bash "$FLOW" handoff --conclusion pass --produced docs/p.md >/dev/null )
approve_design "$WDD" docs/design/dd.md
( cd "$WDD" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/dd/ >/dev/null )
( cd "$WDD" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/dd/ >/dev/null )   # plan→②审闸
( cd "$WDD" && bash "$FLOW" handoff --conclusion needs-repair >/dev/null )                     # ②审打回
[ "$(mfield "$WDD" gate)" = "null" ] && ok "审打回→gate 清空" || no "审打回 gate 清空"
[ "$(mphase "$WDD")" = "plan" ] && ok "审打回→停在 plan 返工" || no "审打回停 plan"
[ "$(mfield "$WDD" repair_count)" = "1" ] && ok "审打回计返工=1" || no "审打回返工计数"
( cd "$WDD" && bash "$FLOW" handoff --conclusion pass --produced docs/plans/dd/ >/dev/null )   # 改完再 pass→重进闸
[ "$(mfield "$WDD" 'phase_outputs.plan|length')" = "1" ] && ok "返修后同产出不重复累积(unique)" || no "phase_outputs 去重"
WRS="$(cd "$WDD" && bash "$FLOW" where)"
echo "$WRS" | grep -q -- "review_start=.*--source docs/plans/dd/" && ok "where 吐 review_start 带 --source" || no "review_start source"
if [ "$(echo "$WRS" | grep -c -- "--source docs/plans/dd/")" = "1" ]; then ok "review_start 无重复 --source"; else no "review_start 重复 source"; fi

# ===== 冷启动:有在飞任务报 RESUMABLE(断点恢复入口),空仓库报 UNMANAGED =====
WCOLD="$(cd "$TMP" && bash "$FLOW" where)"
echo "$WCOLD" | grep -q "^RESUMABLE$" && ok "主仓库有在飞任务 → where 报 RESUMABLE" || no "RESUMABLE"
echo "$WCOLD" | grep -q "UNMANAGED" && no "有在飞任务不该报 UNMANAGED" || ok "有在飞任务不报 UNMANAGED"
echo "$WCOLD" | grep -q "2026-07-05-dedup" && ok "在飞清单含 manifest 任务(slug/phase/path)" || no "在飞清单条目"
echo "$WCOLD" | grep -q "cd .*2026-07-05-dedup.*where" && ok "在飞条目带可执行恢复命令" || no "在飞恢复命令"
WEMPTY="$TMP/empty-repo"
mkdir -p "$WEMPTY"
( cd "$WEMPTY" && git init -q )
WEMPTY_OUT="$(cd "$WEMPTY" && bash "$FLOW" where)"
echo "$WEMPTY_OUT" | grep -q "^UNMANAGED$" && ok "无在飞任务 → where 报 UNMANAGED" || no "空仓库 UNMANAGED"
echo "$WEMPTY_OUT" | grep -q "RESUMABLE" && no "无在飞任务不该报 RESUMABLE" || ok "无在飞任务不报 RESUMABLE"
echo "$WEMPTY_OUT" | grep -q "琐碎单步动作.*不进 orchestrate" && ok "冷启动明确琐碎单步动作直接处理" || no "冷启动缺直接处理边界"
echo "$WEMPTY_OUT" | grep -q "\[small-change\].*独立任务边界" && ok "small-change 收窄到需独立任务边界" || no "small-change 路由仍过宽"

# ===== propose 分叉:--direction-given 落 manifest,where 降级指路 =====
WDG="$(bash "$PREPARE" new --scenario develop --slug 2026-07-05-dg --title t --request t --direction-given 2>/dev/null | grep '^worktree_path=' | cut -d= -f2-)"
[ "$(mfield "$WDG" direction_given)" = "true" ] && ok "--direction-given 钉进 manifest" || no "direction_given 落盘"
mkf "$WDG" docs/i.md
( cd "$WDG" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
echo "$(cd "$WDG" && bash "$FLOW" where)" | grep -q "do=方向已由用户明示" && ok "propose 降级:where 报降级 do" || no "propose 降级 do"
WNF="$(newtask develop 2026-07-05-nf)"
mkf "$WNF" docs/i.md
( cd "$WNF" && bash "$FLOW" handoff --conclusion pass --produced docs/i.md >/dev/null )
WNFO="$(cd "$WNF" && bash "$FLOW" where)"
echo "$WNFO" | grep -q "do=方向已由用户明示" && no "无 flag 不该降级" || true
echo "$WNFO" | grep -q "亮 2-3 方案" && ok "无 flag propose 走全量方案" || no "无 flag 全量方案"

# ===== note 书签(三源回报之一) =====
( cd "$WNF" && bash "$NOTE" note set --text "下一步先对齐計費口徑" >/dev/null )
( cd "$WNF" && bash "$NOTE" note show ) | grep -q "下一步先对齐計費口徑" && ok "note set/show 书签留读" || no "note 书签"
if ( cd "$WNF" && bash "$NOTE" note set >/dev/null 2>&1 ); then no "note set 缺 text 该被拒"; else ok "note set 缺 text 被拒"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
