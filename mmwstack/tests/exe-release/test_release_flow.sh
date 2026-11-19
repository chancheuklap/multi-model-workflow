#!/usr/bin/env bash
# release-flow.sh 引擎空跑:载入 fail-loud、状态机推进、stage run 失败后自动派发、round cap、resume、原子写。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RF="$SCRIPT_DIR/../../skills/exe-release/scripts/release-flow.sh"
FIX="$SCRIPT_DIR/fixtures/release-flow"
SF=".release/release-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }
# $( ) 里的命令退非零不会让脚本停,也看不出来:要断退出码就得单独取。
rc_of() { local rc=0; "$@" >/dev/null 2>&1 || rc=$?; echo "$rc"; }

echo "=== test_release_flow.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
TOP="$(pwd -P)"
git init -q
git config user.email t@t
git config user.name t
echo s > s
git add -A
git commit -qm s

jq 'del(.product)' "$FIX/manifest.fake.json" > bad.json
if bash "$RF" init --manifest bad.json 2>/dev/null; then
  no "bad manifest 应 fail-loud"
else
  ok "bad manifest fail-loud 退非零"
fi
[ ! -f "$SF" ] && ok "fail-loud 不写 release-state" || no "fail-loud 竟写了 state"

bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
[ "$(jq -r .product "$SF")" = "fixture-product" ] && ok "init 注入 product" || no "product ($(jq -r .product "$SF"))"
# 钥匙声明的两段在前，引擎的标准三段追加在后。验钥匙/装配/远端构建是保留字，
# 钥匙用不了(合同挡在 init 之前)——曾经允许同名接管，抄来的一句 assemble 就把引擎的
# 验钥匙整段关掉，而日志每一步都是绿的。
[ "$(jq -r '[.stages[].name]|join(",")' "$SF")" = "doctor,smoke,verify_key,assemble,build" ] \
  && ok "init 钥匙的 2 段在前、引擎的标准 3 段在后" || no "stages len ($(jq -r '[.stages[].name]|join(",")' "$SF"))"
[ "$(jq -r '[.stages[]|select(.status=="pending")]|length' "$SF")" = "5" ] && ok "stages 全 pending" || no "pending"

[ "$(bash "$RF" where)" = "STAGE:doctor RUN:true" ] && ok "where 报首 stage+run" || no "where ($(bash "$RF" where))"

# 守:driving.md 让驱动只读 where 的 stdout、不读退出码——where 的每个状态都退 0。
# 退 1 是「引擎过不去的事实」,退 2 是不认识的子命令;三种结果在所有子命令上含义相同。
[ "$(rc_of bash "$RF" where)" = "0" ] && ok "where 报 STAGE 时退 0" || no "where STAGE 退出码"
[ "$(rc_of bash "$RF")" = "2" ] && ok "没给子命令退 2" || no "没给子命令的退出码 ($(rc_of bash "$RF"))"
[ "$(rc_of bash "$RF" no-such-subcommand)" = "2" ] && ok "不认识的子命令退 2" || no "不认识的子命令退出码"
[ "$(rc_of bash "$RF" --help)" = "0" ] && ok "--help 退 0" || no "--help 退出码"
for verb_group in stage round; do
  usage_err="$(bash "$RF" "$verb_group" no-such-verb 2>&1 >/dev/null || true)"
  if [ "$(rc_of bash "$RF" "$verb_group" no-such-verb)" = "1" ] && [[ "$usage_err" == "ERROR: usage:"* ]]; then
    ok "$verb_group 后面的未知动词退 1 并给 ERROR: usage:"
  else
    no "$verb_group 未知动词 ($usage_err)"
  fi
done

# 守:stage run 只跑最早没做完的那一段。管线有序,跳过前面的去跑 build 就是拿没验过的脚本上构建机。
if bash "$RF" stage run --stage build >/dev/null 2>&1; then
  no "跳过前面的 stage 直接跑 build 竟放行"
else
  ok "stage run 拒绝跳到后面的 stage"
fi
[ "$(jq -r '[.stages[]|select(.status!="pending")]|length' "$SF")" = "0" ] \
  && [ "$(jq -r '.attempt_ledger|length' "$SF")" = "0" ] \
  && ok "被拒的 stage run 什么也没执行" || no "被拒的 stage run 改了状态"

if bash "$RF" stage run --stage doctor >/dev/null; then
  [ "$(jq -r '.stages[]|select(.name=="doctor").status' "$SF")" = "done" ] && ok "stage run 真执行并标 done" || no "stage run 未标 doctor done"
  [ "$(bash "$RF" where)" = "STAGE:smoke RUN:true" ] && ok "stage run 后推进到 smoke" || no "推进 ($(bash "$RF" where))"
  [ "$(jq -r '.current_stage' "$SF")" = "smoke" ] && ok "stage run 做完后 current_stage 指向下一段" || no "current_stage ($(jq -r '.current_stage' "$SF"))"
  [ "$(jq -r '.attempt_ledger[-1] | "\(.stage) \(.outcome)"' "$SF")" = "doctor done" ] \
    && ok "stage run 的这次尝试在 attempt_ledger 里记为 done" || no "attempt_ledger 末条 ($(jq -c '.attempt_ledger[-1]' "$SF"))"
else
  no "stage run 应执行当前普通 argv"
fi
close_err="$(mktemp)"
if bash "$RF" close >/dev/null 2>"$close_err"; then
  no "close 在阶段未全部完成时放行"
else
  grep -q "smoke" "$close_err" && ok "close 拒绝未完成的轮次并点名剩余 stage" || no "close 拒绝理由未点名剩余 stage ($(cat "$close_err"))"
fi
rm -f "$close_err"

for stage in smoke verify_key assemble build; do bash "$RF" stage done --stage "$stage" >/dev/null; done
[ "$(bash "$RF" where)" = "SUCCESS:all stages done" ] && ok "where -> SUCCESS" || no "SUCCESS ($(bash "$RF" where))"
[ "$(rc_of bash "$RF" where)" = "0" ] && ok "where 报 SUCCESS 时退 0" || no "where SUCCESS 退出码"
ledger_before="$(jq -r '.attempt_ledger|length' "$SF")"
if bash "$RF" stage run >/dev/null 2>&1; then
  no "没有剩余 stage 时 stage run 竟放行"
else
  [ "$(jq -r '.attempt_ledger|length' "$SF")" = "$ledger_before" ] \
    && ok "没有剩余 stage 时 stage run 被拒,不留尝试记录" || no "被拒的 stage run 仍记了一次尝试"
fi
bash "$RF" close >/dev/null && ok "全 done 后 close 成功收束" || no "全 done 后 close 被拒"
[ ! -f "$SF" ] && ok "close 之后没有正在进行的一轮" || no "close 没删活状态"

# 守:close 留下的交付记录是步骤 4 同 commit 校验读的唯一凭据:产品名加出包那一刻的 commit。
# 记录要能被 same-commit 读回来,而不是各写各的格式。
delivered_record=".release/delivered/fixture-product.json"
[ "$(jq -r '.product' "$delivered_record" 2>/dev/null)" = "fixture-product" ] \
  && [ "$(jq -r '.source_commit' "$delivered_record" 2>/dev/null)" = "$(git rev-parse HEAD)" ] \
  && ok "close 留下产品名与出包 commit 的交付记录" || no "交付记录 ($(cat "$delivered_record" 2>/dev/null))"
[ "$(bash "$RF" same-commit fixture-product)" = "OK fixture-product" ] \
  && ok "same-commit 认 close 留下的记录" || no "same-commit 读不懂 close 的记录 ($(bash "$RF" same-commit fixture-product))"

# 守:交付记录落在主检出的根,不落在任务 worktree 里——要比对的是几次出包之间的 commit,
# 跨任务、跨会话才成立,而任务 worktree 收尾就删,记录会跟着一起没。
rm -f "$delivered_record"
git worktree add -q "$TMP/linked" -b linked-branch >/dev/null 2>&1
(
  cd "$TMP/linked"
  bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
  for linked_stage in doctor smoke verify_key assemble build; do bash "$RF" stage done --stage "$linked_stage" >/dev/null; done
  bash "$RF" close >/dev/null
)
[ -f "$TMP/$delivered_record" ] && [ ! -e "$TMP/linked/.release/delivered" ] \
  && ok "在 worktree 里 close,交付记录落主检出的根" || no "交付记录没落在主检出的根"
rm -f "$delivered_record"
git worktree remove --force "$TMP/linked"
git branch -q -D linked-branch

