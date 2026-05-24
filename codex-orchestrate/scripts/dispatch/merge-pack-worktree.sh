#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

JOB_FILE=""
NO_FF=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-file) JOB_FILE="$2"; shift 2 ;;
    --ff-only) NO_FF=false; shift ;;
    -h|--help) echo "Usage: merge-pack-worktree.sh --job-file <worker-job.json>"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$JOB_FILE" ]] || { echo "merge-pack-worktree: --job-file is required" >&2; exit 2; }
jq empty "$JOB_FILE" >/dev/null

BRANCH="$(jq -r '.branch' "$JOB_FILE")"
WORKTREE_PATH="$(jq -r '.worktree_path' "$JOB_FILE")"
JOB_RUN_ID="$(jq -r '.run_id' "$JOB_FILE")"
PACK_ID="$(jq -r '.pack_id' "$JOB_FILE")"
RETURN_FILE="$(jq -r '.return_file' "$JOB_FILE")"

[[ -f "$RETURN_FILE" ]] || { echo "merge-pack-worktree: missing durable return $RETURN_FILE" >&2; exit 2; }
jq empty "$RETURN_FILE" >/dev/null || { echo "merge-pack-worktree: durable return is not valid JSON: $RETURN_FILE" >&2; exit 2; }

for required in run_id pack_id verdict changed_files verification; do
  value_type="$(jq -r --arg key "$required" 'if has($key) then (.[$key] | type) else "missing" end' "$RETURN_FILE")"
  [[ "$value_type" != "missing" ]] || { echo "merge-pack-worktree: durable return missing $required" >&2; exit 2; }
done

RETURN_RUN_ID="$(jq -r '.run_id' "$RETURN_FILE")"
RETURN_PACK_ID="$(jq -r '.pack_id' "$RETURN_FILE")"
RETURN_VERDICT="$(jq -r '.verdict' "$RETURN_FILE")"
[[ "$RETURN_RUN_ID" == "$JOB_RUN_ID" ]] || { echo "merge-pack-worktree: return run_id mismatch ($RETURN_RUN_ID != $JOB_RUN_ID)" >&2; exit 2; }
[[ "$RETURN_PACK_ID" == "$PACK_ID" ]] || { echo "merge-pack-worktree: return pack_id mismatch ($RETURN_PACK_ID != $PACK_ID)" >&2; exit 2; }
[[ "$RETURN_VERDICT" == "pass" ]] || { echo "merge-pack-worktree: pack verdict is $RETURN_VERDICT, expected pass before merge" >&2; exit 2; }
jq -e '.changed_files | type == "array"' "$RETURN_FILE" >/dev/null || { echo "merge-pack-worktree: changed_files must be an array" >&2; exit 2; }
jq -e '.verification | type == "array" and length > 0 and all(.[]; .command and .status)' "$RETURN_FILE" >/dev/null || {
  echo "merge-pack-worktree: verification must contain command/status entries" >&2
  exit 2
}

if [[ "$NO_FF" == "true" ]]; then
  git merge --no-ff "$BRANCH" -m "Pack ${PACK_ID}: merge worker branch"
else
  git merge --ff-only "$BRANCH"
fi

MERGE_SHA="$(git rev-parse HEAD 2>/dev/null || echo "unknown")"
git worktree remove "$WORKTREE_PATH"
jq --arg sha "$MERGE_SHA" '.status = "merged" | .merge_sha = $sha' "$JOB_FILE" > "${JOB_FILE}.tmp" && mv "${JOB_FILE}.tmp" "$JOB_FILE"

STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"
ESF="$STATE_BASE/execution-state-${RETURN_RUN_ID}.json"
if [[ -f "$ESF" ]]; then
  source "$PLUGIN_ROOT/scripts/lib/state-lock.sh"
  LOCK_DIR="${STATE_BASE}/${RETURN_RUN_ID}.lock"
  state_lock_acquire "$LOCK_DIR"
  jq --arg pack "$PACK_ID" --arg verdict "$RETURN_VERDICT" --arg sha "$MERGE_SHA" '
    .plans |= with_entries(
      .value.packs |= with_entries(
        if .key == $pack then
          .value.status = "committed"
          | .value.worker_verdict = $verdict
          | .value.commit_sha = $sha
        else . end
      )
    )
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
  PLAN_ID="$(jq -r --arg pack "$PACK_ID" '[.plans | to_entries[] | select(.value.packs[$pack] != null) | .key] | first // empty' "$ESF")"
  if [[ -n "$PLAN_ID" ]]; then
    PLAN_DONE="$(jq --arg pid "$PLAN_ID" '[.plans[$pid].packs | to_entries[] | select(.value.status == "committed")] | length' "$ESF")"
    PLAN_TOTAL="$(jq --arg pid "$PLAN_ID" '[.plans[$pid].packs | to_entries[]] | length' "$ESF")"
    if [[ "$PLAN_TOTAL" -gt 0 && "$PLAN_DONE" -eq "$PLAN_TOTAL" ]]; then
      jq --arg pid "$PLAN_ID" --arg sha "$MERGE_SHA" '.plans[$pid].end_commit = $sha' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
    fi
  fi
  state_lock_release "$LOCK_DIR"
fi
