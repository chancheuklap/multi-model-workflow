#!/usr/bin/env bash
# C1/C3/C4: codex-worker.sh 派发包装端到端（注入假 codex 二进制，不烧真额度）
#   - dispatch：envelope 校验→marker→假 codex 跑→session 记账→ingest 回填→NEXT
#   - 模型分层参数：standard→gpt-5.4 / complex→gpt-5.5（CODEX_MODEL_* 可覆盖，此处断言传参）
#   - resume：读 session_id 续会话；缺 session 报错
#   - 重派守卫：in_progress + session_id 已存在 → 无 resume_from 的 dispatch 被拦
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CODEX_WORKER="$PLUGIN_DIR/scripts/codex-worker.sh"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected non-zero)"; fail=$((fail+1)); else echo "  PASS: $name"; pass=$((pass+1)); fi; }

echo "=== test_codex_worker.sh ==="

RUN_ID="test-cw"
cd "$FIXTURE_DIR"
mkdir -p .claude/multi-model-workflow

# --- 假 codex：记录 argv、打印 session header、写 plan-return + last message ---
FAKE_BIN_DIR="$FIXTURE_DIR/bin"
mkdir -p "$FAKE_BIN_DIR"
cat > "$FAKE_BIN_DIR/fake-codex" <<'FAKE'
#!/usr/bin/env bash
# argv 落盘供断言；模拟 codex exec 行为
echo "$@" > "$FAKE_LOG"
cat > /dev/null  # 吞掉 stdin prompt
# 提取 -o 参数
out=""
prev=""
for a in "$@"; do
  if [[ "$prev" == "-o" ]]; then out="$a"; fi
  prev="$a"
done
echo "OpenAI Codex v0.138.0 (fake)"
echo "session id: fake-sess-0001"
mkdir -p "$(dirname "$FAKE_PLAN_RETURN")"
cp "$FAKE_PLAN_RETURN_SRC" "$FAKE_PLAN_RETURN"
[[ -n "$out" ]] && echo "WORKER DONE" > "$out"
exit "${FAKE_EXIT:-0}"
FAKE
chmod +x "$FAKE_BIN_DIR/fake-codex"

# --- 状态夹具：workflow-state（budget 已初始化）+ execution-state + plan 文件 + worktree ---
export STATE_BASE=".claude/multi-model-workflow"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug cw --route formal >/dev/null
bash "$STATE_SH" budget initialize --run-id "$RUN_ID" --plan-count 1 >/dev/null
echo "$RUN_ID" > .claude/multi-model-workflow/active-run-id

PLAN_FILE="$FIXTURE_DIR/plan-001.md"
cat > "$PLAN_FILE" <<'EOF'
# Plan 001
**Blocked by:** None

## Pack Execution Manifest

- [ ] **Pack 1.1**: do the thing
EOF

cat > ".claude/multi-model-workflow/execution-state-${RUN_ID}.json" <<EOF
{ "run_id": "$RUN_ID", "plans": { "001": { "status": "pending", "packs": { "1.1": { "status": "pending" } } } } }
EOF

WT="$FIXTURE_DIR/wt-001"
mkdir -p "$WT"
bash "$STATE_SH" execution-plan start --run-id "$RUN_ID" --plan-id 001 \
  --start-commit deadbee --worktree-path "$WT" --branch plan-001 >/dev/null

# 假 codex 写的 plan-return 内容
PR_SRC="$FIXTURE_DIR/pr-src.json"
cat > "$PR_SRC" <<EOF
{ "schema_version": "1", "run_id": "$RUN_ID", "plan_id": "001", "verdict": "pass",
  "per_pack": { "1.1": { "status": "committed", "commit_sha": "wt-sha-111" } } }
EOF

export CODEX_BIN="$FAKE_BIN_DIR/fake-codex"
export FAKE_LOG="$FIXTURE_DIR/fake-argv.txt"
export FAKE_PLAN_RETURN_SRC="$PR_SRC"
export FAKE_PLAN_RETURN="$FIXTURE_DIR/.claude/multi-model-workflow/plan-returns/$RUN_ID/001/plan-return.json"
export CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR"

# --- dispatch（standard tier）---
OUT=$(bash "$CODEX_WORKER" dispatch --run-id "$RUN_ID" --plan-id 001 \
  --plan-path "$PLAN_FILE" --worktree-path "$WT" --model-tier standard 2>&1) || true

run_test "dispatch emits NEXT for verdict=pass (Claude review per C5)" \
  bash -c "echo '$OUT' | grep -q 'verdict=pass' && echo '$OUT' | grep -q 'Plan Implementation Review'"
run_test "fake codex invoked with exec -C <worktree> + workspace-write sandbox" \
  bash -c "grep -q -- 'exec -C $WT --sandbox workspace-write' '$FAKE_LOG'"
