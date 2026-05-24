#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"
JOBS_DIR="$STATE_BASE/review-jobs"
EVENTS_DIR="$STATE_BASE/review-events"
PARSE_ENVELOPE="$SCRIPT_DIR/../../hooks/lib/parse-envelope.sh"

cmd="${1:-}"
shift || true

usage() {
  cat <<'USAGE'
Usage:
  review-lane.sh submit --prompt-file <file> --result-file <file> [--lane auto|codex] [--review-kind auto|document|code] [--resume] [--dry-run]
  review-lane.sh status --job-id <id>
  review-lane.sh fetch --job-id <id>
  review-lane.sh cancel --job-id <id>
USAGE
  exit 2
}

write_job() {
  local file="$1"
  shift
  jq -n "$@" > "$file"
}

normalize_review_kind() {
  case "$1" in
    document|documents|doc|docs|design|plan) echo "document" ;;
    code|implementation|impl|bug|release|integration|final) echo "code" ;;
    auto|"") echo "auto" ;;
    *) echo "review-lane: unsupported --review-kind $1" >&2; exit 2 ;;
  esac
}

classify_review_kind() {
  local prompt_file="$1" explicit="$2"
  explicit="$(normalize_review_kind "$explicit")"
  [[ "$explicit" != "auto" ]] && { echo "$explicit"; return; }

  local envelope="" phase="" intent="" name
  if [[ -x "$PARSE_ENVELOPE" ]]; then
    envelope="$(bash "$PARSE_ENVELOPE" "$prompt_file" 2>/dev/null || true)"
  fi
  if [[ -n "$envelope" ]]; then
    phase="$(echo "$envelope" | jq -r '.phase // empty' 2>/dev/null || true)"
    intent="$(echo "$envelope" | jq -r '.review_intent // empty' 2>/dev/null || true)"
    case "$phase" in
      discovery|plan-writing) echo "document"; return ;;
      execution|final-review|multi-pr-merge) echo "code"; return ;;
    esac
    case "$intent" in
      release-risk|post-push-regression|targeted-re-review|path-a-re-review) echo "code"; return ;;
      baseline) ;;
    esac
  fi

  name="$(basename "$prompt_file" | tr '[:upper:]' '[:lower:]')"
  case "$name" in
    *design-review*|*plan-review*|*issue-review*|*issue-quality*|*discovery*|*plan-writing*) echo "document" ;;
    *) echo "code" ;;
  esac
}

model_for_review_kind() {
  case "$1" in
    document) echo "gpt-5.5" ;;
    code) echo "gpt-5.4" ;;
    *) echo "review-lane: unsupported review kind $1" >&2; exit 2 ;;
  esac
}

prompt_run_id() {
  local prompt_file="$1" envelope=""
  if [[ -x "$PARSE_ENVELOPE" ]]; then
    envelope="$(bash "$PARSE_ENVELOPE" "$prompt_file" 2>/dev/null || true)"
  fi
  if [[ -n "$envelope" ]]; then
    echo "$envelope" | jq -r '.run_id // empty' 2>/dev/null || true
  fi
}

