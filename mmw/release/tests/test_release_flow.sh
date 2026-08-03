#!/usr/bin/env bash
# release-flow.sh 引擎空跑:载入 fail-loud、状态机推进、exit-check、round cap、resume、原子写。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.release}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RF="$SCRIPT_DIR/../release-flow.sh"
FIX="$SCRIPT_DIR/fixtures/release-flow"
SF="$STATE_SUBDIR/release-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_release_flow.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
cp "$SCRIPT_DIR/../../cli/mmw.default.json" .mmw.json
git config user.email t@t
git config user.name t
echo s > s
git add -A
git commit -qm s

jq 'del(.event_sink)' "$FIX/manifest.fake.json" > bad.json
if bash "$RF" init --manifest bad.json 2>/dev/null; then
  no "bad manifest 应 fail-loud"
else
  ok "bad manifest fail-loud 退非零"
fi
[ ! -f "$SF" ] && ok "fail-loud 不写 release-state" || no "fail-loud 竟写了 state"

bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
[ "$(jq -r .product "$SF")" = "duck" ] && ok "init 注入 product" || no "product ($(jq -r .product "$SF"))"
[ "$(jq -r '.stages|length' "$SF")" = "2" ] && ok "init 注入 2 stages" || no "stages len"
[ "$(jq -r '[.stages[]|select(.status=="pending")]|length' "$SF")" = "2" ] && ok "stages 全 pending" || no "pending"

[ "$(bash "$RF" where)" = "STAGE:doctor RUN:true" ] && ok "where 报首 stage+run" || no "where ($(bash "$RF" where))"
if bash "$RF" stage run --stage doctor >/dev/null; then
  [ "$(jq -r '.stages[]|select(.name=="doctor").status' "$SF")" = "done" ] && ok "stage run 真执行并标 done" || no "stage run 未标 doctor done"
  [ "$(bash "$RF" where)" = "STAGE:compile RUN:true" ] && ok "stage run 后推进到 compile" || no "推进 ($(bash "$RF" where))"
else
  no "stage run 应执行当前普通 argv"
fi
[ "$(bash "$RF" exit-check)" = "NOT-DONE:stages=compile" ] && ok "exit-check 列剩余" || no "exit-check ($(bash "$RF" exit-check))"

bash "$RF" stage "done" --stage compile >/dev/null
[ "$(bash "$RF" exit-check)" = "DONE" ] && ok "全 done -> DONE" || no "DONE ($(bash "$RF" exit-check))"
[ "$(bash "$RF" where)" = "SUCCESS:all stages done" ] && ok "where -> SUCCESS" || no "SUCCESS ($(bash "$RF" where))"

bash "$RF" close >/dev/null
mkdir -p capture-bin
cat > capture-bin/capture-argv <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$ARGV_CAPTURE"
SH
chmod +x capture-bin/capture-argv
jq '.stages=[{name:"capture",run:["capture-argv","${RELEASE_PLUGIN_DIR}"]}]' "$FIX/manifest.fake.json" > capture-manifest.json
bash "$RF" init --manifest capture-manifest.json >/dev/null
if PATH="$PWD/capture-bin:$PATH" ARGV_CAPTURE="$TMP/plugin-dir.argv" bash "$RF" stage run --stage capture >/dev/null; then
  expected_plugin_dir="$(
    CDPATH='' cd -- "$(dirname -- "$RF")"
    pwd -P
  )"
  [ "$(cat "$TMP/plugin-dir.argv")" = "$expected_plugin_dir" ] && ok "stage run 展开 RELEASE_PLUGIN_DIR 为引擎物理目录" || no "RELEASE_PLUGIN_DIR 展开错误"
else
  no "stage run 应执行 capture argv"
fi

bash "$RF" close >/dev/null
cat > diagnose-p0.sh <<SH
#!/usr/bin/env bash
cat "$FIX/finding.p0.json"
SH
chmod +x diagnose-p0.sh
jq --arg diagnose "$TMP/diagnose-p0.sh" '.stages=[{name:"broken",run:["false"]}] | .diagnose=[$diagnose]' "$FIX/manifest.fake.json" > failed-stage-manifest.json
bash "$RF" init --manifest failed-stage-manifest.json >/dev/null
if bash "$RF" stage run --stage broken >/dev/null; then
  [ "$(jq -r '.pause.reason' "$SF")" = "needs-redirection" ] && ok "普通 stage 非零自动 diagnose 并 P0 PAUSE" || no "普通 stage 非零未写 P0 PAUSE"
