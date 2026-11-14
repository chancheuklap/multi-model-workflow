#!/usr/bin/env bash
# release-flow.sh 分级层:stage fail 分 tier、P0->PAUSE、receipt 从 ledger 渲染、不可诊断 escalate、event_sink 落地。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RF="$SCRIPT_DIR/../../skills/exe-release/scripts/release-flow.sh"
RC="$SCRIPT_DIR/../../skills/exe-release/scripts/release_contracts.py"
FIX="$SCRIPT_DIR/fixtures/release-flow"
SF=".release/release-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
reinit() {
  # abort, not close: close now refuses a release loop that is not DONE, and the previous scenario's
  # release loop usually is not. abort always drops it and clears the state file so init can start.
  bash "$RF" abort >/dev/null 2>&1 || true
  rm -f events.jsonl
  bash "$RF" init --manifest "${1:-$FIX/manifest.fake.json}" >/dev/null
}

# 落地的每一行事件都得过 ReleaseLoopEvent 合同;一个都没落地也算不过。
events_valid() {
  [ -s events.jsonl ] || return 1
  local line bad=0
  while IFS= read -r line; do
    printf '%s' "$line" | uv run --quiet --with 'pydantic>=2' python3 -c '
import sys
sys.path.insert(0, "'"$(dirname "$RC")"'")
from release_contracts import ReleaseLoopEvent
ReleaseLoopEvent.model_validate_json(sys.stdin.read())
' || bad=1
  done < events.jsonl
  [ "$bad" -eq 0 ]
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
[ "$(bash "$RF" where)" = "PAUSED:needs-redirection" ] && ok "P0 后 where PAUSED" || no "where"
[ "$(jq -r '[.attempt_ledger[]|select(.stage=="doctor" and .outcome=="fail")]|length' "$SF")" -ge 1 ] && ok "attempt_ledger 记 doctor fail" || no "attempt 缺"

# 守:PAUSED:needs-redirection 时驱动把 receipt 原样交给操作员(driving.md),所以停在哪一段、为什么、
# 看过哪些指纹、试过什么、证据在哪份文件里,都得在 receipt 里。
r="$(bash "$RF" receipt)"
[[ "$r" == *"paused at stage=doctor reason=needs-redirection"* ]] && ok "receipt 说停在哪个 stage、为什么" || no "receipt 缺停靠信息 ($r)"
[[ "$r" == *"- p0_path:deploy/env x1"* ]] && ok "receipt 列出见过的指纹和次数" || no "receipt 缺指纹账 ($r)"
[[ "$r" == *"stage=doctor outcome=fail fp=p0_path:deploy/env findings=$FIX/finding.p0.json"* ]] \
  && ok "receipt 列出试过的动作及其 findings 文件" || no "receipt 缺动作账 ($r)"
pause_question="$(jq -r '.pause.question' "$SF")"
[ -n "$pause_question" ] && [[ "$r" == *"$pause_question"* ]] \
  && ok "receipt 带着这次暂停要操作员回答的问题" || no "receipt 缺暂停的问题 ($r)"

events_valid && ok "每条 event 都过 ReleaseLoopEvent 合同" || no "event 缺失或有非法 event"

reinit
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json")"
case "$out" in
  CLASSIFY=P1*) ok "P1 分级" ;;
  *) no "P1 分级 ($out)" ;;
esac
[ "$(jq -r '.pause' "$SF")" = "null" ] && ok "P1 不 PAUSE" || no "P1 竟 PAUSE"
[ "$(jq -r '.stages[]|select(.name=="doctor").status' "$SF")" = "failed" ] && ok "P1 把失败的 stage 标 failed" || no "P1 后 doctor 状态 ($(jq -r '.stages[]|select(.name=="doctor").status' "$SF"))"
close_err="$(mktemp)"
if bash "$RF" close >/dev/null 2>"$close_err"; then
  no "close 在失败 stage 还没处理时放行"
else
  grep -q "doctor" "$close_err" && ok "close 拒绝并点名失败的 stage" || no "close 拒绝理由未点名 stage ($(cat "$close_err"))"
fi
rm -f "$close_err"
[ "$(jq -r '[.fingerprint_ledger[]|select(.fingerprint=="missing_module:scipy")][0].count' "$SF")" = "1" ] && ok "fingerprint_ledger 计数+1" || no "fp count"

[ "$(bash "$RF" where)" = "STAGE:doctor RUN:true" ] && ok "where 失败 stage 优先重跑" || no "where ($(bash "$RF" where))"
jq -s -e 'any(.[]; .event == "classified" and .stage == "doctor" and .tier == "P1" and .fingerprint == "missing_module:scipy")' events.jsonl >/dev/null 2>&1 \
  && events_valid && ok "P1 分级落一条带 tier 与指纹的 classified 事件" || no "P1 的 classified 事件缺失或不合法"

reinit
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.bad.json")"
case "$out" in
  UNCLASSIFIABLE*) ok "不可诊断分级" ;;
  *) no "不可诊断 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-context" ] && ok "不可诊断 escalate needs-context" || no "escalate ($(jq -r '.pause.reason' "$SF"))"