run_test "standard tier passes gpt-5.4 + xhigh effort" \
  bash -c "grep -q -- '-m gpt-5.4' '$FAKE_LOG' && grep -q 'model_reasoning_effort' '$FAKE_LOG'"
run_test "--add-dir points at main-tree state dir" \
  bash -c "grep -q -- '--add-dir $FIXTURE_DIR/.claude/multi-model-workflow' '$FAKE_LOG'"
run_test "session id captured into execution-state" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].session_id' '.claude/multi-model-workflow/execution-state-${RUN_ID}.json') == 'fake-sess-0001' ]]"
run_test "ingest backfills worker-reported commit_sha (B4)" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].packs[\"1.1\"].commit_sha' '.claude/multi-model-workflow/execution-state-${RUN_ID}.json') == 'wt-sha-111' ]]"
run_test "per-plan marker created with worktree path content" \
  bash -c "[[ \$(cat '.claude/multi-model-workflow/worker-active-001') == '$WT' ]]"
run_test "dispatch prompt contains envelope + worktree root discipline" \
  bash -c "grep -q 'DISPATCH_ENVELOPE' '.claude/multi-model-workflow/dispatch-prompts/$RUN_ID/001-r0.md' && grep -q '$WT' '.claude/multi-model-workflow/dispatch-prompts/$RUN_ID/001-r0.md'"

# --- 重派守卫：in_progress + session 已在 → 拦 ---
run_test_expect_fail "re-dispatch without resume_from blocked (session guard)" \
  bash "$CODEX_WORKER" dispatch --run-id "$RUN_ID" --plan-id 001 \
    --plan-path "$PLAN_FILE" --worktree-path "$WT" --model-tier standard

# --- resume（修复轮）---
# 先放置 accepted disposition（repair 校验链）
bash "$STATE_SH" disposition append --run-id "$RUN_ID" --finding-id F1 \
  --disposition accepted --evidence "确认缺测试" >/dev/null 2>&1 || true
INSTR="$FIXTURE_DIR/repair.md"
echo "修 F1：补回归测试" > "$INSTR"
# 假 codex 第二次写 pass 的 plan-return（带 repair 元数据无所谓，verdict 沿用）
RESUME_OUT=$(bash "$CODEX_WORKER" resume --run-id "$RUN_ID" --plan-id 001 \
  --repair-round 1 --disposition-refs '["F1"]' --instructions-file "$INSTR" 2>&1) || true
run_test "resume drives 'exec resume <session_id>'" \
  bash -c "grep -q -- 'exec resume fake-sess-0001' '$FAKE_LOG'"
run_test "resume re-ingests and emits NEXT" \
  bash -c "echo '$RESUME_OUT' | grep -q 'verdict=pass'"

# --- resume 缺 session 报错 ---
cat > ".claude/multi-model-workflow/execution-state-${RUN_ID}.json" <<EOF
{ "run_id": "$RUN_ID", "plans": { "002": { "status": "pending", "packs": { "2.1": { "status": "pending" } } } } }
EOF
run_test_expect_fail "resume without session_id errors" \
  bash "$CODEX_WORKER" resume --run-id "$RUN_ID" --plan-id 002 \
    --repair-round 1 --disposition-refs '["F1"]' --instructions-file "$INSTR"

# --- 假 codex 不写 plan-return → BLOCKED 信息而非静默 ---
cat > ".claude/multi-model-workflow/execution-state-${RUN_ID}.json" <<EOF
{ "run_id": "$RUN_ID", "plans": { "003": { "status": "pending", "packs": { "3.1": { "status": "pending" } } } } }
EOF
bash "$STATE_SH" execution-plan start --run-id "$RUN_ID" --plan-id 003 \
  --start-commit deadbee --worktree-path "$WT" --branch plan-003 >/dev/null
export FAKE_PLAN_RETURN="$FIXTURE_DIR/.claude/multi-model-workflow/plan-returns/$RUN_ID/003-nowhere/never.json"
PLAN3="$FIXTURE_DIR/plan-003.md"
sed 's/Plan 001/Plan 003/; s/1\.1/3.1/' "$PLAN_FILE" > "$PLAN3"
OUT3=$(bash "$CODEX_WORKER" dispatch --run-id "$RUN_ID" --plan-id 003 \
  --plan-path "$PLAN3" --worktree-path "$WT" --model-tier complex 2>&1) || true
run_test "missing plan-return → explicit BLOCKED guidance" \
  bash -c "echo '$OUT3' | grep -q 'BLOCKED' && echo '$OUT3' | grep -q 'plan-return.json'"
run_test "complex tier passes gpt-5.5" \
  bash -c "grep -q -- '-m gpt-5.5' '$FAKE_LOG'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
