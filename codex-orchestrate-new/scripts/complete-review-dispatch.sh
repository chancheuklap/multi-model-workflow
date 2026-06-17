#!/usr/bin/env bash
# Marks a reviewer result durable in the registry.
#
# Codex-native split-of-concerns:
#   - Reviews are native codex_reviewer subagents.
#   - This script writes the registry durability marker and increments review
#     budget exactly once when the Coordinator persists a result file.
#   - Hooks do not infer review completion from shell command text.
#   - --allow-over-budget / --override-reason are recorded as registry
#     metadata so that audit can see which reviews were explicit
#     user-authorized over-budget dispatches.
set -euo pipefail

RUN_ID=""
GATE=""
AGENT_ID=""
RESULT_FILE=""
ALLOW_OVER_BUDGET="false"
OVERRIDE_REASON=""

usage() {
  cat <<'USAGE'
Usage: complete-review-dispatch.sh --run-id RUN_ID --gate GATE --agent-id AGENT_ID --result-file PATH [--allow-over-budget --override-reason TEXT]

The agent-id is the reviewer identity returned by the phase-specific reviewer
`spawn_agent(...)` call (`codex_planning_reviewer` for Discovery / Plan Review,
`codex_reviewer` otherwise).
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --gate) GATE="${2:-}"; shift 2 ;;
    --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
    --result-file) RESULT_FILE="${2:-}"; shift 2 ;;
    --allow-over-budget) ALLOW_OVER_BUDGET="true"; shift ;;
    --override-reason) OVERRIDE_REASON="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$RUN_ID" && -n "$GATE" && -n "$AGENT_ID" && -n "$RESULT_FILE" ]] || usage
if [[ "$ALLOW_OVER_BUDGET" == "true" && -z "$OVERRIDE_REASON" ]]; then
  echo "Error: --override-reason required with --allow-over-budget" >&2
  exit 2
fi
[[ -s "$RESULT_FILE" ]] || {
  echo "Error: review result file missing or empty: $RESULT_FILE" >&2
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"
REGISTRY_FILE="$BUDGET_DIR/review-registry/${GATE}.json"

file_sha256() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "Error: shasum or sha256sum is required to verify review prompt integrity" >&2
    exit 2
  fi
}

if [[ ! -f "$REGISTRY_FILE" ]]; then
  BASELINE_REGISTRY=$(find "$BUDGET_DIR/review-registry" -name '*.json' -type f 2>/dev/null \
    -exec jq -r --arg run "$RUN_ID" --arg agent "$AGENT_ID" 'select(.run_id == $run and .agent_id == $agent and (.review_intent // "baseline") == "baseline") | input_filename' {} \; \
    | head -1)
  if [[ -z "$BASELINE_REGISTRY" ]]; then
    echo "Error: review registry not found for gate: $GATE" >&2
    exit 2
  fi

  mkdir -p "$BUDGET_DIR/review-registry"
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq -n \
    --arg run_id "$RUN_ID" \
    --arg gate "$GATE" \
    --arg agent_id "$AGENT_ID" \
    --arg created_at "$now" \
    '{
      run_id: $run_id,
      gate: $gate,
      phase: null,
      review_intent: "baseline",
      agent_id: $agent_id,
      prompt_file: null,
      prompt_sha256: null,
      result_file: null,
      status: "dispatched",
      created_at: $created_at,
      completed_at: null,
      budget_counted: false
    }' > "$REGISTRY_FILE"
fi

RECORDED_AGENT=$(jq -r '.agent_id // empty' "$REGISTRY_FILE")
if [[ "$RECORDED_AGENT" != "$AGENT_ID" ]]; then
  echo "Error: completed review agent_id does not match registry" >&2
  exit 2
fi

STATUS="$(jq -r '.status // empty' "$REGISTRY_FILE")"
BUDGET_COUNTED="$(jq -r '.budget_counted // false' "$REGISTRY_FILE")"
DURABLE_ALREADY="false"
case "$STATUS" in
  completed|disposition_started|disposition_done) DURABLE_ALREADY="true" ;;
esac

if [[ "$DURABLE_ALREADY" == "true" && ( "$RUN_ID" == adhoc-* || "$BUDGET_COUNTED" == "true" ) ]]; then
  echo "OK (already durable)"
  exit 0
fi

if [[ "$DURABLE_ALREADY" != "true" ]]; then
  PROMPT_FILE_RECORDED="$(jq -r '.prompt_file // empty' "$REGISTRY_FILE")"
  PROMPT_SHA_RECORDED="$(jq -r '.prompt_sha256 // empty' "$REGISTRY_FILE")"
  if [[ -n "$PROMPT_FILE_RECORDED" && "$PROMPT_FILE_RECORDED" != "null" && -n "$PROMPT_SHA_RECORDED" && "$PROMPT_SHA_RECORDED" != "null" ]]; then
    if [[ ! -f "$PROMPT_FILE_RECORDED" ]]; then
      echo "Error: recorded review prompt missing: $PROMPT_FILE_RECORDED" >&2
      exit 2
    fi
    CURRENT_PROMPT_SHA="$(file_sha256 "$PROMPT_FILE_RECORDED")"
    if [[ "$CURRENT_PROMPT_SHA" != "$PROMPT_SHA_RECORDED" ]]; then
      echo "Error: review prompt changed after dispatch for gate $GATE; dispatch a fresh review instead of completing a stale result." >&2
      exit 2
    fi
  fi
fi

now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
tmp="${REGISTRY_FILE}.tmp"
if [[ "$ALLOW_OVER_BUDGET" == "true" ]]; then
  OVER_BUDGET_JSON="true"
else
  OVER_BUDGET_JSON="false"
fi

