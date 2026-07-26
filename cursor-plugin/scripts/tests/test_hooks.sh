#!/usr/bin/env bash
# 三个 hook 空跑:sessionStart 分诊(三源回报+新鲜度)/ beforeShell 红线 / afterShell 记进度。
# (相位锚 UserPromptSubmit 已拆:逐条消息注锚干扰讨论态,开场回报一次即可。)
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.cursor/multi-model-workflow}"
WT_REL="${WT_REL:-.cursor/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS="$SCRIPT_DIR/../../hooks"
LOOP="$SCRIPT_DIR/../loop.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
# 跑 hook,回 exit code
run_hook() { local h="$1" payload="$2"; printf '%s' "$payload" | bash "$HOOKS/$h" >/dev/null 2>&1; echo $?; }
# 跑 hook,回 stdout(红线:命中 → permission/ask;放行 → permission/allow。兼容 Claude nested + Cursor flat)
hook_out() { local h="$1" payload="$2"; printf '%s' "$payload" | bash "$HOOKS/$h" 2>/dev/null || true; }
is_ask()    { hook_out guard-redline.sh "$1" | grep -Eq '"permission":[[:space:]]*"ask"|"permissionDecision":[[:space:]]*"ask"'; }
is_allow()  {
  local out ec
  out="$(hook_out guard-redline.sh "$1")"
  ec="$(run_hook guard-redline.sh "$1")"
  [ "$ec" = "0" ] && printf '%s' "$out" | grep -Eq '"permission":[[:space:]]*"allow"' \
    && ! printf '%s' "$out" | grep -Eq '"permission":[[:space:]]*"ask"|"permissionDecision":[[:space:]]*"ask"'
}
# 默认测 Cursor 原生 payload;另用 pl_cc 覆盖 Claude 兼容路径
pl() { printf '{"command":"%s","cwd":"/tmp","sandbox":false}' "$1"; }
pl_cc() { printf '{"tool_input":{"command":"%s"}}' "$1"; }

echo "=== test_hooks.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q -b main; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s

