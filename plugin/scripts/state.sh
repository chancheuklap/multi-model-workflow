#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_BASE="${STATE_BASE:-.claude/multi-model-workflow}"
LOCK_TTL=60

# Budget formula constants (P4: extracted for auditability and override support)
REVIEW_PER_PLAN=3
REVIEW_FIXED_RESERVE=12
MAX_OVERRIDES=2

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
  agent-id          Get/set agent_id in execution-state (per Ruling 2)
  execution-plan    Manage execution-state plan boundaries (start)
  budget            Budget subcommands (initialize, reinitialize, unlimited, check, increment-review, credit)
  set-attendance    Set attendance mode (attended|afk)
  direction-check   Direction Check flow (trigger, ack)
  idempotency       Idempotency key management (check, append)
  review-history    Append a row to a design/plan document's Review History table
  merge-brief       Manage merge-brief lifecycle (init, stage, verify)
  verdict-route     Query mechanical verdict routing from routes-v1.json (--phase, --verdict)
  checkbox          Toggle committed-pack checkboxes in plan doc (toggle --plan-id --plan-file)
  envelope          Build DISPATCH_ENVELOPE block (build --phase --agent-role [--plan-id|--pack-id] ...)

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

# --- Transition Matrix (fallback) ---
# Format: "actor:from:to" — wildcard * matches any value in that position.
# Machine source of truth is state-schema/routes-v1.json (global_transitions ∪
# routes[route].phase_transitions). This array is retained as the fail-open
# fallback: if the manifest is unreadable or the route is unknown,
# transition_allowed() matches against this full matrix (legacy behavior, never
# stricter). Keep it equivalent to (global_transitions ∪ formal.phase_transitions).
TRANSITION_MATRIX=(
  "Coordinator:pending:dispatched"
  "Coordinator:pending:in_progress"
  "Coordinator:dispatched:returned"
  "Coordinator:returned:committed"
  "Coordinator:returned:review_pending"
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
)

# --- routes-v1.json reader (thin jq lookups) ---
ROUTES_MANIFEST="${SCRIPT_DIR}/../state-schema/routes-v1.json"

# routes_load — succeed (0) iff the manifest exists and parses as JSON.
routes_load() {
  [[ -f "$ROUTES_MANIFEST" ]] && jq -e . "$ROUTES_MANIFEST" >/dev/null 2>&1
}

# route_field <route> <jq-path>
# Echo a field from routes[<route>] using the given jq path (relative to the
# route record). Returns empty string on any failure. Thin helper for cmd_init.
route_field() {
  local route="$1" path="$2"
  routes_load || { echo ""; return 0; }
  jq -r --arg r "$route" ".routes[\$r]${path} // empty" "$ROUTES_MANIFEST" 2>/dev/null || echo ""
}

