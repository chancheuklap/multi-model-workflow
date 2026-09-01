#!/usr/bin/env bash
# release-flow.sh 分级层:stage fail 分 tier、P0->PAUSE、receipt 从 ledger 渲染、不可诊断 escalate、event_sink 落地。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RF="$SCRIPT_DIR/../scripts/release-flow.sh"
RC="$SCRIPT_DIR/../scripts/release_contracts.py"
FIX="$SCRIPT_DIR/fixtures/release-flow"
SF=".release/release-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
reinit() {
  bash "$RF" close >/dev/null 2>&1 || true
  rm -f events.jsonl
  bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
}

echo "=== test_release_classify.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
git config user.email t@t
git config user.name t
echo s > s
git add -A
git commit -qm s

reinit
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p0.json")"
case "$out" in
  CLASSIFY=P0*) ok "P0 分级" ;;
  *) no "P0 分级 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "P0 写 PAUSE needs-redirection" || no "P0 pause ($(jq -r '.pause.reason' "$SF"))"
[ "$(bash "$RF" exit-check)" = "PAUSED:needs-redirection" ] && ok "P0 后 exit-check PAUSED" || no "exit-check"
[ "$(jq -r '[.attempt_ledger[]|select(.stage=="doctor" and .outcome=="fail")]|length' "$SF")" -ge 1 ] && ok "attempt_ledger 记 doctor fail" || no "attempt 缺"

r="$(bash "$RF" receipt)"
echo "$r" | grep -q doctor && echo "$r" | grep -q "p0_path:deploy/env" && ok "receipt 含 stage+fp" || no "receipt 内容"

[ -s events.jsonl ] && ok "event_sink 收到 event" || no "events.jsonl 空"
bad=0
while IFS= read -r line; do
  printf '%s' "$line" | uv run --quiet "$RC" validate-event - || bad=1
done < events.jsonl
[ "$bad" -eq 0 ] && ok "每条 event 过 validate-event" || no "有非法 event"

reinit
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  CLASSIFY=P1*) ok "P1 分级" ;;
  *) no "P1 分级 ($out)" ;;
esac
[ "$(jq -r '.pause' "$SF")" = "null" ] && ok "P1 不 PAUSE" || no "P1 竟 PAUSE"
[ "$(bash "$RF" exit-check)" = "NOT-DONE:stages=doctor" ] && ok "P1 后 NOT-DONE 列失败 stage" || no "exit-check ($(bash "$RF" exit-check))"
[ "$(jq -r '[.fingerprint_ledger[]|select(.fingerprint=="missing_module:scipy")][0].count' "$SF")" = "1" ] && ok "fingerprint_ledger 计数+1" || no "fp count"

[ "$(bash "$RF" where)" = "RETRY-STAGE:doctor RUN:true" ] && ok "where 失败 stage 优先重跑" || no "where ($(bash "$RF" where))"

reinit
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.bad.json")"
case "$out" in
  UNCLASSIFIABLE*) ok "不可诊断分级" ;;
  *) no "不可诊断 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-context" ] && ok "不可诊断 escalate needs-context" || no "escalate ($(jq -r '.pause.reason' "$SF"))"

reinit
printf '{"findings":[]}' > empty-findings.json
out="$(bash "$RF" stage fail --stage doctor --findings empty-findings.json)"
case "$out" in
  UNCLASSIFIABLE:doctor*) ok "空 findings 不可诊断分级" ;;
  *) no "空 findings 未 escalate ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-context" ] && ok "空 findings escalate needs-context" || no "空 findings pause ($(jq -r '.pause.reason' "$SF"))"
[ "$(bash "$RF" exit-check)" = "PAUSED:needs-context" ] && ok "空 findings 后 exit-check PAUSED" || no "空 findings exit-check ($(bash "$RF" exit-check))"
[ "$(jq -r '[.attempt_ledger[]|select(.outcome=="fail" and (.root_cause_fingerprint == null))]|length' "$SF")" = "0" ] && ok "空 findings 不记无指纹 fail" || no "空 findings 记了无指纹 fail"
if [ -f events.jsonl ] && grep -q '"event":"classified"' events.jsonl; then no "空 findings 不应 emit classified"; else ok "空 findings 不 emit classified"; fi

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