# ===== guard-redline(PreToolUse,permissionDecision=ask 由用户亲批,无令牌可自铸)=====
# 主分支(main)上:push → ask;本地 merge 放行(可逆、不出站,不打断无人值守自动推进)
is_allow "$(pl 'git merge feat --no-ff')" && ok "主分支本地 merge → 放行(不拦本地合并)" || no "主分支 merge 应放行"
is_ask "$(pl 'git push origin main')" && ok "push → ask" || no "push ask"
is_allow "$(pl 'git status')" && ok "git status → 放行" || no "safe 放行"
is_ask "$(pl_cc 'git push origin main')" && ok "Claude payload push → ask(兼容)" || no "Claude payload push"
is_allow "$(pl_cc 'git status')" && ok "Claude payload status → 放行(兼容)" || no "Claude payload status"
# 老正则的绕过口全堵上
is_ask "$(pl 'git -c core.hooksPath=/dev/null push origin main')" && ok "git -c … push(插参数)→ ask" || no "git -c push 绕过"
is_ask "$(pl 'gh pr merge 123 --merge')" && ok "gh pr merge(GitHub 侧合并)→ ask" || no "gh pr merge 绕过"
is_ask "$(pl './deploy.sh')" && ok "./deploy.sh → ask" || no "deploy.sh 绕过"
is_ask "$(pl 'bash deploy-prod.sh')" && ok "deploy-prod.sh → ask" || no "deploy- 绕过"
is_ask "$(pl 'kubectl apply -f k8s/')" && ok "kubectl apply → ask" || no "kubectl 绕过"
is_ask "$(pl 'terraform apply')" && ok "terraform apply → ask" || no "terraform 绕过"
is_allow "$(pl 'git -C /elsewhere merge feat')" && ok "git -C merge → 放行(本地 merge 一律不拦)" || no "git -C merge 应放行"
is_allow "$(pl 'cat deployment.yaml')" && ok "deployment.yaml(非部署动作)→ 放行" || no "deployment 误伤"
is_allow "$(pl 'git pull origin main')" && ok "git pull(入站)→ 放行" || no "pull 误伤"
# 引号串里的动词不是动作(v1 裸 grep 误拦根因):commit message 提 push/deploy/merge → 放行
is_allow "$(pl 'git commit -m \"docs: deploy guide\"')" && ok "commit message 含 deploy → 放行(剥引号)" || no "commit deploy 误拦"
is_allow "$(pl 'git commit -m \"please push after review\"')" && ok "commit message 含 push → 放行(剥引号)" || no "commit push 误拦"
is_allow "$(pl "echo 'how to merge branches' > note.txt")" && ok "单引号文本含 merge → 放行(剥引号)" || no "echo merge 误拦"
# 命令位判定:关键词落在参数位(echo/printf/grep 文本)不是动作 → 放行;包装器/复合命令里的真动作仍拦
is_allow "$(pl 'echo git push origin main')" && ok "echo 参数位文本 git push → 放行(命令位判定)" || no "echo git push 误拦"
is_allow "$(pl 'grep -rn git.push docs/')" && ok "grep 模式含 push → 放行" || no "grep push 误拦"
is_ask "$(pl 'timeout 30 git push origin main')" && ok "timeout 包装的 git push → ask" || no "timeout git push 绕过"
is_ask "$(pl 'cd /x && git push')" && ok "复合命令中段 git push → ask" || no "复合 git push 绕过"
# 任意分支 merge 都放行(本地不出站);push 在任意分支仍 → ask(出站)
git checkout -q -b task/x
is_allow "$(pl 'git merge plan-a --no-ff')" && ok "任务分支 merge → 放行" || no "任务分支 merge 误拦"
is_ask "$(pl 'git push origin task/x')" && ok "任务分支 push 仍 → ask(出站)" || no "任务分支 push"
git checkout -q main
# 硬化回归(v6.15):shell 关键字/结构符段、包装器选项、引号打散动词、eval/-c 内代码、gh api 合并
is_ask "$(pl 'if git push; then :; fi')" && ok "if git push; then → ask(关键字段不再放行)" || no "if git push 绕过"
is_ask "$(pl 'exec git push')" && ok "exec git push → ask" || no "exec 绕过"
is_ask "$(pl '{ git push; }')" && ok "{ git push; } → ask" || no "花括号段绕过"
is_ask "$(pl 'git \"push\" origin main')" && ok "git \"push\"(引号包动词)→ ask" || no "引号动词绕过"
is_ask "$(pl 'timeout -k 5 30 git push')" && ok "timeout -k 5 30 git push → ask(包装器选项剥净)" || no "timeout 选项绕过"
is_ask "$(pl 'xargs -I{} git push {}')" && ok "xargs -I{} git push → ask" || no "xargs 选项绕过"
is_ask "$(pl 'nice git push')" && ok "nice git push → ask" || no "nice 绕过"
is_ask "$(pl 'gh api repos/o/r/pulls/1/merge -X PUT')" && ok "gh api pulls/*/merge → ask(GitHub 侧合并)" || no "gh api 合并绕过"
is_ask "$(pl "bash -c 'git push'")" && ok "bash -c 'git push' → ask(-c 内代码)" || no "bash -c 绕过"
is_allow "$(pl 'git stash push -m wip')" && ok "git stash push → 放行(子命令位判定)" || no "stash push 误拦"
is_allow "$(pl 'git log --grep=push')" && ok "git log --grep=push → 放行" || no "log --grep 误拦"
is_allow "$(pl 'kubectl apply --dry-run=client -f x.yaml')" && ok "kubectl apply --dry-run → 放行(只读校验)" || no "dry-run 误拦"
is_allow "$(pl 'cat > runbook.md <<EOF\ngit push origin main\nEOF')" && ok "heredoc 正文 git push → 放行(剥正文)" || no "heredoc 正文误拦"

