#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"
LOCK_TTL=60

# Source shared lock primitives
source "$SCRIPT_DIR/lib/state-lock.sh"

usage() {
  cat <<'USAGE'
Usage: state.sh <command> [options]

Commands:
  init              Create initial workflow-state file
  read              Read a field from state
  update            Update a field in state
  transition        State machine transition with matrix validation
  validate          Validate state file against schema
  disposition       Manage review dispositions (append)
  self-verify       Manage self-verification records (append)
  path-a-escalation Manage Path A escalation entries
  agent-id          Get/set agent_id in execution-state (per Ruling 2)
  budget            Budget subcommands (initialize, check, increment-review)
  direction-check   Direction Check flow (trigger, ack)
  idempotency       Idempotency key management (check, append)
  plans             Plan management (add)

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

execution_state_file() {
  echo "${STATE_BASE}/execution-state-${RUN_ID}.json"
}

lock_dir() {
  echo "${STATE_BASE}/${RUN_ID}.lock"
}

acquire_lock() {
  state_lock_acquire "$(lock_dir)"
}

release_lock() {
  state_lock_release "$(lock_dir)"
}

ensure_state_exists() {
  local sf
  sf="$(state_file)"
  if [[ ! -f "$sf" ]]; then
    echo "Error: state file not found: $sf" >&2
    exit 2
  fi
}

# --- Transition Matrix ---
# Format: "actor:from:to" — wildcard * matches any value in that position
TRANSITION_MATRIX=(
  "Coordinator:pending:dispatched"
  "Coordinator:dispatched:returned"
  "Coordinator:returned:committed"
  "Coordinator:review_pending:pass"
  "Coordinator:review_pending:needs_repair"
  "Coordinator:*:blocked"
  "Coordinator:returned:repairing"
  "Coordinator:repairing:returned"
  "Coordinator:workflow:dispatched"
  "Coordinator:workflow:discovery"
  "Coordinator:workflow:plan-writing"
  "Coordinator:workflow:execution"
  "Coordinator:workflow:final-review"
  "Coordinator:discovery:plan-writing"
  "Coordinator:plan-writing:execution"
  "Coordinator:execution:final-review"
  "Coordinator:final-review:closed"
  "Coordinator:*:execution_done"
  "Coordinator:*:closed"
  "agent-return-handler:dispatched:returned"
  "track-execution-state:returned:committed"
)

transition_allowed() {
  local actor="$1" from="$2" to="$3"
  for entry in "${TRANSITION_MATRIX[@]}"; do
    local m_actor m_from m_to
    IFS=':' read -r m_actor m_from m_to <<< "$entry"
    if [[ "$m_actor" == "$actor" || "$m_actor" == "*" ]]; then
      if [[ "$m_from" == "$from" || "$m_from" == "*" ]]; then
        if [[ "$m_to" == "$to" || "$m_to" == "*" ]]; then
          return 0
        fi
      fi
    fi
  done
  return 1
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

  local budget_status review_total effort_total
  case "$route" in
    hotfix|quickfix|spike|maintenance)
      budget_status='"unlimited"'
      review_total='"unlimited"'
      effort_total='"unlimited"'
      ;;
    *)
      budget_status='"pending_plan_count"'
      review_total='null'
      effort_total='null'
      ;;
  esac

  cat > "$sf" <<INITJSON
{
  "run_id": "${RUN_ID}",
  "slug": "${slug}",
  "route": "${route}",
  "started_at": "${now}",
  "cursor": { "phase": "workflow", "reference": null, "step": null },
  "budget": {
    "budget_status": ${budget_status},
    "review_total": ${review_total},
    "review_used": 0,
    "effort_total": ${effort_total},
    "effort_used": 0,
    "direction_check_count": 0
  },
  "plan_count": null,
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
  "last_gate_timestamp": null,
  "mutations": []
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

  # Capture old value for mutation log
  local old_value
  old_value=$(jq "$field" "$sf" 2>/dev/null || echo "null")

  jq "$field = $value" "$sf" > "$tmp"
  mv "$tmp" "$sf"

  # Append mutation record
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq --arg f "$field" --argjson old "$old_value" --argjson new "$value" \
     --arg w "cmd_update" --arg ts "$now" \
    '.mutations += [{"field": $f, "old": $old, "new": $new, "writer": $w, "timestamp": $ts}]' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_transition() {
  local actor="" from="" to="" disposition_refs="" force=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --actor) actor="$2"; shift 2 ;;
      --from) from="$2"; shift 2 ;;
      --to) to="$2"; shift 2 ;;
      --disposition-refs) disposition_refs="$2"; shift 2 ;;
      --force) force="true"; shift ;;
      *) shift ;;
    esac
  done

  # Actor is required
  if [[ -z "$actor" ]]; then
    echo "Error: --actor is required for transition" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"

  # Read current phase from cursor
  local current_phase
  current_phase=$(jq -r '.cursor.phase // "unknown"' "$sf")

  # If --from not provided, use current cursor.phase
  if [[ -z "$from" ]]; then
    from="$current_phase"
  fi

  # Verify --from matches current state (unless --force)
  if [[ "$from" != "$current_phase" && "$force" != "true" ]]; then
    echo "Error: --from ($from) does not match current cursor.phase ($current_phase)" >&2
    exit 2
  fi

  # Validate against transition matrix
  if ! transition_allowed "$actor" "$from" "$to"; then
    echo "Transition denied: actor=$actor from=$from to=$to" >&2
    exit 2
  fi

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
    '.cursor.phase = $phase | .last_gate_phase = $phase | .last_gate_timestamp = $ts' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"

  # Append mutation record for transition
  jq --arg f ".cursor.phase" --arg old "$from" --arg new "$to" \
     --arg w "cmd_transition:${actor}" --arg ts "$now" \
    '.mutations += [{"field": $f, "old": $old, "new": $new, "writer": $w, "timestamp": $ts}]' \
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
    "path_a_escalation" "self_verifications"
    "execution_reflux_count" "last_gate_phase"
    "last_gate_timestamp" "pending_direction_check"
    "pending_post_push_reviews" "plan_writer_agent_id" "started_at")

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

  # --- Cross-file consistency checks (only when execution-state exists) ---
  local esf
  esf="$(execution_state_file)"
  if [[ -f "$esf" ]]; then
    # Check: committed packs must have commit_sha
    local committed_no_sha
    committed_no_sha=$(jq '[.plans | to_entries[] | .value.packs | to_entries[] | select(.value.status == "committed" and (.value.commit_sha == null or .value.commit_sha == ""))] | length' "$esf")
    if [[ "$committed_no_sha" -gt 0 ]]; then
      echo "Error: $committed_no_sha pack(s) with status=committed but no commit_sha in execution-state" >&2
      exit 2
    fi

    # Check: workflow-state plans have corresponding entries in execution-state
    local wf_plan_ids es_plan_ids
    wf_plan_ids=$(jq -r '[.plans[].plan_id] | sort | .[]' "$sf" 2>/dev/null)
    es_plan_ids=$(jq -r '[.plans | keys[]] | sort | .[]' "$esf" 2>/dev/null)
    for pid in $wf_plan_ids; do
      if ! echo "$es_plan_ids" | grep -qF "$pid"; then
        echo "Error: plan_id $pid in workflow-state but not in execution-state" >&2
        exit 2
      fi
    done
  fi

  # Check: accepted dispositions must have non-empty evidence
  local accepted_no_evidence
  accepted_no_evidence=$(jq '[.review_dispositions[] | select(.disposition == "accepted" and (.evidence == null or .evidence == ""))] | length' "$sf")
  if [[ "$accepted_no_evidence" -gt 0 ]]; then
    echo "Error: $accepted_no_evidence accepted disposition(s) with no evidence" >&2
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

  # Enum validation: only allow known disposition values
  case "$disposition" in
    accepted|rejected|suppress|path-a|path-b|duplicate|out-of-scope|needs-evidence|needs-evaluation|user-decision)
      ;;
    *)
      echo "Error: invalid disposition '$disposition'. Allowed: accepted|rejected|suppress|path-a|path-b|duplicate|out-of-scope|needs-evidence|needs-evaluation|user-decision" >&2
      exit 2
      ;;
  esac

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

