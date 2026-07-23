#!/usr/bin/env bash
# Codex 三类 hooks：SessionStart、PreToolUse 红线、PostToolUse Pack 记账。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOKS="$PLUGIN_DIR/hooks"
LOOP="$PLUGIN_DIR/scripts/loop.sh"
STATE=".codex/multi-model-workflow"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

payload() {
  jq -nc --arg command "$1" \
    '{hook_event_name:"PreToolUse",tool_name:"Bash",tool_input:{command:$command}}'
}

approved_payload() {
  jq -nc --arg command "$1" \
    '{hook_event_name:"PreToolUse",tool_name:"Bash",
      tool_input:{command:$command,sandbox_permissions:"require_escalated",
        justification:"Approve outbound release"}}'
}

is_blocked() {
  local input="$1" output status
  set +e
  output="$(printf '%s' "$input" | bash "$HOOKS/guard-redline.sh" 2>&1)"
  status=$?
  set -e
  [ "$status" -eq 2 ] && printf '%s' "$output" | grep -q '需用户通过 Codex 原生权限框确认'
}

is_allowed() {
  printf '%s' "$1" | bash "$HOOKS/guard-redline.sh" >/dev/null 2>&1
}

echo "=== test_hooks.sh ==="

HJ="$HOOKS/hooks.json"
if jq -e '
  (.hooks.SessionStart | length) == 1
  and (.hooks.PreToolUse | length) == 1
  and (.hooks.PostToolUse | length) == 1
  and .hooks.PreToolUse[0].matcher == "Bash"
  and .hooks.PostToolUse[0].matcher == "Bash"
  and ([.hooks | to_entries[].value[] | .hooks[] | .type == "command"] | all)
  and ([.hooks | to_entries[].value[] | .hooks[] | has("if")] | any | not)
' "$HJ" >/dev/null 2>&1 \
  && grep -q '\${PLUGIN_ROOT}' "$HJ"; then
  ok "hooks.json 使用 Codex 三类事件和 PLUGIN_ROOT"
else
  no "hooks.json 不是 Codex 当前接线"
fi

is_allowed "$(payload 'git merge --no-ff feature')" \
  && ok "本地 merge 放行" || no "本地 merge 被误拦"
is_allowed "$(payload 'git status')" \
  && ok "普通命令放行" || no "普通命令被误拦"
is_blocked "$(payload 'git push origin main')" \
  && is_blocked "$(payload 'gh pr merge 12 --merge')" \
  && is_blocked "$(payload 'kubectl apply -f k8s/')" \
  && is_blocked "$(payload './deploy.sh')" \
  && ok "出站发布和部署先被 PreToolUse 拦下" \
  || no "红线命令存在绕过"
is_allowed "$(approved_payload 'git push origin main')" \
  && ok "带原生权限请求的重试交回 Codex approval" \
  || no "原生权限请求无法穿过 hook"
is_allowed "$(payload 'echo git push origin main')" \
  && is_allowed "$(payload 'cat > runbook.md <<EOF\ngit push origin main\nEOF')" \
  && ok "参数文本和 heredoc 不误报" \
  || no "红线 parser 误报"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git -C "$TMP" init -q
git -C "$TMP" config user.email test@example.com
git -C "$TMP" config user.name Test
printf 'seed\n' >"$TMP/seed.txt"
git -C "$TMP" add seed.txt
git -C "$TMP" commit -qm seed
(
  cd "$TMP"
  bash "$LOOP" init >/dev/null
  bash "$LOOP" step add --id 7.1 --desc hook >/dev/null
  printf 'change\n' >change.txt
  git add change.txt
  git commit -qm "feat(codex): Pack 7.1 hooks"
  jq -nc '{hook_event_name:"PostToolUse",tool_name:"Bash",
    tool_input:{command:"git commit -m hooks"},tool_response:{exit_code:0}}' \
    | bash "$HOOKS/record-step.sh"
)
if [ "$(jq -r '.steps[] | select(.id=="7.1") | .status' "$TMP/$STATE/loop-state.json")" = "done" ]; then
  ok "PostToolUse 从 HEAD 的 Pack 号完成 loop step"
else
  no "PostToolUse 没有记录 Pack"
fi

NOGIT="$(mktemp -d)"
triage="$(cd "$NOGIT" && printf '{"hook_event_name":"SessionStart","source":"startup"}' \
  | bash "$HOOKS/session-triage.sh")"
rmdir "$NOGIT"
[ -z "$triage" ] && ok "非 Git 目录 SessionStart 静默" || no "非 Git 分诊不应输出"

triage="$(cd "$TMP" && printf '{"hook_event_name":"SessionStart","source":"resume"}' \
  | bash "$HOOKS/session-triage.sh")"
printf '%s' "$triage" | grep -q 'multi-model-workflow-codex' \
  && printf '%s' "$triage" | grep -q 'mmw' \
  && ! printf '%s' "$triage" | rg -q '/reassess|/progress|\\.pi|Claude|Droid' \
  && ok "SessionStart 注入 Codex 任务恢复入口" \
  || no "SessionStart 仍有旧宿主入口"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