# _matrix_match <actor> <from> <to> <candidate...> (reads candidate set on stdin)
# Apply the existing actor:from:to wildcard match against a newline-separated
# candidate set read from stdin. Returns 0 on match, 1 otherwise.
_matrix_match() {
  local actor="$1" from="$2" to="$3"
  local entry m_actor m_from m_to
  while IFS= read -r entry; do
    [[ -z "$entry" ]] && continue
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

# transition_allowed <actor> <from> <to> [route]
# Route-aware + fail-open. When a route is supplied AND the manifest is readable
# AND routes[route] exists, the candidate set is
#   global_transitions ∪ routes[route].phase_transitions
# and the existing wildcard match runs against it (light is thereby denied
# workflow:discovery — the P2 core behavior). Otherwise (no route / unreadable
# manifest / unknown route) it falls back to the built-in TRANSITION_MATRIX full
# match — legacy behavior, never stricter.
transition_allowed() {
  local actor="$1" from="$2" to="$3" route="${4:-}"

  if [[ -n "$route" ]] && routes_load; then
    if jq -e --arg r "$route" '.routes[$r]' "$ROUTES_MANIFEST" >/dev/null 2>&1; then
      local candidates
      candidates=$(jq -r --arg r "$route" \
        '(.global_transitions + .routes[$r].phase_transitions)[]' \
        "$ROUTES_MANIFEST" 2>/dev/null)
      if [[ -n "$candidates" ]]; then
        _matrix_match "$actor" "$from" "$to" <<< "$candidates"
        return $?
      fi
    fi
  fi

  # Fail-open fallback: built-in matrix (legacy behavior).
  printf '%s\n' "${TRANSITION_MATRIX[@]}" | _matrix_match "$actor" "$from" "$to"
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

  # route → initial budget profile, read from routes-v1.json[route].budget.init.
  # unlimited        → budget_status/review_total all "unlimited"
  # pending_plan_count → budget_status="pending_plan_count", totals null (formal)
  # Fail-open: manifest unreadable / route unknown → pending_plan_count default
  # (matches the legacy `case "$route"` *) branch).
  local budget_status review_total budget_init
  budget_init=$(route_field "$route" ".budget.init")
  case "$budget_init" in
    unlimited)
      budget_status='"unlimited"'
      review_total='"unlimited"'
      ;;
    *)
      budget_status='"pending_plan_count"'
      review_total='null'
      ;;
  esac

  cat > "$sf" <<INITJSON
{
  "run_id": "${RUN_ID}",
  "slug": "${slug}",
  "route": "${route}",
  "commit_format_override": null,
  "started_at": "${now}",
  "cursor": { "phase": "workflow", "reference": null, "step": null },
  "attendance_mode": "afk",
  "budget": {
    "budget_status": ${budget_status},
    "review_total": ${review_total},
    "review_used": 0,
    "review_credit": 0,
    "budget_profile": "standard",
    "override_count": 0,
    "direction_check_count": 0
  },
  "plan_count": null,
  "plans": [],
  "idempotency_keys": [],
  "plan_writer_agent_id": null,
  "review_dispositions": [],
  "pending_post_push_reviews": [],
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

  # Capture old value before write (only needed for DEBUG mutation log)
  local old_value="null"
  if [[ "${STATE_DEBUG:-}" == "1" ]]; then
    old_value=$(jq "$field" "$sf" 2>/dev/null || echo "null")
  fi

  jq "$field = $value" "$sf" > "$tmp"
  mv "$tmp" "$sf"

  # Append mutation record only when STATE_DEBUG=1
  if [[ "${STATE_DEBUG:-}" == "1" ]]; then
    local now
    now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg f "$field" --argjson old "$old_value" --argjson new "$value" \
       --arg w "cmd_update" --arg ts "$now" \
      '.mutations += [{"field": $f, "old": $old, "new": $new, "writer": $w, "timestamp": $ts}]' \
      "$sf" > "$tmp"
    mv "$tmp" "$sf"
  fi
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

  # Read route for route-aware transition validation (fail-open if absent).
  local route
  route=$(jq -r '.route // empty' "$sf" 2>/dev/null)

  # If --from not provided, use current cursor.phase
  if [[ -z "$from" ]]; then
    from="$current_phase"
  fi

  # Verify --from matches current state (unless --force)
  if [[ "$from" != "$current_phase" && "$force" != "true" ]]; then
    echo "Error: --from ($from) does not match current cursor.phase ($current_phase)" >&2
    exit 2
  fi

  # Validate against transition matrix (route-aware; fail-open to full matrix)
  if ! transition_allowed "$actor" "$from" "$to" "$route"; then
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

  # Append mutation record for transition only when STATE_DEBUG=1
  if [[ "${STATE_DEBUG:-}" == "1" ]]; then
    jq --arg f ".cursor.phase" --arg old "$from" --arg new "$to" \
       --arg w "cmd_transition:${actor}" --arg ts "$now" \
      '.mutations += [{"field": $f, "old": $old, "new": $new, "writer": $w, "timestamp": $ts}]' \
      "$sf" > "$tmp"
    mv "$tmp" "$sf"
  fi
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
    "idempotency_keys" "review_dispositions"
    "self_verifications"
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

  # Pack 2.8 (Plan 002 R3): accepted dispositions, IF they carry a
  # coordinator_verified_evidence key, must not have it as empty string.
  # null / absent is backward-compatible (pre-Plan-002 state files and
  # dispositions recorded without the new flag). The intent: prevent
  # repair workers from running with an explicitly-blank verification.
  local accepted_blank_cve
  accepted_blank_cve=$(jq '[.review_dispositions[] | select(.disposition == "accepted" and has("coordinator_verified_evidence") and .coordinator_verified_evidence == "")] | length' "$sf")
  if [[ "$accepted_blank_cve" -gt 0 ]]; then
    echo "Error: $accepted_blank_cve accepted disposition(s) with explicitly empty coordinator_verified_evidence" >&2
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
  local plan_id="" coord_verified_evidence=""
  local coord_verified_evidence_set="false"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --review-round) review_round="$2"; shift 2 ;;
      --finding-id) finding_id="$2"; shift 2 ;;
      --disposition) disposition="$2"; shift 2 ;;
      --confidence) confidence="$2"; shift 2 ;;
      --severity) severity="$2"; shift 2 ;;
      --evidence) evidence="$2"; shift 2 ;;
      --path) path="$2"; shift 2 ;;
      --plan-id) plan_id="$2"; shift 2 ;;
      --coordinator-verified-evidence) coord_verified_evidence="$2"; coord_verified_evidence_set="true"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$finding_id" || -z "$disposition" ]]; then
    echo "Error: --finding-id and --disposition required" >&2
    exit 2
  fi

  # Enum validation: only allow known disposition values
  case "$disposition" in
    accepted|rejected|suppress|path-b|duplicate|out-of-scope|needs-evidence|needs-evaluation|user-decision)
      ;;
    *)
      echo "Error: invalid disposition '$disposition'. Allowed: accepted|rejected|suppress|path-b|duplicate|out-of-scope|needs-evidence|needs-evaluation|user-decision" >&2
      exit 2
      ;;
  esac

  if [[ "$disposition" == "accepted" && ( -z "$evidence" || "$evidence" == "" ) ]]; then
    echo "Error: --evidence required and must be non-empty for accepted disposition" >&2
    exit 2
  fi

  # Pack 2.8: if --coordinator-verified-evidence is provided for accepted disposition,
  # it must be non-empty. This guards the explicit "I verified this" path. When the
  # flag is omitted entirely the field stays null (backward-compatible with pre-Plan-002
  # state and old fixtures); enforcement at validate time is likewise null-tolerant.
  if [[ "$disposition" == "accepted" && "$coord_verified_evidence_set" == "true" && -z "$coord_verified_evidence" ]]; then
    echo "Error: --coordinator-verified-evidence cannot be empty for accepted disposition" >&2
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

  # Build plan_id / coordinator_verified_evidence JSON values.
  # Use jq --argjson with raw JSON strings so null vs "" stays distinct.
  local plan_id_json="null"
  if [[ -n "$plan_id" ]]; then
    plan_id_json=$(jq -nc --arg v "$plan_id" '$v')
  fi
  local cve_json="null"
  if [[ "$coord_verified_evidence_set" == "true" ]]; then
    cve_json=$(jq -nc --arg v "$coord_verified_evidence" '$v')
  fi

  jq --arg rr "${review_round:-0}" --arg fid "$finding_id" --arg disp "$disposition" \
     --arg conf "${confidence:-0}" --arg sev "${severity:-M}" \
     --arg ev "${evidence:-}" --arg p "${path:-}" --arg ts "$now" \
     --argjson pid "$plan_id_json" --argjson cve "$cve_json" \
    '.review_dispositions += [{"review_round": ($rr|tonumber), "finding_id": $fid, "disposition": $disp, "confidence": ($conf|tonumber), "severity": $sev, "evidence": $ev, "path": $p, "dispatched_at": $ts, "resolved_at": null, "plan_id": $pid, "coordinator_verified_evidence": $cve}]' \
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

  # When STATE_DEBUG is not set, this is a no-op (exit 0) — callers in SKILL references
  # still invoke it without error; the field remains an empty array in production.
  if [[ "${STATE_DEBUG:-}" != "1" ]]; then
    return 0
  fi

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
  local pack_id="" plan_id="" agent_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pack-id) pack_id="$2"; shift 2 ;;
      --plan-id) plan_id="$2"; shift 2 ;;
      --agent-id) agent_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -n "$pack_id" && -n "$plan_id" ]]; then
    echo "Error: --pack-id and --plan-id are mutually exclusive for agent-id set" >&2
    exit 2
  fi
  if [[ -z "$pack_id" && -z "$plan_id" ]]; then
    echo "Error: one of --pack-id or --plan-id required for agent-id set" >&2
    exit 2
  fi
  if [[ -z "$agent_id" ]]; then
    echo "Error: --agent-id required for agent-id set" >&2
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
  if [[ -n "$plan_id" ]]; then
    # plan-level: write to .plans[plan_id].worker_agent_id (per Pack 2.5 schema)
    if ! jq -e --arg pid "$plan_id" '.plans[$pid] != null' "$esf" >/dev/null; then
      echo "Error: plan_id $plan_id not found in execution-state" >&2
      exit 2
    fi
    jq --arg pid "$plan_id" --arg aid "$agent_id" \
      '.plans[$pid].worker_agent_id = $aid' "$esf" > "$tmp"
    mv "$tmp" "$esf"
  else
    # pack-level: legacy path under .plans[*].packs[pack_id].agent_id
    jq --arg pid "$pack_id" --arg aid "$agent_id" '
      .plans |= with_entries(
        .value.packs |= with_entries(
          if .key == $pid then .value.agent_id = $aid else . end
        )
      )
    ' "$esf" > "$tmp"
    mv "$tmp" "$esf"
  fi
}

cmd_agent_id_get() {
  local pack_id="" plan_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pack-id) pack_id="$2"; shift 2 ;;
      --plan-id) plan_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -n "$pack_id" && -n "$plan_id" ]]; then
    echo "Error: --pack-id and --plan-id are mutually exclusive for agent-id get" >&2
    exit 2
  fi
  if [[ -z "$pack_id" && -z "$plan_id" ]]; then
    echo "Error: one of --pack-id or --plan-id required for agent-id get" >&2
    exit 2
  fi

  local esf
  esf="$(execution_state_file)"
  if [[ ! -f "$esf" ]]; then
    echo ""
    return 0
  fi

  local result
  if [[ -n "$plan_id" ]]; then
    result=$(jq -r --arg pid "$plan_id" '.plans[$pid].worker_agent_id // empty' "$esf" 2>/dev/null || echo "")
  else
    result=$(jq -r --arg pid "$pack_id" '
      [.plans | to_entries[] | .value.packs // {} | to_entries[] | select(.key == $pid) | .value.agent_id // empty] | first // empty
    ' "$esf" 2>/dev/null || echo "")
  fi

  if [[ "$result" == "null" ]]; then
    echo ""
  else
    echo "$result"
  fi
}

# --- execution-plan subcommand (operates on execution-state plan boundaries) ---
cmd_execution_plan() {
  local subcmd="$1"; shift
  case "$subcmd" in
    start) cmd_execution_plan_start "$@" ;;
    complete) cmd_execution_plan_complete "$@" ;;
    *) echo "Error: unknown execution-plan subcommand: $subcmd (use start|complete)" >&2; exit 2 ;;
  esac
}