cmd_path_a_escalation() {
  local subcmd="$1"; shift
  case "$subcmd" in
    start) cmd_pa_start "$@" ;;
    update) cmd_pa_update "$@" ;;
    clear) cmd_pa_clear "$@" ;;
    *) echo "Error: unknown path-a-escalation subcommand: $subcmd" >&2; exit 2 ;;
  esac
}

cmd_pa_start() {
  local finding_id="" round=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --finding-id) finding_id="$2"; shift 2 ;;
      --round) round="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"

  local existing
  existing=$(jq -r --arg fid "$finding_id" '[.path_a_escalation[] | select(.finding_id == $fid and .blocked_for_self_fix == true)] | length' "$sf")
  if [[ "$existing" -gt 0 ]]; then
    echo "Error: finding $finding_id already has a blocked path_a_escalation entry" >&2
    exit 2
  fi

  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local tmp="${sf}.tmp"
  jq --arg fid "$finding_id" --arg rnd "${round:-1}" --arg ts "$now" \
    '.path_a_escalation += [{"finding_id": $fid, "current_round": ($rnd|tonumber), "last_codex_verdict": null, "blocked_for_self_fix": false, "triggered_at": $ts}]' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_pa_update() {
  local finding_id="" verdict=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --finding-id) finding_id="$2"; shift 2 ;;
      --verdict) verdict="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"

  if [[ "$verdict" == "approved" ]]; then
    jq --arg fid "$finding_id" \
      '.path_a_escalation |= map(select(.finding_id != $fid))' \
      "$sf" > "$tmp"
    mv "$tmp" "$sf"
  elif [[ "$verdict" == "needs_repair" ]]; then
    jq --arg fid "$finding_id" \
      '.path_a_escalation |= map(if .finding_id == $fid then .blocked_for_self_fix = true | .last_codex_verdict = "needs_repair" else . end)' \
      "$sf" > "$tmp"
    mv "$tmp" "$sf"
  fi
}

