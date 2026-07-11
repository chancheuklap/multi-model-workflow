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
  # C4:schtasks 起 release.ps1 必须显式传上下文绝对路径,否则默认 cwd 读不到裸文件名
  grep -q "release.ps1' -ReleaseContextPath '" "$TMP/transport.calls" && ok "remote build 显式传上下文绝对路径(cwd 合同)" || no "remote build 未传 -ReleaseContextPath"
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

bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
[ "$(bash "$SCRIPT_DIR/../mmw.sh" release where)" = "STAGE:doctor RUN:true" ] && ok "mmw release 路由到引擎" || no "mmw 路由"

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
