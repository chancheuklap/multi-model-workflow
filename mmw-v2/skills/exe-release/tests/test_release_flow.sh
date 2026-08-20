#!/usr/bin/env bash
# release-flow.sh 引擎空跑:载入 fail-loud、状态机推进、exit-check、round cap、resume、原子写。
set -euo pipefail
# 状态目录由目标仓库的 .mmw.json 的 paths.release 决定，不再是写死的常量。
STATE_SUBDIR="${STATE_SUBDIR:-.release}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RF="$SCRIPT_DIR/../scripts/release-flow.sh"
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
printf '{"paths":{"release":"%s","scratch":".scratch","reviews":".reviews","worktrees":".worktrees"}}\n' \
  "$STATE_SUBDIR" > .mmw.json
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
if bash "$RF" stage run --stage doctor >/dev/null; then
  [ "$(jq -r '.stages[]|select(.name=="doctor").status' "$SF")" = "done" ] && ok "stage run 真执行并标 done" || no "stage run 未标 doctor done"
  [ "$(bash "$RF" where)" = "STAGE:smoke RUN:true" ] && ok "stage run 后推进到 smoke" || no "推进 ($(bash "$RF" where))"
else
  no "stage run 应执行当前普通 argv"
fi
[ "$(bash "$RF" exit-check)" = "NOT-DONE:stages=smoke,verify_key,assemble,build" ] && ok "exit-check 列剩余" || no "exit-check ($(bash "$RF" exit-check))"

for stage in smoke verify_key assemble build; do bash "$RF" stage done --stage "$stage" >/dev/null; done
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
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "5" ] && ok "同 HEAD resume 令失败 stage 及后继 pending" || no "同 HEAD resume stage 状态错误"

bash "$RF" close >/dev/null
bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
bash "$RF" stage done --stage doctor >/dev/null
echo changed > source-change
git add source-change
git commit -qm source-change
bash "$RF" resume >/dev/null
[ "$(jq -r '.source_commit' "$SF")" = "$(git rev-parse HEAD)" ] && ok "HEAD 改变后更新 source_commit" || no "HEAD 改变后 source_commit 过期"
[ "$(jq -r '.current_stage' "$SF")" = "doctor" ] && ok "HEAD 改变后从首 stage 重验" || no "HEAD 改变后未回首 stage"
[ "$(jq -r '[.stages[] | select(.status == "pending")] | length' "$SF")" = "5" ] && ok "HEAD 改变后所有 stage pending" || no "HEAD 改变后残留旧产物状态"

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
  bash "$RF" close >/dev/null 2>&1 || true
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
  for f in release.ps1 release-context.json run-release.ps1 run-release.cmd SOURCE_COMMIT.txt; do
    [ -s "$bd/$f" ] || { no "构建输入缺 $f"; continue; }
  done
  ok "构建输入都上传了"

  # 守:源码 zip 是 `git archive $(cat SOURCE_COMMIT.txt)` 一字不差重生得出来的,不是记录。
  # 一份几百 MB,每一次尝试在两端各留一份,几轮就把两台机器塞满。
  [ ! -e "$bd/source.zip" ] && ok "解压后构建机上不留源码 zip" || no "构建机上留着源码 zip"
  [ -z "$(find "$(dirname "$SF")/release-artifacts" -name source.zip 2>/dev/null)" ] \
    && ok "上传后 Mac 上不留源码 zip" || no "Mac 上留着源码 zip"

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
bash "$RF" close >/dev/null

# 守:失败的构建目录必须留下。根因只存在于那台机器上的那个目录里,删了就再也查不出来。
remote_reset
init_for_remote_build
export FAKE_BUILD_OUTCOME=fail:3
remote_build >/dev/null 2>&1 || true
[ -n "$(build_dir)" ] && ok "失败的构建目录留在构建机上" || no "失败现场被删掉了"
bash "$RF" close >/dev/null
printf '{"repo_root":"/placeholder","product":"test-product"}\n' > "$LOOP_DIR/release-context.json"