cmd_pa_clear() {
  local finding_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --finding-id) finding_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"
  jq --arg fid "$finding_id" \
    '.path_a_escalation |= map(select(.finding_id != $fid))' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

# --- agent-id subcommand (operates on execution-state per Ruling 2) ---
cmd_agent_id() {
  local subcmd="$1"; shift
  case "$subcmd" in
    set) cmd_agent_id_set "$@" ;;
    get) cmd_agent_id_get "$@" ;;
    *) echo "Error: unknown agent-id subcommand: $subcmd (use set|get)" >&2; exit 2 ;;
  esac
}

cmd_agent_id_set() {
  local pack_id="" agent_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pack-id) pack_id="$2"; shift 2 ;;
      --agent-id) agent_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$pack_id" || -z "$agent_id" ]]; then
    echo "Error: --pack-id and --agent-id required for agent-id set" >&2
    exit 2
  fi

  local esf
  esf="$(execution_state_file)"
  if [[ ! -f "$esf" ]]; then
    echo "Error: execution-state file not found: $esf" >&2
    exit 2
  fi

  acquire_lock
  trap release_lock EXIT

  local tmp="${esf}.tmp"
  jq --arg pid "$pack_id" --arg aid "$agent_id" '
    .plans |= with_entries(
      .value.packs |= with_entries(
        if .key == $pid then .value.agent_id = $aid else . end
      )
    )
  ' "$esf" > "$tmp"
  mv "$tmp" "$esf"
}