# ── init 的入口 ─────────────────────────────────────────────────────────────
# 守:已有一轮在进行时 init 必须拒绝。静默覆盖会丢掉那一轮的状态与现场,
# 而 where 报出怪状态时最顺手的错误动作就是再 init 一次(driving.md 明令不许)。
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
mkdir -p "$(dirname "$SF")/release-artifacts/a0-doctor"
printf 'keep\n' > "$(dirname "$SF")/release-artifacts/a0-doctor/doctor.log"
state_before="$(cat "$SF")"
if open_err="$(bash "$RF" init --manifest "$FIX/manifest.fake.json" 2>&1 >/dev/null)"; then
  no "已有一轮在进行时 init 竟放行"
else
  case "$open_err" in
    *fixture-product*) ok "已有一轮在进行时 init 被拒并点名那个产品" ;;
    *) no "init 被拒但没点名在进行的产品 ($open_err)" ;;
  esac
fi
[ "$(cat "$SF")" = "$state_before" ] && ok "被拒的 init 不动那一轮的状态" || no "被拒的 init 改了状态"
[ -f "$(dirname "$SF")/release-artifacts/a0-doctor/doctor.log" ] \
  && ok "被拒的 init 不清那一轮的现场" || no "被拒的 init 清掉了现场"
bash "$RF" abort >/dev/null

# 守:--max-rounds 是轮次上限,必须是非负整数。-1 和 1.5 能通过 jq 却会让上限悄悄失效。
for bad_rounds in abc -1 1.5 ""; do
  if bash "$RF" init --manifest "$FIX/manifest.fake.json" --max-rounds "$bad_rounds" >/dev/null 2>&1; then
    no "--max-rounds '$bad_rounds' 竟放行"
  else
    [ ! -f "$SF" ] && ok "--max-rounds '$bad_rounds' 被拒且不写状态" || no "--max-rounds '$bad_rounds' 被拒却写了状态"
  fi
  rm -f "$SF"
done

# 守:钥匙的 stages 在前、引擎标准三段居中、post_build_stages 在最后——出包之后才能跑的
# 收尾检查排在 build 前面就永远读不到安装包。manifest 路径落成绝对路径:之后在别的目录里
# 跑 where / stage fail,引擎还得找得到它(事件记录就读它)。
jq '.post_build_stages=[{name:"publish",run:["true"]}]' "$FIX/manifest.fake.json" > post-build-manifest.json
bash "$RF" init --manifest post-build-manifest.json >/dev/null
[ "$(jq -r '[.stages[].name]|join(",")' "$SF")" = "doctor,smoke,verify_key,assemble,build,publish" ] \
  && ok "post_build_stages 排在引擎标准三段之后" || no "stage 顺序 ($(jq -r '[.stages[].name]|join(",")' "$SF"))"
mkdir -p other-dir
(cd other-dir && bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null 2>&1)
[ -s other-dir/events.jsonl ] \
  && ok "init 时给的是相对路径,换个目录跑引擎照样找得到钥匙" || no "换目录后找不到钥匙,事件没记下"
bash "$RF" abort >/dev/null
rm -rf other-dir

mkdir -p capture-bin
cat > capture-bin/capture-argv <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$ARGV_CAPTURE"
SH
chmod +x capture-bin/capture-argv
jq '.stages=[{name:"capture",run:["capture-argv","${RELEASE_PLUGIN_DIR}","${RELEASE_STAGE_DIR}","${RELEASE_LOOP_DIR}"]}]' "$FIX/manifest.fake.json" > capture-manifest.json
bash "$RF" init --manifest capture-manifest.json >/dev/null
if PATH="$PWD/capture-bin:$PATH" ARGV_CAPTURE="$TMP/plugin-dir.argv" bash "$RF" stage run --stage capture >/dev/null; then
  expected_plugin_dir="$(
    CDPATH= cd -- "$(dirname -- "$RF")"
    pwd -P
  )"
  [ "$(sed -n 1p "$TMP/plugin-dir.argv")" = "$expected_plugin_dir" ] && ok "stage run 展开 RELEASE_PLUGIN_DIR 为引擎物理目录" || no "RELEASE_PLUGIN_DIR 展开错误"
  [ "$(sed -n 2p "$TMP/plugin-dir.argv")" = "$TOP/.release/release-artifacts/a0-capture" ] \
    && ok "stage run 展开 RELEASE_STAGE_DIR 为本次尝试的目录" || no "RELEASE_STAGE_DIR 展开错误 ($(sed -n 2p "$TMP/plugin-dir.argv"))"
  [ "$(sed -n 3p "$TMP/plugin-dir.argv")" = "$TOP/.release/release-artifacts/_loop" ] \
    && ok "stage run 展开 RELEASE_LOOP_DIR 为整轮的交接目录" || no "RELEASE_LOOP_DIR 展开错误 ($(sed -n 3p "$TMP/plugin-dir.argv"))"
else
  no "stage run 应执行 capture argv"
fi

# 守:钥匙里的 stage 命令靠这六个环境变量认出它在哪一轮、该把东西放哪;工作目录固定是产品仓库根,
# 不管驱动 agent 在哪个子目录里敲的命令。少一个,stage 就在没有它的前提下照跑,
# 日志里看不出来。
bash "$RF" abort >/dev/null
probe_script='pwd -P > "$PROBE_OUT"; printf "%s\n" "$RELEASE_REPO_ROOT" "$RELEASE_STATE_FILE" "$RELEASE_STAGE_NAME" "$RELEASE_SOURCE_COMMIT" "$RELEASE_STAGE_DIR" "$RELEASE_LOOP_DIR" >> "$PROBE_OUT"; jq -r ".stages[]|select(.name==\"probe\").status" "$RELEASE_STATE_FILE" >> "$PROBE_OUT"'
jq --arg s "$probe_script" '.stages=[{name:"probe",run:["sh","-c",$s]}]' "$FIX/manifest.fake.json" > probe-manifest.json
bash "$RF" init --manifest probe-manifest.json >/dev/null
mkdir -p probe-subdir
if (cd probe-subdir && PROBE_OUT="$TMP/probe.out" bash "$RF" stage run --stage probe >/dev/null); then
  probe_line() { sed -n "${1}p" "$TMP/probe.out"; }
  [ "$(probe_line 1)" = "$TOP" ] && ok "stage 命令的工作目录是产品仓库根" || no "stage 工作目录 ($(probe_line 1))"
  [ "$(probe_line 2)" = "$TOP" ] && ok "RELEASE_REPO_ROOT" || no "RELEASE_REPO_ROOT ($(probe_line 2))"
  [ "$(probe_line 3)" = "$TOP/.release/release-state.json" ] && ok "RELEASE_STATE_FILE" || no "RELEASE_STATE_FILE ($(probe_line 3))"
  [ "$(probe_line 4)" = "probe" ] && ok "RELEASE_STAGE_NAME" || no "RELEASE_STAGE_NAME ($(probe_line 4))"
  [ "$(probe_line 5)" = "$(git rev-parse HEAD)" ] && ok "RELEASE_SOURCE_COMMIT" || no "RELEASE_SOURCE_COMMIT ($(probe_line 5))"
  [ "$(probe_line 6)" = "$TOP/.release/release-artifacts/a0-probe" ] && ok "RELEASE_STAGE_DIR 是本次尝试的目录" || no "RELEASE_STAGE_DIR ($(probe_line 6))"
  [ "$(probe_line 7)" = "$TOP/.release/release-artifacts/_loop" ] && ok "RELEASE_LOOP_DIR 是整轮固定的交接目录" || no "RELEASE_LOOP_DIR ($(probe_line 7))"
  # 进程在这一段跑到一半被杀时,状态里得是 running,where 才知道它没做完而不是跳过它。
  [ "$(probe_line 8)" = "running" ] && ok "stage 执行期间状态里是 running" || no "stage 执行期间的状态 ($(probe_line 8))"
else
  no "probe stage 应执行成功"
fi
rm -rf probe-subdir

