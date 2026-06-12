#!/usr/bin/env bash
# Pack 2.13: validate-pack-manifest.sh — three-way reconciliation hook.
# Test cases:
#   (a) three-way consistent  → allow
#   (b) Manifest missing pack → BLOCKED with diagnostic
#   (c) Body missing pack     → BLOCKED with diagnostic
#   (d) execution-state contains pack not in Manifest → BLOCKED
#   (e) plan-level dispatch (plan_id) consistent → allow
#   (f) non-execution phase → bypass
#   (g) plan file absent → bypass (route without execution-state plan files)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/validate-pack-manifest.sh"

pass=0
fail=0
run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass + 1))
  else echo "  FAIL: $name"; fail=$((fail + 1)); fi
}
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail + 1))
  else echo "  PASS: $name (expected failure)"; pass=$((pass + 1)); fi
}

echo "=== test_validate_pack_manifest.sh ==="

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

cd "$WORKDIR"

RUN_ID="test-mf-001"
SLUG="manifest-test"
STATE_BASE="$WORKDIR/.codex/multi-model-workflow"
mkdir -p "$STATE_BASE" "$WORKDIR/docs/orchestrate/plans/$SLUG"
echo "$RUN_ID" > "$STATE_BASE/active-run-id"

cat > "$STATE_BASE/workflow-state-$RUN_ID.json" <<JSON
{ "run_id": "$RUN_ID", "slug": "$SLUG" }
JSON

# Helper: build hook input JSON. Use printf '%s' (not echo) when piping so
# embedded \n escapes stay literal in transit to jq.
build_input() {
  local run_id="$1" pack_id="$2" plan_id="${3:-null}" phase="${4:-execution}" agent_role="${5:-pack_executor}"
  jq -nc --arg run_id "$run_id" --arg pack_id "$pack_id" --arg plan_id "$plan_id" \
         --arg phase "$phase" --arg agent_role "$agent_role" '
    {
      tool_input: {
        prompt: ("<!-- DISPATCH_ENVELOPE\n" + ({
          protocol_version: "1",
          run_id: $run_id,
          phase: $phase,
          agent_role: $agent_role,
          agent_id: null,
          pack_id: ($pack_id | if . == "null" then null else . end),
          plan_id: ($plan_id | if . == "null" then null else . end),
          repair_round: 0,
          idempotency_key: ($run_id + "/" + (if $pack_id == "null" then ("plan-" + $plan_id) else $pack_id end) + "/r0")
        } | tojson) + "\n-->")
      }
    }
  '
}

# --- (a) three-way consistent ---
plan_consistent="$WORKDIR/docs/orchestrate/plans/$SLUG/001-foo.md"
cat > "$plan_consistent" <<'PLAN'
# Plan 001

## Pack Execution Manifest

| pack_id | title | anchor | risk | dependencies | owned_files (核心) |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Foo | `#task-pack-11-foo` | normal | — | `a.py` |
| 1.2 | Bar | `#task-pack-12-bar` | normal | 1.1 | `b.py` |

---

### Task Pack 1.1: Foo

Owned files:
- Modify: `a.py`

Risk flags: normal
Dependencies: —

---

### Task Pack 1.2: Bar

Owned files:
- Modify: `b.py`

Risk flags: normal
Dependencies: 1.1
PLAN

cat > "$STATE_BASE/execution-state-$RUN_ID.json" <<JSON
{
  "run_id": "$RUN_ID",
  "plans": {
    "001": {
      "packs": {
        "1.1": { "status": "pending" },
        "1.2": { "status": "pending" }
      }
    }
  }
}
JSON

INPUT_A=$(build_input "$RUN_ID" "1.1")
run_test "(a) three-way consistent → allow" \
  bash -c "printf '%s' '$INPUT_A' | bash '$HOOK'"

# --- (b) Manifest missing a pack ---
plan_b="$WORKDIR/docs/orchestrate/plans/$SLUG/002-bbody.md"
cat > "$plan_b" <<'PLAN'
# Plan 002

## Pack Execution Manifest

| pack_id | title | anchor | risk | dependencies | owned_files (核心) |
| --- | --- | --- | --- | --- | --- |
| 2.1 | first | `#task-pack-21-first` | normal | — | `c.py` |

---

### Task Pack 2.1: first

Risk flags: normal

---

### Task Pack 2.2: missing-from-manifest

Risk flags: normal
PLAN