# Plan 005 Pack 5.7: execution-plan complete — marks a Plan as worker-finished.
# Writes .plans[plan_id].finished_at + .plans[plan_id].worker_verdict.
cmd_execution_plan_complete() {
  local plan_id="" verdict=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --verdict) verdict="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_id" || -z "$verdict" ]]; then
    echo "Error: --plan-id and --verdict required for execution-plan complete" >&2
    exit 2
  fi

  case "$verdict" in
    pass|partial-pass|blocked|need-fresh-worker|needs-context|needs-plan-revision) ;;
    *)
      echo "Error: invalid verdict '$verdict'. Allowed: pass|partial-pass|blocked|need-fresh-worker|needs-context|needs-plan-revision" >&2
      exit 2
      ;;
  esac

  local esf
  esf="$(execution_state_file)"
  if [[ ! -f "$esf" ]]; then
    echo "Error: execution-state file not found: $esf" >&2
    exit 2
  fi
  if ! jq -e --arg pid "$plan_id" '.plans[$pid] != null' "$esf" >/dev/null 2>&1; then
    echo "Error: plan_id $plan_id not found in execution-state" >&2
    exit 2
  fi

  acquire_lock
  trap release_lock EXIT

  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local tmp="${esf}.tmp"
  jq --arg pid "$plan_id" --arg v "$verdict" --arg ts "$now" '
    .plans[$pid].finished_at = $ts
    | .plans[$pid].worker_verdict = $v
  ' "$esf" > "$tmp"
  mv "$tmp" "$esf"
}

# Plan 005 Pack 5.7: pack-progress — Worker calls this after each Pack commit.
# Writes .plans[plan_id].packs[pack_id].status + .commit_sha.
cmd_pack_progress() {
  local plan_id="" pack_id="" status="" commit_sha=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --pack-id) pack_id="$2"; shift 2 ;;
      --status) status="$2"; shift 2 ;;
      --commit-sha) commit_sha="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_id" || -z "$pack_id" || -z "$status" ]]; then
    echo "Error: --plan-id, --pack-id, --status required for pack-progress" >&2
    exit 2
  fi

  case "$status" in
    committed|blocked|skipped) ;;
    *)
      echo "Error: invalid status '$status'. Allowed: committed|blocked|skipped" >&2
      exit 2
      ;;
  esac

  local esf
  esf="$(execution_state_file)"
  if [[ ! -f "$esf" ]]; then
    echo "Error: execution-state file not found: $esf" >&2
    exit 2
  fi
  if ! jq -e --arg pid "$plan_id" --arg packid "$pack_id" \
      '.plans[$pid].packs[$packid] != null' "$esf" >/dev/null 2>&1; then
    echo "Error: plan_id $plan_id / pack_id $pack_id not found in execution-state" >&2
    exit 2
  fi

  acquire_lock
  trap release_lock EXIT

  local tmp="${esf}.tmp"
  if [[ -n "$commit_sha" ]]; then
    jq --arg pid "$plan_id" --arg packid "$pack_id" --arg s "$status" --arg sha "$commit_sha" '
      .plans[$pid].packs[$packid].status = $s
      | .plans[$pid].packs[$packid].commit_sha = $sha
    ' "$esf" > "$tmp"
  else
    jq --arg pid "$plan_id" --arg packid "$pack_id" --arg s "$status" '
      .plans[$pid].packs[$packid].status = $s
    ' "$esf" > "$tmp"
  fi
  mv "$tmp" "$esf"
}

# Plan 005 Pack 5.7: plan-returns ingest — agent-return-handler calls this.
# Reads plan-returns/<run_id>/<plan_id>/plan-return.json, validates schema,
# expands per_pack into execution-state, mirrors verdict.
cmd_plan_returns() {
  local subcmd="$1"; shift
  case "$subcmd" in
    ingest) cmd_plan_returns_ingest "$@" ;;
    *) echo "Error: unknown plan-returns subcommand: $subcmd (use ingest)" >&2; exit 2 ;;
  esac
}

cmd_plan_returns_ingest() {
  local plan_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_id" ]]; then
    echo "Error: --plan-id required for plan-returns ingest" >&2
    exit 2
  fi

  local pr_file="${STATE_BASE}/plan-returns/${RUN_ID}/${plan_id}/plan-return.json"
  if [[ ! -f "$pr_file" ]]; then
    echo "Error: plan-return.json not found at: $pr_file" >&2
    exit 2
  fi
  if ! jq empty "$pr_file" 2>/dev/null; then
    echo "Error: plan-return.json is not valid JSON" >&2
    exit 2
  fi

  # Minimal schema check: schema_version=1, has run_id/plan_id/verdict/per_pack
  local sv verdict
  sv=$(jq -r '.schema_version // empty' "$pr_file")
  verdict=$(jq -r '.verdict // empty' "$pr_file")
  if [[ "$sv" != "1" ]]; then
    echo "Error: plan-return schema_version expected '1', got '$sv'" >&2
    exit 2
  fi
  case "$verdict" in
    pass|partial-pass|blocked|need-fresh-worker|needs-context|needs-plan-revision) ;;
    *) echo "Error: invalid verdict '$verdict'" >&2; exit 2 ;;
  esac
  if ! jq -e '.per_pack | type == "object"' "$pr_file" >/dev/null 2>&1; then
    echo "Error: plan-return missing per_pack object" >&2
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
  # Merge per_pack entries into .plans[plan_id].packs and write worker_verdict
  jq --arg pid "$plan_id" --slurpfile pr "$pr_file" '
    . as $base
    | ($pr[0].per_pack // {}) as $pp
    | .plans[$pid].worker_verdict = $pr[0].verdict
    | .plans[$pid].packs = (
        ($base.plans[$pid].packs // {}) as $cur
        | reduce ($pp | to_entries[]) as $e
          ($cur; .[$e.key] = ((.[$e.key] // {}) + ($e.value)))
      )
  ' "$esf" > "$tmp"
  mv "$tmp" "$esf"
}

cmd_execution_plan_start() {
  local plan_id="" start_commit=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --start-commit) start_commit="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_id" || -z "$start_commit" ]]; then
    echo "Error: --plan-id and --start-commit required for execution-plan start" >&2
    exit 2
  fi

  local esf
  esf="$(execution_state_file)"
  if [[ ! -f "$esf" ]]; then
    echo "Error: execution-state file not found: $esf" >&2
    exit 2
  fi

  if ! jq -e --arg pid "$plan_id" '.plans[$pid] != null' "$esf" >/dev/null; then
    echo "Error: plan_id $plan_id not found in execution-state" >&2
    exit 2
  fi

  local existing_start
  existing_start=$(jq -r --arg pid "$plan_id" '.plans[$pid].start_commit // empty' "$esf")
  if [[ -n "$existing_start" && "$existing_start" != "$start_commit" ]]; then
    echo "Error: plan_id $plan_id already has start_commit=$existing_start" >&2
    exit 2
  fi

  acquire_lock
  trap release_lock EXIT

  local tmp="${esf}.tmp"
  jq --arg pid "$plan_id" --arg sha "$start_commit" '
    .current_plan_id = $pid
    | .plans[$pid].status = "in_progress"
    | .plans[$pid].start_commit = $sha
  ' "$esf" > "$tmp"
  mv "$tmp" "$esf"
}

# --- budget subcommand ---
cmd_budget() {
  local subcmd="$1"; shift
  case "$subcmd" in
    initialize) cmd_budget_initialize "$@" ;;
    reinitialize) cmd_budget_reinitialize "$@" ;;
    unlimited) cmd_budget_unlimited "$@" ;;
    check) cmd_budget_check "$@" ;;
    increment-review) cmd_budget_increment_review "$@" ;;
    credit) cmd_budget_credit "$@" ;;
    *) echo "Error: unknown budget subcommand: $subcmd (use initialize|reinitialize|unlimited|check|increment-review|credit)" >&2; exit 2 ;;
  esac
}