cmd_agent_id_get() {
  local pack_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pack-id) pack_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$pack_id" ]]; then
    echo "Error: --pack-id required for agent-id get" >&2
    exit 2
  fi

  local esf
  esf="$(execution_state_file)"
  if [[ ! -f "$esf" ]]; then
    echo ""
    return 0
  fi

  local result
  result=$(jq -r --arg pid "$pack_id" '
    [.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.agent_id // empty] | first // empty
  ' "$esf" 2>/dev/null || echo "")

  if [[ "$result" == "null" ]]; then
    echo ""
  else
    echo "$result"
  fi
}

# --- budget subcommand ---
cmd_budget() {
  local subcmd="$1"; shift
  case "$subcmd" in
    initialize) cmd_budget_initialize "$@" ;;
    check) cmd_budget_check "$@" ;;
    increment-review) cmd_budget_increment_review "$@" ;;
    *) echo "Error: unknown budget subcommand: $subcmd (use initialize|check|increment-review)" >&2; exit 2 ;;
  esac
}

cmd_budget_initialize() {
  local plan_count=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-count) plan_count="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_count" ]]; then
    echo "Error: --plan-count required for budget initialize" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"

  local current_status
  current_status=$(jq -r '.budget.budget_status // "unknown"' "$sf")
  if [[ "$current_status" != "pending_plan_count" ]]; then
    echo "Error: budget already initialized (status=$current_status). Can only initialize from pending_plan_count." >&2
    exit 2
  fi

  local review_total=$((3 * plan_count + 12))
  local effort_total=$((review_total * 2))

  local tmp="${sf}.tmp"
  jq --argjson rt "$review_total" --argjson et "$effort_total" --argjson pc "$plan_count" \
    '.budget.budget_status = "initialized" | .budget.review_total = $rt | .budget.effort_total = $et | .plan_count = $pc' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_budget_check() {
  ensure_state_exists
  local sf
  sf="$(state_file)"

  local status
  status=$(jq -r '.budget.budget_status // "unknown"' "$sf")

  if [[ "$status" == "pending_plan_count" ]]; then
    echo "Error: budget not initialized (status=pending_plan_count). Run 'budget initialize --plan-count N' first." >&2
    exit 2
  fi

  if [[ "$status" == "unlimited" ]]; then
    echo "OK: unlimited"
    exit 0
  fi

  local review_total review_used
  review_total=$(jq -r '.budget.review_total' "$sf")
  review_used=$(jq -r '.budget.review_used' "$sf")

  if [[ "$review_used" -ge "$review_total" ]] 2>/dev/null; then
    echo "EXHAUSTED: review budget ${review_used}/${review_total}" >&2
    exit 2
  fi

  echo "OK: ${review_used}/${review_total}"
  exit 0
}

cmd_budget_increment_review() {
  ensure_state_exists
  local sf
  sf="$(state_file)"

  acquire_lock
  trap release_lock EXIT

  local status
  status=$(jq -r '.budget.budget_status // "unknown"' "$sf")
  if [[ "$status" == "pending_plan_count" ]]; then
    echo "Error: budget not initialized (status=pending_plan_count). Run 'budget initialize --plan-count N' first." >&2
    exit 2
  fi

  local tmp="${sf}.tmp"
  jq '.budget.review_used += 1' "$sf" > "$tmp"
  mv "$tmp" "$sf"

  local used total needs_dc=false msg
  used=$(jq -r '.budget.review_used' "$sf")
  total=$(jq -r '.budget.review_total' "$sf")

  if [[ "$total" == "unlimited" ]]; then
    msg="Review budget: ${used} dispatches used (unlimited)."
  elif [[ "$used" -ge "$total" ]] 2>/dev/null; then
    msg="BUDGET EXHAUSTED: ${used}/${total}. Stop dispatching reviews and report to user."
  elif [[ "$used" -ge "$(( total * 80 / 100 ))" ]] 2>/dev/null; then
    local current_dc
    current_dc=$(jq -r '.pending_direction_check // "null"' "$sf")
    if [[ "$current_dc" == "null" ]]; then
      needs_dc=true
    fi
    msg="DIRECTION CHECK: Review budget at ${used}/${total} (>=80%). Confirm with user."
  else
    msg="Review budget: ${used}/${total} dispatches used."
  fi

  release_lock
  trap - EXIT

  if [[ "$needs_dc" == "true" ]]; then
    cmd_dc_trigger --type review --threshold-percent 80 >/dev/null
  fi

  echo "$msg"
}