# 守:失败的构建目录只留最近两个。一个几个 GB,不封顶的话构建机迟早被自己的中间产物填满;
# 而封过头就是把还要查的现场删掉——所以断的是「哪几个还在」,不是「删过东西」。
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
[ ! -e "$input_root/000000000001-test-product" ] && ok "更老的失败目录被清掉" || no "旧构建目录无上限地堆着"
[ -e "$input_root/000000000002-test-product" ] && [ -e "$input_root/000000000003-test-product" ] \
  && ok "最近两个失败目录留着" || no "还要查的现场被删掉了"
[ -e "$input_root/000000000004-other-product" ] && ok "不碰别的产品的目录" || no "删到了别的产品"
bash "$RF" close >/dev/null

# 守:装配之后技能自己改了，那份生成脚本就过期了。拿它去构建机跑，日志里每一步都对——
# 只是跑的不是刚改的那一份。引擎只按产品仓库的 HEAD 判断要不要重来，看不见这一类改动。
remote_reset
init_for_remote_build
edit_state() { jq "$1" "$SF" > "$SF.tmp" && mv "$SF.tmp" "$SF"; }
edit_state '.skill_fingerprint = "从前那一份"'
if remote_build >/dev/null 2>&1; then
  no "拿着过期的脚本照跑了"
else
  [ "$(jq -r '.current_stage' "$SF")" = "assemble" ] \
    && ok "技能改过就先回去重新装配" || no "没有回到 assemble"
fi
bash "$RF" close >/dev/null

# 守:上一轮的 attempt 目录不能留。attempt 号从 a0 重新数,旧目录跟本轮同名对撞,于是
# 「本轮的 a0-build」读到的是上一个产品的结果,而没有任何一步报错。
remote_reset
mkdir -p "$(dirname "$SF")/release-artifacts/a0-build"
printf '别的产品的结果\n' > "$(dirname "$SF")/release-artifacts/a0-build/build.findings.json"
init_for_remote_build
[ ! -e "$(dirname "$SF")/release-artifacts/a0-build/build.findings.json" ] \
  && ok "init 不继承上一轮的 attempt 目录" || no "上一轮的 attempt 目录跟本轮同名对撞"
bash "$RF" close >/dev/null

# 守:重跑同一个 commit 时,若不清上一轮的退出码,第一次轮询就会读到上轮的 0,把仍在跑
# 或已失败的本轮判成成功——错的包会被当成好包发出去。
remote_reset
init_for_remote_build
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
init_for_remote_build
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "清不掉旧产物就不开工" || no "清理失败仍判 done"
[ "$(task_count)" = "0" ] && ok "清不掉旧产物时不建计划任务" || no "清理失败仍建了任务"
bash "$RF" close >/dev/null

# 守:构建卡死时若不结束任务,孤儿构建会抢写下一轮同 commit 的退出码。
remote_reset
export FAKE_BUILD_OUTCOME=hang
init_for_remote_build
PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 RELEASE_REMOTE_BUILD_TIMEOUT_SECONDS=0 \
  RELEASE_REMOTE_HOST="fake@pc" RELEASE_REMOTE_ROOT="C:/release-input" \
  bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "构建超时不判 done" || no "超时误判 done"
[ "$(task_count)" = "0" ] && ok "构建超时清掉计划任务" || no "超时留下孤儿任务"
bash "$RF" close >/dev/null

# 守:启动命令偶发「返回 0 但任务没起来」,已建的任务必须清掉,否则同样留孤儿。
remote_reset
export FAKE_RUN_FAILS=1
init_for_remote_build
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "任务起不来不判 done" || no "起不来仍判 done"
[ "$(task_count)" = "0" ] && ok "任务起不来也清掉已建的任务" || no "起不来留下孤儿任务"
bash "$RF" close >/dev/null

# 守:退出码文件损坏时判不出成败,同样要清干净再交人。
remote_reset
export FAKE_BUILD_OUTCOME=garbage
init_for_remote_build
remote_build >/dev/null 2>&1 || true
[ "$(build_status)" != "done" ] && ok "退出码非法不判 done" || no "退出码非法仍判 done"
[ "$(task_count)" = "0" ] && ok "退出码非法也清掉计划任务" || no "退出码非法留下孤儿任务"
bash "$RF" close >/dev/null