bash "$RF" abort >/dev/null
cat > diagnose-p0.sh <<SH
#!/usr/bin/env bash
cat "$FIX/finding.p0.json"
SH
chmod +x diagnose-p0.sh
jq --arg diagnose "$TMP/diagnose-p0.sh" '.stages=[{name:"broken",run:["false"]}] | .diagnose=[$diagnose]' "$FIX/manifest.fake.json" > failed-stage-manifest.json
bash "$RF" init --manifest failed-stage-manifest.json >/dev/null
rm -f events.jsonl
if bash "$RF" stage run --stage broken >/dev/null; then
  [ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "普通 stage 非零自动 diagnose 并 P0 PAUSE" || no "普通 stage 非零未写 P0 PAUSE"
else
  no "普通 stage 非零应进入诊断分级而非直接退回 drive"
fi
# 守:停下的那一轮在事件流里只留一条 paused。P0 已经停了,stage run 就不该再去派发——
# 否则同一次暂停被记两遍,receipt 里也多出一条根本没发生过的派发尝试。
[ "$(grep -c '"event":"paused"' events.jsonl 2>/dev/null || true)" = "1" ] \
  && ok "P0 停下后只记一条 paused 事件" || no "paused 事件条数 ($(grep -c '"event":"paused"' events.jsonl 2>/dev/null || true))"
[ "$(jq -r '[.attempt_ledger[]|select(.action_kind=="dispatch")]|length' "$SF")" = "0" ] \
  && ok "P0 停下后没有再去派发" || no "P0 停下后又派发了一次"

# 守:stage run 失败后自己接着派发(原来的 dispatch)和计轮次(原来的 round next),
# 驱动 agent 不用再跑那两条命令——只剩"问 where,跑它说的 stage"。
bash "$RF" abort >/dev/null
cat > diagnose-transient.sh <<SH
#!/usr/bin/env bash
cat "$FIX/finding.transient.json"
SH
chmod +x diagnose-transient.sh
jq --arg diagnose "$TMP/diagnose-transient.sh" '.stages=[{name:"doctor",run:["false"]}] | .diagnose=[$diagnose]' "$FIX/manifest.fake.json" > transient-stage-manifest.json
bash "$RF" init --manifest transient-stage-manifest.json >/dev/null
round_before="$(jq -r '.round' "$SF")"
out="$(bash "$RF" stage run --stage doctor 2>&1)"
case "$out" in
  *"TRANSIENT-RETRY:doctor"*) ok "stage run 失败后自己派发,不用驱动 agent 再跑 dispatch" ;;
  *) no "stage run 未自动派发 ($out)" ;;
esac
[ "$(jq -r '.stages[0].status' "$SF")" = "pending" ] && ok "stage run 自动派发后重置该 stage" || no "stage run 自动派发未重置 stage"
jq -e 'any(.attempt_ledger[]; .action_kind == "transient_retry" and .root_cause_fingerprint == "transient:network.pnpm_fetch")' "$SF" >/dev/null \
  && ok "瞬态重跑记进 attempt_ledger,receipt 看得到重试过几次" || no "瞬态重跑没记账"
[ "$(jq -r '.round' "$SF")" = "$((round_before + 1))" ] && ok "stage run 自动派发后自己计了轮次" || no "stage run 自动派发未计轮次(round=$(jq -r '.round' "$SF"))"
[ "$(jq -r '.pause' "$SF")" = "null" ] && ok "自动派发后没有 pause,驱动 agent 只需再问 where" || no "自动派发后意外 pause"
bash "$RF" abort >/dev/null

# 守:钥匙没声明 diagnose 时用技能自带的诊断器,从失败日志一路走到分级与派发。
# 日志里的 ECONNRESET 是网络瞬态:能被翻译成 transient 指纹并自动重跑,
# 说明引擎把 stage 日志交到了诊断器手里,而不是让它对着空现场回「无法分类」。
jq 'del(.diagnose) | .stages=[{name:"doctor",run:["sh","-c","echo ECONNRESET; exit 1"]}]' "$FIX/manifest.fake.json" > default-diagnose-manifest.json
bash "$RF" init --manifest default-diagnose-manifest.json >/dev/null
out="$(bash "$RF" stage run --stage doctor 2>&1)"
case "$out" in
  *"TRANSIENT-RETRY:doctor"*) ok "没声明 diagnose 时技能自带的诊断器翻译出瞬态失败并重跑" ;;
  *) no "默认诊断器没把失败翻译出来 ($out)" ;;
esac
bash "$RF" abort >/dev/null

# 守:交给诊断器的三个环境变量各管一份现场。diagnose_core 只认这三个——丢一个,
# 它就看不见对应的日志,真实失败降级成「无法分类」交人。
cat > diagnose-dump.sh <<SH
#!/usr/bin/env bash
printf '%s\n' "\$RELEASE_FAILED_STAGE" "\$RELEASE_STAGE_LOG" "\$RELEASE_BUILD_LOG" > "$TMP/diagnose.env"
echo '{"findings":[]}'
SH
chmod +x diagnose-dump.sh
jq --arg d "$TMP/diagnose-dump.sh" \
  '.stages=[{name:"noisy",run:["sh","-c","echo marker-from-the-stage; exit 1"]}] | .diagnose=[$d]' \
  "$FIX/manifest.fake.json" > diagnose-dump-manifest.json
bash "$RF" init --manifest diagnose-dump-manifest.json >/dev/null
bash "$RF" stage run --stage noisy >/dev/null 2>&1 || true
diag_line() { sed -n "${1}p" "$TMP/diagnose.env"; }
[ "$(diag_line 1)" = "noisy" ] && ok "RELEASE_FAILED_STAGE 是失败的那一段" || no "RELEASE_FAILED_STAGE ($(diag_line 1))"
grep -q marker-from-the-stage "$(diag_line 2)" 2>/dev/null \
  && ok "RELEASE_STAGE_LOG 指向这一段自己的输出" || no "RELEASE_STAGE_LOG ($(diag_line 2))"
[ -z "$(diag_line 3)" ] && ok "没有远端构建日志时 RELEASE_BUILD_LOG 为空" || no "RELEASE_BUILD_LOG 不该有值 ($(diag_line 3))"
bash "$RF" abort >/dev/null

bash "$RF" abort >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
[ "$(jq -r '.source_commit' "$SF")" = "$(git rev-parse HEAD)" ] && ok "init 绑定完整 source_commit" || no "init 未绑定 source_commit"
# 失败的是第二段(smoke):同 HEAD 的 resume 只重来 smoke 及其后,不把已经做完的 doctor 也推倒。
# 停在 P0 上的那一轮 resume 之后 where 不再报 PAUSED,驱动才有下一步可走。
bash "$RF" stage done --stage doctor >/dev/null
[ "$(jq -r '[.attempt_ledger[]|select(.stage=="doctor" and .outcome=="done")]|length' "$SF")" = "1" ] \
  && ok "stage done 记进 attempt_ledger,receipt 看得到人工确认过哪一段" || no "stage done 没进 attempt_ledger"
bash "$RF" stage fail --stage smoke --findings "$FIX/finding.p0.json" >/dev/null
[ "$(bash "$RF" where)" = "PAUSED:needs-redirection" ] || no "前提:P0 后应停下 ($(bash "$RF" where))"
bash "$RF" resume >/dev/null
[ "$(jq -r '.current_stage' "$SF")" = "smoke" ] && ok "同 HEAD resume 从最早 failed stage 继续" || no "同 HEAD resume 未回到 smoke"
[ "$(jq -r '.stages[]|select(.name=="doctor").status' "$SF")" = "done" ] && ok "同 HEAD resume 不推倒失败之前已完成的 stage" || no "同 HEAD resume 把 doctor 也重置了"
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "4" ] && ok "同 HEAD resume 令失败 stage 及后继 pending" || no "同 HEAD resume stage 状态错误"
[ "$(jq -r '.pause' "$SF")" = "null" ] && [ "$(bash "$RF" where)" = "STAGE:smoke RUN:true" ] \
  && ok "resume 解除暂停,where 回到该 stage" || no "resume 后 where ($(bash "$RF" where))"

bash "$RF" abort >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
bash "$RF" stage done --stage doctor >/dev/null
echo changed > source-change
git add source-change
git commit -qm source-change
bash "$RF" resume >/dev/null
[ "$(jq -r '.source_commit' "$SF")" = "$(git rev-parse HEAD)" ] && ok "HEAD 改变后更新 source_commit" || no "HEAD 改变后 source_commit 过期"
[ "$(jq -r '.current_stage' "$SF")" = "doctor" ] && ok "HEAD 改变后从首 stage 重验" || no "HEAD 改变后未回首 stage"
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "5" ] && ok "HEAD 改变后所有 stage pending" || no "HEAD 改变后残留旧产物状态"