# --- direction-check subcommand ---
cmd_direction_check() {
  local subcmd="$1"; shift
  case "$subcmd" in
    trigger) cmd_dc_trigger "$@" ;;
    ack) cmd_dc_ack "$@" ;;
    *) echo "Error: unknown direction-check subcommand: $subcmd (use trigger|ack)" >&2; exit 2 ;;
  esac
}

cmd_dc_trigger() {
  local dc_type="" threshold_percent=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --type) dc_type="$2"; shift 2 ;;
      --threshold-percent) threshold_percent="$2"; shift 2 ;;
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

  jq --arg ts "$now" --arg dt "${dc_type:-review}" --arg tp "${threshold_percent:-80}" \
    '.pending_direction_check = {"triggered_at": $ts, "threshold_type": $dt, "threshold_percent": ($tp|tonumber), "ack_status": "pending"} | .budget.direction_check_count += 1' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_dc_ack() {
  local action=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --action) action="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$action" ]]; then
    echo "Error: --action required (continue|stop|adjust)" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"

  case "$action" in
    continue)
      jq '.pending_direction_check.ack_status = "acknowledged"' "$sf" > "$tmp"
      mv "$tmp" "$sf"
      ;;
    stop)
      jq '.pending_direction_check.ack_status = "stopped"' "$sf" > "$tmp"
      mv "$tmp" "$sf"
      ;;
    adjust)
      jq '.pending_direction_check = null' "$sf" > "$tmp"
      mv "$tmp" "$sf"
      ;;
    *)
      echo "Error: unknown action: $action (use continue|stop|adjust)" >&2
      exit 2
      ;;
  esac
}

# --- idempotency subcommand ---
cmd_idempotency() {
  local subcmd="$1"; shift
  case "$subcmd" in
    check) cmd_idempotency_check "$@" ;;
    append) cmd_idempotency_append "$@" ;;
    *) echo "Error: unknown idempotency subcommand: $subcmd (use check|append)" >&2; exit 2 ;;
  esac
}

cmd_idempotency_check() {
  local key=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --key) key="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$key" ]]; then
    echo "Error: --key required for idempotency check" >&2
    exit 2
  fi

  ensure_state_exists
  local sf
  sf="$(state_file)"

  local existing
  existing=$(jq -r --arg key "$key" '.idempotency_keys | index($key) // empty' "$sf")
  if [[ -n "$existing" ]]; then
    echo "DUPLICATE" >&2
    exit 2
  fi

  echo "NEW"
  exit 0
}

cmd_idempotency_append() {
  local key=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --key) key="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$key" ]]; then
    echo "Error: --key required for idempotency append" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"
  jq --arg key "$key" '.idempotency_keys += [$key]' "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

# --- plans subcommand ---
cmd_plans() {
  local subcmd="$1"; shift
  case "$subcmd" in
    add) cmd_plans_add "$@" ;;
    *) echo "Error: unknown plans subcommand: $subcmd (use add)" >&2; exit 2 ;;
  esac
}

cmd_plans_add() {
  local plan_id="" status="pending"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --status) status="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  if [[ -z "$plan_id" ]]; then
    echo "Error: --plan-id required" >&2
    exit 2
  fi
  ensure_state_exists
  acquire_lock
  trap release_lock EXIT
  local sf
  sf="$(state_file)"
  jq --arg pid "$plan_id" --arg st "$status" \
    '.plans += [{"plan_id": $pid, "status": $st}]' \
    "$sf" > "${sf}.tmp" && mv "${sf}.tmp" "$sf"
  release_lock
  trap - EXIT
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
  path-a-escalation) cmd_path_a_escalation "$@" ;;
  agent-id) cmd_agent_id "$@" ;;
  budget) cmd_budget "$@" ;;
  direction-check) cmd_direction_check "$@" ;;
  idempotency) cmd_idempotency "$@" ;;
  plans) cmd_plans "$@" ;;
  *) echo "Error: unknown command: $CMD" >&2; usage ;;
esac
