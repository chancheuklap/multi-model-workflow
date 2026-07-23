#!/usr/bin/env bash
# prototype design 内层循环：登记、续作、逐轮日志、选中、接管与路径安全。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
PREPARE="$PLUGIN/scripts/prepare.sh"
FLOW="$PLUGIN/scripts/flow.sh"
MMW="$PLUGIN/scripts/mmw.sh"
# shellcheck source=../lib/runtime.sh
. "$PLUGIN/scripts/lib/runtime.sh"

state_subdir() {
  if declare -F mmw_state_subdir >/dev/null 2>&1; then mmw_state_subdir; else printf '%s' "$MMW_STATE_SUBDIR"; fi
}

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

advance_to_design() {
  local wt="$1" slug="$2"
  mkdir -p "$wt/docs/design/$slug"
  printf '# investigating\n' >"$wt/docs/design/$slug/investigating.md"
  (cd "$wt" && bash "$FLOW" handoff --conclusion pass --produced "docs/design/$slug/investigating.md" >/dev/null)
  printf '# direction\n' >"$wt/docs/design/$slug/direction.md"
  (cd "$wt" && bash "$FLOW" handoff --conclusion pass --produced "docs/design/$slug/direction.md" >/dev/null)
}

new_design_task() {
  local slug="$1" wt
  wt="$(bash "$PREPARE" new --scenario develop --slug "$slug" --title "prototype test" --request "验证 prototype 迭代闭环" 2>/dev/null | sed -n 's/^worktree_path=//p')"
  [ -n "$wt" ] || return 1
  advance_to_design "$wt" "$slug"
  printf '%s' "$wt"
}

echo "=== test_prototype.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q; git config user.email test@example.com; git config user.name Test
printf 'seed\n' >seed; git add seed; git commit -qm seed

SD="$(state_subdir)"
SLUG="2026-07-23-prototype"
WT="$(new_design_task "$SLUG")"
MAN="$WT/$SD/task.json"
LOG="$WT/docs/design/$SLUG/prototype/README.md"
MAIN_DESIGN="docs/design/$SLUG/$SLUG.md"
printf '# design\n' >"$WT/$MAIN_DESIGN"

# 未启动 prototype 时 design 出口也必须指向 pin/预审/人闸，不得误导 agent 走 handoff pass。
WHERE_EMPTY="$(cd "$WT" && bash "$MMW" where)"
echo "$WHERE_EMPTY" | grep -q '^then=.*pin --phase design' \
  && echo "$WHERE_EMPTY" | grep -q -- "--produced ${MAIN_DESIGN}；" \
  && echo "$WHERE_EMPTY" | grep -q '/approve-design' \
  && ! echo "$WHERE_EMPTY" | grep -q '^then=.*handoff --conclusion' \
  && ok "design where 给正确唯一出口" || no "design where 仍误导 handoff"
if (cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1); then no "空 prototype 不得 handoff pass"; else
  [ "$(jq -r .phase "$MAN")" = design ] && ok "未审批 design 禁止 handoff pass" || no "design pass 改了阶段"
fi

# fresh start：只登记状态与日志，不替 agent 生成实现骨架。
START="$(cd "$WT" && bash "$MMW" prototype start --kind logic --question "暂停后是否恢复原队列" --run "python docs/design/$SLUG/prototype/demo.py")"
[ "$(jq -r '.prototype.status' "$MAN")" = active ] \
  && [ "$(jq -r '.prototype.iteration' "$MAN")" = 1 ] \
  && [ "$(jq -r '.prototype.artifacts|length' "$MAN")" = 0 ] \
  && ok "fresh start 建 active 第 1 轮" || no "fresh start 状态"
[ -f "$LOG" ] && grep -q '暂停后是否恢复原队列' "$LOG" \
  && echo "$START" | grep -q '^NEXT=' && ok "fresh start 写日志并给唯一下一步" || no "fresh start 回执"
