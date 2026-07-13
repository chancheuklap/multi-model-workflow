#!/usr/bin/env bash
# Droid exec 写码工人和写计划工人派发器。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"

EXECUTOR_DROID="${DROID_EXECUTOR_DROID:-pack-executor}"
EXECUTOR_MODEL="${DROID_EXECUTOR_MODEL:-glm-5.2}"
EXECUTOR_EFFORT="${DROID_EXECUTOR_EFFORT:-max}"
CAPABLE_EXECUTOR_DROID="${DROID_CAPABLE_EXECUTOR_DROID:-pack-executor-capable}"
CAPABLE_EXECUTOR_MODEL="${DROID_CAPABLE_EXECUTOR_MODEL:-gemini-3.1-pro-preview}"
CAPABLE_EXECUTOR_EFFORT="${DROID_CAPABLE_EXECUTOR_EFFORT:-high}"
PLAN_DROID="${DROID_PLAN_DROID:-plan-writer}"
PLAN_MODEL="${DROID_PLAN_MODEL:-gpt-5.6-terra}"
PLAN_EFFORT="${DROID_PLAN_EFFORT:-xhigh}"

die() { echo "ERROR: $*" >&2; exit 2; }
state_for() { mmw_resolve_state_subdir "$1"; }
plan_ns() { basename "$1" .md; }

render_droid_prompt() {
  local source="$1" target="$2"
  awk 'BEGIN{n=0} /^---[[:space:]]*$/{n++; next} n>=2{print}' "$source" >"$target"
  [ -s "$target" ] || die "droid prompt 为空:$source"
}

ensure_worktree() {
  local wt="$1" base="$2" repo="$3"
  if [ ! -d "$wt" ]; then
    git -C "$repo" worktree add -b "$(mmw_worker_branch_prefix)/$(basename "$wt")" "$wt" "$base" >&2 \
      || die "建 worktree 失败: $wt"
  fi
  mmw_ensure_wt_state_ignore "$wt"
}

build_prompt() {
  local plan="$1" wt="$2" design="$3" issue="$4"
  local skill; skill="$(mmw_plugin_root)/skills/worktree-build"
  cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 落地一份计划。
先读 Droid plugin 内 worktree-build skill 并严格执行:$skill/SKILL.md

工作树(你唯一可写的源码区):$wt
开工前依次读:
${design:+- 设计文档:$design
}${issue:+- 负责的 issue:$issue
}- 实施计划:$plan

逐 Task Pack TDD、每 Pack 提交、禁改 docs/、卡住协议和 Return Contract 全按 worktree-build skill。不要向用户提问;缺输入时在最终回执中结构化报告。
PROMPT
}

build_plan_prompt() {
  local plan="$1" wt="$2" design="$3" issue="$4" mockup="$5"
  local skill; skill="$(mmw_plugin_root)/skills/worktree-plan"
  cat <<PROMPT
你是计划撰写者,被主线程派进任务 worktree 把一个大 issue 写成一份实施计划。
先读 Droid plugin 内 worktree-plan skill 并严格执行:$skill/SKILL.md

任务工作树:$wt
唯一 plan 落点:$plan
开工前依次读:
${design:+- 源设计文档:$design
}${issue:+- 负责的大 issue:$issue
}${mockup:+- mockup 目录:$mockup
}
只准写该 plan 与对应 issue 的 Small issues。禁止改源码、docs/design 或其他 plan,禁止 commit。不要向用户提问;缺输入时在最终回执中结构化报告。
PROMPT
}

check_docs_boundary() {
  local wt="$1" start_sha="$2" touched
  touched="$( {
    git -C "$wt" diff --name-only "$start_sha" HEAD 2>/dev/null || true
    git -C "$wt" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'
  } | grep '^docs/' | sort -u || true )"
  [ -z "$touched" ] && return 0
  echo "DOCS_VIOLATION: Worker 改了 docs/:" >&2
  printf '%s\n' "$touched" | sed 's/^/  /' >&2
  return 3
}