bash "$RF" abort >/dev/null
# ── 远程构建 ────────────────────────────────────────────────────────────────
# 假构建机在 fixtures/fake-remote/：它维护一棵目录树当远端文件系统、一份登记表当
# Task Scheduler，不记录命令文本。下面每条断的都是这两样的最终状态——引擎把任务名
# 拼错、create 与 delete 用了两个名字，登记表里就会留下残骸，断言自然红。
#
# 上传的 wrapper 内容对不对（脱附会话里日志落不落地、PS 5.1 的编码转换）要一台
# 真的 Windows 构建机才能验，这里只断它被上传了。
REMOTE_FIX="$SCRIPT_DIR/fixtures/fake-remote"
export FAKE_REMOTE_ROOT="$TMP/remote-fs"
export FAKE_REMOTE_TASKS="$TMP/remote-tasks.json"

remote_reset() {
  rm -rf "$FAKE_REMOTE_ROOT"; mkdir -p "$FAKE_REMOTE_ROOT"
  printf '{}' > "$FAKE_REMOTE_TASKS"
  unset FAKE_RUN_FAILS FAKE_REMOVE_FAILS
  export FAKE_BUILD_OUTCOME=success
}

remote_build() {
  PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
    RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="${1:-C:/release-input}" \
    bash "$RF" stage run --stage build
}

build_dir() { find "$FAKE_REMOTE_ROOT" -name run-release.cmd -exec dirname {} \; 2>/dev/null | head -1; }
task_count() { jq -r 'length' "$FAKE_REMOTE_TASKS" 2>/dev/null || echo BROKEN; }
build_status() { jq -r '.stages[] | select(.name=="build") | .status' "$SF"; }

# 远端构建这一段用引擎自己的那一份(钥匙用不了 build 这个名字)。装配的产物落在
# _loop/ 下,所以这里把假的 release.ps1 与 context 放到同一处,再把前面几段标 done。
LOOP_DIR="$TMP/.release/release-artifacts/_loop"
seed_loop_pair() {
  mkdir -p "$LOOP_DIR"
  printf '# fake release\n' > "$LOOP_DIR/release.ps1"
  printf '{"repo_root":"/placeholder","product":"test-product"}\n' > "$LOOP_DIR/release-context.json"
}
jq '.stages=[]' "$FIX/manifest.fake.json" > remote-build-manifest.json
init_for_remote_build() {
  # abort, not close: close now refuses a release loop that is not DONE, and the previous scenario's
  # release loop usually is not. abort always drops it and clears the state file so init can start.
  bash "$RF" abort >/dev/null 2>&1 || true
  bash "$RF" init --manifest remote-build-manifest.json >/dev/null
  bash "$RF" stage done --stage verify_key >/dev/null
  bash "$RF" stage done --stage assemble >/dev/null
  seed_loop_pair
}

# 守:构建机拿到的必须是当前 HEAD 的代码。拿错版本出的包发给客户就是错的产品。
remote_reset
init_for_remote_build
if remote_build >/dev/null; then
  bd="$(build_dir)"
  [ "$(cat "$bd/SOURCE_COMMIT.txt" 2>/dev/null)" = "$(git rev-parse HEAD)" ] \
    && ok "构建机拿到的是当前 HEAD" || no "SOURCE_COMMIT 不是 HEAD"
  [ "$(cat "$bd/source/s" 2>/dev/null)" = "$(cat s)" ] \
    && ok "源码真的解压到构建机且内容一致" || no "远端源码内容对不上"
  missing_inputs=""
  for f in release.ps1 release-context.json run-release.ps1 run-release.cmd SOURCE_COMMIT.txt; do
    [ -s "$bd/$f" ] || missing_inputs="$missing_inputs $f"
  done
  [ -z "$missing_inputs" ] && ok "构建输入都上传了" || no "构建输入缺:$missing_inputs"

  # 守:源码 zip 是 `git archive $(cat SOURCE_COMMIT.txt)` 一字不差重生得出来的,不是记录。
  # 一份几百 MB,每一次尝试在两端各留一份,几轮就把两台机器塞满。
  [ ! -e "$bd/source.zip" ] && ok "解压后构建机上不留源码 zip" || no "构建机上留着源码 zip"
  [ -z "$(find "$(dirname "$SF")/release-artifacts" -name source.zip 2>/dev/null)" ] \
    && ok "上传后 Mac 上不留源码 zip" || no "Mac 上留着源码 zip"

  # 守:构建目录每个产品固定一个。名字带 commit,构建机的编译缓存(按绝对路径认人)
  # 每轮都不中;名字不带产品,同一 commit 的第二个产品会冲掉前一个的安装包。
  case "$(basename "$bd")" in
    "test-product") ok "构建目录按产品名固定" ;;
    *) no "构建目录命名错误($(basename "$bd"))" ;;
  esac

  # 守:残留的计划任务会在下一轮同 commit 抢写产物,把别人的构建结果当成自己的。
  [ "$(task_count)" = "0" ] && ok "构建结束不留计划任务" || no "残留计划任务($(cat "$FAKE_REMOTE_TASKS"))"
  [ "$(build_status)" = "done" ] && ok "构建成功标 stage done" || no "构建成功未标 done"
  jq -e 'any(.attempt_ledger[]; any(.log_refs[]; startswith("pc:")))' "$SF" >/dev/null \
    && ok "记下构建机日志位置" || no "没记日志位置"
else
  no "构建成功场景 stage run 应退 0"
fi
bash "$RF" abort >/dev/null

# 守:装配之后技能自己改了,_loop 里那份 release.ps1 就过期了。拿它去构建机跑,每一步都对,
# 只是跑的不是刚改的那一份——这一类失败在日志里完全看不出来。
# 连带守 where 的判定顺序:管线有序,下一步是第一个还没 done 的阶段。曾经先挑 failed 再挑
# pending,于是这里把靠前的 assemble 打回 pending 之后,where 还指着靠后那个 build,驱动原地打转。
remote_reset
init_for_remote_build
tmp_state="$(mktemp)"
jq '.skill_fingerprint = "recorded-when-the-skill-looked-different"
    | (.stages |= map(if .name == "build" then .status = "failed" else . end))' "$SF" > "$tmp_state"
mv "$tmp_state" "$SF"
if remote_build >/dev/null 2>&1; then
  no "技能改过之后 build 应该拒跑"
else
  ok "技能改过之后 build 拒跑,不拿过期脚本上构建机"
fi
[ "$(jq -r '.stages[]|select(.name=="assemble").status' "$SF")" = "pending" ] \
  && [ "$(jq -r '.current_stage' "$SF")" = "assemble" ] \
  && ok "拒跑同时把装配打回 pending 并回到 assemble" || no "装配没被打回 pending"
case "$(bash "$RF" where)" in
  STAGE:assemble*) ok "where 指向第一个还没 done 的阶段(装配),不是靠后那个 failed 的构建" ;;
  *) no "where ($(bash "$RF" where))" ;;
esac
bash "$RF" abort >/dev/null

# 守:schtasks 的命令行跨 cmd、PowerShell 语言、native CLI 三个解析器,单引号只在其中
# 一个是定界符。任务必须指向一个上传好的 .cmd,不能把多段命令串进任务命令行,也不能带
# 引号——带了的话清理时找不到任务,构建机上会堆死条目。
task_cmd="$(tail -1 "$FAKE_REMOTE_TASKS.history" 2>/dev/null | jq -r '.cmd // "无"')"
case "$task_cmd" in
  *run-release.cmd) ok "计划任务指向上传好的 .cmd" ;;
  *) no "计划任务命令行不是 .cmd($task_cmd)" ;;
esac
case "$task_cmd" in
  *\'*|*'"'*) no "计划任务命令行带引号(跨三个解析器会被当字面字符)" ;;
  *) ok "计划任务命令行裸传不带引号" ;;
esac

# 守:工具链缓存必须落在构建机的数据盘上。不设的话 uv / Nuitka / ccache / pnpm / Electron
# 全都落在 %LOCALAPPDATA%——构建目录在数据盘上跑得好好的,系统盘却被这几个缓存慢慢填满,
# 直到某一轮磁盘闸把出包整个拦下来。这是真发生过的。
remote_reset
init_for_remote_build
remote_build >/dev/null 2>&1 || true
bd="$(build_dir)"
[ "$(jq -r '.cache_root' "$bd/release-context.json" 2>/dev/null)" = "C:/release-input-cache" ] \
  && ok "缓存根没人指定时从构建输入根推:<根>-cache" || no "缓存根 ($(jq -r '.cache_root' "$bd/release-context.json" 2>/dev/null))"

remote_reset
init_for_remote_build
RELEASE_CACHE_ROOT="D:/shared-cache" remote_build >/dev/null 2>&1 || true
bd="$(build_dir)"
[ "$(jq -r '.cache_root' "$bd/release-context.json" 2>/dev/null)" = "D:/shared-cache" ] \
  && ok "环境变量能临时把缓存指到别处" || no "缓存根环境变量没生效"

