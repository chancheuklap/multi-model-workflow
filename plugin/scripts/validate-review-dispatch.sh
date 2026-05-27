#!/usr/bin/env bash
# Explicit Coordinator gate for Codex reviewer dispatch on Claude side.
#
# Claude reviews go through `node codex-companion.mjs task --background[--resume]`,
# so the transport is always Bash. This script validates the DISPATCH_ENVELOPE
# shape and budget readiness *before* the Coordinator runs codex-companion.
#
# Baseline vs targeted re-review is derived from `review_intent` in the
# envelope (no separate transport flag — the envelope is the source of truth).
set -euo pipefail

PROMPT_FILE=""
GATE=""
ALLOW_OVER_BUDGET="false"
OVERRIDE_REASON=""

usage() {
  cat <<'USAGE'
Usage: validate-review-dispatch.sh --prompt-file PATH [--gate GATE] [--allow-over-budget --override-reason TEXT]

The envelope's `review_intent` ("baseline" or "targeted-re-review") drives
validation: baseline requires agent_id=null; targeted-re-review requires
agent_id (= baseline reviewer JOB_ID), exception_code, and repair_round >= 1.
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
    --gate) GATE="${2:-}"; shift 2 ;;
    --allow-over-budget) ALLOW_OVER_BUDGET="true"; shift ;;
    --override-reason) OVERRIDE_REASON="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" ]] || usage
if [[ "$ALLOW_OVER_BUDGET" == "true" && -z "$OVERRIDE_REASON" ]]; then
  echo "Error: --override-reason required with --allow-over-budget" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

AGENT_ROLE=$(echo "$ENVELOPE" | jq -r '.agent_role // empty')
REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')
RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
AGENT_ID=$(echo "$ENVELOPE" | jq -r '.agent_id // empty')
EXCEPTION_CODE=$(echo "$ENVELOPE" | jq -r '.exception_code // empty')
REPAIR_ROUND=$(echo "$ENVELOPE" | jq -r '.repair_round // 0')

BUDGET_DIR="${STATE_BASE:-.claude/multi-model-workflow}"

gate_from_prompt_file() {
  basename "$PROMPT_FILE" .md
}

canonical_plan_id() {
  printf "%03d" "$1"
}