[ -d "$WT/docs/design/$SLUG/prototype/runs" ] && [ ! -e "$WT/docs/design/$SLUG/prototype/demo.py" ] \
  && ok "start 只建日志与 runs" || no "start 不应生成原型骨架"

# active 状态必须接管冷启动导航、进度板和会话分诊，并阻止设计确认。
WHERE_ACTIVE="$(cd "$WT" && bash "$MMW" where)"
echo "$WHERE_ACTIVE" | grep -q '^inner_loop=prototype$' \
  && echo "$WHERE_ACTIVE" | grep -q '^prototype_iteration=1$' \
  && echo "$WHERE_ACTIVE" | grep -q '^load=references/design/prototype-mockup.md$' \
  && echo "$WHERE_ACTIVE" | grep -q '^then=.*prototype checkpoint' \
  && ok "where 精确恢复 active prototype" || no "where active prototype 指路"
BOARD_ACTIVE="$(cd "$WT" && bash "$MMW" progress render --stdout)"
echo "$BOARD_ACTIVE" | grep -q 'Prototype.*active.*第 1 轮' \
  && ok "progress 投影 active prototype" || no "progress prototype 投影"
TRIAGE_ACTIVE="$(cd "$WT" && bash "$PLUGIN/hooks/session-triage.sh")"
echo "$TRIAGE_ACTIVE" | grep -q 'prototype.*active.*第 1 轮' \
  && echo "$TRIAGE_ACTIVE" | grep -q "$LOG" \
  && ok "session triage 回报 prototype 断点" || no "session triage prototype"
if (cd "$WT" && bash "$MMW" approve --report "$MAIN_DESIGN" >/dev/null 2>&1); then
  no "active prototype 不得 approve"
else
  [ "$(jq -r .phase "$MAN")" = design ] && ok "active prototype 阻止设计确认" || no "active approve 改动阶段"
fi
if (cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1); then no "active prototype 不得 handoff pass"; else
  [ "$(jq -r .phase "$MAN")" = design ] && ok "active 时禁止绕过审批" || no "active handoff pass 改了阶段"
fi

# active 重复 start 必须拒绝且不覆盖日志。
BEFORE="$(shasum "$LOG" | awk '{print $1}')"
if (cd "$WT" && bash "$MMW" prototype start --kind logic --question "重建" --run "false" >/dev/null 2>&1); then
  no "active 重复 start 应拒绝"
else
  [ "$(shasum "$LOG" | awk '{print $1}')" = "$BEFORE" ] && ok "重复 start 拒绝且日志不变" || no "重复 start 覆盖日志"
fi

# 第 1 轮：产物与证据真实存在，continue 追加日志并进入第 2 轮。
mkdir -p "$WT/docs/design/$SLUG/prototype/runs/001"
printf 'prototype\n' >"$WT/docs/design/$SLUG/prototype/demo.py"
printf 'passed\n' >"$WT/docs/design/$SLUG/prototype/runs/001/output.txt"
cp "$MAN" "$TMP/manifest-before-round1.json"
ROUND1="$(cd "$WT" && bash "$MMW" prototype checkpoint \
  --feedback "重复恢复会产生两条任务" \
  --change "增加幂等检查" \
  --result "重复恢复被拒绝" \
  --artifact "docs/design/$SLUG/prototype/demo.py" \
  --evidence "docs/design/$SLUG/prototype/runs/001/output.txt" \
  --verdict continue)"
[ "$(jq -r '.prototype.iteration' "$MAN")" = 2 ] \
  && [ "$(jq -r '.prototype.artifacts[0]' "$MAN")" = "docs/design/$SLUG/prototype/demo.py" ] \
  && echo "$ROUND1" | grep -q 'prototype_iteration=2' && ok "continue 关闭本轮并进入下一轮" || no "continue 状态"
[ "$(grep -c '<!-- mmw-prototype-round:1 -->' "$LOG")" = 1 ] \
  && ok "第 1 轮日志原子追加一次" || no "第 1 轮日志标记"