check_plan_boundary() {
  local wt="$1" start_sha="$2" touched offending
  touched="$( {
    git -C "$wt" diff --name-only "$start_sha" HEAD 2>/dev/null || true
    git -C "$wt" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'
  } | sort -u | grep -v '^[[:space:]]*$' || true )"
  offending="$(printf '%s\n' "$touched" | grep -vE '^docs/(plans|issues)/' | grep -v '^[[:space:]]*$' || true)"
  [ -z "$offending" ] && return 0
  echo "PLAN_VIOLATION: 计划工人越界:" >&2
  printf '%s\n' "$offending" | sed 's/^/  /' >&2
  return 3
}

write_meta() {
  local file="$1" mode="$2" droid="$3" model="$4" effort="$5" wt="$6" prompt="$7" start_sha="$8" plan="$9" system_prompt="${10}"
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")" || return 1
  jq -n \
    --arg backend droid-exec --arg mode "$mode" --arg droid "$droid" \
    --arg model "$model" --arg effort "$effort" --arg wt "$wt" \
    --arg plan "$plan" --arg prompt "$prompt" --arg start "$start_sha" \
    --arg system "$system_prompt" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{backend:$backend,mode:$mode,droid:$droid,model:$model,reasoning_effort:$effort,
      worktree:$wt,plan:$plan,prompt_file:$prompt,system_prompt_file:$system,start_sha:$start,
      status:"prepared",pid:null,session_id:null,result_file:null,log_file:null,
      created_at:$at,updated_at:$at}' >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

update_meta() {
  local meta="$1"; shift
  local tmp
  tmp="$(mktemp "$(dirname "$meta")/.meta.XXXXXX")" || return 1
  jq "$@" "$meta" >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$meta" \
    || { rm -f "$tmp"; return 1; }
}

launch_exec() {
  local meta="$1" prompt="$2" wt="$3" model="$4" effort="$5" system_prompt="$6" session_id="${7:-}" status_cmd="$8"
  command -v droid >/dev/null 2>&1 || die "找不到 droid CLI"
  local pkg result log pid
  pkg="$(dirname "$meta")"
  result="$pkg/result.json"
  log="$pkg/run.log"
  rm -f "$result" "$log"
  local -a cmd=(droid exec --output-format json --auto high --cwd "$wt"
    --model "$model" --reasoning-effort "$effort"
    --append-system-prompt-file "$system_prompt")
  [ -n "$session_id" ] && cmd+=(--session-id "$session_id")
  cmd+=(--file "$prompt")
  nohup "${cmd[@]}" >"$result" 2>"$log" </dev/null &
  pid=$!
  if ! update_meta "$meta" \
    --argjson pid "$pid" --arg result "$result" --arg log "$log" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="running" | .pid=$pid | .result_file=$result | .log_file=$log | .updated_at=$at'; then
    kill "$pid" 2>/dev/null || true
    die "worker 已停止：派发账本写入失败"
  fi
  echo "WORKER_STARTED"
  echo "pid=$pid"
  echo "result_file=$result"
  echo "log_file=$log"
  echo "NEXT=$status_cmd"
}

refresh_meta() {
  local meta="$1" pid result status session subtype
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  pid="$(jq -r '.pid // empty' "$meta")"
  result="$(jq -r '.result_file // empty' "$meta")"
  status="$(jq -r '.status // "prepared"' "$meta")"
  if [ -z "$result" ] || [ ! -s "$result" ] || ! jq -e . "$result" >/dev/null 2>&1; then
    if [ "$status" = running ] && [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo RUNNING
      return 0
    fi
    update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="failed" | .updated_at=$at'
    echo FAILED
    return 1
  fi
  subtype="$(jq -r '.subtype // empty' "$result")"
  session="$(jq -r '.session_id // empty' "$result")"
  if [ "$subtype" = success ] && [ "$(jq -r '.is_error // false' "$result")" = false ] && [ -n "$session" ]; then
    update_meta "$meta" --arg session "$session" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="completed" | .session_id=$session | .updated_at=$at'
    echo COMPLETED
    return 0
  fi
  update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="failed" | .updated_at=$at'
  echo FAILED
  return 1
}

guard_no_active() {
  local meta="$1" state
  [ -f "$meta" ] || return 0
  state="$(refresh_meta "$meta" 2>/dev/null || true)"
  case "$state" in
    RUNNING) die "已有 worker 正在运行:$meta" ;;
    COMPLETED) die "已有成功 worker；需要补改请用 resume:$meta" ;;
  esac
}

