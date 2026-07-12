#!/usr/bin/env bash
# Droid Task 写码工人和写计划工人派发包。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"

EXECUTOR_DROID="${DROID_EXECUTOR_DROID:-pack-executor}"
EXECUTOR_MODEL="${DROID_EXECUTOR_MODEL:-glm-5.2}"
EXECUTOR_EFFORT="${DROID_EXECUTOR_EFFORT:-max}"
PLAN_DROID="${DROID_PLAN_DROID:-plan-writer}"
PLAN_MODEL="${DROID_PLAN_MODEL:-gpt-5.6-terra}"
PLAN_EFFORT="${DROID_PLAN_EFFORT:-xhigh}"

die() { echo "ERROR: $*" >&2; exit 2; }
state_for() { mmw_resolve_state_subdir "$1"; }
plan_ns() { basename "$1" .md; }

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
  local file="$1" mode="$2" droid="$3" model="$4" effort="$5" wt="$6" prompt="$7" start_sha="$8" plan="$9"
  cat > "$file" <<META
{
  "backend": "droid-task",
  "mode": "$mode",
  "droid": "$droid",
  "model": "$model",
  "reasoning_effort": "$effort",
  "worktree": "$wt",
  "plan": "$plan",
  "prompt_file": "$prompt",
  "start_sha": "$start_sha",
  "task_id": null,
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
META
}

print_dispatch() {
  local label="$1" droid="$2" prompt="$3" wt="$4" model="$5" effort="$6" record_cmd="$7" check_cmd="$8"
  cat <<EOF
--- $label ---
用 Task 派 Custom Droid:
  subagent_type:$droid
  description:3-5 个词的任务标签
  prompt:完整读取并执行 $prompt
  独立任务优先 run_in_background=true;工作目录必须是 $wt
  droid 文件已固定 model=$model,reasoningEffort=$effort
Task 返回 task_id 后立即记账:
  $record_cmd
完成后先取 TaskOutput,再运行:
  $check_cmd
机器边界检查通过后,主线程才可亲验 diff、提交、测试并推进 loop。
EOF
}

cmd_dispatch() {
  local plan="" wt="" base="HEAD" design="" issue="" model="$EXECUTOR_MODEL" effort="$EXECUTOR_EFFORT"
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
  ensure_worktree "$wt" "$base" "$repo"
  local st pkg start prompt meta
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  mkdir -p "$pkg"
  start="$(git -C "$wt" rev-parse HEAD)"
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  build_prompt "$plan" "$wt" "$design" "$issue" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" dispatch "$EXECUTOR_DROID" "$model" "$effort" "$wt" "$prompt" "$start" "$plan"
  echo "WORKER_BACKEND=droid-task"
  echo "PROMPT_FILE=$prompt"
  echo "META_FILE=$meta"
  print_dispatch "Droid 写码派发" "$EXECUTOR_DROID" "$prompt" "$wt" "$model" "$effort" \
    "mmw worker task-record --worktree \"$wt\" --task-id <task_id>" \
    "mmw worker check-docs --worktree \"$wt\""
}

cmd_resume() {
  local wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -d "$wt" ] || die "worktree 不存在:$wt"
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  local st pkg task_id
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  task_id="$(jq -r '.task_id // empty' "$pkg/meta.json" 2>/dev/null || true)"
  cp "$instr" "$pkg/resume-prompt.md"
  if [ -n "$task_id" ]; then
    cat <<EOF
用 Task 的 resume=$task_id 续接原 pack-executor,follow-up prompt 完整读取 $pkg/resume-prompt.md。
完成后先取 TaskOutput,再运行:mmw worker check-docs --worktree "$wt"
EOF
  else
    echo "WARNING: 原派发没有 task_id,需新派 pack-executor 并在派发后 task-record。" >&2
    print_dispatch "Droid 写码重派" "$EXECUTOR_DROID" "$pkg/resume-prompt.md" "$wt" "$EXECUTOR_MODEL" "$EXECUTOR_EFFORT" \
      "mmw worker task-record --worktree \"$wt\" --task-id <task_id>" \
      "mmw worker check-docs --worktree \"$wt\""
  fi
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
  local st ns pkg start prompt meta
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  mkdir -p "$pkg"
  start="$(git -C "$wt" rev-parse HEAD)"
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  build_plan_prompt "$plan" "$wt" "$design" "$issue" "$mockup" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" dispatch "$PLAN_DROID" "$model" "$effort" "$wt" "$prompt" "$start" "$plan"
  echo "WORKER_BACKEND=droid-task"
  echo "PLAN_WORKER_NS=$ns"
  echo "PROMPT_FILE=$prompt"
  print_dispatch "Droid 写计划派发" "$PLAN_DROID" "$prompt" "$wt" "$model" "$effort" \
    "mmw worker task-record --worktree \"$wt\" --plan \"$plan\" --task-id <task_id>" \
    "mmw worker plan-check --plan \"$plan\" --worktree \"$wt\""
}

cmd_plan_resume() {
  local plan="" wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  local st ns pkg task_id
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  task_id="$(jq -r '.task_id // empty' "$pkg/meta.json" 2>/dev/null || true)"
  cp "$instr" "$pkg/resume-prompt.md"
  if [ -n "$task_id" ]; then
    cat <<EOF
用 Task 的 resume=$task_id 续接原 plan-writer,follow-up prompt 完整读取 $pkg/resume-prompt.md。
完成后先取 TaskOutput,再运行:mmw worker plan-check --plan "$plan" --worktree "$wt"
EOF
  else
    echo "WARNING: 原派发没有 task_id,需新派 plan-writer 并在派发后 task-record。" >&2
    print_dispatch "Droid 写计划重派" "$PLAN_DROID" "$pkg/resume-prompt.md" "$wt" "$PLAN_MODEL" "$PLAN_EFFORT" \
      "mmw worker task-record --worktree \"$wt\" --plan \"$plan\" --task-id <task_id>" \
      "mmw worker plan-check --plan \"$plan\" --worktree \"$wt\""
  fi
}

cmd_task_record() {
  local wt="" plan="" task_id=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --plan) plan="$2"; shift 2 ;;
    --task-id) task_id="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -n "$wt" ] && [ -n "$task_id" ] || die "--worktree 与 --task-id 必填"
  local st meta tmp
  st="$(state_for "$wt")"
  if [ -n "$plan" ]; then
    meta="$wt/$st/plan-workers/$(plan_ns "$plan")/dispatch/meta.json"
  else
    meta="$wt/$st/worker-dispatch/meta.json"
  fi
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  tmp="${meta}.tmp"
  jq --arg id "$task_id" '.task_id=$id' "$meta" > "$tmp" && mv "$tmp" "$meta"
  echo "TASK_RECORDED=$task_id"
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
  task-record) shift; cmd_task_record "$@" ;;
  *) die "用法:worker.sh dispatch|resume|check-docs|plan-dispatch|plan-resume|plan-check|task-record ..." ;;
esac
