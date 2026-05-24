#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_BASE="${STATE_BASE:-.codex/multi-model-workflow}"

ENVELOPE_FILE=""
PACK_BRIEF=""
BASE_REF="HEAD"
WORKTREE_ROOT=".worktrees/codex-orchestrate"
DRY_RUN=false

usage() {
  cat <<'USAGE'
Usage: worktree-exec.sh --envelope-file <file> --pack-brief <file> [--base-ref <ref>] [--worktree-root <dir>] [--dry-run]

Creates a managed git worktree, runs codex exec in that worktree, and records a pack job.
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --envelope-file) ENVELOPE_FILE="$2"; shift 2 ;;
    --pack-brief) PACK_BRIEF="$2"; shift 2 ;;
    --base-ref) BASE_REF="$2"; shift 2 ;;
    --worktree-root) WORKTREE_ROOT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

[[ -f "$ENVELOPE_FILE" ]] || { echo "worktree-exec: --envelope-file is required" >&2; exit 2; }
[[ -f "$PACK_BRIEF" ]] || { echo "worktree-exec: --pack-brief is required" >&2; exit 2; }
jq empty "$ENVELOPE_FILE" >/dev/null

RUN_ID="$(jq -r '.run_id' "$ENVELOPE_FILE")"
PACK_ID="$(jq -r '.pack_id' "$ENVELOPE_FILE")"
ROLE="$(jq -r '.agent_role' "$ENVELOPE_FILE")"
SAFE_PACK_ID="${PACK_ID//./-}"
JOB_ID="${RUN_ID}-${SAFE_PACK_ID}-$(date -u +%Y%m%d%H%M%S)"
AGENT_CONFIG="$PLUGIN_ROOT/agents/${ROLE}.toml"

OUT_DIR="$STATE_BASE/worker-jobs/$JOB_ID"
RETURN_DIR="$STATE_BASE/pack-returns/$RUN_ID"
mkdir -p "$OUT_DIR" "$RETURN_DIR" "$WORKTREE_ROOT"

BRANCH="codex-orchestrate/${RUN_ID}/${SAFE_PACK_ID}"
WORKTREE_PATH="$WORKTREE_ROOT/${RUN_ID}/${SAFE_PACK_ID}"
PROMPT_FILE="$OUT_DIR/prompt.md"
FINAL_FILE="$OUT_DIR/final.md"
EVENTS_FILE="$OUT_DIR/events.jsonl"
RETURN_FILE="$RETURN_DIR/${PACK_ID}.json"
AGENT_CONTEXT_FILE="$OUT_DIR/agent-context.md"

[[ -f "$AGENT_CONFIG" ]] || { echo "worktree-exec: missing agent config $AGENT_CONFIG" >&2; exit 2; }

read_agent_field() {
  python3 - "$AGENT_CONFIG" "$1" <<'PY'
import sys
import tomllib

path, key = sys.argv[1], sys.argv[2]
with open(path, "rb") as fh:
    data = tomllib.load(fh)
value = data.get(key, "")
if value is None:
    value = ""
print(value)
PY
}

MODEL="$(read_agent_field model)"
EFFORT="$(read_agent_field model_reasoning_effort)"
SANDBOX_MODE="$(read_agent_field sandbox_mode)"
[[ -n "$MODEL" ]] || { echo "worktree-exec: agent config missing model" >&2; exit 2; }
[[ -n "$EFFORT" ]] || { echo "worktree-exec: agent config missing model_reasoning_effort" >&2; exit 2; }
[[ -n "$SANDBOX_MODE" ]] || SANDBOX_MODE="workspace-write"

python3 - "$AGENT_CONFIG" > "$AGENT_CONTEXT_FILE" <<'PY'
import sys
import tomllib

path = sys.argv[1]
with open(path, "rb") as fh:
    data = tomllib.load(fh)

print("# Agent Runtime Contract")
print()
print(f"Agent name: {data.get('name', '')}")
print(f"Model: {data.get('model', '')}")
print(f"Reasoning effort: {data.get('model_reasoning_effort', '')}")
print(f"Sandbox mode: {data.get('sandbox_mode', '')}")
print()
print("## Developer Instructions")
print()
print(data.get("developer_instructions", "").strip())

skills = data.get("skills", {}).get("config", [])
if skills:
    print()
    print("## Enabled Skills")
    print()
    for skill in skills:
        if skill.get("enabled", True):
            print(f"- {skill.get('path', '')}")
PY

