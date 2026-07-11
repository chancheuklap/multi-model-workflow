#!/usr/bin/env bash
# 三个 hook 空跑:SessionStart 分诊 / PreToolUse 红线 / PostToolUse 记进度。
# (审 loop 完工不再用 SubagentStop 看守,改由 flow.sh handoff 确定性闸把关,见 test_flow.sh。)
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS="$SCRIPT_DIR/../../hooks"
LOOP="$SCRIPT_DIR/../loop.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
# 跑 hook,回 exit code
run_hook() { local h="$1" payload="$2"; printf '%s' "$payload" | bash "$HOOKS/$h" >/dev/null 2>&1; echo $?; }
# 跑 hook,回 stdout(红线 ask 判定用:命中 → 吐 permissionDecision=ask JSON;放行 → 空)
hook_out() { local h="$1" payload="$2"; printf '%s' "$payload" | bash "$HOOKS/$h" 2>/dev/null || true; }
is_ask()    { hook_out guard-redline.sh "$1" | grep -q '"permissionDecision":[[:space:]]*"ask"'; }
is_allow()  { [ -z "$(hook_out guard-redline.sh "$1")" ] && [ "$(run_hook guard-redline.sh "$1")" = "0" ]; }
pl() { printf '{"tool_input":{"command":"%s"}}' "$1"; }

echo "=== test_hooks.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q -b main; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s

# ===== guard-redline(PreToolUse,permissionDecision=ask 由用户亲批,无令牌可自铸)=====
# 主分支(main)上:push → ask;本地 merge 放行(可逆、不出站,不打断无人值守自动推进)
is_allow "$(pl 'git merge feat --no-ff')" && ok "主分支本地 merge → 放行(不拦本地合并)" || no "主分支 merge 应放行"
is_ask "$(pl 'git push origin main')" && ok "push → ask" || no "push ask"
is_allow "$(pl 'git status')" && ok "git status → 放行" || no "safe 放行"
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
# 任意分支 merge 都放行(本地不出站);push 在任意分支仍 → ask(出站)
git checkout -q -b task/x
is_allow "$(pl 'git merge plan-a --no-ff')" && ok "任务分支 merge → 放行" || no "任务分支 merge 误拦"
is_ask "$(pl 'git push origin task/x')" && ok "任务分支 push 仍 → ask(出站)" || no "任务分支 push"
git checkout -q main

# ===== record-step(PostToolUse commit)=====
bash "$LOOP" close >/dev/null   # 幂等清任何残留 loop 再起新 loop(init 拒覆盖未收束 loop)
bash "$LOOP" init --kind execution >/dev/null
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

# ===== session-triage(SessionStart 分诊)=====
# 非 git 目录 → 静默退出(不注入不报错)
NOGIT="$(mktemp -d)"
OUT="$(cd "$NOGIT" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"; EC=$?
[ "$EC" = "0" ] && [ -z "$OUT" ] && ok "非 git 目录 → 静默 exit 0" || no "非 git 静默 ($EC/$OUT)"
rm -rf "$NOGIT"
# 主仓库无在飞任务 → 只注入分诊指令
rm -f ${STATE_SUBDIR}/task.json ${STATE_SUBDIR}/loop-state.json
OUT="$(printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "会话分诊" && ok "主仓库注入分诊指令(正式进流程/简单直接答)" || no "分诊指令"
echo "$OUT" | grep -q "在飞任务" && no "无在飞不该列清单" || ok "无在飞任务不列清单"
# 主仓库有在飞 worktree(有 manifest 才算)→ 追加在飞清单
mkdir -p ${WT_REL}/w1/${STATE_SUBDIR}
printf '{"slug":"w1","scenario":"develop","phase":"design","status":"active","worktree_path":"%s"}' "$TMP/${WT_REL}/w1" \
  > ${WT_REL}/w1/${STATE_SUBDIR}/task.json
OUT="$(printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "在飞任务" && echo "$OUT" | grep -q "w1.*phase=design" && ok "有在飞任务 → 列清单(slug/phase)" || no "在飞清单"
# 在管任务 worktree 内 → 报身份+续跑入口
WTREPO="$(mktemp -d)"
( cd "$WTREPO" && git init -q && mkdir -p ${STATE_SUBDIR} \
  && printf '{"slug":"t9","scenario":"bug","phase":"build","status":"active"}' > ${STATE_SUBDIR}/task.json )
OUT="$(cd "$WTREPO" && printf '{}' | bash "$HOOKS/session-triage.sh" 2>&1)"
echo "$OUT" | grep -q "在管任务 worktree:t9" && echo "$OUT" | grep -q "phase=build" && ok "在管 worktree → 报身份+续跑" || no "在管身份"
rm -rf "$WTREPO"

# ===== hooks.json 接线(宿主分组:Execute=Droid 无 if / Bash=Claude 带 if 前筛)=====
HJ="$HOOKS/hooks.json"
python3 -m json.tool "$HJ" >/dev/null 2>&1 && ok "hooks.json JSON 合法" || no "hooks.json JSON 不合法"
noif_exec="$(jq -r '[.hooks.PreToolUse[],.hooks.PostToolUse[]|select(.matcher=="Execute")|.hooks[]|has("if")]|any' "$HJ")"
[ "$noif_exec" = "false" ] && ok "Execute 组(Droid)不带 if(Droid 忽略 if,不能依赖它筛)" || no "Execute 组混入 if"
allif_bash="$(jq -r '[.hooks.PreToolUse[],.hooks.PostToolUse[]|select(.matcher=="Bash")|.hooks[]|has("if")]|all' "$HJ")"
[ "$allif_bash" = "true" ] && ok "Bash 组(Claude)每条都带 if 前筛" || no "Bash 组有条目缺 if"
# 红线 if 关键词集必须覆盖 guard-redline 全部 ask 命令(漏一条 = Claude 侧红线漏拦)
kw="$(jq -r '.hooks.PreToolUse[]|select(.matcher=="Bash")|.hooks[].if' "$HJ" | sed -E 's/^Bash\(\*//; s/\*\)$//' | paste -sd'|' -)"
miss=0
for c in 'git push origin main' 'git -c core.hooksPath=/dev/null push origin main' 'gh pr merge 123 --merge' './deploy.sh' 'bash deploy-prod.sh' 'kubectl apply -f k8s/' 'terraform apply' 'terraform destroy'; do
  printf '%s' "$c" | grep -Eq "$kw" || { miss=1; echo "  漏筛: $c"; }
done
[ "$miss" = "0" ] && ok "if 关键词集覆盖全部红线命令(无漏筛)" || no "if 关键词集漏筛红线命令"
rsif="$(jq -r '.hooks.PostToolUse[]|select(.matcher=="Bash")|.hooks[0].if' "$HJ")"
[ "$rsif" = "Bash(git commit:*)" ] && ok "record-step Bash 侧 if 只认 git commit" || no "record-step if 异常 ($rsif)"

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" -eq 0 ]