if [[ "$DURABLE_ALREADY" != "true" ]]; then
  jq --arg result_file "$RESULT_FILE" --arg completed_at "$now" \
    --argjson over_budget "$OVER_BUDGET_JSON" --arg override_reason "$OVERRIDE_REASON" '
    .result_file = $result_file
    | .status = "completed"
    | .completed_at = $completed_at
    | .over_budget_allowed = $over_budget
    | .over_budget_reason = (if $over_budget then $override_reason else null end)
  ' "$REGISTRY_FILE" > "$tmp"
  mv "$tmp" "$REGISTRY_FILE"
fi

if [[ "$RUN_ID" != adhoc-* ]] && [[ "$(jq -r '.budget_counted // false' "$REGISTRY_FILE")" != "true" ]]; then
  WF_STATE="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
  BUDGET_STATUS="$(jq -r '.budget.budget_status // empty' "$WF_STATE" 2>/dev/null || echo "")"
  if [[ "$BUDGET_STATUS" == "pending_plan_count" ]]; then
    tmp="${REGISTRY_FILE}.tmp"
    jq '.budget_counted = false | .budget_count_skip_reason = "pending_plan_count"' "$REGISTRY_FILE" > "$tmp"
    mv "$tmp" "$REGISTRY_FILE"
  else
    BUDGET_ARGS=(--run-id "$RUN_ID" --gate "$GATE")
    if [[ "$ALLOW_OVER_BUDGET" == "true" ]]; then
      BUDGET_ARGS+=(--allow-over-budget --override-reason "$OVERRIDE_REASON")
    fi
    bash "$SCRIPT_DIR/state.sh" budget increment-review "${BUDGET_ARGS[@]}" >/dev/null
    tmp="${REGISTRY_FILE}.tmp"
    jq '.budget_counted = true | del(.budget_count_skip_reason)' "$REGISTRY_FILE" > "$tmp"
    mv "$tmp" "$REGISTRY_FILE"
  fi
fi

# Pack 2.9: auto-append Review History row when the gate matches a known design/plan
# review pattern. We do this best-effort — failures to append are logged to stderr
# but never fail the script, because durability marking is the primary purpose
# of this script and Plan 002 R3 backward-compat keeps the workflow forward-progressing
# even if the secondary append misses (the row can still be added manually).
#
# Slug source: prefer workflow-state.slug (read via jq); fallback to env STATE_SLUG.
# Plan id source: derived from the gate suffix when the kind is "plan".
#
# Gate name conventions (matched here):
#   design-review-content-N         -> doc=design, round=N
#   design-review-alignment-N       -> doc=design, round=N
#   plan-review-<plan_id>-<angle>-N -> doc=plan, plan_id=<plan_id>, round=N
# Targeted re-review gates contain "-repair-" — we still write a row but mark round
# as the repair round derived from the suffix.

append_review_history_row() {
  local kind="$1" round="$2" plan_id="${3:-}"
  local state_sh="${SCRIPT_DIR}/state.sh"
  if [[ ! -x "$state_sh" ]]; then return 0; fi

  # Resolve slug from workflow-state file; if missing, fallback to STATE_SLUG env var.
  local wf_state_file="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
  local slug=""
  if [[ -f "$wf_state_file" ]]; then
    slug=$(jq -r '.slug // empty' "$wf_state_file" 2>/dev/null)
  fi
  if [[ -z "$slug" ]]; then
    slug="${STATE_SLUG:-}"
  fi
  if [[ -z "$slug" ]]; then
    echo "Note: review-history append skipped — could not resolve slug for run $RUN_ID" >&2
    return 0
  fi

  # Verdict parse from result file: first non-empty line under "### Verdict".
  local verdict=""
  if [[ -s "$RESULT_FILE" ]]; then
    verdict=$(awk '
      /^### Verdict/ { capture=1; next }
      capture==1 && /^[[:space:]]*$/ { next }
      capture==1 { print; exit }
    ' "$RESULT_FILE" | head -c 200 | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//')
  fi
  : "${verdict:=unknown}"

  local args=(--run-id "$RUN_ID" --doc "$kind" --slug "$slug" --round "$round"
              --verdict "$verdict" --reviewer "${AGENT_ID:-codex_reviewer}")
  if [[ "$kind" == "plan" ]]; then
    if [[ -z "$plan_id" ]]; then
      echo "Note: plan review gate did not yield plan_id ($GATE); skipping append" >&2
      return 0
    fi
    args+=(--plan-id "$plan_id")
  fi

  if ! bash "$state_sh" review-history append "${args[@]}" >/dev/null 2>&1; then
    echo "Note: state.sh review-history append failed for gate $GATE (non-fatal)" >&2
  fi
}

# Derive round and (optional) plan_id from gate name.
# Round defaults to 1 when no trailing digit is found.
ROUND="1"
if [[ "$GATE" =~ -([0-9]+)$ ]]; then
  ROUND="${BASH_REMATCH[1]}"
elif [[ "$GATE" =~ -repair-([0-9]+)$ ]]; then
  ROUND="${BASH_REMATCH[1]}"
fi

if [[ "$DURABLE_ALREADY" != "true" ]]; then
  case "$GATE" in
    design-review-*)
      append_review_history_row design "$ROUND" ""
      ;;
    plan-review-*)
      # Gate convention: plan-review-<plan_id>-... where <plan_id> is the
      # zero-padded numeric segment (e.g. plan-review-001-coverage-1).
      PLAN_ID=""
      if [[ "$GATE" =~ ^plan-review-([0-9]+)- ]]; then
        PLAN_ID="${BASH_REMATCH[1]}"
      fi
      append_review_history_row plan "$ROUND" "$PLAN_ID"
      ;;
  esac
fi

echo "OK"