cmd_dispatch() {
  local plan="" wt="" base="HEAD" design="" issue="" model="" effort=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;; --issue) issue="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;; --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -f "$plan" ] || die "plan 文件不存在:$plan"
  [ -n "$wt" ] || die "--worktree 必填"
  local repo; repo="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel 2>/dev/null)" ||
    die "plan 不在 git 仓库内:$plan"
  local droid="$EXECUTOR_DROID" default_model="$EXECUTOR_MODEL" default_effort="$EXECUTOR_EFFORT"
  if grep -qiE '(complexity|复杂度).*capable' "$plan" 2>/dev/null; then
    droid="$CAPABLE_EXECUTOR_DROID"
    default_model="$CAPABLE_EXECUTOR_MODEL"
    default_effort="$CAPABLE_EXECUTOR_EFFORT"
  fi
  [ -n "$model" ] || model="$default_model"
  [ -n "$effort" ] || effort="$default_effort"
  ensure_worktree "$wt" "$base" "$repo"
  local st pkg start prompt meta system_prompt system_source
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  mkdir -p "$pkg"
  start="$(git -C "$wt" rev-parse HEAD)"
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  guard_no_active "$meta"
  system_source="$(mmw_plugin_root)/droids/$droid.md"
  [ -f "$system_source" ] || die "找不到 executor droid:$system_source"
  system_prompt="$pkg/system-prompt.md"
  render_droid_prompt "$system_source" "$system_prompt"
  build_prompt "$plan" "$wt" "$design" "$issue" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" dispatch "$droid" "$model" "$effort" "$wt" "$prompt" "$start" "$plan" "$system_prompt"
  echo "WORKER_BACKEND=droid-exec"
  echo "DROID=$droid"
  echo "MODEL=$model"
  echo "REASONING_EFFORT=$effort"
  echo "PROMPT_FILE=$prompt"
  echo "META_FILE=$meta"
  launch_exec "$meta" "$prompt" "$wt" "$model" "$effort" "$system_prompt" "" \
    "mmw worker status --worktree \"$wt\""
}

cmd_resume() {
  local wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -d "$wt" ] || die "worktree 不存在:$wt"
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  local st pkg meta state session model effort system_prompt
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  meta="$pkg/meta.json"
  state="$(refresh_meta "$meta" 2>/dev/null || true)"
  [ "$state" != RUNNING ] || die "原 worker 仍在运行"
  session="$(jq -r '.session_id // empty' "$meta")"
  model="$(jq -r .model "$meta")"
  effort="$(jq -r .reasoning_effort "$meta")"
  system_prompt="$(jq -r .system_prompt_file "$meta")"
  [ -n "$session" ] || die "无成功 session_id,不能续接；先看 $(jq -r '.log_file // empty' "$meta")"
  cp "$instr" "$pkg/resume-prompt.md"
  launch_exec "$meta" "$pkg/resume-prompt.md" "$wt" "$model" "$effort" "$system_prompt" "$session" \
    "mmw worker status --worktree \"$wt\""
}