# 守:构建目录是过程不是记录。一轮的源码树、node_modules 与中间产物是几个 GB,安装包收进
# 交付目录、日志回传之后再没有人会读它。留着的话构建机在几十轮内被自己的中间产物填满。
remote_reset
init_for_remote_build
printf '{"repo_root":"/placeholder","product":"test-product","build_target":{"installer_glob":"out/*-setup.exe"}}\n' \
  > "$LOOP_DIR/release-context.json"
remote_build >/dev/null 2>&1 || true
# 交付目录没人指定时从构建输入根推：<根>-delivered。技能里不写死任何一个仓库的路径。
[ -n "$(find "$FAKE_REMOTE_ROOT/release-input-delivered" -name '*-setup.exe' 2>/dev/null)" ] \
  && ok "安装包收进推出来的交付目录" || no "安装包没进交付目录"
[ -z "$(build_dir)" ] && ok "成功并交付后删掉远端构建目录" || no "远端构建目录留在构建机上"
# driving.md 让收尾去 build 阶段的日志里找 DELIVERED 行拿安装包路径,不许凭空编一个。
grep -rq '^DELIVERED .*test-product-setup.exe' "$(dirname "$SF")/release-artifacts" --include=build.log \
  && ok "build 日志里留着 DELIVERED 行" || no "build 日志里没有 DELIVERED 行"
bash "$RF" abort >/dev/null

# 守:钥匙声明要带回的构建产物(return_artifacts),必须在删掉远端构建目录之前拷回交接目录——
# post_build_stages 读的就是这一轮构建出来的那一份。拷不回来 build 失败,并留下远端现场。
remote_reset
init_for_remote_build
printf '{"repo_root":"/placeholder","product":"test-product","build_target":{"installer_glob":"out/*-setup.exe","return_artifacts":{"out/test-product-setup.exe":"returned.bin"}}}\n' \
  > "$LOOP_DIR/release-context.json"
rm -f "$LOOP_DIR/returned.bin"
remote_build >/dev/null 2>&1 || true
[ "$(cat "$LOOP_DIR/returned.bin" 2>/dev/null)" = "fake installer" ] \
  && ok "声明的构建产物带回了交接目录" || no "构建产物没带回"
[ -z "$(build_dir)" ] && [ "$(build_status)" = "done" ] \
  && ok "带回之后 build 照常成功并清掉远端构建目录" || no "带回之后 build 状态不对 ($(build_status))"
bash "$RF" abort >/dev/null

remote_reset
init_for_remote_build
printf '{"repo_root":"/placeholder","product":"test-product","build_target":{"installer_glob":"out/*-setup.exe","return_artifacts":{"out/never-built.zip":"maps.zip"}}}\n' \
  > "$LOOP_DIR/release-context.json"
rm -f "$LOOP_DIR/maps.zip"
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" = "failed" ] \
  && ok "带不回声明的产物时 build 失败" || no "带不回声明的产物时 build 状态是 $(build_status)"
[ -n "$(build_dir)" ] \
  && ok "带不回时留下远端构建目录" || no "带不回时远端现场被删了"
[ -z "$(find "$LOOP_DIR" -name 'maps.zip*' 2>/dev/null)" ] \
  && ok "带不回时交接目录里不留半截文件" || no "交接目录里留了半截文件"
bash "$RF" abort >/dev/null

# 守:失败的构建目录必须留下。根因只存在于那台机器上的那个目录里,删了就再也查不出来。
remote_reset
init_for_remote_build
export FAKE_BUILD_OUTCOME=fail:3
remote_build >/dev/null 2>&1 || true
[ -n "$(build_dir)" ] && ok "失败的构建目录留在构建机上" || no "失败现场被删掉了"
# 任务名要留在远端目录里:这一侧断掉之后再来接,清理靠它才知道该结束哪个任务。
[ "$(tr -d '\r\n' < "$(build_dir)/build-run.task" 2>/dev/null)" = "$(tail -1 "$FAKE_REMOTE_TASKS.history" | jq -r '.name')" ] \
  && ok "建任务时把任务名记在远端构建目录里" || no "远端构建目录里没有任务名 ($(cat "$(build_dir)/build-run.task" 2>/dev/null))"
bash "$RF" abort >/dev/null
printf '{"repo_root":"/placeholder","product":"test-product"}\n' > "$LOOP_DIR/release-context.json"

# 守:构建目录每个产品固定一个,按 commit 命名的旧目录(一个几个 GB)全部清掉;
# 别的产品的目录不碰。断的是「哪几个还在」,不是「删过东西」。
remote_reset
init_for_remote_build
input_root="$FAKE_REMOTE_ROOT/release-input"
mkdir -p "$input_root"
for old_dir in 000000000001 000000000002 000000000003; do
  mkdir -p "$input_root/$old_dir-test-product"
  printf 'x\n' > "$input_root/$old_dir-test-product/build-run.log"
done
mkdir -p "$input_root/000000000004-other-product"
touch -t 202601010101 "$input_root/000000000001-test-product"
touch -t 202601010102 "$input_root/000000000002-test-product"
touch -t 202601010103 "$input_root/000000000003-test-product"
export FAKE_BUILD_OUTCOME=fail:3
remote_build >/dev/null 2>&1 || true
[ ! -e "$input_root/000000000001-test-product" ] && [ ! -e "$input_root/000000000002-test-product" ] \
  && [ ! -e "$input_root/000000000003-test-product" ] \
  && ok "按 commit 命名的旧构建目录全部清掉" || no "旧构建目录还堆着"
[ -d "$input_root/test-product/source" ] && ok "本产品在固定目录里构建" || no "没有在 <根>/<产品> 里构建"
[ -e "$input_root/000000000004-other-product" ] && ok "不碰别的产品的目录" || no "删到了别的产品"
bash "$RF" abort >/dev/null

# 守:指纹是引擎在装配成功那一刻自己记下的,不是别人写进去的。上面那条拿手写的假指纹验
# 「对不上就拒跑」;这里验另一半:真跑一遍装配之后,技能没动的 build 放行,技能被改了的 build 拒跑。
# 引擎用一份技能脚本的拷贝跑,这样可以改它而不碰真的技能。
skill_copy="$TMP/skill-copy"
rm -rf "$skill_copy"
cp -R "$SCRIPT_DIR/../../skills/exe-release/scripts" "$skill_copy"
find "$skill_copy" -name __pycache__ -prune -exec rm -rf {} +
RFC="$skill_copy/release-flow.sh"
assembled_loop() {
  bash "$RFC" abort >/dev/null 2>&1 || true
  bash "$RFC" init --manifest "$SCRIPT_DIR/fixtures/release-assembler/v2.adapter.json" >/dev/null
  bash "$RFC" stage done --stage verify_key >/dev/null
  bash "$RFC" stage run --stage assemble >/dev/null
}
build_with_copy() {
  PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
    RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" \
    bash "$RFC" stage run --stage build
}
remote_reset
assembled_loop
if build_with_copy >/dev/null 2>&1; then
  [ "$(build_status)" = "done" ] && ok "装配之后技能没动过,build 放行" || no "技能没动过 build 却没完成"
else
  no "技能没动过,装配之后的 build 被拒了"
fi
remote_reset
assembled_loop
printf '\n# edited after assemble\n' >> "$skill_copy/release_contracts.py"
if build_with_copy >/dev/null 2>&1; then
  no "技能在装配之后被改过,build 却放行了"
else
  [ "$(jq -r '.current_stage' "$SF")" = "assemble" ] \
    && ok "技能在装配之后被改过,build 拒跑并回到 assemble" || no "没有回到 assemble ($(jq -r '.current_stage' "$SF"))"
fi
bash "$RFC" abort >/dev/null

# 守:上一轮的 attempt 目录不能留。attempt 号从 a0 重新数,旧目录跟本轮同名对撞,于是
# 「本轮的 a0-build」读到的是上一个产品的结果,而没有任何一步报错。
remote_reset
mkdir -p "$(dirname "$SF")/release-artifacts/a0-build"
printf '别的产品的结果\n' > "$(dirname "$SF")/release-artifacts/a0-build/build.findings.json"
init_for_remote_build
[ ! -e "$(dirname "$SF")/release-artifacts/a0-build/build.findings.json" ] \
  && ok "init 不继承上一轮的 attempt 目录" || no "上一轮的 attempt 目录跟本轮同名对撞"
bash "$RF" abort >/dev/null

