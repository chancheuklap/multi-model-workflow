#!/usr/bin/env bash
# loop.sh 内层引擎空跑:看守 exit-check、软停×在场、冒泡、审核 checklist、合同门。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/../loop.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
ec() { bash "$LOOP" exit-check; }   # exit-check 输出

echo "=== test_loop.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s

# ===== 落地 loop:看守逼做完 =====
bash "$LOOP" init --kind execution >/dev/null
bash "$LOOP" step add --id 1.1 --desc a >/dev/null
bash "$LOOP" step add --id 1.2 --desc b >/dev/null
[ "$(ec)" = "NOT-DONE:steps=1.1,1.2" ] && ok "未做完 → NOT-DONE 列剩余" || no "NOT-DONE ($(ec))"
bash "$LOOP" step done --id 1.1 --commit abc >/dev/null
[ "$(ec)" = "NOT-DONE:steps=1.2" ] && ok "做一半仍 NOT-DONE" || no "做一半 ($(ec))"
bash "$LOOP" step done --id 1.2 >/dev/null
[ "$(ec)" = "DONE" ] && ok "全 done → DONE(看守放停)" || no "全 done ($(ec))"
# 回归:step done 不带 --commit 不许把元素从步账蒸发(旧 jq select 写法之坑)
f0="${STATE_SUBDIR}/loop-state.json"
[ "$(jq -r '.steps|length' "$f0")" = "2" ] && ok "done 不带 commit 步账元素保留(不蒸发)" || no "步账蒸发!($(jq -r '.steps|length' "$f0"))"
[ "$(jq -r '.steps[1].commit' "$f0")" = "null" ] && ok "无 commit 时字段保持 null" || no "commit 字段"

# ===== init 从外层 task.json 读值守档(权威在 task.json,loop 只是派生缓存) =====
bash "$LOOP" close >/dev/null
mkdir -p .claude/multi-model-workflow
echo '{"attendance":"unattended"}' > .claude/multi-model-workflow/task.json
bash "$LOOP" init --kind execution >/dev/null
[ "$(jq -r .attendance .claude/multi-model-workflow/loop-state.json)" = "unattended" ] && ok "init 从 task.json 读入 unattended" || no "init 读 task.json mode"
rm -f .claude/multi-model-workflow/task.json   # 后续用例回到无 task.json(默认 afk)

# ===== 软停 × 在场开关 =====
bash "$LOOP" close >/dev/null   # 换 loop 前收束上一个(init 拒覆盖未收束 loop)
bash "$LOOP" init --kind execution >/dev/null
[ "$(jq -r .attendance .claude/multi-model-workflow/loop-state.json)" = "afk" ] && ok "无 task.json 时 init 缺省 afk" || no "缺省 afk"
bash "$LOOP" step add --id 2.1 --desc x >/dev/null
# unattended 也是合法档(软停自决,与 afk 同路;禁问是 Coordinator 合同,不在 loop 层)
bash "$LOOP" attendance --mode unattended >/dev/null
[ "$(jq -r .attendance .claude/multi-model-workflow/loop-state.json)" = "unattended" ] && ok "attendance 接受 unattended" || no "attendance unattended"
bash "$LOOP" attendance --mode afk >/dev/null
# afk:自决+留痕,不写 pause
bash "$LOOP" attendance --mode afk >/dev/null
OUT="$(bash "$LOOP" softstop --question "用默认超时?" --default 30s --at-step 2.1)"
echo "$OUT" | grep -q "AUTO-DECIDED" && ok "afk 软停 → 自决" || no "afk 自决"
f="${STATE_SUBDIR}/loop-state.json"
[ "$(jq -r '.decisions|length' "$f")" = "1" ] && ok "afk 自决留痕(decisions)" || no "afk 留痕"
[ "$(jq -r '.pause' "$f")" = "null" ] && ok "afk 不写 pause、不停" || no "afk 不停"
# attended:写 pause、停
bash "$LOOP" attendance --mode attended >/dev/null
OUT2="$(bash "$LOOP" softstop --question "用默认超时?" --at-step 2.1)"
echo "$OUT2" | grep -q "PAUSED-SOFT" && ok "在场软停 → 停下问" || no "在场软停"
[ "$(ec)" = "PAUSED:soft" ] && ok "停着 exit-check=PAUSED(不算 done)" || no "PAUSED ($(ec))"
bash "$LOOP" resume >/dev/null
[ "$(jq -r '.pause' "$f")" = "null" ] && ok "resume 清 pause" || no "resume 清"