baseline_gate_for_targeted() {
  local gate="$1"
  if [[ "$gate" =~ ^(.+)-repair-[0-9]+$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi
  echo ""
}

validate_plan_impl_gate() {
  local gate="$1"
  [[ "$gate" =~ ^plan-impl-review-([0-9]+)$ ]] || return 0

  local plan_id
  plan_id="$(canonical_plan_id "${BASH_REMATCH[1]}")"

  local esf="${BUDGET_DIR}/execution-state-${RUN_ID}.json"
  if [[ ! -f "$esf" ]]; then
    echo "Error: execution state not found for plan implementation review: $esf" >&2
    exit 2
  fi

  if [[ "$(jq -r --arg pid "$plan_id" '.plans[$pid] != null' "$esf")" != "true" ]]; then
    echo "Error: Plan $plan_id not found in execution-state" >&2
    exit 2
  fi

  local start_commit
  start_commit=$(jq -r --arg pid "$plan_id" '.plans[$pid].start_commit // empty' "$esf")
  if [[ -z "$start_commit" || "$start_commit" == "null" ]]; then
    echo "Error: Plan $plan_id missing start_commit" >&2
    exit 2
  fi

  local pack_count unfinished missing_commit
  pack_count=$(jq --arg pid "$plan_id" '.plans[$pid].packs // {} | length' "$esf")
  if [[ "$pack_count" -eq 0 ]]; then
    echo "Error: Plan $plan_id has no packs to review" >&2
    exit 2
  fi

  unfinished=$(jq --arg pid "$plan_id" '[.plans[$pid].packs // {} | to_entries[] | select(.value.status != "committed")] | length' "$esf")
  if [[ "$unfinished" -gt 0 ]]; then
    echo "Error: Plan $plan_id has $unfinished pack(s) not committed" >&2
    exit 2
  fi

  missing_commit=$(jq --arg pid "$plan_id" '[.plans[$pid].packs // {} | to_entries[] | select((.value.commit_sha // "") == "")] | length' "$esf")
  if [[ "$missing_commit" -gt 0 ]]; then
    echo "Error: Plan $plan_id has $missing_commit committed pack(s) without commit_sha" >&2
    exit 2
  fi
}

validate_targeted_continuity() {
  local gate="$1"
  local baseline_gate
  baseline_gate="$(baseline_gate_for_targeted "$gate")"

  local expected_agent=""
  if [[ -n "$baseline_gate" && -f "${BUDGET_DIR}/review-agents/${baseline_gate}.agent-id" ]]; then
    expected_agent=$(cat "${BUDGET_DIR}/review-agents/${baseline_gate}.agent-id")
  fi

  if [[ -z "$expected_agent" ]]; then
    expected_agent=$(find "${BUDGET_DIR}/review-registry" -name '*.json' -type f 2>/dev/null \
      -exec jq -r --arg run "$RUN_ID" --arg agent "$AGENT_ID" 'select(.run_id == $run and .agent_id == $agent and (.review_intent // "baseline") == "baseline") | .agent_id' {} \; \
      | head -1)
  fi

  if [[ -z "$expected_agent" || "$expected_agent" == "null" ]]; then
    echo "Error: targeted re-review could not find recorded baseline reviewer JOB_ID" >&2
    exit 2
  fi

  if [[ "$AGENT_ID" != "$expected_agent" ]]; then
    echo "Error: targeted re-review agent_id does not match recorded baseline reviewer JOB_ID" >&2
    exit 2
  fi

  if [[ -n "$baseline_gate" && ! -s "${BUDGET_DIR}/review-results/${baseline_gate}.md" ]]; then
    echo "Error: targeted re-review requires baseline review result for $baseline_gate" >&2
    exit 2
  fi

  if [[ "$REPAIR_ROUND" -lt 1 ]] 2>/dev/null; then
    echo "Error: targeted re-review requires repair_round >= 1" >&2
    exit 2
  fi

  local sf="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
  while IFS= read -r ref; do
    [[ -n "$ref" ]] || continue
    local accepted evidence
    accepted=$(jq -r --arg fid "$ref" '[.review_dispositions[] | select(.finding_id == $fid and .disposition == "accepted")] | length' "$sf" 2>/dev/null || echo "0")
    if [[ "$accepted" -eq 0 ]]; then
      echo "Error: targeted re-review disposition_ref $ref is not accepted" >&2
      exit 2
    fi
    evidence=$(jq -r --arg fid "$ref" '[.review_dispositions[] | select(.finding_id == $fid and .disposition == "accepted") | .evidence // ""] | first // ""' "$sf" 2>/dev/null)
    if [[ -z "$evidence" || "$evidence" == "null" ]]; then
      echo "Error: targeted re-review disposition_ref $ref has no evidence" >&2
      exit 2
    fi
  done < <(echo "$ENVELOPE" | jq -r '.disposition_refs // [] | .[]')
}

if [[ "$AGENT_ROLE" != "codex-reviewer" ]]; then
  echo "Error: review dispatch envelope agent_role must be codex-reviewer" >&2
  exit 2
fi

if [[ -z "$GATE" ]]; then
  GATE="$(gate_from_prompt_file)"
fi

case "$REVIEW_INTENT" in
  baseline)
    if [[ -n "$AGENT_ID" && "$AGENT_ID" != "null" ]]; then
      echo "Error: baseline review envelope must set agent_id to null (this is a fresh dispatch)" >&2
      exit 2
    fi
    validate_plan_impl_gate "$GATE"
    ;;
  targeted-re-review)
    if [[ -z "$AGENT_ID" || "$AGENT_ID" == "null" ]]; then
      echo "Error: targeted re-review must include baseline reviewer JOB_ID as agent_id" >&2
      exit 2
    fi
    if [[ -z "$EXCEPTION_CODE" || "$EXCEPTION_CODE" == "null" ]]; then
      echo "Error: targeted re-review must include exception_code" >&2
      exit 2
    fi
    validate_targeted_continuity "$GATE"
    ;;
  *)
    echo "Error: review_intent must be baseline or targeted-re-review (got: ${REVIEW_INTENT:-empty})" >&2
    exit 2
    ;;
esac

if [[ "$RUN_ID" != adhoc-* ]]; then
  BUDGET_ARGS=(--run-id "$RUN_ID")
  if [[ "$ALLOW_OVER_BUDGET" == "true" ]]; then
    BUDGET_ARGS+=(--allow-over-budget --override-reason "$OVERRIDE_REASON")
  fi
  bash "$SCRIPT_DIR/state.sh" budget check "${BUDGET_ARGS[@]}" >/dev/null
fi

echo "OK"
