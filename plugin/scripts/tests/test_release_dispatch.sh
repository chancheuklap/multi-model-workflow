#!/usr/bin/env bash
# release-flow.sh fix-dispatch:收敛熔断、P2 derive、P1 staging/path-gate。
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RF="$SCRIPT_DIR/../release-flow.sh"
FIX="$SCRIPT_DIR/fixtures/release-flow"
SF="$STATE_SUBDIR/release-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

init_with() {
  local d="$1"
  shift
  bash "$RF" close >/dev/null 2>&1 || true
  rm -f events.jsonl derive-marker.txt
  jq --argjson d "$d" '.derive=$d' "$FIX/manifest.fake.json" > m.json
  bash "$RF" init --manifest m.json "$@" >/dev/null
}

init_with_fix() {
  bash "$RF" close >/dev/null 2>&1 || true
  rm -f events.jsonl
  jq --argjson fx "$1" '.fix_executor=$fx' "$FIX/manifest.fake.json" > m.json
  bash "$RF" init --manifest m.json >/dev/null
}

init_pfg() {
  bash "$RF" close >/dev/null 2>&1 || true
  rm -f events.jsonl scripts/release/patched.txt
  local fx='["sh","-c","mkdir -p \"$RELEASE_FIX_STAGING/scripts/release\"; echo fixed > \"$RELEASE_FIX_STAGING/scripts/release/patched.txt\""]'
  if [ -n "$2" ]; then
    jq --argjson fx "$fx" --argjson pfg "$1" --argjson pfd "$2" \
      '.fix_executor=$fx | .post_fix_gate=$pfg | .post_fix_diagnose=$pfd' "$FIX/manifest.fake.json" > m.json
  else
    jq --argjson fx "$fx" --argjson pfg "$1" \
      '.fix_executor=$fx | .post_fix_gate=$pfg' "$FIX/manifest.fake.json" > m.json
  fi
  bash "$RF" init --manifest m.json >/dev/null
}

echo "=== test_release_dispatch.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
git config user.email t@t
git config user.name t
mkdir -p scripts/release migrations
echo seed > scripts/release/existing.txt
echo "m" > migrations/0001.py
git add -A
git commit -qm s

init_with '["true"]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  CIRCUIT-BREAK:fingerprint=missing_module:scipy*) ok "同 fp 达阈值熔断" ;;
  *) no "熔断 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "熔断写 PAUSE needs-redirection" || no "熔断 pause ($(jq -r '.pause.reason' "$SF"))"
[ "$(bash "$RF" exit-check)" = "PAUSED:needs-redirection" ] && ok "熔断后 exit-check PAUSED" || no "exit-check ($(bash "$RF" exit-check))"

init_with '["true"]' --max-rounds 1
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  BUDGET-EXCEEDED:attempts=1*) ok "attempts 预算越界熔断" ;;
  *) no "attempts 越界 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "attempts 越界 PAUSE" || no "attempts pause"

init_with '["true"]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
t="$(mktemp)"
jq '.budget.started_at="2000-01-01T00:00:00Z"' "$SF" > "$t" && mv "$t" "$SF"
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  BUDGET-EXCEEDED:wallclock=*) ok "墙钟预算越界熔断" ;;
  *) no "墙钟越界 ($out)" ;;
esac

init_with '["sh","-c","echo derived > derive-marker.txt"]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p2.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p2.json")"
case "$out" in
  DERIVED:doctor*) ok "P2 derive 分级" ;;
  *) no "P2 derive ($out)" ;;
esac
[ -f derive-marker.txt ] && ok "derive 被执行(marker)" || no "derive 未执行"
[ "$(jq -r '[.stages[]|select(.name=="doctor")][0].status' "$SF")" = "pending" ] && ok "derive 后 stage 回 pending 待重跑" || no "stage 状态"
[ "$(jq -r '.attempt_ledger[-1].action_kind' "$SF")" = "derive" ] && [ "$(jq -r '.attempt_ledger[-1].outcome' "$SF")" = "done" ] && ok "attempt_ledger 记 derive/done" || no "attempt derive"

init_with '["false"]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p2.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p2.json")"
case "$out" in
  DERIVE-FAILED:*) ok "derive 失败分级" ;;
  *) no "derive 失败 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-context" ] && ok "derive 失败 escalate needs-context" || no "escalate ($(jq -r '.pause.reason' "$SF"))"

