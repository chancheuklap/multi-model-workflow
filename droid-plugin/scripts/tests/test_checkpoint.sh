#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PREPARE="$SCRIPT_DIR/../prepare.sh"
CHECKPOINT="$SCRIPT_DIR/../checkpoint.sh"
FLOW="$SCRIPT_DIR/../flow.sh"
LOOP="$SCRIPT_DIR/../loop.sh"
HOOK="$SCRIPT_DIR/../../hooks/prompt-anchor.sh"
STATE_SUBDIR=".factory/multi-model-workflow"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_checkpoint.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
git config user.email t@t
git config user.name t
echo seed > seed
git add seed
git commit -qm seed

out="$(bash "$PREPARE" new --scenario develop --slug checkpoint-demo --title checkpoint --request checkpoint 2>/dev/null)"
WT="$(printf '%s\n' "$out" | sed -n 's/^worktree_path=//p')"
MAN="$WT/$STATE_SUBDIR/task.json"
jq '.phase="design" | .phase_index=2 | .step_index=3' "$MAN" >"$MAN.next" && mv "$MAN.next" "$MAN"
mkdir -p "$WT/docs/design" "$WT/docs/issues/demo"
printf 'approved design\n' >"$WT/docs/design/design file.md"
printf 'different design\n' >"$WT/docs/design/other.md"

prepared="$(cd "$WT" && bash "$CHECKPOINT" prepare --report "docs/design/design file.md")"
token="$(printf '%s\n' "$prepared" | sed -n 's/^approval_token=//p')"
[ "$(jq -r .checkpoint.status "$MAN")" = waiting-user ] \
  && [ "$(jq -r .status "$MAN")" = waiting-user ] \
  && ok "prepare 等待明确用户确认" || no "prepare waiting-user"
[ -n "$token" ] && ok "prepare 生成确认 token" || no "确认 token"
waiting_where="$(cd "$WT" && bash "$FLOW" where)"
printf '%s\n' "$waiting_where" | grep '^then=' | grep -q 'AskUser' \
  && ok "where 在等待期只引导一次 AskUser" || no "where 等待导航"

wrong_payload="$(jq -cn --arg cwd "$WT" '{hook_event_name:"UserPromptSubmit",cwd:$cwd,prompt:"继续"}')"
printf '%s' "$wrong_payload" | bash "$HOOK" >/dev/null
[ "$(jq -r .checkpoint.status "$MAN")" = waiting-user ] \
  && ok "普通用户消息不构成批准" || no "普通消息错误批准"
(cd "$TMP" && bash "$PREPARE" resume --slug checkpoint-demo >/dev/null)
[ "$(jq -r .status "$MAN")" = waiting-user ] \
  && ok "普通 resume 不能绕过设计确认" || no "resume 绕过 checkpoint"

approve_payload="$(jq -cn --arg cwd "$WT" --arg prompt "确认设计 $token" \
  '{hook_event_name:"UserPromptSubmit",cwd:$cwd,prompt:$prompt}')"
printf '%s' "$approve_payload" | bash "$HOOK" >/dev/null
[ "$(jq -r .checkpoint.status "$MAN")" = approved ] \
  && [ "$(jq -r .status "$MAN")" = active ] \
  && ok "精确 token 由 UserPromptSubmit Hook 批准" || no "Hook 批准"
approved_where="$(cd "$WT" && bash "$FLOW" where)"
printf '%s\n' "$approved_where" | grep '^then=' | grep -q 'handoff --conclusion' \
  && printf '%s\n' "$approved_where" | grep '^then=' | grep -q 'design\\ file.md' \
  && ok "批准后 where 恢复 shell-safe handoff" || no "批准后导航"

if (cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/design/other.md >/dev/null 2>&1); then
  no "handoff 不得替换用户确认的报告"
else
  ok "handoff 产出绑定已确认报告"
fi
[ "$(jq -r .phase "$MAN")" = design ] && ok "错误产出不推进阶段" || no "错误产出推进了阶段"

(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced "docs/design/design file.md" >/dev/null)
[ "$(jq -r .gate "$MAN")" = design ] && ok "确认后进入设计审" || no "未进入设计审"

(
  cd "$WT"
  bash "$LOOP" init --kind review --max-rounds 2 >/dev/null
  bash "$LOOP" checklist add --item gate --source design >/dev/null
  bash "$LOOP" checklist cover --item gate --evidence pass >/dev/null
  bash "$FLOW" handoff --conclusion pass >/dev/null
)
[ "$(jq -r .phase "$MAN")" = to-issue ] \
  && [ "$(jq -r .checkpoint.status "$MAN")" = none ] \
  && ok "设计审通过后清 checkpoint" || no "设计审后 checkpoint"

(cd "$WT" && bash "$FLOW" handoff --conclusion pass --produced docs/issues/demo >/dev/null)
[ "$(jq -r .phase "$MAN")" = plan ] \
  && [ "$(jq -r .attendance "$MAN")" = afk ] \
  && ok "进入 plan 自动切 AFK" || no "plan 自动 AFK"

if (cd "$WT" && bash "$CHECKPOINT" approve >/dev/null 2>&1); then
  no "不应存在公开 approve 命令"
else
  ok "无公开 approve 命令"
fi

jq '.phase="design" | .phase_index=2 | .step_index=3 | .gate=null | .status="active" |
  .checkpoint={phase:null,status:"none",report:[],source_fingerprint:null,approval_id:null,prepared_at:null,approved_at:null}' \
  "$MAN" >"$MAN.next" && mv "$MAN.next" "$MAN"
printf 'before change\n' >"$WT/docs/design/change.md"
(cd "$WT" && bash "$CHECKPOINT" prepare --report docs/design/change.md >/dev/null)
changed_id="$(jq -r .checkpoint.approval_id "$MAN")"
printf 'after change\n' >"$WT/docs/design/change.md"
changed_payload="$(jq -cn --arg cwd "$WT" --arg prompt "确认设计 MMW-APPROVE:$changed_id" \
  '{hook_event_name:"UserPromptSubmit",cwd:$cwd,prompt:$prompt}')"
if printf '%s' "$changed_payload" | bash "$HOOK" >/dev/null 2>&1; then
  no "报告改变后 Hook 应拒绝批准"
else
  ok "报告改变后必须重新 prepare"
fi
[ "$(jq -r .checkpoint.status "$MAN")" = waiting-user ] \
  && ok "拒绝后 checkpoint 保持等待" || no "拒绝后状态"

ln -s /etc/hosts "$WT/docs/design/outside.md"
if (cd "$WT" && bash "$CHECKPOINT" prepare --report docs/design/outside.md >/dev/null 2>&1); then
  no "外部符号链接不应成为批准报告"
else
  ok "报告指纹拒绝 worktree 外符号链接"
fi

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
