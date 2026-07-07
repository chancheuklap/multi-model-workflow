#!/usr/bin/env bash
# codex-worker.sh —— build 阶段 Codex 落地的唯一派发通道。
#
# 主线程快进快出:一条命令把一份 plan 派给 Codex 在 worktree 里落地,不让主线程
# 手搓 git worktree + codex CLI + session 记账。Codex 写代码(workspace-write 物理
# 围在 worktree),Claude 主线程在脚本外按 plan 验收清单 verify(命门,不脚本化)。
#
#   dispatch  --plan <abs.md> --worktree <abs> [--design <abs.md>] [--issue <abs.md>] [--base <ref>] [--model <m>] [--effort <e>]
#             worktree 不存在则从 --base(默认 HEAD)建;组装瘦前言 prompt(铁律在 Codex 侧 worktree-build
#             skill,prompt 只给三文档路径 + 指向 skill);codex exec 落地;记 session id(供 resume);打印 SESSION= + Codex 最后消息。
#             收工 fail-closed 核 docs/ 边界:Codex 碰了 docs/ → 打印 DOCS_VIOLATION 退非零(Worker 禁改 docs/,只有 Coordinator 能改)。
#   resume    --worktree <abs> --instructions <abs.md>
#             从 worktree 记的 session 续会话修复(keep context),发回修复指令;
#             session 文件丢失(dispatch 被杀)时自动从 codex-logs/run.log 捞回。
#
# 落地用标准档(设计/计划审用高档,在 review 侧);沙箱放行 git common dir,否则 worktree
# 内 git commit 写 objects/index.lock 被拒。
set -euo pipefail

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_EFFORT="${CODEX_EFFORT:-xhigh}"
STATE_SUBDIR=".claude/multi-model-workflow"

die() { echo "ERROR: $*" >&2; exit 2; }

# 瘦派发前言:不内联铁律(铁律在 Codex 侧已装的 worktree-build skill 里,渐进加载,
# 开工前不占 context)。这里只给角色 + worktree + 三文档路径 + 指向 skill。
build_prompt() {  # $1=plan_path $2=worktree $3=design_path(可空) $4=issue_path(可空)
  cat <<PROMPT
你是落地执行者(Codex),被主线程 Claude 派进一个 worktree 落地一份计划。
**读你已装的 \`worktree-build\` skill,照它走整个落地流程**(它是总纲,细纪律在它的 references,到那步再读)。

工作树(你唯一可写的源码区): $2
开工前读这几份(worktree 内路径,顺序读):
${3:+- 设计文档(意图/合同边界/发布风险): $3
}${4:+- 你的 issue(What to build / Acceptance / Blocked by): $4
}- 你的计划(实施唯一权威): $1

落地铁律、逐 Pack TDD、每 Pack 提交格式、禁改 docs/、卡住协议、收工回执格式 —— **全在 worktree-build skill,照它做,本消息不重复**(skill 是唯一权威;读不到就停下报,别猜别硬上)。
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
  local plan="" wt="" base="HEAD" model="$CODEX_MODEL" effort="$CODEX_EFFORT" design="" issue=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;;   # 设计文档路径(develop 必给;small-change/bug 无设计可空)
    --issue) issue="$2"; shift 2 ;;      # 该 plan 对应的 issue 路径(develop 给;无 issue 可空)
    --base) base="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填"
  [ -n "$wt" ]   || die "--worktree 必填"
  [ -f "$plan" ] || die "plan 文件不存在: $plan"

  # worktree 不存在则从 base 建(主线程开好 worktree 分配给 codex 的"开好"这步,脚本代劳)。
  # 挂命名分支(不留 detached HEAD):Codex 提交挂在分支上,清 worktree 不成孤儿,B4 按分支合并。
  if [ ! -d "$wt" ]; then
    git worktree add -b "codex/$(basename "$wt")" "$wt" "$base" >&2 \
      || die "建 worktree 失败: $wt(分支 codex/$(basename "$wt") 已存在?先清理旧分支)"
  fi
  # 状态平面对 git 不可见(同 prepare.sh):防 Codex add -A 把 codex-logs/session 记账提交进代码
  mkdir -p "$wt/.claude"
  [ -f "$wt/.claude/.gitignore" ] || printf '*\n' > "$wt/.claude/.gitignore"

  # 沙箱放行 git common dir(worktree 的 objects/refs 在父仓库,否则 commit 被拒)
  local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""

  # 本次派发起点(Codex 动了什么 = start_sha..HEAD + 未提交),供收工核 docs/ 边界
  local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"

  local pf; pf="$(mktemp)"; build_prompt "$plan" "$wt" "$design" "$issue" > "$pf"
  local rc=0
  run_codex "$wt" "$pf" \
    exec -C "$wt" --sandbox workspace-write \
    ${gcd:+--add-dir "$gcd"} \
    -m "$model" -c "model_reasoning_effort=\"$effort\"" || rc=$?
  rm -f "$pf"

  # fail-closed:Worker 禁改 docs/(CLAUDE.md 硬规则——docs/ 只有 Coordinator/主线程能改)。
  # Codex 碰了(本次已提交 或 未提交)就报违规、退非零,不让主线程当成功收下(prompt 文本之外的强制层)。
  local docs_touched
  docs_touched="$( { [ -n "$start_sha" ] && git -C "$wt" diff --name-only "$start_sha" HEAD 2>/dev/null
                     git -C "$wt" status --porcelain 2>/dev/null | sed 's/^...//'; } \
                   | grep '^docs/' | sort -u || true )"
  if [ -n "$docs_touched" ]; then
    echo "DOCS_VIOLATION: Codex 改了 docs/(Worker 禁改,只有 Coordinator 能改),打回重来:" >&2
    printf '%s\n' "$docs_touched" | sed 's/^/  /' >&2
    [ "$rc" -eq 0 ] && rc=3
  fi
  return "$rc"   # codex 失败或碰 docs/ 时透给主线程,不伪装成功(输出已留 CODEX_EXIT + log)
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
  # dispatch 中途被杀(如 Bash 超时)时 session 文件没落,但 run.log 实时写、开头就有
  # session id:从 log 捞回补记,不丢 resume 能力;捞不到才 fail-closed 拒
  [ -f "$sf" ] || record_session "$wt" "$wt/$STATE_SUBDIR/codex-logs/run.log" >/dev/null
  [ -f "$sf" ] || die "无 session 记账($sf,run.log 也捞不到);首派走 dispatch"
  local sid; sid="$(cat "$sf")"

  run_codex "$wt" "$instr" exec resume "$sid"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume)   shift; cmd_resume "$@" ;;
  *) die "用法: codex-worker.sh dispatch|resume ..." ;;
esac