else
  no "普通 stage 非零应进入诊断分级而非直接退回 drive"
fi

bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
[ "$(jq -r '.source_commit' "$SF")" = "$(git rev-parse HEAD)" ] && ok "init 绑定完整 source_commit" || no "init 未绑定 source_commit"
bash "$RF" stage fail --stage doctor --findings "$FIX/finding.p1.json" >/dev/null
bash "$RF" resume >/dev/null
[ "$(jq -r '.current_stage' "$SF")" = "doctor" ] && ok "同 HEAD resume 从最早 failed stage 继续" || no "同 HEAD resume 未回到 doctor"
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "2" ] && ok "同 HEAD resume 令失败 stage 及后继 pending" || no "同 HEAD resume stage 状态错误"

bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
bash "$RF" stage "done" --stage doctor >/dev/null
echo changed > source-change
git add source-change
git commit -qm source-change
bash "$RF" resume >/dev/null
[ "$(jq -r '.source_commit' "$SF")" = "$(git rev-parse HEAD)" ] && ok "HEAD 改变后更新 source_commit" || no "HEAD 改变后 source_commit 过期"
[ "$(jq -r '.current_stage' "$SF")" = "doctor" ] && ok "HEAD 改变后从首 stage 重验" || no "HEAD 改变后未回首 stage"
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "2" ] && ok "HEAD 改变后所有 stage pending" || no "HEAD 改变后残留旧产物状态"

bash "$RF" close >/dev/null
# ── 远程构建 ────────────────────────────────────────────────────────────────
# 假构建机在 fixtures/fake-remote/：它维护一棵目录树当远端文件系统、一份登记表当
# Task Scheduler，不记录命令文本。下面每条断的都是这两样的最终状态——引擎把任务名
# 拼错、create 与 delete 用了两个名字，登记表里就会留下残骸，断言自然红。
#
# 验不了的写在 TESTING.md：上传的 wrapper 内容对不对（脱附会话里日志落不落地、
# PS 5.1 的编码转换）要一台 Windows 构建机才能验，这里只断它被上传了。
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

printf '# fake release\n' > release.ps1
printf '{"repo_root":"/placeholder","product":"test-product"}\n' > release-context.json
jq --arg script "$TMP/release.ps1" --arg context "$TMP/release-context.json" \
  '.stages=[{name:"build",run:["mmw-release-remote-build","--script",$script,"--context",$context]}]' \
  "$FIX/manifest.fake.json" > remote-build-manifest.json

# 守:构建机拿到的必须是当前 HEAD 的代码。拿错版本出的包发给客户就是错的产品。
remote_reset
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
if remote_build >/dev/null; then
  bd="$(build_dir)"
  [ "$(cat "$bd/SOURCE_COMMIT.txt" 2>/dev/null)" = "$(git rev-parse HEAD)" ] \
    && ok "构建机拿到的是当前 HEAD" || no "SOURCE_COMMIT 不是 HEAD"
  [ "$(cat "$bd/source/s" 2>/dev/null)" = "$(cat s)" ] \
    && ok "源码真的解压到构建机且内容一致" || no "远端源码内容对不上"
  for f in release.ps1 release-context.json run-release.ps1 run-release.cmd source.zip; do
    [ -s "$bd/$f" ] || { no "构建输入缺 $f"; continue; }
  done
  ok "五份构建输入都上传了"

  # 守:同一个 commit 出第二个产品时,只按 commit 命名会让后一个产品的重解压把前一个
  # 已产出的安装包整片冲掉。短 commit 是因为全 commit 会让 NSIS 的 include 路径越过
  # Windows 路径长度上限。
  case "$(basename "$bd")" in
    "$(git rev-parse HEAD | cut -c1-12)-test-product") ok "构建目录按短 commit 加产品名命名" ;;
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
bash "$RF" close >/dev/null

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

