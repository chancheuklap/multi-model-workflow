#!/usr/bin/env bash
# worker.sh —— 写码工人 + 写计划工人派发(宿主中立入口)
#
# 写码(build 落地,开子 worktree、改源码、每 Pack 提交):
#   dispatch  --plan <abs.md> --worktree <abs> [--design ...] [--issue ...] [--base ...] [--model ...] [--effort ...]
#   resume    --worktree <abs> --instructions <abs.md>
#   check-docs --worktree <abs>                 # 机器核 docs/ 红线(禁碰 docs/)
#
# 写计划(plan 撰写,在任务 worktree 内、只写 docs/plans + docs/issues、不 commit):
#   plan-dispatch --plan <落点 abs.md> --worktree <任务 wt abs> [--design ...] [--issue ...] [--model ...] [--effort ...]
#   plan-resume   --plan <落点 abs.md> --worktree <abs> --instructions <abs.md>
#   plan-check    --plan <落点 abs.md> --worktree <abs>   # 反向边界:diff 必须 ⊆ {docs/plans, docs/issues}
#
# 后端:
#   claude → 外挂 codex CLI(写码 = codex-worker 行为;写计划 = codex exec -C 任务 worktree)
#   droid  → 准备 prompt 包,打印 Task 派发说明(写码→pack-executor / 写计划→plan-writer)
#
# 兼容:mmw codex * 仍路由到本脚本。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/host.sh
. "$SCRIPT_DIR/lib/host.sh"

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.5}"
CODEX_EFFORT="${CODEX_EFFORT:-xhigh}"
DROID_EXECUTOR_DROID="${DROID_EXECUTOR_DROID:-pack-executor}"
DROID_EXECUTOR_MODEL="${DROID_EXECUTOR_MODEL:-glm-5.2}"
DROID_EXECUTOR_EFFORT="${DROID_EXECUTOR_EFFORT:-max}"
# 写计划档(plan-dispatch):Claude 宿主 Codex / Droid 宿主 plan-writer droid。plan = design 档,gpt-5.5 xhigh。
CODEX_PLAN_MODEL="${CODEX_PLAN_MODEL:-gpt-5.5}"
CODEX_PLAN_EFFORT="${CODEX_PLAN_EFFORT:-xhigh}"
DROID_PLAN_DROID="${DROID_PLAN_DROID:-plan-writer}"
DROID_PLAN_MODEL="${DROID_PLAN_MODEL:-gpt-5.5}"
DROID_PLAN_EFFORT="${DROID_PLAN_EFFORT:-xhigh}"

# worktree 真实状态平面(跨宿主续跑;新建派发时若无旧平面则落到当前宿主)
state_for() { mmw_resolve_state_subdir "$1"; }

die() { echo "ERROR: $*" >&2; exit 2; }

build_prompt() {  # $1=plan $2=worktree $3=design $4=issue
  # skill 指针按宿主:Claude 侧 Codex CLI 读它自己 hub 装的;Droid 侧读 plugin 内随插件发布的副本(绝对路径)。
  local skill_ref skill_tail
  if [ "$(mmw_host)" = "droid" ]; then
    local sroot; sroot="$(mmw_plugin_root)/skills/worktree-build"
    skill_ref="**读 plugin 内 \`worktree-build\` skill,照它走整个落地流程**(它是总纲,细纪律在它的 references,到那步再读):$sroot/SKILL.md"
    skill_tail="**全在 worktree-build skill(plugin 内 $sroot/),照它做,本消息不重复**"
  else
    skill_ref="**读你已装的 \`worktree-build\` skill,照它走整个落地流程**(它是总纲,细纪律在它的 references,到那步再读)。"
    skill_tail="**全在 worktree-build skill,照它做,本消息不重复**"
  fi
  cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 落地一份计划。
$skill_ref

工作树(你唯一可写的源码区): $2
开工前读这几份(worktree 内路径,顺序读):
${3:+- 设计文档(意图/合同边界/发布风险): $3
}${4:+- 你的 issue(What to build / Acceptance / Blocked by): $4
}- 你的计划(实施唯一权威): $1

落地铁律、逐 Pack TDD、每 Pack 提交格式、禁改 docs/、卡住协议、收工回执格式 —— ${skill_tail}。
PROMPT
}