cat > "$STATE_BASE/execution-state-$RUN_ID.json" <<JSON
{
  "run_id": "$RUN_ID",
  "plans": {
    "002": { "packs": { "2.1": { "status": "pending" } } }
  }
}
JSON

INPUT_B=$(build_input "$RUN_ID" "2.1")
run_test_expect_fail "(b) Manifest missing pack → BLOCKED" \
  bash -c "printf '%s' '$INPUT_B' | bash '$HOOK'"

run_test "(b) diagnostic mentions Pack 2.2" \
  bash -c "printf '%s' '$INPUT_B' | bash '$HOOK' 2>&1 | grep -q 'Pack 2.2'"

# --- (c) Body missing a pack (Manifest declares 3.2, body only has 3.1) ---
plan_c="$WORKDIR/docs/orchestrate/plans/$SLUG/003-cbody.md"
cat > "$plan_c" <<'PLAN'
# Plan 003

## Pack Execution Manifest

| pack_id | title | anchor | risk | dependencies | owned_files (核心) |
| --- | --- | --- | --- | --- | --- |
| 3.1 | only | `#task-pack-31-only` | normal | — | `d.py` |
| 3.2 | ghost | `#task-pack-32-ghost` | normal | 3.1 | `e.py` |

---

### Task Pack 3.1: only

Risk flags: normal
PLAN

cat > "$STATE_BASE/execution-state-$RUN_ID.json" <<JSON
{
  "run_id": "$RUN_ID",
  "plans": {
    "003": { "packs": { "3.1": { "status": "pending" } } }
  }
}
JSON

INPUT_C=$(build_input "$RUN_ID" "3.1")
run_test_expect_fail "(c) Body missing pack → BLOCKED" \
  bash -c "printf '%s' '$INPUT_C' | bash '$HOOK'"

run_test "(c) diagnostic mentions Pack 3.2 (absent from body)" \
  bash -c "printf '%s' '$INPUT_C' | bash '$HOOK' 2>&1 | grep -q 'Pack 3.2'"

# --- (d) execution-state stray pack id not in Manifest ---
cat > "$STATE_BASE/execution-state-$RUN_ID.json" <<JSON
{
  "run_id": "$RUN_ID",
  "plans": {
    "001": {
      "packs": {
        "1.1": { "status": "pending" },
        "1.2": { "status": "pending" },
        "9.9": { "status": "pending" }
      }
    }
  }
}
JSON

INPUT_D=$(build_input "$RUN_ID" "1.1")
run_test_expect_fail "(d) execution-state contains stray pack → BLOCKED" \
  bash -c "printf '%s' '$INPUT_D' | bash '$HOOK'"

run_test "(d) diagnostic mentions Pack 9.9" \
  bash -c "printf '%s' '$INPUT_D' | bash '$HOOK' 2>&1 | grep -q 'Pack 9.9'"

# --- (e) plan-level dispatch (pack_id=null, plan_id=001), consistent → allow ---
cat > "$STATE_BASE/execution-state-$RUN_ID.json" <<JSON
{
  "run_id": "$RUN_ID",
  "plans": {
    "001": {
      "packs": {
        "1.1": { "status": "pending" },
        "1.2": { "status": "pending" }
      }
    }
  }
}
JSON

INPUT_E=$(build_input "$RUN_ID" "null" "001" "execution" "complex_pack_executor")
run_test "(e) plan-level dispatch with consistent Manifest → allow" \
  bash -c "printf '%s' '$INPUT_E' | bash '$HOOK'"

# --- (f) phase=plan-writing → bypass ---
INPUT_F=$(build_input "$RUN_ID" "null" "null" "plan-writing" "plan_writer")
run_test "(f) non-execution phase bypasses hook" \
  bash -c "printf '%s' '$INPUT_F' | bash '$HOOK'"

# --- (g) plan file does not exist → bypass ---
NORUN_ID="test-mf-noplan"
cat > "$STATE_BASE/workflow-state-$NORUN_ID.json" <<JSON
{ "run_id": "$NORUN_ID", "slug": "missing-slug" }
JSON
cat > "$STATE_BASE/execution-state-$NORUN_ID.json" <<JSON
{ "run_id": "$NORUN_ID", "plans": { "001": { "packs": { "1.1": { "status": "pending" } } } } }
JSON

INPUT_G=$(build_input "$NORUN_ID" "1.1")
run_test "(g) missing plan file → bypass" \
  bash -c "printf '%s' '$INPUT_G' | bash '$HOOK'"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