# ===== record-step(PostToolUse commit)=====
bash "$LOOP" close >/dev/null   # 幂等清任何残留 loop 再起新 loop(init 拒覆盖未收束 loop)
bash "$LOOP" init >/dev/null
bash "$LOOP" step add --id 2.1 --desc x >/dev/null
echo change > c.txt; git add -A; git commit -qm "Pack 2.1: do the thing"
P_COMMIT='{"tool_input":{"command":"git commit -m \"Pack 2.1: do the thing\""}}'
run_hook record-step.sh "$P_COMMIT" >/dev/null
st="$(jq -r '.steps[]|select(.id=="2.1")|.status' ${STATE_SUBDIR}/loop-state.json)"
[ "$st" = "done" ] && ok "提交 Pack 2.1 → 记 step done" || no "记 step done ($st)"
sha="$(jq -r '.steps[]|select(.id=="2.1")|.commit' ${STATE_SUBDIR}/loop-state.json)"
[ -n "$sha" ] && [ "$sha" != "null" ] && ok "记下 commit sha" || no "记 sha"
# 非 commit 命令:hook 早退(exit 0)且不碰 loop-state(record-step.sh:11 grep 不中即 exit 0)
before="$(cat ${STATE_SUBDIR}/loop-state.json)"
ec_noop="$(run_hook record-step.sh '{"tool_input":{"command":"ls -la"}}')"
after="$(cat ${STATE_SUBDIR}/loop-state.json)"
[ "$ec_noop" = "0" ] && [ "$before" = "$after" ] && ok "非 commit 命令 → 早退 exit 0、loop-state 不变" || no "非 commit 应早退不改 state (ec=$ec_noop)"
# echo 文本里提到 git commit + Pack N.M:参数位不是动作,不得误记进度
bash "$LOOP" step add --id 2.9 --desc probe >/dev/null
before="$(cat ${STATE_SUBDIR}/loop-state.json)"
run_hook record-step.sh '{"tool_input":{"command":"echo git commit -m Pack 2.9: fake text"}}' >/dev/null
after="$(cat ${STATE_SUBDIR}/loop-state.json)"
[ "$before" = "$after" ] && ok "echo 文本含 git commit+Pack → 不记(命令位判定)" || no "echo 文本误记进度"
# 真值化回归(v6.15):Pack 从 HEAD 取,不信命令文本
# a) commit 成功但命令后段有别的 Pack 字样 → 只记 HEAD 真 Pack
bash "$LOOP" step add --id 3.1 --desc real >/dev/null
bash "$LOOP" step add --id 9.9 --desc decoy >/dev/null
echo v3 > c.txt; git add -A; git commit -qm "Pack 3.1: real work"
run_hook record-step.sh '{"tool_input":{"command":"git commit -m \"Pack 3.1: real work\" && echo Pack 9.9 next"}}' >/dev/null
[ "$(jq -r '.steps[]|select(.id=="3.1")|.status' ${STATE_SUBDIR}/loop-state.json)" = "done" ] && ok "HEAD 真 Pack 3.1 → 记 done" || no "真 Pack 未记"
[ "$(jq -r '.steps[]|select(.id=="9.9")|.status' ${STATE_SUBDIR}/loop-state.json)" = "pending" ] && ok "命令文本诱饵 Pack 9.9 → 不记(HEAD 真值)" || no "诱饵 Pack 被误记"
# b) commit 失败(HEAD 没动、信息里无该 Pack)→ 不记
bash "$LOOP" step add --id 4.1 --desc failcase >/dev/null
run_hook record-step.sh '{"tool_input":{"command":"git commit -m \"Pack 4.1: never landed\""}}' >/dev/null
[ "$(jq -r '.steps[]|select(.id=="4.1")|.status' ${STATE_SUBDIR}/loop-state.json)" = "pending" ] && ok "commit 失败 → 不记(sha 不脏)" || no "失败提交被误记"
# c) git -C <path> commit 形态 → 记(全局选项剥离)
bash "$LOOP" step add --id 5.1 --desc cdir >/dev/null
echo v5 > c.txt; git add -A; git commit -qm "Pack 5.1: via -C"
( cd / && printf '{"tool_input":{"command":"git -C %s commit -m \\"Pack 5.1: via -C\\""}}' "$TMP" | bash "$HOOKS/record-step.sh" ) >/dev/null 2>&1
[ "$(jq -r '.steps[]|select(.id=="5.1")|.status' ${STATE_SUBDIR}/loop-state.json)" = "done" ] && ok "git -C <path> commit → 记(跨目录真值)" || no "git -C commit 漏记"

# ===== session-triage(SessionStart 分诊)=====
# 非 git 目录 → 静默退出(不注入不报错)
NOGIT="$(mktemp -d)"
OUT="$(cd "$NOGIT" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"; EC=$?
[ "$EC" = "0" ] && [ -z "$OUT" ] && ok "非 git 目录 → 静默 exit 0" || no "非 git 静默 ($EC/$OUT)"
rm -rf "$NOGIT"
# 主仓库无 manifest → 静默；默认直接处理，不用系统注入把每个请求推向 MMW。
rm -f ${STATE_SUBDIR}/task.json ${STATE_SUBDIR}/loop-state.json
OUT="$(printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
[ -z "$OUT" ] && ok "未在管主仓库不注入 MMW 分诊" || no "未在管主仓库应静默($OUT)"
# 即使磁盘上有在飞 worktree，也只在用户明确续跑、主动执行 mmw where 时发现。
mkdir -p ${WT_REL}/w1/${STATE_SUBDIR}
printf '{"slug":"w1","scenario":"develop","phase":"design","status":"active","worktree_path":"%s"}' "$TMP/${WT_REL}/w1" \
  > ${WT_REL}/w1/${STATE_SUBDIR}/task.json
OUT="$(printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
[ -z "$OUT" ] && ok "未在管主仓库不主动扫描注入在飞任务" || no "在飞任务不应自动注入($OUT)"
# 在管任务 worktree 内 → 报身份+续跑入口
WTREPO="$(mktemp -d)"
( cd "$WTREPO" && git init -q && mkdir -p ${STATE_SUBDIR} \
  && printf '{"slug":"t9","scenario":"bug","phase":"build","status":"active"}' > ${STATE_SUBDIR}/task.json )
