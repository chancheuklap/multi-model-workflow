#!/usr/bin/env bash
# test_state_merge_brief.sh
# Pack 6.8: dedicated tests for state.sh merge-brief init/stage/verify helpers.
# Covers: 9-section schema, ephemeral path, slug requirement, enum validation,
# META round-trip, verify self-consistency, idempotency.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="test-mb-v1"
pass=0
fail=0

run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure but passed)"
    fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass + 1))
  fi
}

run_test_value() {
  local name="$1"; local expected="$2"; shift 2
  local actual
  actual=$("$@" 2>/dev/null) || actual="ERROR"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected='$expected' actual='$actual')"
    fail=$((fail + 1))
  fi
}

echo "=== test_state_merge_brief.sh ==="
echo ""
echo "--- init tests ---"

# Init requires --slug
run_test_expect_fail "init without --slug fails" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID"

# Successful init
run_test "init with --slug succeeds" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID" --slug "test-feature"

# File created at correct ephemeral path (STATE_BASE, NOT docs/)
BRIEF_PATH="$FIXTURE_DIR/merge-brief-${RUN_ID}.md"
run_test "init creates file at STATE_BASE path" \
  test -f "$BRIEF_PATH"

run_test_expect_fail "init does NOT create file at docs/ path" \
  test -f "docs/orchestrate/merge-briefs/merge-brief-${RUN_ID}.md"

# File contains MERGE_BRIEF_META block
run_test "init file has MERGE_BRIEF_META block" \
  grep -q "MERGE_BRIEF_META" "$BRIEF_PATH"

# META block has valid JSON
run_test "init META block is valid JSON" \
  bash -c "python3 -c \"
import re, json
with open('$BRIEF_PATH') as f: c = f.read()
m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', c, re.DOTALL)
assert m, 'no META block'
meta = json.loads(m.group(1))
assert meta['schema_version'] == '1'
assert meta['run_id'] == '$RUN_ID'
assert meta['slug'] == 'test-feature'
assert meta['current_stage'] == 'init'
\""

# File has all 9 required section headings
for section in "## 1. Meta" "## 2. 参与 PR" "## 3. 合并后正确状态模型" \
               "## 4. Conflict Findings" "## 5. Root Cause Analysis" \
               "## 6. Resolution Log" "## 7. Integration Review Pointers" \
               "## 8. Open Items" "## 9. Verdict"; do
  run_test "init file has section: $section" \
    grep -qF "$section" "$BRIEF_PATH"
done

# Idempotent: second init does not overwrite
run_test "init is idempotent (second call succeeds)" \
  bash "$STATE_SH" merge-brief init --run-id "$RUN_ID" --slug "test-feature"

# Content unchanged after idempotent call
run_test "init idempotent: file still has META block" \
  grep -q "MERGE_BRIEF_META" "$BRIEF_PATH"

echo ""
echo "--- stage tests ---"

# Stage valid values
for valid_stage in conflict_discovery rca repair integration_review merging complete; do
  run_test "stage to $valid_stage succeeds" \
    bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "$valid_stage"
  run_test "stage $valid_stage updates META current_stage" \
    bash -c "python3 -c \"
import re, json
with open('$BRIEF_PATH') as f: c = f.read()
m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', c, re.DOTALL)
meta = json.loads(m.group(1))
assert meta['current_stage'] == '$valid_stage', f'expected $valid_stage got {meta[\"current_stage\"]}'
\""
done

# Stage updates last_updated_at
run_test "stage updates last_updated_at in META" \
  bash -c "python3 -c \"
import re, json
with open('$BRIEF_PATH') as f: c = f.read()
m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', c, re.DOTALL)
meta = json.loads(m.group(1))
assert meta['last_updated_at'] != '', 'last_updated_at is empty'
\""

# Invalid stage enum must fail
run_test_expect_fail "stage invalid value fails" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "compositional-model"

run_test_expect_fail "stage missing --stage fails" \
  bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID"

# Stage on non-existent brief fails
run_test_expect_fail "stage on missing file fails" \
  bash "$STATE_SH" merge-brief stage --run-id "nonexistent-run" --stage "rca"

echo ""
echo "--- verify tests ---"

# Reset to complete stage for verify testing
bash "$STATE_SH" merge-brief stage --run-id "$RUN_ID" --stage "complete" >/dev/null

run_test "verify passes on complete scaffold" \
  bash "$STATE_SH" merge-brief verify --run-id "$RUN_ID"