cmd_plan_dispatch() {
  local plan="" wt="" design="" issue="" mockup="" model="$PLAN_MODEL" effort="$PLAN_EFFORT"
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;; --issue) issue="$2"; shift 2 ;;
    --mockup) mockup="$2"; shift 2 ;; --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  case "$plan" in /*) ;; *) die "--plan 必须绝对路径" ;; esac
  [ -d "$wt" ] || die "任务 worktree 不存在:$wt"
  mmw_ensure_wt_state_ignore "$wt"
  local st ns pkg start prompt meta system_prompt system_source
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  mkdir -p "$pkg"
  start="$(git -C "$wt" rev-parse HEAD)"
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  guard_no_active "$meta"
  system_source="$(mmw_plugin_root)/droids/$PLAN_DROID.md"
  [ -f "$system_source" ] || die "找不到 plan writer droid:$system_source"
  system_prompt="$pkg/system-prompt.md"
  render_droid_prompt "$system_source" "$system_prompt"
  build_plan_prompt "$plan" "$wt" "$design" "$issue" "$mockup" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" dispatch "$PLAN_DROID" "$model" "$effort" "$wt" "$prompt" "$start" "$plan" "$system_prompt"
  echo "WORKER_BACKEND=droid-exec"
  echo "PLAN_WORKER_NS=$ns"
  echo "DROID=$PLAN_DROID"
  echo "MODEL=$model"
  echo "REASONING_EFFORT=$effort"
  echo "PROMPT_FILE=$prompt"
  launch_exec "$meta" "$prompt" "$wt" "$model" "$effort" "$system_prompt" "" \
    "mmw worker status --plan \"$plan\" --worktree \"$wt\""
}

cmd_plan_resume() {
  local plan="" wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  local st ns pkg meta state session model effort system_prompt
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  meta="$pkg/meta.json"
  state="$(refresh_meta "$meta" 2>/dev/null || true)"
  [ "$state" != RUNNING ] || die "原 plan writer 仍在运行"
  session="$(jq -r '.session_id // empty' "$meta")"
  model="$(jq -r .model "$meta")"
  effort="$(jq -r .reasoning_effort "$meta")"
  system_prompt="$(jq -r .system_prompt_file "$meta")"
  [ -n "$session" ] || die "无成功 session_id,不能续接；先看 $(jq -r '.log_file // empty' "$meta")"
  cp "$instr" "$pkg/resume-prompt.md"
  launch_exec "$meta" "$pkg/resume-prompt.md" "$wt" "$model" "$effort" "$system_prompt" "$session" \
    "mmw worker status --plan \"$plan\" --worktree \"$wt\""
}

cmd_status() {
  local wt="" plan=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --plan) plan="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -n "$wt" ] || die "--worktree 必填"
  local st meta state result log session start
  st="$(state_for "$wt")"
  if [ -n "$plan" ]; then
    meta="$wt/$st/plan-workers/$(plan_ns "$plan")/dispatch/meta.json"
  else
    meta="$wt/$st/worker-dispatch/meta.json"
  fi
  state="$(refresh_meta "$meta")" || true
  result="$(jq -r '.result_file // empty' "$meta")"
  log="$(jq -r '.log_file // empty' "$meta")"
  session="$(jq -r '.session_id // empty' "$meta")"
  echo "WORKER_STATUS=$state"
  echo "META_FILE=$meta"
  echo "SESSION_ID=${session:-none}"
  echo "RESULT_FILE=${result:-none}"
  echo "LOG_FILE=${log:-none}"
  [ "$state" = COMPLETED ] || return 1
  if [ -n "$plan" ]; then
    start="$(jq -r '.start_sha' "$meta")"
    check_plan_boundary "$wt" "$start" || return 3
  else
    start="$(jq -r '.start_sha' "$meta")"
    check_docs_boundary "$wt" "$start" || return 3
  fi
  echo "--- Droid 最后消息 ---"
  jq -r '.result // "(无结果)"' "$result"
}

cmd_check_docs() {
  local wt="" start=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --start-sha) start="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  local st; st="$(state_for "$wt")"
  [ -n "$start" ] || start="$(cat "$wt/$st/worker-dispatch/start_sha" 2>/dev/null || true)"
  [ -n "$start" ] || die "无 start_sha"
  check_docs_boundary "$wt" "$start"
}

cmd_plan_check() {
  local plan="" wt="" start=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --start-sha) start="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  local st ns; st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"
  [ -n "$start" ] || start="$(cat "$wt/$st/plan-workers/$ns/dispatch/start_sha" 2>/dev/null || true)"
  [ -n "$start" ] || die "无 start_sha"
  check_plan_boundary "$wt" "$start"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume) shift; cmd_resume "$@" ;;
  check-docs) shift; cmd_check_docs "$@" ;;
  plan-dispatch) shift; cmd_plan_dispatch "$@" ;;
  plan-resume) shift; cmd_plan_resume "$@" ;;
  plan-check) shift; cmd_plan_check "$@" ;;
  status) shift; cmd_status "$@" ;;
  *) die "用法:worker.sh dispatch|resume|check-docs|plan-dispatch|plan-resume|plan-check|status ..." ;;
esac
