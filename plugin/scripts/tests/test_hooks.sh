#!/usr/bin/env bash
# 三个 hook 空跑:SubagentStop 看守 / PreToolUse 红线 / PostToolUse 记进度。
set -euo pipefail
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

# ===== guard-loop(SubagentStop)=====
# 无 loop-state → 放行
[ "$(run_hook guard-loop.sh '{}')" = "0" ] && ok "无 loop-state → 放行" || no "无 state 放行"
bash "$LOOP" init --kind execution >/dev/null
bash "$LOOP" step add --id 1.1 --desc a >/dev/null
[ "$(run_hook guard-loop.sh '{}')" = "2" ] && ok "没做完 → exit2 顶回去" || no "没做完 exit2"
bash "$LOOP" step done --id 1.1 >/dev/null
[ "$(run_hook guard-loop.sh '{}')" = "0" ] && ok "全 done → 放停" || no "全 done 放停"
bash "$LOOP" step add --id 1.2 --desc b >/dev/null
bash "$LOOP" attendance --mode attended >/dev/null
bash "$LOOP" softstop --question "?" --at-step 1.2 >/dev/null
[ "$(run_hook guard-loop.sh '{}')" = "0" ] && ok "PAUSED → 放停(等人)" || no "PAUSED 放停"
# 空转熔断:连续零进展顶回 ≥6 次 → 写 pause 交人、放停(不无限顶回)
bash "$LOOP" resume >/dev/null
for i in 1 2 3 4 5; do run_hook guard-loop.sh '{}' >/dev/null || true; done
[ "$(jq -r '.guard_blocks' .claude/multi-model-workflow/loop-state.json)" = "5" ] && ok "零进展顶回计数累加(5)" || no "guard_blocks 计数 ($(jq -r '.guard_blocks' .claude/multi-model-workflow/loop-state.json))"
[ "$(run_hook guard-loop.sh '{}')" = "0" ] && ok "第 6 次零进展 → 熔断放停" || no "空转熔断放停"
[ "$(jq -r '.pause.kind' .claude/multi-model-workflow/loop-state.json)" = "surface" ] && ok "熔断写 pause 交人(留痕)" || no "熔断 pause 留痕"
# 有进展 → 计数归 1(不误熔断)
bash "$LOOP" resume >/dev/null
bash "$LOOP" step add --id 1.3 --desc c >/dev/null
bash "$LOOP" step done --id 1.2 >/dev/null   # 账本进展:done 数变了
run_hook guard-loop.sh '{}' >/dev/null || true
[ "$(jq -r '.guard_blocks' .claude/multi-model-workflow/loop-state.json)" = "1" ] && ok "有进展 → 顶回计数归 1" || no "进展重置 ($(jq -r '.guard_blocks' .claude/multi-model-workflow/loop-state.json))"
# 损坏 loop-state → 看守 fail-closed(不放停),不把损坏当 PAUSED 静默放行
echo 'garbage{' > .claude/multi-model-workflow/loop-state.json
[ "$(run_hook guard-loop.sh '{}')" = "2" ] && ok "损坏 loop-state → 看守 exit2(fail-closed)" || no "损坏态看守 fail-closed"

# ===== guard-redline(PreToolUse,permissionDecision=ask 由用户亲批,无令牌可自铸)=====
# 主分支(main)上:merge/push → ask
is_ask "$(pl 'git merge feat --no-ff')" && ok "主分支 merge → ask(要人批)" || no "主分支 merge ask"
is_ask "$(pl 'git push origin main')" && ok "push → ask" || no "push ask"
is_allow "$(pl 'git status')" && ok "git status → 放行" || no "safe 放行"
# 老正则的绕过口全堵上
is_ask "$(pl 'git -c core.hooksPath=/dev/null push origin main')" && ok "git -c … push(插参数)→ ask" || no "git -c push 绕过"
is_ask "$(pl 'gh pr merge 123 --merge')" && ok "gh pr merge(GitHub 侧合并)→ ask" || no "gh pr merge 绕过"
is_ask "$(pl './deploy.sh')" && ok "./deploy.sh → ask" || no "deploy.sh 绕过"
is_ask "$(pl 'bash deploy-prod.sh')" && ok "deploy-prod.sh → ask" || no "deploy- 绕过"
is_ask "$(pl 'kubectl apply -f k8s/')" && ok "kubectl apply → ask" || no "kubectl 绕过"
is_ask "$(pl 'terraform apply')" && ok "terraform apply → ask" || no "terraform 绕过"
is_ask "$(pl 'git -C /elsewhere merge feat')" && ok "git -C merge(判不了目标)→ ask(fail-closed)" || no "git -C merge"
is_allow "$(pl 'cat deployment.yaml')" && ok "deployment.yaml(非部署动作)→ 放行" || no "deployment 误伤"
is_allow "$(pl 'git pull origin main')" && ok "git pull(入站)→ 放行" || no "pull 误伤"
# 任务分支上 merge 子分支 = 流程内动作(build B4 合 plan worktree),放行
git checkout -q -b task/x
is_allow "$(pl 'git merge plan-a --no-ff')" && ok "任务分支上 merge 子分支 → 放行(流程内)" || no "任务分支 merge 误拦"
is_ask "$(pl 'git push origin task/x')" && ok "任务分支 push 仍 → ask(出站)" || no "任务分支 push"
git checkout -q main

# ===== record-step(PostToolUse commit)=====
bash "$LOOP" close >/dev/null   # 清掉上一段(含损坏态)再起新 loop(init 拒覆盖未收束 loop)
bash "$LOOP" init --kind execution >/dev/null
bash "$LOOP" step add --id 2.1 --desc x >/dev/null
echo change > c.txt; git add -A; git commit -qm "Pack 2.1: do the thing"
P_COMMIT='{"tool_input":{"command":"git commit -m \"Pack 2.1: do the thing\""}}'
run_hook record-step.sh "$P_COMMIT" >/dev/null
st="$(jq -r '.steps[]|select(.id=="2.1")|.status' .claude/multi-model-workflow/loop-state.json)"
[ "$st" = "done" ] && ok "提交 Pack 2.1 → 记 step done" || no "记 step done ($st)"
sha="$(jq -r '.steps[]|select(.id=="2.1")|.commit' .claude/multi-model-workflow/loop-state.json)"
[ -n "$sha" ] && [ "$sha" != "null" ] && ok "记下 commit sha" || no "记 sha"
# 非 commit 命令不动
P_NOOP='{"tool_input":{"command":"ls -la"}}'
run_hook record-step.sh "$P_NOOP" >/dev/null
ok "非 commit 命令安全跳过(无崩)"

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" -eq 0 ]