find_resume_job() {
  local run_id="$1" review_kind="$2"
  local best_created="" best_job="" best_thread="" file created job thread kind lane resume status
  shopt -s nullglob
  for file in "$JOBS_DIR"/*.json; do
    lane="$(jq -r '.lane // empty' "$file" 2>/dev/null || true)"
    kind="$(jq -r '.review_kind // empty' "$file" 2>/dev/null || true)"
    resume="$(jq -r '.resume // false' "$file" 2>/dev/null || true)"
    status="$(jq -r '.status // empty' "$file" 2>/dev/null || true)"
    thread="$(jq -r '.thread_id // empty' "$file" 2>/dev/null || true)"
    [[ "$lane" == "codex" ]] || continue
    [[ "$kind" == "$review_kind" ]] || continue
    [[ "$resume" == "false" ]] || continue
    [[ "$status" == "completed" ]] || continue
    [[ -n "$thread" ]] || continue
    if [[ -n "$run_id" ]]; then
      [[ "$(jq -r '.run_id // empty' "$file" 2>/dev/null || true)" == "$run_id" ]] || continue
    fi
    created="$(jq -r '.created_at // empty' "$file" 2>/dev/null || true)"
    job="$(jq -r '.job_id // empty' "$file" 2>/dev/null || true)"
    if [[ -z "$best_created" || "$created" > "$best_created" ]]; then
      best_created="$created"
      best_job="$job"
      best_thread="$thread"
    fi
  done
  shopt -u nullglob
  [[ -n "$best_thread" ]] || return 1
  printf '%s\t%s\n' "$best_job" "$best_thread"
}

extract_thread_id() {
  local events_file="$1"
  jq -r 'select(.type == "thread.started") | .thread_id // empty' "$events_file" 2>/dev/null | tail -1
}

submit() {
  local prompt_file="" result_file="" lane="auto" review_kind="auto" resume=false dry_run=false base="" commit=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --prompt-file) prompt_file="$2"; shift 2 ;;
      --result-file) result_file="$2"; shift 2 ;;
      --lane) lane="$2"; shift 2 ;;
      --review-kind) review_kind="$2"; shift 2 ;;
      --resume) resume=true; shift ;;
      --dry-run) dry_run=true; shift ;;
      --base) base="$2"; shift 2 ;;
      --commit) commit="$2"; shift 2 ;;
      *) echo "Unknown submit argument: $1" >&2; usage ;;
    esac
  done

  [[ -f "$prompt_file" ]] || { echo "review-lane: --prompt-file is required" >&2; exit 2; }
  [[ -n "$result_file" ]] || { echo "review-lane: --result-file is required" >&2; exit 2; }

  [[ "$lane" == "auto" ]] && lane="codex"
  review_kind="$(classify_review_kind "$prompt_file" "$review_kind")"
  local review_model review_effort
  case "$lane" in
    codex)
      review_model="$(model_for_review_kind "$review_kind")"
      review_effort="xhigh"
      ;;
    *)
      echo "review-lane: unsupported lane $lane" >&2
      exit 2
      ;;
  esac

  mkdir -p "$JOBS_DIR" "$EVENTS_DIR" "$(dirname "$result_file")"
  local job_id job_file status run_id events_file thread_id="" resumed_from_job_id="" resume_info
  job_id="review-$(date -u +%Y%m%d%H%M%S)-$RANDOM"
  job_file="$JOBS_DIR/${job_id}.json"
  events_file="$EVENTS_DIR/${job_id}.jsonl"
  run_id="$(prompt_run_id "$prompt_file")"
  status="completed"

  if [[ "$dry_run" == "true" ]]; then
    if [[ "$lane" == "codex" && "$resume" == "true" ]]; then
      resume_info="$(find_resume_job "$run_id" "$review_kind")" || {
        echo "review-lane: --resume requested but no completed baseline Codex review session exists for run_id=${run_id:-unknown} kind=$review_kind" >&2
        exit 2
      }
      resumed_from_job_id="${resume_info%%$'\t'*}"
      thread_id="${resume_info#*$'\t'}"
    elif [[ "$lane" == "codex" ]]; then
      thread_id="dry-run-thread-${job_id}"
    fi
    printf 'DRY RUN review lane=%s kind=%s model=%s effort=%s resume=%s thread=%s prompt=%s\n' "$lane" "$review_kind" "$review_model" "$review_effort" "$resume" "$thread_id" "$prompt_file" > "$result_file"
  elif [[ "$lane" == "codex" ]]; then
    local selector=(--uncommitted)
    [[ -n "$base" ]] && selector=(--base "$base")
    [[ -n "$commit" ]] && selector=(--commit "$commit")
    if [[ "$resume" == "true" ]]; then
      resume_info="$(find_resume_job "$run_id" "$review_kind")" || {
        echo "review-lane: --resume requested but no completed baseline Codex review session exists for run_id=${run_id:-unknown} kind=$review_kind" >&2
        exit 2
      }
      resumed_from_job_id="${resume_info%%$'\t'*}"
      thread_id="${resume_info#*$'\t'}"
      codex exec resume \
        --json \
        -o "$result_file" \
        -m "$review_model" \
        -c "model_reasoning_effort=\"$review_effort\"" \
        "$thread_id" - < "$prompt_file" > "$events_file"
    else
      codex exec review \
        --json \
        -o "$result_file" \
        -m "$review_model" \
        -c "model_reasoning_effort=\"$review_effort\"" \
        "${selector[@]}" - < "$prompt_file" > "$events_file"
      thread_id="$(extract_thread_id "$events_file")"
    fi
    if [[ -z "$thread_id" ]]; then
      echo "review-lane: Codex review completed but no thread_id was captured; targeted re-review cannot be guaranteed." >&2
      exit 2
    fi
  else
    echo "review-lane: unsupported lane $lane" >&2
    exit 2
  fi

  write_job "$job_file" \
    --arg job_id "$job_id" \
    --arg lane "$lane" \
    --arg status "$status" \
    --arg prompt_file "$prompt_file" \
    --arg result_file "$result_file" \
    --arg events_file "$events_file" \
    --arg run_id "$run_id" \
    --arg review_kind "$review_kind" \
    --arg model "$review_model" \
    --arg reasoning_effort "$review_effort" \
    --arg thread_id "$thread_id" \
    --arg resumed_from_job_id "$resumed_from_job_id" \
    --argjson resume "$resume" \
    '{job_id:$job_id,lane:$lane,status:$status,prompt_file:$prompt_file,result_file:$result_file,events_file:$events_file,run_id:$run_id,review_kind:$review_kind,model:$model,reasoning_effort:$reasoning_effort,thread_id:$thread_id,resume:$resume,resumed_from_job_id:$resumed_from_job_id,created_at:now|todate}'

  echo "$job_id"
}

status() {
  local job_id="" wait=false timeout_ms=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --job-id) job_id="$2"; shift 2 ;;
      --wait) wait=true; shift ;;
      --timeout-ms) timeout_ms="$2"; shift 2 ;;
      *) usage ;;
    esac
  done
  local job_file="$JOBS_DIR/${job_id}.json"
  [[ -f "$job_file" ]] || { echo "review-lane: job not found" >&2; exit 2; }
  if [[ "$wait" == "true" ]]; then
    local elapsed=0
    while true; do
      local current
      current="$(jq -r '.status' "$job_file")"
      case "$current" in
        completed|blocked|cancelled|failed) break ;;
      esac
      if [[ "$timeout_ms" -gt 0 && "$elapsed" -ge "$timeout_ms" ]]; then
        jq -r '.status' "$job_file"
        return 124
      fi
      sleep 1
      elapsed=$((elapsed + 1000))
    done
  fi
  jq -r '.status' "$JOBS_DIR/${job_id}.json"
}

fetch() {
  local job_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --job-id) job_id="$2"; shift 2 ;;
      *) usage ;;
    esac
  done
  local job_file="$JOBS_DIR/${job_id}.json"
  [[ -f "$job_file" ]] || { echo "review-lane: job not found" >&2; exit 2; }
  local result_file
  result_file="$(jq -r '.result_file' "$job_file")"
  [[ -f "$result_file" ]] || { echo "review-lane: result not found" >&2; exit 2; }
  cat "$result_file"
}

cancel() {
  local job_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --job-id) job_id="$2"; shift 2 ;;
      *) usage ;;
    esac
  done
  local job_file="$JOBS_DIR/${job_id}.json"
  [[ -f "$job_file" ]] || { echo "review-lane: job not found" >&2; exit 2; }
  jq '.status = "cancelled"' "$job_file" > "${job_file}.tmp" && mv "${job_file}.tmp" "$job_file"
}

case "$cmd" in
  submit) submit "$@" ;;
  status) status "$@" ;;
  fetch|result) fetch "$@" ;;
  cancel) cancel "$@" ;;
  *) usage ;;
esac