# 模拟“日志已写、manifest 未写”的中断；重跑只能补状态，不能重复日志。
cp "$TMP/manifest-before-round1.json" "$MAN"
(cd "$WT" && bash "$MMW" prototype checkpoint \
  --feedback "重复恢复会产生两条任务" \
  --change "增加幂等检查" \
  --result "重复恢复被拒绝" \
  --artifact "docs/design/$SLUG/prototype/demo.py" \
  --evidence "docs/design/$SLUG/prototype/runs/001/output.txt" \
  --verdict continue >/dev/null)
[ "$(grep -c '<!-- mmw-prototype-round:1 -->' "$LOG")" = 1 ] \
  && [ "$(jq -r '.prototype.iteration' "$MAN")" = 2 ] \
  && ok "checkpoint 中断重跑幂等" || no "checkpoint 重跑重复写"

# accepted 必须明确 selected。
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback "通过" --change "补边界" --result "全部通过" --verdict accepted >/dev/null 2>&1); then
  no "accepted 缺 selected 应拒绝"
else
  ok "accepted 缺 selected fail-closed"
fi
ROUND2="$(cd "$WT" && bash "$MMW" prototype checkpoint \
  --feedback "全部场景符合预期" --change "补齐错误状态" --result "走查通过" \
  --verdict accepted --selected "docs/design/$SLUG/prototype/demo.py")"
[ "$(jq -r '.prototype.status' "$MAN")" = accepted ] \
  && [ "$(jq -r '.prototype.selected[0]' "$MAN")" = "docs/design/$SLUG/prototype/demo.py" ] \
  && echo "$ROUND2" | grep -q '回填主设计文档' && ok "accepted 钉选中产物并返回设计成文" || no "accepted 状态"

# accepted 收到新反馈时用同一 checkpoint 重新打开，不重建产物。
REOPEN="$(cd "$WT" && bash "$MMW" prototype checkpoint --feedback "用户要求再验证断电恢复" --verdict continue)"
[ "$(jq -r '.prototype.status' "$MAN")" = active ] \
  && [ "$(jq -r '.prototype.iteration' "$MAN")" = 3 ] \
  && [ "$(jq -r '.prototype.selected|length' "$MAN")" = 0 ] \
  && echo "$REOPEN" | grep -q 'prototype_iteration=3' && ok "accepted 可重新打开下一轮" || no "accepted reopen"

# 路径安全：越界、绝对路径、换行、软链都拒绝。
printf 'outside\n' >"$WT/outside.txt"
ln -s demo.py "$WT/docs/design/$SLUG/prototype/link.py"
for bad in "../outside.txt" "$WT/outside.txt" $'docs/design/'"$SLUG"$'/prototype/bad\nname'; do
  if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r --artifact "$bad" --verdict continue >/dev/null 2>&1); then
    no "非法路径应拒绝:$bad"
  else
    ok "非法路径 fail-closed"
  fi
done
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r \
  --artifact "docs/design/$SLUG/prototype/link.py" --verdict continue >/dev/null 2>&1); then
  no "软链产物应拒绝"
else
  ok "软链产物 fail-closed"
fi
rm "$WT/docs/design/$SLUG/prototype/link.py"
mkdir -p "$WT/docs/design/$SLUG/prototype/runs/003"
printf 'walk evidence\n' >"$WT/docs/design/$SLUG/prototype/runs/003/evidence.txt"
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r \
  --artifact "docs/design/$SLUG/prototype/runs/003/evidence.txt" --verdict continue >/dev/null 2>&1); then
  no "runs 证据不得登记为 artifact"
else
  ok "runs 与实现产物分类隔离"
fi
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r \
  --artifact "docs/design/$SLUG/prototype/demo.py" \
  --selected "docs/design/$SLUG/prototype/README.md" --verdict accepted >/dev/null 2>&1); then
  no "README 不得成为 selected"
else
  ok "README 与 selected 分类隔离"
fi

