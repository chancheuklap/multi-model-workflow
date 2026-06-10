#!/usr/bin/env bash
# C1/C3/C4: Codex 执行者派发包装 —— execution 阶段 Plan 落地的唯一派发通道。
#
# 设计：Coordinator 用 Bash(run_in_background: true) 跑本脚本；脚本在后台 Bash
# 内**同步**驱动 codex exec，退出后由同一进程完成 plan-return ingest + NEXT
# 输出（落在后台任务输出里，Coordinator 收完成通知即读）。回收不依赖 hook
# 时序——比 PostToolUse 更确定（后台 Bash 的 PostToolUse 在任务启动时就触发，
# 看不到最终输出）。
#
# 子命令：
#   dispatch  首派 / need-fresh-worker 续派（新 session）
#   resume    修复轮续会话（codex exec resume <session_id>，C4）
#
# 模型分层（2026-06-10 拍板）：complex tier → gpt-5.5 xhigh；standard → gpt-5.4 xhigh。
# 沙箱（B2/C1）：-C <worktree> + --sandbox workspace-write 物理围栏；
# --add-dir <主树状态目录> 放行 plan-return / pack-returns / state.sh 上报通道。
# docs/ 不受沙箱细分保护 → 合并前 `git diff -- docs/` 检查兜底（C6，回收步执行）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/state.sh"
VALIDATE_DISPATCH="$SCRIPT_DIR/../hooks/validate-plan-dispatch.sh"
STATE_BASE="${STATE_BASE:-.claude/multi-model-workflow}"
CODEX_BIN="${CODEX_BIN:-codex}"

# 模型分层常量（唯一权威源；SKILL/handbook 不重复声明具体型号）
CODEX_MODEL_COMPLEX="${CODEX_MODEL_COMPLEX:-gpt-5.5}"
CODEX_MODEL_STANDARD="${CODEX_MODEL_STANDARD:-gpt-5.4}"
CODEX_EFFORT="${CODEX_EFFORT:-xhigh}"

usage() {
  cat <<'USAGE'
Usage:
  codex-worker.sh dispatch --run-id <id> --plan-id <NNN> --plan-path <abs.md> \
      --worktree-path <abs> [--branch <name>] [--model-tier standard|complex] \
      [--resume-from-pack-id <N.M>]
  codex-worker.sh resume --run-id <id> --plan-id <NNN> --repair-round <n> \
      --disposition-refs '<json-array>' --instructions-file <abs.md>
USAGE
  exit 2
}

MAIN_TREE="$(pwd)"
ABS_STATE_DIR="$MAIN_TREE/$STATE_BASE"

emit_next_by_verdict() {
  # 与 agent-return-handler.sh plan-level 路由语义一致；reviewer 按 C5 翻转为 Claude。
  local plan_id="$1" verdict="$2"
  case "$verdict" in
    pass)
      echo "[multi-model-workflow] NEXT: Plan ${plan_id} verdict=pass. Dispatch Plan Implementation Review（C5：Claude 审 Codex 产出，复用 review 模板与 disposition 流程）。Review pass 后 state.sh checkbox toggle + execution-plan finish --status completed。" ;;
    partial-pass)
      echo "[multi-model-workflow] NEXT: Plan ${plan_id} verdict=partial-pass. 读 plan-return per_pack blocked reason + open-items.json；committed packs 进 Claude Plan Implementation Review；blocked packs 走处置（resume 修复 / isolated）。" ;;
    blocked)
      echo "[multi-model-workflow] BLOCKED: Plan ${plan_id} verdict=blocked. 读 per_pack[].reason + open-items.json；并行批次内其余 Plan 不受影响——本 Plan execution-plan finish --status isolated，按需单独回退串行重试。" ;;
    need-fresh-worker)
      echo "[multi-model-workflow] NEXT: Plan ${plan_id} verdict=need-fresh-worker（session 累积）。用 codex-worker.sh dispatch 开新 session（带 --resume-from-pack-id），新 worker 读 execution-state 自动跳过 committed packs。" ;;
    needs-context)
      echo "[multi-model-workflow] NEXT: Plan ${plan_id} verdict=needs-context. 补齐 Contract anchors / Mockup specs / verification 后重新 dispatch。" ;;
    needs-plan-revision)
      echo "[multi-model-workflow] NEXT: Plan ${plan_id} verdict=needs-plan-revision（plan 缺必备字段或与 source issue 意图冲突）。回 plan-writing 修订，re-review 后重新 dispatch。" ;;
    *)
      echo "[multi-model-workflow] BLOCKED: Plan ${plan_id} unknown verdict '${verdict}'. Inspect plan-return.json." ;;
  esac
}