init_with_fix '["true"]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  FIX-APPLIED:doctor*) ok "P1 默认 fix 分支" ;;
  *) no "P1 fix ($out)" ;;
esac
[ "$(jq -r '.pause' "$SF")" = "null" ] && ok "P1 fix 不 PAUSE" || no "P1 竟 PAUSE"

if bash "$RF" dispatch --stage doctor --findings /nonexistent/x.json 2>/dev/null; then no "缺 findings 文件应 fail"; else ok "findings 不存在 fail-loud"; fi
if bash "$RF" dispatch --bogus 1 2>/dev/null; then no "未知参数应 fail"; else ok "未知参数 fail-loud"; fi

init_with '["true"]'
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p0.json")"
case "$out" in
  P0:doctor*) ok "dispatch P0 分级" ;;
  *) no "dispatch P0 分支 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "dispatch P0 写 PAUSE needs-redirection" || no "dispatch P0 pause ($(jq -r '.pause.reason' "$SF"))"
[ "$(bash "$RF" exit-check)" = "PAUSED:needs-redirection" ] && ok "dispatch P0 后 exit-check PAUSED" || no "dispatch P0 exit-check ($(bash "$RF" exit-check))"
jq -e '[.attempt_ledger[]|select(.root_cause_fingerprint=="p0_path:deploy/env")]|length>=1' "$SF" >/dev/null && ok "dispatch P0 记 attempt_ledger" || no "dispatch P0 未记 attempt"

init_with_fix '["sh","-c","mkdir -p \"$RELEASE_FIX_STAGING/scripts/release\"; echo fixed > \"$RELEASE_FIX_STAGING/scripts/release/patched.txt\""]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  FIX-APPLIED:doctor*) ok "in-bounds fix 应用" ;;
  *) no "in-bounds ($out)" ;;
esac
[ -f scripts/release/patched.txt ] && ok "fix 文件 cp 回主树" || no "主树无 fix 文件"
jq -e '[.attempt_ledger[]|select(.action_kind=="fix")]|length>=1' "$SF" >/dev/null && ok "attempt 有 fix 条目" || no "无 fix attempt"
jq -e '[.attempt_ledger[]|select(.action_kind=="fix" and (.changed_paths|length>=1))]|length>=1' "$SF" >/dev/null && ok "fix attempt changed_paths 非空" || no "changed_paths 空"
[ "$(jq -r '[.stages[]|select(.name=="doctor")][0].status' "$SF")" = "pending" ] && ok "fix 后 stage 回 pending" || no "stage 状态"
rm -f scripts/release/patched.txt

rm -f scripts/release/link.txt
ln -s ../../migrations/0001.py scripts/release/link.txt
init_with_fix '["sh","-c","echo symlink-safe > \"$RELEASE_FIX_STAGING/scripts/release/link.txt\""]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  FIX-APPLIED:doctor*) ok "symlink editable apply 走正常 fix 分支" ;;
  *) no "symlink apply 分支 ($out)" ;;
esac
[ "$(cat migrations/0001.py)" = "m" ] && ok "apply 不跟随主树 symlink 覆盖 P0" || no "apply 跟随 symlink 覆盖 P0 ($(cat migrations/0001.py))"
[ ! -L scripts/release/link.txt ] && [ "$(cat scripts/release/link.txt)" = "symlink-safe" ] && ok "apply 打断 symlink 后写真实文件" || no "apply 未打断 symlink"
rm -f scripts/release/link.txt
echo "m" > migrations/0001.py

init_with_fix '["sh","-c","echo hack >> \"$RELEASE_FIX_STAGING/migrations/0001.py\"; mkdir -p \"$RELEASE_FIX_STAGING/scripts/release\"; echo ok > \"$RELEASE_FIX_STAGING/scripts/release/patched.txt\""]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  PATH-GATE-REJECT:doctor*migrations/0001.py*) ok "p0 越界 REJECT 列越界" ;;
  *) no "p0 REJECT ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "越界 PAUSE needs-redirection" || no "越界 pause"
[ "$(cat migrations/0001.py)" = "m" ] && ok "主树 p0 文件未被写(隔离)" || no "主树被脏写!($(cat migrations/0001.py))"
[ "$(git worktree list | wc -l | tr -d ' ')" = "1" ] && ok "staging 已清(worktree 仅主树)" || no "staging 泄漏"
jq -e '.attempt_ledger[-1].action_kind=="path_gate" and (.attempt_ledger[-1].blocked_paths|index("migrations/0001.py"))' "$SF" >/dev/null && ok "attempt path_gate + blocked_paths" || no "attempt blocked"
[ ! -f scripts/release/patched.txt ] && ok "越界时 in-bounds 文件也不 apply(全弃)" || no "部分 apply 了"

