#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_BASE="${STATE_BASE:-.claude/multi-model-workflow}"
LOCK_TTL=60

usage() {
  cat <<'USAGE'
Usage: state.sh <command> [options]

Commands:
  init          Create initial workflow-state file
  read          Read a field from state
  update        Update a field in state
  transition    State machine transition with matrix validation
  validate      Validate state file against schema
  disposition   Manage review dispositions (append)
  self-verify   Manage self-verification records (append)

Options:
  --run-id <id>     Run identifier (required for most commands)
  --field <jq-path> Field to read/update
  --value <json>    Value to set (for update)
  --actor <name>    Actor performing transition
  --from <state>    Source state (transition)
  --to <state>      Target state (transition)
USAGE
  exit 1
}

state_file() {
  echo "${STATE_BASE}/workflow-state-${RUN_ID}.json"
}

lock_dir() {
  echo "${STATE_BASE}/${RUN_ID}.lock"
}

acquire_lock() {
  local lock
  lock="$(lock_dir)"
  local attempts=0

  while ! mkdir "$lock" 2>/dev/null; do
    if [[ -f "$lock/ts" ]]; then
      local ts
      ts=$(cat "$lock/ts")
      local now
      now=$(date +%s)
      if (( now - ts > LOCK_TTL )); then
        echo "Cleaning stale lock (age=$((now - ts))s)" >&2
        rm -rf "$lock"
        continue
      fi
    fi
    attempts=$((attempts + 1))
    if (( attempts > 50 )); then
      echo "Error: could not acquire lock after 50 attempts" >&2
      exit 2
    fi
    sleep 0.1
  done

  echo $$ > "$lock/pid"
  date +%s > "$lock/ts"
}

release_lock() {
  local lock
  lock="$(lock_dir)"
  rm -rf "$lock"
}

ensure_state_exists() {
  local sf
  sf="$(state_file)"
  if [[ ! -f "$sf" ]]; then
    echo "Error: state file not found: $sf" >&2
    exit 2
  fi
}

cmd_init() {
  local slug="" route=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --slug) slug="$2"; shift 2 ;;
      --route) route="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  mkdir -p "$STATE_BASE"
  local sf
  sf="$(state_file)"

  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local review_total=3
  case "$route" in
    hotfix|quickfix|spike|maintenance) review_total='"unlimited"' ;;
  esac

  cat > "$sf" <<INITJSON
{
  "run_id": "${RUN_ID}",
  "slug": "${slug}",
  "route": "${route}",
  "started_at": "${now}",
  "current_phase": "workflow",
  "current_reference": null,
  "current_step": null,
  "cursor": { "phase": "workflow", "reference": null, "step": null },
  "budget": {
    "review_total": ${review_total},
    "review_used": 0,
    "effort_total": 0,
    "effort_used": 0,
    "direction_check_count": 0
  },
  "plans": [],
  "idempotency_keys": [],
  "plan_writer_agent_id": null,
  "review_dispositions": [],
  "review_effectiveness": {
    "reject_count": 0,
    "suppress_count": 0,
    "path_a_count": 0,
    "path_b_count": 0,
    "total_findings": 0,
    "last_aggregated_at": null
  },
  "pending_post_push_reviews": [],
  "path_a_escalation": [],
  "self_verifications": [],
  "pending_direction_check": null,
  "execution_reflux_count": 0,
  "last_gate_phase": null,
  "last_gate_timestamp": null
}
INITJSON
  echo "Created: $sf"
}

cmd_read() {
  local field=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --field) field="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  local sf
  sf="$(state_file)"

  if [[ -z "$field" ]]; then
    cat "$sf"
  else
    jq -r "$field" "$sf"
  fi
}