# 父目录软链同样不得让 artifact / selected / evidence 逃出 worktree。
PARENT_OUTSIDE="$TMP/prototype-parent-outside"
mkdir -p "$PARENT_OUTSIDE" "$WT/docs/design/$SLUG/prototype/runs/003"
printf 'escape\n' >"$PARENT_OUTSIDE/escape.py"
printf 'evidence\n' >"$PARENT_OUTSIDE/result.txt"
ln -s "$PARENT_OUTSIDE" "$WT/docs/design/$SLUG/prototype/escape"
ln -s "$PARENT_OUTSIDE" "$WT/docs/design/$SLUG/prototype/runs/003/escape"
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r \
  --artifact "docs/design/$SLUG/prototype/escape/escape.py" --verdict continue >/dev/null 2>&1); then
  no "父软链 artifact 应拒绝"
else
  ok "父软链 artifact fail-closed"
fi
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r \
  --artifact "docs/design/$SLUG/prototype/demo.py" \
  --selected "docs/design/$SLUG/prototype/escape/escape.py" --verdict accepted >/dev/null 2>&1); then
  no "父软链 selected 应拒绝"
else
  ok "父软链 selected fail-closed"
fi
if (cd "$WT" && bash "$MMW" prototype checkpoint --feedback f --change c --result r \
  --artifact "docs/design/$SLUG/prototype/demo.py" \
  --evidence "docs/design/$SLUG/prototype/runs/003/escape/result.txt" --verdict continue >/dev/null 2>&1); then
  no "父软链 evidence 应拒绝"
else
  ok "父软链 evidence fail-closed"
fi
rm "$WT/docs/design/$SLUG/prototype/escape" "$WT/docs/design/$SLUG/prototype/runs/003/escape"

# superseded 保留记录，并给唯一回退指令。
SUPER="$(cd "$WT" && bash "$MMW" prototype checkpoint \
  --feedback "上游方向已改变" --change "停止当前模型" --result "当前问题不再成立" \
  --verdict superseded)"
[ "$(jq -r '.prototype.status' "$MAN")" = superseded ] \
  && echo "$SUPER" | grep -q 'handoff --conclusion needs-redirection --to-phase propose' \
  && ok "superseded 明确退回 propose" || no "superseded 回执"
WHERE_SUPER="$(cd "$WT" && bash "$MMW" where)"
echo "$WHERE_SUPER" | grep -q '^prototype_status=superseded$' \
  && echo "$WHERE_SUPER" | grep -q '^then=.*handoff --conclusion needs-redirection --to-phase propose' \
  && ok "where 恢复 superseded 唯一回退" || no "where superseded"
if (cd "$WT" && bash "$MMW" approve --report "$MAIN_DESIGN" >/dev/null 2>&1); then
  no "superseded prototype 不得 approve"
else
  ok "superseded 阻止设计确认"
fi
if (cd "$WT" && bash "$FLOW" handoff --conclusion pass >/dev/null 2>&1); then no "superseded 不得 handoff pass"; else
  [ "$(jq -r .phase "$MAN")" = design ] && ok "superseded 时禁止绕过审批" || no "superseded handoff pass 改了阶段"
fi

# superseded 回 propose 再进 design 后，新验证问题必须沿用全局递增轮次，不能撞旧日志 marker。
(cd "$WT" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase propose >/dev/null)
printf '# direction v2\n' >"$WT/docs/design/$SLUG/direction.md"
(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced "docs/design/$SLUG/direction.md" >/dev/null)
RESTART="$(cd "$WT" && bash "$MMW" prototype start --kind logic --question "新方向是否覆盖恢复" --run "python docs/design/$SLUG/prototype/demo-v2.py")"
jq -e --arg old "docs/design/$SLUG/prototype/demo.py" '.prototype.artifacts | index($old) != null' "$MAN" >/dev/null \
  && ok "superseded 后新问题继续携带已有产物" || no "superseded 重开丢失已有产物"
printf 'v2\n' >"$WT/docs/design/$SLUG/prototype/demo-v2.py"
(cd "$WT" && bash "$MMW" prototype checkpoint \
  --feedback "新方向通过" --change "改用新状态模型" --result "全场景通过" \
  --artifact "docs/design/$SLUG/prototype/demo-v2.py" \
  --selected "docs/design/$SLUG/prototype/demo-v2.py" --verdict accepted >/dev/null)
