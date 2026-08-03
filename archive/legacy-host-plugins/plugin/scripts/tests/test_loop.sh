#!/usr/bin/env bash
# loop.sh 执行账本空跑:init 无参/值守缓存、step 记账、软停×在场、冒泡、status 只报不否决、close 幂等。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/../loop.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
st() { bash "$LOOP" status; }   # status 输出(只报,不当闸)

echo "=== test_loop.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s
LF="${STATE_SUBDIR}/loop-state.json"

# ===== init:无参、只有执行账本、缺省 attended =====
[ "$(st)" = "NO-LOOP" ] && ok "无账本 status=NO-LOOP" || no "NO-LOOP ($(st))"
if bash "$LOOP" init --kind execution >/dev/null 2>&1; then no "init 带旧参数应被拒"; else ok "init 拒绝旧 --kind 形态(审查不记账)"; fi
bash "$LOOP" init >/dev/null
[ "$(jq -r .kind "$LF")" = "execution" ] && ok "账本 kind 固定 execution" || no "kind"
[ "$(jq -r .attendance "$LF")" = "attended" ] && ok "无 task.json 缺省 attended(不冒充放权)" || no "缺省 attended ($(jq -r .attendance "$LF"))"
# init 守卫:已有未收束账本拒覆盖(防抹掉派发映射)
if bash "$LOOP" init >/dev/null 2>&1; then no "已有账本再 init 应被拒"; else ok "init 守卫:未收束账本拒覆盖"; fi

# ===== init 从外层 task.json 读值守(权威在 task.json,loop 只是派生缓存) =====
bash "$LOOP" close >/dev/null
mkdir -p "$STATE_SUBDIR"
echo '{"attendance":"afk"}' > "$STATE_SUBDIR/task.json"
bash "$LOOP" init >/dev/null
[ "$(jq -r .attendance "$LF")" = "afk" ] && ok "init 从 task.json 读入 afk" || no "init 读 task.json"
rm -f "$STATE_SUBDIR/task.json"

# ===== step 记账 + status 完成度 =====
bash "$LOOP" step add --id 1.1 --desc a >/dev/null
bash "$LOOP" step add --id 1.2 --desc b >/dev/null
[ "$(st)" = "steps=0/2 remaining=1.1,1.2" ] && ok "status 报剩余步(只报不否决)" || no "status 剩余 ($(st))"
bash "$LOOP" step done --id 1.1 --commit abc >/dev/null
[ "$(st)" = "steps=1/2 remaining=1.2" ] && ok "做一半 status=1/2" || no "做一半 ($(st))"
bash "$LOOP" step done --id 1.2 >/dev/null
[ "$(st)" = "steps=2/2 remaining=none" ] && ok "全 done remaining=none" || no "全 done ($(st))"
# 回归:step done 不带 --commit 不许把元素从步账蒸发(旧 jq select 写法之坑)
[ "$(jq -r '.steps|length' "$LF")" = "2" ] && ok "done 不带 commit 步账元素保留(不蒸发)" || no "步账蒸发!($(jq -r '.steps|length' "$LF"))"
[ "$(jq -r '.steps[1].commit' "$LF")" = "null" ] && ok "无 commit 时字段保持 null" || no "commit 字段"
if bash "$LOOP" step done --id ghost >/dev/null 2>&1; then no "done 不存在的 step 应被拒"; else ok "done 不存在的 step 被拒"; fi

# ===== 步账记 plan/worktree(断点恢复认哪步派到哪) =====
bash "$LOOP" step add --id planA --desc "计划A" --plan docs/plans/x/001.md --worktree /wt/planA >/dev/null
[ "$(jq -r '.steps[2].plan' "$LF")" = "docs/plans/x/001.md" ] && ok "步账记 plan 路径" || no "step.plan 未记"
[ "$(jq -r '.steps[2].worktree' "$LF")" = "/wt/planA" ] && ok "步账记子 worktree" || no "step.worktree 未记"
[ "$(jq -r '.steps[0].plan' "$LF")" = "null" ] && ok "无 plan 步记 null(小改步兼容)" || no "step.plan 应 null"