# Verify fails when META block is missing
CORRUPT_BRIEF="$FIXTURE_DIR/merge-brief-corrupt.md"
cp "$BRIEF_PATH" "$CORRUPT_BRIEF"
# Create a separate run for corruption test
bash "$STATE_SH" merge-brief init --run-id "corrupt-test" --slug "corrupt" >/dev/null
CORRUPT_PATH="$FIXTURE_DIR/merge-brief-corrupt-test.md"

# Remove META block from corrupt copy
python3 -c "
import re
with open('$CORRUPT_PATH') as f: c = f.read()
c = re.sub(r'<!--\s*MERGE_BRIEF_META.*?-->', '', c, flags=re.DOTALL)
with open('$CORRUPT_PATH', 'w') as f: f.write(c)
"
run_test_expect_fail "verify fails when META block missing" \
  bash "$STATE_SH" merge-brief verify --run-id "corrupt-test"

# Verify fails when a required section is missing
bash "$STATE_SH" merge-brief init --run-id "missing-section" --slug "mtest" >/dev/null
MISSING_PATH="$FIXTURE_DIR/merge-brief-missing-section.md"
# Remove §3 heading
python3 -c "
with open('$MISSING_PATH') as f: lines = f.readlines()
lines = [l for l in lines if '## 3. 合并后正确状态模型' not in l]
with open('$MISSING_PATH', 'w') as f: f.writelines(lines)
"
run_test_expect_fail "verify fails when required section missing" \
  bash "$STATE_SH" merge-brief verify --run-id "missing-section"

# Verify on non-existent brief fails
run_test_expect_fail "verify on missing file fails" \
  bash "$STATE_SH" merge-brief verify --run-id "nonexistent-xyz"

echo ""
echo "--- §4 status self-consistency tests ---"

# Create a brief with a resolved conflict that has no §6 entry — verify must fail
# We build the file directly (not via init) to have full control over section content
CONFLICT_RUN="conflict-test-sc"
CONFLICT_PATH="$FIXTURE_DIR/merge-brief-${CONFLICT_RUN}.md"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > "$CONFLICT_PATH" <<BRIEF_EOF
<!-- MERGE_BRIEF_META
{
  "schema_version": "1",
  "run_id": "${CONFLICT_RUN}",
  "slug": "sctest",
  "created_at": "${NOW}",
  "last_updated_at": "${NOW}",
  "current_stage": "repair",
  "integration_review_gate": null
}
-->

# Merge Brief: ${CONFLICT_RUN}

## 1. Meta

- run_id: ${CONFLICT_RUN}

## 2. 参与 PR（Big Picture）

| PR | Branch | 核心行为 |
| --- | --- | --- |
| #101 | feat/x | implements X |

## 3. 合并后正确状态模型（Step 2 强制产出）

- behaviors: X enabled

## 4. Conflict Findings（Steps 5-7 持续追加）

### Conflict C-001

- conflict_id: C-001
- type: code
- involved_prs: [#101, #102]
- description: test conflict
- severity: medium
- classification: simple
- route: coordinator-fix
- status: resolved
- discovered_by: Coordinator
- discovered_at: ${NOW}

## 5. Root Cause Analysis（Step 10 追加；仅 systemic conflict）

<no systemic conflicts>

## 6. Resolution Log（Steps 13-15 追加）

<no resolutions yet — pending>

## 7. Integration Review Pointers（Step 16 前补写）

- base_diff_range: git diff HEAD

## 8. Open Items / Out-of-scope

<none>

## 9. Verdict（Step 22 写入）

<pending>
BRIEF_EOF

run_test_expect_fail "verify fails when resolved conflict has no §6 entry" \
  bash "$STATE_SH" merge-brief verify --run-id "$CONFLICT_RUN"

# Now add the §6 resolution — verify should pass
python3 - "$CONFLICT_PATH" <<'PYEOF'
import sys, re

filepath = sys.argv[1]
with open(filepath, 'r') as f: content = f.read()

# Insert resolution into §6 section (replace placeholder)
resolution_entry = """
### Resolution for C-001

- conflict_id: C-001
- owner: coordinator-path-a
- repair_round: 1
- summary: fixed the conflict
- status_after: resolved
"""
content = content.replace('<no resolutions yet — pending>', resolution_entry)
with open(filepath, 'w') as f: f.write(content)
PYEOF

run_test "verify passes after adding §6 entry for resolved conflict" \
  bash "$STATE_SH" merge-brief verify --run-id "$CONFLICT_RUN"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
