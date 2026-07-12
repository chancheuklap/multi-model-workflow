#!/usr/bin/env bash
# release-flow.sh 引擎空跑:载入 fail-loud、状态机推进、exit-check、round cap、resume、原子写。
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

echo "=== test_release_flow.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q
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

real_mktemp="$(command -v mktemp)"
mkdir -p fakebin
cat > fakebin/mktemp <<SH
#!/usr/bin/env bash
case "\${1:-}" in
  */.tmp*) exec "$real_mktemp" "\$@" ;;
  *) echo "mktemp called without state-dir template" >&2; exit 42 ;;
esac
SH
chmod +x fakebin/mktemp
if PATH="$PWD/fakebin:$PATH" bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null; then
  ok "state write 使用同目录 tmp"
else
  no "state write 未使用同目录 tmp"
fi
jq -e . "$SF" >/dev/null && ok "同目录 tmp 写出合法 state" || no "同目录 tmp state 非法"
bash "$RF" close >/dev/null
rm -rf fakebin

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

[ "$(bash "$RF" where)" = "STAGE:compile RUN:true" ] && ok "kill 后 where 续跑不重报 doctor" || no "resume"

bash "$RF" stage done --stage compile >/dev/null
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
    CDPATH= cd -- "$(dirname -- "$RF")"
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
bash "$RF" stage done --stage doctor >/dev/null
echo changed > source-change
git add source-change
git commit -qm source-change
bash "$RF" resume >/dev/null
[ "$(jq -r '.source_commit' "$SF")" = "$(git rev-parse HEAD)" ] && ok "HEAD 改变后更新 source_commit" || no "HEAD 改变后 source_commit 过期"
[ "$(jq -r '.current_stage' "$SF")" = "doctor" ] && ok "HEAD 改变后从首 stage 重验" || no "HEAD 改变后未回首 stage"
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "2" ] && ok "HEAD 改变后所有 stage pending" || no "HEAD 改变后残留旧产物状态"

bash "$RF" close >/dev/null
mkdir -p remote-bin "$TMP/fake-remote"
cat > remote-bin/scp <<'SH'
#!/usr/bin/env bash
printf 'scp %s\n' "$*" >> "$TRANSPORT_CALLS"
cp "$1" "$FAKE_REMOTE/$(basename "$1")"
SH
cat > remote-bin/ssh <<'SH'
#!/usr/bin/env bash
printf 'ssh %s\n' "$*" >> "$TRANSPORT_CALLS"
case "$*" in
  *Test-Path*) printf 'Y\n' ;;
  *Get-Content*) printf '%s\n' "${FAKE_REMOTE_EXIT:-0}" ;;
esac
SH
chmod +x remote-bin/scp remote-bin/ssh
printf '# fake release\n' > release.ps1
printf '{"repo_root":"/placeholder"}\n' > release-context.json
jq --arg script "$TMP/release.ps1" --arg context "$TMP/release-context.json" '.stages=[{name:"build",run:["mmw-release-remote-build","--script",$script,"--context",$context]}]' "$FIX/manifest.fake.json" > remote-build-manifest.json
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
if PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" bash "$RF" stage run --stage build >/dev/null; then
  grep -q '^scp ' "$TMP/transport.calls" && ok "remote build 上传 archive 与输入" || no "remote build 未调用 scp"
  grep -q 'schtasks /create' "$TMP/transport.calls" && ok "remote build 创建 schtasks" || no "remote build 未创建 schtasks"
  # 远端 DefaultShell 是 cmd.exe:一切 PowerShell 维护命令必须显式经 powershell -Command。
  grep -q 'powershell -NoProfile -NonInteractive -Command.*New-Item' "$TMP/transport.calls" && ok "远端维护命令显式包 powershell(不裸跑 cmdlet)" || no "远端命令未包 powershell,cmd 下 New-Item 必炸"
  # cwd 合同 + exitcode 落地合同都在上传的 wrapper 内:release.ps1 的 throw 是 terminating
  # error,靠 -Command 串分号写 exitcode 会被中止;wrapper 用 try/catch/finally 保证必落地。
  if [ -f "$TMP/fake-remote/run-release.ps1" ] \
    && grep -q 'ReleaseContextPath' "$TMP/fake-remote/run-release.ps1" \
    && grep -q 'finally' "$TMP/fake-remote/run-release.ps1" \
    && grep -q 'build-run.exitcode' "$TMP/fake-remote/run-release.ps1"; then
    ok "remote build 上传 wrapper(显式上下文 + finally 落 exitcode)"
  else
    no "remote build wrapper 缺失或未保证 exitcode 落地"
  fi
  # Windows PowerShell 5.1 裸重定向写 UTF-16LE,Mac 侧按 UTF-8 翻译会全灭:wrapper 必须显式编码。
  if grep -q 'Out-File.*-Encoding utf8' "$TMP/fake-remote/run-release.ps1" \
    && grep -q 'Add-Content -Encoding UTF8' "$TMP/fake-remote/run-release.ps1" \
    && grep -q 'Set-Content.*-Encoding ascii' "$TMP/fake-remote/run-release.ps1"; then
    ok "wrapper 显式 UTF-8 写日志 / ascii 写 exitcode(不写 UTF-16LE)"
  else
    no "wrapper 未显式声明编码,PS5.1 裸重定向会写 UTF-16LE"
  fi
  grep -q 'File .*run-release.ps1' "$TMP/transport.calls" && ok "schtasks /tr 只指 wrapper 文件(不串多语句)" || no "schtasks /tr 仍串多语句"
  # 引号合同:create/run 走 cmd.exe、任务命令行走 powershell native CLI,单引号在两处都是字面
  # 字符——带引号则清理找不到任务、-File 找的是假路径。断 /tn 全链一致且不带引号。
  if grep -q "/tn '" "$TMP/transport.calls" || grep -q "File '" "$TMP/transport.calls"; then
    no "schtasks 任务名或 /tr 路径带单引号(cmd/native CLI 会当字面字符)"
  else
    ok "schtasks 任务名与 wrapper 路径裸传(无跨 shell 引号歧义)"
  fi
  [ "$(grep -o '/tn [^ ]*' "$TMP/transport.calls" | sort -u | wc -l | tr -d ' ')" = "1" ] && ok "create/run/清理引用同一任务名" || no "任务名跨命令不一致,清理会找不到任务"
  grep -q 'schtasks /run' "$TMP/transport.calls" && ok "remote build 启动 schtasks" || no "remote build 未启动 schtasks"
  [ "$(cat "$TMP/fake-remote/SOURCE_COMMIT.txt")" = "$(git rev-parse HEAD)" ] && ok "remote build 绑定完整 SourceCommit" || no "remote build SourceCommit 错误"
  [ -s "$TMP/fake-remote/source.zip" ] && ok "remote build 上传 git archive HEAD" || no "remote build 缺 source archive"
  jq -e 'any(.attempt_ledger[]; any(.log_refs[]; startswith("pc:")))' "$SF" >/dev/null && ok "remote build 记录远端日志引用" || no "remote build 未记录远端日志引用"
