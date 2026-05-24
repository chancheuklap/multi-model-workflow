#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
AGENT_TYPE="$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.agent_type // empty) else empty end' 2>/dev/null || true)"
AGENT_ID="$(printf '%s' "$INPUT" | jq -r 'if type == "object" then (.agent_id // empty) else empty end' 2>/dev/null || true)"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

case "$AGENT_TYPE" in
  pack_executor|complex_pack_executor) ;;
  *) exit 0 ;;
esac

RUN_ID_FILE="$STATE_BASE/active-run-id"
[[ -f "$RUN_ID_FILE" ]] || exit 0
RUN_ID="$(cat "$RUN_ID_FILE")"
ESF="$STATE_BASE/execution-state-${RUN_ID}.json"
[[ -f "$ESF" && -n "$AGENT_ID" ]] || exit 0

PACK_ID="$(jq -r --arg aid "$AGENT_ID" '[.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.value.agent_id == $aid) | .key] | first // empty' "$ESF" 2>/dev/null || true)"
[[ -n "$PACK_ID" ]] || exit 0

RETURN_FILE="$STATE_BASE/pack-returns/${RUN_ID}/${PACK_ID}.json"
VERDICT="unknown"
if [[ -f "$RETURN_FILE" ]] && jq empty "$RETURN_FILE" >/dev/null 2>&1; then
  VERDICT="$(jq -r '.verdict // "unknown"' "$RETURN_FILE")"
fi

source "$(cd "$(dirname "$0")" && pwd)/../scripts/lib/state-lock.sh"
LOCK_DIR="$STATE_BASE/${RUN_ID}.lock"
state_lock_acquire "$LOCK_DIR"
jq --arg pack "$PACK_ID" --arg verdict "$VERDICT" '
  .plans |= with_entries(
    .value.packs |= with_entries(
      if .key == $pack then .value.status = "returned" | .value.worker_verdict = $verdict else . end
    )
  )
' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
state_lock_release "$LOCK_DIR"

MSG="[codex-orchestrate] NEXT: ${AGENT_TYPE} ${AGENT_ID} returned for pack ${PACK_ID} with verdict ${VERDICT}. Process open items, verify, checkpoint, then review."
jq -n --arg msg "$MSG" \
  '{hookSpecificOutput:{hookEventName:"SubagentStop",additionalContext:$msg}}'