run_codex_and_ingest() {
  # $1=plan_id $2=round $3=prompt_file $4..=codex args（不含 stdin 重定向）
  local plan_id="$1" round="$2" prompt_file="$3"; shift 3

  local log_dir="$ABS_STATE_DIR/codex-logs/$RUN_ID"
  mkdir -p "$log_dir"
  local log="$log_dir/${plan_id}-r${round}.log"
  local last_msg="$log_dir/${plan_id}-r${round}-last.md"

  # 同步驱动 codex（本脚本整体运行于 Coordinator 的后台 Bash 内）
  set +e
  "$CODEX_BIN" "$@" -o "$last_msg" - < "$prompt_file" > "$log" 2>&1
  local codex_exit=$?
  set -e

  # session id 记账（C4 resume 依据）——header 格式 `session id: <uuid>`
  local session_id
  session_id=$(grep -m1 -E '^session id:' "$log" 2>/dev/null | sed 's/^session id:[[:space:]]*//' || true)
  if [[ -n "$session_id" ]]; then
    bash "$STATE_SH" execution-plan session --run-id "$RUN_ID" \
      --plan-id "$plan_id" --session-id "$session_id" 2>/dev/null || true
  fi

  echo "=== codex exit=${codex_exit} session=${session_id:-unknown} log=${log} ==="
  echo "--- last message ---"
  cat "$last_msg" 2>/dev/null || echo "(no last message file)"
  echo "--------------------"

  # C3: 同进程回收 —— ingest plan-return（Worker 上报的 per_pack.commit_sha 整值
  # 合并回填 execution-state，覆盖 track hook 在主树取错的 fallback SHA，B4）
  local pr_file="$ABS_STATE_DIR/plan-returns/$RUN_ID/$plan_id/plan-return.json"
  if [[ ! -f "$pr_file" ]]; then
    echo "[multi-model-workflow] BLOCKED: Plan ${plan_id} worker 退出（exit=${codex_exit}）但未写 plan-return.json（期望 ${pr_file}）。读上方 last message + ${log} 排障；视情况 resume 或 isolated。"
    return 0
  fi
  if ! STATE_BASE="$ABS_STATE_DIR" bash "$STATE_SH" plan-returns ingest \
      --run-id "$RUN_ID" --plan-id "$plan_id" 2>&1; then
    echo "[multi-model-workflow] BLOCKED: Plan ${plan_id} plan-return ingest 失败（schema 不合规？）。人工核 ${pr_file}。"
    return 0
  fi

  local verdict
  verdict=$(jq -r '.verdict // "unknown"' "$pr_file")
  echo "⚠️ 写入交付物前必须校验本次返回的事实声明（行号 / 计数 / 存在性 / 引用关系）"
  emit_next_by_verdict "$plan_id" "$verdict"
}

cmd_dispatch() {
  local plan_id="" plan_path="" worktree_path="" branch="" model_tier="standard"
  local resume_from=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --plan-path) plan_path="$2"; shift 2 ;;
      --worktree-path) worktree_path="$2"; shift 2 ;;
      --branch) branch="$2"; shift 2 ;;
      --model-tier) model_tier="$2"; shift 2 ;;
      --resume-from-pack-id) resume_from="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  [[ -z "$plan_id" || -z "$plan_path" || -z "$worktree_path" ]] && usage
  if [[ ! -f "$plan_path" ]]; then
    echo "Error: plan file not found: $plan_path" >&2; exit 2
  fi
  if [[ ! -d "$worktree_path" ]]; then
    echo "Error: worktree not found: $worktree_path（须先 git worktree add <path> HEAD）" >&2; exit 2
  fi

  local model agent_role
  case "$model_tier" in
    complex)  model="$CODEX_MODEL_COMPLEX";  agent_role="complex-pack-executor" ;;
    standard) model="$CODEX_MODEL_STANDARD"; agent_role="pack-executor" ;;
    *) echo "Error: --model-tier must be standard|complex" >&2; exit 2 ;;
  esac

  # 1. envelope（A3 生成器；plan-level key；含 worktree_path / plan_path）
  local extra=()
  [[ -n "$resume_from" ]] && extra+=(--resume-from-pack-id "$resume_from")
  local envelope_block
  envelope_block=$(bash "$STATE_SH" envelope build --run-id "$RUN_ID" \
    --phase execution --agent-role "$agent_role" --plan-id "$plan_id" \
    --plan-path "$plan_path" --worktree-path "$worktree_path" \
    ${extra[@]+"${extra[@]}"})

  # 2. 派工 prompt（envelope + Codex worker 头部；纪律细则在 handbook）
  local prompt_dir="$ABS_STATE_DIR/dispatch-prompts/$RUN_ID"
  mkdir -p "$prompt_dir"
  local prompt_file="$prompt_dir/${plan_id}-r0.md"
  local handbook="${CLAUDE_PLUGIN_ROOT:-$SCRIPT_DIR/..}/skills/orchestrate-execution/references/codex-worker-handbook.md"
  cat > "$prompt_file" <<PROMPT
