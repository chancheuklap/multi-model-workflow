#!/usr/bin/env bash
# worker.sh —— 写码工人派发(宿主中立入口)
#
#   dispatch  --plan <abs.md> --worktree <abs> [--design ...] [--issue ...] [--base ...] [--model ...] [--effort ...]
#   resume    --worktree <abs> --instructions <abs.md>
#
# 后端:
#   claude → 外挂 codex CLI(原 codex-worker 行为)
#   droid  → 准备 worktree + prompt 包,打印 Task 派发说明(主线程 Task → pack-executor)
#
# 兼容:mmw codex * 仍路由到本脚本。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/host.sh
. "$SCRIPT_DIR/lib/host.sh"

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
CODEX_EFFORT="${CODEX_EFFORT:-xhigh}"
DROID_EXECUTOR_DROID="${DROID_EXECUTOR_DROID:-pack-executor}"
DROID_EXECUTOR_MODEL="${DROID_EXECUTOR_MODEL:-gpt-5.3-codex}"
DROID_EXECUTOR_EFFORT="${DROID_EXECUTOR_EFFORT:-high}"

STATE_SUBDIR="$(mmw_state_subdir)"

die() { echo "ERROR: $*" >&2; exit 2; }

build_prompt() {  # $1=plan $2=worktree $3=design $4=issue
  cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 落地一份计划。
**读你已装的 \`worktree-build\` skill,照它走整个落地流程**(它是总纲,细纪律在它的 references,到那步再读)。

工作树(你唯一可写的源码区): $2
开工前读这几份(worktree 内路径,顺序读):
${3:+- 设计文档(意图/合同边界/发布风险): $3
}${4:+- 你的 issue(What to build / Acceptance / Blocked by): $4
}- 你的计划(实施唯一权威): $1

落地铁律、逐 Pack TDD、每 Pack 提交格式、禁改 docs/、卡住协议、收工回执格式 —— **全在 worktree-build skill,照它做,本消息不重复**。
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

# ---------- Codex CLI backend (Claude host) ----------
record_session() {
  local sid; sid="$(grep -m1 -E '^session id:' "$2" 2>/dev/null | sed 's/^session id:[[:space:]]*//' || true)"
  [ -n "$sid" ] || { echo ""; return; }
  mkdir -p "$1/$STATE_SUBDIR"
  printf '%s\n' "$sid" > "$1/$STATE_SUBDIR/codex-session"
  echo "$sid"
}

run_codex() {
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
  return "$ec"
}

ensure_worktree() {
  local wt="$1" base="$2"
  if [ ! -d "$wt" ]; then
    local bprefix; case "$(mmw_host)" in droid) bprefix=worker ;; *) bprefix=codex ;; esac
    git worktree add -b "$bprefix/$(basename "$wt")" "$wt" "$base" >&2 \
      || die "建 worktree 失败: $wt(分支 $bprefix/$(basename "$wt") 已存在?先清理)"
  fi
  mmw_ensure_wt_state_ignore "$wt"
}

# ---------- Droid Task backend ----------
write_droid_dispatch_pkg() {
  local wt="$1" plan="$2" design="$3" issue="$4" model="$5" effort="$6" mode="$7" instr="${8:-}"
  local pkg="$wt/$STATE_SUBDIR/worker-dispatch"
  mkdir -p "$pkg"
  if [ "$mode" = "dispatch" ]; then
    build_prompt "$plan" "$wt" "$design" "$issue" > "$pkg/prompt.md"
  else
    cp "$instr" "$pkg/prompt.md"
  fi
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
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
META
  printf '%s %s\n' "$model" "$effort" > "$wt/$STATE_SUBDIR/worker-model"
  echo "WORKER_BACKEND=droid-task"
  echo "WORKER_MODE=$mode"
  echo "WORKTREE=$wt"
  echo "PROMPT_FILE=$pkg/prompt.md"
  echo "META_FILE=$pkg/meta.json"
  echo "DROID=$DROID_EXECUTOR_DROID"
  echo "MODEL=$model"
  echo "EFFORT=$effort"
  cat <<EOF
--- droid 派发(主线程照做)---
用 Task 工具派 Custom Droid:
  subagent_type: $DROID_EXECUTOR_DROID
  model 偏好: $model (reasoningEffort=$effort; droid 定义可 inherit 时以 droid 文件为准)
  prompt: 完整读取并执行 $pkg/prompt.md
工作目录必须是 worktree: $wt
完成后主线程亲验(跑测试/读 diff),再 mmw loop step done。
Worker 禁改 docs/;碰了按 DOCS_VIOLATION 打回。
EOF
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
  mkdir -p "$wt/$STATE_SUBDIR"

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
      printf '%s %s\n' "$model" "$effort" > "$wt/$STATE_SUBDIR/codex-model"
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

  case "$(mmw_worker_backend)" in
    droid-task)
      local model="$DROID_EXECUTOR_MODEL" effort="$DROID_EXECUTOR_EFFORT"
      [ -f "$wt/$STATE_SUBDIR/worker-model" ] && read -r model effort < "$wt/$STATE_SUBDIR/worker-model"
      write_droid_dispatch_pkg "$wt" "" "" "" "$model" "$effort" "resume" "$instr"
      return 0
      ;;
    codex-cli)
      local sf="$wt/$STATE_SUBDIR/codex-session"
      [ -f "$sf" ] || record_session "$wt" "$wt/$STATE_SUBDIR/codex-logs/run.log" >/dev/null
      [ -f "$sf" ] || die "无 session 记账($sf,run.log 也捞不到);首派走 dispatch"
      local sid; sid="$(cat "$sf")"
      local model="$CODEX_MODEL" effort="$CODEX_EFFORT"
      [ -f "$wt/$STATE_SUBDIR/codex-model" ] && read -r model effort < "$wt/$STATE_SUBDIR/codex-model"
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

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume)   shift; cmd_resume "$@" ;;
  *) die "用法: worker.sh dispatch|resume ..." ;;
esac