# 守:重跑同一个 commit 时,若不清上一轮的退出码,第一次轮询就会读到上轮的 0,把仍在跑
# 或已失败的本轮判成成功——错的包会被当成好包发出去。
remote_reset
init_for_remote_build
stale="$FAKE_REMOTE_ROOT/release-input/test-product"
mkdir -p "$stale"
printf '0\n' > "$stale/build-run.exitcode"
printf '上一轮的日志\n' > "$stale/build-run.log"
export FAKE_BUILD_OUTCOME=fail:3
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "本轮失败不被上一轮的退出码盖成成功" || no "读到过期退出码误判成功"
bash "$RF" abort >/dev/null

# 守:清不掉旧产物还往下走,等于拿上一轮的结果当本轮的。
remote_reset
export FAKE_REMOVE_FAILS=1
init_for_remote_build
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "清不掉旧产物就不开工" || no "清理失败仍判 done"
[ "$(task_count)" = "0" ] && ok "清不掉旧产物时不建计划任务" || no "清理失败仍建了任务"
bash "$RF" abort >/dev/null

# 守:构建卡死时若不结束任务,孤儿构建会抢写下一轮同 commit 的退出码。
remote_reset
export FAKE_BUILD_OUTCOME=hang
init_for_remote_build
PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 RELEASE_REMOTE_BUILD_TIMEOUT_SECONDS=0 \
  RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" \
  bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "构建超时不判 done" || no "超时误判 done"
[ "$(task_count)" = "0" ] && ok "构建超时清掉计划任务" || no "超时留下孤儿任务"
bash "$RF" abort >/dev/null

# 守:启动命令偶发「返回 0 但任务没起来」,已建的任务必须清掉,否则同样留孤儿。
remote_reset
export FAKE_RUN_FAILS=1
init_for_remote_build
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "任务起不来不判 done" || no "起不来仍判 done"
[ "$(task_count)" = "0" ] && ok "任务起不来也清掉已建的任务" || no "起不来留下孤儿任务"
bash "$RF" abort >/dev/null

# 守:退出码文件损坏时判不出成败,同样要清干净再交人。
remote_reset
export FAKE_BUILD_OUTCOME=garbage
init_for_remote_build
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "退出码非法不判 done" || no "退出码非法仍判 done"
[ "$(task_count)" = "0" ] && ok "退出码非法也清掉计划任务" || no "退出码非法留下孤儿任务"
bash "$RF" abort >/dev/null

# 守:远端路径里的空格与引号会打断 PowerShell 字符串或触发变量展开,而跨三个解析器
# 没有统一的引号合同。这类根路径必须在碰构建机之前就被拒。
for bad_root in "C:/release input" "C:/release'input" 'C:/release$input'; do
  remote_reset
  init_for_remote_build
  remote_build "$bad_root" >/dev/null 2>&1 || true
  [ "$(build_status)" != "done" ] && ok "危险远端根被拒($bad_root)" || no "危险远端根未被拒($bad_root)"
  [ -z "$(ls -A "$FAKE_REMOTE_ROOT")" ] && ok "危险远端根没碰到构建机($bad_root)" || no "危险远端根已在构建机落地($bad_root)"
  bash "$RF" abort >/dev/null
done

# 守:产品名是裸拼进远端路径的(<根>/<产品>),所以它也要在碰构建机之前过字符白名单。
for bad_product in "a b" "../escape" 'a$b'; do
  remote_reset
  init_for_remote_build
  jq -nc --arg p "$bad_product" '{repo_root:"/placeholder",product:$p}' > "$LOOP_DIR/release-context.json"
  remote_build >/dev/null 2>&1 || true
  [ "$(build_status)" != "done" ] && [ -z "$(ls -A "$FAKE_REMOTE_ROOT")" ] \
    && ok "危险的产品名被拒,没碰到构建机($bad_product)" || no "危险的产品名没被拦在构建机之外($bad_product)"
  bash "$RF" abort >/dev/null
done

# 守:失败根因只存在于构建机的日志里。不回传,Mac 侧永远诊断不出 finding,自愈闭环断掉。
# 回传的那份日志要交到诊断器手里(RELEASE_BUILD_LOG),回执也要给出它的位置。
remote_reset
export FAKE_BUILD_OUTCOME=fail:7
jq --arg d "$TMP/diagnose-dump.sh" '.stages=[] | .diagnose=[$d]' "$FIX/manifest.fake.json" > remote-dump-manifest.json
bash "$RF" abort >/dev/null 2>&1 || true
bash "$RF" init --manifest remote-dump-manifest.json >/dev/null
bash "$RF" stage done --stage verify_key >/dev/null
bash "$RF" stage done --stage assemble >/dev/null
seed_loop_pair
rm -f "$TMP/diagnose.env"
remote_build >/dev/null 2>&1 || true
[ "$(diag_line 1)" = "build" ] && ok "远端构建失败时 RELEASE_FAILED_STAGE 是 build" || no "RELEASE_FAILED_STAGE ($(diag_line 1))"
grep -q "fake build log" "$(diag_line 3)" 2>/dev/null \
  && ok "回传的构建机日志交给了诊断器(RELEASE_BUILD_LOG)" || no "RELEASE_BUILD_LOG ($(diag_line 3))"
bash "$RF" receipt > "$TMP/receipt.out"
log_ref="$(jq -r '[.attempt_ledger[].log_refs[]?] | first // empty' "$SF")"
[ -n "$log_ref" ] && grep -qF "$log_ref" "$TMP/receipt.out" \
  && ok "回执给出日志位置(自主处置的入口)" || no "回执没有日志位置 (log_ref=$log_ref)"
bash "$RF" abort >/dev/null
unset FAKE_BUILD_OUTCOME FAKE_RUN_FAILS FAKE_REMOVE_FAILS
bash "$RF" abort >/dev/null

# 守:构建机是哪一台,不能只活在人的记忆里。两个值都缺时出包停在这一步等人补,
# 而钥匙旁边放一份 remote-build.json 就没人需要记它。
for input in missing_host missing_root invalid_root; do
  remote_reset
  init_for_remote_build
  host="" root=""
  case "$input" in
    missing_host) fingerprint=env:missing_RELEASE_REMOTE_HOST ;;
    missing_root) host="fake@pc"; fingerprint=env:missing_RELEASE_REMOTE_ROOT ;;
    invalid_root) host="fake@pc"; root="relative/path"; fingerprint=env:invalid_RELEASE_REMOTE_ROOT ;;
  esac
  PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
    RELEASE_REMOTE_HOST="$host" RELEASE_REMOTE_ROOT="$root" \
    bash "$RF" stage run --stage build >/dev/null 2>&1 || true
  log="$(find .release/release-artifacts -name 'build.log' -print)"
  rc=0
  RELEASE_FAILED_STAGE=build RELEASE_BUILD_LOG= RELEASE_STAGE_LOG="$log" \
    python3 "$(dirname "$RF")/diagnose_core.py" --adapter remote-build-manifest.json \
      > "$TMP/settings-findings.json" || rc=$?
  if [ "$rc" -eq 1 ] && jq -e --arg fp "$fingerprint" \
    '[.findings[].root_cause_fingerprint] == [$fp]' "$TMP/settings-findings.json" >/dev/null; then
    ok "build stage diagnostic: $fingerprint"
  else
    no "build stage diagnostic did not report $fingerprint"
  fi
  bash "$RF" abort >/dev/null
done

printf '{"host":"fake@pc","root":"C:/from-file","cache_root":"D:/file-cache","delivery_root":"D:/file-delivered","build_env":{"UV_INDEX_URL":"https://mirror.invalid/simple"}}\n' > remote-build.json
remote_reset
init_for_remote_build
PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
  bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(build_status)" = "done" ] && ok "只有 remote-build.json 也能出包" || no "读不到 remote-build.json"
