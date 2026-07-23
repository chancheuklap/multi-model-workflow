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
[ "$(grep -c '<!-- mmw-prototype-round:1 -->' "$LOG")" = 1 ] && ok "第 1 轮日志追加一次" || no "第 1 轮日志标记"

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

# superseded 保留记录，并给唯一回退指令。
SUPER="$(cd "$WT" && bash "$MMW" prototype checkpoint \
  --feedback "上游方向已改变" --change "停止当前模型" --result "当前问题不再成立" \
  --verdict superseded)"
[ "$(jq -r '.prototype.status' "$MAN")" = superseded ] \
  && echo "$SUPER" | grep -q 'handoff --conclusion needs-redirection --to-phase propose' \
  && ok "superseded 明确退回 propose" || no "superseded 回执"

# 旧任务磁盘已有产物：fresh start 拒绝，--adopt 原地登记。
SLUG2="2026-07-23-adopt"
WT2="$(new_design_task "$SLUG2")"
MAN2="$WT2/$SD/task.json"
mkdir -p "$WT2/docs/design/$SLUG2/mockup"
printf '<html>old</html>\n' >"$WT2/docs/design/$SLUG2/mockup/current.html"
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

printf '\nResults: %s passed, %s failed\n' "$pass" "$fail"
[ "$fail" = 0 ]
