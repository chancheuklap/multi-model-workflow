#!/usr/bin/env bash
# PreToolUse Bash hook (if: "Bash(*codex*task*)")
# 轮次截断机器强制 — 拦截超过 repair_policy.max_repair_rounds 的 Targeted Re-Review 派发。
#
# 机制：每轮 repair 闭环必含一次 Targeted Re-Review（codex-companion task 派发）。
# hook 从 gate 名（plan-impl-review-N-repair-<round> / plan-review-repair-<round>）或
# execution-state plans[N].repair_round 读取当前轮次，与 routes-v1.json 的
# repair_policy.max_repair_rounds 比较，超限即 exit 2 拦截。
#
# fail-open 硬要求：任何解析失败 / routes 不可读 / 非 re-review 派发 → exit 0 放行。
# 不因 hook 自身问题卡死正常流程。
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"
ROUTES_JSON="$SCRIPT_DIR/../state-schema/routes-v1.json"

# ── 1. 只处理 codex-companion.*task 命令（与 gate-codex-review.sh 同触发面）──
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)
if [[ -z "$COMMAND" ]]; then exit 0; fi
if ! echo "$COMMAND" | grep -qE '(codex-companion|CODEX_SCRIPT).*[[:space:]]task([[:space:]]|$)'; then exit 0; fi

# ── 2. 提取 --prompt-file ──
PROMPT_FILE=$(echo "$COMMAND" | sed -n 's/.*--prompt-file[[:space:]]*\([^[:space:]]*\).*/\1/p')
if [[ -z "$PROMPT_FILE" || ! -f "$PROMPT_FILE" ]]; then exit 0; fi  # fail-open: gate-codex-review.sh 会挡无效文件

# ── 3. 解析 DISPATCH_ENVELOPE（fail-open：解析失败放行） ──
ENVELOPE=$(bash "$PARSE_ENVELOPE" "$PROMPT_FILE" 2>/dev/null) || { exit 0; }
if [[ -z "$ENVELOPE" ]]; then exit 0; fi

# ── 4. 从 gate 名识别是否是 Targeted Re-Review 派发 + 提取 round ──
# gate 名来自 envelope 的 gate 字段（baseline review prompt 文件名）
# 或 prompt_file 文件名。两种格式：
#   plan-impl-review-N-repair-<round>   (execution phase)
#   plan-review-repair-<round>          (plan-review gate)
# 非 re-review 派发（baseline / final-review 的 RCA Agent 等）→ 放行。

ROUND=""
PHASE_KEY=""

# 尝试从 envelope gate 字段读（如 envelope 携带 gate 字段）
GATE_NAME=$(echo "$ENVELOPE" | jq -r '.gate // empty' 2>/dev/null || true)

# 若 envelope 无 gate 字段，从 prompt_file 文件名推断
if [[ -z "$GATE_NAME" ]]; then
  GATE_NAME=$(basename "$PROMPT_FILE" .md)
fi

# 匹配 execution re-review: plan-impl-review-N-repair-<round>
if echo "$GATE_NAME" | grep -qE '^plan-impl-review-[0-9]+-repair-[0-9]+$'; then
  ROUND=$(echo "$GATE_NAME" | sed -n 's/.*-repair-\([0-9]*\)$/\1/p')
  PHASE_KEY="execution"
# 匹配 plan-review re-review: plan-review-repair-<round>
elif echo "$GATE_NAME" | grep -qE '^plan-review-repair-[0-9]+$'; then
  ROUND=$(echo "$GATE_NAME" | sed -n 's/.*-repair-\([0-9]*\)$/\1/p')
  PHASE_KEY="plan-review"
else
  # 非 re-review 派发（baseline review / RCA 等）→ fail-open 放行
  exit 0
fi

# ── 5. round 解析保护 ──
if [[ -z "$ROUND" ]] || ! [[ "$ROUND" =~ ^[0-9]+$ ]]; then exit 0; fi

# ── 6. 读 routes repair_policy ──
if [[ ! -f "$ROUTES_JSON" ]]; then exit 0; fi  # fail-open: routes 不可读

PHASE_FROM_ENVELOPE=$(echo "$ENVELOPE" | jq -r '.phase // empty' 2>/dev/null || true)
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty' 2>/dev/null || true)
ROUTE=""

# 尝试从 workflow-state 读 route（fail-open：读不到就跳过）
if [[ -n "$RUN_ID" ]]; then
  BUDGET_DIR=".claude/multi-model-workflow"
  SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
  if [[ -f "$SF" ]]; then
    ROUTE=$(jq -r '.route // empty' "$SF" 2>/dev/null || true)
  fi
fi

# 若 route 仍为空，默认 formal（最常见路线；不确定就 fail-open）
if [[ -z "$ROUTE" ]]; then
  ROUTE="formal"
fi

# 读 max_repair_rounds
MAX_ROUNDS=$(jq -r \
  --arg r "$ROUTE" --arg p "$PHASE_KEY" \
  '.routes[$r].repair_policy[$p].max_repair_rounds // empty' \
  "$ROUTES_JSON" 2>/dev/null || true)

if [[ -z "$MAX_ROUNDS" ]] || ! [[ "$MAX_ROUNDS" =~ ^[0-9]+$ ]]; then
  # fail-open: routes 无本 phase 的 repair_policy → 放行
  exit 0
fi

# ── 7. 比较并拦截 ──
# hook 只读当前 repair_round 值（已由 Coordinator 写入 execution-state），
# 不自行推算，避免误杀 reflux（repair_round 在 re-entry 时不递增，见 SKILL.md）。
# ROUND 来自 gate 名，代表"本次想派发的是第 ROUND 轮 re-review"。
# 若 ROUND > MAX_ROUNDS，说明 Worker repair 轮数已超上限。
if [[ "$ROUND" -gt "$MAX_ROUNDS" ]]; then
  ESCALATE=$(jq -r \
    --arg r "$ROUTE" --arg p "$PHASE_KEY" \
    '.routes[$r].repair_policy[$p].escalate_to_rca // false' \
    "$ROUTES_JSON" 2>/dev/null || echo "false")
  if [[ "$ESCALATE" == "true" ]]; then
    echo "[multi-model-workflow] BLOCKED: ${PHASE_KEY} 已达修复轮上限 ${MAX_ROUNDS}（当前 round=${ROUND}），应走 RCA escalation（root-cause-analyst）而非再次 re-review。" >&2
  else
    echo "[multi-model-workflow] BLOCKED: ${PHASE_KEY} 已达修复轮上限 ${MAX_ROUNDS}（当前 round=${ROUND}），应标记 BLOCKED 报告用户。" >&2
  fi
  exit 2
fi

exit 0