case "$(build_dir)" in
  */from-file/*) ok "构建落在文件里写的远端根" ;;
  *) no "远端根不是文件里那个($(build_dir))" ;;
esac
# new-product.md 写给操作员的三项:文件里的 cache_root 与 build_env 跟着 context 上构建机。
[ "$(jq -r '.cache_root' "$(build_dir)/release-context.json" 2>/dev/null)" = "D:/file-cache" ] \
  && ok "remote-build.json 的 cache_root 生效" || no "文件里的 cache_root 没生效"
[ "$(jq -r '.build_env.UV_INDEX_URL' "$(build_dir)/release-context.json" 2>/dev/null)" = "https://mirror.invalid/simple" ] \
  && ok "remote-build.json 的 build_env 跟着 context 上了构建机" || no "文件里的 build_env 没上构建机"
bash "$RF" abort >/dev/null

# 安装包收拢到哪,环境变量压过文件,文件压过「<根>-delivered」的推断。
for delivery_case in "file:" "env:D:/env-delivered"; do
  remote_reset
  init_for_remote_build
  printf '{"repo_root":"/placeholder","product":"test-product","build_target":{"installer_glob":"out/*-setup.exe"}}\n' \
    > "$LOOP_DIR/release-context.json"
  case "$delivery_case" in
    env:*) RELEASE_DELIVERY_ROOT="${delivery_case#env:}" remote_build >/dev/null 2>&1 || true; expected_dir="env-delivered" ;;
    *) remote_build >/dev/null 2>&1 || true; expected_dir="file-delivered" ;;
  esac
  [ -n "$(find "$FAKE_REMOTE_ROOT/$expected_dir" -name '*-setup.exe' 2>/dev/null)" ] \
    && ok "安装包收进 $expected_dir" || no "安装包没收进 $expected_dir"
  bash "$RF" abort >/dev/null
done

# 守:环境变量必须压过文件——临时换一台构建机只有这一个手段,测试也靠它灌假值。
remote_reset
init_for_remote_build
remote_build "C:/from-env" >/dev/null 2>&1 || true
case "$(build_dir)" in
  */from-env/*) ok "环境变量压过 remote-build.json" ;;
  *) no "文件盖掉了环境变量($(build_dir))" ;;
esac
bash "$RF" abort >/dev/null
rm -f remote-build.json

# 守:--max-rounds N 就是整整 N 轮:第 N 轮结束时还没收敛才熔断,不是提前一轮,也不是多放一轮。
bash "$RF" init --manifest "$FIX/manifest.fake.json" --max-rounds 2 >/dev/null
out="$(bash "$RF" round next)"
case "$out" in
  ROUND=2/2) ok "没到上限的 round next 照常计数" ;;
  *) no "round next 计数 ($out)" ;;
esac
out="$(bash "$RF" round next)"
case "$out" in
  ROUND-CAP:max=2*) ok "round 越 cap 熔断" ;;
  *) no "round cap ($out)" ;;
esac
[ "$(bash "$RF" where)" = "PAUSED:needs-redirection" ] && ok "熔断后 where PAUSED" || no "PAUSED ($(bash "$RF" where))"
[ "$(rc_of bash "$RF" where)" = "0" ] && ok "where 报 PAUSED 时退 0" || no "where PAUSED 退出码"
[ "$(jq -r '.pause.at_stage' "$SF")" = "doctor" ] && ok "熔断的 pause 点名停在哪个 stage" || no "熔断 pause 的 at_stage ($(jq -r '.pause.at_stage' "$SF"))"
# 守:resume 解除暂停。没有失败的 stage 时(像这里的轮次熔断)也一样——不然驱动永远停在 PAUSED。
bash "$RF" resume >/dev/null
[ "$(jq -r '.pause' "$SF")" = "null" ] && [ "$(bash "$RF" where)" = "STAGE:doctor RUN:true" ] \
  && ok "没有失败 stage 时 resume 也解除暂停" || no "resume 没解除暂停 ($(bash "$RF" where))"
bash "$RF" abort >/dev/null

# 守:surface 把一段暂停写进状态,where 读得到,receipt 把问题原样交出来。
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
if bash "$RF" surface --kind no-such-kind --question q >/dev/null 2>&1; then
  no "surface 收了不认识的 kind"
else
  ok "surface 拒绝不认识的 kind"
fi
bash "$RF" surface --kind needs-context --question "which build machine?" --at-stage doctor >/dev/null
surface_receipt="$(bash "$RF" receipt)"
[ "$(bash "$RF" where)" = "PAUSED:needs-context" ] && [[ "$surface_receipt" == *"which build machine?"* ]] \
  && ok "surface 的暂停被 where 与 receipt 读到" || no "surface 没落进状态 ($(bash "$RF" where))"
# 守:每个 stage 都做完了、但还停在一个没回答的问题上,这一轮也不算出包:close 要拒绝,不写交付记录。
for paused_stage in doctor smoke verify_key assemble build; do bash "$RF" stage done --stage "$paused_stage" >/dev/null; done
if bash "$RF" close >/dev/null 2>&1; then
  no "停在暂停上的一轮 close 竟放行"
else
  [ -f "$SF" ] && [ ! -e ".release/delivered/fixture-product.json" ] \
    && ok "停在暂停上的一轮 close 被拒,状态与交付记录都不动" || no "close 被拒却改了状态或写了记录"
fi

# 守:状态文件坏了就停,并且原样留着,不再往下写。write 不接受空输出或非法 JSON,
# 否则一次失败的 jq 会把唯一的现场截成 0 字节。
printf 'not json' > "$SF"
if bash "$RF" resume 2>/dev/null; then
  no "corrupt 上 resume 应退非零"
else
  ok "corrupt 上 resume 退非零"
fi
if bash "$RF" surface --kind needs-context --question q 2>/dev/null; then
  no "corrupt 上 surface 应退非零"
else
  ok "corrupt 上写状态退非零"
fi
if bash "$RF" close >/dev/null 2>&1; then
  no "corrupt 上 close 应退非零"
else
  ok "corrupt 上 close 退非零"
fi
if bash "$RF" stage run >/dev/null 2>&1; then
  no "corrupt 上 stage run 应退非零"
else
  ok "corrupt 上 stage run 退非零,不跑任何 stage"
fi
[ "$(cat "$SF")" = "not json" ] && [ ! -e ".release/delivered/fixture-product.json" ] \
  && ok "写失败后原文件保留(不截 0 字节),close 不在坏状态上写交付记录" || no "文件被截断或写了交付记录"
case "$(bash "$RF" where)" in
  CORRUPT:*) ok "corrupt -> where CORRUPT(fail-closed)" ;;
  *) no "CORRUPT 读" ;;
esac
[ "$(rc_of bash "$RF" where)" = "0" ] && ok "where 报 CORRUPT 时退 0" || no "where CORRUPT 退出码"
# driving.md 让 CORRUPT 时去读 receipt:它得自己说出 CORRUPT,而不是在坏文件上报错退出。
case "$(bash "$RF" receipt 2>&1)" in
  CORRUPT:*) ok "corrupt 时 receipt 说 CORRUPT" ;;
  *) no "corrupt 时 receipt ($(bash "$RF" receipt 2>&1))" ;;
esac

# 回归:进程在 stage 标 running 后中断,where 必须报 STAGE 让该 stage 重跑,不跳下一个、不报 SUCCESS。
bash "$RF" abort >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
jq '(.stages[0].status)="running"' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
case "$(bash "$RF" where)" in
  STAGE:doctor*) ok "where 认 running:中断 stage 重跑不跳步" ;;
  *) no "where 忽略 running ($(bash "$RF" where))" ;;
esac
jq '(.stages |= map(.status="done")) | (.stages[-1].status)="running"' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
case "$(bash "$RF" where)" in
  STAGE:build*) ok "where 认 running:只剩它没做完时也不误报 SUCCESS" ;;
  *) no "running 是最后一段时误报 ($(bash "$RF" where))" ;;
esac

# 回归:stage done 只是人工确认位,拒绝跳步把从未执行的 stage 标 done(伪造 close 眼中的 DONE)。
bash "$RF" abort >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
if bash "$RF" stage done --stage build 2>/dev/null; then
  no "stage done 跳步应被拒绝"
else
  ok "stage done 拒绝跳步标 done"
fi
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" = "pending" ] && ok "被拒后 build 仍 pending" || no "被拒后状态被改"

# 回归:transient 指纹不派修,直接重置该 stage 重跑;同指纹熔断兜底防无限重试。
bash "$RF" abort >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.transient.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.transient.json")"
case "$out" in
  TRANSIENT-RETRY:doctor*) ok "transient 指纹直接重跑不派修" ;;
  *) no "transient dispatch ($out)" ;;
esac
[ "$(jq -r '.stages[0].status' "$SF")" = "pending" ] && ok "transient 后 stage 重置 pending" || no "transient 未重置 stage"
[ "$(jq -r '.pause' "$SF")" = "null" ] && ok "transient 不 PAUSE" || no "transient 竟 PAUSE"
[ "$(jq -r '.budget.fix_rounds' "$SF")" = "0" ] && ok "transient 不消耗 fix_rounds" || no "transient 误耗 fix_rounds"

# 回归:预算按 fix_rounds 熔断,不按动作数;达 max 后 dispatch 熔断交人。
jq '.budget.fix_rounds = .budget.max_fix_rounds' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.p2.json")"
case "$out" in
  BUDGET-EXCEEDED:fix_rounds=*) ok "fix_rounds 达 max 熔断交人" ;;
  *) no "fix_rounds 熔断 ($out)" ;;
esac

bash "$RF" abort >/dev/null

# 回归:env: 指纹是环境处置,不派修。停在 needs-context 的 .pause 上,question 就是这条
# finding 的 remediation;跑出包流程的那个 agent 做完那件事自己 resume。
env_head_before="$(git rev-parse HEAD)"
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.env.json" >/dev/null
out="$(bash "$RF" dispatch --stage doctor --findings "$FIX/finding.env.json")"
case "$out" in
  ENV-ACTION:doctor*) ok "env: 指纹印环境处置回执" ;;
  *) no "env: dispatch ($out)" ;;
esac
[ "$(jq -r '.pause.reason // ""' "$SF")" = "needs-context" ] \
  && ok "env: 停在 needs-context 的 .pause 上" || no "env: pause=$(jq -c '.pause' "$SF")"
[ "$(jq -r '.pause.question // ""' "$SF")" = "$(jq -r '.findings[0].remediation' "$FIX/finding.env.json")" ] \
  && ok "env: question 就是这条 finding 的 remediation" || no "env: question=$(jq -r '.pause.question // ""' "$SF")"
[ "$(git rev-parse HEAD)" = "$env_head_before" ] && ok "env: 没有自动修复提交" || no "env: 竟产生了修复提交"
jq -s -e 'any(.[]; .event == "paused" and .stage == "doctor" and .fingerprint == "env:active_product_process:duck")' events.jsonl >/dev/null 2>&1 \
  && ok "env: 停下时事件流里留一条 paused" || no "env: 没有 paused 事件"
bash "$RF" abort >/dev/null

# ── 放弃这一轮 ──────────────────────────────────────────────────────────────
#
# 守:abort 不写交付记录。close 无条件写那一份,它说的是「这个产品在这个 commit 上出过包」;
# 中途换产品、放弃重来时用 close,写下的就是一个根本不存在的包,而且盖掉上一次真实的记录——
# 第 4 步的同 commit 校验读的正是它。真发生过:一轮构建被环境挡下,要换另一个产品先出,
# 当时没有这条命令,只能手工把状态文件挪走。
remote_reset
init_for_remote_build
prev_delivered="$TMP/.release/delivered/test-product.json"
mkdir -p "$(dirname "$prev_delivered")"
printf '{"product":"test-product","source_commit":"realcommit","closed_at":"earlier"}' > "$prev_delivered"
out="$(bash "$RF" abort)"
case "$out" in
  ABORTED:*) ok "abort 收掉这一轮" ;;
  *) no "abort 输出 ($out)" ;;
esac
[ ! -f "$SF" ] && ok "abort 之后没有正在进行的一轮" || no "abort 没删活状态"
[ "$(jq -r '.source_commit' "$prev_delivered")" = "realcommit" ] \
  && ok "abort 不碰上一次真实的交付记录" || no "abort 把交付记录改了"
[ -n "$(find "$TMP/.release/release-artifacts" -name 'aborted-*.json' 2>/dev/null | head -1)" ] \
  && ok "放弃的那一轮状态留在现场" || no "abort 把现场也删了"
[ "$(bash "$RF" abort)" = "NO-LOOP" ] && ok "没有正在进行的一轮时 abort 说清楚" || no "空 abort 的输出"
rm -f "$prev_delivered"

# ── 断线重连 ────────────────────────────────────────────────────────────────
#
# 守:构建跑在那台机器的计划任务里,这一侧只是在看 exitcode 出没出现。看的人被杀掉,
# 构建照样跑完,而这一侧什么都不知道——收拢没跑,状态停在「构建中」。真发生过一次,
# 代价是一轮四十分钟的编译要靠人手工收尾。
#
# 这里模拟那个现场:远端目录里有日志、没有 exitcode(还在跑),再让引擎重新 stage run。
# 它该接上去,而不是重传源码——重传会 Remove-Item 掉正在被读写的源码树。
# 远端目录里有日志、没有 exitcode、SOURCE_COMMIT.txt 是这一轮的 commit、任务名在 build-run.task 里,
# 登记表里挂着那个任务:这就是「构建还在跑,而看它的人被杀掉了」的现场。
# 产出由假构建机在被接上的那一刻写(真实构建也可能在任何一秒结束);接上去的那条路不会
# schtasks /run,所以不能指望 /run 去写它。
# 注意 stage run 在失败被处置之后也退 0,所以判断「接上去了」要看状态与远端,不看退出码。
for attach_exit in 0 3; do
  remote_reset
  init_for_remote_build
  bd_live="$FAKE_REMOTE_ROOT/release-input/test-product"
  mkdir -p "$bd_live/source"
  printf 'building...\n' > "$bd_live/build-run.log"
  printf 'sentinel\n' > "$bd_live/source/DO-NOT-WIPE"
  git rev-parse HEAD > "$bd_live/SOURCE_COMMIT.txt"
  printf 'mmw-release-existing-task\n' > "$bd_live/build-run.task"
  printf '{"mmw-release-existing-task":{"cmd":"x","state":"running"}}' > "$FAKE_REMOTE_TASKS"
  rm -f "$FAKE_REMOTE_TASKS.history"
  FAKE_ATTACH_FINISH="$attach_exit" remote_build >/dev/null 2>&1 || true
  # 接上去就不再建第二个计划任务:假构建机一条建任务的记录都不该有。
  [ ! -s "$FAKE_REMOTE_TASKS.history" ] \
    && ok "认出远端还有一轮在跑,接上去,不另建计划任务(远端 exitcode=$attach_exit)" || no "没接上去,又建了计划任务 ($(cat "$FAKE_REMOTE_TASKS.history"))"
  if [ "$attach_exit" = 0 ]; then
    [ "$(build_status)" = "done" ] && ok "接上去的那一轮按远端的 exitcode 判成功" || no "接上去之后判定错 ($(build_status))"
  else
    [ "$(build_status)" = "failed" ] && ok "接上去的那一轮按远端的 exitcode 判失败" || no "接上去之后判定错 ($(build_status))"
  fi
  # 重传会先 Remove-Item 掉 source 再解压。这个哨兵文件只有不重传才活得下来。
  [ -f "$bd_live/source/DO-NOT-WIPE" ] \
    && ok "接上去不重传,正在被读写的源码树没被冲掉" || no "接上去时把远端源码树重传了"
  # 任务名是从远端 build-run.task 读回来的,登记表里那个任务靠它才清得掉。
  [ "$(task_count)" = "0" ] && ok "接上去的那一轮也把原来的计划任务清干净" || no "残留计划任务($(cat "$FAKE_REMOTE_TASKS"))"
  bash "$RF" abort >/dev/null
done

# 守:目录是同一个,远端还在跑的若是别的 commit,开工就会冲掉它正在读写的源码树;
# 这一轮要停下,不重传、不建任务。
remote_reset
init_for_remote_build
bd_other="$FAKE_REMOTE_ROOT/release-input/test-product"
mkdir -p "$bd_other/source"
printf 'building...\n' > "$bd_other/build-run.log"
printf 'sentinel\n' > "$bd_other/source/DO-NOT-WIPE"
printf '0123456789abcdef0123456789abcdef01234567\n' > "$bd_other/SOURCE_COMMIT.txt"
tasks_created_before="$(wc -l < "$FAKE_REMOTE_TASKS.history" 2>/dev/null || echo 0)"
other_out="$(remote_build 2>&1 || true)"
tasks_created_after="$(wc -l < "$FAKE_REMOTE_TASKS.history" 2>/dev/null || echo 0)"
other_log="$(find "$(dirname "$SF")/release-artifacts" -path '*-build/build.log' -newer "$bd_other/SOURCE_COMMIT.txt" -exec cat {} + 2>/dev/null)"
case "$other_out|$other_log" in
  *"rc=73"*"still running"*) [ "$(build_status)" != "done" ] \
    && ok "远端还在跑别的 commit 时这一轮停下并说明原因" || no "说了在跑却仍判 done" ;;
  *) no "远端还在跑别的 commit 时照样开工: $(printf '%s' "$other_out" | tail -c 300)" ;;
esac
[ -f "$bd_other/source/DO-NOT-WIPE" ] && [ "$tasks_created_after" -eq "$tasks_created_before" ] \
  && ok "不冲掉别的 commit 正在用的源码树,也不建计划任务" || no "冲掉了正在跑的那一轮或建了任务"
bash "$RF" abort >/dev/null

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
