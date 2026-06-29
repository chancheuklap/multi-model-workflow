#!/usr/bin/env bash
# codex-worker.sh —— build 阶段 Codex 落地的唯一派发通道。
#
# 主线程快进快出:一条命令把一份 plan 派给 Codex 在 worktree 里落地,不让主线程
# 手搓 git worktree + codex CLI + session 记账。Codex 写代码(workspace-write 物理
# 围在 worktree),Claude 主线程在脚本外按 plan 验收清单 verify(命门,不脚本化)。
#
#   dispatch  --plan <abs.md> --worktree <abs> [--base <ref>] [--model <m>] [--effort <e>]
#             worktree 不存在则从 --base(默认 HEAD)建;组装固定前言 prompt;codex exec 落地;
#             记 session id(供 resume);打印 SESSION= + Codex 最后消息。
#   resume    --worktree <abs> --instructions <abs.md>
#             从 worktree 记的 session 续会话修复(keep context),发回修复指令。
#
# 落地用标准档(设计/计划审用高档,在 review 侧);沙箱放行 git common dir,否则 worktree
# 内 git commit 写 objects/index.lock 被拒。
set -euo pipefail

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_EFFORT="${CODEX_EFFORT:-xhigh}"
STATE_SUBDIR=".claude/multi-model-workflow"

die() { echo "ERROR: $*" >&2; exit 2; }

# 固定前言:PDF「严防过度设计/兜底/思考」+ 落地纪律(规范 Codex 行为,不给自由发挥)
build_prompt() {  # $1=plan_path $2=worktree
  cat <<PROMPT
你是落地执行者(Codex),严格按计划落地,不发挥、不扩张。
计划文件(唯一权威,照它做): $1
工作树(你唯一可写的源码区): $2

铁律:
- 严防过度设计 / 过度兜底 / 过度思考:只实现计划写明的;不加计划没要求的抽象 / 配置项 /
  防御分支 / 未来功能 / "顺手优化"。拿不准就少做,不多做。
- 严格 TDD(用已装的 /tdd):写失败测试 → 确认它真失败 → 最小实现 → 确认它真通过 → 提交。
- 一个 Task Pack 一次提交,commit message 含 "Pack N.M"。
- 只改源码,**禁改 docs/ 下任何文件**(设计 / 计划是上游权威,你不碰)。
- 缺输入,或计划与代码现实冲突 → 停下,在最后消息里讲清,**不自己猜着改方向**。

最后消息(主线程靠它验收): 逐 Pack 报 done / blocked + 每个 acceptance 达没达成 + 改了哪些文件 + 跑了哪些测试结果。
PROMPT
}

# 从 codex 日志抓 session id(header 格式 `session id: <uuid>`),记进 worktree 状态目录
record_session() {  # $1=worktree $2=logfile
  local sid; sid="$(grep -m1 -E '^session id:' "$2" 2>/dev/null | sed 's/^session id:[[:space:]]*//' || true)"
  [ -n "$sid" ] || { echo ""; return; }
  mkdir -p "$1/$STATE_SUBDIR"
  printf '%s\n' "$sid" > "$1/$STATE_SUBDIR/codex-session"
  echo "$sid"
}

run_codex() {  # $1=worktree $2=prompt_file $3..=codex args(不含 stdin)
  local wt="$1" prompt="$2"; shift 2
  local sd="$wt/$STATE_SUBDIR/codex-logs"; mkdir -p "$sd"
  local log="$sd/run.log" last="$sd/last.md"
  set +e
  "$CODEX_BIN" "$@" -o "$last" - < "$prompt" > "$log" 2>&1
  local ec=$?
  set -e
  local sid; sid="$(record_session "$wt" "$log")"
  echo "CODEX_EXIT=$ec"
  echo "SESSION=${sid:-unknown}"
  echo "--- codex 最后消息(验收读这个,事实需主线程亲验)---"
  cat "$last" 2>/dev/null || echo "(无最后消息;读 $log 排障)"
  # codex 非零退出 = 真失败,把退出码透给调用方,不伪装成功(输出已留痕 CODEX_EXIT + log)
  return "$ec"
}

cmd_dispatch() {
  local plan="" wt="" base="HEAD" model="$CODEX_MODEL" effort="$CODEX_EFFORT"
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填"
  [ -n "$wt" ]   || die "--worktree 必填"
  [ -f "$plan" ] || die "plan 文件不存在: $plan"

  # worktree 不存在则从 base 建(主线程开好 worktree 分配给 codex 的"开好"这步,脚本代劳)
  if [ ! -d "$wt" ]; then
    git worktree add "$wt" "$base" >&2 || die "建 worktree 失败: $wt"
  fi

  # 沙箱放行 git common dir(worktree 的 objects/refs 在父仓库,否则 commit 被拒)
  local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""

  local pf; pf="$(mktemp)"; build_prompt "$plan" "$wt" > "$pf"
  local rc=0
  run_codex "$wt" "$pf" \
    exec -C "$wt" --sandbox workspace-write \
    ${gcd:+--add-dir "$gcd"} \
    -m "$model" -c "model_reasoning_effort=\"$effort\"" || rc=$?
  rm -f "$pf"
  return "$rc"   # codex 失败时透给主线程,不伪装成功(输出已留 CODEX_EXIT + log)
}

cmd_resume() {
  local wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$wt" ]    || die "--worktree 必填"
  [ -f "$instr" ] || die "--instructions 文件不存在: $instr"
  local sf="$wt/$STATE_SUBDIR/codex-session"
  [ -f "$sf" ] || die "无 session 记账($sf);首派走 dispatch"
  local sid; sid="$(cat "$sf")"

  run_codex "$wt" "$instr" exec resume "$sid"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume)   shift; cmd_resume "$@" ;;
  *) die "用法: codex-worker.sh dispatch|resume ..." ;;
esac
