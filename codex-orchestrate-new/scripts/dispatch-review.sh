#!/usr/bin/env bash
# Unified Codex review dispatch script.
# Subcommands: validate | record
# Usage:
#   dispatch-review.sh validate --prompt-file PATH [--gate GATE] [--allow-over-budget --override-reason TEXT]
#   dispatch-review.sh record  --prompt-file PATH --gate GATE --agent-id AGENT_ID
set -euo pipefail

SUBCMD="${1:-}"
shift 2>/dev/null || true

case "$SUBCMD" in
  validate)
    # --- validate subcommand ---
    PROMPT_FILE=""
    GATE=""
    ALLOW_OVER_BUDGET="false"
    OVERRIDE_REASON=""

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
        --gate) GATE="${2:-}"; shift 2 ;;
        --allow-over-budget) ALLOW_OVER_BUDGET="true"; shift ;;
        --override-reason) OVERRIDE_REASON="${2:-}"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
      esac
    done

    [[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" ]] || { echo "Usage: dispatch-review.sh validate --prompt-file PATH [--gate GATE]" >&2; exit 2; }
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

    BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"

    gate_from_prompt_file() { basename "$PROMPT_FILE" .md; }

    canonical_plan_id() { printf "%03d" "$1"; }

    validate_gate_name() {
      local gate="$1"
      if [[ "$gate" == *targeted* ]]; then
        echo "Error: targeted review gates are deprecated; use baseline review plus Coordinator self-verification/RCA per phase repair policy." >&2
        exit 2
      fi
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

    validate_repair_round_cap() {
      local gate="$1"
      local phase_key=""
      local round=""

      if [[ "$gate" =~ ^plan-impl-review-[0-9]+-repair-([0-9]+)$ ]]; then
        phase_key="execution"
        round="${BASH_REMATCH[1]}"
      elif [[ "$gate" =~ ^plan-review-repair-([0-9]+)$ ]]; then
        phase_key="plan-review"
        round="${BASH_REMATCH[1]}"
      elif [[ "$gate" =~ ^final-review-repair-([0-9]+)$ ]]; then
        phase_key="final-review"
        round="${BASH_REMATCH[1]}"
      else
        return 0
      fi

      [[ "$round" =~ ^[0-9]+$ ]] || return 0

      local sf route routes_json max_rounds escalate
      sf="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
      route="$(jq -r '.route // "formal"' "$sf" 2>/dev/null || echo "formal")"
      routes_json="$SCRIPT_DIR/../state-schema/routes-v1.json"
      [[ -f "$routes_json" ]] || return 0

      max_rounds="$(jq -r --arg r "$route" --arg p "$phase_key" '.routes[$r].repair_policy[$p].max_repair_rounds // empty' "$routes_json" 2>/dev/null || true)"
      [[ "$max_rounds" =~ ^[0-9]+$ ]] || return 0

      if [[ "$round" -gt "$max_rounds" ]]; then
        escalate="$(jq -r --arg r "$route" --arg p "$phase_key" '.routes[$r].repair_policy[$p].escalate_to_rca // false' "$routes_json" 2>/dev/null || echo "false")"
        if [[ "$escalate" == "true" ]]; then
          echo "Error: ${phase_key} repair round ${round} exceeds route cap ${max_rounds}; dispatch root_cause_analyst instead of another review loop." >&2
        else
          echo "Error: ${phase_key} repair round ${round} exceeds route cap ${max_rounds}; report BLOCKED to user." >&2
        fi
        exit 2
      fi
    }

    if [[ "$AGENT_ROLE" != "codex_reviewer" ]]; then
      echo "Error: review dispatch envelope agent_role must be codex_reviewer" >&2
      exit 2
    fi

    if [[ -z "$GATE" ]]; then
      GATE="$(gate_from_prompt_file)"
    fi
    validate_gate_name "$GATE"

    case "$REVIEW_INTENT" in
      baseline)
        if [[ -n "$AGENT_ID" && "$AGENT_ID" != "null" ]]; then
          echo "Error: baseline review envelope must set agent_id to null (this is a fresh dispatch)" >&2
          exit 2
        fi
        validate_plan_impl_gate "$GATE"
        validate_repair_round_cap "$GATE"
        ;;
      *)
        echo "Error: review_intent must be baseline (got: ${REVIEW_INTENT:-empty})" >&2
        exit 2
        ;;
    esac

    if [[ "$RUN_ID" != adhoc-* ]]; then
      # Budget is initialized at plan-writing (after plan_count is known). Design
      # review — the only baseline review dispatched during discovery — runs while
      # budget_status is still pending_plan_count. That pre-init window is the
      # legitimate early state, not an error, so skip the gate there. A
      # plan-impl-review-N always runs in execution (budget long since
      # initialized), so pending there is a real fault and must still surface.
      SF="${BUDGET_DIR}/workflow-state-${RUN_ID}.json"
      BUDGET_STATUS=$(jq -r '.budget.budget_status // empty' "$SF" 2>/dev/null || echo "")
      if [[ "$BUDGET_STATUS" == "pending_plan_count" && ! "$GATE" =~ ^plan-impl-review-[0-9]+$ ]]; then
        : # pre-init discovery window — design review not yet on the budget ledger
      else
        BUDGET_ARGS=(--run-id "$RUN_ID")
        if [[ "$ALLOW_OVER_BUDGET" == "true" ]]; then
          BUDGET_ARGS+=(--allow-over-budget --override-reason "$OVERRIDE_REASON")
        fi
        bash "$SCRIPT_DIR/state.sh" budget check "${BUDGET_ARGS[@]}" >/dev/null
      fi
    fi

    # Auto-inject the anti-hallucination quartet into the review prompt (§1 切片).
    # The quartet (Confidence rubric / Pre-emit Gate / 证据表 / Bias indicators) is
    # review-prompt content copied verbatim into every Codex prompt — moving it out
    # of the Coordinator's read path (review-dispatch.md) and injecting it here keeps
    # it out of the main-thread context window while guaranteeing every prompt carries
    # it. Idempotent (marker-guarded) so re-running validate on resume won't double it.
    QUARTET="$SCRIPT_DIR/../skills/_shared/review-prompt-quartet.md"
    QUARTET_MARKER="<!-- REVIEW-PROMPT-QUARTET (auto-injected by dispatch-review.sh) -->"
    if [[ -f "$QUARTET" ]] && ! grep -qF "$QUARTET_MARKER" "$PROMPT_FILE"; then
      { printf '\n%s\n\n' "$QUARTET_MARKER"; cat "$QUARTET"; } >> "$PROMPT_FILE"
    fi

    echo "OK"
    ;;

  record)
    # --- record subcommand ---
    PROMPT_FILE=""
    GATE=""
    AGENT_ID=""

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --prompt-file) PROMPT_FILE="${2:-}"; shift 2 ;;
        --gate) GATE="${2:-}"; shift 2 ;;
        --agent-id) AGENT_ID="${2:-}"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
      esac
    done

    [[ -n "$PROMPT_FILE" && -f "$PROMPT_FILE" && -n "$GATE" && -n "$AGENT_ID" ]] || {
      echo "Usage: dispatch-review.sh record --prompt-file PATH --gate GATE --agent-id AGENT_ID" >&2
      exit 2
    }

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    ENVELOPE=$(bash "$SCRIPT_DIR/../hooks/lib/parse-envelope.sh" "$PROMPT_FILE")

    RUN_ID=$(echo "$ENVELOPE" | jq -r '.run_id // empty')
    PHASE=$(echo "$ENVELOPE" | jq -r '.phase // empty')
    REVIEW_INTENT=$(echo "$ENVELOPE" | jq -r '.review_intent // empty')

    if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
      echo "Error: run_id required" >&2
      exit 2
    fi

    if [[ "$REVIEW_INTENT" != "baseline" ]]; then
      echo "Error: dispatch-review record only records baseline reviewer dispatches" >&2
      exit 2
    fi

    BUDGET_DIR="${STATE_BASE:-.codex/multi-model-workflow}"
    mkdir -p "$BUDGET_DIR/review-agents" "$BUDGET_DIR/review-registry"

    echo "$AGENT_ID" > "$BUDGET_DIR/review-agents/${GATE}.agent-id"

    now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq -n \
      --arg run_id "$RUN_ID" \
      --arg gate "$GATE" \
      --arg phase "$PHASE" \
      --arg agent_id "$AGENT_ID" \
      --arg prompt_file "$PROMPT_FILE" \
      --arg created_at "$now" \
      '{
        run_id: $run_id,
        gate: $gate,
        phase: $phase,
        review_intent: "baseline",
        agent_id: $agent_id,
        prompt_file: $prompt_file,
        result_file: null,
        status: "dispatched",
        created_at: $created_at,
        completed_at: null,
        budget_counted: false
      }' > "$BUDGET_DIR/review-registry/${GATE}.json"

    echo "OK"
    ;;

  -h|--help|help)
    cat <<'HELP'
dispatch-review.sh — Unified Codex review dispatch (validate + record)

Subcommands:
  validate  Validate a Codex review dispatch envelope before sending
  record    Record a successful baseline dispatch after receiving agent_id

Usage:
  dispatch-review.sh validate --prompt-file PATH [--gate GATE] [--allow-over-budget --override-reason TEXT]
  dispatch-review.sh record  --prompt-file PATH --gate GATE --agent-id AGENT_ID
HELP
    ;;

  *)
    echo "Usage: dispatch-review.sh <validate|record> [options]" >&2
    echo "Run 'dispatch-review.sh --help' for details." >&2
    exit 2
    ;;
esac