# ===== 软停 × 在场开关 =====
bash "$LOOP" attendance --mode unattended >/dev/null
[ "$(jq -r .attendance "$LF")" = "unattended" ] && ok "attendance 接受 unattended" || no "attendance unattended"
# afk/unattended:自决+留痕,不写 pause、不停
bash "$LOOP" attendance --mode afk >/dev/null
OUT="$(bash "$LOOP" softstop --question "用默认超时?" --default 30s --at-step 1.1)"
echo "$OUT" | grep -q "AUTO-DECIDED" && ok "afk 软停 → 自决" || no "afk 自决 ($OUT)"
[ "$(jq -r '.decisions|length' "$LF")" = "1" ] && ok "afk 自决留痕(decisions)" || no "afk 留痕"
[ "$(jq -r '.pause' "$LF")" = "null" ] && ok "afk 不写 pause、不停" || no "afk 不停"
# attended:写 pause、停
bash "$LOOP" attendance --mode attended >/dev/null
OUT2="$(bash "$LOOP" softstop --question "用默认超时?" --at-step 1.1)"
echo "$OUT2" | grep -q "PAUSED-SOFT" && ok "在场软停 → 停下问" || no "在场软停 ($OUT2)"
[ "$(st)" = "PAUSED:soft" ] && ok "停着 status=PAUSED:soft" || no "PAUSED ($(st))"
bash "$LOOP" resume >/dev/null
[ "$(jq -r '.pause' "$LF")" = "null" ] && ok "resume 清 pause" || no "resume 清"

# ===== 冒泡:永远停,不分在场 =====
bash "$LOOP" attendance --mode afk >/dev/null
bash "$LOOP" surface --kind needs-redirection --question "方向是不是错了?" >/dev/null
[ "$(st)" = "PAUSED:needs-redirection" ] && ok "冒泡 afk 也停(needs-redirection)" || no "冒泡停 ($(st))"
bash "$LOOP" resume >/dev/null
bash "$LOOP" surface --kind needs-context --question "缺哪份输入?" >/dev/null
[ "$(st)" = "PAUSED:needs-context" ] && ok "needs-context 也停" || no "needs-context ($(st))"
bash "$LOOP" resume >/dev/null

# ===== close 幂等 + 收束删账本 =====
[ -f "$LF" ] && ok "close 前 loop-state 在" || no "close 前应有 loop-state"
echo "$(bash "$LOOP" close)" | grep -q "CLOSED" && ok "close 报 CLOSED" || no "close 回执"
[ ! -f "$LF" ] && ok "close 删掉 loop-state" || no "close 未删 loop-state"
echo "$(bash "$LOOP" close)" | grep -q "CLOSED" && [ ! -f "$LF" ] && ok "close 幂等(无账本也安静退)" || no "close 非幂等"

# ===== fail-closed:缺参/坏参 =====
bash "$LOOP" init >/dev/null
if bash "$LOOP" surface --kind needs-context >/dev/null 2>&1; then no "surface 缺 question 应被拒"; else ok "surface 缺 question 被拒"; fi
if bash "$LOOP" surface --kind bogus --question q >/dev/null 2>&1; then no "surface 坏 kind 应被拒"; else ok "surface 坏 kind 被拒"; fi
if bash "$LOOP" attendance --mode bogus >/dev/null 2>&1; then no "attendance 坏 mode 应被拒"; else ok "attendance 坏 mode 被拒"; fi
if bash "$LOOP" step add --desc x >/dev/null 2>&1; then no "step add 缺 id 应被拒"; else ok "step add 缺 id 被拒"; fi

# ===== fail-open 防护:损坏状态 status 报 CORRUPT(不假装正常) =====
echo 'garbage{' > "$LF"
[ "$(st)" = "CORRUPT:loop-state 空/非法 JSON" ] && ok "损坏状态 status 报 CORRUPT" || no "CORRUPT ($(st))"
rm -f "$LF"

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" -eq 0 ]