[ "$(jq -r '.prototype.iteration' "$MAN")" = 4 ] \
  && echo "$RESTART" | grep -q 'prototype_iteration=4' \
  && [ "$(grep -c '<!-- mmw-prototype-round:4 -->' "$LOG")" = 1 ] \
  && [ "$(grep -c '<!-- mmw-prototype-session:' "$LOG")" = 2 ] \
  && ok "superseded 后重开沿用单调轮次且日志不碰撞" || no "superseded 重开轮次/日志"

# 旧任务磁盘已有产物：fresh start 拒绝，--adopt 原地登记。
SLUG2="2026-07-23-adopt"
WT2="$(new_design_task "$SLUG2")"
MAN2="$WT2/$SD/task.json"
mkdir -p "$WT2/docs/design/$SLUG2/mockup" "$WT2/docs/design/$SLUG2/prototype/runs/001"
printf '<html>old</html>\n' >"$WT2/docs/design/$SLUG2/mockup/current.html"
printf 'old evidence\n' >"$WT2/docs/design/$SLUG2/prototype/runs/001/output.txt"
printf '# design\n' >"$WT2/docs/design/$SLUG2/$SLUG2.md"
cp "$MAN2" "$TMP/manifest-before-broken.json"
jq '.prototype={status:"broken"}' "$MAN2" >"$MAN2.tmp" && mv "$MAN2.tmp" "$MAN2"
WHERE_BROKEN="$(cd "$WT2" && bash "$MMW" where)"
echo "$WHERE_BROKEN" | grep -q '^then=STOP:prototype 状态损坏' \
  && ok "损坏状态明确 STOP" || no "损坏状态仍给推进指令"
cp "$TMP/manifest-before-broken.json" "$MAN2"
WHERE_UNTRACKED="$(cd "$WT2" && bash "$MMW" where)"
echo "$WHERE_UNTRACKED" | grep -q '^prototype_untracked=' \
  && echo "$WHERE_UNTRACKED" | grep -q '^then=.*prototype start --adopt' \
  && ! echo "$WHERE_UNTRACKED" | grep -q 'runs/001/output.txt' \
  && ok "where 只要求接管实现产物，不混入 runs 证据" || no "where untracked 分类"
if (cd "$WT2" && bash "$MMW" approve --report "docs/design/$SLUG2/$SLUG2.md" >/dev/null 2>&1); then
  no "未登记 prototype 不得 approve"
else
  ok "未登记 prototype 阻止设计确认"
fi
if (cd "$WT2" && bash "$MMW" prototype start --kind ui --question "采用哪种布局" --run "open mockup/current.html" >/dev/null 2>&1); then
  no "已有未登记产物时 fresh start 应拒绝"
else
  ok "已有未登记产物阻止 fresh start"
fi
ADOPT="$(cd "$WT2" && bash "$MMW" prototype start --adopt --kind ui --question "采用哪种布局" \
  --run "open docs/design/$SLUG2/mockup/current.html" \
  --artifact "docs/design/$SLUG2/mockup/current.html")"
[ "$(jq -r '.prototype.status' "$MAN2")" = active ] \
  && [ "$(jq -r '.prototype.artifacts[0]' "$MAN2")" = "docs/design/$SLUG2/mockup/current.html" ] \
  && grep -q '采用哪种布局' "$WT2/docs/design/$SLUG2/prototype/README.md" \
  && echo "$ADOPT" | grep -q 'PROTOTYPE_ADOPTED' && ok "--adopt 原地接管旧产物" || no "--adopt 状态"