OUT="$(cd "$WTREPO" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "在管任务 worktree: slug=t9" && echo "$OUT" | grep -q "phase=build" && ok "在管 worktree → 报身份+续跑" || no "在管身份"
echo "$OUT" | grep -q "无关写操作不要在此 worktree 执行" && ok "在管 worktree 禁止无关写操作污染" || no "在管 worktree 缺写操作边界"
echo "$OUT" | grep -q "位置只是书签不是命令" && ok "在管 worktree 讲明书签语义(不锁死会话)" || no "书签语义"
echo "$OUT" | grep -q "上次做了" && no "无提交流水不该报上次做了" || ok "无提交流水不硬凑三源"
rm -rf "$WTREPO"
# 三源回报:①最近提交流水 ②书签注记 ③设计文档 Open Decisions 指引
WT3="$(mktemp -d)"
( cd "$WT3" && git init -q && git config user.email t@t && git config user.name t \
  && echo s>s && git add -A && git commit -qm base )
BASE3="$(cd "$WT3" && git rev-parse HEAD)"
( cd "$WT3" && echo a>a && git add -A && git commit -qm "fix: 修掉登录态丢失" \
  && echo b>b && git add -A && git commit -qm "feat: 加会员到期提醒" )
mkdir -p "$WT3/${STATE_SUBDIR}" "$WT3/docs/design"
printf '# d\n## Open Decisions\n- 计费口径未定\n' > "$WT3/docs/design/t3.md"
jq -n --arg base "$BASE3" '{slug:"t3",scenario:"develop",phase:"design",status:"active",
  base_commit:$base, note:{text:"下一步对齐计费口径", at:"2026-07-15T00:00:00Z"},
  docs:{design:"docs/design/t3"}}' > "$WT3/${STATE_SUBDIR}/task.json"
OUT="$(cd "$WT3" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "上次做了:.*会员到期提醒" && ok "三源①:最近提交流水回报" || no "三源① 提交流水 ($OUT)"
echo "$OUT" | grep -q "现场注记:下一步对齐计费口径" && ok "三源②:note 书签回报" || no "三源② 书签"
echo "$OUT" | grep -q "待拍板:.*docs/design/t3.md.*Open Decisions" && ok "三源③:Open Decisions 指引" || no "三源③ 待拍板"
# 新鲜度:旧版本/超 7 天 → 开场警告先 /reassess
jq '.plugin_version="0.0.1" | .updated_at="2026-01-01T00:00:00Z"' "$WT3/${STATE_SUBDIR}/task.json" > "$WT3/tj.tmp" && mv "$WT3/tj.tmp" "$WT3/${STATE_SUBDIR}/task.json"
OUT="$(cd "$WT3" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "旧版 plugin" && ok "版本不符开场警告(别把旧指令当最新)" || no "旧版警告"
echo "$OUT" | grep -q "天没动" && ok "超 7 天开场警告(先 /reassess)" || no "时效警告"
# 强无人档:开场声明合同 + 用户回来任意消息即恢复
jq '.attendance="unattended"' "$WT3/${STATE_SUBDIR}/task.json" > "$WT3/tj.tmp" && mv "$WT3/tj.tmp" "$WT3/${STATE_SUBDIR}/task.json"
OUT="$(cd "$WT3" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "强无人档" && echo "$OUT" | grep -q "任意消息即恢复" && ok "unattended 开场声明退出语义" || no "unattended 声明"
rm -rf "$WT3"

# ===== hooks.json Cursor 原生接线 =====
HJ="$HOOKS/hooks.json"
python3 -m json.tool "$HJ" >/dev/null 2>&1 && ok "hooks.json JSON 合法" || no "hooks.json JSON 不合法"
jq -e '.hooks.sessionStart and .hooks.beforeShellExecution and .hooks.afterShellExecution' "$HJ" >/dev/null \
  && ok "注册 sessionStart/beforeShellExecution/afterShellExecution" || no "缺 Cursor hook 事件"
jq -e '.. | strings | select(test("CURSOR_PLUGIN_ROOT"))' "$HJ" >/dev/null 2>&1 &&
  ok "hook 使用 CURSOR_PLUGIN_ROOT" || no "plugin root 未接线"
[ "$(jq -r '.hooks | has("UserPromptSubmit")' "$HJ")" = "false" ] && ok "无 UserPromptSubmit" || no "UserPromptSubmit 残留"

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" -eq 0 ]
