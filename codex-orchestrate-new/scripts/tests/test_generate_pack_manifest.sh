#!/usr/bin/env bash
# Pack 2.11: generate-pack-manifest.sh — scans plan body for ### Task Pack N.M
# and (re)generates the "## Pack Execution Manifest" section, or validates it
# with --check.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$(cd "$SCRIPT_DIR/../.." && pwd)/build/generate-pack-manifest.sh"

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

echo "=== test_generate_pack_manifest.sh ==="

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

# --- Fixture 1: plan without an existing Manifest ---
P1="$WORKDIR/plan-no-manifest.md"
cat > "$P1" <<'PLN'
# Plan A

## File / Responsibility Map

---

### Task Pack 1.1: First Pack

Goal: do thing one.

Owned files:
- Modify: `path/one.py`

Risk flags: normal
Dependencies: —

---

### Task Pack 1.2: Second Pack

Owned files:
- Create: `path/two.py`

Risk flags: high-risk
Dependencies: 1.1
PLN

run_test "generate-pack-manifest appends Manifest when missing" \
  bash "$GEN" "$P1"

run_test "Manifest section header present after generate" \
  grep -qF '## Pack Execution Manifest' "$P1"

run_test "Manifest contains pack 1.1 row" \
  grep -qF '| 1.1 | First Pack' "$P1"

run_test "Manifest contains pack 1.2 row with high-risk and dep" \
  bash -c "grep -F '| 1.2 | Second Pack' '$P1' | grep -qF 'high-risk' && grep -F '| 1.2 |' '$P1' | grep -qF '| 1.1 |'"

run_test "--check passes after regenerate" \
  bash "$GEN" --check "$P1"

# --- Fixture 2: plan with stale Manifest (drift) ---
P2="$WORKDIR/plan-stale.md"
cat > "$P2" <<'PLN'
# Plan B

## Pack Execution Manifest

| pack_id | title | anchor | risk | dependencies | owned_files (核心) |
| --- | --- | --- | --- | --- | --- |
| 9.9 | obsolete pack | `#wrong` | normal | — | `none` |

---

### Task Pack 2.1: Real Pack

Owned files:
- Modify: `real.py`

Risk flags: normal
Dependencies: —
PLN

run_test_expect_fail "--check detects drift before regeneration" \
  bash "$GEN" --check "$P2"

run_test "regenerate overwrites stale Manifest" \
  bash "$GEN" "$P2"

run_test "regenerated Manifest no longer mentions obsolete pack 9.9" \
  bash -c "! grep -q '| 9.9 |' '$P2'"

run_test "regenerated Manifest mentions real pack 2.1" \
  grep -qF '| 2.1 | Real Pack' "$P2"

run_test "regenerated Pack body 2.1 still present (not engulfed)" \
  grep -qF '### Task Pack 2.1: Real Pack' "$P2"

run_test "--check passes after regeneration" \
  bash "$GEN" --check "$P2"

# --- Fixture 3: no Task Pack headings — Manifest with empty rows ---
P3="$WORKDIR/plan-empty.md"
cat > "$P3" <<'PLN'
# Plan C

## File / Responsibility Map

(no packs yet)
PLN

run_test "generate on plan without packs still succeeds" \
  bash "$GEN" "$P3"

run_test "Manifest section appended (with header)" \
  grep -qF '## Pack Execution Manifest' "$P3"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