# 守:重跑同一个 commit 时,若不清上一轮的退出码,第一次轮询就会读到上轮的 0,把仍在跑
# 或已失败的本轮判成成功——错的包会被当成好包发出去。
remote_reset
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
stale="$FAKE_REMOTE_ROOT/release-input/$(git rev-parse HEAD | cut -c1-12)-test-product"
mkdir -p "$stale"
printf '0\n' > "$stale/build-run.exitcode"
printf '上一轮的日志\n' > "$stale/build-run.log"
export FAKE_BUILD_OUTCOME=fail:3
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "本轮失败不被上一轮的退出码盖成成功" || no "读到过期退出码误判成功"
bash "$RF" close >/dev/null

# 守:清不掉旧产物还往下走,等于拿上一轮的结果当本轮的。
remote_reset
export FAKE_REMOVE_FAILS=1
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "清不掉旧产物就不开工" || no "清理失败仍判 done"
[ "$(task_count)" = "0" ] && ok "清不掉旧产物时不建计划任务" || no "清理失败仍建了任务"
bash "$RF" close >/dev/null

# 守:构建卡死时若不结束任务,孤儿构建会抢写下一轮同 commit 的退出码。
remote_reset
export FAKE_BUILD_OUTCOME=hang
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 RELEASE_REMOTE_BUILD_TIMEOUT_SECONDS=0 \
  RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" \
  bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "构建超时不判 done" || no "超时误判 done"
[ "$(task_count)" = "0" ] && ok "构建超时清掉计划任务" || no "超时留下孤儿任务"
bash "$RF" close >/dev/null

# 守:启动命令偶发「返回 0 但任务没起来」,已建的任务必须清掉,否则同样留孤儿。
remote_reset
export FAKE_RUN_FAILS=1
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "任务起不来不判 done" || no "起不来仍判 done"
[ "$(task_count)" = "0" ] && ok "任务起不来也清掉已建的任务" || no "起不来留下孤儿任务"
bash "$RF" close >/dev/null

# 守:退出码文件损坏时判不出成败,同样要清干净再交人。
remote_reset
export FAKE_BUILD_OUTCOME=garbage
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "退出码非法不判 done" || no "退出码非法仍判 done"
[ "$(task_count)" = "0" ] && ok "退出码非法也清掉计划任务" || no "退出码非法留下孤儿任务"
bash "$RF" close >/dev/null

# 守:远端路径里的空格与引号会打断 PowerShell 字符串或触发变量展开,而跨三个解析器
# 没有统一的引号合同。这类根路径必须在碰构建机之前就被拒。
for bad_root in "C:/release input" "C:/release'input" 'C:/release$input'; do
  remote_reset
  bash "$RF" init --manifest remote-build-manifest.json >/dev/null
  remote_build "$bad_root" >/dev/null 2>&1 || true
  [ "$(build_status)" != "done" ] && ok "危险远端根被拒($bad_root)" || no "危险远端根未被拒($bad_root)"
  [ -z "$(ls -A "$FAKE_REMOTE_ROOT")" ] && ok "危险远端根没碰到构建机($bad_root)" || no "危险远端根已在构建机落地($bad_root)"
  bash "$RF" close >/dev/null
done

# 守:失败根因只存在于构建机的日志里。不回传,Mac 侧永远诊断不出 finding,自愈闭环断掉。
remote_reset
export FAKE_BUILD_OUTCOME=fail:7
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
remote_build >/dev/null 2>&1 || true
bash "$RF" receipt > "$TMP/receipt.out"
grep -q 'logs=' "$TMP/receipt.out" && ok "回执给出日志位置(自主处置的入口)" || no "回执没有日志位置"
bash "$RF" close >/dev/null
unset FAKE_BUILD_OUTCOME FAKE_RUN_FAILS FAKE_REMOVE_FAILS
bash "$RF" close >/dev/null

bash "$RF" init --manifest "$FIX/manifest.fake.json" --max-rounds 1 >/dev/null
out="$(bash "$RF" round next)"
case "$out" in
  ROUND-CAP:max=1*) ok "round 越 cap 熔断" ;;
  *) no "round cap ($out)" ;;