{
  echo '<!-- DISPATCH_ENVELOPE'
  cat "$ENVELOPE_FILE"
  echo '-->'
  echo
  cat "$AGENT_CONTEXT_FILE"
  echo
  cat "$PACK_BRIEF"
  echo
  echo "Durable return file: $RETURN_FILE"
} > "$PROMPT_FILE"

BASE_SHA="$(git rev-parse "$BASE_REF")"

if [[ "$DRY_RUN" == "false" ]]; then
  if [[ ! -d "$WORKTREE_PATH/.git" ]]; then
    git worktree add -b "$BRANCH" "$WORKTREE_PATH" "$BASE_REF"
  fi

  codex exec --cd "$WORKTREE_PATH" \
    --sandbox "$SANDBOX_MODE" \
    --json \
    --output-last-message "$FINAL_FILE" \
    -m "$MODEL" \
    -c "model_reasoning_effort=\"$EFFORT\"" \
    - < "$PROMPT_FILE" > "$EVENTS_FILE"
else
  mkdir -p "$WORKTREE_PATH"
  printf 'dry-run: codex exec skipped\n' > "$FINAL_FILE"
  printf '{"type":"thread.started","thread_id":"dry-run-thread-%s"}\n' "$JOB_ID" > "$EVENTS_FILE"
fi

THREAD_ID="$(jq -r 'select(.type == "thread.started") | .thread_id // empty' "$EVENTS_FILE" 2>/dev/null | head -1)"
[[ -n "$THREAD_ID" ]] || THREAD_ID="unknown"
AGENT_ID="codex-exec:${THREAD_ID}"

HEAD_SHA="$(git -C "$WORKTREE_PATH" rev-parse HEAD 2>/dev/null || echo "$BASE_SHA")"
VERDICT="unknown"
if [[ -f "$RETURN_FILE" ]] && jq empty "$RETURN_FILE" >/dev/null 2>&1; then
  VERDICT="$(jq -r '.verdict // "unknown"' "$RETURN_FILE")"
fi

jq -n \
  --arg job_id "$JOB_ID" \
  --arg run_id "$RUN_ID" \
  --arg pack_id "$PACK_ID" \
  --arg role "$ROLE" \
  --arg branch "$BRANCH" \
  --arg worktree_path "$WORKTREE_PATH" \
  --arg base_sha "$BASE_SHA" \
  --arg head_sha "$HEAD_SHA" \
  --arg prompt_file "$PROMPT_FILE" \
  --arg agent_config "$AGENT_CONFIG" \
  --arg thread_id "$THREAD_ID" \
  --arg agent_id "$AGENT_ID" \
  --arg model "$MODEL" \
  --arg effort "$EFFORT" \
  --arg sandbox "$SANDBOX_MODE" \
  --arg events_file "$EVENTS_FILE" \
  --arg final_file "$FINAL_FILE" \
  --arg return_file "$RETURN_FILE" \
  --arg verdict "$VERDICT" \
  '{job_id:$job_id, run_id:$run_id, pack_id:$pack_id, agent_role:$role, agent_id:$agent_id, thread_id:$thread_id, agent_config:$agent_config, model:$model, reasoning_effort:$effort, sandbox_mode:$sandbox, branch:$branch, worktree_path:$worktree_path, base_sha:$base_sha, head_sha:$head_sha, prompt_file:$prompt_file, events_file:$events_file, final_file:$final_file, return_file:$return_file, worker_verdict:$verdict, resume_jobs:[], status:"completed"}' \
  > "$OUT_DIR/job.json"

ESF="$STATE_BASE/execution-state-${RUN_ID}.json"
if [[ -f "$ESF" ]]; then
  source "$PLUGIN_ROOT/scripts/lib/state-lock.sh"
  LOCK_DIR="${STATE_BASE}/${RUN_ID}.lock"
  state_lock_acquire "$LOCK_DIR"
  jq --arg pack "$PACK_ID" --arg verdict "$VERDICT" --arg job "$OUT_DIR/job.json" --arg thread "$THREAD_ID" --arg agent "$AGENT_ID" '
    .plans |= with_entries(
      .value.packs |= with_entries(
        if .key == $pack then
          .value.status = "returned"
          | .value.worker_verdict = $verdict
          | .value.worker_job_file = $job
          | .value.worker_thread_id = $thread
          | .value.worker_backend = "codex-exec"
          | .value.agent_id = $agent
        else . end
      )
    )
  ' "$ESF" > "${ESF}.tmp" && mv "${ESF}.tmp" "$ESF"
  state_lock_release "$LOCK_DIR"
fi

echo "$OUT_DIR/job.json"