# 没有 tier 也没有指纹的失败,事件里这两项必须是空(null),不是空串——合同不收空串。
jq -s -e 'any(.[]; .event == "stage.failed" and .stage == "doctor" and .tier == null and .fingerprint == null)' events.jsonl >/dev/null 2>&1 \
  && events_valid && ok "不可诊断落一条 stage.failed 事件,tier 与指纹为 null" || no "不可诊断的 stage.failed 事件缺失或不合法"

reinit
printf '{"findings":[]}' > empty-findings.json
out="$(bash "$RF" stage fail --stage doctor --findings empty-findings.json)"
case "$out" in
  UNCLASSIFIABLE:doctor*) ok "空 findings 不可诊断分级" ;;
  *) no "空 findings 未 escalate ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$SF")" = "needs-context" ] && ok "空 findings escalate needs-context" || no "空 findings pause ($(jq -r '.pause.reason' "$SF"))"
[ "$(bash "$RF" where)" = "PAUSED:needs-context" ] && ok "空 findings 后 where PAUSED" || no "空 findings where ($(bash "$RF" where))"
[ "$(jq -r '[.attempt_ledger[]|select(.outcome=="fail" and (.root_cause_fingerprint == null))]|length' "$SF")" = "0" ] && ok "空 findings 不记无指纹 fail" || no "空 findings 记了无指纹 fail"
if [ -f events.jsonl ] && grep -q '"event":"classified"' events.jsonl; then no "空 findings 不应 emit classified"; else ok "空 findings 不 emit classified"; fi

# ── 事件落地 ────────────────────────────────────────────────────────────────
# event_sink 是钥匙交给引擎的一条命令:每条事件从它的 stdin 进去。
#
# 守:sink 拿到引擎自己正在用的那份合同所在的目录(MMW_PLUGIN_DIR),而且钥匙里写的
# ${RELEASE_PLUGIN_DIR} 被展开成同一个目录。sink 靠这个去加载 ReleaseLoopEvent;让它自己猜
# 目录,已安装的技能与源仓库布局不同,事件就长期落不下来。
plugin_dir="$(CDPATH= cd -- "$(dirname -- "$RF")" && pwd -P)"
jq '.event_sink=["sh","-c","printf \"%s\\n\" \"$0\" \"$MMW_PLUGIN_DIR\" > sink.args; cat >> events.jsonl","${RELEASE_PLUGIN_DIR}"]' \
  "$FIX/manifest.fake.json" > sink-env-manifest.json
reinit sink-env-manifest.json
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
[ "$(sed -n 1p sink.args 2>/dev/null)" = "$plugin_dir" ] && ok "event_sink 命令里的 RELEASE_PLUGIN_DIR 被展开成引擎所在目录" || no "sink 的 RELEASE_PLUGIN_DIR ($(sed -n 1p sink.args 2>/dev/null))"
[ "$(sed -n 2p sink.args 2>/dev/null)" = "$plugin_dir" ] && ok "event_sink 的环境里有 MMW_PLUGIN_DIR" || no "sink 的 MMW_PLUGIN_DIR ($(sed -n 2p sink.args 2>/dev/null))"

# 守:落不了事件不能拖垮出包。sink 失败只留一行 WARN,分级照常给出结果;钥匙没接日志系统就没有事件,也不出错。
jq '.event_sink=["false"]' "$FIX/manifest.fake.json" > sink-fails-manifest.json
reinit sink-fails-manifest.json
sink_err="$(mktemp)"
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" 2>"$sink_err")" && sink_rc=0 || sink_rc=$?
if [ "$sink_rc" -eq 0 ] && [[ "$out" == CLASSIFY=P1* ]] && grep -q "event_sink did not record" "$sink_err"; then
  ok "sink 失败只留 WARN,分级照常完成"
else
  no "sink 失败的处理 (rc=$sink_rc out=$out err=$(cat "$sink_err"))"
fi
rm -f "$sink_err"

jq 'del(.event_sink)' "$FIX/manifest.fake.json" > no-sink-manifest.json
reinit no-sink-manifest.json
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json")" && sink_rc=0 || sink_rc=$?
if [ "$sink_rc" -eq 0 ] && [[ "$out" == CLASSIFY=P1* ]] && [ ! -e events.jsonl ]; then
  ok "钥匙没声明 event_sink 时分级照常,也不凭空造事件文件"
else
  no "没有 event_sink 的处理 (rc=$sink_rc out=$out)"
fi

# 钥匙文件在 init 之后被删了:事件记不下来,但出包不该因此崩——留一行 WARN 点名那份钥匙,分级照常。
cp "$FIX/manifest.fake.json" gone-manifest.json
reinit gone-manifest.json
rm -f gone-manifest.json
gone_err="$(mktemp)"
out="$(bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" 2>"$gone_err")" && gone_rc=0 || gone_rc=$?
if [ "$gone_rc" -eq 0 ] && [[ "$out" == CLASSIFY=P1* ]] && grep -q "^WARN:.*gone-manifest.json" "$gone_err" && ! grep -q "^jq:" "$gone_err" && [ ! -e events.jsonl ]; then
  ok "钥匙文件没了:事件跳过并 WARN 点名它,分级照常"
else
  no "钥匙文件没了的处理 (rc=$gone_rc out=$out err=$(cat "$gone_err"))"
fi
rm -f "$gone_err"

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
