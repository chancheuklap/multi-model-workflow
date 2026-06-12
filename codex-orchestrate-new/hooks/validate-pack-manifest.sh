#!/usr/bin/env bash
# Pack 2.13 / R2: PreToolUse subagent hook ((pack_executor|complex_pack_executor)) that
# performs the three-way reconciliation between:
#   A) plan document's "## Pack Execution Manifest" rows           (pack_id list)
#   B) plan document's "### Task Pack N.M" body headings           (pack_id list)
#   C) execution-state.plans[plan_id].packs keys                   (already-tracked packs)
#
# Required invariants:
#   - A == B (Manifest and Pack bodies must declare the same pack ids exactly).
#   - C ⊆ A (Every pack the system thinks exists must be in the Manifest. On
#            first dispatch C may be empty — that's fine.)
#
# Mis-alignment → BLOCKED with a precise diagnostic, because the alternative is a
# Worker that either drives off the Manifest (and silently skips a Pack present
# only in the body) or off the body (and silently runs a Pack that no reviewer
# planned for). Both modes corrupt the audit chain.
#
# Hook design (mirroring validate-pack-dispatch.sh):
#   1. Parse DISPATCH_ENVELOPE from tool_input.prompt.
#   2. Resolve plan_id (envelope.plan_id for plan-level dispatch; otherwise
#      derive from envelope.pack_id by looking up which plan owns it in
#      execution-state).
#   3. Resolve the plan file path: docs/orchestrate/plans/<slug>/<plan_id>-*.md
#   4. Extract sets A and B with grep/awk; load set C from execution-state.
#   5. Compare and emit BLOCKED on any drift, OK otherwise.
#   6. Optionally invoke generate-pack-manifest.sh --check as a second check
#      that the Manifest content (not just pack_id list) matches body fields.
set -euo pipefail

INPUT=$(cat)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSE_ENVELOPE="$SCRIPT_DIR/lib/parse-envelope.sh"
# Source routes library (fail-open if unavailable) —— 裸 source 在 set -e 下,
# routes.sh 缺失会让脚本 rc=1 退出,PreToolUse 非 2 即放行未校验的派发(fail-open)。
# shellcheck source=lib/routes.sh
if [[ -f "$SCRIPT_DIR/lib/routes.sh" ]]; then
  source "$SCRIPT_DIR/lib/routes.sh"
else
  routes_manifest_readable() { return 1; }
  routes_dispatch_shape() { echo ""; }
fi