cmd_budget_initialize() {
  local plan_count="" review_total_override="" profile_override=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-count) plan_count="$2"; shift 2 ;;
      --review-total) review_total_override="$2"; shift 2 ;;
      --profile) profile_override="$2"; shift 2 ;;
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

  local review_total budget_profile
  if [[ -n "$review_total_override" ]]; then
    # Direct override: skip formula
    review_total="$review_total_override"
    budget_profile="custom"
  elif [[ -n "$profile_override" ]]; then
    # Profile-based formula
    local per_plan fixed_reserve
    case "$profile_override" in
      standard) per_plan=$REVIEW_PER_PLAN; fixed_reserve=$REVIEW_FIXED_RESERVE ;;
      generous)  per_plan=4; fixed_reserve=16 ;;
      tight)     per_plan=2; fixed_reserve=6 ;;
      *) echo "Error: unknown --profile '$profile_override' (use standard|generous|tight)" >&2; exit 2 ;;
    esac
    review_total=$(( per_plan * plan_count + fixed_reserve ))
    budget_profile="$profile_override"
  else
    # Default: standard formula using constants
    review_total=$(( REVIEW_PER_PLAN * plan_count + REVIEW_FIXED_RESERVE ))
    budget_profile="standard"
  fi

  local tmp="${sf}.tmp"
  jq --argjson rt "$review_total" --argjson pc "$plan_count" --arg bp "$budget_profile" \
    '.budget.budget_status = "initialized" | .budget.review_total = $rt | .budget.budget_profile = $bp | .plan_count = $pc' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

# cmd_budget_reinitialize — one-way Light→Formal escape-hatch upgrade.
# Mirror image of cmd_budget_initialize's entry guard: this command ONLY accepts
# an `unlimited` entry (light run), converting it to a bounded formal budget.
# initialize protects "fresh formal run starts from pending_plan_count"; this
# command serves the escape hatch (light discovered to be a big change). Atomically:
#   budget_status unlimited → initialized + review_total + plan_count
#   route → "formal" (升级门同步翻 formal so every formal gate auto re-arms).
# Formula: standard profile (REVIEW_PER_PLAN*P + REVIEW_FIXED_RESERVE).
# reinitialize does not accept --profile/--review-total; use initialize for custom budgets.
cmd_budget_reinitialize() {
  local plan_count=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-count) plan_count="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_count" ]]; then
    echo "Error: --plan-count required for budget reinitialize" >&2
    exit 2
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"

  local current_status
  current_status=$(jq -r '.budget.budget_status // "unknown"' "$sf")
  if [[ "$current_status" != "unlimited" ]]; then
    echo "Error: reinitialize only valid from unlimited (escape-hatch Light→Formal upgrade, status=$current_status). Use 'budget initialize' for fresh formal runs." >&2
    exit 2
  fi

  local review_total=$(( REVIEW_PER_PLAN * plan_count + REVIEW_FIXED_RESERVE ))

  local tmp="${sf}.tmp"
  jq --argjson rt "$review_total" --argjson pc "$plan_count" \
    '.budget.budget_status = "initialized"
     | .budget.review_total = $rt
     | .budget.budget_profile = "standard"
     | .plan_count = $pc
     | .route = "formal"' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"
}

cmd_budget_unlimited() {
  local route=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --route) route="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  ensure_state_exists
  local sf
  sf="$(state_file)"

  local current_status
  current_status=$(jq -r '.budget.budget_status' "$sf")
  if [[ "$current_status" == "initialized" ]]; then
    echo "Error: cannot change initialized bounded budget to unlimited" >&2
    exit 2
  fi

  acquire_lock
  trap release_lock EXIT

  local tmp="${sf}.tmp"
  if [[ -n "$route" ]]; then
    jq --arg route "$route" '
      .route = $route |
      .budget.budget_status = "unlimited" |
      .budget.review_total = "unlimited"
    ' "$sf" > "$tmp"
  else
    jq '
      .budget.budget_status = "unlimited" |
      .budget.review_total = "unlimited"
    ' "$sf" > "$tmp"
  fi
  mv "$tmp" "$sf"
}

cmd_budget_check() {
  local allow_over_budget="false" override_reason=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --allow-over-budget) allow_over_budget="true"; shift ;;
      --override-reason) override_reason="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ "$allow_over_budget" == "true" && -z "$override_reason" ]]; then
    echo "Error: --override-reason required with --allow-over-budget" >&2
    exit 2
  fi

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

  local review_total review_used review_credit effective_used
  review_total=$(jq -r '.budget.review_total' "$sf")
  review_used=$(jq -r '.budget.review_used' "$sf")
  review_credit=$(jq -r '.budget.review_credit // 0' "$sf")
  effective_used=$(( review_used - review_credit ))

  if [[ "$effective_used" -ge "$review_total" ]] 2>/dev/null; then
    if [[ "$allow_over_budget" == "true" ]]; then
      # R1 override cap: prevent Coordinator from self-releasing indefinitely
      local override_count
      override_count=$(jq -r '.budget.override_count // 0' "$sf")
      if [[ "$override_count" -ge "$MAX_OVERRIDES" ]]; then
        echo "BLOCKED: over-budget override 上限已达 (${override_count}/${MAX_OVERRIDES})，必须报告用户，不可继续自我放行" >&2
        exit 2
      fi
      # Increment override_count (requires lock)
      acquire_lock
      trap release_lock EXIT
      local tmp="${sf}.tmp"
      jq '.budget.override_count = ((.budget.override_count // 0) + 1)' "$sf" > "$tmp"
      mv "$tmp" "$sf"
      release_lock
      trap - EXIT
      echo "OK: over-budget override ${effective_used}/${review_total} (credit=${review_credit})"
      exit 0
    fi
    echo "EXHAUSTED: review budget ${effective_used}/${review_total} (raw_used=${review_used}, credit=${review_credit})" >&2
    exit 2
  fi

  echo "OK: ${effective_used}/${review_total} (raw_used=${review_used}, credit=${review_credit})"
  exit 0
}

cmd_budget_increment_review() {
  local allow_over_budget="false" override_reason=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --allow-over-budget) allow_over_budget="true"; shift ;;
      --override-reason) override_reason="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ "$allow_over_budget" == "true" && -z "$override_reason" ]]; then
    echo "Error: --override-reason required with --allow-over-budget" >&2
    exit 2
  fi

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

  local used total credit effective
  used=$(jq -r '.budget.review_used' "$sf")
  total=$(jq -r '.budget.review_total' "$sf")
  credit=$(jq -r '.budget.review_credit // 0' "$sf")
  effective=$(( used - credit ))

  # Cap-guard: refuse to count past effective exhaustion (uses effective_used)
  if [[ "$total" != "unlimited" && "$effective" -ge "$total" ]] 2>/dev/null; then
    if [[ "$allow_over_budget" != "true" ]]; then
      echo "Error: review budget exhausted (effective=${effective}/${total}, raw=${used}, credit=${credit}); refusing to count another review." >&2
      exit 2
    fi
    echo "Warning: review budget exhausted (effective=${effective}/${total}); applying explicit over-budget override." >&2
  fi

  local tmp="${sf}.tmp"
  jq '.budget.review_used += 1' "$sf" > "$tmp"
  mv "$tmp" "$sf"

  local needs_dc=false dc_threshold=80 msg
  used=$(jq -r '.budget.review_used' "$sf")
  total=$(jq -r '.budget.review_total' "$sf")
  credit=$(jq -r '.budget.review_credit // 0' "$sf")
  effective=$(( used - credit ))
  local attendance
  attendance=$(jq -r '.attendance_mode // "afk"' "$sf")

  if [[ "$total" == "unlimited" ]]; then
    msg="Review budget: ${used} dispatches used (unlimited)."
  elif [[ "$effective" -ge "$total" ]] 2>/dev/null; then
    # 100%: both modes → needs_dc (escape hatch) + MSG
    local current_dc
    current_dc=$(jq -r '.pending_direction_check // "null"' "$sf")
    if [[ "$current_dc" == "null" ]]; then
      needs_dc=true
      dc_threshold=100
    fi
    msg="⚠ BUDGET EXHAUSTED: ${effective}/${total} (raw=${used}, credit=${credit}). Escape hatch: 报告用户，需显式 --allow-over-budget 或 stop。"
  elif [[ "$effective" -ge "$(( total * 80 / 100 ))" ]] 2>/dev/null; then
    # 80-100%: mode-dependent
    if [[ "$attendance" == "attended" ]]; then
      local current_dc
      current_dc=$(jq -r '.pending_direction_check // "null"' "$sf")
      if [[ "$current_dc" == "null" ]]; then
        needs_dc=true
        dc_threshold=80
      fi
      msg="DIRECTION CHECK: Review budget at ${effective}/${total} (≥80%, attended). Confirm with user."
    else
      # AFK: soft signal only, no DC
      msg="⚠ Review budget ${effective}/${total} (≥80%)，AFK 继续中，到顶将停。"
    fi
  else
    msg="Review budget: ${effective}/${total} dispatches used (raw=${used}, credit=${credit})."
  fi

  release_lock
  trap - EXIT

  if [[ "$needs_dc" == "true" ]]; then
    cmd_dc_trigger --type review --threshold-percent "$dc_threshold" >/dev/null
  fi

  echo "$msg"
}