# ===== 冒泡:永远停 =====
bash "$LOOP" attendance --mode afk >/dev/null
bash "$LOOP" surface --kind needs-redirection --question "方向是不是错了?" >/dev/null
[ "$(ec)" = "PAUSED:needs-redirection" ] && ok "冒泡 afk 也停(needs-redirection)" || no "冒泡停 ($(ec))"

# ===== 审核 loop:checklist 没全 covered 不放 pass =====
bash "$LOOP" close >/dev/null
bash "$LOOP" init --kind review >/dev/null
bash "$LOOP" checklist add --item intent-1 --source design.md:10 >/dev/null
bash "$LOOP" checklist add --item intent-2 --source design.md:20 >/dev/null
echo "$(ec)" | grep -q "^NOT-DONE:checklist=intent-1,intent-2" && ok "审:清单没覆盖 → NOT-DONE" || no "审 NOT-DONE ($(ec))"
bash "$LOOP" checklist cover --item intent-1 --evidence "测过" >/dev/null
bash "$LOOP" checklist cover --item intent-2 --evidence "测过" >/dev/null
[ "$(ec)" = "DONE" ] && ok "审:清单全覆盖 + 无 Critical → DONE" || no "审 DONE ($(ec))"
bash "$LOOP" finding add --severity Critical --confidence 8 --locator foo.py:3 >/dev/null
echo "$(ec)" | grep -q "open_critical=1" && ok "审:有开口 Critical → 不放 DONE" || no "审 Critical ($(ec))"

# ===== ③合同门:全 pack committed + 合同存在 =====
bash "$LOOP" close >/dev/null
bash "$LOOP" init --kind contract-gate >/dev/null
bash "$LOOP" step add --id p1 --desc pack1 >/dev/null
bash "$LOOP" checklist add --item contractA --source plan.md >/dev/null
echo "$(ec)" | grep -q "NOT-DONE:packs=p1;contracts=contractA" && ok "合同门:未达 → NOT-DONE" || no "合同门 NOT-DONE ($(ec))"
bash "$LOOP" step done --id p1 --commit z >/dev/null
bash "$LOOP" checklist cover --item contractA --evidence "接上了" >/dev/null
[ "$(ec)" = "DONE" ] && ok "合同门:全提交+合同在 → DONE" || no "合同门 DONE ($(ec))"

# ===== 模式B 步账记 plan/worktree(内层断点恢复)+ init 守卫 + close 幂等 =====
CF="${STATE_SUBDIR}/loop-state.json"
bash "$LOOP" close >/dev/null   # 收束上一个 contract-gate loop
bash "$LOOP" init --kind execution >/dev/null
# init 守卫:已有未收束 loop 再 init 被拒(防手滑抹掉 execution 进度/子 worktree 映射)
if bash "$LOOP" init --kind review >/dev/null 2>&1; then no "已有 loop 再 init 应被拒"; else ok "init 守卫:未收束 loop 拒覆盖"; fi
# 步账记 plan + 子 worktree(pending+有 worktree = 已派,断点恢复据此认哪步派到哪)
bash "$LOOP" step add --id planA --desc "计划A" --plan docs/plans/x/001.md --worktree /wt/planA >/dev/null
[ "$(jq -r '.steps[0].plan' "$CF")" = "docs/plans/x/001.md" ] && ok "步账记 plan 路径(恢复认哪步=哪 plan)" || no "step.plan 未记"
[ "$(jq -r '.steps[0].worktree' "$CF")" = "/wt/planA" ] && ok "步账记子 worktree(恢复认派到哪)" || no "step.worktree 未记"
# 不带 plan/worktree 的步 → null(模式A 小改步)
bash "$LOOP" step add --id 9.9 --desc x >/dev/null
[ "$(jq -r '.steps[1].plan' "$CF")" = "null" ] && ok "无 plan 步记 null(模式A 兼容)" || no "step.plan 应 null"
[ -f "$CF" ] && ok "close 前 loop-state 在" || no "close 前应有 loop-state"
echo "$(bash "$LOOP" close)" | grep -q "CLOSED" && ok "close 报 CLOSED" || no "close 回执"
[ ! -f "$CF" ] && ok "close 删掉 loop-state" || no "close 未删 loop-state"
echo "$(bash "$LOOP" close)" | grep -q "CLOSED" && [ ! -f "$CF" ] && ok "close 幂等(无 loop 也安静退)" || no "close 非幂等"