plan_ns() { basename "$1" .md; }  # 落点路径 → 派发命名空间(并行写计划在同一 worktree,靠它隔离 session/log)

build_plan_prompt() {  # $1=落点 $2=worktree $3=design $4=issue $5=task-pack.md abs $6=plan-self-check.md abs $7=mockup 目录(可空)
  local skill_ref
  if [ "$(mmw_host)" = "droid" ]; then
    local sroot; sroot="$(mmw_plugin_root)/skills/worktree-plan"
    skill_ref="**读 plugin 内 \`worktree-plan\` skill,照它走整个写计划流程**(总纲,细纪律到那步再读):$sroot/SKILL.md"
  else
    skill_ref="**读你已装的 \`worktree-plan\` skill,照它走整个写计划流程**(总纲,细纪律到那步再读)。"
  fi
  cat <<PROMPT
你是计划撰写者,被主线程派进任务 worktree 把一个大 issue 写成一份实施计划。
$skill_ref

任务工作树: $2
你的落点(只写这一份 plan 文件): $1
开工前读这几份(绝对路径,顺序读):
${3:+- 源设计文档(architecture / 合同边界 / Cross-Plan Contract Anchors): $3
}${4:+- 你负责的大 issue(What to build;## Small issues 若为 PENDING 你来拆): $4
}- 写作方法论(写每个 pack 时读): $5
- 交付前自检(返回前读): $6
${7:+- mockup 目录(每页视觉规格 / 交互 / 状态变体拆进对应 pack 的 acceptance): $7
}
拆小 issue、逐 Task Pack、无 Placeholder、测试规划严谨度、Return Contract —— **全在 worktree-plan skill,照它做,本消息不重复**。
边界:只写你落点那份 plan + 你 issue 的 \`## Small issues\`;不碰源码 / \`docs/design/\` / 别的 plan;不 commit(改动留 unstaged,主线程统一提交)。
PROMPT
}

check_docs_boundary() {  # $1=worktree $2=start_sha
  local docs_touched
  docs_touched="$( { [ -n "$2" ] && git -C "$1" diff --name-only "$2" HEAD 2>/dev/null
                     git -C "$1" status --porcelain 2>/dev/null | sed 's/^...//'; } \
                   | grep '^docs/' | sort -u || true )"
  [ -z "$docs_touched" ] && return 0
  echo "DOCS_VIOLATION: Worker 改了 docs/(只有 Coordinator 能改),打回重来:" >&2
  printf '%s\n' "$docs_touched" | sed 's/^/  /' >&2
  return 3
}

check_plan_boundary() {  # $1=worktree $2=start_sha —— 反向:写计划只准碰 docs/plans + docs/issues,越界打回
  # --untracked-files=all:否则 git 把整棵未跟踪目录折叠成一条(如 docs/),核不到文件级会误判。
  local touched offending
  touched="$( { [ -n "$2" ] && git -C "$1" diff --name-only "$2" HEAD 2>/dev/null
                git -C "$1" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'; } \
              | sort -u | grep -v '^[[:space:]]*$' || true )"
  offending="$( printf '%s\n' "$touched" | grep -vE '^docs/(plans|issues)/' | grep -v '^[[:space:]]*$' || true )"
  [ -z "$offending" ] && return 0
  echo "PLAN_VIOLATION: 写计划工人碰了 docs/plans, docs/issues 以外的文件(只准写这两处),打回重来:" >&2
  printf '%s\n' "$offending" | sed 's/^/  /' >&2
  return 3
}

# ---------- Codex CLI backend (Claude host) ----------
record_session() {
  local sid sd; sid="$(grep -m1 -E '^session id:' "$2" 2>/dev/null | sed 's/^session id:[[:space:]]*//' || true)"
  [ -n "$sid" ] || { echo ""; return; }
  sd="$(state_for "$1")"
  mkdir -p "$1/$sd"
  printf '%s\n' "$sid" > "$1/$sd/codex-session"
  echo "$sid"
}

run_codex() {
  local wt="$1" prompt="$2"; shift 2
  local st; st="$(state_for "$wt")"
  local sd="$wt/$st/codex-logs"; mkdir -p "$sd"
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
  return "$ec"
}

# 写计划专用:session/log 落 plan-workers/<ns>/,并行同 worktree 多 writer 互不覆盖。
run_codex_plan() {  # $1=wt $2=ns $3=prompt; shift 3; rest=codex args
  local wt="$1" ns="$2" prompt="$3"; shift 3
  local st; st="$(state_for "$wt")"
  local sd="$wt/$st/plan-workers/$ns"; mkdir -p "$sd"
  local log="$sd/run.log" last="$sd/last.md"
  set +e
  "$CODEX_BIN" "$@" -o "$last" - < "$prompt" > "$log" 2>&1
  local ec=$?
  set -e
  local sid; sid="$(grep -m1 -E '^session id:' "$log" 2>/dev/null | sed 's/^session id:[[:space:]]*//' || true)"
  [ -n "$sid" ] && printf '%s\n' "$sid" > "$sd/codex-session"
  echo "CODEX_EXIT=$ec"
  echo "SESSION=${sid:-unknown}"
  echo "PLAN_WORKER_NS=$ns"
  echo "--- codex 最后消息(验收读这个,事实需主线程亲验)---"
  cat "$last" 2>/dev/null || echo "(无最后消息;读 $log 排障)"
  return "$ec"
}

ensure_worktree() {
  local wt="$1" base="$2"
  if [ ! -d "$wt" ]; then
    local bprefix; bprefix="$(mmw_worker_branch_prefix)"
    git worktree add -b "$bprefix/$(basename "$wt")" "$wt" "$base" >&2 \
      || die "建 worktree 失败: $wt(分支 $bprefix/$(basename "$wt") 已存在?先清理)"
  fi
  mmw_ensure_wt_state_ignore "$wt"
}

# ---------- Droid Task backend ----------
write_droid_dispatch_pkg() {
  local wt="$1" plan="$2" design="$3" issue="$4" model="$5" effort="$6" mode="$7" instr="${8:-}"
  local st; st="$(state_for "$wt")"
  local pkg="$wt/$st/worker-dispatch"
  local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
  mkdir -p "$pkg"
  if [ "$mode" = "dispatch" ]; then
    build_prompt "$plan" "$wt" "$design" "$issue" > "$pkg/prompt.md"
  else
    cp "$instr" "$pkg/prompt.md"
  fi
  printf '%s\n' "$start_sha" > "$pkg/start_sha"
  cat > "$pkg/meta.json" <<META
{
  "backend": "droid-task",
  "mode": "$mode",
  "droid": "$DROID_EXECUTOR_DROID",
  "model": "$model",
  "effort": "$effort",
  "worktree": "$wt",
  "plan": "$plan",
  "design": "$design",
  "issue": "$issue",
  "prompt_file": "$pkg/prompt.md",
  "start_sha": "$start_sha",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
META
  printf '%s %s\n' "$model" "$effort" > "$wt/$st/worker-model"
  echo "WORKER_BACKEND=droid-task"
  echo "WORKER_MODE=$mode"
  echo "WORKTREE=$wt"
  echo "PROMPT_FILE=$pkg/prompt.md"
  echo "META_FILE=$pkg/meta.json"
  echo "START_SHA=$start_sha"
  echo "DROID=$DROID_EXECUTOR_DROID"
  echo "MODEL=$model"
  echo "EFFORT=$effort"
  cat <<EOF
--- droid 派发(主线程照做)---
用 Task 工具派 Custom Droid:
  subagent_type: $DROID_EXECUTOR_DROID
  model 偏好: $model (reasoningEffort=$effort; 以 droid 文件 model 为准)
  prompt: 完整读取并执行 $pkg/prompt.md
工作目录必须是 worktree: $wt
Task 返回后**必须**先机器核 docs 红线(与 Claude codex 路径同语义 fail-closed):
  mmw worker check-docs --worktree $wt
非零 / DOCS_VIOLATION → 写修复指令 resume 打回,禁止 mmw loop step done。
通过后再亲验(跑测试/读 diff) → mmw loop step done。
EOF
}

# Droid 写计划派发包(plan-writer droid,在任务 worktree 内写 plan,不开子 worktree)
write_droid_plan_pkg() {
  local plan="$1" wt="$2" design="$3" issue="$4" taskpack="$5" selfcheck="$6" mockup="$7" model="$8" effort="$9" mode="${10}" instr="${11:-}"
  local ns; ns="$(plan_ns "$plan")"
  local st; st="$(state_for "$wt")"
  local pkg="$wt/$st/plan-workers/$ns/dispatch"
  local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
  mkdir -p "$pkg"
  if [ "$mode" = "dispatch" ]; then
    build_plan_prompt "$plan" "$wt" "$design" "$issue" "$taskpack" "$selfcheck" "$mockup" > "$pkg/prompt.md"
  else
    cp "$instr" "$pkg/prompt.md"
  fi
  printf '%s\n' "$start_sha" > "$pkg/start_sha"
  printf '%s %s\n' "$model" "$effort" > "$wt/$st/plan-workers/$ns/worker-model"
  echo "WORKER_BACKEND=droid-task"
  echo "WORKER_MODE=$mode"
  echo "WORKTREE=$wt"
  echo "PLAN_WORKER_NS=$ns"
  echo "PROMPT_FILE=$pkg/prompt.md"
  echo "START_SHA=$start_sha"
  echo "DROID=$DROID_PLAN_DROID"
  echo "MODEL=$model"
  echo "EFFORT=$effort"
  cat <<EOF
--- droid 写计划派发(主线程照做)---
用 Task 工具派 Custom Droid:
  subagent_type: $DROID_PLAN_DROID
  model 偏好: $model (reasoningEffort=$effort; 以 droid 文件 model 为准)
  prompt: 完整读取并执行 $pkg/prompt.md
工作目录必须是任务 worktree: $wt
Task 返回后**必须**先机器核写计划边界(fail-closed):
  mmw worker plan-check --plan $plan --worktree $wt
非零 / PLAN_VIOLATION → 写修复指令 plan-resume 打回,禁止采信。
通过后再亲验(plan 文件存在 / Pack 数 / file:line / 小 issue 写回)。
EOF
}

# 机器核 docs/ 边界(Claude 路径在 dispatch/resume 末自动跑;Droid 路径 Task 返回后主线程必跑)
cmd_check_docs() {
  local wt="" start_sha=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;;
    --start-sha) start_sha="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$wt" ] || die "--worktree 必填"
  [ -d "$wt" ] || die "worktree 不存在: $wt"
  local st; st="$(state_for "$wt")"
  if [ -z "$start_sha" ] && [ -f "$wt/$st/worker-dispatch/start_sha" ]; then
    start_sha="$(cat "$wt/$st/worker-dispatch/start_sha")"
  fi
  if [ -z "$start_sha" ] && [ -f "$wt/$st/worker-dispatch/meta.json" ]; then
    start_sha="$(jq -r '.start_sha // empty' "$wt/$st/worker-dispatch/meta.json" 2>/dev/null || true)"
  fi
  [ -n "$start_sha" ] || die "无 start_sha(dispatch 包或 --start-sha);无法核 docs 边界"
  check_docs_boundary "$wt" "$start_sha"
}

cmd_dispatch() {
  local plan="" wt="" base="HEAD" model="" effort="" design="" issue=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;;
    --issue) issue="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填"
  [ -n "$wt" ]   || die "--worktree 必填"
  [ -f "$plan" ] || die "plan 文件不存在: $plan"

  ensure_worktree "$wt" "$base"
  local st; st="$(state_for "$wt")"
  mkdir -p "$wt/$st"

  case "$(mmw_worker_backend)" in
    droid-task)
      [ -n "$model" ] || model="$DROID_EXECUTOR_MODEL"
      [ -n "$effort" ] || effort="$DROID_EXECUTOR_EFFORT"
      write_droid_dispatch_pkg "$wt" "$plan" "$design" "$issue" "$model" "$effort" "dispatch"
      return 0
      ;;
    codex-cli)
      [ -n "$model" ] || model="$CODEX_MODEL"
      [ -n "$effort" ] || effort="$CODEX_EFFORT"
      local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
      local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
      printf '%s %s\n' "$model" "$effort" > "$wt/$st/codex-model"
      local pf; pf="$(mktemp)"; build_prompt "$plan" "$wt" "$design" "$issue" > "$pf"
      local rc=0
      run_codex "$wt" "$pf" \
        exec -C "$wt" --sandbox workspace-write \
        ${gcd:+--add-dir "$gcd"} \
        -m "$model" -c "model_reasoning_effort=\"$effort\"" || rc=$?
      rm -f "$pf"
      if ! check_docs_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
      return "$rc"
      ;;
    *) die "未知 worker backend: $(mmw_worker_backend)" ;;
  esac
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
  local st; st="$(state_for "$wt")"

  case "$(mmw_worker_backend)" in
    droid-task)
      local model="$DROID_EXECUTOR_MODEL" effort="$DROID_EXECUTOR_EFFORT"
      [ -f "$wt/$st/worker-model" ] && read -r model effort < "$wt/$st/worker-model"
      write_droid_dispatch_pkg "$wt" "" "" "" "$model" "$effort" "resume" "$instr"
      return 0
      ;;
    codex-cli)
      local sf="$wt/$st/codex-session"
      [ -f "$sf" ] || record_session "$wt" "$wt/$st/codex-logs/run.log" >/dev/null
      [ -f "$sf" ] || die "无 session 记账($sf,run.log 也捞不到);首派走 dispatch"
      local sid; sid="$(cat "$sf")"
      local model="$CODEX_MODEL" effort="$CODEX_EFFORT"
      [ -f "$wt/$st/codex-model" ] && read -r model effort < "$wt/$st/codex-model"
      local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
      local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
      local rc=0
      run_codex "$wt" "$instr" \
        exec -C "$wt" --sandbox workspace-write \
        ${gcd:+--add-dir "$gcd"} \
        -m "$model" -c "model_reasoning_effort=\"$effort\"" \
        resume "$sid" || rc=$?
      if ! check_docs_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
      return "$rc"
      ;;
    *) die "未知 worker backend" ;;
  esac
}

# ---------- 写计划派发(在任务 worktree 内,不开子 worktree、不 commit)----------
plan_methodology_paths() {  # 回显 taskpack + selfcheck 绝对路径(单源在 orchestrate,build-a 也用)
  local root; root="$(mmw_plugin_root)"
  local tp="$root/skills/orchestrate/references/plan/task-pack.md"
  local sc="$root/skills/orchestrate/references/plan/plan-self-check.md"
  [ -f "$tp" ] || die "写计划方法论缺失: $tp"
  [ -f "$sc" ] || die "写计划方法论缺失: $sc"
  printf '%s\t%s\n' "$tp" "$sc"
}

cmd_plan_dispatch() {
  local plan="" wt="" design="" issue="" mockup="" model="" effort=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;;
    --issue) issue="$2"; shift 2 ;;
    --mockup) mockup="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填(落点路径)"
  [ -n "$wt" ]   || die "--worktree 必填"
  case "$plan" in /*) ;; *) die "--plan 必须绝对路径" ;; esac
  [ -d "$wt" ]   || die "任务 worktree 不存在: $wt"
  local tp sc; IFS=$'\t' read -r tp sc < <(plan_methodology_paths)
  local st; st="$(state_for "$wt")"; mkdir -p "$wt/$st"
  mmw_ensure_wt_state_ignore "$wt"   # 状态平面 gitignore,否则 plan-workers/ 会被 check_plan_boundary 当越界误报
  local ns; ns="$(plan_ns "$plan")"

  case "$(mmw_worker_backend)" in
    droid-task)
      [ -n "$model" ] || model="$DROID_PLAN_MODEL"
      [ -n "$effort" ] || effort="$DROID_PLAN_EFFORT"
      write_droid_plan_pkg "$plan" "$wt" "$design" "$issue" "$tp" "$sc" "$mockup" "$model" "$effort" "dispatch"
      return 0
      ;;
    codex-cli)
      [ -n "$model" ] || model="$CODEX_PLAN_MODEL"
      [ -n "$effort" ] || effort="$CODEX_PLAN_EFFORT"
      local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
      local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
      mkdir -p "$wt/$st/plan-workers/$ns"
      printf '%s %s\n' "$model" "$effort" > "$wt/$st/plan-workers/$ns/codex-model"
      printf '%s\n' "$start_sha" > "$wt/$st/plan-workers/$ns/start_sha"
      local pf; pf="$(mktemp)"; build_plan_prompt "$plan" "$wt" "$design" "$issue" "$tp" "$sc" "$mockup" > "$pf"
      local rc=0
      run_codex_plan "$wt" "$ns" "$pf" \
        exec -C "$wt" --sandbox workspace-write \
        ${gcd:+--add-dir "$gcd"} \
        -m "$model" -c "model_reasoning_effort=\"$effort\"" || rc=$?
      rm -f "$pf"
      if ! check_plan_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
      return "$rc"
      ;;
    *) die "未知 worker backend: $(mmw_worker_backend)" ;;
  esac
}

cmd_plan_resume() {
  local plan="" wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ]  || die "--plan 必填(定位是哪份计划的会话)"
  [ -n "$wt" ]    || die "--worktree 必填"
  [ -f "$instr" ] || die "--instructions 文件不存在: $instr"
  local st; st="$(state_for "$wt")"
  local ns; ns="$(plan_ns "$plan")"
  local sd="$wt/$st/plan-workers/$ns"

  case "$(mmw_worker_backend)" in
    droid-task)
      local model="$DROID_PLAN_MODEL" effort="$DROID_PLAN_EFFORT"
      [ -f "$sd/worker-model" ] && read -r model effort < "$sd/worker-model"
      write_droid_plan_pkg "$plan" "$wt" "" "" "" "" "" "$model" "$effort" "resume" "$instr"
      return 0
      ;;
    codex-cli)
      [ -f "$sd/codex-session" ] || die "无 session 记账($sd/codex-session);首派走 plan-dispatch"
      local sid; sid="$(cat "$sd/codex-session")"
      local model="$CODEX_PLAN_MODEL" effort="$CODEX_PLAN_EFFORT"
      [ -f "$sd/codex-model" ] && read -r model effort < "$sd/codex-model"
      local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
      local start_sha; start_sha="$(cat "$sd/start_sha" 2>/dev/null || git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
      local rc=0
      run_codex_plan "$wt" "$ns" "$instr" \
        exec -C "$wt" --sandbox workspace-write \
        ${gcd:+--add-dir "$gcd"} \
        -m "$model" -c "model_reasoning_effort=\"$effort\"" \
        resume "$sid" || rc=$?
      if ! check_plan_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
      return "$rc"
      ;;
    *) die "未知 worker backend" ;;
  esac
}

cmd_plan_check() {  # 机器核写计划边界(Droid 路径 Task 返回后主线程必跑)
  local plan="" wt="" start_sha=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --start-sha) start_sha="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填"
  [ -n "$wt" ]   || die "--worktree 必填"
  [ -d "$wt" ]   || die "worktree 不存在: $wt"
  local st; st="$(state_for "$wt")"
  local ns; ns="$(plan_ns "$plan")"
  [ -z "$start_sha" ] && [ -f "$wt/$st/plan-workers/$ns/start_sha" ] && start_sha="$(cat "$wt/$st/plan-workers/$ns/start_sha")"
  [ -z "$start_sha" ] && [ -f "$wt/$st/plan-workers/$ns/dispatch/start_sha" ] && start_sha="$(cat "$wt/$st/plan-workers/$ns/dispatch/start_sha")"
  [ -n "$start_sha" ] || die "无 start_sha(派发包或 --start-sha);无法核写计划边界"
  check_plan_boundary "$wt" "$start_sha"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume)   shift; cmd_resume "$@" ;;
  check-docs) shift; cmd_check_docs "$@" ;;
  plan-dispatch) shift; cmd_plan_dispatch "$@" ;;
  plan-resume)   shift; cmd_plan_resume "$@" ;;
  plan-check)    shift; cmd_plan_check "$@" ;;
  *) die "用法: worker.sh dispatch|resume|check-docs|plan-dispatch|plan-resume|plan-check ..." ;;
esac
