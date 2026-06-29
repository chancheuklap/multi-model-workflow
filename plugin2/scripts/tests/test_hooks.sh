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

echo "=== test_hooks.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s

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
# 损坏 loop-state → 看守 fail-closed(不放停),不把损坏当 PAUSED 静默放行
echo 'garbage{' > .claude/multi-model-workflow/loop-state.json
[ "$(run_hook guard-loop.sh '{}')" = "2" ] && ok "损坏 loop-state → 看守 exit2(fail-closed)" || no "损坏态看守 fail-closed"

# ===== guard-redline(PreToolUse)=====
P_MERGE='{"tool_input":{"command":"git merge feat --no-ff"}}'
P_PUSH='{"tool_input":{"command":"git push origin main"}}'
P_SAFE='{"tool_input":{"command":"git status"}}'
[ "$(run_hook guard-redline.sh "$P_MERGE")" = "2" ] && ok "merge 无批准 → deny" || no "merge deny"
[ "$(run_hook guard-redline.sh "$P_PUSH")" = "2" ] && ok "push 无批准 → deny" || no "push deny"
[ "$(run_hook guard-redline.sh "$P_SAFE")" = "0" ] && ok "git status → 放行" || no "safe 放行"
touch .claude/multi-model-workflow/release-approval
[ "$(run_hook guard-redline.sh "$P_MERGE")" = "0" ] && ok "有 release-approval → merge 放行" || no "批准后放行"
rm -f .claude/multi-model-workflow/release-approval

# ===== record-step(PostToolUse commit)=====
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