else
  no "remote build exit=0 应完成 stage"
fi

bash "$RF" close >/dev/null

# 回归 F3:真实构建耗时分钟级 + remote_input 只按 commit 命名。harness 必须清掉上一轮
# build-run.{log,exitcode} 再跑,并轮询等待本轮 exitcode 出现,不是 3 次即弃、也不信过期产物。
cat > remote-bin/ssh <<'SH'
#!/usr/bin/env bash
printf 'ssh %s\n' "$*" >> "$TRANSPORT_CALLS"
case "$*" in
  *Test-Path*)
    n=$(( $(cat "$POLL_COUNTER" 2>/dev/null || echo 0) + 1 ))
    printf '%s' "$n" > "$POLL_COUNTER"
    if [ "$n" -ge 3 ]; then printf 'Y\n'; else printf 'N\n'; fi
    ;;
  *Get-Content*) printf '0\n' ;;
esac
SH
chmod +x remote-bin/ssh
: > "$TMP/transport.calls"
printf '0' > "$TMP/poll-counter"
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
if PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" \
   POLL_COUNTER="$TMP/poll-counter" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
   RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" bash "$RF" stage run --stage build >/dev/null; then
  grep -q 'Remove-Item' "$TMP/transport.calls" && ok "remote build 开跑前清旧 build-run 产物(不信过期 exitcode)" || no "remote build 未清旧产物"
  [ "$(grep -c 'Test-Path' "$TMP/transport.calls")" -ge 3 ] && ok "remote build 轮询等待本轮构建完成(非 3 次即弃)" || no "remote build 未等待构建"
else
  no "remote build 等待完成后 exit=0 应完成 stage"
fi
bash "$RF" close >/dev/null

# 回归 C3:构建超时(exitcode 永不出现)必须 fail 且清理计划任务,不遗留孤儿构建/任务。
# exitcode 从不出现 → 墙钟超时(TIMEOUT=0 立即触发,poll=0 不影响墙钟)→ 走 schtasks /end+/delete。
cat > remote-bin/ssh <<'SH'
#!/usr/bin/env bash
printf 'ssh %s\n' "$*" >> "$TRANSPORT_CALLS"
case "$*" in
  *Test-Path*) printf 'N\n' ;;
esac
SH
chmod +x remote-bin/ssh
: > "$TMP/transport.calls"
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
# stage run 遇构建失败会诊断+PAUSE(返回 0,非命令失败),故不门控退出码;清理在 _run_remote_build
# 内返回 70 前发生,直接查 transport.calls。schtasks /end 只在超时清理路径出现,是超时的确证。
PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" \
   RELEASE_REMOTE_BUILD_POLL_SECONDS=0 RELEASE_REMOTE_BUILD_TIMEOUT_SECONDS=0 \
   RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" bash "$RF" stage run --stage build >/dev/null 2>&1 || true