# cmd_budget_credit — reflux/重写归还额度
# 归还量 = --reviews m (若给) 否则 plans * REVIEW_PER_PLAN
# 执行 .budget.review_credit += 归还量，保留 review_used 作历史累计真相
cmd_budget_credit() {
  local reason="" plans="" reviews=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --reason) reason="$2"; shift 2 ;;
      --plans)  plans="$2"; shift 2 ;;
      --reviews) reviews="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$reason" ]]; then
    echo "Error: --reason required for budget credit (e.g. --reason reflux)" >&2
    exit 2
  fi
  if [[ -z "$plans" && -z "$reviews" ]]; then
    echo "Error: --plans <n> or --reviews <m> required for budget credit" >&2
    exit 2
  fi

  local credit_amount
  if [[ -n "$reviews" ]]; then
    credit_amount="$reviews"
  else
    credit_amount=$(( plans * REVIEW_PER_PLAN ))
  fi

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"
  jq --argjson ca "$credit_amount" \
    '.budget.review_credit = ((.budget.review_credit // 0) + $ca)' \
    "$sf" > "$tmp"
  mv "$tmp" "$sf"

  local new_credit used total
  new_credit=$(jq -r '.budget.review_credit' "$sf")
  used=$(jq -r '.budget.review_used' "$sf")
  total=$(jq -r '.budget.review_total' "$sf")
  echo "Budget credit applied: +${credit_amount} (reason=${reason}). review_credit=${new_credit}, effective_used=$((used - new_credit))/${total}"
}

# cmd_set_attendance — write attendance_mode to top-level state field
cmd_set_attendance() {
  local mode=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode) mode="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  case "$mode" in
    attended|afk) ;;
    "") echo "Error: --mode required (attended|afk)" >&2; exit 2 ;;
    *) echo "Error: invalid --mode '$mode' (use attended|afk)" >&2; exit 2 ;;
  esac

  ensure_state_exists
  acquire_lock
  trap release_lock EXIT

  local sf
  sf="$(state_file)"
  local tmp="${sf}.tmp"
  jq --arg m "$mode" '.attendance_mode = $m' "$sf" > "$tmp"
  mv "$tmp" "$sf"

  echo "attendance_mode set to: $mode"
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

# --- review-history subcommand (Pack 2.8) ---
# Appends a row to a design/plan document's "## Review History" / "## Plan Review History"
# markdown table. Idempotent: skip if a row with the same (round, verdict, reviewer, date)
# already exists. Locking via the workflow-state lock — even though we don't write the
# state file, we serialize concurrent writers against the same target document.
cmd_review_history() {
  local subcmd="$1"; shift
  # Forward --help on the subcommand line to the help text below.
  for a in "$@"; do
    case "$a" in --help|-h) subcmd="help"; break ;; esac
  done
  case "$subcmd" in
    append) cmd_review_history_append "$@" ;;
    --help|-h|help)
      cat <<'RHHELP'
Usage: state.sh review-history append --run-id <id> --doc design|plan --slug <slug> \
         [--plan-id <N>] --round <R> --verdict <V> [--reviewer <name>] \
         [--gotchas <text>] [--date <YYYY-MM-DD>]

Appends a row to the Review History table in:
  - design: docs/orchestrate/design/<slug>.md  (## Review History)
  - plan:   docs/orchestrate/plans/<slug>/<plan-id>-*.md  (## Plan Review History)

Idempotent: re-running with the same (round, verdict, reviewer, date) is a no-op.
RHHELP
      exit 0
      ;;
    *) echo "Error: unknown review-history subcommand: $subcmd (use append)" >&2; exit 2 ;;
  esac
}

cmd_review_history_append() {
  local doc_kind="" slug="" plan_id="" round="" verdict="" reviewer="" gotchas="" date_str=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --doc) doc_kind="$2"; shift 2 ;;
      --slug) slug="$2"; shift 2 ;;
      --plan-id) plan_id="$2"; shift 2 ;;
      --round) round="$2"; shift 2 ;;
      --verdict) verdict="$2"; shift 2 ;;
      --reviewer) reviewer="$2"; shift 2 ;;
      --gotchas) gotchas="$2"; shift 2 ;;
      --date) date_str="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$doc_kind" || -z "$slug" || -z "$round" || -z "$verdict" ]]; then
    echo "Error: --doc, --slug, --round, --verdict required for review-history append" >&2
    exit 2
  fi
  case "$doc_kind" in
    design|plan) ;;
    *) echo "Error: --doc must be 'design' or 'plan' (got '$doc_kind')" >&2; exit 2 ;;
  esac
  if [[ "$doc_kind" == "plan" && -z "$plan_id" ]]; then
    echo "Error: --plan-id required when --doc plan" >&2
    exit 2
  fi

  local target=""
  local heading=""
  if [[ "$doc_kind" == "design" ]]; then
    target="docs/orchestrate/design/${slug}.md"
    heading="## Review History"
  else
    # Plan files live under docs/orchestrate/plans/<slug>/<plan_id>-*.md
    local plan_dir="docs/orchestrate/plans/${slug}"
    # Find file starting with plan_id-
    target=$(ls "${plan_dir}/${plan_id}"-*.md 2>/dev/null | head -1)
    heading="## Plan Review History"
  fi

  if [[ -z "$target" || ! -f "$target" ]]; then
    echo "Error: target document not found for doc=$doc_kind slug=$slug plan_id=$plan_id" >&2
    exit 2
  fi
  if ! grep -qF "$heading" "$target"; then
    echo "Error: heading '$heading' not found in $target — schema must include this section" >&2
    exit 2
  fi

  : "${reviewer:=-}"
  : "${gotchas:=-}"
  : "${date_str:=$(date -u +%Y-%m-%d)}"

  acquire_lock
  trap release_lock EXIT

  # Idempotency: check exact (round, verdict, reviewer, date) tuple already present.
  local probe="| ${round} | ${verdict} | ${reviewer} |"
  if grep -F "$probe" "$target" | grep -qF "| ${date_str} |"; then
    echo "OK (already present)"
    return 0
  fi

  local new_row="| ${round} | ${verdict} | ${reviewer} | ${gotchas} | - | ${date_str} |"

  # Append the new row right after the last table line ('| ... |') beneath the
  # target heading, before the next blank line or before the next heading.
  # Use awk for the state-machine — sed/regex line-substitution is too fragile
  # when the template carries a placeholder row.
  local tmp="${target}.rh.tmp"
  awk -v heading="$heading" -v new_row="$new_row" '
    BEGIN { in_section=0; inserted=0; last_table_line=-1; }
    {
      lines[NR]=$0
    }
    END {
      # First pass: find heading line, then walk forward to last table row.
      heading_line=0
      for (i=1; i<=NR; i++) {
        if (lines[i] == heading) { heading_line=i; break }
      }
      if (heading_line == 0) {
        # Fallback: heading not exactly matched (shouldn'\''t happen — grep -qF above).
        for (i=1; i<=NR; i++) print lines[i]
        print new_row
        exit
      }
      last_table=heading_line
      for (i=heading_line+1; i<=NR; i++) {
        line=lines[i]
        if (substr(line,1,2) == "##") break        # next heading
        if (line ~ /^\|.*\|/) { last_table=i; continue }
      }
      for (i=1; i<=NR; i++) {
        print lines[i]
        if (i == last_table) print new_row
      }
    }
  ' "$target" > "$tmp"
  mv "$tmp" "$target"
  echo "OK"
}


