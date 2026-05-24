#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

JOB_FILE=""
REPAIR_PROMPT=""
DRY_RUN=false

usage() {
  cat <<'USAGE'
Usage: worktree-resume.sh --job-file <worker-job.json> --repair-prompt <file> [--dry-run]

Resumes a worktree-exec worker through codex exec resume <thread_id>.
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-file) JOB_FILE="$2"; shift 2 ;;
    --repair-prompt) REPAIR_PROMPT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

[[ -f "$JOB_FILE" ]] || { echo "worktree-resume: --job-file is required" >&2; exit 2; }
[[ -f "$REPAIR_PROMPT" ]] || { echo "worktree-resume: --repair-prompt is required" >&2; exit 2; }
jq empty "$JOB_FILE" >/dev/null

RUN_ID="$(jq -r '.run_id' "$JOB_FILE")"
PACK_ID="$(jq -r '.pack_id' "$JOB_FILE")"
ROLE="$(jq -r '.agent_role' "$JOB_FILE")"
THREAD_ID="$(jq -r '.thread_id // empty' "$JOB_FILE")"
MODEL="$(jq -r '.model // empty' "$JOB_FILE")"
EFFORT="$(jq -r '.reasoning_effort // empty' "$JOB_FILE")"
SANDBOX_MODE="$(jq -r '.sandbox_mode // "workspace-write"' "$JOB_FILE")"
WORKTREE_PATH="$(jq -r '.worktree_path' "$JOB_FILE")"
RETURN_FILE="$(jq -r '.return_file' "$JOB_FILE")"
JOB_DIR="$(cd "$(dirname "$JOB_FILE")" && pwd)"

[[ -n "$THREAD_ID" && "$THREAD_ID" != "unknown" && "$THREAD_ID" != "null" ]] || { echo "worktree-resume: job has no resumable thread_id" >&2; exit 2; }
[[ -n "$MODEL" && "$MODEL" != "null" ]] || { echo "worktree-resume: job missing model" >&2; exit 2; }
[[ -n "$EFFORT" && "$EFFORT" != "null" ]] || { echo "worktree-resume: job missing reasoning_effort" >&2; exit 2; }
[[ -d "$WORKTREE_PATH" ]] || { echo "worktree-resume: missing worktree $WORKTREE_PATH" >&2; exit 2; }

ENVELOPE_JSON="$(bash "$PLUGIN_ROOT/hooks/lib/parse-envelope.sh" "$REPAIR_PROMPT")"
ENVELOPE_RUN_ID="$(echo "$ENVELOPE_JSON" | jq -r '.run_id')"
ENVELOPE_PACK_ID="$(echo "$ENVELOPE_JSON" | jq -r '.pack_id // empty')"
ENVELOPE_ROLE="$(echo "$ENVELOPE_JSON" | jq -r '.agent_role')"
REPAIR_ROUND="$(echo "$ENVELOPE_JSON" | jq -r '.repair_round')"
IDEMPOTENCY_KEY="$(echo "$ENVELOPE_JSON" | jq -r '.idempotency_key')"

[[ "$ENVELOPE_RUN_ID" == "$RUN_ID" ]] || { echo "worktree-resume: repair prompt run_id mismatch" >&2; exit 2; }
[[ "$ENVELOPE_PACK_ID" == "$PACK_ID" ]] || { echo "worktree-resume: repair prompt pack_id mismatch" >&2; exit 2; }
[[ "$ENVELOPE_ROLE" == "$ROLE" ]] || { echo "worktree-resume: repair prompt agent_role mismatch" >&2; exit 2; }
[[ "$REPAIR_ROUND" -ge 1 ]] 2>/dev/null || { echo "worktree-resume: repair prompt must use repair_round >= 1" >&2; exit 2; }

SF="$STATE_BASE/workflow-state-${RUN_ID}.json"
if [[ -f "$SF" ]]; then
  existing="$(jq -r --arg key "$IDEMPOTENCY_KEY" '.idempotency_keys | index($key) // empty' "$SF")"
  [[ -z "$existing" ]] || { echo "worktree-resume: duplicate idempotency key $IDEMPOTENCY_KEY" >&2; exit 2; }

  missing=0
  missing_evidence=0
  while IFS= read -r ref; do
    [[ -n "$ref" ]] || continue
    disp="$(jq -r --arg fid "$ref" '.review_dispositions[]? | select(.finding_id == $fid) | .disposition // empty' "$SF")"
    [[ "$disp" == "accepted" ]] || missing=1
    evidence="$(jq -r --arg fid "$ref" '.review_dispositions[]? | select(.finding_id == $fid) | .evidence // empty' "$SF")"
    [[ -n "$evidence" && "$evidence" != "null" ]] || missing_evidence=1
  done < <(echo "$ENVELOPE_JSON" | jq -r '.disposition_refs // [] | .[]')
  [[ "$missing" -eq 0 ]] || { echo "worktree-resume: repair prompt references non-accepted finding" >&2; exit 2; }
  [[ "$missing_evidence" -eq 0 ]] || { echo "worktree-resume: accepted repair finding missing evidence" >&2; exit 2; }
  STATE_BASE="$STATE_BASE" bash "$PLUGIN_ROOT/scripts/state.sh" idempotency append --run-id "$RUN_ID" --key "$IDEMPOTENCY_KEY" >/dev/null
