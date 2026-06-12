#!/usr/bin/env bash
# PostToolUse hook for Bash (if: "Bash(git commit *)").
# Updates execution-state via state-lock after successful Pack commit.
set -euo pipefail

INPUT=$(cat)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ]; then exit 0; fi

BUDGET_DIR=".claude/multi-model-workflow"
RUN_ID_FILE="${BUDGET_DIR}/active-run-id"
if [ ! -f "$RUN_ID_FILE" ]; then exit 0; fi
RUN_ID=$(cat "$RUN_ID_FILE")

ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
if [ ! -f "$ESF" ]; then exit 0; fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
# Pack ID from validated commit message (enforce-plan-commit.sh guarantees format "Pack N.M: ...")
# Uses bash regex instead of sed — input is commit message text, not prompt/control-plane
if [[ "$COMMAND" =~ Pack[[:space:]]+([0-9]+\.[0-9]+) ]]; then
  PACK_ID="${BASH_REMATCH[1]}"
else
  PACK_ID=""
fi
if [ -z "$PACK_ID" ]; then exit 0; fi

# B4: 此处取的是 hook cwd（主会话工作树）的 HEAD——串行模式正确；并行隔离
# worktree 模式下 Worker 在自己的树里 commit，这个值必错，仅作 fallback 记账。
# 权威 SHA 来源是 Worker 上报：plan-return.per_pack[*].commit_sha 经
# `state.sh plan-returns ingest` 整值合并回填，覆盖本 fallback 值。
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/../scripts/lib/state-lock.sh"

LOCK_DIR="${BUDGET_DIR}/${RUN_ID}.lock"
# 裸调用时 acquire 抢锁失败(return 2)会被 set -e 静默杀掉钩子,state 写入整段不执行
# 且无任何 stderr;显式降级为可见的 no-op(钩子是观测性的,丢一次记账可接受)。
state_lock_acquire "$LOCK_DIR" || { echo "[multi-model-workflow] WARN: state lock busy, skipping execution-state update." >&2; exit 0; }
trap 'state_lock_release "$LOCK_DIR"' EXIT

# Update execution-state (pack-level data per Ruling 2)
jq --arg pack "$PACK_ID" --arg sha "$COMMIT_SHA" '
  .plans |= with_entries(
    .value.packs |= with_entries(
      if .key == $pack then
        .value.status = "committed" | .value.commit_sha = $sha
      else . end
    )
  )
' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"

# Count completed packs across all plans
DONE=$(jq '[.plans | to_entries[] | .value.packs | to_entries[] | select(.value.status == "committed")] | length' "$ESF")
TOTAL=$(jq '[.plans | to_entries[] | .value.packs | to_entries[]] | length' "$ESF")

# Find which plan this pack belongs to
PLAN_ID=$(jq -r --arg pack "$PACK_ID" '[.plans | to_entries[] | select(.value.packs[$pack] != null) | .key] | first // empty' "$ESF")

# Count packs in this plan
PLAN_DONE=0
PLAN_TOTAL=0
if [ -n "$PLAN_ID" ]; then
  PLAN_DONE=$(jq --arg pid "$PLAN_ID" '[.plans[$pid].packs | to_entries[] | select(.value.status == "committed")] | length' "$ESF")
  PLAN_TOTAL=$(jq --arg pid "$PLAN_ID" '[.plans[$pid].packs | to_entries[]] | length' "$ESF")
fi

if [ "$PLAN_DONE" -eq "$PLAN_TOTAL" ] && [ "$PLAN_TOTAL" -gt 0 ]; then
  # Write end_commit for plan review diff (start_commit..end_commit)
  jq --arg pid "$PLAN_ID" --arg sha "$COMMIT_SHA" '
    .plans[$pid].end_commit = $sha
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"

  # Plan 005 Pack 5.10: when worker_agent_id is set (autonomous-mode Worker still
  # in flight), suppress the "Dispatch Plan Implementation Review" NEXT — the
  # Worker is committing all packs in a single session and will return through
  # agent-return-handler.sh, which is the authoritative routing decision point.
  # Emitting Review NEXT here would mislead Coordinator into dispatching review
  # before Worker returns the plan-return.json artifact.
  WORKER_AGENT_ID=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].worker_agent_id // empty' "$ESF" 2>/dev/null || echo "")
  # 已审完 / 已收口的 Plan 不该再被提示去 review。Plan Implementation Review pass 后
  # Coordinator 写 plans[N].review_verdict=pass；execution-plan finish 写
  # plans[N].status=completed。任一为真 → 该 Plan 终态，后续 commit（含 commit_sha
  # 数据污染场景）再次满足「全 pack committed」也不能重发 review NEXT，否则对已审完
  # Plan 制造误导噪声、诱导 Coordinator 重复派审。
  REVIEW_VERDICT=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].review_verdict // empty' "$ESF" 2>/dev/null || echo "")
  PLAN_STATUS=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].status // empty' "$ESF" 2>/dev/null || echo "")
  if [ "$REVIEW_VERDICT" = "pass" ] || [ "$PLAN_STATUS" = "completed" ]; then
    MSG="[multi-model-workflow] STATE: All ${PLAN_TOTAL} packs in Plan ${PLAN_ID} committed (end_commit: ${COMMIT_SHA}). Plan already reviewed/finalized (review_verdict=${REVIEW_VERDICT:-none}, status=${PLAN_STATUS:-none}) — no further Plan Implementation Review needed."
  elif [ -n "$WORKER_AGENT_ID" ] && [ "$WORKER_AGENT_ID" != "null" ]; then
    MSG="[multi-model-workflow] STATE: All ${PLAN_TOTAL} packs in Plan ${PLAN_ID} committed (end_commit: ${COMMIT_SHA}). Worker ${WORKER_AGENT_ID} still in session — wait for SubagentStop / agent-return-handler.sh. Do NOT dispatch Plan Implementation Review yet."
  else
    MSG="[multi-model-workflow] NEXT: All ${PLAN_TOTAL} packs in Plan ${PLAN_ID} committed (end_commit: ${COMMIT_SHA}). Dispatch Plan Implementation Review."
  fi
else
  MSG="[multi-model-workflow] STATE: Pack ${PACK_ID} committed (${PLAN_DONE}/${PLAN_TOTAL} in Plan ${PLAN_ID})."
fi

jq -n --arg msg "$MSG" \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