# --- merge-brief subcommand (Pack 6.8) ---
# Lifecycle helper for merge-brief-v1 9-section artifact.
# Path: ${STATE_BASE}/merge-brief-<run_id>.md (ephemeral, not docs/).
# Content sections are Coordinator-authored markdown; these helpers only manage
# the structured MERGE_BRIEF_META comment block. Decision 8: per-run conflict_id,
# new PR = new run, no archive by default.
#
# Does NOT expose: conflict add / rca write / resolution append
# (those are markdown content — Coordinator edits directly, avoiding template-fill anti-pattern).
cmd_merge_brief() {
  local subcmd="$1"; shift
  for a in "$@"; do
    case "$a" in --help|-h) subcmd="help"; break ;; esac
  done
  case "$subcmd" in
    init)   cmd_merge_brief_init "$@" ;;
    stage)  cmd_merge_brief_stage "$@" ;;
    verify) cmd_merge_brief_verify "$@" ;;
    --help|-h|help)
      cat <<'MBHELP'
Usage:
  state.sh merge-brief init   --run-id <id> --slug <slug>
  state.sh merge-brief stage  --run-id <id> --stage <stage>
  state.sh merge-brief verify --run-id <id>

Path: <STATE_BASE>/merge-brief-<run_id>.md
Stages: init | conflict_discovery | rca | repair | integration_review | merging | complete

Manages only the MERGE_BRIEF_META structured block. Content sections are
written by Coordinator via Edit. No conflict/rca/resolution subcommands
(avoids template-fill anti-pattern).
MBHELP
      exit 0
      ;;
    *) echo "Error: unknown merge-brief subcommand: $subcmd (use init|stage|verify)" >&2; exit 2 ;;
  esac
}

# Valid stages for merge-brief current_stage (matches merge-brief-v1.json schema enum)
MERGE_BRIEF_STAGES=(init conflict_discovery rca repair integration_review merging complete)

merge_brief_default_path() {
  echo "${STATE_BASE}/merge-brief-${RUN_ID}.md"
}

merge_brief_is_valid_stage() {
  local s="$1"
  for vs in "${MERGE_BRIEF_STAGES[@]}"; do
    [[ "$s" == "$vs" ]] && return 0
  done
  return 1
}

cmd_merge_brief_init() {
  local slug=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --slug) slug="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$slug" ]]; then
    echo "Error: --slug is required for merge-brief init" >&2
    exit 2
  fi

  local target
  target="$(merge_brief_default_path)"

  acquire_lock
  trap release_lock EXIT

  # Idempotent: if file exists, do not overwrite
  if [[ -f "$target" ]]; then
    echo "OK (already initialized: $target)"
    return 0
  fi

  mkdir -p "$(dirname "$target")"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  cat > "$target" <<MBEOF
<!-- MERGE_BRIEF_META
{
  "schema_version": "1",
  "run_id": "${RUN_ID}",
  "slug": "${slug}",
  "created_at": "${now}",
  "last_updated_at": "${now}",
  "current_stage": "init",
  "integration_review_gate": null
}
-->

# Merge Brief: ${RUN_ID}

> Read merge-brief-template.md for section writing guidance.
> Coordinator: fill sections below by editing this file directly (state.sh merge-brief does not fill content).

## 1. Meta

- **run_id**: \`${RUN_ID}\`
- **slug**: \`${slug}\`
- **route**: \`multi-pr-merge\`
- **created_at**: \`${now}\`
- **current_stage**: \`init\`
- **关联 workflow-state 路径**: \`.claude/multi-model-workflow/workflow-state-${RUN_ID}.json\`

## 2. 参与 PR（Big Picture）

<Coordinator fills: PR table with branch, design path, plan path, final-review verdict, core_behavior>

## 3. 合并后正确状态模型（Step 2 强制产出）

<Coordinator fills: behaviors, contract_surfaces, file_cross_matrix, merge_order, risk_hotspots>

## 4. Conflict Findings（Steps 5-7 持续追加）

<Coordinator appends after Explorer returns: per-conflict block with conflict_id C-001, C-002...>

## 5. Root Cause Analysis（Step 10 追加；仅 systemic conflict）

<Coordinator appends after Analyst returns: per-conflict RCA block>

## 6. Resolution Log（Steps 13-15 追加）

<Coordinator appends after verifying worker fix: per-conflict resolution record>

## 7. Integration Review Pointers（Step 16 前补写）

<Coordinator fills before dispatching Codex integration review>

## 8. Open Items / Out-of-scope

<Coordinator appends: non-blocking items, out-of-scope conflicts, user decisions needed>

## 9. Verdict（Step 22 写入）

<Coordinator fills after all conflicts resolved and integration review passes>
MBEOF
  echo "Created: $target"
}

cmd_merge_brief_stage() {
  local stage=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --stage) stage="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$stage" ]]; then
    echo "Error: --stage required for merge-brief stage" >&2
    exit 2
  fi

  if ! merge_brief_is_valid_stage "$stage"; then
    echo "Error: invalid stage '$stage'. Valid: ${MERGE_BRIEF_STAGES[*]}" >&2
    exit 2
  fi

  local target
  target="$(merge_brief_default_path)"
  if [[ ! -f "$target" ]]; then
    echo "Error: merge brief not found: $target (run 'merge-brief init' first)" >&2
    exit 2
  fi

  acquire_lock
  trap release_lock EXIT

  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Update current_stage and last_updated_at inside MERGE_BRIEF_META JSON comment
  local tmp="${target}.stg.tmp"
  python3 - "$target" "$stage" "$now" "$tmp" <<'PYEOF'
import sys, re

filepath, new_stage, now, outpath = sys.argv[1:]

with open(filepath, 'r') as f:
    content = f.read()

# Update current_stage in META block
content = re.sub(
    r'("current_stage"\s*:\s*)"[^"]*"',
    r'\g<1>"' + new_stage + '"',
    content, count=1
)
# Update last_updated_at in META block
content = re.sub(
    r'("last_updated_at"\s*:\s*)"[^"]*"',
    r'\g<1>"' + now + '"',
    content, count=1
)
# Also update the Stage line in §1 Meta section if present
content = re.sub(
    r'(\*\*current_stage\*\*:\s*)`[^`]*`',
    r'\g<1>`' + new_stage + '`',
    content, count=1
)

with open(outpath, 'w') as f:
    f.write(content)
PYEOF
  mv "$tmp" "$target"
  echo "OK (stage=$stage)"
}

