#!/usr/bin/env bash
# steer.sh 控制面:unattended 门禁(fail-closed 不降级)、attend 自由切、side-finding 落盘、loop 同步。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STEER="$SCRIPT_DIR/../steer.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_steer.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s
SD=.cursor/multi-model-workflow; mkdir -p "$SD"
MAN="$SD/task.json"

PHASES='["investigate","propose","design","to-issue","plan","build","closing"]'
mkman() {  # $1=phase_index $2=status
  jq -n --argjson ph "$PHASES" --argjson pi "$1" --arg st "$2" \
    '{schema_version:"1",slug:"demo",scenario:"develop",phases:$ph,phase:($ph[$pi]),phase_index:$pi,status:$st,attendance:"afk",unattended_policy:null,open_items:[]}' > "$MAN"
}

# 设计未过门(phase_index=2 = design 本阶段,未越过)→ 拒
mkman 2 active
if bash "$STEER" unattended enter >/dev/null 2>&1; then no "设计未过门应拒 unattended"; else ok "设计未过门 → 拒绝进入 unattended"; fi
[ "$(jq -r .attendance "$MAN")" = "afk" ] && ok "拒绝后 mode 仍 afk(不静默降级)" || no "拒绝后不该改 mode"

# 计划未过门(phase_index=4 = plan 本阶段)→ 拒
mkman 4 active
if bash "$STEER" unattended enter >/dev/null 2>&1; then no "计划未过门应拒"; else ok "计划未过门 → 拒绝进入"; fi

# 设计+计划都过(phase_index=5 = build),但有未答 HITL(waiting-user)→ 拒
mkman 5 waiting-user
if bash "$STEER" unattended enter >/dev/null 2>&1; then no "未答 HITL 应拒"; else ok "未答 HITL(waiting-user)→ 拒绝进入"; fi

# 全部满足(phase_index=5,active)→ 进
mkman 5 active
OUT="$(bash "$STEER" unattended enter 2>&1)"
echo "$OUT" | grep -q "UNATTENDED-ENTERED" && ok "门禁全过 → 进入 unattended" || no "应进入 ($OUT)"
[ "$(jq -r .attendance "$MAN")" = "unattended" ] && ok "task.json.attendance=unattended" || no "mode 未写"
[ "$(jq -r '.unattended_policy.review_fail' "$MAN")" = "rework_then_hard_stop" ] && ok "policy 写盘(默认 review_fail)" || no "policy 未写"

# status 报告(先捕获再 grep:steer 多行输出,grep -q 早关管道会触发 SIGPIPE+pipefail)
ST="$(bash "$STEER" unattended status)"
echo "$ST" | grep -q "mode=unattended" && ok "unattended status 报 mode" || no "status"

# exit → 回 attended
bash "$STEER" unattended exit >/dev/null
[ "$(jq -r .attendance "$MAN")" = "attended" ] && ok "unattended exit → attended" || no "exit"

# attend 自由切
bash "$STEER" attend --mode afk >/dev/null
[ "$(jq -r .attendance "$MAN")" = "afk" ] && ok "attend --mode afk" || no "attend afk"
if bash "$STEER" attend --mode unattended >/dev/null 2>&1; then no "attend 不该接受 unattended(须走门禁)"; else ok "attend 拒 unattended(强制走门禁)"; fi

# loop-state 同步:有活动 loop 时切档同步到 loop-state
cat > "$SD/loop-state.json" <<'J'
{"schema_version":"1","kind":"execution","round":1,"max_rounds":0,"steps":[],"checklist":[],"findings":[],"decisions":[],"pause":null,"attendance":"afk"}
J
mkman 5 active
bash "$STEER" unattended enter >/dev/null
[ "$(jq -r .attendance "$SD/loop-state.json")" = "unattended" ] && ok "进 unattended 同步到活动 loop-state" || no "loop 同步"

# side-finding 落 open_items(带 disposition)
bash "$STEER" side-finding record --tag bug --disposition fix --finding "空指针" >/dev/null
bash "$STEER" side-finding record --tag out-of-scope --disposition issue --finding "样式" >/dev/null
[ "$(jq -r '.open_items|length' "$MAN")" = "2" ] && ok "side-finding 落 open_items" || no "side-finding 落盘"
[ "$(jq -r '.open_items[0].disposition' "$MAN")" = "fix_now" ] && ok "fix → fix_now" || no "fix 映射"
[ "$(jq -r '.open_items[1].disposition' "$MAN")" = "defer_issue" ] && ok "issue → defer_issue" || no "issue 映射"
if bash "$STEER" side-finding record --tag bug --disposition maybe >/dev/null 2>&1; then no "非法 disposition 应拒"; else ok "非法 disposition 被拒"; fi

# 无 task.json → 报错不伪造
cd "$TMP"; rm -rf sub; mkdir sub; cd sub; git init -q
if bash "$STEER" unattended status >/dev/null 2>&1; then no "无 task.json 应报错"; else ok "无在管任务 → 报错(不伪造)"; fi

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" = 0 ]