grep -q 'schtasks /end' "$TMP/transport.calls" && ok "remote build 超时结束在跑的构建(schtasks /end)" || no "remote build 超时未 end 任务"
grep -q 'schtasks /delete' "$TMP/transport.calls" && ok "remote build 超时删计划任务(不遗留孤儿)" || no "remote build 超时未删任务"
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" != "done" ] && ok "remote build 超时不判 stage done" || no "remote build 超时误判 done"
# PAUSED:needs-context 的自主处置第一步是从回执拿日志 locator——receipt 漏印 log_refs,
# 驱动 Agent 只能翻裸 state 猜路径。
bash "$RF" receipt > "$TMP/receipt.out"
grep -q 'logs=' "$TMP/receipt.out" && ok "receipt 输出 attempt 的 log_refs(自主处置有日志入口)" || no "receipt 未输出 log_refs"
bash "$RF" close >/dev/null

# 清不掉远端旧 build-run 产物必须 fail-loud:旧 exitcode 留场会把仍在跑/已失败的本轮误判成功。
cat > remote-bin/ssh <<'SH'
#!/usr/bin/env bash
printf 'ssh %s\n' "$*" >> "$TRANSPORT_CALLS"
case "$*" in
  *Remove-Item*) exit 1 ;;
  *Test-Path*) printf 'Y\n' ;;
  *Get-Content*) printf '0\n' ;;
esac
SH
chmod +x remote-bin/ssh
: > "$TMP/transport.calls"
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" \
   RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
   RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" != "done" ] && ok "旧产物清除失败不继续构建(防过期 exitcode 伪成功)" || no "旧产物清除失败仍误判 done"
grep -q 'schtasks /create' "$TMP/transport.calls" && no "旧产物清除失败仍创建了计划任务" || ok "旧产物清除失败不创建计划任务"
bash "$RF" close >/dev/null

# 远端根路径含空格直接拒:跨 cmd/PowerShell/native CLI 三解析器的引号没有统一合同。
: > "$TMP/transport.calls"
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" \
   RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release input" bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" != "done" ] && ok "RELEASE_REMOTE_ROOT 含空格被拒(引号无稳定合同)" || no "含空格远端根未被拒"
grep -q 'schtasks /create' "$TMP/transport.calls" && no "含空格远端根仍创建了计划任务" || ok "含空格远端根未触达 schtasks"
bash "$RF" close >/dev/null

# 回归 I1:schtasks /run 起不来(任务已 /create)时,尾部统一清理必须删掉已建的计划任务。
# 上轮只在超时分支清理,漏了 /run 失败这个出口;这里断言现在所有出口都统一走 /delete。
cat > remote-bin/ssh <<'SH'
#!/usr/bin/env bash
printf 'ssh %s\n' "$*" >> "$TRANSPORT_CALLS"
case "$*" in
  *"schtasks /run"*) exit 1 ;;
  *Test-Path*) printf 'N\n' ;;
esac
SH
chmod +x remote-bin/ssh
: > "$TMP/transport.calls"
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" \
   RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
   RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" bash "$RF" stage run --stage build >/dev/null 2>&1 || true
grep -q 'schtasks /delete' "$TMP/transport.calls" && ok "remote build /run 失败仍删已建计划任务(I1 不遗留)" || no "remote build /run 失败未删任务"
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" != "done" ] && ok "remote build /run 失败不判 stage done" || no "remote build /run 失败误判 done"
bash "$RF" close >/dev/null

# 回归 I1:exitcode 文件内容非法(非数字)时,尾部统一清理必须删掉计划任务(该出口上轮也漏清)。
cat > remote-bin/ssh <<'SH'
#!/usr/bin/env bash
printf 'ssh %s\n' "$*" >> "$TRANSPORT_CALLS"
case "$*" in
  *Test-Path*) printf 'Y\n' ;;
  *Get-Content*) printf 'garbage\n' ;;
esac
SH
chmod +x remote-bin/ssh
: > "$TMP/transport.calls"
bash "$RF" init --manifest remote-build-manifest.json >/dev/null
PATH="$PWD/remote-bin:$PATH" TRANSPORT_CALLS="$TMP/transport.calls" FAKE_REMOTE="$TMP/fake-remote" \
   RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
   RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" bash "$RF" stage run --stage build >/dev/null 2>&1 || true
grep -q 'schtasks /delete' "$TMP/transport.calls" && ok "remote build exitcode 非法仍删计划任务(I1 不遗留)" || no "remote build exitcode 非法未删任务"
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" != "done" ] && ok "remote build exitcode 非法不判 stage done" || no "remote build exitcode 非法误判 done"
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
if bash "$RF" stage done --stage compile 2>/dev/null; then
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
[ "$(bash "$SCRIPT_DIR/../mmw.sh" release where)" = "STAGE:doctor RUN:true" ] && ok "mmw release 路由到引擎" || no "mmw 路由"

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