cmd_merge_brief_verify() {
  while [[ $# -gt 0 ]]; do
    shift
  done

  local target
  target="$(merge_brief_default_path)"
  if [[ ! -f "$target" ]]; then
    echo "Error: merge brief not found: $target" >&2
    echo "Fix: run 'state.sh merge-brief init --run-id $RUN_ID --slug <slug>'" >&2
    exit 2
  fi

  local errors=()

  # 1. META block must be parseable and contain required fields
  local meta_block
  meta_block=$(python3 - "$target" <<'PYEOF' 2>/dev/null
import sys, re, json

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

m = re.search(r'<!--\s*MERGE_BRIEF_META\s*(.*?)\s*-->', content, re.DOTALL)
if not m:
    print('ERROR: MERGE_BRIEF_META comment block not found')
    sys.exit(1)

try:
    meta = json.loads(m.group(1))
except json.JSONDecodeError as e:
    print(f'ERROR: MERGE_BRIEF_META is not valid JSON: {e}')
    sys.exit(1)

required_fields = ['schema_version', 'run_id', 'slug', 'created_at', 'last_updated_at', 'current_stage']
missing = [f for f in required_fields if f not in meta]
if missing:
    print(f'ERROR: META missing fields: {", ".join(missing)}')
    sys.exit(1)

valid_stages = ['init', 'conflict_discovery', 'rca', 'repair', 'integration_review', 'merging', 'complete']
if meta['current_stage'] not in valid_stages:
    print(f'ERROR: META current_stage "{meta["current_stage"]}" not in valid stages: {valid_stages}')
    sys.exit(1)

print(f'META OK (stage={meta["current_stage"]})')
PYEOF
)
  if [[ $? -ne 0 ]] || echo "$meta_block" | grep -q "^ERROR:"; then
    errors+=("META: $meta_block")
  fi

  # 2. All 9 sections must be present (by section heading number)
  local missing_sections=()
  for heading in "## 1. Meta" "## 2. 参与 PR" "## 3. 合并后正确状态模型" \
                 "## 4. Conflict Findings" "## 5. Root Cause Analysis" \
                 "## 6. Resolution Log" "## 7. Integration Review Pointers" \
                 "## 8. Open Items" "## 9. Verdict"; do
    if ! grep -qF "$heading" "$target"; then
      missing_sections+=("$heading")
    fi
  done
  if [[ ${#missing_sections[@]} -gt 0 ]]; then
    errors+=("Missing sections: ${missing_sections[*]}")
  fi

  # 3. §4 status self-consistency check:
  # - status=resolved must have a corresponding entry in §6 (Resolution Log)
  # - status=rca-in-progress must have a §5 entry with analyst_agent_id
  python3 - "$target" <<'PYEOF' >> /tmp/merge_brief_verify_$$.txt 2>&1
import sys, re

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

# Extract all conflict_ids and their statuses from §4
conflicts = {}
for m in re.finditer(r'conflict_id[^:]*:\s*[`"]?([^`"\s,]+)[`"]?', content):
    cid = m.group(1)
    # find adjacent status line (within 20 chars context)
    snippet = content[m.start():m.start()+500]
    sm = re.search(r'status[^:]*:\s*[`"]?([^`"\n,]+)[`"]?', snippet)
    if sm:
        conflicts[cid] = sm.group(1).strip('` ')

def extract_section(text, start_heading, end_heading=None):
    """Extract content between start_heading and end_heading (exclusive)."""
    start_idx = text.find(start_heading)
    if start_idx == -1:
        return ''
    if end_heading:
        end_idx = text.find(end_heading, start_idx + len(start_heading))
        return text[start_idx:end_idx] if end_idx != -1 else text[start_idx:]
    return text[start_idx:]

# Extract §4, §5, §6 as bounded sections (not open-ended)
section4 = extract_section(content, '## 4. Conflict', '## 5. Root Cause')
section5 = extract_section(content, '## 5. Root Cause', '## 6. Resolution')
section6 = extract_section(content, '## 6. Resolution', '## 7. Integration')

# Only check conflict_ids found in §4 (not the whole document)
conflicts4 = {}
for m in re.finditer(r'conflict_id[^:]*:\s*[`"]?([^`"\s,]+)[`"]?', section4):
    cid = m.group(1)
    snippet = section4[m.start():m.start()+500]
    sm = re.search(r'\bstatus[^:]*:\s*[`"]?([^`"\n,]+)[`"]?', snippet)
    if sm:
        conflicts4[cid] = sm.group(1).strip('` ')

errors = []
for cid, status in conflicts4.items():
    if status == 'resolved':
        # §6 (bounded) must mention this conflict_id
        if cid not in section6:
            errors.append(f'{cid} status=resolved but no §6 entry found (fix: add Resolution Log for {cid})')
    elif status == 'rca-in-progress':
        # §5 (bounded) must mention this conflict_id
        if cid not in section5:
            errors.append(f'{cid} status=rca-in-progress but no §5 RCA entry found (fix: add RCA block or mark as pending)')

if errors:
    for e in errors:
        print(f'ERROR: {e}')
    sys.exit(1)
else:
    print('STATUS OK')
PYEOF
  local status_check
  status_check=$(cat /tmp/merge_brief_verify_$$.txt 2>/dev/null)
  rm -f /tmp/merge_brief_verify_$$.txt
  if echo "$status_check" | grep -q "^ERROR:"; then
    errors+=("§4 status self-consistency: $(echo "$status_check" | grep "^ERROR:" | tr '\n' '; ')")
  fi

  if [[ ${#errors[@]} -gt 0 ]]; then
    echo "BLOCKED: merge brief verification failed" >&2
    for e in "${errors[@]}"; do echo "  - $e" >&2; done
    echo "Fix: edit $target and address the issues above" >&2
    exit 2
  fi
  echo "Valid: $target ($meta_block)"
}

# --- A1: verdict-route — workflow-level verdict 机械路由查询 ---
# 查 routes-v1.json .verdict_routing[phase][verdict]，输出机械动作 JSON。
# 判断类分支（judgment=true）只给候选动作，最终选择留给 Coordinator 散文判断。
# 特例 reflux-counter（final-review NEEDS_EXECUTION）：读写 workflow-state
# execution_reflux_count——0 → 递增并 goto execution；≥1 → blocked。
# Fail-open：verdict_routing 缺数据 → exit 0 输出 no-data 提示（never stricter）。
cmd_verdict_route() {
  local phase="" verdict=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --phase) phase="$2"; shift 2 ;;
      --verdict) verdict="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$phase" || -z "$verdict" ]]; then
    echo "Error: --phase and --verdict required for verdict-route" >&2
    exit 2
  fi

  if ! routes_load; then
    echo "[multi-model-workflow] VERDICT-ROUTE no-data (routes manifest unreadable) — follow SKILL.md prose."
    exit 0
  fi

  local record
  record=$(jq -c --arg p "$phase" --arg v "$verdict" \
    '.verdict_routing[$p][$v] // empty' "$ROUTES_MANIFEST" 2>/dev/null)
  if [[ -z "$record" ]]; then
    echo "[multi-model-workflow] VERDICT-ROUTE no-data for phase=$phase verdict=$verdict — follow SKILL.md prose."
    exit 0
  fi

  local action
  action=$(echo "$record" | jq -r '.action')

  if [[ "$action" == "reflux-counter" ]]; then
    ensure_state_exists
    local sf count
    sf="$(state_file)"
    count=$(jq -r '.execution_reflux_count // 0' "$sf")
    if [[ "$count" -eq 0 ]]; then
      acquire_lock
      trap release_lock EXIT
      local tmp="${sf}.tmp"
      jq '.execution_reflux_count = 1' "$sf" > "$tmp"
      mv "$tmp" "$sf"
      echo "$record" | jq -c '. + {action: "goto", reflux_count: 1, resolved: "reflux 0→1，回 execution"}'
    else
      echo "$record" | jq -c '. + {action: "report-user", target: null, reflux_count: '"$count"', resolved: "reflux 已达上限，BLOCKED 报告用户"}'
    fi
    return 0
  fi

  echo "$record"
}

# --- A2: checkbox toggle — Plan Implementation Review 通过后勾选 committed Pack ---
# Source-of-truth = plan-return.per_pack[*].status == committed（D4 裁决）。
# 按 Pack ID 精确匹配 `- [ ] **Pack N.M**` 行 toggle 为 `- [x]`；非 committed 不动。
cmd_checkbox() {
  local subcmd="$1"; shift
  case "$subcmd" in
    toggle) cmd_checkbox_toggle "$@" ;;
    *) echo "Error: unknown checkbox subcommand: $subcmd (use toggle)" >&2; exit 2 ;;
  esac
}

cmd_checkbox_toggle() {
  local plan_id="" plan_file=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --plan-id) plan_id="$2"; shift 2 ;;
      --plan-file) plan_file="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$plan_id" || -z "$plan_file" ]]; then
    echo "Error: --plan-id and --plan-file required for checkbox toggle" >&2
    exit 2
  fi
  if [[ ! -f "$plan_file" ]]; then
    echo "Error: plan file not found: $plan_file" >&2
    exit 2
  fi

  local pr_file="${STATE_BASE}/plan-returns/${RUN_ID}/${plan_id}/plan-return.json"
  if [[ ! -f "$pr_file" ]]; then
    echo "Error: plan-return.json not found at: $pr_file" >&2
    exit 2
  fi

  local committed_packs
  committed_packs=$(jq -r '.per_pack | to_entries[] | select(.value.status == "committed") | .key' "$pr_file")
  if [[ -z "$committed_packs" ]]; then
    echo "[multi-model-workflow] checkbox toggle: no committed packs in plan-return — nothing to toggle."
    return 0
  fi

  local toggled=0 already=0 missing=0 pack escaped
  while IFS= read -r pack; do
    [[ -z "$pack" ]] && continue
    escaped=$(printf '%s' "$pack" | sed 's/\./\\./g')
    if grep -qE "^[[:space:]]*- \[x\] \*\*Pack ${escaped}\*\*" "$plan_file"; then
      already=$((already + 1))
      continue
    fi
    if grep -qE "^[[:space:]]*- \[ \] \*\*Pack ${escaped}\*\*" "$plan_file"; then
      # macOS/BSD sed -i 需要后缀参数；用 portable tmp 写法
      local tmp="${plan_file}.tmp.$$"
      sed -E "s/^([[:space:]]*)- \[ \] (\*\*Pack ${escaped}\*\*)/\1- [x] \2/" "$plan_file" > "$tmp"
      mv "$tmp" "$plan_file"
      toggled=$((toggled + 1))
    else
      missing=$((missing + 1))
      echo "Warning: checkbox line for Pack ${pack} not found in $plan_file" >&2
    fi
  done <<< "$committed_packs"

  echo "[multi-model-workflow] checkbox toggle: ${toggled} toggled, ${already} already checked, ${missing} missing."
  [[ "$missing" -eq 0 ]] || exit 2
}