cmd_update() {
  local field="" value=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --field) field="$2"; shift 2 ;;
      --value) value="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$field" || -z "$value" ]]; then
    echo "Error: --field and --value required for update" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"
  jq "$field = $value" "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_transition() {
  local actor="" from="" to="" disposition_refs=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --actor) actor="$2"; shift 2 ;;
      --from) from="$2"; shift 2 ;;
      --to) to="$2"; shift 2 ;;
      --disposition-refs) disposition_refs="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"

  # Validate disposition-refs for repairing transition
  if [[ "$to" == "repairing" && -n "$disposition_refs" ]]; then
    IFS=',' read -ra refs <<< "$disposition_refs"
    for ref in "${refs[@]}"; do
      local found
      found=$(jq -r --arg fid "$ref" '.review_dispositions[] | select(.finding_id == $fid) | .disposition' "$sf")
      if [[ "$found" != "accepted" ]]; then
        echo "Error: finding $ref not found or not accepted in review_dispositions" >&2
        exit 2
      fi
      local evidence
      evidence=$(jq -r --arg fid "$ref" '.review_dispositions[] | select(.finding_id == $fid) | .evidence // ""' "$sf")
      if [[ -z "$evidence" || "$evidence" == "null" ]]; then
        echo "Error: finding $ref has no evidence" >&2
        exit 2
      fi
    done
  elif [[ "$to" == "repairing" && -z "$disposition_refs" ]]; then
    echo "Error: --disposition-refs required for transition to repairing" >&2
    exit 2
  fi

  local tmp="${sf}.tmp"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg phase "$to" --arg ts "$now" \
    '.cursor.phase = $phase | .current_phase = $phase | .last_gate_phase = $phase | .last_gate_timestamp = $ts' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_validate() {
  ensure_state_exists
  local sf
  sf="$(state_file)"

  python3 -m json.tool "$sf" > /dev/null || {
    echo "Error: invalid JSON in $sf" >&2
    exit 2
  }

  local required_fields=("run_id" "slug" "route" "cursor" "budget" "plans"
    "idempotency_keys" "review_dispositions" "review_effectiveness"
    "path_a_escalation" "self_verifications")

  for field in "${required_fields[@]}"; do
    local val
    val=$(jq "has(\"$field\")" "$sf")
    if [[ "$val" != "true" ]]; then
      echo "Error: missing required field: $field" >&2
      exit 2
    fi
  done

  local rd_type
  rd_type=$(jq -r '.review_dispositions | type' "$sf")
  if [[ "$rd_type" != "array" ]]; then
    echo "Error: review_dispositions must be array, got $rd_type" >&2
    exit 2
  fi

  echo "Valid"
}

cmd_disposition() {
  local subcmd="$1"; shift
  case "$subcmd" in
    append) cmd_disposition_append "$@" ;;
    *) echo "Error: unknown disposition subcommand: $subcmd" >&2; exit 2 ;;
  esac
}

cmd_disposition_append() {
  local review_round="" finding_id="" disposition="" confidence="" severity="" evidence="" path=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --review-round) review_round="$2"; shift 2 ;;
      --finding-id) finding_id="$2"; shift 2 ;;
      --disposition) disposition="$2"; shift 2 ;;
      --confidence) confidence="$2"; shift 2 ;;
      --severity) severity="$2"; shift 2 ;;
      --evidence) evidence="$2"; shift 2 ;;
      --path) path="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$finding_id" || -z "$disposition" ]]; then
    echo "Error: --finding-id and --disposition required" >&2
    exit 2
  fi

  if [[ "$disposition" == "accepted" && ( -z "$evidence" || "$evidence" == "" ) ]]; then
    echo "Error: --evidence required and must be non-empty for accepted disposition" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local tmp="${sf}.tmp"

  jq --arg rr "${review_round:-0}" --arg fid "$finding_id" --arg disp "$disposition" \
     --arg conf "${confidence:-0}" --arg sev "${severity:-M}" \
     --arg ev "${evidence:-}" --arg p "${path:-}" --arg ts "$now" \
    '.review_dispositions += [{"review_round": ($rr|tonumber), "finding_id": $fid, "disposition": $disp, "confidence": ($conf|tonumber), "severity": $sev, "evidence": $ev, "path": $p, "dispatched_at": $ts, "resolved_at": null}]' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_self_verify() {
  local subcmd="$1"; shift
  case "$subcmd" in
    append) cmd_self_verify_append "$@" ;;
    *) echo "Error: unknown self-verify subcommand: $subcmd" >&2; exit 2 ;;
  esac
}

cmd_self_verify_append() {
  local pack_id="" repair_round="" verification_passed="" exception=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pack-id) pack_id="$2"; shift 2 ;;
      --repair-round) repair_round="$2"; shift 2 ;;
      --verification-passed) verification_passed="$2"; shift 2 ;;
      --exception) exception="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local tmp="${sf}.tmp"

  jq --arg rid "$RUN_ID" --arg pid "${pack_id:-}" --arg rr "${repair_round:-0}" \
     --arg vp "${verification_passed:-yes}" --arg ex "${exception:-none}" --arg ts "$now" \
    '.self_verifications += [{"run_id": $rid, "pack_id": $pid, "repair_round": ($rr|tonumber), "verification_passed": $vp, "exception": $ex, "verified_at": $ts}]' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

# --- Main ---
if [[ $# -lt 1 ]]; then usage; fi

CMD="$1"; shift
RUN_ID=""

# Extract --run-id from remaining args
REMAINING_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    *) REMAINING_ARGS+=("$1"); shift ;;
  esac
done
set -- "${REMAINING_ARGS[@]+"${REMAINING_ARGS[@]}"}"

if [[ -z "$RUN_ID" && "$CMD" != "help" ]]; then
  echo "Error: --run-id is required" >&2
  exit 2
fi

case "$CMD" in
  init) cmd_init "$@" ;;
  read) cmd_read "$@" ;;
  update) cmd_update "$@" ;;
  transition) cmd_transition "$@" ;;
  validate) cmd_validate "$@" ;;
  disposition) cmd_disposition "$@" ;;
  self-verify) cmd_self_verify "$@" ;;
  *) echo "Error: unknown command: $CMD" >&2; usage ;;
esac
