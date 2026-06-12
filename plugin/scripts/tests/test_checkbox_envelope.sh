#!/usr/bin/env bash
# A2: state.sh checkbox toggle — committed pack 勾选 / 非 committed 不勾 / Pack ID 精确匹配
# A3: state.sh envelope build — 字段完整、plan|pack key 形态、parse-envelope 对称自检
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
PARSER="$SCRIPT_DIR/../../hooks/lib/parse-envelope.sh"
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected non-zero)"; fail=$((fail+1)); else echo "  PASS: $name"; pass=$((pass+1)); fi; }

echo "=== test_checkbox_envelope.sh ==="

RUN_ID="test-ce"

# --- A2 fixture: plan doc + plan-return ---
# 真实 plan 形态：`## Pack Execution Manifest` 是 validate-pack-manifest.sh 解析的
# 表（cell1 = bare pack_id，无 checkbox），完成 checkbox 在各 Pack body 首行
# `- [ ] **Pack N.M**`。toggle 必须命中 body checkbox，不能依赖 Manifest 表里有
# checkbox（早期 bug：toggle 期望 Manifest 含 checkbox，真实 plan 用表 → 0 toggled）。
PLAN_FILE="$FIXTURE_DIR/plan-001.md"
cat > "$PLAN_FILE" <<'EOF'
# Plan 001

## Pack Execution Manifest

| pack_id | title | risk | dependencies | owned_files |
| --- | --- | --- | --- | --- |
| 1.1 | first pack | normal | — | `a.py` |
| 1.2 | second pack | normal | 1.1 | `b.py` |
| 1.10 | tenth pack | normal | — | `c.py` |
| 1.3 | blocked pack | normal | — | `d.py` |

### Task Pack 1.1: first pack

- [ ] **Pack 1.1**: first pack

### Task Pack 1.2: second pack

- [ ] **Pack 1.2**: second pack

### Task Pack 1.10: tenth pack (prefix-collision probe for 1.1)

- [ ] **Pack 1.10**: tenth pack

### Task Pack 1.3: blocked pack

- [ ] **Pack 1.3**: blocked pack
EOF

mkdir -p "$FIXTURE_DIR/plan-returns/$RUN_ID/001"
cat > "$FIXTURE_DIR/plan-returns/$RUN_ID/001/plan-return.json" <<'EOF'
{
  "schema_version": "1",
  "run_id": "test-ce",
  "plan_id": "001",
  "verdict": "partial-pass",
  "per_pack": {
    "1.1": { "status": "committed", "commit_sha": "abc111" },
    "1.2": { "status": "committed", "commit_sha": "abc222" },
    "1.10": { "status": "skipped", "reason": "pre-empted" },
    "1.3": { "status": "blocked", "reason": "three failures" }
  }
}
EOF

run_test "checkbox toggle runs clean" \
  bash "$STATE_SH" checkbox toggle --run-id "$RUN_ID" --plan-id 001 --plan-file "$PLAN_FILE"
run_test "Pack 1.1 toggled to [x]" \
  bash -c "grep -q -- '- \[x\] \*\*Pack 1.1\*\*' '$PLAN_FILE'"
run_test "Pack 1.2 toggled to [x]" \
  bash -c "grep -q -- '- \[x\] \*\*Pack 1.2\*\*' '$PLAN_FILE'"
run_test "Pack 1.10 (skipped) NOT toggled — precise ID match, no prefix bleed" \
  bash -c "grep -q -- '- \[ \] \*\*Pack 1.10\*\*' '$PLAN_FILE'"
run_test "Pack 1.3 (blocked) NOT toggled" \
  bash -c "grep -q -- '- \[ \] \*\*Pack 1.3\*\*' '$PLAN_FILE'"
run_test "Manifest 表行（bare pack_id）不被 toggle 触碰——toggle 只命中 body checkbox" \
  bash -c "grep -qE '^\| 1\.1 \| first pack \|' '$PLAN_FILE'"