# --- A3: envelope build — DISPATCH_ENVELOPE 生成器（与 parse-envelope.sh 校验对称）---
# idempotency_key 统一为 <run_id>/<plan_id|pack_id>/r<repair_round>（plan-level 用
# plan_id，pack-level 用 pack_id，消除旧模板只写 pack_id 的歧义）。
# 生成后立即过一遍 hooks/lib/parse-envelope.sh 自检，保证生成与校验不漂移。
cmd_envelope() {
  local subcmd="$1"; shift
  case "$subcmd" in
    build) cmd_envelope_build "$@" ;;
    *) echo "Error: unknown envelope subcommand: $subcmd (use build)" >&2; exit 2 ;;
  esac
}

cmd_envelope_build() {
  local phase="" agent_role="" plan_id="" pack_id="" repair_round="0"
  local agent_id="" worktree_path="" review_intent="" exception_code=""
  local disposition_refs="" resume_from_pack_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --phase) phase="$2"; shift 2 ;;
      --agent-role) agent_role="$2"; shift 2 ;;
      --plan-id) plan_id="$2"; shift 2 ;;
      --pack-id) pack_id="$2"; shift 2 ;;
      --repair-round) repair_round="$2"; shift 2 ;;
      --agent-id) agent_id="$2"; shift 2 ;;
      --worktree-path) worktree_path="$2"; shift 2 ;;
      --review-intent) review_intent="$2"; shift 2 ;;
      --exception-code) exception_code="$2"; shift 2 ;;
      --disposition-refs) disposition_refs="$2"; shift 2 ;;
      --resume-from-pack-id) resume_from_pack_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$phase" || -z "$agent_role" ]]; then
    echo "Error: --phase and --agent-role required for envelope build" >&2
    exit 2
  fi
  if [[ -n "$plan_id" && -n "$pack_id" ]]; then
    echo "Error: exactly one of --plan-id / --pack-id may be set (got both)" >&2
    exit 2
  fi

  # idempotency 基（plan-level 优先 plan_id；pack-level 用 pack_id；route-worker 无两者用 phase）
  local key_base="${plan_id:-${pack_id:-$phase}}"
  local idempotency_key="${RUN_ID}/${key_base}/r${repair_round}"
  local correlation_id="${RUN_ID}/${key_base}"

  if [[ "$repair_round" -ge 1 ]] && [[ -z "$disposition_refs" || "$disposition_refs" == "null" || "$disposition_refs" == "[]" ]]; then
    echo "Error: repair dispatch (round=$repair_round) requires non-empty --disposition-refs" >&2
    exit 2
  fi
  if [[ "$agent_role" == "codex-reviewer" && "$review_intent" != "baseline" ]]; then
    echo "Error: codex-reviewer dispatch requires --review-intent baseline" >&2
    exit 2
  fi

  local envelope
  envelope=$(jq -cn \
    --arg run_id "$RUN_ID" \
    --arg phase "$phase" \
    --arg agent_role "$agent_role" \
    --arg agent_id "$agent_id" \
    --arg pack_id "$pack_id" \
    --arg plan_id "$plan_id" \
    --argjson repair_round "$repair_round" \
    --arg idempotency_key "$idempotency_key" \
    --arg correlation_id "$correlation_id" \
    --arg review_intent "$review_intent" \
    --arg exception_code "$exception_code" \
    --arg worktree_path "$worktree_path" \
    --arg resume_from "$resume_from_pack_id" \
    --arg drefs "$disposition_refs" \
    '{
      protocol_version: "1",
      run_id: $run_id,
      phase: $phase,
      agent_role: $agent_role,
      agent_id: (if $agent_id == "" then null else $agent_id end),
      pack_id: (if $pack_id == "" then null else $pack_id end),
      plan_id: (if $plan_id == "" then null else $plan_id end),
      repair_round: $repair_round,
      idempotency_key: $idempotency_key,
      disposition_refs: (if $drefs == "" then null else ($drefs | fromjson? // $drefs) end),
      review_intent: (if $review_intent == "" then null else $review_intent end),
      exception_code: (if $exception_code == "" then null else $exception_code end),
      correlation_id: $correlation_id,
      worktree_path: (if $worktree_path == "" then null else $worktree_path end)
    }
    + (if $resume_from == "" then {} else {resume_from_pack_id: $resume_from} end)')

  local block="<!-- DISPATCH_ENVELOPE ${envelope} -->"

  # 自检：生成物必须通过 parse-envelope.sh（生成与校验对称，杜绝漂移）
  local parser="$SCRIPT_DIR/../hooks/lib/parse-envelope.sh"
  if [[ -f "$parser" ]]; then
    if ! echo "$block" | bash "$parser" >/dev/null 2>&1; then
      echo "Error: generated envelope failed parse-envelope.sh self-check" >&2
      echo "$block" >&2
      exit 2
    fi
  fi

  echo "$block"
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

# Help mode (--help / -h) does not require --run-id.
HELP_REQUESTED="false"
for arg in "$@"; do
  case "$arg" in
    --help|-h|help) HELP_REQUESTED="true"; break ;;
  esac
done

if [[ -z "$RUN_ID" && "$CMD" != "help" && "$HELP_REQUESTED" != "true" ]]; then
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
  agent-id) cmd_agent_id "$@" ;;
  pack-progress) cmd_pack_progress "$@" ;;
  plan-returns) cmd_plan_returns "$@" ;;
  execution-plan) cmd_execution_plan "$@" ;;
  budget) cmd_budget "$@" ;;
  set-attendance) cmd_set_attendance "$@" ;;
  direction-check) cmd_direction_check "$@" ;;
  idempotency) cmd_idempotency "$@" ;;
  review-history) cmd_review_history "$@" ;;
  merge-brief) cmd_merge_brief "$@" ;;
  verdict-route) cmd_verdict_route "$@" ;;
  checkbox) cmd_checkbox "$@" ;;
  envelope) cmd_envelope "$@" ;;
  *) echo "Error: unknown command: $CMD" >&2; usage ;;
esac