esac
[ "$(bash "$RF" exit-check)" = "PAUSED:needs-redirection" ] && ok "熔断后 exit-check PAUSED" || no "PAUSED ($(bash "$RF" exit-check))"

printf 'not json' > "$SF"
if bash "$RF" resume 2>/dev/null; then
  no "corrupt 上 resume 应退非零"
else
  ok "corrupt 上 write 拒空/非法退非零"
fi
[ "$(cat "$SF")" = "not json" ] && ok "write 拒后原文件保留(不截 0 字节)" || no "文件被截断"
case "$(bash "$RF" exit-check)" in
  CORRUPT:*) ok "corrupt -> exit-check CORRUPT(fail-closed)" ;;
  *) no "CORRUPT 读" ;;
esac

# 回归:进程在 stage 标 running 后中断,where 必须报该 stage 重跑,不跳下一个、不报 SUCCESS。
bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
jq '(.stages[0].status)="running"' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
case "$(bash "$RF" where)" in
  RETRY-STAGE:doctor*) ok "where 认 running:中断 stage 重跑不跳步" ;;
  *) no "where 忽略 running ($(bash "$RF" where))" ;;
esac
jq '(.stages[0].status)="running" | (.stages[1].status)="done"' "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"
case "$(bash "$RF" where)" in
  RETRY-STAGE:doctor*) ok "where 认 running:无 pending 也不误报 SUCCESS" ;;
  *) no "running+无 pending 误报 ($(bash "$RF" where))" ;;
esac

# 回归:stage done 只是人工确认位,拒绝跳步把从未执行的 stage 标 done(伪造 exit-check DONE)。
bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
if bash "$RF" stage "done" --stage compile 2>/dev/null; then
  no "stage done 跳步应被拒绝"
else
  ok "stage done 拒绝跳步标 done"
fi
[ "$(jq -r '.stages[] | select(.name=="compile") | .status' "$SF")" = "pending" ] && ok "被拒后 compile 仍 pending" || no "被拒后状态被改"

# 回归:transient 指纹不派修,直接重置该 stage 重跑;同指纹熔断兜底防无限重试。
bash "$RF" close >/dev/null
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

bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
[ "$(bash "$SCRIPT_DIR/../../cli/mmw" release where)" = "STAGE:doctor RUN:true" ] && ok "mmw release 路由到引擎" || no "mmw 路由"

# 守:一次改动影响多个产品时,后一个产品的自愈修复会推进 HEAD,早前那个产品的包就不是
# 最终代码了。混着不同 commit 的包发给客户,他们装到的是两份不同的东西。收束时留下的
# 交付记录是发出去之前唯一能发现这件事的地方——判断归技能,引擎只负责把事实留下。
bash "$RF" close >/dev/null 2>&1 || true
rm -rf "$STATE_SUBDIR/delivered"
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
closed_at_commit="$(git rev-parse HEAD)"
bash "$RF" close >/dev/null
[ "$(jq -r '.product' "$STATE_SUBDIR/delivered/duck.json" 2>/dev/null)" = "duck" ] \
  && ok "收束留下这个产品的交付记录" || no "收束没留交付记录"
[ "$(jq -r '.source_commit' "$STATE_SUBDIR/delivered/duck.json" 2>/dev/null)" = "$closed_at_commit" ] \
  && ok "交付记录钉住出包时的 commit" || no "交付记录的 commit 不对"
[ ! -f "$SF" ] && ok "收束后不留活状态" || no "收束后仍有活状态"

# 守:交付记录要落主仓库根,不能落当前这棵任务 worktree。它比对的是几次出包之间的
# commit,跨任务才成立,而任务 worktree 收尾就删——落在树里的记录活不过一次任务,
# 下次出另一个产品时看不到早前那个包基于哪个提交,混包正是它要防的。
git worktree add -q wt -b task-y
(cd wt && bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null && bash "$RF" close >/dev/null)
[ -f "$STATE_SUBDIR/delivered/duck.json" ] \
  && ok "在 worktree 里收束，交付记录落主仓库根" || no "交付记录没落主仓库根"
[ ! -e "wt/$STATE_SUBDIR/delivered" ] \
  && ok "worktree 里不留交付记录" || no "worktree 里留了交付记录"

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