fi

RESUME_ID="${RUN_ID}-${PACK_ID//./-}-resume-${REPAIR_ROUND}-$(date -u +%Y%m%d%H%M%S)"
RESUME_DIR="$JOB_DIR/resumes"
mkdir -p "$RESUME_DIR"
PROMPT_FILE="$RESUME_DIR/${RESUME_ID}.prompt.md"
FINAL_FILE="$RESUME_DIR/${RESUME_ID}.final.md"
EVENTS_FILE="$RESUME_DIR/${RESUME_ID}.events.jsonl"

{
  cat "$REPAIR_PROMPT"
  echo
  echo "## Original Worktree Worker"
  echo "- Job file: $JOB_FILE"
  echo "- Worktree path: $WORKTREE_PATH"
  echo "- Thread id: $THREAD_ID"
  echo
  echo "Continue the original worker session. Do not create a replacement dispatch. Keep using the durable return file: $RETURN_FILE"
} > "$PROMPT_FILE"

if [[ "$DRY_RUN" == "false" ]]; then
  codex exec resume \
    --json \
    --output-last-message "$FINAL_FILE" \
    -m "$MODEL" \
    -c "model_reasoning_effort=\"$EFFORT\"" \
    -c "sandbox_mode=\"$SANDBOX_MODE\"" \
    "$THREAD_ID" - < "$PROMPT_FILE" > "$EVENTS_FILE"
else
  printf 'dry-run: codex exec resume skipped\n' > "$FINAL_FILE"
  printf '{"type":"thread.resumed","thread_id":"%s"}\n' "$THREAD_ID" > "$EVENTS_FILE"
fi

HEAD_SHA="$(git -C "$WORKTREE_PATH" rev-parse HEAD 2>/dev/null || jq -r '.head_sha // "unknown"' "$JOB_FILE")"
VERDICT="unknown"
if [[ -f "$RETURN_FILE" ]] && jq empty "$RETURN_FILE" >/dev/null 2>&1; then
  VERDICT="$(jq -r '.verdict // "unknown"' "$RETURN_FILE")"
fi

RESUME_JSON="$(jq -n \
  --arg resume_id "$RESUME_ID" \
  --arg repair_round "$REPAIR_ROUND" \
  --arg prompt_file "$PROMPT_FILE" \
  --arg events_file "$EVENTS_FILE" \
  --arg final_file "$FINAL_FILE" \
  --arg head_sha "$HEAD_SHA" \
  --arg verdict "$VERDICT" \
  '{resume_id:$resume_id, repair_round:($repair_round|tonumber), prompt_file:$prompt_file, events_file:$events_file, final_file:$final_file, head_sha:$head_sha, worker_verdict:$verdict}')"

jq --argjson resume "$RESUME_JSON" --arg head "$HEAD_SHA" --arg verdict "$VERDICT" '
  .resume_jobs = ((.resume_jobs // []) + [$resume])
  | .head_sha = $head
  | .worker_verdict = $verdict
  | .status = "completed"
' "$JOB_FILE" > "${JOB_FILE}.tmp" && mv "${JOB_FILE}.tmp" "$JOB_FILE"

ESF="$STATE_BASE/execution-state-${RUN_ID}.json"
if [[ -f "$ESF" ]]; then
  source "$PLUGIN_ROOT/scripts/lib/state-lock.sh"
  LOCK_DIR="${STATE_BASE}/${RUN_ID}.lock"
  state_lock_acquire "$LOCK_DIR"
  jq --arg pack "$PACK_ID" --arg verdict "$VERDICT" --arg job "$JOB_FILE" --arg thread "$THREAD_ID" '
    .plans |= with_entries(
      .value.packs |= with_entries(
        if .key == $pack then
          .value.status = "returned"
          | .value.worker_verdict = $verdict
          | .value.worker_job_file = $job
          | .value.worker_thread_id = $thread
          | .value.worker_backend = "codex-exec"
        else . end
      )
    )
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
  state_lock_release "$LOCK_DIR"
fi

echo "$JOB_FILE"