# accepted 后 where 回设计成文；approve 自动指纹覆盖 log + selected，下游能按接力单读取。
SLUG3="2026-07-23-approve"
WT3="$(new_design_task "$SLUG3")"
MAN3="$WT3/$SD/task.json"
MAIN3="docs/design/$SLUG3/$SLUG3.md"
ART3="docs/design/$SLUG3/prototype/demo.py"
LOG3="docs/design/$SLUG3/prototype/README.md"
printf '# design\n' >"$WT3/$MAIN3"
(cd "$WT3" && bash "$FLOW" pin --phase design --produced "$MAIN3" >/dev/null)
(cd "$WT3" && bash "$MMW" prototype start --kind logic --question "确认状态模型" --run "python $ART3" >/dev/null)
printf 'accepted\n' >"$WT3/$ART3"
(cd "$WT3" && bash "$MMW" prototype checkpoint --feedback "走查完成" --change "补齐失败态" --result "全部通过" \
  --artifact "$ART3" --verdict accepted --selected "$ART3" >/dev/null)
WHERE_ACCEPTED="$(cd "$WT3" && bash "$MMW" where)"
echo "$WHERE_ACCEPTED" | grep -q '^prototype_status=accepted$' \
  && echo "$WHERE_ACCEPTED" | grep -q '^prototype_selected=.*demo.py' \
  && echo "$WHERE_ACCEPTED" | grep -q '回填主设计文档' \
  && echo "$WHERE_ACCEPTED" | grep -q '^then=.*pin --phase design' \
  && ok "where accepted 回到设计成文" || no "where accepted"
(cd "$WT3" && bash "$MMW" approve >/dev/null)
[ "$(jq -r .phase "$MAN3")" = to-issue ] \
  && jq -e --arg main "$MAIN3" --arg log "$LOG3" --arg art "$ART3" '.approval.reports | index($main) != null and index($log) != null and index($art) != null' "$MAN3" >/dev/null \
  && jq -e --arg main "$MAIN3" --arg log "$LOG3" --arg art "$ART3" '.phase_outputs.design | index($main) != null and index($log) != null and index($art) != null' "$MAN3" >/dev/null \
  && ok "无参数 approve 保留主设计并追加 accepted 产物" || no "approve 丢失主设计"
printf 'changed after approval\n' >>"$WT3/$ART3"
STALE="$(cd "$WT3" && bash "$MMW" where)"
echo "$STALE" | grep -q '^approval_stale=' && ok "selected 改动触发 approval stale" || no "selected stale"

# A 被新一轮 B 淘汰后，design 接力单必须替换而非累加旧 selected。
SLUG4="2026-07-23-reselect"
WT4="$(new_design_task "$SLUG4")"
MAN4="$WT4/$SD/task.json"; MAIN4="docs/design/$SLUG4/$SLUG4.md"
printf '# design\n' >"$WT4/$MAIN4"
(cd "$WT4" && bash "$FLOW" pin --phase design --produced "$MAIN4" >/dev/null)
A4="docs/design/$SLUG4/prototype/a.py"; B4="docs/design/$SLUG4/prototype/b.py"
(cd "$WT4" && bash "$MMW" prototype start --kind logic --question q --run run >/dev/null)
printf A >"$WT4/$A4"
(cd "$WT4" && bash "$MMW" prototype checkpoint --feedback f --change c --result r --artifact "$A4" --selected "$A4" --verdict accepted >/dev/null && bash "$MMW" approve >/dev/null)
(cd "$WT4" && bash "$FLOW" handoff --conclusion needs-redirection --to-phase design >/dev/null && bash "$MMW" prototype checkpoint --feedback reopen --verdict continue >/dev/null)
printf B >"$WT4/$B4"
(cd "$WT4" && bash "$MMW" prototype checkpoint --feedback f2 --change c2 --result r2 --artifact "$B4" --selected "$B4" --verdict accepted >/dev/null && bash "$MMW" approve >/dev/null)
jq -e --arg main "$MAIN4" --arg a "$A4" --arg b "$B4" '.phase_outputs.design | index($main) != null and index($a) == null and index($b) != null' "$MAN4" >/dev/null \
  && ok "重新选择后接力单只保留当前 selected" || no "旧 selected 残留在接力单"
printf '\nResults: %s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