PROMPT=$(echo "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null)
if [[ -z "$PROMPT" ]]; then exit 0; fi

ENVELOPE=$(echo "$PROMPT" | bash "$PARSE_ENVELOPE" 2>/dev/null) || exit 0

RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
PACK_ID=$(echo "$ENVELOPE" | jq -r '.pack_id // empty')
ENV_PLAN_ID=$(echo "$ENVELOPE" | jq -r '.plan_id // empty')
PHASE=$(echo "$ENVELOPE" | jq -r '.phase // empty')

BUDGET_DIR=".codex/multi-model-workflow"
SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
ESF="${BUDGET_DIR}/execution-state-${RUN_ID}.json"

# Only police plan-level (Manifest-model) Worker dispatches.
# Machine source: routes-v1.json[route].dispatch_shape[PHASE] == "plan-level".
# Fail-open: manifest unreadable / no shape → legacy literal PHASE == "execution".
ROUTE=""
if [[ -f "$SF" ]]; then ROUTE=$(jq -r '.route // empty' "$SF" 2>/dev/null); fi
DISPATCH_SHAPE=$(routes_dispatch_shape "$ROUTE" "$PHASE")
if [[ -n "$DISPATCH_SHAPE" ]]; then
  [[ "$DISPATCH_SHAPE" == "plan-level" ]] || exit 0
else
  [[ "$PHASE" == "execution" ]] || exit 0
fi

# If state files don't exist, this is not a real workflow run — let the dispatch
# proceed (some test routes have no execution-state).
if [[ ! -f "$SF" ]]; then exit 0; fi

# Resolve plan_id. Pack-level dispatch: derive from execution-state.
PLAN_ID=""
if [[ -n "$ENV_PLAN_ID" && "$ENV_PLAN_ID" != "null" ]]; then
  PLAN_ID="$ENV_PLAN_ID"
elif [[ -n "$PACK_ID" && "$PACK_ID" != "null" && -f "$ESF" ]]; then
  PLAN_ID=$(jq -r --arg pid "$PACK_ID" \
    '[.plans | to_entries[] | select(.value.packs[$pid] != null) | .key] | first // empty' \
    "$ESF" 2>/dev/null || echo "")
fi

# If we still can't resolve a plan, exit 0 — this is a route that does not use
# the Plan/Pack Manifest model (e.g. the route-worker routes).
if [[ -z "$PLAN_ID" ]]; then exit 0; fi

# Resolve plan file path. Slug comes from workflow-state.slug.
SLUG=$(jq -r '.slug // empty' "$SF" 2>/dev/null)
if [[ -z "$SLUG" ]]; then exit 0; fi

PLAN_GLOB="docs/orchestrate/plans/${SLUG}/${PLAN_ID}-*.md"
PLAN_FILE=""
for candidate in $PLAN_GLOB; do
  if [[ -f "$candidate" ]]; then PLAN_FILE="$candidate"; break; fi
done

# If the plan file does not yet exist, silently let dispatch proceed. The hook is
# a Manifest-integrity check, not a plan-existence check.
if [[ -z "$PLAN_FILE" ]]; then exit 0; fi

# --- Build set A: pack_ids from "## Pack Execution Manifest" rows ---
# Strategy: read the file with awk; enter capture mode after the heading, exit
# at the next "## " heading; for each candidate row, extract the first table
# cell and emit it if it matches N.M. We use POSIX awk (no gawk-only match()
# with capture array) so this works on macOS/BSD awk too.
A_IDS=$(awk '
  /^## Pack Execution Manifest/ { capture=1; next }
  capture==1 && /^## / && !/^## Pack Execution Manifest/ { capture=0 }
  capture==1 && /^\| *[0-9]+\.[0-9]+ *\|/ {
    # Split on | and trim cell 2 (cell 1 is empty before the leading |).
    n = split($0, parts, "|")
    if (n >= 2) {
      cell = parts[2]
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", cell)
      if (cell ~ /^[0-9]+\.[0-9]+$/) print cell
    }
  }
' "$PLAN_FILE" 2>/dev/null | sort -u)

# --- Build set B: pack_ids from "### Task Pack N.M" headings ---
B_IDS=$(grep -E '^### Task Pack [0-9]+\.[0-9]+' "$PLAN_FILE" 2>/dev/null \
  | sed -E 's/^### Task Pack ([0-9]+\.[0-9]+).*/\1/' | sort -u)

# --- Build set C: pack_ids tracked in execution-state for this plan ---
C_IDS=""
if [[ -f "$ESF" ]]; then
  C_IDS=$(jq -r --arg pid "$PLAN_ID" \
    '.plans[$pid].packs // {} | keys[]' \
    "$ESF" 2>/dev/null | sort -u || echo "")
fi

# --- Compare A vs B ---
MISSING_FROM_MANIFEST=$(comm -23 <(echo "$B_IDS") <(echo "$A_IDS"))
MISSING_FROM_BODY=$(comm -13 <(echo "$B_IDS") <(echo "$A_IDS"))

if [[ -n "$MISSING_FROM_MANIFEST" ]]; then
  echo "[multi-model-workflow] BLOCKED: Pack Execution Manifest (plan $PLAN_ID) does not list:" >&2
  echo "$MISSING_FROM_MANIFEST" | sed 's/^/  - Pack /' >&2
  echo "  Fix: add row(s) to '## Pack Execution Manifest' in $PLAN_FILE or run 'bash codex-orchestrate-new/build/generate-pack-manifest.sh $PLAN_FILE'." >&2
  exit 2
fi

if [[ -n "$MISSING_FROM_BODY" ]]; then
  echo "[multi-model-workflow] BLOCKED: Pack Execution Manifest lists packs absent from plan body:" >&2
  echo "$MISSING_FROM_BODY" | sed 's/^/  - Pack /' >&2
  echo "  Fix: either add '### Task Pack N.M' sections to $PLAN_FILE or remove the Manifest rows." >&2
  exit 2
fi

# --- Compare C against A (C must be a subset of A) ---
if [[ -n "$C_IDS" ]]; then
  STRAY_C=$(comm -23 <(echo "$C_IDS") <(echo "$A_IDS"))
  if [[ -n "$STRAY_C" ]]; then
    echo "[multi-model-workflow] BLOCKED: execution-state.plans[$PLAN_ID].packs contains pack ids not in the Manifest:" >&2
    echo "$STRAY_C" | sed 's/^/  - Pack /' >&2
    echo "  Fix: either remove the stray pack(s) from execution-state, or add them to '## Pack Execution Manifest' in $PLAN_FILE." >&2
    exit 2
  fi
fi

# --- Optional secondary check: invoke generate-pack-manifest.sh --check ---
# Manifest content (anchors / risk / dependencies / owned files) must match Pack
# bodies, not just the pack id list. We treat this check as non-blocking if the
# generator is missing (older worktree), and as advisory-only if it reports
# DRIFT but the pack id set itself is consistent — Coordinator can choose to
# regenerate. We emit a warning to additionalContext, not BLOCKED, so we don't
# stall every dispatch on cosmetic Manifest drift.
GEN_SH="$SCRIPT_DIR/../build/generate-pack-manifest.sh"
ADVISORY=""
if [[ -x "$GEN_SH" ]]; then
  if ! bash "$GEN_SH" --check "$PLAN_FILE" >/dev/null 2>&1; then
    ADVISORY="[multi-model-workflow] NOTE: Manifest content for plan $PLAN_ID differs from Pack bodies (anchors/risk/deps). Run 'bash $GEN_SH $PLAN_FILE' to regenerate."
  fi
fi

if [[ -n "$ADVISORY" ]]; then
  jq -n --arg msg "$ADVISORY" \
    '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $msg}}'
fi

exit 0
