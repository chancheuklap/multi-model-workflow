#!/usr/bin/env bash
# Tests route-aware transition_allowed() reading routes-v1.json (P2):
#   ① route=formal behaves equivalently to the legacy TRANSITION_MATRIX
#      (sampled phase transitions still allowed).
#   ② route=light DENIES workflow→discovery (exit≠0) — machine拦轻档误跳,
#      the P2 core new behavior (light's phase_transitions has no
#      Coordinator:workflow:discovery).
#   ③ fail-open: when the manifest is absent / the route is unknown, transition
#      falls back to the built-in full matrix (transition still allowed).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected non-zero)"; fail=$((fail+1)); else echo "  PASS: $name"; pass=$((pass+1)); fi; }

# Helper: set cursor.phase then attempt a transition for a given run.
do_transition() {
  local rid="$1" from="$2" to="$3" actor="${4:-Coordinator}"
  bash "$STATE_SH" update --run-id "$rid" --field '.cursor.phase' --value "\"$from\"" >/dev/null 2>&1
  bash "$STATE_SH" transition --run-id "$rid" --actor "$actor" --from "$from" --to "$to"
}

echo "=== test_routes_transition.sh ==="

# --- ① formal == legacy matrix (sampled phase transitions allowed) ---
RID_F="rt-formal"
bash "$STATE_SH" init --run-id "$RID_F" --slug t --route formal >/dev/null

run_test "formal: workflow→discovery allowed" \
  do_transition "$RID_F" workflow discovery
run_test "formal: discovery→plan-writing allowed" \
  do_transition "$RID_F" discovery plan-writing
run_test "formal: plan-writing→execution allowed" \
  do_transition "$RID_F" plan-writing execution
run_test "formal: execution→final-review allowed" \
  do_transition "$RID_F" execution final-review
# global_transitions (route-agnostic work-item) still allowed under formal
run_test "formal: pending→dispatched allowed (global work-item)" \
  do_transition "$RID_F" pending dispatched
run_test "formal: wildcard *→blocked allowed (global)" \
  do_transition "$RID_F" some_phase blocked

# --- ② light DENIES workflow→discovery (P2 core new behavior) ---
RID_L="rt-light"
bash "$STATE_SH" init --run-id "$RID_L" --slug t --route light >/dev/null
run_test "light: route written as light" \
  bash -c "[[ \$(jq -r '.route' '$FIXTURE_DIR/workflow-state-${RID_L}.json') == 'light' ]]"
run_test_expect_fail "light: workflow→discovery DENIED (machine拦轻档误跳)" \
  do_transition "$RID_L" workflow discovery
# light DOES allow its declared phase推进 (workflow→plan-writing, execution→final-review)
run_test "light: workflow→plan-writing allowed" \
  do_transition "$RID_L" workflow plan-writing
run_test "light: execution→final-review allowed" \
  do_transition "$RID_L" execution final-review
# light still honors global work-item transitions
run_test "light: pending→dispatched allowed (global)" \
  do_transition "$RID_L" pending dispatched

# --- ③ fail-open: manifest absent → fall back to full legacy matrix ---
# Build an isolated scripts dir copy WITHOUT a sibling state-schema/ so the
# manifest path ($SCRIPT_DIR/../state-schema/routes-v1.json) does not resolve.
ISO_DIR=$(mktemp -d)
mkdir -p "$ISO_DIR/scripts/lib"
cp "$STATE_SH" "$ISO_DIR/scripts/state.sh"
cp "$SCRIPT_DIR/../lib/state-lock.sh" "$ISO_DIR/scripts/lib/state-lock.sh"
ISO_STATE_SH="$ISO_DIR/scripts/state.sh"
# Sanity: confirm the manifest is genuinely unreachable from the isolated copy.
run_test "fail-open precondition: manifest absent next to isolated state.sh" \
  bash -c "[[ ! -f '$ISO_DIR/state-schema/routes-v1.json' ]]"

RID_FO="rt-failopen"
STATE_BASE="$FIXTURE_DIR" bash "$ISO_STATE_SH" init --run-id "$RID_FO" --slug t --route light >/dev/null
# With NO manifest, light's restriction cannot apply → legacy matrix放行
# workflow→discovery (which the full TRANSITION_MATRIX contains).
run_test "fail-open: manifest absent → light's workflow→discovery ALLOWED via legacy matrix" \
  bash -c "STATE_BASE='$FIXTURE_DIR' bash -c 'bash \"$ISO_STATE_SH\" update --run-id \"$RID_FO\" --field \".cursor.phase\" --value \"\\\"workflow\\\"\" >/dev/null && bash \"$ISO_STATE_SH\" transition --run-id \"$RID_FO\" --actor Coordinator --from workflow --to discovery'"

# --- ③b fail-open: unknown route → fall back to full legacy matrix ---
RID_UNK="rt-unknown"
bash "$STATE_SH" init --run-id "$RID_UNK" --slug t --route formal >/dev/null
# Force an unknown route value not present in routes-v1.json.
bash "$STATE_SH" update --run-id "$RID_UNK" --field '.route' --value '"no-such-route"' >/dev/null
run_test "fail-open: unknown route → workflow→discovery ALLOWED via legacy matrix" \
  do_transition "$RID_UNK" workflow discovery
# Even under fail-open, a genuinely illegal transition (unknown actor) is still
# denied — fail-open means "fall back to the full matrix", not "allow anything".
run_test_expect_fail "fail-open: unknown route → illegal transition still DENIED (matrix enforced)" \
  do_transition "$RID_UNK" pending committed evil

rm -rf "$ISO_DIR"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