$envelope_block

你是 plan-level autonomous worker（Codex）。先完整读 handbook，再按其 Worker Loop 执行整个 Plan。

- Handbook（行为规范，必读）：$handbook
- Plan 文件：$plan_path
- Run ID：$RUN_ID
- 工作树（你的唯一源码写入区）：$worktree_path
- 状态目录（绝对路径；所有 state.sh 调用前缀 STATE_BASE="$ABS_STATE_DIR"）：$ABS_STATE_DIR
- state.sh 绝对路径（handbook 中的 state.sh / <plugin>/scripts/state.sh 一律指它）：$STATE_SH
- plan-return 写入路径：$ABS_STATE_DIR/plan-returns/$RUN_ID/$plan_id/plan-return.json

路径纪律：所有文件操作以工作树 $worktree_path 为根解析；除状态目录外不得写其外任何路径；禁改任何 docs/ 下文件（合并前有 diff 检查）。
PROMPT

  # 3. 派发前校验（复用 validate-plan-dispatch：plan_id/plan_path/manifest/budget/
  #    idempotency，校验通过即追加 idempotency key）
  if ! jq -n --rawfile p "$prompt_file" '{tool_input:{prompt:$p}}' \
      | bash "$VALIDATE_DISPATCH"; then
    echo "Error: dispatch validation failed（见上方 BLOCKED 原因）" >&2
    exit 2
  fi

  # 4. per-plan marker（B3：守卫据此知道飞行中 + 登记 worktree）
  printf '%s\n' "$worktree_path" > "$STATE_BASE/worker-active-${plan_id}"

  # 5. 驱动 codex + 同进程回收
  run_codex_and_ingest "$plan_id" 0 "$prompt_file" \
    exec -C "$worktree_path" --sandbox workspace-write \
    --add-dir "$ABS_STATE_DIR" \
    -m "$model" -c "model_reasoning_effort=\"$CODEX_EFFORT\""
}

cmd_resume() {
  local plan_id="" repair_round="" disposition_refs="" instructions_file=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --repair-round) repair_round="$2"; shift 2 ;;
      --disposition-refs) disposition_refs="$2"; shift 2 ;;
      --instructions-file) instructions_file="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  [[ -z "$plan_id" || -z "$repair_round" || -z "$instructions_file" ]] && usage
  if [[ ! -f "$instructions_file" ]]; then
    echo "Error: instructions file not found: $instructions_file" >&2; exit 2
  fi

  local esf="$STATE_BASE/execution-state-${RUN_ID}.json"
  local session_id worktree_path
  session_id=$(jq -r --arg pid "$plan_id" '.plans[$pid].session_id // empty' "$esf" 2>/dev/null)
  worktree_path=$(jq -r --arg pid "$plan_id" '.plans[$pid].worktree_path // empty' "$esf" 2>/dev/null)
  if [[ -z "$session_id" ]]; then
    echo "Error: no session_id for plan $plan_id（首派未记账？需走 dispatch 新 session）" >&2
    exit 2
  fi

  # 修复轮 envelope（repair_round>=1 强制 disposition_refs，生成器校验）
  local envelope_block
  envelope_block=$(bash "$STATE_SH" envelope build --run-id "$RUN_ID" \
    --phase execution --agent-role pack-executor --plan-id "$plan_id" \
    --repair-round "$repair_round" --disposition-refs "$disposition_refs" \
    ${worktree_path:+--worktree-path "$worktree_path"})

  local prompt_dir="$ABS_STATE_DIR/dispatch-prompts/$RUN_ID"
  mkdir -p "$prompt_dir"
  local prompt_file="$prompt_dir/${plan_id}-r${repair_round}.md"
  {
    echo "$envelope_block"
    echo ""
    echo "Repair Mode（round=${repair_round}）：按 disposition_refs 逐 finding 修复，每 finding 独立 commit（Pack N.M: ... — repair: <摘要>），修完重写 plan-return.json（附 repair_round 元数据）。"
    echo ""
    cat "$instructions_file"
  } > "$prompt_file"

  run_codex_and_ingest "$plan_id" "$repair_round" "$prompt_file" \
    exec resume "$session_id"
}

if [[ $# -lt 1 ]]; then usage; fi
SUBCMD="$1"; shift
RUN_ID=""
REMAINING=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) REMAINING+=("$1"); shift ;;
  esac
done
set -- ${REMAINING[@]+"${REMAINING[@]}"}
if [[ -z "$RUN_ID" ]]; then echo "Error: --run-id required" >&2; exit 2; fi

case "$SUBCMD" in
  dispatch) cmd_dispatch "$@" ;;
  resume) cmd_resume "$@" ;;
  *) usage ;;
esac