run_test "second run idempotent (already-checked counted, exit 0)" \
  bash -c "bash '$STATE_SH' checkbox toggle --run-id '$RUN_ID' --plan-id 001 --plan-file '$PLAN_FILE' | grep -q '2 already checked'"
run_test_expect_fail "missing plan-return → exit 2" \
  bash "$STATE_SH" checkbox toggle --run-id "$RUN_ID" --plan-id 999 --plan-file "$PLAN_FILE"

# --- A3: envelope build ---
run_test "plan-level envelope passes parse-envelope self-check & prints block" \
  bash -c "bash '$STATE_SH' envelope build --run-id '$RUN_ID' --phase execution --agent-role pack-executor --plan-id 001 --worktree-path /tmp/wt-001 | grep -q 'DISPATCH_ENVELOPE'"

ENV_JSON=$(bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase execution --agent-role pack-executor --plan-id 001 --worktree-path /tmp/wt-001 | sed -n 's/.*DISPATCH_ENVELOPE \(.*\) -->.*/\1/p')
run_test "plan-level idempotency_key uses plan_id (run/001/r0)" \
  bash -c "[[ \$(echo '$ENV_JSON' | jq -r '.idempotency_key') == '${RUN_ID}/001/r0' ]]"
run_test "worktree_path carried in envelope" \
  bash -c "[[ \$(echo '$ENV_JSON' | jq -r '.worktree_path') == '/tmp/wt-001' ]]"
run_test "pack_id null on plan-level dispatch" \
  bash -c "[[ \$(echo '$ENV_JSON' | jq -r '.pack_id') == 'null' ]]"
run_test "required fields all present (protocol_version/run_id/phase/agent_role/repair_round/idempotency_key)" \
  bash -c "echo '$ENV_JSON' | jq -e '.protocol_version and .run_id and .phase and .agent_role and (.repair_round != null) and .idempotency_key'"

PACK_JSON=$(bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase direct-repair --agent-role pack-executor --pack-id 2.3 | sed -n 's/.*DISPATCH_ENVELOPE \(.*\) -->.*/\1/p')
run_test "pack-level idempotency_key uses pack_id (run/2.3/r0)" \
  bash -c "[[ \$(echo '$PACK_JSON' | jq -r '.idempotency_key') == '${RUN_ID}/2.3/r0' ]]"

run_test_expect_fail "both --plan-id and --pack-id rejected" \
  bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase execution --agent-role pack-executor --plan-id 001 --pack-id 1.1
run_test_expect_fail "repair round >=1 without disposition_refs rejected" \
  bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase execution --agent-role pack-executor --plan-id 001 --repair-round 1
run_test "repair round with disposition_refs OK" \
  bash -c "bash '$STATE_SH' envelope build --run-id '$RUN_ID' --phase execution --agent-role pack-executor --plan-id 001 --repair-round 1 --disposition-refs '[\"F1\"]' | grep -q 'DISPATCH_ENVELOPE'"
run_test_expect_fail "codex-reviewer without review_intent rejected" \
  bash "$STATE_SH" envelope build --run-id "$RUN_ID" --phase execution --agent-role codex-reviewer --plan-id 001
run_test "codex-reviewer with baseline OK and parses" \
  bash -c "bash '$STATE_SH' envelope build --run-id '$RUN_ID' --phase execution --agent-role codex-reviewer --plan-id 001 --review-intent baseline | bash '$PARSER' | jq -e '.review_intent == \"baseline\"'"
run_test "resume_from_pack_id carried when set" \
  bash -c "bash '$STATE_SH' envelope build --run-id '$RUN_ID' --phase execution --agent-role pack-executor --plan-id 001 --resume-from-pack-id 1.3 | sed -n 's/.*DISPATCH_ENVELOPE \(.*\) -->.*/\1/p' | jq -e '.resume_from_pack_id == \"1.3\"'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