# ===== 空账本不算 DONE(防漏登记静默过门)=====
bash "$LOOP" close >/dev/null
bash "$LOOP" init --kind execution >/dev/null
echo "$(ec)" | grep -q "NOT-DONE:steps=EMPTY" && ok "execution 空步账 → NOT-DONE(不静默过)" || no "execution 空账 ($(ec))"
bash "$LOOP" close >/dev/null
bash "$LOOP" init --kind review >/dev/null
echo "$(ec)" | grep -q "NOT-DONE:checklist=EMPTY" && ok "review 空清单 → NOT-DONE" || no "review 空账 ($(ec))"
bash "$LOOP" close >/dev/null
bash "$LOOP" init --kind contract-gate >/dev/null
echo "$(ec)" | grep -q "NOT-DONE:contracts=EMPTY" && ok "③合同门空清单 → NOT-DONE(无合同也要显式登记)" || no "合同门空账 ($(ec))"
bash "$LOOP" checklist add --item no-cross-plan-contracts --source design.md:83 >/dev/null
bash "$LOOP" checklist cover --item no-cross-plan-contracts --evidence "design.md:83(anchors 空)" >/dev/null
[ "$(ec)" = "DONE" ] && ok "显式登记 no-cross-plan-contracts 并 cover → DONE" || no "显式空合同 ($(ec))"

# ===== 审 loop 轮账:round next 机器计数,到 max_rounds 自动 surface 熔断 =====
bash "$LOOP" close >/dev/null
bash "$LOOP" init --kind review --max-rounds 2 >/dev/null
[ "$(jq -r '.round' "${STATE_SUBDIR}/loop-state.json")" = "1" ] && ok "init round=1" || no "init round"
[ "$(jq -r '.max_rounds' "${STATE_SUBDIR}/loop-state.json")" = "2" ] && ok "init max_rounds=2" || no "init max_rounds"
OUTR="$(bash "$LOOP" round next)"
echo "$OUTR" | grep -q "ROUND=2/2" && ok "round next → 2/2" || no "round next ($OUTR)"
OUTR2="$(bash "$LOOP" round next)"
echo "$OUTR2" | grep -q "ROUND-CAP" && ok "超 max_rounds → ROUND-CAP 熔断" || no "ROUND-CAP ($OUTR2)"
echo "$(ec)" | grep -q "PAUSED:needs-redirection" && ok "熔断自动 surface(exit-check=PAUSED,机器不靠自觉)" || no "熔断 surface ($(ec))"
# cover 不带 --evidence 不蒸发元素(与 step done 同坑回归)
bash "$LOOP" resume >/dev/null
bash "$LOOP" checklist add --item x1 --source s:1 >/dev/null
bash "$LOOP" checklist cover --item x1 >/dev/null
[ "$(jq -r '.checklist|length' "${STATE_SUBDIR}/loop-state.json")" = "1" ] && ok "cover 不带 evidence 清单元素保留(不蒸发)" || no "清单蒸发!"
bash "$LOOP" close >/dev/null

# ===== fail-closed:坏 kind / 缺参 =====
if bash "$LOOP" init --kind bogus >/dev/null 2>&1; then no "坏 kind 被拒"; else ok "坏 kind 被拒"; fi
if bash "$LOOP" surface --kind needs-context >/dev/null 2>&1; then no "surface 缺 question 被拒"; else ok "surface 缺 question 被拒"; fi

# ===== fail-open 防护:上游 jq 失败不把状态截成 0 字节(违"不搞静默兜底")=====
LF="${STATE_SUBDIR}/loop-state.json"
bash "$LOOP" init --kind review >/dev/null
SZB="$(wc -c < "$LF")"
# 非数字 confidence → --argjson 失败 → 应拒写、退非零、原文件保留
if bash "$LOOP" finding add --severity Critical --confidence "8/10" --locator a:1 >/dev/null 2>&1; then no "非数字 confidence 应被拒"; else ok "非数字 confidence 被拒(--argjson 失败)"; fi
[ "$(wc -c < "$LF")" = "$SZB" ] && ok "拒写后原状态保留(没截空)" || no "状态被截空!"
jq -e . "$LF" >/dev/null 2>&1 && ok "拒写后状态仍合法 JSON" || no "状态损坏"
# 损坏状态 → exit-check 报 CORRUPT(不假 PAUSED 放行)
echo 'garbage{' > "$LF"
[ "$(ec)" = "CORRUPT:loop-state 空/非法 JSON" ] && ok "损坏状态 exit-check 报 CORRUPT(不假 PAUSED)" || no "CORRUPT ($(ec))"

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" -eq 0 ]