# 守:远端路径里的空格与引号会打断 PowerShell 字符串或触发变量展开,而跨三个解析器
# 没有统一的引号合同。这类根路径必须在碰构建机之前就被拒。
for bad_root in "C:/release input" "C:/release'input" 'C:/release$input'; do
  remote_reset
  init_for_remote_build
  remote_build "$bad_root" >/dev/null 2>&1 || true
  [ "$(build_status)" != "done" ] && ok "危险远端根被拒($bad_root)" || no "危险远端根未被拒($bad_root)"
  [ -z "$(ls -A "$FAKE_REMOTE_ROOT")" ] && ok "危险远端根没碰到构建机($bad_root)" || no "危险远端根已在构建机落地($bad_root)"
  bash "$RF" close >/dev/null
done

# 守:失败根因只存在于构建机的日志里。不回传,Mac 侧永远诊断不出 finding,自愈闭环断掉。
remote_reset
export FAKE_BUILD_OUTCOME=fail:7
init_for_remote_build
remote_build >/dev/null 2>&1 || true
bash "$RF" receipt > "$TMP/receipt.out"
grep -q 'logs=' "$TMP/receipt.out" && ok "回执给出日志位置(自主处置的入口)" || no "回执没有日志位置"
bash "$RF" close >/dev/null
unset FAKE_BUILD_OUTCOME FAKE_RUN_FAILS FAKE_REMOVE_FAILS
bash "$RF" close >/dev/null

# 守:构建机是哪一台,不能只活在人的记忆里。两个值都缺时出包停在这一步等人补,
# 而钥匙旁边放一份 remote-build.json 就没人需要记它。
remote_reset
init_for_remote_build
PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
  bash "$RF" stage run --stage build >/dev/null 2>&1 || true
if grep -rq 'ERROR: remote build has no RELEASE_REMOTE_HOST' "$STATE_SUBDIR" 2>/dev/null; then
  ok "两处都没有时报错文字不变(诊断的根因指纹靠它)"
else
  no "缺构建机的报错文字变了"
fi
bash "$RF" close >/dev/null

printf '{"host":"fake@pc","root":"C:/from-file"}\n' > remote-build.json
remote_reset
init_for_remote_build
PATH="$REMOTE_FIX:$PATH" RELEASE_REMOTE_BUILD_POLL_SECONDS=0 \
  bash "$RF" stage run --stage build >/dev/null 2>&1 || true
[ "$(build_status)" = "done" ] && ok "只有 remote-build.json 也能出包" || no "读不到 remote-build.json"
case "$(build_dir)" in
  */from-file/*) ok "构建落在文件里写的远端根" ;;
  *) no "远端根不是文件里那个($(build_dir))" ;;
esac
bash "$RF" close >/dev/null

# 守:环境变量必须压过文件——临时换一台构建机只有这一个手段,测试也靠它灌假值。
remote_reset
init_for_remote_build
remote_build "C:/from-env" >/dev/null 2>&1 || true
case "$(build_dir)" in
  */from-env/*) ok "环境变量压过 remote-build.json" ;;
  *) no "文件盖掉了环境变量($(build_dir))" ;;
esac
bash "$RF" close >/dev/null
rm -f remote-build.json

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
if bash "$RF" stage done --stage build 2>/dev/null; then
  no "stage done 跳步应被拒绝"
else
  ok "stage done 拒绝跳步标 done"
fi
[ "$(jq -r '.stages[] | select(.name=="build") | .status' "$SF")" = "pending" ] && ok "被拒后 build 仍 pending" || no "被拒后状态被改"

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

# 没有 .mmw.json 的仓库也要能出包：状态落 .release。旧引擎在这里直接 die，
# 而绝大多数仓库根本没有那个文件。
NOCFG="$(mktemp -d)"
(
  cd "$NOCFG"
  git init -q
  git config user.email t@t
  git config user.name t
  echo s > s
  git add -A
  git commit -qm s
  bash "$RF" init --manifest "$FIX/manifest.fake.json" >/dev/null
)
[ -f "$NOCFG/.release/release-state.json" ] && ok "无 .mmw.json 时状态落 .release" || no "无 .mmw.json 缺省落点"
rm -rf "$NOCFG"

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]
