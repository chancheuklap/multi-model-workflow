#!/usr/bin/env bash
# C9: 承重字段/枚举 对账检查（doc01 §5 红线索引 + §6.5 验收 + doc08 §3.6）
#
# 目的：doc01 §5 列出的"运行时承重字段"——改名/改枚举即静默失守。本检查对每个
# 承重字段断言它在 schema 定义处 + 各消费点都字面在位。任一侧被重命名/删除而另一
# 侧没跟上 → grep 失败 → 本套件红。这是设计要求的"可观测对账工具"（此前缺席、
# §6.5 锚点悬空）。检查按文件名 grep 字面量，不依赖会漂移的行号。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
P="$SCRIPT_DIR/../.."          # plugin/ 根
SCHEMA="$P/state-schema"
HOOKS="$P/hooks"
SCRIPTS="$P/scripts"

pass=0; fail=0
# present <name> <literal> <file...>：literal 必须出现在所有给定文件里
present() {
  local name="$1" lit="$2"; shift 2
  local f miss=""
  for f in "$@"; do
    if [[ ! -f "$f" ]]; then miss="$f (缺文件)"; break; fi
    if ! grep -q -- "$lit" "$f"; then miss="$(basename "$f")"; break; fi
  done
  if [[ -z "$miss" ]]; then echo "  PASS: $name"; pass=$((pass+1));
  else echo "  FAIL: $name — '$lit' 缺失于 $miss"; fail=$((fail+1)); fi
}

echo "=== test_load_bearing_fields.sh（承重字段对账）==="

# 1. idempotency_key / idempotency_keys[]
present "idempotency_key 在 envelope 消费点" "idempotency_key" \
  "$HOOKS/validate-plan-dispatch.sh" "$HOOKS/lib/parse-envelope.sh"
present "idempotency_keys[] 在 state schema" "idempotency_keys" \
  "$SCHEMA/workflow-state-v1.json"

# 2. plan_id / plan_path（execution dispatch 契约）
present "plan_id 在 dispatch 校验" "plan_id" "$HOOKS/validate-plan-dispatch.sh"
present "plan_path 在 dispatch 校验" "plan_path" "$HOOKS/validate-plan-dispatch.sh"

# 3. cursor.phase / cursor.reference / cursor.step（断点续传权威）
present "cursor 在 state.sh + schema" "cursor" \
  "$SCRIPTS/state.sh" "$SCHEMA/workflow-state-v1.json"

# 4. last_gate_phase / last_gate_timestamp（transition 自动写 + Source Stability）
present "last_gate_phase 在 state.sh" "last_gate_phase" "$SCRIPTS/state.sh"
present "last_gate_timestamp 在 state.sh" "last_gate_timestamp" "$SCRIPTS/state.sh"

# 5. status=="committed" / commit_sha（execution-state 三处消费）
present "status committed 在 track-execution-state" "committed" \
  "$HOOKS/track-execution-state.sh"
present "commit_sha 在 track-execution-state + schema" "commit_sha" \
  "$HOOKS/track-execution-state.sh" "$SCHEMA/execution-state-v1.json"

# 6. pending_direction_check.ack_status=="pending"（预算硬停判定）
present "pending_direction_check 在 dispatch 校验" "pending_direction_check" \
  "$HOOKS/validate-plan-dispatch.sh"

# 7. worker-active marker（doc-guard 约定）
present "worker-active marker 在 guard-doc-edit" "worker-active" \
  "$HOOKS/guard-doc-edit.sh"

# 8. merge-brief conflict_id / status / current_stage(7 值)
present "merge-brief conflict_id 在 state.sh" "conflict_id" "$SCRIPTS/state.sh"
# current_stage 7 枚举值必须在 schema 定义处 + state.sh 消费正则两侧都在位
STAGES=(init conflict_discovery rca repair integration_review merging complete)
for s in "${STAGES[@]}"; do
  present "current_stage 枚举 '$s' 两侧一致" "$s" \
    "$SCHEMA/merge-brief-v1.json" "$SCRIPTS/state.sh"
done
# merge-brief status 承重枚举
for st in resolved rca-in-progress; do
  present "merge-brief status '$st' 在 state.sh" "$st" "$SCRIPTS/state.sh"
done

# 9. voice-directive [variant=...] 单源注入（footer 单源后仍每路径注入）
present "VOICE_FOOTER 单源在 build.sh" "VOICE_FOOTER" "$P/build/build.sh"
present "禁止词 footer 渲染进 SKILL（execution 抽样）" "delve" \
  "$P/skills/orchestrate-execution/SKILL.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