init_with_fix '["sh","-c","echo leak >> migrations/0001.py"]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  PATH-GATE-REJECT:doctor*migrations/0001.py*) ok "相对路径 fix 被 staging 隔离并 REJECT" ;;
  *) no "相对路径 fix 未隔离 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "相对路径越界 PAUSE needs-redirection" || no "相对路径越界 pause"
[ "$(cat migrations/0001.py)" = "m" ] && ok "相对路径 fix 未脏写主树 P0" || no "相对路径 fix 写穿主树!($(cat migrations/0001.py))"

main_p0="$PWD/migrations/0001.py"
fx_abs="$(jq -nc --arg p "$main_p0" '["sh","-c","echo abs-leak >> " + $p]')"
init_with_fix "$fx_abs"
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  PATH-GATE-REJECT:doctor*main:migrations/0001.py*) ok "绝对路径脏写主树被防御拦截" ;;
  *) no "绝对路径脏写未拦截 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "绝对路径脏写 PAUSE needs-redirection" || no "绝对路径脏写 pause"
[ "$(cat migrations/0001.py)" = "m" ] && ok "绝对路径脏写已复原主树 P0" || no "绝对路径脏写未复原!($(cat migrations/0001.py))"

init_with_fix '["sh","-c","mkdir -p \"$RELEASE_FIX_STAGING/random\"; echo x > \"$RELEASE_FIX_STAGING/random/other.txt\""]'
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  PATH-GATE-REJECT:doctor*random/other.txt*) ok "not-editable 越界 REJECT" ;;
  *) no "not-editable ($out)" ;;
esac

[ -z "$(git status --porcelain -uno)" ] && ok "REJECT 后主树 tracked 干净(无脏 diff)" || no "主树 tracked 被脏写"

init_pfg '["true"]' ''
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  *POST-FIX-GATE-PASS:doctor*) ok "post-fix-gate 绿 PASS" ;;
  *) no "gate PASS ($out)" ;;
esac
[ "$(jq -r '[.stages[]|select(.name=="doctor")][0].status' "$SF")" = "pending" ] && ok "gate 绿后 stage pending" || no "stage 状态"
jq -e '[.attempt_ledger[]|select(.action_kind=="post_fix_gate" and .outcome=="pass")]|length>=1' "$SF" >/dev/null && ok "attempt post_fix_gate/pass" || no "attempt gate pass"
rm -f scripts/release/patched.txt

PFD="$(jq -nc --arg p "$FIX/finding.gatefail.json" '["cat",$p]')"
init_pfg '["false"]' "$PFD"
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  *POST-FIX-GATE-FAIL:doctor*) ok "post-fix-gate 红 FAIL" ;;
  *) no "gate FAIL ($out)" ;;
esac
[ "$(bash "$RF" exit-check)" != "DONE" ] && ok "gate 红不宣告 DONE" || no "竟 DONE(包能出不等于可发布被破)"
jq -e '[.fingerprint_ledger[]|select(.fingerprint=="arch:shared_reverse_import")]|length>=1' "$SF" >/dev/null && ok "破架构 fp 计入 fingerprint_ledger" || no "fp 未记"
jq -e '[.attempt_ledger[]|select(.action_kind=="post_fix_gate" and .outcome=="fail")]|length>=1' "$SF" >/dev/null && ok "attempt post_fix_gate/fail" || no "attempt gate fail"
rm -f scripts/release/patched.txt

init_pfg '["true"]' ''
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.gatefail.json" >/dev/null
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.gatefail.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.gatefail.json")"
case "$out" in
  CIRCUIT-BREAK:fingerprint=arch:shared_reverse_import*) ok "破架构 fp 达阈值熔断" ;;
  *) no "回归熔断 ($out)" ;;
esac

PFD_BAD="$(jq -nc --arg p "$FIX/finding.bad.json" '["cat",$p]')"
init_pfg '["false"]' "$PFD_BAD"
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p1.json")"
[ "$(jq -r '.pause.reason' "$SF")" = "needs-context" ] && ok "gate 红不可诊断 escalate needs-context" || no "escalate ($(jq -r '.pause.reason' "$SF"))"
rm -f scripts/release/patched.txt

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
